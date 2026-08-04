---
name: prose-poetry-video
description: "散文诗/诗词配音视频双模式：简单模式一键出片MP4，复杂模式生成剪辑详情+素材清单供剪映剪辑。"
version: 1.0.0
---

# 散文诗 / 诗词情感视频生成

参考风格：B站「二狗的散文诗」类视频（如 BV1Tp421X7yd）——词 + 背景图/影视片段 + BGM + 字幕，「句句不提释怀，句句都是释怀」的文案氛围感。

## 触发条件

- 用户说「把这篇散文/诗做成视频」「生成剪辑详情」「散文诗视频」「给诗词配音」「视频剪辑详情」「读一段散文」
- 用户提供文本（散文/诗词/金句文案）或主题，想要多音色朗读 + 背景画面 + 音乐

## 两种模式 —— 先 clarify 确认选哪种

| 模式 | 适用 | 产出 |
|---|---|---|
| **A 简单** | 内容短、想直接要成品 | 完整 MP4（Remotion 全自动流水线）|
| **B 复杂** | 内容长、想要电影感、想自己精剪 | `剪辑详情.md` + 分段配音 mp3 + SRT 字幕 + 素材清单，用户拖进剪映自己剪 |

开工前问清楚：文本来源、横屏还是竖屏、是否已有背景图/电影片段/BGM、音色偏好（没有就用默认 xiaoxiao）。

## 输入

- 文本：散文/诗/文案，**空行分隔 = 一个配音段 = 一个镜头**（段内换行保留，诗句可多行）
- 可选：`--bg-dir` 背景图目录、`--bgm` 音乐、`--voices` 音色序列、`--orientation` 横竖屏、`--vertical-text` 文字竖排

## 音色表（本机 edge-tts 实测可用，2026-08 验证，勿写表外音色）

| key | 声音 | 性别·风格 | 适合 |
|---|---|---|---|
| xiaoxiao | zh-CN-XiaoxiaoNeural | 女·温柔知性 | 散文主声/情感叙述（默认）|
| xiaoyi | zh-CN-XiaoyiNeural | 女·活泼清亮 | 轻快/年少回忆 |
| yunxi | zh-CN-YunxiNeural | 男·阳光少年 | 青春/初恋 |
| yunjian | zh-CN-YunjianNeural | 男·沉稳磁性 | 深夜哲思/男性叙述 |
| yunyang | zh-CN-YunyangNeural | 男·浑厚大气 | 开场/史诗感 |
| yunxia | zh-CN-YunxiaNeural | 男·青涩少年 | 年少心事 |
| xiaobei | zh-CN-liaoning-XiaobeiNeural | 女·东北腔 | 趣味/烟火气 |
| xiaoni | zh-CN-shaanxi-XiaoniNeural | 女·陕西腔 | 乡土/怀旧 |
| hiugaai | zh-HK-HiuGaaiNeural | 女·粤语 | 粤语散文 |
| wanlung | zh-HK-WanLungNeural | 男·粤语 | 粤语诗词 |
| hsiaochen | zh-TW-HsiaoChenNeural | 女·台湾腔 | 温柔叙述 |
| hsiaoyu | zh-TW-HsiaoYuNeural | 女·台湾腔甜 | 甜系/可爱 |
| yunjhe | zh-TW-YunJheNeural | 男·台湾腔 | 叙述 |

⚠️ 本机 edge-tts 只有上面这些中文音色（Xiaochen/Xiaomo/Xiaohan 等不存在，写了会报错）。

## 音色分配策略

- **单声贯穿**：一个主声 + 固定语速（最常见最稳）
- **男女对读**：叙述用男声（yunjian/yunxi），金句/内心独白用女声（xiaoxiao）——情感对比强
- **每段换声**：段落间轮换音色（用户「不同音色读散文诗句」的需求），`--voices a,b,c` 自动循环分配
- **情绪微调**：低沉段 `--pitch -10Hz`，轻快段 `--rate +15%`；朗诵默认 `--rate +4%` 偏慢

## 模式 A：一键出片

```bash
# 文本放 WSL ext4（铁律），跑流水线（自动：TTS→时长→data.ts→渲染）
python3 ~/.hermes/skills/creative/prose-poetry-video/scripts/poem_pipeline.py \
  --text /tmp/poem.txt --mode video \
  --title "错过就错过了吧" \
  --voices xiaoxiao,yunjian,xiaoyi \
  --orientation horizontal \
  --bg-dir /tmp/bgs --bgm /tmp/bgm.mp3 \
  --out /mnt/d/项目/个人总结/散文诗视频/20260804_错过
```

- 无背景图时用渐变底色兜底（按段自动换色相），有 bgm 自动低音量垫底
- 渲染完 cp 回 /mnt/d（项目源码在 ext4 ~/poem-video，禁止放 /mnt/d/）
- 先 `--dry-run` 预览分段和音色分配再正式跑

