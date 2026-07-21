---
name: ai-weekly-video
description: "一键生成 AI 周报视频：从 Markdown 报告到 B站可发布 MP4 的全自动流水线。VTT 字幕精确对齐配音，PPT 风格纯代码画面。"
version: 1.0.0
---

# AI 周报视频一键生成

从 AI 周报 Markdown 文件自动生成带配音、字幕、PPT 风格画面的 Remotion MP4 视频。

## 触发条件

- 用户说"把周报生成视频""根据这份报告做视频""AI 周报转 MP4""Skill 周报"
- 用户提供 Markdown 报告文件路径
- ⚠️ "Skill 周报"有两个含义，必须先 clarify：GitHub Agent Skill 生态（github.com 上的 Skill 仓库）vs Hermes 自带的 Skill。两种都走相同的视频生成流水线，只是数据来源和报告内容不同。

## 输入

一份结构化的 AI 周报 Markdown 文件，通常包含：
- 日期、收录项目数
- 本周亮点（2-5 条）
- 分类详情（Agent/LLM/多模态/RAG 等）
- 本周统计

## 工作流（完整流水线）

### 阶段 1：脚本生成

1. **读周报**：提取关键数据——总项目数、各类别数量、Star 涨幅 TOP 5、新项目亮点
2. **写配音稿**：按你的 B站偏好写口语化中文稿——
   - 第一人称"我翻 GitHub Trending"
   - 3 个核心趋势做主线
   - 生活类比（不用技术类比）
   - 2000 字左右，最终配音 2m50s (±30s)
   - 纯文字，不要画面标注
3. **用户审核**：发脚本，等确认再继续

### 阶段 2：TTS 配音 + VTT 字幕

```bash
cd <项目根>/ai-weekly-video

# 将审核通过的配音文本写入文件
cat > /tmp/narration.txt << 'EOF'
<配音全文>
EOF

# 一步生成 MP3 + 精确时间戳 VTT
edge-tts --voice zh-CN-YunxiNeural --rate=+12% \
  -f /tmp/narration.txt \
  --write-media public/narration_YYYYMMDD.mp3 \
  --write-subtitles public/narration_YYYYMMDD.vtt

# 获取精确时长
ffprobe -v quiet -show_entries format=duration -of csv=p=0 public/narration_YYYYMMDD.mp3
```

### 阶段 3：解析 VTT → 帧数数组

用 Python 把 VTT 解析成帧数精确的 TypeScript 字幕数组：

```python
import re
vtt = open("public/narration_YYYYMMDD.vtt").read()
for block in vtt.strip().split("\n\n"):
    lines = block.strip().split("\n")
    if len(lines) < 2: continue
    m = re.match(r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[.,](\d{3})", lines[1])
    if not m: continue
    h1,m1,s1,ms1,h2,m2,s2,ms2 = [int(x) for x in m.groups()]
    start_s = h1*3600+m1*60+s1+ms1/1000
    end_s = h2*3600+m2*60+s2+ms2/1000
    text = "".join(lines[2:])
    print(f"  {{ from: {int(start_s*30)}, to: {int(end_s*30)}, text: \"{text}\" }},")
print(f"\n// Total: {int(end_s*30)} frames, {end_s:.1f}s")
```

输出格式：
```ts
const SUBTITLES = [
  { from: 3, to: 99, text: "这周我翻 GitHub Trending 的时候，发现一个规律。" },
  { from: 98, to: 219, text: "AI Agent 正在悄悄渗透进你能想到的每一个角落。" },
  // ...
];
```

### 阶段 4：分镜规划

根据每句字幕的内容，决定这段用什么视觉组件：

| 内容类型 | 对应组件 | 适用场景 |
|---|---|---|
| 章节标题 | `Chapter` | 每个板块开头（Agent 赛道、LLM 工具等） |
| 单个项目介绍 | `ProjCard` | CrewAI、Dify 等具体项目 |
| 关键数据强调 | `HighlightCard` | "Cognee +182⭐" |
| 数据并列 | `NumberCards` | "30 个项目 / 12 个新项目" |
| 柱状图对比 | `BarChart` | TOP 5 Star 增量 |
| 金句/短结论 | `FactSlide` | "零 API Key 也能跑" |
| 分类数据 | `CategoryBreakdown` | "Agent 框架 12 个 / LLM 5 个" |
| 左右对比 | `SideBySide` | Cherry Studio vs UI-TARS |
| 流程展示 | `FlowPipeline` | "研究→脚本→画面→配音→渲染" |
| 仅字幕 | 纯色背景 | 过渡句（"它是干嘛的？"） |

**分镜原则：**
- 短句（<3 秒）用 FactSlide 或纯字幕
- 中句（3-6 秒）用 ProjCard 或 HighlightCard
- 长段（6+ 秒）用多组件混搭
- 绝不连续 3 段用同一种组件

### 阶段 5：更新 Remotion 代码（使用模板，推荐）

项目已内置通用组件库 `src/components.tsx`（15 个组件）和空白模板 `src/Video.template.tsx`。每周只需改 4 个地方：

1. **`public/narration_YYYYMMDD.mp3`** — 替换音频文件
2. **`src/Video.tsx` 的 `SUBTITLES` 数组** — 跑 `scripts/vtt_to_subtitles.py public/narration_YYYYMMDD.vtt 30` 粘贴结果（`{from, to}` 格式）
3. **`DURATION`** — 设为 `ceil(音频秒数 × 30)`
4. **场景 `<Sequence>` 编排** — 按分镜规划写

所有组件从 `src/components.tsx` 导入，不需要每次复制粘贴组件代码。`Root.tsx` 只需改 `durationInFrames` 和 composition `id`。

