"""OCR.space API integration for extracting menu items from photos/PDFs."""

import os
import re

import requests


OCR_API_KEY = os.environ.get("OCR_SPACE_API_KEY", "")
OCR_API_URL = "https://api.ocr.space/parse/image"


def ocr_extract_text(file_storage, language="rus"):
    """Send a file to OCR.space and return extracted text.

    Uses Engine 1 with table detection for better layout parsing of menus
    where prices are right-aligned.
    """
    if not OCR_API_KEY:
        raise ValueError("OCR_SPACE_API_KEY environment variable is not set")

    filename = file_storage.filename or "upload"
    file_bytes = file_storage.read()
    file_storage.seek(0)

    payload = {
        "apikey": OCR_API_KEY,
        "language": language,
        "isOverlayRequired": False,
        "detectOrientation": True,
        "scale": True,
        "isTable": True,
        "OCREngine": 1,
    }

    if filename.lower().endswith(".pdf"):
        payload["filetype"] = "PDF"

    resp = requests.post(
        OCR_API_URL,
        data=payload,
        files={"file": (filename, file_bytes, file_storage.content_type or "application/octet-stream")},
        timeout=120,
    )
    resp.raise_for_status()
    result = resp.json()

    if result.get("IsErroredOnProcessing"):
        error_msg = result.get("ErrorMessage") or result.get("ErrorDetails") or "OCR processing failed"
        raise ValueError(f"OCR error: {error_msg}")

    pages = result.get("ParsedResults", [])
    if not pages:
        raise ValueError("OCR returned no results")

    return "\n".join(p.get("ParsedText", "") for p in pages)


def clean_ocr_name(name):
    """Clean OCR artifacts from dish names.

    Strips common misreadings of menu icons (N), (V), circled letters,
    and other OCR garbage characters.  Runs two passes so that junk
    exposed by earlier substitutions (e.g. '{' left after '(y)' removal)
    is also caught.
    """
    for _ in range(2):
        # Remove leading OCR junk: @, @@, {, }, (), (N), (V), (84), (y), etc.
        name = re.sub(r'^[\s@{}\[\]#*]+', '', name)
        # Remove leading parenthesized garbage: (N), (V), (84), (y), etc.
        name = re.sub(r'^\([^)]{0,5}\)\s*', '', name)
        # Remove circled/special unicode chars that OCR might produce
        name = re.sub(r'^[®©™⓪①②③④⑤⑥⑦⑧⑨ⓝⓥⓃⓋ]+\s*', '', name)
    # Remove trailing @, {, }, etc.
    name = re.sub(r'[\s@{}\[\]#*]+$', '', name)
    # Remove leading/trailing dashes, dots, underscores
    name = re.sub(r'^[\s.\-–—_…\t]+|[\s.\-–—_…\t]+$', '', name)
    # Collapse multiple spaces
    name = re.sub(r'\s{2,}', ' ', name).strip()
    return name


