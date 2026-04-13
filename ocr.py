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

    # Price pattern: 2-3 digits + separator + 3 digits, optionally repeated, or 4+ digits
    PRICE = r'(\d{2,3}' + SEP + r'?\d{3}(?:' + SEP + r'?\d{3})?|\d{4,})'
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

    def clean_name(s):
        s = re.sub(r'[ .\-–—_…\t]+$', '', s).strip()
        s = re.sub(r'^[\-–—•*]\s*', '', s).strip()
        return s

    def is_description(line):
        if not line:
            return True
        if line[0].islower():
            return True
        if line.count(',') >= 3 and not re.search(r'\d{3}', line):
            return True
        return False

    def is_category_header(line):
        """Only treat as category if it clearly looks like a section header.

        Strict to avoid confusing all-caps dish names with categories.
        """
        if re.search(r'\d', line):
            return False
        if len(line) > 25:
            return False
        if not re.match(r'^[A-ZА-ЯЁa-zа-яё\s/&\-]+:?\s*$', line):
            return False
        # Lines ending with colon are almost certainly categories
        if line.rstrip().endswith(':'):
            return True
        # Single-word all-caps (e.g. "SALADS", "ДЕСЕРТЫ")
        stripped = line.strip()
        if stripped == stripped.upper() and ' ' not in stripped and len(stripped) <= 20:
            return True
        return False

    pending_name = None

    for line in lines:
        line = line.strip()
        if not line or len(line) < 2:
            continue

        # 1. Check for standalone price (belongs to previous pending dish name)
        sp = standalone_price.match(line)
        if sp and pending_name:
            price = clean_price(sp.group(1))
            if price:
                items.append({"name": pending_name, "price": price, "category": current_category})
                pending_name = None
                continue

        # 2. Check for tab-separated: "DISH NAME\t220 000"
        m = price_after_tab.search(line)
        if m:
            price = clean_price(m.group(1))
            if price:
                name = clean_name(line[:m.start()])
                if name and len(name) > 1:
                    items.append({"name": name, "price": price, "category": current_category})
                    pending_name = None
                    continue

        # 3. Check for multi-space separated: "DISH NAME       220 000"
        m = price_after_spaces.search(line)
        if m:
            price = clean_price(m.group(1))
            if price:
                name = clean_name(line[:m.start()])
                if name and len(name) > 1:
                    items.append({"name": name, "price": price, "category": current_category})
                    pending_name = None
                    continue

        # 4. Check for price at end of line: "DISH NAME 220000"
        m = price_end.search(line)
        if m:
            price = clean_price(m.group(1))
            if price:
                name = clean_name(line[:m.start()])
                if name and len(name) > 1:
                    items.append({"name": name, "price": price, "category": current_category})
                    pending_name = None
                    continue

        # 5. Skip description lines
        if is_description(line):
            continue

        # 6. Check for category header (strict: short, no digits, looks like heading)
        if is_category_header(line):
            current_category = line.rstrip(':').strip().title()
            pending_name = None
            continue

        # 7. Likely a dish name — store for pairing with price on next line
        if line[0].isupper():
            pending_name = clean_name(line)

    return items
