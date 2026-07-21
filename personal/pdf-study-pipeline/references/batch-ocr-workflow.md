# Batch OCR Workflow for Exam Question Banks

## When to Use
- You have a LARGE scanned PDF (200+ pages) of exam questions
- Multiple years/sections need separate output files
- Need to run as background process (>30 min expected runtime)

## Step-by-Step

### 1. Classify the PDF
```bash
python3 -c "
import fitz
doc = fitz.open('input.pdf')
for i in range(min(5, len(doc))):
    t = doc[i].get_text().strip()
    print(f'Page {i+1}: {len(t)} chars')
doc.close()
"
```
- All pages < 30 chars → scanned (OCR needed)
- Pages > 200 chars → has text (use PyMuPDF directly)

### 2. Get the Table of Contents
OCR page ~6 (usually TOC) to get chapter-to-page mapping:
```python
# quick check
page = doc[5]  # page 6
pix = page.get_pixmap(dpi=200)
r = easyocr.Reader(['ch_sim','en'], gpu=False)
for bbox, text, conf in r.readtext(pix.tobytes('png')):
    if conf > 0.3:
        print(text)
```

### 3. Define Section Ranges
From TOC, map chapters to (start_page, end_page, year, label):
```python
SECTIONS = [
    (8, 27, 2013, '上午试题（综合知识）'),
    (28, 45, 2013, '下午试题I（案例分析）'),
    # skip 下午II (论文/写作) if not needed
]
```

### 4. Write the OCR Script
Use the template from SKILL.md section "Batch OCR for Large Exam Question Banks".
Key elements:
- Log file for progress monitoring
- Incremental .part saves every 5 pages
- min_conf=0.3, dpi=200
- gpu=False unless NVIDIA confirmed

### 5. Run in Background
```bash
terminal(background=true, command="PYTHONPATH=$HOME/.local/lib/python3.12/site-packages python3 /tmp/ocr_batch.py", notify_on_complete=true, timeout=7200)
```

### 6. Monitor Progress
```bash
tail -5 /path/to/output/_ocr_progress.log
ls -la /path/to/output/
```

### 7. Post-Processing
- Rename files to clear convention: `{year}_{section}_{type}.txt`
- Verify content quality on a sample file
- Delete .part files if any remain

## File Naming Convention
```
2013_综合知识_上午试题.txt
2013_案例分析_下午试题I.txt
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| MuPDF error: "too many kids in page tree" | Malformed PDF structure | Non-fatal, ignore |
| Only "仅供个人学习" text extracted | Watermark overlay on scanned content | Check page count — it's really scanned |
| Background process shows no output | Pipe capture doesn't flush | Write to log file instead |
| Process stuck / no progress | EasyOCR model download or GPU hang | Check ~/.EasyOCR/ exists; kill and retry with gpu=False |
| File says "下午试题_综合知识" | Wrong filename from TOC page mapping | Rename after extraction |

## Expected Time
- 200dpi CPU: ~12s/page → 250 pages ≈ 50 min
- 300dpi CPU: ~15s/page → 250 pages ≈ 63 min  
- With GPU (NVIDIA/cuDNN): 2-5x faster
