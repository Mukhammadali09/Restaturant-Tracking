"""Menu image parsing — Claude Vision API (primary) with OCR.space fallback."""

import base64
import json
import os
import re

import requests

try:
    import anthropic

    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False


ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OCR_API_KEY = os.environ.get("OCR_SPACE_API_KEY", "")
OCR_API_URL = "https://api.ocr.space/parse/image"

MENU_EXTRACTION_PROMPT = """Extract ALL dishes with their prices from this restaurant menu image.

Return ONLY a valid JSON array — no explanation, no markdown, just the array.
Each element must have exactly these keys:
- "name": the complete dish name as printed on the menu (omit markers like V, N, circled icons)
- "price": the price as a plain integer in UZS (e.g. 280000 not "280 000")
- "category": the section/category header this dish belongs to, in Title Case

Rules:
- Include EVERY dish on the page — do not skip any
- Read each column independently; do NOT merge text across columns
- Prices in Uzbekistan are typically 5–7 digits (e.g. 70000 … 1050000)
- Convert spaced prices: "280 000" → 280000
- Strip menu markers (V) vegetarian, (N) new, circled letters, etc.
- For nested sub-sections (e.g. "Ceviche" under "Raw Bar"), use "Raw Bar" as category
"""


# ═══════════════════════════════════════════════════════════════════════════════
#  PRIMARY: Claude Vision API
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_with_claude(files_list):
    """Send one or more menu images/PDFs to Claude Vision in a SINGLE API call.

    files_list: list of (file_bytes, content_type, filename) tuples.
    All files are sent as separate image/document blocks in one message,
    so 10 menu pages = 1 API call instead of 10.
    """
    if not _HAS_ANTHROPIC or not ANTHROPIC_API_KEY:
        raise ValueError("Anthropic SDK not available or ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Build content blocks — one per file
    content_blocks = []
    for file_bytes, content_type, filename in files_list:
        b64_data = base64.b64encode(file_bytes).decode("utf-8")
        is_pdf = filename.lower().endswith(".pdf")

        if is_pdf:
            content_blocks.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": b64_data,
                },
            })
        else:
            media_type = content_type or "image/jpeg"
            if media_type == "application/octet-stream":
                media_type = "image/jpeg"
            content_blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": b64_data,
                },
            })

    # Add the extraction prompt after all images
    content_blocks.append({"type": "text", "text": MENU_EXTRACTION_PROMPT})

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8192,
        messages=[{"role": "user", "content": content_blocks}],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        parts = raw.split("```")
        inner = parts[1] if len(parts) >= 3 else parts[-1]
        if inner.startswith("json"):
            inner = inner[4:]
        raw = inner.strip()

    items = json.loads(raw)

    # Validate
    result = []
    for item in items:
        name = str(item.get("name", "")).strip()
        price = item.get("price", 0)
        category = str(item.get("category", "Uncategorized")).strip()
        if name and isinstance(price, (int, float)) and price > 0:
            result.append({"name": name, "price": int(price), "category": category})

    return result


# ═══════════════════════════════════════════════════════════════════════════════
#  FALLBACK: OCR.space + text parser
# ═══════════════════════════════════════════════════════════════════════════════

def _ocr_api_call(file_bytes, filename, content_type, language="rus", engine=1):
    """Low-level OCR.space API call. Returns extracted text."""
    if not OCR_API_KEY:
        raise ValueError("OCR_SPACE_API_KEY environment variable is not set")

    payload = {
        "apikey": OCR_API_KEY,
        "language": language,
        "isOverlayRequired": False,
        "detectOrientation": True,
        "scale": True,
        "OCREngine": engine,
    }
    if engine == 1:
        payload["isTable"] = True
    if filename.lower().endswith(".pdf"):
        payload["filetype"] = "PDF"

    resp = requests.post(
        OCR_API_URL,
        data=payload,
        files={"file": (filename, file_bytes, content_type)},
        timeout=120,
    )
    resp.raise_for_status()
    result = resp.json()

    if result.get("IsErroredOnProcessing"):
        error_msg = (
            result.get("ErrorMessage") or result.get("ErrorDetails") or "OCR processing failed"
        )
        raise ValueError(f"OCR error: {error_msg}")

    pages = result.get("ParsedResults", [])
    if not pages:
        raise ValueError("OCR returned no results")

    return "\n".join(p.get("ParsedText", "") for p in pages)


