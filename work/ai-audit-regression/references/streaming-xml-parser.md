# Streaming XML Parser for Large Data Files

The production `061601.xml` is **300MB / 493K lines** — loading it fully into memory causes OOM or multi-minute hangs.

## Pattern: Line-by-Line Row Accumulator

```python
def stream_parse(xml_path, targets):
    """Streaming parser: yields matching rows without loading 300MB into memory."""
    with open(xml_path, encoding='utf-8') as f:
        header_map = None
        buffer = []
        in_row = False
        in_table = False
        row_count = 0
        match_count = 0
        seen_pairs = set()  # dedup: one per (catalog, brand)

        for line in f:
            if '<ss:Table>' in line:
                in_table = True
                continue
            if '</ss:Table>' in line:
                in_table = False
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
                row_count += 1

                cells = parse_cells(row_text)
                if not cells or len(cells) < 32:
                    continue

                if header_map is None:
                    header_map = {cells[i]: i for i in range(len(cells))}
                    continue

                cat = cells[header_map.get('base_catalog', -1)]
                brand = cells[header_map.get('base_brand', -1)]
                fidelity = cells[header_map.get('data_label_fidelity', -1)]

                if fidelity != 'HIGH':
                    continue

                if (cat, brand) in targets:
                    if (cat, brand) in seen_pairs:
                        continue  # dedup
                    seen_pairs.add((cat, brand))
                    match_count += 1
                    yield {'cat': cat, 'brand': brand, 'cells': cells, ...}
            elif in_row:
                buffer.append(line)

    print(f"Scanned {row_count} rows, found {match_count} matching items")
```

## Key Design Decisions

1. **Line-by-line, not full read:** `for line in f` instead of `f.read()` — memory stays ~tens of MB.
2. **Row accumulator:** `<ss:Row>` may span multiple lines. Accumulate in `buffer` list, join when `</ss:Row>` seen.
3. **Header on first row:** First data row after `<ss:Table>` is the header. Build column map.
4. **Dedup by (catalog, brand):** Use `seen_pairs` set — rejects duplicates of same (cat, brand) after first match.
5. **Early exit on `</ss:Table>`:** Don't scan entire file if data ends early.
6. **`flush=True` on prints:** Critical for background process output visibility.

## When to Use

| Scenario | Parser | Reason |
|----------|--------|--------|
| Full catalog regression (all items) | `parse_xml()` full load | Need all rows anyway |
| Focused re-test (mismatches only) | Streaming | Only ~40 items needed |
| XML >50MB | Streaming | Avoid OOM |
| XML <50MB | Either | Full load is fine |

## Performance

- 300MB / 493K lines: ~30-60s to scan (vs 60-120s+ for full regex)
- Memory: ~20MB (vs 500MB+ for full load)
- Output starts immediately as matches found (vs waiting for full parse)