**`src/components.tsx`** 导出 15 个组件：`GradientBg` `DotGrid` `Watermark` `Particles` `PulseRing` `ActiveSub` `Chapter` `ProjCard`（支持可选 `logo` 参数显示项目头像）`FactSlide` `HighlightCard` `NumberCards` `BarChart` `CategoryBreakdown` `SideBySide` `FlowPipeline`

## 关键踩坑

1. **VTT 解析：`split("\n\n")` 必须是双换行**，单换行只拆行不拆 cue
2. **字幕数组里的 `from`/`to` 可能有微秒级重叠**（上句 `to` > 下句 `from`），`ActiveSub` 用第一个匹配的即可
3. **`npx create-video` 在 WSL + /mnt/d/ 下超时** → 手动 `npm init` + `npm install remotion @remotion/cli react react-dom`（180s timeout 常见，装完继续用）
4. **edge-tts 必须 CLI 方式**，不要用 Python API（`Communicate.subs()` 不存在）
5. **配音时长用 ffprobe 精确到帧**，不要手动估算
6. **Sequence 的 `from` 用字幕 `from` 帧数，`durationInFrames` = `to - from`**
7. **每个 Sequence 必须有对应配音时间段内的句子数** — 如果一段配音里有 2 句字幕，这 2 句都要在这个 Sequence 的 `from`-`to` 范围内，否则字幕不会显示
8. **edge-tts 长文本 (>~2000 字) 返回 `NoAudioReceived`** — 需分块处理。用 `split -C 2000 narration.txt /tmp/part_` 切分，逐块 `edge-tts -f /tmp/part_aa --write-media /tmp/part_aa.mp3`，最后 `ffmpeg -f concat` 合并。VTT 字幕不受此限制，可从全文单独生成
9. **TSX 中禁止转义引号 `\"`** — esbuild 打包时报 `Unexpected backslash in JSX element`。所有引号改用中文直角引号 `「」`。检查 SUBTITLES 数组和 JSX 组件属性（`desc="..."`）两处

### 阶段 6：渲染

```bash
cd <项目根>/ai-weekly-video
npx remotion render <composition-id> out/ai-weekly-YYYYMMDD-v1.mp4
# 约 5-8 分钟，输出 ~15MB
```

## 素材增强（可选，每次发布前运行）

### BGM 背景音乐

```bash
ffmpeg -y -f lavfi -i "sine=frequency=220:duration=${DURATION}" \
  -f lavfi -i "sine=frequency=330:duration=${DURATION}" \
  -f lavfi -i "sine=frequency=440:duration=${DURATION}" \
  -filter_complex "[0:a]volume=0.04[a];[1:a]volume=0.03,adelay=5000|5000[b];[2:a]volume=0.02,adelay=15000|15000[c];[a][b][c]amix=inputs=3:duration=longest,afade=t=in:d=3,afade=t=out:st=${DURATION-4}:d=4" \
  -c:a libmp3lame -b:a 64k public/bgm.mp3
```

在 `Video.tsx` 中加：`<Audio src={staticFile("bgm.mp3")} volume={0.12} />`

### 项目 Logo

`https://github.com/{owner}.png` 可直接下载。批量抓取：

```bash
for owner in owner1 owner2 ...; do
  curl -sL --max-time 10 -x http://127.0.0.1:8888 "https://github.com/${owner}.png" -o "public/logos/${owner}.png"
done
```

`ProjCard` 支持 `logo` 参数显示头像替代 emoji。

## 项目结构

### BGM

```
ai-weekly-video/
├── src/
│   ├── components.tsx         # 15 个通用组件（每次直接 import，不用复制）
│   ├── Video.template.tsx     # 空白模板（带注释示例，每周复制起点）
│   ├── Video.tsx              # 本周成品
│   ├── Root.tsx               # Composition 定义（改 durationInFrames + id）
│   └── index.ts               # registerRoot
├── scripts/
│   └── vtt_to_subtitles.py    # VTT → {from, to, text} 帧数组
├── public/
│   ├── narration_YYYYMMDD.mp3 # edge-tts 配音
│   ├── narration_YYYYMMDD.vtt # 时间戳字幕
│   ├── bgm.mp3                # 背景音乐（可选）
│   └── logos/                 # 项目头像（可选，github.com/{owner}.png）
├── out/                       # 渲染输出
├── package.json
└── tsconfig.json
```

## 数据采集（GitHub Trending）

当 `web_search` / `web_extract` 不可用时（Firecrawl token 过期），直接 curl GitHub Trending 通过代理抓数据：

```bash
# 通过代理抓取 trending 页面
curl -sL --max-time 20 -x http://127.0.0.1:8888 -A "Mozilla/5.0" \
  "https://github.com/trending/python?since=weekly" -o /tmp/gh_python.html

# 提取仓库名 + 本周 star（用 Python 解析 HTML）
# ⚠️ 用户会阻止 python3 -c / heredoc，必须 write_file + terminal 方式
```

解析后逐仓库调 API 拿总 Star：`curl -x proxy "https://api.github.com/repos/{owner}/{repo}"`

搜索特定主题仓库：`https://github.com/search?q=skill+agent&type=repositories&s=stars&o=desc` → grep HTML 提取 `href="/(owner/repo)"`。

## 用户偏好

- B站账号：无问凡
- 风格：深度解读型，不露脸，8-10 分钟 → 配音约 2m50s-3m
- 第一人称，普通开发者学习笔记
- **类比用生活类比，绝不用技术类比**
- 视频项目根目录：`D:\项目\个人总结\AI周报\`
