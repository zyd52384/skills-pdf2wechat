#!/usr/bin/env python3
"""
Capture specific pages from a PDF as high-resolution PNG screenshots.

Usage:
    python capture_pages.py <pdf_path> --pages <1,3,5> [--output <dir>] [--dpi 300]

Output: JSON to stdout with paths to generated images
"""

import json
import sys
import os


def parse_pages(pages_str):
    """Parse comma-separated page numbers, supports ranges like 1-3."""
    result = []
    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            try:
                start, end = part.split("-", 1)
                result.extend(range(int(start), int(end) + 1))
            except ValueError:
                continue
        else:
            try:
                result.append(int(part))
            except ValueError:
                continue
    return sorted(set(result))


def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": "Usage: capture_pages.py <pdf_path> --pages <1,3,5> [--output <dir>] [--dpi 300]"
        }, ensure_ascii=False))
        sys.exit(1)

    pdf_path = sys.argv[1]

    pages_str = None
    output_dir = None
    dpi = 300

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--pages" and i + 1 < len(args):
            pages_str = args[i + 1]
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_dir = args[i + 1]
            i += 2
        elif args[i] == "--dpi" and i + 1 < len(args):
            try:
                dpi = int(args[i + 1])
            except ValueError:
                pass
            i += 2
        else:
            i += 1

    if not pages_str:
        print(json.dumps({"error": "--pages is required"}, ensure_ascii=False))
        sys.exit(1)

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

    # Determine output directory
    if not output_dir:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_dir = os.path.join(os.path.dirname(pdf_path) or ".", f"{base_name}_screenshots")

    os.makedirs(output_dir, exist_ok=True)

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(json.dumps({"error": f"Failed to open PDF: {e}"}, ensure_ascii=False))
        sys.exit(1)

    try:
        page_numbers = parse_pages(pages_str)
        total_pages = doc.page_count

        # Filter out invalid page numbers
        valid_pages = [p for p in page_numbers if 1 <= p <= total_pages]
        invalid_pages = [p for p in page_numbers if p < 1 or p > total_pages]

        if not valid_pages:
            print(json.dumps({
                "error": f"No valid pages in range 1-{total_pages}. Requested: {page_numbers}"
            }, ensure_ascii=False))
            doc.close()
            sys.exit(1)

        # Zoom factor for DPI
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)

        images = []
        for page_num in valid_pages:
            page = doc[page_num - 1]  # 0-based
            pix = page.get_pixmap(matrix=mat)

            output_path = os.path.join(output_dir, f"page_{page_num:03d}.png")
            pix.save(output_path)

            images.append({
                "page_num": page_num,
                "path": os.path.abspath(output_path),
                "width": pix.width,
                "height": pix.height,
                "dpi": dpi,
            })

        doc.close()

        result = {
            "output_dir": os.path.abspath(output_dir),
            "dpi": dpi,
            "page_count": len(images),
            "skipped_pages": invalid_pages,
            "images": images,
        }

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(json.dumps({"error": f"Capture failed: {e}"}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
