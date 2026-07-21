---
name: bilibili-video-production
description: 将Hermes生成的AI技术内容（周报、研究总结等）转化为B站深度解读视频文稿，含决策框架、脚本结构、剪映适配提示。
version: 1.0.0
---

# B站深度解读视频文稿制作

将Hermes Agent自动生成的技术报告（AI周报等）转化为B站发布的视频文稿。

## 触发条件

- 用户要求基于Hermes报告制作B站视频
- 用户说"根据XX写视频文稿""做成视频发B站"等
- 用户提到剪映、视频脚本、B站发布

## 核心流程

### Phase 1: 方向对齐（可精简）

根据用户状态决定确认轮数：

**轻量模式**（已知道用户偏好，且用户说「直接给我」「直接生成」）：跳过三轮确认，沿用已记录的用户偏好（深度解读型、不露脸、8-10分钟、生活类比），直接进入 Phase 2 写稿。

**完整模式**（首次合作或用户主动要求调整）：不直接写稿，先通过clarify分三轮确认：

**第一轮：视频风格**
提供四种选项，让用户单选：
- 干货盘点型 — 快速过所有项目，数据密集
- 深度解读型 — 挑3-5个核心趋势深入讲
- 新闻快报型 — 周报做背景+行业新闻
- 吃瓜吐槽型 — 轻松幽默泛科技向

**第二轮：展现形式**
- 纯画面+配音（不露脸）— 最常用
- 半露脸
- 全程出镜
- 由你建议

**第三轮：时长**
- 5-8分钟（精选3个趋势）
- 8-12分钟（5个趋势全讲）
- 12-15分钟（趋势+延伸）
- 由你建议

### Phase 2: 内容筛选与主线设计

根据视频风格从报告中提取核心内容：

| 风格 | 选取策略 |
|------|----------|
| 深度解读 | 3-4个趋势，用一条逻辑主线串起来 |
| 干货盘点 | 全量项目，按类别分组，控制节奏 |
| 新闻快报 | 报告重点+补充行业新闻 |

**深度解读的主线设计模式：**
- "三件套"结构 — 三条腿撑一个主题（如：记忆-生态-安全 → Agent成熟三要素）
- "时间线"结构 — 从过去到未来的演进
- "对比"结构 — 两个阵营/方向的碰撞

### Phase 3: 脚本结构（纯画面+配音版）

标准深度解读脚本结构（8-10分钟）：

```
【开头 30秒】
- 钩子：一个震撼数据或观点
- 本期主题一句话
- "这周AI圈发生了什么？我们挑三个最重要的深聊"

【正片 每段约3分钟 × 3段】
每段结构：
- 现象描述（1分钟）：这是什么项目/趋势，数据有多大
- 深入分析（1.5分钟）：为什么重要，背后逻辑
- 画面提示（穿插其中）：标注画面切换点

【结尾 30秒】
- 三点总结
- 下期预告（可选）
- 关注/三连引导
```

### Phase 4: 文稿格式要求

文稿输出需包含：

1. **口语化文稿** — 适合配音朗读，不要书面语
2. **画面提示** — 用【画面：XXX】标注每个视觉切换点，方便剪映剪辑
3. **素材建议** — 列出需要准备的截图/动画/图表
4. **时长估算** — 每段标注预计时长

画面提示类型：
- 【画面：项目GitHub首页截图】— 静态截图
- 【画面：Star增长动画/数据图表】— 数据可视化
- 【画面：技术架构示意图】— 需要自己做的图
- 【画面：新闻标题/引用文字】— 文字卡片
- 【画面：纯色背景+大字】— 强调金句

## 用户偏好