## 模式 B：剪辑详情（用户剪映剪辑）

```bash
python3 ~/.hermes/skills/creative/prose-poetry-video/scripts/poem_pipeline.py \
  --text /tmp/poem.txt --mode script \
  --title "标题" --voices xiaoxiao,yunjian,xiaoyi \
  --out /mnt/d/项目/个人总结/散文诗视频/20260804_标题_素材
```

交付物（都可直接拖进剪映）：
- **剪辑详情.md**：分镜表（镜号/时间段/画面建议/配音文本/音色/素材文件/转场）+ 配音素材清单 + 背景图/电影片段/BGM 素材清单 + 剪映操作步骤
- **audio/seg_NN_音色.mp3**：每段独立配音（已按音色生成，无需再合成）
- **subtitles.srt**：剪映可导入字幕

## 素材来源

- **背景图（默认自动生成，无需准备）**：流水线默认 `--gen-bg`（可用 `--no-gen-bg` 关闭），每段按情绪关键词自动配图，优先级：
  1. **fun-codex**（Hermes Web UI 图像端点，需在 config.yaml 配 `custom_providers: fun-codex`，见 apikey-image-gen skill）——可精确控制意境（黄昏天空/雨夜霓虹/江边灯火/人物背影等）
  2. **Bing 每日壁纸**（免费无 key，风景空镜）——fun-codex 未配置时自动兜底
  3. 渐变底色（兜底的兜底）
- 也可 `--bg-dir 目录` 用自己的图（轮换分配，优先级最高）
- **电影片段**：用户自备（法律风险见下）
- **BGM**：剪映音乐库/网易云纯音乐（搜"治愈 钢琴""纯音乐 慢"）> ffmpeg 氛围音兜底（见 ai-weekly-video skill）

## ⚖️ 法律风险提示（每次交付都要提醒）

1. **电影片段拼接**：电影是受著作权保护的视听作品，未经授权剪辑拼接发布 → 侵犯复制权/信息网络传播权。自娱自乐不发布 ≈ 安全；发 B站（即使不盈利）是灰色地带，可能被权利人投诉下架、平台限流；商用（带货/接广告/直播引流）高风险，可被起诉赔偿。B站文案类视频大量用影视片段，本质都是灰色，别以为别人发了你就能发。
2. **AI 模仿演员声音**（音色克隆明星声/配音师声）：《民法典》1023 条声音参照肖像权保护，未经许可用 AI 合成他人声音制作内容 = 侵害声音权。判例：北京互联网法院全国首例 AI 声音侵权案（配音师声音被 AI 化后商用）判赔 25 万。明星声商用还可能构成不正当竞争。**别碰。**
3. **安全路径**：edge-tts 微软官方音色（不模仿真人）✅ / 无版权背景图（Pexels/AI生成/自拍）✅ / 自写文案 ✅ / 影视片段 ⚠️ 谨慎（自娱可，发布有风险）。

## 关键踩坑（实测）

1. **typescript 必须 5.x**（^5.9.3），remotion ^4.0.505，react ^19.2.8 —— 与 ~/ai-weekly-video 同款版本组合，别升级 typescript@7（Go 重写版崩 @remotion/bundler）
2. **edge-tts 会网络挂死**：subprocess 必须 timeout=60 + 重试 3 次 + sleep 3；中断留下的 mp3 检查 `st_size > 1000` 才复用
3. **段 >1500 字切分**再 concat（NoAudioReceived）
4. **WSL 渲染必须在 ext4**（~/poem-video），禁止 /mnt/d/（9P 协议写上万文件性能灾难）；渲染完再 cp 回 /mnt/d/
5. **Python 生成 TS 文件用 `json.dumps(ensure_ascii=False)` 写字符串值**，JSX 结构行用普通字符串拼接（f-string 的 `{{` 会吞花括号）
6. **Linux 渲染中文字体**：需 fonts-noto-cjk（`fc-list :lang=zh` 检查），字体栈 `"Noto Serif CJK SC","KaiTi","STKaiti",serif`
7. **模板只有 src/data.ts 每次重写**：Root.tsx/Video.tsx 静态不用动
8. **Remotion staticFile 只解析 public/ 下文件**：TTS 产物必须放 `public/parts/`（放 work/ 会报 "could not be found"，2026-08 实测踩过）
9. **配音复用有内容哈希防护**：脚本会对 文本+音色 算 md5 存 `.hash`，只有完全相同才复用已有 mp3，换文本自动清空重配——不会静默用旧配音
10. 本机 edge-tts 音色少，别凭网上教程写 Xiaochen 等不存在的音色（实测报错）

## 模板与脚本

- Remotion 模板：`templates/poem-video/`（package.json/tsconfig/src，流水线自动复制并注入 data.ts）
- 流水线：`scripts/poem_pipeline.py`（`--mode video|script`，`--dry-run` 预览分段；音色轮换/长段切分/时长计算/背景图分配全自动）
