#!/usr/bin/env python3
"""框架协议商品智能审核Excel分析脚本。

用法:
    python3 analyze_excel_audit.py <excel_path>

输出:
    1. 总体有效性（一致率）
    2. AI vs 人工交叉矩阵（含双通道AI结论）
    3. 各目录一致率
    4. 不一致原因归类
    5. AI退回原因 vs 人工退回原因对比
"""

import sys
import pandas as pd


def norm_ai_conclusion(row):
    """标准化AI结论，优先AI审核结论，回退到AI结论type"""
    c = row.get('AI审核结论')
    t = row.get('AI结论type')
    if pd.notna(c) and str(c) not in ('\\N', '未知', 'nan'):
        return str(c)
    if pd.notna(t) and str(t) not in ('\\N', 'nan'):
        return '通过' if str(t) == '2' else ('退回' if str(t) == '-1' else '未知')
    return '未知'


def norm_human_conclusion(row):
    """标准化人工结论"""
    t = row.get('人工结论type')
    if pd.notna(t) and str(t) not in ('\\N', 'nan'):
        return '通过' if str(t) == '2' else ('退回' if str(t) == '-1' else '未知')
    op = str(row.get('人工操作名', '')) if pd.notna(row.get('人工操作名')) else ''
    if '通过' in op:
        return '通过'
    if '退回' in op:
        return '退回'
    return '未知'


def classify_ai_reject_reason(ai_reason):
    """分类AI不通过原因"""
    r = str(ai_reason) if pd.notna(ai_reason) else ''
    if not r or r == '\\N':
        return 'AI:LLM失败/无理由(FAILED会话)'
    if '无法' in r or '视觉审核' in r:
        return 'AI:图片审核失败/超时'
    if '包装' in r and ('不带包装' in r or '实物' in r):
        return 'AI:耗材缺实物图(全包装)'
    if '主图' in r and '数量' in r:
        return 'AI:主图数量不足'
    if '型号' in r and '不一致' in r:
        return 'AI:型号不一致'
    if '名称' in r:
        return 'AI:名称格式'
    if '参数' in r and '不一致' in r:
        return 'AI:参数不一致'
    if '室外机' in r:
        return 'AI:缺室外机'
    return 'AI:其他'


def classify_human_reject_reason(h_reason):
    """分类人工不通过原因"""
    r = str(h_reason) if pd.notna(h_reason) else ''
    if '名称' in r and ('修改' in r or '改为' in r):
        return '人工:名称格式修正'
    if '附件' in r and ('公章' in r or '加盖' in r):
        return '人工:附件盖章'
    if '附件' in r:
        return '人工:附件原因'
    if '图片' in r and ('水印' in r or '至少上传3张' in r or '主视图' in r):
        return '人工:图片规范(水印/数量)'
    if '室外机' in r:
        return '人工:室外机'
    if '核实' in r or '是否同步' in r:
        return '人工:核实信息'
    return '人工:其他'


def analyze(path):
    df = pd.read_excel(path, dtype=str)
    print(f"总行数: {len(df)}")
    print(f"列名: {list(df.columns)}")

    # 会话状态
    status = df['会话状态'].value_counts()
    print(f"\n会话状态: {dict(status)}")

    # 筛选已审核
    reviewed = df[df['结论一致性'].isin(['一致', '不一致'])].copy()
    pending = df[~df['结论一致性'].isin(['一致', '不一致'])]
    total = len(reviewed)
    match = len(reviewed[reviewed['结论一致性'] == '一致'])
    mismatch = total - match

    print(f"\n{'='*60}")
    print(f"总体有效性")
    print(f"{'='*60}")
    print(f"已审核: {total}, 待审核: {len(pending)}")
    print(f"一致: {match} ({match/total*100:.1f}%)")
    print(f"不一致: {mismatch} ({mismatch/total*100:.1f}%)")

    # 双通道标准化
    reviewed['AIc'] = reviewed.apply(norm_ai_conclusion, axis=1)
    reviewed['Hc'] = reviewed.apply(norm_human_conclusion, axis=1)

    print(f"\n{'='*60}")
    print(f"交叉矩阵")
    print(f"{'='*60}")
    ct = pd.crosstab(reviewed['AIc'], reviewed['Hc'], margins=True)
    print(ct)

    # 分目录
    print(f"\n{'='*60}")
    print(f"各目录一致率")
    print(f"{'='*60}")
    for cat in sorted(reviewed['采购目录'].unique()):
        cd = reviewed[reviewed['采购目录'] == cat]
        t = len(cd)
        m = len(cd[cd['结论一致性'] == '一致'])
        print(f"  {cat}: {t}条, 一致{m}({m/t*100:.1f}%), 不一致{t-m}({(t-m)/t*100:.1f}%)")

    # 不一致分析
    mismatch_df = reviewed[reviewed['结论一致性'] == '不一致']
    type_a = mismatch_df[mismatch_df['AIc'].isin(['退回', '不通过'])]  # AI退回人工通过
    type_b = mismatch_df[mismatch_df['AIc'] == '通过']  # AI通过人工退回

    print(f"\n{'='*60}")
    print(f"不一致: AI退回/不通过 但人工通过 ({len(type_a)}条)")
    print(f"{'='*60}")
    type_a_reasons = type_a['AI审核理由'].apply(classify_ai_reject_reason)
    print(type_a_reasons.value_counts())
    print(f"\n  目录分布: {dict(type_a['采购目录'].value_counts())}")

    print(f"\n{'='*60}")
    print(f"不一致: AI通过 但人工退回 ({len(type_b)}条)")
    print(f"{'='*60}")
    type_b_reasons = type_b['人工审核理由'].apply(classify_human_reject_reason)
    print(type_b_reasons.value_counts())

    # AI不通过原因汇总
    print(f"\n{'='*60}")
    print(f"AI不通过原因汇总 (AIc=退回/不通过, {len(reviewed[reviewed['AIc'].isin(['退回','不通过'])])}条)")
    print(f"{'='*60}")
    ai_all_reasons = reviewed[reviewed['AIc'].isin(['退回', '不通过'])]['AI审核理由'].apply(classify_ai_reject_reason)
    print(ai_all_reasons.value_counts())


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 analyze_excel_audit.py <excel_path>")
        sys.exit(1)
    analyze(sys.argv[1])
