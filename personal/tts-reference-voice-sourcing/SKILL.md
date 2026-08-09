---
name: tts-reference-voice-sourcing
description: "为CosyVoice等零样本TTS找真实人声参考：B站/YouTube搜索、whisper定位裁剪、质量筛选与法律边界。"
version: 1.0.0
---

# 零样本 TTS 参考音色素材获取

CosyVoice / GPT-SoVITS / IndexTTS 等零样本复刻 TTS：**参考音频决定 90% 音色，指令/提示词只控制语气情绪**。要"听不出 AI 感"，必须找真实目标人声做参考——播音腔参考输出永远是播音腔。

本 skill 沉淀 2026-08 为散文诗视频找"老年男声"参考的完整工作流（prose-poetry-video skill 使用本流程）。

## 核心原理（实测）

- 参考音色决定音色底子；指令控制情绪/语速，改不了音色
- 降音高后处理上限约 -5%~-6%，再低变"怪兽音"失真（用户实测反馈）
- 表演腔/播音腔/评书腔参考 → 输出带同款腔调；要日常说话感需日常说话参考
- 生成后必须 whisper 转写验证内容（零样本 TTS 可能输出噪音、把指令当正文读、读成方言）

## 找素材工作流

1. **B站搜索 API**（web_search 结果被 SEO 垃圾污染，B站 API 更准）：
   ```bash
   curl -s -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
     "https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword=<urlencode>&page=1"
   ```
   ⚠️ 连续搜索会被风控（返回非 JSON）→ 换关键词、稍等、或改走 YouTube
2. **YouTube 搜索**：`yt-dlp "ytsearch5:<关键词>" --print "%(id)s | %(title)s" --no-playlist --skip-download`（无需代理即可搜）
3. **下载音频**：
   - B站：`yt-dlp --no-playlist -f "ba/b" -o "x_%(id)s.%(ext)s" <URL>`（匿名可下）
   - YouTube：加 `--proxy http://127.0.0.1:8888`；部分视频 403 限制下载 → 换候选
4. **whisper 转写定位**（faster-whisper，CPU int8 可跑）：
   ```bash
   ffmpeg -y -i src -ar 16000 -ac 1 x_16k.wav
   # faster-whisper small 转写带时间戳，找 >4s 连续人声段
   ```
5. **裁剪参考**：`ffmpeg -y -ss <start> -t 8 -i src -ar 24000 -ac 1 elderlyN_prompt.wav`（3-10s 最佳；24kHz 单声道与 CosyVoice 默认 prompt 一致）

## 素材质量筛选标准（实测踩坑）

| 类型 | 是否可用 | 实例 |
|---|---|---|
| 真实老人连续讲述/朗读 | ✅ 最佳 | 「董爷爷讲从前的事」（90岁河北保定普通话）、CCTV《朗读者》普通读者念信 |
| 方言老人 | ❌ 不适合普通话参考（whisper 转写乱码=方言）| 百岁老人采访（粤语/方言）|
| 多角色配音喜剧 | ❌（配音+变声，非真实老人）| B站"华爷爷讲故事"（151万播放那条）|
| 采访答话零散 | ❌（老人只答 1-3s 短语，凑不出连续段）| 百寿探秘合集、街头采访、户晨风"随机找老人购物"系列 |
| 博主 vlog 旁白/演唱 | ❌ | 维修大爷唱歌视频 |
| 台湾/港台腔 | ❌ 口音会带入生成 | 拾光大街（台湾街头采访）|

## 已积累素材（2026-08，位于 ~/cosyvoice-models/assets/）

| 文件 | 来源 | 说明 |
|---|---|---|
| elderly4_prompt.wav | 董爷爷讲从前的事（YouTube kO5WTnejy_o，121s 起）| 男·90岁·河北保定·自然讲述 ⭐最佳 |
| elderly2_prompt.wav | CCTV《朗读者》74岁女读者念信（YouTube 3bXmbRN5_ys，414.9s 起）| 女·普通话标准·情感真挚 |
| elderly3_prompt.wav | B站农村大叔田间朗诵（BV1wq4y1K7wX）| 男·朗诵腔（表演腔）|
| elderly_prompt.wav | 孙敬修讲西游记（BV1ps411y7eR，16s 起）| 男·评书腔·已故名人⚠️ |
| cross_lingual_prompt.wav / zero_shot_prompt.wav | CosyVoice 官方 | 男·播音腔 / 女·标准普通话 |

## 法律边界（民法典 1023 条声音权益）

- 已故名人（如孙敬修）声音做参考 → 公开发布高风险（声音权由继承人主张）
- 普通老人（节目参与者、非名人）→ 风险低，但声音权仍属本人
- 最安全：自己录/家人录 8 秒 → 音色 100% 自有，零风险
- 参考音频仅提取音色特征（不发布原音频）是常见做法，但本质仍是灰区；发布场景务必提醒用户

## 验证

生成音频后用 faster-whisper 转写（`~/cosyvoice-venv/bin/python` + `from faster_whisper import WhisperModel`，small 模型 CPU int8），确认内容与原文一致且不含指令文本/噪音。内容验证是交付前的必要质检。
