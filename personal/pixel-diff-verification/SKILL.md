---
name: pixel-diff-verification
description: "无视觉模型时用双帧像素差分验证渲染帧。Use when no vision model."
version: 1.0.0
---

# 无视觉模型时的像素级验证（Pixel-Diff Verification）

验证「代码绘制的图片/动画帧/截图里，某个元素真的渲染出来且在动」，但当前模型无原生视觉、或 vision_analyze 回退模型拒图（如 deepseek-v4-flash + 文本-only 回退）时，用 PIL 像素分析替代肉眼。

## 触发条件

- 生成了图片/视频帧/动画截图，需要确认元素（粒子、光效、文字、形状）真实存在
- vision_analyze 报错（`unknown variant image_url` / 400）或模型不支持看图
- 不想只靠"渲染成功"就声称完成——需要客观证据

## 核心技巧 1：双帧差分（首选，免疫阈值问题）

同一场景渲染**两帧**（间隔 ≥60 帧，让动画元素明显位移），逐像素比较，按**区域带**统计差异：

```python
from PIL import Image
ia = Image.open("frameA.png").convert("RGB")
ib = Image.open("frameB.png").convert("RGB")
pa, pb = ia.load(), ib.load()
w, h = ia.size
# 按区域带(y0..y1 比例)统计 diff>阈值 的像素数
diff = sum(1 for y in range(int(0.7*h), h) for x in range(w)
           if abs(pa[x,y][0]-pb[x,y][0])+abs(pa[x,y][1]-pb[x,y][1])+abs(pa[x,y][2]-pb[x,y][2]) > 25)
```

判定逻辑：
- **动的元素** → 其所在区域带 diff 显著 >0（几千到几万）
- **静态背景/文字** → 对应带 ≈0
- diff 带分布 = 元素位置 → 同时证明「渲染了」且「在工作」
- 若某带 0 而预期元素在那 → 元素没渲染或太慢/太暗（调参数后重测）
- 注意：既有的大面积动态层（如底部雾、胶片噪点）会吞掉该带所有 diff，判断时排除或对比同风格旧帧

Remotion 取帧命令（无需全片渲染）：

```bash
npx remotion still <composition-id> --frame=60 out/A.png
npx remotion still <composition-id> --frame=150 out/B.png
```

可复用脚本：`scripts/two_frame_diff.py`（传两帧 + 区域带 + 阈值，打印各带 diff）。

## 核心技巧 2：颜色阈值探针为什么骗人（误报"没渲染"）

按原始色值设阈值数像素（如 `r>130 and g>80 and b<115`）会**大面积误报**。原因：alpha 叠加链——

```
元素填充(0.85-0.95 alpha) × 组件 opacity(0.4-0.9) × 暗角(径向 0.15-0.62 黑) × 胶片噪点 overlay
```

实测：源色 (216,158,88) 的元素在成片里渲染成 (128,64,32) 左右——**比原始色值暗 40-60%**。本会话落叶/涟漪都被阈值探针报过"0 像素没渲染"，实际都在渲染。

- 用阈值探针时，先按预期色值的 40-60% 亮度下限设宽松阈值（`r>90 and g>60` 级别），或干脆用双帧差分
- 配一个**对照组**（已知不含该元素的风格帧）比同阈值，排除背景本身撞色（如绿色渐变底会虚增"极光绿"计数）

## 核心技巧 3：最小隔离（定位"组件没渲染" vs "被图层盖住"）

在完整合成里猜根因浪费时间。把可疑组件抽到独立文件，Root.tsx 注册**第二个 Composition**（纯黑背景、单帧渲染），再对该帧做颜色直方图：

```python
from collections import Counter
c = Counter()
for y in range(h):
    for x in range(w):
        r,g,b = px[x,y]
        if r>60 or g>60 or b>60:
            c[(r//32*32, g//32*32, b//32*32)] += 1
print(c.most_common(10))  # 出现元素色桶 = 组件渲染正常
```

黑底上直方图有元素色桶 → 组件没问题，问题在整片合成的层级/暗角/阈值。黑底上什么都没有 → 组件代码本身不渲染（查 JSX 结构、尺寸为 0、overflow 裁剪、被上层全屏 div 遮住）。

## 给用户交付

- 静态帧图看不出动效，交付预览图时说明"单帧偏暗是暗角压制，动态才显眼"，建议用户跑段短视频看动效
- **新增动效后主动渲染 demo MP4**（用户会问"视频呢"）：临时 data.ts 每风格 5-6s 一段，音频复用 `public/parts/seg_*.mp3`，`npx remotion render poem out/x.mp4 --codec=h264`，渲染完恢复 data.ts.bak
- 预览图/视频复制到用户 Windows 可见目录（本机惯例 `D:\平时处理文件\` 下建子目录），用 Markdown 路径引用（`<D:/...>` 尖括号包裹）
- WSL interop 不可用（`explorer.exe`/`cmd.exe` 报 Exec format error、`/proc/sys/fs/binfmt_misc/WSLInterop` 不存在）→ 无法从 WSL 拉起 Windows 播放器，直接给 Windows 路径链接让用户点，别反复尝试打开

## 踩坑

- **防相位混叠**：两帧间隔若 ≈ 运动周期整数倍，diff 会异常小但动画实际一直在动（实测草浪 `speed 0.07 × 90帧差 ≈ 2π`，两帧几乎同相，diff 从 2.6万 骤降到 8千）。遇到"diff 莫名小"先检查 `帧差 × 角速度` 是否 ≈ 2π 整数倍，换帧间隔再测
- **粒子速度**：`y = f * 0.006 * spd` 在 30fps 下 10 秒只动几像素，元素全堆顶部——粒子下落/漂移系数用 0.02~0.05 量级，出生 y0 撒开到 -10..60%
- **单帧"存在"≠"在动"**：静态元素两帧 diff 为 0，务必双帧差分而不是单帧阈值
- argparse CLI 的 `--help` 崩 "unsupported format character" = help 文本里有裸 `%`（如 `-20%/+10%`），转义成 `%%`
- 改完代码必须重新构建/同步再渲染验证，否则验证的是旧产物
- Remotion 流水线只在项目目录不存在时复制模板：改 `templates/.../src/Video.tsx` 后必须手动 `cp` 到工作副本（如 `~/poem-video/src/`），否则渲染用旧代码