def parse_menu_text(raw_text):
    """Parse OCR text to extract dish names and prices.

    Handles common menu formats:
      - Tab-separated: "Caesar Salad\\t220 000"
      - Multi-space: "Caesar Salad       220 000"
      - Same line: "Caesar Salad 220000 UZS"
      - Price on next line after dish name
    """
    items = []
    lines = raw_text.split("\n")
    current_category = "Uncategorized"

    # Use space/comma/dot/apostrophe as thousand separator (NOT tab)
    SEP = r'[ ,.\']'

    # Price pattern: 1-3 digits + separator + 3 digits, optionally repeated, or 4+ digits
    PRICE = r'(\d{1,3}' + SEP + r'?\d{3}(?:' + SEP + r'?\d{3})?|\d{4,})'
    SUFFIX = r'\s*(?:uzs|сум|сўм|so.m)?\s*'

    # Price at end of line (after tab or multi-space)
    price_after_tab = re.compile(r'\t+' + PRICE + SUFFIX + '$', re.IGNORECASE)
    price_after_spaces = re.compile(r' {3,}' + PRICE + SUFFIX + '$', re.IGNORECASE)
    price_end = re.compile(PRICE + SUFFIX + '$', re.IGNORECASE)

    # Standalone price line
    standalone_price = re.compile(r'^\s*' + PRICE + SUFFIX + '$', re.IGNORECASE)

    def clean_price(s):
        cleaned = re.sub(r'[, .\']', '', s)
        try:
            p = int(cleaned)
            return p if 1000 <= p <= 50_000_000 else None
        except ValueError:
            return None

    def is_junk_line(line):
        """Check if a line is likely junk (too short, only symbols, etc.)."""
        stripped = re.sub(r'[\s@{}\[\]()#*.,\-–—_…]+', '', line)
        return len(stripped) < 2

    def is_description(line):
        """Check if a line is a description (ingredients list, not a dish name)."""
        if not line:
            return True
        # Very long lines with many commas are ingredient lists
        if line.count(',') >= 4 and not re.search(r'\d{3}', line):
            return True
        return False

    def is_category_header(line):
        """Only treat as category if it clearly looks like a section header."""
        # Clean the line first
        cleaned = re.sub(r'[^A-Za-zА-Яа-яЁё\s:/&\-]', '', line).strip()
        if not cleaned or len(cleaned) < 3:
            return False
        if re.search(r'\d', line):
            return False
        if len(cleaned) > 25:
            return False
        # Lines ending with colon
        if line.rstrip().endswith(':'):
            return True
        # Known category words (English and Russian)
        lower = cleaned.lower()
        category_words = [
            'pasta', 'seafood', 'meat', 'desserts', 'dessert', 'salads', 'salad',
            'soups', 'soup', 'appetizers', 'starters', 'mains', 'main courses',
            'drinks', 'beverages', 'wine', 'sides', 'sauces', 'grill',
            'meat dishes', 'fish', 'cold appetizers', 'hot appetizers',
            'салаты', 'супы', 'горячее', 'десерты', 'закуски', 'напитки',
            'паста', 'мясо', 'рыба', 'гриль', 'основные блюда',
            'durum wheat pasta',
        ]
        if lower in category_words:
            return True
        # Two-word categories in ALL CAPS
        words = cleaned.split()
        if len(words) <= 2 and cleaned == cleaned.upper():
            return True
        return False

    pending_name = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip junk lines
        if is_junk_line(line):
            continue

        # 1. Check for standalone price (belongs to previous pending dish name)
        sp = standalone_price.match(line)
        if sp and pending_name:
            price = clean_price(sp.group(1))
            if price:
                items.append({"name": pending_name, "price": price, "category": current_category})
                pending_name = None
                continue

        # Try to extract price from the line using multiple strategies
        price = None
        name_part = None

        # 2. Tab-separated: "DISH NAME\t220 000"
        m = price_after_tab.search(line)
        if m:
            price = clean_price(m.group(1))
            if price:
                name_part = line[:m.start()]

        # 3. Multi-space separated: "DISH NAME       220 000"
        if not price:
            m = price_after_spaces.search(line)
            if m:
                price = clean_price(m.group(1))
                if price:
                    name_part = line[:m.start()]

        # 4. Price at end of line: "DISH NAME 220000"
        if not price:
            m = price_end.search(line)
            if m:
                price = clean_price(m.group(1))
                if price:
                    name_part = line[:m.start()]

        if price and name_part is not None:
            name = clean_ocr_name(name_part)
            if name and len(name) > 1:
                items.append({"name": name, "price": price, "category": current_category})
                pending_name = None
                continue

        # 5. Skip description lines (ingredient lists)
        if is_description(line):
            continue

        # 6. Check for category header
        if is_category_header(line):
            current_category = re.sub(r'[^A-Za-zА-Яа-яЁё\s/&\-]', '', line).strip().title()
            pending_name = None
            continue

        # 7. Potential dish name — store for pairing with price on next line
        cleaned_line = clean_ocr_name(line)
        if cleaned_line and len(cleaned_line) > 2 and cleaned_line[0].isupper():
            pending_name = cleaned_line

    return items
