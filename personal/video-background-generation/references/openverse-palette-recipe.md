# Openverse 照片色板配方（免 key，2026-08 实测）

完整可复现配方：Openverse 搜 CC0 真实照片 → 下载 → PIL 提 HSL 色板 → 像素级验证注入。

## API 要点

- 端点：`https://api.openverse.org/v1/images/?q=<query>&license=cc0&page_size=5&aspect_ratio=wide`
- **匿名免 key**；`license=cc0` 过滤纯 CC0（零署名负担，B站 可发）
- `aspect_ratio=wide` 适配 16:9 视频背景
- ⚠️ **拒绝 urllib 默认 UA**：`Python-urllib/3.12` → 403；`Mozilla/5.0` / `curl/8.5.0` / 空 UA → 200。脚本一律 subprocess 调 curl
- ⚠️ 国内直连被墙，走代理：`-x http://127.0.0.1:8888`（用户环境 sing-box）
- 返回 `results[]`：`url`（flickr/wikimedia 高清直链，`_b.jpg` 后缀为中等尺寸）、`title`、`creator`、`license`
- 搜索词无结果时回退默认词 `nature landscape moody`（实测 "aurora night" 首轮可能无健康图，靠候选循环兜住）

## 中文意境词 → 英文搜索词映射

| 中文 | 英文 |
|---|---|
| 雾 | misty forest / foggy mountain / morning mist |
| 山 | mountain lake / valley sunrise |
| 雨 | rainy window / rain drops bokeh |
| 雪 | snow forest / winter landscape |
| 花 | cherry blossom / flower field |
| 月 | moon night / full moon clouds |
| 星 | starry sky milky way / night stars |
| 城 | city night lights / city skyline night |
| 海 | ocean waves sunset / sea horizon |
| 秋 | autumn leaves / autumn forest |
| 极光 | aurora borealis / aurora night |
| 云 | clouds sunset / sky clouds golden |
| 落/夕 | sunset horizon / dusk landscape |
| 林 | forest path / green forest |
| 江/桥 | river sunset / lake reflection |
| 晨 | morning light / sunrise field |
| 默认 | nature landscape moody |

## 色板提取（PIL）

```python
from PIL import Image
img = Image.open(path).convert("RGB")
img.thumbnail((160, 160))                      # 缩略加速
q = img.quantize(colors=20, method=Image.MEDIANCUT)
pal_raw = q.getpalette()
# 统计桶占比 → 排序 → 合并相近色(色相差<18 且亮度差<12) → 过滤 l<6 纯黑
# RGB→HLS: colorsys.rgb_to_hls(r/255, g/255, b/255) → h*360, l*100, s*100
```

**健康度筛选**（必须）：`max(l) >= 12 且 (max(l)-min(l)) >= 8`，否则跳过该候选。
Openverse 排序不保证第一张质量（实测首张命中过全黑夜图，色板全黑不可用）。
流程：拉 5 张候选 → 逐张下载提色板 → 第一张健康者胜出。

## 像素级验证（无视觉模型时）

vision_analyze 在 deepseek 系后端报 `unknown variant image_url`（拒图），别重试。用色相直方图：

```python
from PIL import Image
import colorsys
im = Image.open("frame.png").convert("RGB").resize((320, 180))
hues = {"蓝紫(210-270)": 0, "绿黄(50-110)": 0, "青(150-200)": 0, "暖白": 0, "其他": 0}
for r, g, b in im.getdata():
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    hd = h * 360
    if l > 0.75 and s < 0.25: hues["暖白"] += 1
    elif 210 <= hd <= 270: hues["蓝紫(210-270)"] += 1
    elif 50 <= hd <= 110: hues["绿黄(50-110)"] += 1
    elif 150 <= hd <= 200: hues["青(150-200)"] += 1
    else: hues["其他"] += 1
# 期望主导桶与注入色板一致
```

实测锚点：极光色板帧 → 蓝紫 99%；雾林色板帧 → 绿黄 96%；默认兜底帧 → 蓝紫 99%。

## Remotion 测试渲染

- `npx remotion still poem out.png --frame=N` 出测试帧：**不读音频文件**，缺 mp3 也能渲染
- `npx remotion render poem out.mp4 --frames=0-59`：**读音频**，缺 `public/parts/seg_NN.mp3` 报 readFile 错
- 先造静音占位：`ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 5 -q:a 9 parts/seg_01.mp3`
- 测试项目可软链已有 node_modules：`ln -sfn ~/poem-video/node_modules <test>/node_modules`，免 npm install

## 产物格式

```json
{"query": "misty forest", "source": "openverse", "image_url": "...",
 "license": "cc0", "creator": "Dmitry Grey",
 "palette": [[93, 39, 10], [98, 61, 6], [79, 12, 26], [57, 85, 29], [78, 31, 15]]}
```

图片默认不保留（只留几 KB 的 json），`--save-img` 才留原图。
