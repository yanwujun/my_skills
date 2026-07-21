"""
Shared XML parser for 框架协议商品智能审核 test data.
Reads Excel SpreadsheetML XML, extracts rows with named column access.

Usage:
    import sys; sys.path.insert(0, '/path/to/skill/scripts')
    from data_parser import parse_xml, stream_parse, norm, select_items

    # Full parse (loads entire 300MB into memory, ~30s)
    rows = parse_xml('/path/to/061601.xml')

    # Streaming parse (line-by-line, ~15s, ~20MB RAM, supports filtering)
    for r in stream_parse('/path/to/061601.xml', targets={("目录","品牌")}):
        print(r['cat'], r['brand'])
"""

import re
import html


def _parse_cells(row_xml):
    """Extract cell values from a <ss:Row> XML fragment."""
    return [html.unescape(d) for d in re.findall(r'<Data[^>]*>(.*?)</Data>', row_xml, re.DOTALL)]


def _build_header(rows):
    """Build column name -> index map from header row."""
    hdr = _parse_cells(rows[0])
    return {hdr[i]: i for i in range(len(hdr))}


def _make_getter(header_map, cells):
    """Return a closure to access cell value by column name."""
    def g(field):
        i = header_map.get(field, -1)
        return cells[i].strip() if 0 <= i < len(cells) else ''
    return g


def parse_xml(xml_path):
    """
    Full in-memory parse. Suitable for <50MB files.
    For 300MB files, prefer stream_parse().

    Returns list of dicts with keys:
        cat, brand, model, scenario, fidelity, fast, human,
        ai_reason, human_reason, audit_request_json

    fast = ai_audit_result_code (-1/0=退回, 2=通过)
    human = human_audit_result (0=退回, 1=通过)
    """
    with open(xml_path, encoding='utf-8') as f:
        xc = f.read()

    ws = xc.find('<ss:Table>')
    we = xc.find('</ss:Table>', ws)
    if we == -1:
        we = len(xc)

    rows = re.findall(r'<ss:Row>(.*?)</ss:Row>', xc[ws:we+11], re.DOTALL)
    if not rows:
        return []

    header_map = _build_header(rows)
    result = []

    for row_xml in rows[1:]:
        cells = _parse_cells(row_xml)
        if not cells or len(cells) < 32:
            continue

        g = _make_getter(header_map, cells)
        cat = g('base_catalog')
        aj = g('audit_request_json')
        if not cat or len(aj) < 10:
            continue

        result.append({
            'cat': cat,
            'brand': g('base_brand'),
            'model': g('base_model'),
            'scenario': g('training_scenario'),
            'fidelity': g('data_label_fidelity'),
            'fast': g('ai_audit_result_code'),
            'human': g('human_audit_result'),
            'ai_reason': g('ai_audit_reason'),
            'human_reason': g('human_audit_reason'),
            'audit_request_json': aj,
        })

    return result


def stream_parse(xml_path, targets=None, fidelity_filter=None):
    """
    Streaming line-by-line parser for large XML files (300MB+).
    O(n) single pass, ~20MB RAM.

    Args:
        xml_path: Path to the Excel XML file.
        targets: Optional set of (catalog, brand) tuples to filter.
                 Only matching rows are yielded. If None, yields all rows.
        fidelity_filter: Optional 'HIGH'/'MEDIUM'/'LOW' to filter.

    Yields dicts with keys: cat, brand, model, scenario, fidelity,
        fast, human, ai_reason, human_reason, audit_request_json
    """
    header_map = None
    buffer = []
    in_row = False
    in_table = False
    seen_pairs = set()

    with open(xml_path, encoding='utf-8') as f:
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

                cells = _parse_cells(row_text)
                if not cells or len(cells) < 32:
                    continue

                if header_map is None:
                    header_map = {cells[i]: i for i in range(len(cells))}
                    continue

                g = _make_getter(header_map, cells)
                cat = g('base_catalog')
                brand = g('base_brand')
                aj = g('audit_request_json')

                if not cat or len(aj) < 10:
                    continue

                fidelity = g('data_label_fidelity')
                if fidelity_filter and fidelity != fidelity_filter:
                    continue

                if targets is not None:
                    key = (cat, brand)
                    if key not in targets:
                        continue
                    if key in seen_pairs:
                        continue
                    seen_pairs.add(key)

                yield {
                    'cat': cat,
                    'brand': brand,
                    'model': g('base_model'),
                    'scenario': g('training_scenario'),
                    'fidelity': fidelity,
                    'fast': g('ai_audit_result_code'),
                    'human': g('human_audit_result'),
                    'ai_reason': g('ai_audit_reason'),
                    'human_reason': g('human_audit_reason'),
                    'audit_request_json': aj,
                }

            elif in_row:
                buffer.append(line)


def norm(v):
    """Normalize audit result values to '0' or '1'."""
    v = str(v).strip()
    if v in ('-1','0','退回','审核不通过','不通过','智能审核退回','否','FAIL','fail','reject','False'):
        return "0"
    if v in ('2','1','通过','审核通过','PASS','pass','True','true'):
        return "1"
    return v


def select_items(rows, per_scenario=3):
    """
    Brand-dedup selection: pick per_scenario items per (catalog, scenario).
    Prefers HIGH fidelity items first.

    Returns list of selected items.
    """
    groups = {}
    for r in rows:
        key = (r['cat'], r['scenario'])
        if key not in groups:
            groups[key] = []
        groups[key].append(r)

    selected = []
    for (cat, scenario), items in sorted(groups.items()):
        high = [r for r in items if r.get('fidelity') == 'HIGH']
        pool = high if high else items
        seen = set()
        picked = []
        for r in pool:
            if len(picked) >= per_scenario:
                break
            if r['brand'] not in seen:
                picked.append(r)
                seen.add(r['brand'])
        for r in pool:
            if len(picked) >= per_scenario:
                break
            if r not in picked:
                picked.append(r)
        selected.extend(picked[:per_scenario])
    return selected
