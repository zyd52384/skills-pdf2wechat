#!/usr/bin/env python3
"""
Extract text content from a PDF file.

Usage:
    python extract_pdf.py <pdf_path> [--limit N]

Output: JSON to stdout with pages array (page_num, word_count, text, has_images)
"""

import json
import sys
import os


def get_pdf_info(doc):
    """Return basic PDF metadata."""
    meta = doc.metadata or {}
    return {
        "title": meta.get("title", ""),
        "author": meta.get("author", ""),
        "subject": meta.get("subject", ""),
        "page_count": doc.page_count,
    }


def page_has_images(page):
    """Check if page contains embedded images."""
    try:
        images = page.get_images(full=True)
        return len(images) > 0
    except Exception:
        return False


def extract_text(doc, limit=None):
    """Extract text from each page."""
    pages = []
    total_pages = doc.page_count
    page_range = range(total_pages)

    if limit and limit < total_pages:
        page_range = range(limit)

    for i in page_range:
        page = doc[i]
        text = page.get_text("text")
        word_count = len(text.split()) if text.strip() else 0
        has_img = page_has_images(page)

        pages.append({
            "page_num": i + 1,  # 1-based
            "word_count": word_count,
            "has_images": has_img,
            "text": text.strip(),
        })

    return pages


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: extract_pdf.py <pdf_path> [--limit N]"}, ensure_ascii=False))
        sys.exit(1)

    pdf_path = sys.argv[1]
    limit = None

    # Parse optional --limit
    args = sys.argv[2:]
    for i, arg in enumerate(args):
        if arg == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                pass

    if not os.path.exists(pdf_path):
        print(json.dumps({"error": f"File not found: {pdf_path}"}, ensure_ascii=False))
        sys.exit(1)

    try:
        import fitz  # pymupdf
    except ImportError:
        print(json.dumps({
            "error": "pymupdf (fitz) not installed. Install with: pip install pymupdf"
        }, ensure_ascii=False))
        sys.exit(1)

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(json.dumps({"error": f"Failed to open PDF: {e}"}, ensure_ascii=False))
        sys.exit(1)

    try:
        info = get_pdf_info(doc)
        pages = extract_text(doc, limit)
        doc.close()

        result = {
            "info": info,
            "pages": pages,
            "total_text_length": sum(p["word_count"] for p in pages),
        }

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(json.dumps({"error": f"Extraction failed: {e}"}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