def _ocr_dual_engine(file_bytes, filename, content_type, language="rus"):
    """Try both OCR engines and return whichever extracts more menu items."""
    raw1, items1 = "", []
    raw2, items2 = "", []

    try:
        raw1 = _ocr_api_call(file_bytes, filename, content_type, language, engine=1)
        items1 = parse_menu_text(raw1)
    except Exception:
        pass

    try:
        raw2 = _ocr_api_call(file_bytes, filename, content_type, language, engine=2)
        items2 = parse_menu_text(raw2)
    except Exception:
        pass

    if len(items2) > len(items1):
        return raw2, items2
    if items1:
        return raw1, items1
    return raw1 or raw2, []


def clean_ocr_name(name):
    """Clean OCR artifacts from dish names."""
    for _ in range(2):
        name = re.sub(r'^[\s@{}\[\]#*]+', '', name)
        name = re.sub(r'^\([^)]{0,5}\)\s*', '', name)
        name = re.sub(r'^[A-Za-z0-9]\)\s*', '', name)
        name = re.sub(r'^[\u00ae\u00a9\u2122\u24ea\u2460-\u2468\u24dd\u24e5\u24c3\u24cb]+\s*', '', name)
    name = re.sub(r'[\s@{}\[\]#*]+$', '', name)
    name = re.sub(r'^[\s.\-\u2013\u2014_\u2026\t]+|[\s.\-\u2013\u2014_\u2026\t]+$', '', name)
    name = re.sub(r'\s{2,}', ' ', name).strip()
    return name


