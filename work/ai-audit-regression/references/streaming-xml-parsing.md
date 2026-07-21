# Streaming XML Parsing for Large Test Data Files

The `061601.xml` test data file is ~300MB (9,857 rows × 48 columns with embedded JSON in `audit_request_json`). Full-load parsing (`f.read()` → `re.findall()`) is impractical for targeted retests.

## Comparison

| Approach | Time | RAM | Use Case |
|----------|------|-----|----------|
| Full-load + regex | 45-60s | 500MB+ | Full batch (need all items) |
| Streaming line-by-line | 10-15s | ~20MB | Targeted retest / subsets |

## Streaming Pattern

```python
import re, html

def stream_parse(xml_path, targets):
    """Stream XML, yield matching rows without loading 300MB into memory.
    targets: set of (catalog, brand) tuples to match.
    """
    with open(xml_path, encoding='utf-8') as f:
        header_map = None
        buffer = []; in_row = False; in_table = False
        seen_pairs = set()

        for line in f:
            if '<ss:Table>' in line:
                in_table = True
                continue
            if '</ss:Table>' in line:
                break
            if not in_table:
                continue

            if '<ss:Row>' in line:
                in_row = True
                buffer = [line]
            elif '</ss:Row>' in line and in_row:
                buffer.append(line)
                row_text = ''.join(buffer)
                in_row = False

                cells = [html.unescape(d) for d in 
                         re.findall(r'<Data[^>]*>(.*?)</Data>', row_text, re.DOTALL)]
                if not cells or len(cells) < 32:
                    continue

                # Parse header on first data row
                if header_map is None:
                    header_map = {cells[i]: i for i in range(len(cells))}
                    continue

                def g(field):
                    i = header_map.get(field, -1)
                    return cells[i].strip() if 0 <= i < len(cells) else ''

                cat = g('base_catalog')
                brand = g('base_brand')
                fidelity = g('data_label_fidelity')

                if fidelity != 'HIGH':
                    continue

                key = (cat, brand)
                if key in seen_pairs or key not in targets:
                    continue
                seen_pairs.add(key)

                yield {
                    'cat': cat, 'brand': brand,
                    'model': g('base_model'),
                    'fast': g('ai_audit_result_code'),
                    'human': g('human_audit_result'),
                    'ai_reason': g('ai_audit_reason'),
                    'audit_request_json': g('audit_request_json'),
                }
            elif in_row:
                buffer.append(line)
```

## Key Points

- Uses `seen_pairs` to dedup by (catalog, brand) inside the stream — returns only first match per pair
- Stops at `</ss:Table>` — doesn't scan the entire file
- No `f.read()` — memory footprint stays ~20MB regardless of file size
- Each `<ss:Row>` block accumulates in a buffer until `</ss:Row>` is seen
- `html.unescape()` handles `&quot;` and `&amp;` in cell values

## When to Use

- Targeted retests (re-running only mismatched items)
- Debugging specific catalog+brand combos
- Any time you need <100 items from the full dataset
- When memory is constrained (WSL with limited RAM)
