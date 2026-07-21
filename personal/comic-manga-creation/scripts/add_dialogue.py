#!/usr/bin/env python3
"""《圆的囚徒》自动对话气泡 — 面板布局驱动，无需手动坐标

基于分镜稿的面板布局自动定位气泡和旁白框。
修改 PAGES 字典适配其他漫画项目。

用法: python3 add_dialogue.py [page_ids...]
      不传参数则处理全部 01-10 页

依赖: Pillow, CJK字体(WenQuanYi Zen Hei)

气泡类型:
  N = 旁白框 (深灰矩形 + 白字)
  S = 对话气泡 (白色椭圆 + 黑字 + 角色标签)
  H = 愤怒锯齿气泡 (红色锯齿 + 白字)
"""

from PIL import Image, ImageDraw, ImageFont
import os, random

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
]
FONT_PATH = next((f for f in FONT_CANDIDATES if os.path.exists(f)), None)

PROJ = os.path.dirname(os.path.abspath(__file__))  # comic project root

# ── 面板布局 (基于 768×1024 画布) ──
LAYOUTS = {
    "2panels": [(0, 0, 768, 512), (0, 512, 768, 512)],
    "3panels": [(0, 0, 768, 500), (0, 500, 384, 524), (384, 500, 384, 524)],
    "4panels": [(0, 0, 384, 340), (384, 0, 384, 340), (0, 340, 768, 340), (0, 680, 768, 344)],
    "5panels": [(0, 0, 384, 300), (384, 0, 384, 300), (0, 300, 768, 300),
                (0, 600, 384, 424), (384, 600, 384, 424)],
}

SPEAKER_COLORS = {
    "林正则": "#3B82F6", "沈远": "#D97706", "赵之恒": "#DC2626",
    "何玥": "#10B981", "学者": "#6B7280", "学生": "#8B5CF6", "审判长": "#4B5563",
}

# ── 每页对话数据 (覆盖你自己的漫画) ──
# text: { panel_index: [(type, text, speaker), ...] }
PAGES = {
    "01": {"layout": "3panels", "texts": {0: [("N", "凌晨2:47")]}},
    "02": {"layout": "4panels", "texts": {
        1: [("N", "第37次。一样。")],
        2: [("S", "你确定？", "沈远"), ("S", "我确定。", "林正则")],
        3: [("S", "我已经沉默过一次了。\n这次，我陪你。", "沈远")],
    }},
    "03": {"layout": "3panels", "texts": {
        0: [("N", "旋臂异常消失了。\n干干净净。")],
        1: [("N", "大自然一直在用它。")],
        2: [("S", "你会后悔的。", "赵之恒"), ("S", "真理应该经得起检验。", "林正则")],
    }},
    "04": {"layout": "4panels", "texts": {
        0: [("N", "第142届学术年会。\n这座穹顶本身，就是一个\n错误的纪念碑。")],
        2: [("S", "ξ=3.14？\n开什么玩笑...", "学者")],
        3: [("S", "请允许我做现场实验。", "林正则")],
    }},
    "05": {"layout": "5panels", "texts": {
        3: [("H", "这是测量误差！\n你选择性地报告数据！", "赵之恒")],
        4: [("N", "他想反驳。\n但他没有说出口。")],
    }},
    "06": {"layout": "4panels", "texts": {
        0: [("N", "终身不得从事研究工作。")],
        1: [("S", "你还要走下去。", "沈远")],
        2: [("S", "终极之圆测量计划。", "何玥")],
        3: [("N", "他写得很好。\n无懈可击。")],
    }},
    "07": {"layout": "3panels", "texts": {
        2: [("S", "谢谢你。", "林正则"), ("S", "别谢我，谢ξ吧。", "何玥")],
    }},
    "08": {"layout": "4panels", "texts": {
        2: [("N", "数据已发送至6家媒体")],
        3: [("S", "你发出了什么？", "赵之恒"), ("S", "真相。", "林正则")],
    }},
    "09": {"layout": "5panels", "texts": {
        0: [("S", "剥夺学术身份，\n终身不得从事研究工作。", "审判长")],
        2: [("N", "有一种默契，\n不需要语言。")],
        3: [("N", "30年后。S = πr²。")],
        4: [("N", "『我不恨他们。\n他们也只是\n错误的囚徒。』")],
    }},
    "10": {"layout": "2panels", "texts": {
        0: [("S", "老师，这是什么意思？", "学生"),
            ("N", "没什么。只是一个数字。")],
        1: [("N", "处处是圆。\n处处是那个数字。"),
            ("N", "— 圆的囚徒 · 完 —")],
    }},
}


