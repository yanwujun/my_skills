# Item Selection Strategy: Brand-Dedup 5-per-Catalog

## Problem

When testing multiple items per catalog, selecting items with the **same brand** produces redundant results (same terminating rules fire, same image patterns). For meaningful coverage, each catalog needs items spanning different brands — but most catalogs are dominated by 1-2 large suppliers.

## Strategy: Brand-Deduplicated Top-N

1. **Sort by `data_label_fidelity`** — HIGH first (reliable gold standard)
2. **Collect items cycling through distinct brands** — pick one per brand before doubling up
3. **Count = 5** — enough for statistical signal without overwhelming the API

## Implementation

```python
ITEMS_PER_CAT = 5

for cat in target_catalogs:
    items = [r for r in all_data if g(r, 'base_catalog') == cat and g(r, 'data_label_fidelity') == 'HIGH']
    
    # Pass 1: one per unique brand
    selected = []
    seen_brands = set()
    for r in items:
        br = g(r, 'base_brand')
        if br not in seen_brands and len(selected) < ITEMS_PER_CAT:
            selected.append(r)
            seen_brands.add(br)
    
    # Pass 2: fill remaining slots (if fewer than 5 distinct brands)
    if len(selected) < ITEMS_PER_CAT:
        for r in items:
            if r not in selected and len(selected) < ITEMS_PER_CAT:
                selected.append(r)
    
    cat_items[cat] = selected[:ITEMS_PER_CAT]
```

## Why 5 (not 10)

| Factor | 5 items | 10 items | Rationale |
|--------|:-------:|:--------:|-----------|
| API calls per catalog | 5 | 10 | Linear savings |
| Brand diversity | Same strategy | Same strategy | 5 already covers most catalogs' distinct brands |
| Statistical confidence | Sufficient for pass/fail patterns | Higher | 5 is adequate for identifying problem categories |
| Total for 37 catalogs | 185 calls | 370 calls | ~2-3h vs ~5-6h wall time |

## Edge Cases

- **Catalogs with < 5 distinct brands** (e.g. 家具 dominated by 宝地文亿): Fill remaining slots with same-brand items. Accept lower brand diversity in the report.
- **Catalogs with < 5 HIGH items total** (e.g. 其他打印机(证卡) with 7 HIGH): Take all available, note the reduced sample in the report.
- **Catalogs with 0 HIGH items**: Skip entirely — LOW/MEDIUM fidelity labels are not reliable as gold standards.
