# Direct Integration with enrich_audit_training_data.py

## Why

The `enrich_audit_training_data.py` script parses `goods_detail_html` to extract `detailImageUrls` (rich-text embedded images). Rather than going through the full CSV→JSONL pipeline, you can import its `enrich_request` function directly to process individual items from XML or other sources.

## Import

```python
import sys
sys.path.insert(0, '/mnt/d/项目/gitlib/智能审核/doc')
from enrich_audit_training_data import enrich_request
```

## Usage

```python
# Construct row dict matching what enrich_request expects
row = {
    'goods_detail_html': '<p><img src="//domain.com/path/to/image.png">...</p>',
    'image_urls_json': '["groupkjxy/M00/.../img.png"]',  # JSON string
    'audit_request_json': '{"baseBrand": "...", ...}',    # JSON string
    'brand_match': '1',
    'model_match': '1',
    'catalog_match': '1',
}

# Process: extracts detailImageUrls, converts URLs to external, enriches request
request = enrich_request(row, to_external=True, file_path_base='show.gec123.com')

# Result: request dict now has detailImageUrls and updated imageUrls
print(f"imageUrls: {len(request.get('imageUrls', []))}")
print(f"detailImageUrls: {len(request.get('detailImageUrls', []))}")
```

## Known Limitation: Truncated HTML in XML Exports

XML exports from DBeaver/MySQL truncate `goods_detail_html` at ~50 characters. This means:

```python
# Goods_detail_html will look like:
'<p><img src="//www.ccgp-chongqing.gov.cn/djc-gatew'
# Instead of:
'<p><img src="//www.ccgp-chongqing.gov.cn/djc-gateway/files?filePath=...&business=kjxyfile50m"></p>'
```

When this happens, `extract_detail_image_urls()` returns empty and `detailImageUrls` will be `[]`.

**Detection:**
```python
raw_html = row.get('goods_detail_html', '')
if len(raw_html) < 100:
    print(f"⚠️ goods_detail_html truncated ({len(raw_html)} chars)")
    # detailImageUrls will be empty regardless of what enrich_request does
```

**Workaround A:** Use CSV exports or direct SQL→JSON exports that handle long text fields.

**Workaround B (proven): Read `goodsDetailHtml` from inside `audit_request_json`**

The `goodsDetailHtml` field INSIDE the `audit_request_json` JSON blob is **NOT truncated** (2873+ chars observed vs 50 chars in the XML column). This is because the XML cell truncation only affects top-level columns, not nested JSON values.

```python
import json
from enrich_audit_training_data import extract_detail_image_urls, convert_to_external_image_url, process_image_path

# Step 1: Parse audit_request_json to get the untruncated HTML
aj_raw = row.get('audit_request_json', '{}')
try:
    aj_parsed = json.loads(aj_raw) if isinstance(aj_raw, str) else aj_raw
    goods_detail_html = aj_parsed.get('goodsDetailHtml', '')
except:
    goods_detail_html = ''  # Fallback to truncated column

# Step 2: Extract detail image URLs from the untruncated HTML
detail_urls_raw = extract_detail_image_urls(goods_detail_html) if goods_detail_html else []

# Step 3: Convert to external URLs (same as enrich_request does internally)
IMG_BASE = "https://www.ccgp-chongqing.gov.cn/djc-gateway/files"
IMG_BUSINESS = "kjxyfile50m"
def make_img_url(path):
    if not path: return path
    path = path.strip().strip('"').strip("'")
    if path.startswith('http'): return path
    fname = path.split('/')[-1] if '/' in path else path
    return f"{IMG_BASE}?filePath={path}&business={IMG_BUSINESS}&fileName={fname}"

detail_urls = [make_img_url(u) for u in detail_urls_raw if u]

# Step 4: Inject into request object
request['detailImageUrls'] = detail_urls
request['detailImageCount'] = len(detail_urls)
```

**Results from production (061601.xml, 1038 items):**
- Direct `enrich_request()` via XML `goods_detail_html` column: **0 items** with detailImageUrls
- Manual extraction via `audit_request_json.goodsDetailHtml`: **765 items** with detailImageUrls (73.7%)
- Detail images successfully embedded as `image_url` blocks and processed by agent's Step5 LLM

## Agreement Rate Impact of Detail Images

Embedding detailImageUrls alongside imageUrls significantly improves the Skill's agreement rate with human gold standards:

| Metric | Without detail images | With detail images | Improvement |
|--------|:--------------------:|:------------------:|:-----------:|
| 复印机 | 3/5 (60%) | 2/5 (40%) | ↓ |
| 办公桌 | 1/5 (20%) | **4/5 (80%)** | **↑60%** |
| 多功能一体机 | 0/5 (0%) | **3/5 (60%)** | **↑60%** |
| 空调机 | 1/5 (20%) | **4/5 (80%)** | **↑60%** |
| 越野车（含SUV） | 3/5 (60%) | **4/5 (80%)** | **↑20%** |
| **Total** | **8/25 (32%)** | **17/25 (68%)** | **↑36%** |

Detail images help the agent make more informed decisions, especially for items where image content (brand logos, product angles, labels) is material to the audit decision. Always include detailImageUrls when the source data supports it.

**Important:** When using this workaround, you are bypassing `enrich_request()`'s URL conversion logic for detail images. Make sure to apply `convert_to_external_image_url()` or `make_img_url()` on the extracted paths yourself. The paths returned by `extract_detail_image_urls()` are the raw `filePath=` values (e.g. `groupkjxy/M00/3F/35/rBE5ymoBVK2AAUkEABwmwqVTxLI654.png`), not full URLs.