- B站账号：无问凡 (mid:477332376)
- 风格偏好：深度解读型，不露脸
- 时长偏好：8-10分钟，3个核心趋势
- **类比方式**：生活类比（手机、充电线、门锁、体检），**绝对不要技术类比（Java/JDBC/Redis/Session等）**
- **人设**：普通开发者学习笔记，第一人称，可表达困惑和兴奋，不装专家
- **目的**：借做视频倒逼学习，真诚分享成长过程
- 视频项目存放根目录：`D:\项目\个人总结\AI周报\`

## Phase 5: Remotion 代码制作（从文稿到MP4）

当用户希望用CLI工具直接生成视频时，使用 Remotion（React框架）+ edge-tts（中文配音）。

### 5.1 环境检查

```bash
which node && node --version    # 需要 v16+
which ffmpeg && ffmpeg -version # 渲染用
which edge-tts || pip3 install edge-tts --break-system-packages -q
```

### 5.2 项目搭建（手动方式，避免超时）

`npx create-video` 在 WSL 下操作 `/mnt/d/` 经常超时。改用：

```bash
mkdir -p "项目根/ai-weekly-video/src"
cd "项目根/ai-weekly-video"
npm init -y
npm install remotion @remotion/cli react react-dom @types/react typescript
```

创建文件：
- `src/index.ts` — `registerRoot(RemotionRoot)`
- `src/Root.tsx` — `<Composition id="..." fps={30} width={1920} height={1080} durationInFrames={...} />`
- `src/Video.tsx` — 主组件，含场景路由、字幕、动画
- `tsconfig.json` — `{"compilerOptions":{"jsx":"react-jsx","strict":true}}`

### 5.3 素材准备 + VTT 字幕同步（必读）

**配音画面同步：** 不要手动估算 Sequence 时间轴。用 edge-tts 的 `--write-subtitles` 生成 VTT 文件，解析时间戳转帧数，所有 Sequence 按 VTT 对齐。详见 `report-to-video` skill 的 "VTT-Based Subtitle + Video Sync" 章节。

**截图**：不建议用 GitHub 截图做背景——效果太 low。用纯代码画渐变背景 + 圆点纹理 + 玻璃质感卡片替代（参考 `report-to-video` skill 的色彩系统和组件模式）。如果必须用截图：

```bash
# WSL下路径太长cp会报"No such file or directory"，必须用 find -exec
find /home/administrator/.hermes/cache/screenshots/ -name "browser_screenshot_XXX.png" -exec cp {} "目标路径" \;
```

**生活场景素材**（充电线/手机/门锁等）：用户自己从剪映素材库获取，不在代码中硬编码。

### 5.4 TTS 配音生成

```python
import asyncio, edge_tts

async def main():
    voice = "zh-CN-YunxiNeural"  # 中文男声；女声用 zh-CN-XiaoxiaoNeural
    rate = "+10%"
    communicate = edge_tts.Communicate(FULL_NARRATION_TEXT, voice, rate=rate)
    await communicate.save("public/narration.mp3")

asyncio.run(main())
```

配音文本要精简——原稿8-10分钟的话，TTS缩到3-5分钟即可。再用 ffprobe 检查实际时长：

```bash
ffprobe -v quiet -show_entries format=duration -of csv=p=0 public/narration.mp3
# 返回秒数，乘以30得到帧数，更新 durationInFrames
```

在 Video.tsx 中引入：`<Audio src="/narration.mp3" />`

### 5.5 视频组件设计

视觉风格：深色背景 `#0a0a12`，青色 accent `#00d4ff`。

- **背景**：`<Img>` 全屏 + Ken Burns 缩放 + `rgba(0,0,0,0.6-0.7)` 暗色遮罩
- **字幕条**：底部居中，半透明黑底 `rgba(0,0,0,0.75)` + `backdropFilter blur(10px)` + 圆角16px + 白色36px字体
- **章节标题**：全屏深色背景 + 大字标题 + accent色横线
- **转场**：纯黑2-4秒，中间一条accent色横线扫描
- **水印**：右下角 `@无问凡` 半透明白色

关键动画：`spring({fps:30, config:{damping:15}})` + `interpolate(frame, [start,end], [0,1])`

### 5.6 渲染

```bash
# 预览（验证布局和颜色）
npx remotion still <composition-id> --frame=180 --scale=0.25 out/preview.png

# 完整渲染（后台运行，避免阻塞）
npx remotion render <composition-id> out/ai-weekly-0629.mp4
```

首次渲染需下载 Chrome Headless Shell (~92MB)，后续有缓存。6300帧约需5-10分钟。

### 5.7 交付

告知用户：
- Remotion 项目路径（完整可编辑）
- 渲染的 MP4 路径
- 可替换项：`public/narration.mp3`（配音）、`public/assets/`（截图）、后续可加 BGM
- 可视化编辑：`cd 项目 && npx remotion studio`

## Phase 7: OpenMontage 替代方案

[calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) 是开源 Agent 视频制作系统（12条管线、52个工具）。可作为 Remotion 手写代码的替代。

