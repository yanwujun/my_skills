---
name: video-background-generation
description: "视频背景生成与提质：无缝循环决策框架+无key路线(Z-Image+ESRGAN)。触发:视频背景/背景提质。"
---

# 视频背景生成与提质

触发：用户问「背景怎么更高级/更唯美/更真实」「视频背景用什么」「生成背景图/背景视频」「背景要更好看」。适用于用户的散文诗视频（prose-poetry-video）和 AI 周报视频（ai-weekly-video）两条 Remotion 流水线。

## 核心决策框架（先判断再选方案）

视频背景的硬需求，按优先级：

1. **无缝循环** — 背景要能无限循环；录屏（WebGL 流体）、AI 视频片段（可灵/即梦）、实拍素材都难做到，代码生成天然循环
2. **确定性伪随机** — 重渲染不闪变（Remotion 逐帧合成必须；录屏/AI 生成都做不到）
3. **任意分辨率** — 4K 不糊
4. **情绪可控** — 随文案段落换色调/风格
5. **零版权风险**

**结论：代码生成背景（Remotion Canvas/CSS）在这些维度全面胜出。** GitHub 上的壁纸生成器项目（WebGL-Fluid-Simulation 录屏、uiGradients/webgradients 渐变工具站、AI 壁纸站）对「视频背景」用途是降级方案：静态图项目不产动态，录屏不可无缝循环、分辨率受限、颜色随机漂移不可控。用户现有代码背景：散文诗 pipeline 12 种 `--bg-style`（flow/bokeh/dust/rain/snow/city/starry/autumn/aurora/fireflies/dandelion/summerbreeze），AI 周报 pipeline 的 GradientBg/Particles 等组件。

想要新效果（流体/熔岩/水墨）→ **在 Remotion 里写 Canvas 组件**（保持无缝+确定性），不要用 WebGL 项目录屏。

## 真实感提质路径（全免费、无 key）

**用户偏好（2026-08 明确）：背景提质不用本地 AI 模型、不要 key。** 先走照片色板路线，Z-Image/FLUX 本地模型只作备选、不主动推荐。

### 首选：照片色板 + 算法渲染（最强组合，2026-08 落地）

真实照片提取主色板 → 代码渲染层全部用色板取色 → **运动逻辑一行不动**（无缝循环/确定性全保留）。真实感来自照片色调，循环来自代码动画——录屏和 AI 生成都做不到「又真又能循环」。

```
Openverse 免key搜 CC0 照片 (license=cc0 零署名, B站安全) → PIL 中位切分提 5 主色
→ HSL 色板 [[h,s,l],...] → 组件 P(pal, i, lAdj, sAdj, alpha, hueShift) 取色
```

- 完整实现：prose-poetry-video skill `scripts/openverse_palette.py` + `--palette-dir` 注入 + `Video.tsx` P() helper（12 风格全 palette 驱动）
- 踩坑：Openverse 拒 urllib UA（403，走 curl/Mozilla UA）；色板健康度筛选（max_l≥12 且明暗差≥8，跳过全黑图，试 5 候选）；有物理语义颜色（月亮/雪/落叶）不随色板走
- 无视觉模型验证：PIL 色相直方图分桶（蓝紫 210-270/绿黄 50-110），实测极光帧蓝紫 99%、雾林帧绿黄 96%
- 详细配方：`references/openverse-palette-recipe.md`

### 备选：本地 AI 生成（用户已拒绝，仅记录）

代码背景 → 本机 ComfyUI 生成意境图 → Real-ESRGAN 超分 → Ken Burns 动态化：

1. **Z-Image-Turbo NVFP4**（首选）：阿里 6B DiT，6GB 显存可跑（RTX 3050：~55s/张 512×768，VRAM ~5GB），**原生中文提示词**，国风/水墨/唯美是强项。教程+模板在 comfyui skill：`references/z-image-turbo-nvfp4-setup.md`、`templates/z_image_turbo_nvfp4.json`（API 格式即用）。首次使用需从 **hf-mirror** 下载 3 个模型文件（DiT NVFP4 4.2GB + Qwen3-4B-FP4 3.3GB + Flux AE 320MB，共 ~7.8GB）；URL 勿加 `?download=true`（redirect 死循环），curl 必带 `-H "User-Agent: Mozilla/5.0"`
2. **Real-ESRGAN 4x 超分**：生成图 512×768 → 2048×3072，视频里不糊（comfyui skill `workflows/` 有 ESRGAN upscale 示例）
3. **Remotion Ken Burns**：超分图缓慢推拉 + 胶片颗粒 overlay → 动态唯美背景

备选：**FLUX.1-schnell GGUF Q4** — 真实感天花板但慢（社区实测 ~9min/张 512，6GB 卡），需装 ComfyUI-GGUF 自定义节点，适合后台批量出图。对比基准：dreamshaper_8（SD1.5，0.9B 参数）质感最弱，Z-Image（6B）是质变。

## 素材兜底顺序（无 key 优先）

- 照片色板（Openverse CC0 免key 提色板）> 自放图（`--bg-dir`）> Bing 每日壁纸 > 渐变兜底
- Pexels 需免费 key；付费 AI 视频（可灵/即梦）**用户明确不优先**（要无 key 方案）
- 用户偏好（2026-08 确认）：**不用本地 AI 模型、不要 key、不要付费**，代码背景 + 照片色板 + 免费图库已覆盖

## 参考

- 用户视频流水线：prose-poetry-video（散文诗）、ai-weekly-video（AI周报）
- ComfyUI 6GB 显卡细节：comfyui skill 的 `wsl-low-vram-setup.md`、`z-image-turbo-nvfp4-setup.md`
- 注意：以上两个视频 skill 与 comfyui skill 均为用户自有/三方 skill，curator 不可直接改（需 `hermes curator adopt`）
