---
name: ocr-and-documents
description: "Extract text from PDFs/scans (pymupdf, marker-pdf)."
version: 2.3.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [PDF, Documents, Research, Arxiv, Text-Extraction, OCR]
    related_skills: [powerpoint]
---

# PDF & Document Extraction

For DOCX: use `python-docx` (parses actual document structure, far better than OCR).
For PPTX: see the `powerpoint` skill (uses `python-pptx` with full slide/notes support).
This skill covers **PDFs and scanned documents**.

## Step 1: Remote URL Available?

If the document has a URL, **always try `web_extract` first**:

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

This handles PDF-to-markdown conversion via Firecrawl with no local dependencies.

Only use local extraction when: the file is local, web_extract fails, or you need batch processing.

## Step 2: Choose Local Extractor

| Feature | pymupdf (~25MB) | marker-pdf (~3-5GB) |
|---------|-----------------|---------------------|
| **Text-based PDF** | ✅ | ✅ |
| **Scanned PDF (OCR)** | ❌ | ✅ (90+ languages) |
| **Tables** | ✅ (basic) | ✅ (high accuracy) |
| **Equations / LaTeX** | ❌ | ✅ |
| **Code blocks** | ❌ | ✅ |
| **Forms** | ❌ | ✅ |
| **Headers/footers removal** | ❌ | ✅ |
| **Reading order detection** | ❌ | ✅ |
| **Images extraction** | ✅ (embedded) | ✅ (with context) |
| **Images → text (OCR)** | ❌ | ✅ (marker-pdf) |
| | | ✅ (easyocr — lightweight alternative) |
| **EPUB** | ✅ | ✅ |
| **Markdown output** | ✅ (via pymupdf4llm) | ✅ (native, higher quality) |
| **Install size** | ~25MB | ~3-5GB (PyTorch + models) for marker-pdf |
| | | ~800MB (torch+cuda) or ~300MB (cpu-only) for easyocr |
| **Speed** | Instant | ~1-14s/page (CPU), ~0.2s/page (GPU) for marker-pdf |
| | | ~3-10s/page (CPU) for easyocr |

**Decision tree**:
1. **Text-based PDF** → pymupdf (instant, no deps)
2. **Scanned PDF, need OCR** → Try **EasyOCR first** (lighter, pure Python, ch_sim+en support, ~300MB install). Only fall back to marker-pdf if easyocr quality is insufficient or you need full layout preservation.
3. **Equations, complex layouts, forms** → marker-pdf (~3-5GB)

### EasyOCR (lightweight OCR, recommended for Chinese/English scans)

**Setup:**
```bash
python3 -m pip install --user --break-system-packages easyocr pymupdf
```

First run downloads models (~100MB). Subsequent runs cache them.

**Important: PYTHONPATH for user-installed packages**
When running via `terminal()` tool, user site-packages isn't on default path. Always use:
```bash
PYTHONPATH=$HOME/.local/lib/python3.12/site-packages python3 script.py
```
Or write a standalone `.py` file and call via `terminal()`.

**Standalone OCR script** (save to `scripts/ocr_easy.py`):
```python
# scripts/ocr_easy.py — OCR scanned PDF using EasyOCR
# Usage: PYTHONPATH=... python3 scripts/ocr_easy.py input.pdf --pages 1-10 --dpi 200
import fitz, easyocr, sys, os, argparse, time

def ocr_pdf(pdf_path, start_page=0, end_page=None, dpi=300, min_conf=0.3):
    doc = fitz.open(pdf_path)
    total = len(doc)
    end_page = min(end_page or total, total)
    
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    all_text = []
    
    for i in range(start_page, end_page):
        pix = doc[i].get_pixmap(dpi=dpi)
        t0 = time.time()
        result = reader.readtext(pix.tobytes("png"))
        elapsed = time.time() - t0
        
        texts = [t for _, t, c in result if c >= min_conf]
        page_text = f"\n===== Page {i+1} ({elapsed:.1f}s) =====\n" + "\n".join(texts)
        all_text.append(page_text)
        sys.stderr.write(f"  Page {i+1}/{end_page}: {len(texts)} segs ({elapsed:.1f}s)\n")
    
    doc.close()
    return "\n".join(all_text)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("--pages"); ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--output"); ap.add_argument("--min-conf", type=float, default=0.3)
    args = ap.parse_args()
    
    start, end = 0, None
    if args.pages:
        p = args.pages.split("-"); start = max(0, int(p[0])-1); end = int(p[1]) if len(p)>1 else None
    
    text = ocr_pdf(args.pdf, start, end, args.dpi, args.min_conf)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f: f.write(text)
    else:
        print(text)
```

**Tips for EasyOCR on Chinese scanned textbooks:**
- **200dpi** is sufficient for most textbook text (faster)
- **300dpi** for dense text or small fonts
- Filter confidence < 0.3 to reduce garbage
- OCR takes ~3-10s per page on CPU — for large books, OCR only needed pages (10-20 at a time)
- The model is ~100MB downloaded once to `~/.EasyOCR/model/`
- GPU mode (`gpu=True`) is 5-10x faster if CUDA is available

---

## pymupdf (lightweight)

```bash
pip install pymupdf pymupdf4llm
```

**Via helper script**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Inline**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (high-quality OCR)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Via helper script**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (installed with marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## Arxiv Papers

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Split, Merge & Search

pymupdf handles these natively — use `execute_code` or inline Python:

```python
# Split: extract pages 1-5 to a new PDF
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")
```

```python
# Merge multiple PDFs
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

```python
# Search for text across all pages
import pymupdf
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
        print(page.get_text("text"))
```

No extra dependencies needed — pymupdf covers split, merge, search, and text extraction in one package.

---

## Notes

- `web_extract` is always first choice for URLs
- pymupdf is the safe default — instant, no models, works everywhere
- marker-pdf is for OCR, scanned docs, equations, complex layouts — install only when needed
- Both helper scripts accept `--help` for full usage
- marker-pdf downloads ~2.5GB of models to `~/.cache/huggingface/` on first use
- For Word docs: `pip install python-docx` (better than OCR — parses actual structure)
- For PowerPoint: see the `powerpoint` skill (uses python-pptx)