### 适用场景
- 从零开始，没有现成 Remotion 项目
- 做英文视频（Piper TTS 英文质量尚可）
- 想快速体验 Agent 驱动的视频制作流程

### 不适用场景
- **已有打磨好的 Remotion 管线** — 直接用 Phase 5 更快
- **中文视频** — Piper 中文 TTS 远不如 edge-tts（YunxiNeural），OpenMontage 默认用 Piper
- **WSL + /mnt/d/** — npm install 极慢（需 300s+ timeout），`npx create-video` 同样超时

### 安装要点
```bash
git clone https://github.com/calesthio/OpenMontage.git
cd OpenMontage
make setup  # 如果 npm install 超时，手动 cd remotion-composer && npm install
source .venv/bin/activate && pip install piper-tts
cp .env.example .env  # 零 Key 也能跑
```

### 管线流程
```
research → proposal → script → scene_plan → assets → edit → compose
```
每阶段有对应的 stage director skill（`skills/pipelines/explainer/`），Agent 逐阶段执行，有审批门禁和自检。

### 与 Remotion 管线对比
| 维度 | OpenMontage | Remotion 手写 |
|---|---|---|
| 上手速度 | 快（一条 prompt 启动） | 慢（需写 React 组件） |
| 中文配音 | Piper（一般） | edge-tts（好） |
| 灵活性 | 低（管线约束） | 高（完全自定义） |
| 零 Key 可用 | ✅ | ✅ |
| 适合场景 | 探索、英文视频 | 生产、中文 B 站视频 |

### 混合方案
可以借 OpenMontage 的管线思路（proposal→script→scene_plan），用 Remotion 渲染。本次 AI 周报视频就是这样做的：用 OpenMontage 的 Animated Explainer 管线设计了提案和脚本，实际渲染走 Remotion + edge-tts。

## Phase 6: 剪映后期（仍为可选）

如果用户在剪映中完成后期（添加BGM/转场/生活素材），文稿中应包含：
- 【画面：XXX】标注每个视觉切换点
- 素材清单（截图、数据动画、生活场景素材）
- 剪映制作建议（节奏、转场、音效）

## 参考文件

- `references/ai-weekly-0629-3trends.md` — 3趋势主线结构示例
- `references/ai-weekly-0629-full-pipeline.md` — 本期完整流水线记录（文稿+Remotion+TTS+渲染）
- `references/ai-memory-concepts.md` — AI记忆概念与类比库，含精准/禁止类比对照表

## 踩坑

**文稿阶段：**
- 不要上来就写稿，必须先对齐方向（风格/形式/类比/时长），否则返工
- 深度解读不是流水账，必须有一条逻辑主线串起趋势
- 画面提示要具体，不要写"展示相关内容"这种废话
- 用户明确不要技术类比（Java/JDBC），必须用生活类比
- 类比写完要做「机制匹配度检查」——类比的运作原理是否和技术的实际原理一致？如果一个是「全量搬」一个是「挑重点」，就是错的
- 用户会主动指正不精准的类比（如「云端备份」被质疑），不要等——自己先检查
- **类比精准度要求**：生活类比不能只求「好懂」，必须精准匹配核心机制。写完每个类比后做「机制匹配度检查」——类比的运作方式是否与技术的实际机制一致。反例：「AI memory = 云端备份」（全量恢复 vs 选择性提炼，机制完全不同，被用户直接指正）。正例：「AI memory = 开会记笔记」（挑重点记、下次翻看、不是逐字还原）。同一主题类比（如「手机」）越延伸越容易偏，每次都要独立检查。

**Remotion阶段：**
- `npx create-video` 在WSL的 `/mnt/d/` 下经常超时 → 改手动 npm init + npm install
- `cp` 报错 "No such file or directory" 但 `ls` 能看到 → WSL路径过长，用 `find -exec cp`
- `browser_vision` vision analysis 报400错误 → deepseek模型不支持图片输入，但截图正常保存
- `npm install --save-dev` 可能清空已有依赖 → 重新 install 主依赖即可
- 首次 remotion render 需下载 Chrome，给足够 timeout（180-600s）

**配音阶段：**
- TTS配音文本要精简（原稿1/3长度），否则音频太长
- 渲染前用 ffprobe 确认音频时长，调整 durationInFrames 匹配