def parse_menu_text(raw_text):
    """Parse OCR text to extract dish names and prices."""
    items = []
    lines = raw_text.split("\n")
    current_category = "Uncategorized"

    SEP = r'[ ,.\']'
    PRICE = r'(\d{1,3}' + SEP + r'?\d{3}(?:' + SEP + r'?\d{3})?|\d{4,})'
    SUFFIX = r'\s*(?:uzs|\u0441\u0443\u043c|\u0441\u045e\u043c|so.m)?\s*'

    price_after_tab = re.compile(r'\t+' + PRICE + SUFFIX + '$', re.IGNORECASE)
    price_after_spaces = re.compile(r' {3,}' + PRICE + SUFFIX + '$', re.IGNORECASE)
    price_end = re.compile(PRICE + SUFFIX + '$', re.IGNORECASE)
    standalone_price = re.compile(r'^\s*' + PRICE + SUFFIX + '$', re.IGNORECASE)

    def clean_price(s):
        cleaned = re.sub(r'[, .\']', '', s)
        try:
            p = int(cleaned)
            return p if 1000 <= p <= 50_000_000 else None
        except ValueError:
            return None

    def is_junk_line(line):
        stripped = re.sub(r'[\s@{}\[\]()#*.,\-\u2013\u2014_\u2026]+', '', line)
        return len(stripped) < 2

    def is_description(line):
        if not line:
            return True
        if line.count(',') >= 4 and not re.search(r'\d{3}', line):
            return True
        return False

    def is_category_header(line):
        cleaned = re.sub(r'[^A-Za-z\u0410-\u042f\u0430-\u044f\u0401\u0451\s:/&\-]', '', line).strip()
        if not cleaned or len(cleaned) < 3 or re.search(r'\d', line) or len(cleaned) > 25:
            return False
        if line.rstrip().endswith(':'):
            return True
        category_words = [
            'pasta', 'seafood', 'meat', 'desserts', 'dessert', 'salads', 'salad',
            'soups', 'soup', 'appetizers', 'starters', 'mains', 'main courses',
            'drinks', 'beverages', 'wine', 'sides', 'sauces', 'grill',
            'meat dishes', 'fish', 'cold appetizers', 'hot appetizers',
            'raw bar', 'risotto',
            '\u0441\u0430\u043b\u0430\u0442\u044b', '\u0441\u0443\u043f\u044b',
            '\u0433\u043e\u0440\u044f\u0447\u0435\u0435', '\u0434\u0435\u0441\u0435\u0440\u0442\u044b',
            '\u0437\u0430\u043a\u0443\u0441\u043a\u0438', '\u043d\u0430\u043f\u0438\u0442\u043a\u0438',
            '\u043f\u0430\u0441\u0442\u0430', '\u043c\u044f\u0441\u043e',
            '\u0440\u044b\u0431\u0430', '\u0433\u0440\u0438\u043b\u044c',
            '\u043e\u0441\u043d\u043e\u0432\u043d\u044b\u0435 \u0431\u043b\u044e\u0434\u0430',
            'durum wheat pasta',
        ]
        if cleaned.lower() in category_words:
            return True
        words = cleaned.split()
        if len(words) <= 2 and cleaned == cleaned.upper():
            return True
        return False

    pending_name = None
    for line in lines:
        line = line.strip()
        if not line or is_junk_line(line):
            continue

        sp = standalone_price.match(line)
        if sp and pending_name:
            price = clean_price(sp.group(1))
            if price:
                items.append({"name": pending_name, "price": price, "category": current_category})
                pending_name = None
                continue

        price, name_part = None, None
        for pattern in (price_after_tab, price_after_spaces, price_end):
            m = pattern.search(line)
            if m:
                price = clean_price(m.group(1))
                if price:
                    name_part = line[:m.start()]
                    break

        if price and name_part is not None:
            name = clean_ocr_name(name_part)
            if name and len(name) > 1:
                items.append({"name": name, "price": price, "category": current_category})
                pending_name = None
                continue

        if is_description(line):
            continue
        if is_category_header(line):
            current_category = re.sub(
                r'[^A-Za-z\u0410-\u042f\u0430-\u044f\u0401\u0451\s/&\-]', '', line
            ).strip().title()
            pending_name = None
            continue

        cleaned_line = clean_ocr_name(line)
        if cleaned_line and len(cleaned_line) > 2 and cleaned_line[0].isupper():
            pending_name = cleaned_line

    return items


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def parse_menu_image(files_list, language="eng"):
    """Parse one or more menu image/PDF files.

    files_list: list of (file_bytes, content_type, filename) tuples.
    With Claude Vision, ALL files are sent in ONE API call (saves credits).
    Returns a 4-tuple: (raw_text, items, method_used, error_detail)
    """
    # Try Claude Vision first — sends ALL files in a single API call
    if _HAS_ANTHROPIC and ANTHROPIC_API_KEY:
        try:
            items = _parse_with_claude(files_list)
            if items:
                summary = "\n".join(
                    f"[{it['category']}] {it['name']} — {it['price']:,}" for it in items
                )
                return summary, items, "claude_vision", None
        except Exception as exc:
            claude_error = str(exc)
            print(f"Claude Vision failed: {claude_error}")
            if not OCR_API_KEY:
                raise ValueError(f"Claude Vision failed: {claude_error}")
    elif not _HAS_ANTHROPIC and ANTHROPIC_API_KEY:
        claude_error = "anthropic package not installed on server"
    elif _HAS_ANTHROPIC and not ANTHROPIC_API_KEY:
        claude_error = "ANTHROPIC_API_KEY not set in environment"
    else:
        claude_error = "anthropic package not installed and ANTHROPIC_API_KEY not set"

    # Fallback to OCR.space — must process each file separately
    if OCR_API_KEY:
        all_items = []
        all_raw = []
        for file_bytes, content_type, filename in files_list:
            raw, items = _ocr_dual_engine(file_bytes, filename, content_type, language)
            all_items.extend(items)
            all_raw.append(raw)
        return "\n\n".join(all_raw), all_items, "ocr_space", claude_error

    raise ValueError(
        f"No working API. Claude Vision: {claude_error}. "
        "OCR.space: OCR_SPACE_API_KEY not set."
    )
