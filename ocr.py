"""OCR.space API integration for extracting menu items from photos/PDFs."""

import os
import re

import requests


OCR_API_KEY = os.environ.get("OCR_SPACE_API_KEY", "")
OCR_API_URL = "https://api.ocr.space/parse/image"


def ocr_extract_text(file_storage, language="rus"):
    """Send a file to OCR.space and return extracted text.

    Args:
        file_storage: werkzeug FileStorage object from request.files
        language: OCR language code ('rus' for Russian, 'eng' for English).
                  Defaults to 'rus' since most Tashkent menus are in Russian.

    Returns:
        str: extracted text, or raises an exception on failure
    """
    if not OCR_API_KEY:
        raise ValueError("OCR_SPACE_API_KEY environment variable is not set")

    filename = file_storage.filename or "upload"
    payload = {
        "apikey": OCR_API_KEY,
        "language": language,
        "isOverlayRequired": False,
        "detectOrientation": True,
        "scale": True,
        "OCREngine": 2,
    }

    # Determine if PDF
    if filename.lower().endswith(".pdf"):
        payload["filetype"] = "PDF"

    resp = requests.post(
        OCR_API_URL,
        data=payload,
        files={"file": (filename, file_storage.stream, file_storage.content_type or "application/octet-stream")},
        timeout=60,
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

    Looks for patterns like:
      Dish Name ... 128,000
      Dish Name    128 000
      Dish Name - 128000

    Returns:
        list[dict]: each with keys 'name', 'price', 'category'
    """
    items = []
    lines = raw_text.split("\n")
    current_category = "Uncategorized"

    # Price patterns: digits with optional thousand separators (space, comma, dot, apostrophe)
    price_pattern = re.compile(
        r'([\d]{2,3}(?:[,.\s\']?\d{3})+|[\d]{4,})\s*(?:сум|sum|uzs|so.m|сўм)?\s*$',
        re.IGNORECASE
    )

    # Category-like headers: short lines with no digits, often ALL CAPS or ending with ':'
    category_pattern = re.compile(r'^([A-ZА-ЯЁa-zа-яё\s]{3,40})\s*:?\s*$')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if this looks like a category header
        cat_match = category_pattern.match(line)
        if cat_match and not re.search(r'\d', line):
            candidate = cat_match.group(1).strip().title()
            if len(candidate) > 2:
                current_category = candidate
            continue

        # Try to extract price from end of line
        price_match = price_pattern.search(line)
        if price_match:
            price_str = price_match.group(1)
            # Remove separators
            price_clean = re.sub(r'[,.\s\']', '', price_str)
            try:
                price = int(price_clean)
            except ValueError:
                continue

            # Skip unrealistic prices (too low or too high)
            if price < 1000 or price > 50_000_000:
                continue

            # Dish name is everything before the price
            name = line[:price_match.start()].strip()
            # Clean trailing dots, dashes, ellipses
            name = re.sub(r'[\s.\-–—_…]+$', '', name).strip()

            if name and len(name) > 1:
                items.append({
                    "name": name,
                    "price": price,
                    "category": current_category,
                })

    return items
