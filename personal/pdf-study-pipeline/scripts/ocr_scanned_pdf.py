#!/usr/bin/env python3
"""
扫描版PDF OCR工具 — 用 EasyOCR 将扫描版PDF每页渲染为图片后识别文字

用法：
  python3 scripts/ocr_scanned_pdf.py input.pdf
  python3 scripts/ocr_scanned_pdf.py input.pdf --pages 5-15
  python3 scripts/ocr_scanned_pdf.py input.pdf --dpi 200
  python3 scripts/ocr_scanned_pdf.py input.pdf --output result.txt
  python3 scripts/ocr_scanned_pdf.py input.pdf --min-conf 0.4
  python3 scripts/ocr_scanned_pdf.py input.pdf --no-skip
  python3 scripts/ocr_scanned_pdf.py input.pdf --batch 10
"""
import fitz, easyocr, os, sys, argparse, time

def ocr_pdf(pdf_path, start_page=0, end_page=None, dpi=300, min_conf=0.3, skip_low=True, batch_size=10):
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"[PDF] Opening: {os.path.basename(pdf_path)}", file=sys.stderr)
    doc = fitz.open(pdf_path)
    total = len(doc)
    if end_page is None or end_page > total:
        end_page = total
    
    print(f"[PDF] Pages: {total}, Range: {start_page+1}-{end_page}", file=sys.stderr)
    print(f"[OCR] Initializing EasyOCR (ch_sim+en)...", file=sys.stderr)
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    
    all_text = []
    for i in range(start_page, end_page):
        page = doc[i]
        pix = page.get_pixmap(dpi=dpi)
        img_bytes = pix.tobytes("png")
        
        t0 = time.time()
        result = reader.readtext(img_bytes)
        elapsed = time.time() - t0
        
        page_text = f"\n\n===== Page {i+1} (OCR: {elapsed:.1f}s) =====\n"
        segments = []
        for bbox, text, conf in result:
            if not skip_low or conf >= min_conf:
                segments.append(text)
                page_text += text + "\n"
        
        all_text.append(page_text)
        status = f"  Page {i+1}/{end_page}, {len(segments)} segments, {elapsed:.1f}s"
        if segments:
            print(f"  [OK] {status}", file=sys.stderr)
        else:
            print(f"  [--] {status} (no text found)", file=sys.stderr)
    
    doc.close()
    return "\n".join(all_text)

def main():
    parser = argparse.ArgumentParser(description="OCR scanned PDF using EasyOCR")
    parser.add_argument("pdf", help="PDF file path")
    parser.add_argument("--pages", help="Page range like 5-15 (1-indexed)")
    parser.add_argument("--dpi", type=int, default=300, help="Render DPI (default: 300)")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--min-conf", type=float, default=0.3, help="Min confidence threshold (default: 0.3)")
    parser.add_argument("--no-skip", action="store_true", help="Don't filter low confidence results")
    args = parser.parse_args()
    
    start, end = 0, None
    if args.pages:
        parts = args.pages.split("-")
        start = max(0, int(parts[0]) - 1)
        if len(parts) > 1:
            end = int(parts[1])
    
    text = ocr_pdf(args.pdf, start, end, args.dpi, args.min_conf, not args.no_skip)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\n[OK] Saved to: {args.output}", file=sys.stderr)
    else:
        print(text)

if __name__ == "__main__":
    main()
