---
name: code-drawn-video-backgrounds
description: "Use when adding/verifying Remotion code-drawn backgrounds."
version: 1.0.0
---

# 代码绘制视频背景（Remotion 确定性动画元素）

给 Remotion 视频管线（prose-poetry-video、ai-weekly-video 等）新增/调试**代码绘制动态背景**：渐变底 + 剪影 + 光效 + 粒子 + 噪点的多层合成，全部用确定性伪随机，多帧渲染画面一致。

## 触发条件

- 用户要求给视频背景加元素（"加雨滴涟漪/落叶/极光/萤火虫/蒲公英飘絮"这类点菜）
- 新增 `--bg-style` 风格、调整粒子速度/密度、验证背景动效是否渲染
- 当前模型无视觉能力时（deepseek 系 + vision 回退模型拒图）验证任何动画产物

## 确定性组件模式（必须遵守）

- **伪随机**：`const seeded = (i, seed) => ((i * 137 + seed * 59) % 100) / 100;`，参数表 `Array.from({length: N}, (_, i) => ({...seeded 计算}))`。新元素的 seed 用 90-180 段，避免与既有元素冲突。**禁止 Math.random**（Remotion 多帧渲染会闪）。
- **运动三型**：下落/漂移 `(y0 + f*spd) % 范围` 循环；横漂 `x0 + sin(f*freq + phase)*amplitude`；闪烁 `sin` 呼吸（如萤火虫/风丝淡入淡出）。
- **速度系数参考表**（f 为帧号，30fps；系数是每帧位移占屏百分比）：
  | 元素 | 公式 | 效果 |
  |---|---|---|
  | 雨丝 | `f*0.02*spd`（spd 2-5）| 每秒 ~2-5% 屏高 |
  | 雪/微尘 | `f*0.004*spd` | 极慢漂浮（1.5px/s 级）|
  | 落叶 | `f*0.04*spd`（spd 1-3）| ~30-50s 飘完全屏 |
  | 云（快速）| `f*0.02*spd`（spd 6-18）| 高速横移，肉眼可辨 |
  | 萤火虫 | `f*0.004*spd` + 慢闪烁 | 悬停 + 呼吸 |
  | 草浪/波纹 | sin 相位 `f*speed`（0.05-0.1）| 每秒 0.3-0.5Hz 摇摆 |
- **分层渲染顺序**（CodeBg 组装）：底（渐变）→ 景（远山/树枝剪影）→ 光（月/日/极光）→ 粒（雨/雪/叶/虫）→ 雾 → 噪点。粒子一般叠在剪影之上、文字之下。
- **透明度余量**：暗角（0.15-0.62 径向）+ Grain 噪点会吃掉 ~40% 亮度。白色细线条（蒲公英绒毛/风丝）加 `drop-shadow` 光晕增强存在感；涟漪环用 2px 边框 + 内外 boxShadow。
- **SVG vs div**：SVG path 波浪（极光丝带/草浪）没问题；单粒子优先 div（绝对定位 + 百分比 left/top + rotate），别用 SVG 单元素——调试成本高收益低。

## 新增元素/风格四步流程

1. `Video.tsx`：加参数表 + 组件 + `CodeBg` 加 `case "styleName"`（注意上面分层顺序）
2. `poem_pipeline.py`：`--bg-style` 的 `choices` 列表 + help 文案同步加新值（漏了直接 argparse 报错）
3. `SKILL.md` 风格表加一行（效果 + 适合情绪）
4. **双帧差分验证**（见下）——渲染两帧确认元素在动，且动效分布符合预期（粒子在对应区域）

## 像素差分验证法（免视觉模型，核心）

半透明粒子叠在深色背景上**永远过不了绝对色值阈值**（"找白色/蓝色像素"会误报 0 = 没渲染；2026-08 实测误判 4 次，实际都渲染正常）。正确做法：

```bash
# 1. 测试 data.ts 写单风格段（如 0-240 帧），渲染同段两帧（间隔 30-90 帧）
npx remotion still poem --frame=60 out/A.png
npx remotion still poem --frame=150 out/B.png
# 2. 按区域统计 diff（脚本见 scripts/bg_diff_check.py）
python3 scripts/bg_diff_check.py out/A.png out/B.png \
  --bands "天空0-35%:0-0.35,中35-70%:0.35-0.70,水面70-100%:0.70-1.0"
```

判读：
- 静态背景/文字两帧不变 → 该区域 diff ≈ 0
- 元素所在区域 diff 数千-数万 → 在动 ✅
- **底部区域大 diff 是 Mist/Grain 常态**，别误判为元素动效
- 验证完**恢复原 data.ts**（先 `cp src/data.ts src/data.ts.bak`）

## 踩坑

1. **差分相位混叠**：sin 相位推进型元素（草浪 speed 0.07 × 90 帧差 = 6.3 rad ≈ 2π）两帧形状几乎相同 → diff 意外偏小 ≠ 元素不动。换帧间隔，或先算 `speed×帧差` 避开 2π 整数倍。
2. **模板与工作副本双写**：pipeline 只在项目目录不存在时复制模板（`if not project.exists()`），改了 `templates/` 必须手动 `cp` 到工作副本 `~/poem-video/src/` 才生效。
3. **argparse help 字符串 `%` 必须写成 `%%`**（如 `-20%/+10%`），否则 `--help` 崩 `ValueError: unsupported format character`（正常跑不触发 help 格式化，易潜伏）。
4. **静帧预览 vs 视频**：用户说"生成视频了吗"时，静帧 still ≠ 成品。出演示视频用 `npx remotion render <comp> out/x.mp4 --codec=h264`，单风格演示 12s / 全风格 36s 都行。
5. **WSL interop 禁用时无法从 WSL 调 Windows 播放器**（explorer.exe Exec format error）：交付用 markdown 文件链接（`[名](<D:/路径>)`），并告知修复命令（`wsl -u root sh -c "..." >> /etc/wsl.conf` + `wsl --shutdown`）让用户决定。

## 关联技能

- `prose-poetry-video`（user-owned）：12 种风格的完整表 + pipeline 用法，本技能的模式在其 Video.tsx 落地
- 本技能的方法论同样适用于 ai-weekly-video 等任何代码绘制背景管线
