#!/usr/bin/env python3
"""双帧像素差分: 无视觉模型时证明渲染帧里的元素存在且在动.

用法:
  python3 two_frame_diff.py frameA.png frameB.png \
      [--bands "天空:0-0.35,中:0.35-0.7,水面:0.7-1.0"] [--thresh 25]

前置(Remotion 示例, 同风格两帧间隔>=60帧):
  npx remotion still <composition-id> --frame=60 out/A.png
  npx remotion still <composition-id> --frame=150 out/B.png

判定:
  - 动的元素所在区域带 diff 显著 >0 (几千到几万), 静态背景/文字带 ~0
  - 全部带 ~0 = 元素未渲染或太慢/太暗(调参数重测)
  - 全部带都在动 = 大面积极动态层(雾/噪点)干扰, 缩小带或对比旧帧
依赖: PIL (pip install pillow)
"""
import argparse

from PIL import Image


def diff_bands(a_path: str, b_path: str, bands: dict, thresh: int) -> dict:
    ia = Image.open(a_path).convert("RGB")
    ib = Image.open(b_path).convert("RGB")
    assert ia.size == ib.size, f"两帧尺寸不一致: {ia.size} vs {ib.size}"
    w, h = ia.size
    pa, pb = ia.load(), ib.load()
    out = {}
    for bname, (y0, y1) in bands.items():
        n = 0
        for y in range(int(y0 * h), int(y1 * h)):
            for x in range(w):
                ra, ga, ba = pa[x, y]
                rb, gb, bb = pb[x, y]
                if abs(ra - rb) + abs(ga - gb) + abs(ba - bb) > thresh:
                    n += 1
        out[bname] = n
    return out


def main() -> None:
    ap = argparse.ArgumentParser(
        description="双帧像素差分: 按区域带统计两帧差异, 证明元素渲染且在动.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("a", help="帧A PNG")
    ap.add_argument("b", help="帧B PNG (与A同风格, 间隔>=60帧)")
    ap.add_argument("--bands", default="天空:0-0.35,中:0.35-0.7,水面:0.7-1.0",
                    help="区域带, 逗号分隔 name:y0-y1 (比例), 默认 天空/中/水面")
    ap.add_argument("--thresh", type=int, default=25,
                    help="RGB三通道绝对差之和阈值, 默认25")
    args = ap.parse_args()

    bands = {}
    for item in args.bands.split(","):
        name, rng = item.split(":")
        y0, y1 = rng.split("-")
        bands[name] = (float(y0), float(y1))

    res = diff_bands(args.a, args.b, bands, args.thresh)
    for name, n in res.items():
        print(f"  {name}: {n}")
    total = sum(res.values())
    print(f"总diff: {total}")
    near_zero = sum(1 for n in res.values() if n < 50)
    moving = sum(1 for n in res.values() if n > 500)
    if moving >= 1 and near_zero >= 1:
        print("判定: 元素在动 ✅ (局部带显著diff, 静态带~0)")
    elif total == 0:
        print("判定: 完全无差异 — 元素未渲染或两帧间静止")
    else:
        print("判定: 无法确认 — 所有带都在动(大动态层干扰?)或全部偏小(元素太慢/太暗?)")


if __name__ == "__main__":
    main()