def draw_narration(draw, panel, text):
    """旁白框: 深灰半透明 + 白字 + 粗边框, 面板顶部居中"""
    px, py, pw, ph = panel
    font = ImageFont.truetype(FONT_PATH, 28)
    lines = text.split('\n')
    lh = 38
    max_w = max(draw.textbbox((0, 0), l, font=font)[2] for l in lines)
    bw = min(pw - 60, max_w + 50)
    bh = lh * len(lines) + 30
    x, y = px + (pw - bw) // 2, py + 20
    draw.rounded_rectangle([x, y, x + bw, y + bh], radius=12,
                          fill=(45, 55, 72, 235), outline=(156, 163, 175, 255), width=3)
    ty = y + 12
    for line in lines:
        tw = draw.textbbox((0, 0), line, font=font)[2]
        draw.text((x + (bw - tw) // 2, ty), line, fill=(255, 255, 255, 255), font=font)
        ty += lh


def draw_speech(draw, panel, text, speaker, is_shout=False):
    """对话气泡: 白色/红色 + 尾巴 + 角色名标签"""
    px, py, pw, ph = panel
    font = ImageFont.truetype(FONT_PATH, 28)
    font_lbl = ImageFont.truetype(FONT_PATH, 20)
    color = SPEAKER_COLORS.get(speaker, "#6B7280")
    lines = text.split('\n')
    lh = 38
    max_w = max(draw.textbbox((0, 0), l, font=font)[2] for l in lines)
    bw = min(pw - 40, max_w + 80)
    bh = lh * len(lines) + 40
    x = px + (pw - bw) // 2
    y = py + 15

    if is_shout:
        jw = [random.randint(-8, 8) for _ in range(100)]
        jh = [random.randint(-8, 8) for _ in range(100)]
        jagged = []
        step = 20
        for px2 in range(x, x + bw, step):
            jagged.append((px2 + jw[len(jagged) % 100], y + jh[len(jagged) % 100]))
        jagged.append((x + bw + jw[len(jagged) % 100], y + jh[len(jagged) % 100]))
        for py2 in range(y, y + bh, step):
            jagged.append((x + bw + jw[len(jagged) % 100], py2 + jh[len(jagged) % 100]))
        jagged.append((x + bw + jw[len(jagged) % 100], y + bh + jh[len(jagged) % 100]))
        for px2 in range(x + bw, x, -step):
            jagged.append((px2 + jw[len(jagged) % 100], y + bh + jh[len(jagged) % 100]))
        jagged.append((x + jw[len(jagged) % 100], y + bh + jh[len(jagged) % 100]))
        for py2 in range(y + bh, y, -step):
            jagged.append((x + jw[len(jagged) % 100], py2 + jh[len(jagged) % 100]))
        draw.polygon(jagged, fill=(255, 255, 255, 245), outline=(220, 38, 38, 255), width=3)
    else:
        draw.rounded_rectangle([x, y, x + bw, y + bh], radius=18,
                              fill=(255, 255, 255, 242), outline=(26, 32, 44, 255), width=3)

    # Tail
    tc = x + bw // 2
    ty = y + bh
    tail = [(tc - 12, ty), (tc + 12, ty), (tc, ty + 28)]
    draw.polygon(tail, fill=(255, 255, 255, 242), outline=(26, 32, 44, 255), width=3)
    draw.line([(tc - 10, ty), (tc + 10, ty)], fill=(255, 255, 255, 242), width=5)

    # Text + speaker label
    ly = y + 15
    for line in lines:
        tw = draw.textbbox((0, 0), line, font=font)[2]
        draw.text((x + (bw - tw) // 2, ly), line, fill=(26, 32, 44, 255), font=font)
        ly += lh
    if speaker:
        lbl = f"— {speaker}"
        lw = draw.textbbox((0, 0), lbl, font=font_lbl)[2]
        draw.text((x + bw - lw - 10, y + bh - font_lbl.size - 8),
                 lbl, fill=(107, 114, 128, 255), font=font_lbl)


def process_page(pid):
    img_path = os.path.join(PROJ, f'{pid}-page.png')
    if not os.path.exists(img_path):
        return f"FILE MISSING: {img_path}"
    img = Image.open(img_path).convert('RGBA')
    draw = ImageDraw.Draw(img)
    page = PAGES.get(pid, {})
    layout = LAYOUTS.get(page.get('layout', '3panels'), LAYOUTS['3panels'])
    for pi, items in page.get('texts', {}).items():
        if pi >= len(layout): continue
        panel = layout[pi]
        for item in items:
            ttype, text = item[0], item[1]
            speaker = item[2] if len(item) > 2 else ""
            if ttype == "N":
                draw_narration(draw, panel, text)
            elif ttype == "H":
                draw_speech(draw, panel, text, speaker, is_shout=True)
            else:
                draw_speech(draw, panel, text, speaker)
    out = os.path.join(PROJ, f'{pid}-final.png')
    img.save(out)
    return f"OK → {pid}-final.png"


if __name__ == '__main__':
    import sys
    pids = sys.argv[1:] if len(sys.argv) > 1 else [f"{i:02d}" for i in range(1, 11)]
    if not FONT_PATH:
        print("ERROR: No CJK font found. Install wqy-zenhei or set FONT_PATH.")
        sys.exit(1)
    for pid in pids:
        print(f"  {pid}: {process_page(pid)}")
    print("Done!")
