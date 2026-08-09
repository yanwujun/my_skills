#!/usr/bin/env python3
"""双帧像素差分验证：确认 Remotion 代码背景的动态元素确实在渲染（无需视觉模型）。

背景：半透明粒子（雨丝/涟漪/飘絮/风丝）叠在深色背景上永远过不了绝对色值阈值
（"找白色像素"会误报 0 = 没渲染）。正确做法：同段渲染两帧，静态背景/文字不动，
只有动态元素所在区域产生 diff。

用法：
  python3 bg_diff_check.py <frameA.png> <frameB.png> \
    --bands "天空0-35%:0-0.35,中35-70%:0.35-0.70,水面70-100%:0.70-1.0" \
    --thresh 25

判读：
- 元素所在区域 diff 数千-数万 = 在动 ✅；静态区应 ≈ 0
- 底部区域大 diff 是 Mist/Grain 常态，别误判为元素动效
- 若某元素 diff 意外偏小：检查相位混叠（f×speed ≈ 2π 整数倍，见 SKILL.md 踩坑1），换帧间隔重测
"""
import argparse

from PIL import Image


def main():
    ap = argparse.ArgumentParser(description="双帧像素差分验证动画元素")
    ap.add_argument("frame_a", help="同段第 1 帧 PNG")
    ap.add_argument("frame_b", help="同段第 2 帧 PNG（间隔 30-90 帧）")
    ap.add_argument("--bands", default="全图:0-1.0",
                    help="区域列表 name:y0-y1 逗号分隔, y 为 0-1 比例, 如 '天空:0-0.5,水面:0.7-1.0'")
    ap.add_argument("--thresh", type=int, default=25,
                    help="RGB 和差阈值(默认25)")
    args = ap.parse_args()

    ia = Image.open(args.frame_a).convert("RGB")
    ib = Image.open(args.frame_b).convert("RGB")
    if ia.size != ib.size:
        raise SystemExit(f"尺寸不一致: {ia.size} vs {ib.size}")
    w, h = ia.size
    pa, pb = ia.load(), ib.load()

    print(f"帧A={args.frame_a} 帧B={args.frame_b} 尺寸={w}x{h} 阈值={args.thresh}")
    total = 0
    for band in args.bands.split(","):
        name, _, yrange = band.partition(":")
        y0s, y1s = yrange.split("-")
        y0, y1 = float(y0s), float(y1s)
        n = 0
        for y in range(int(y0 * h), int(y1 * h)):
            for x in range(w):
                ra, ga, ba = pa[x, y]
                rb, gb, bb = pb[x, y]
                if abs(ra - rb) + abs(ga - gb) + abs(ba - bb) > args.thresh:
                    n += 1
        total += n
        print(f"  {name} (y {y0:.0%}-{y1:.0%}): {n}")
    print(f"总 diff: {total}")
    print("解读: 元素区数千+ = 在动; 静态区≈0; 底部/全屏大diff多为Grain/Mist常态")


if __name__ == "__main__":
    main()
