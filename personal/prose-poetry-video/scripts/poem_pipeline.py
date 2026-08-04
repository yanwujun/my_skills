#!/usr/bin/env python3
"""散文诗/诗词视频流水线 (prose-poetry-video skill)

Mode A (--mode video)  一键出片: TTS配音 -> data.ts -> Remotion 渲染 MP4
Mode B (--mode script) 剪辑详情: 分段配音 mp3 + SRT + 剪辑详情.md (用户剪映剪辑)

用法示例见 SKILL.md。核心规则:
- 文本空行分段 = 一个配音段 = 一个镜头
- --voices a,b,c 音色自动轮换
- edge-tts 必须 timeout+重试 (会网络挂死); 段>1500字自动切分 concat
- 渲染必须在 WSL ext4 (9P 性能灾难)
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

FPS = 30

# key -> (edge-tts voice, 风格描述) —— 本机实测可用, 勿加表外音色
VOICES = {
    "xiaoxiao": ("zh-CN-XiaoxiaoNeural", "女·温柔知性"),
    "xiaoyi": ("zh-CN-XiaoyiNeural", "女·活泼清亮"),
    "yunxi": ("zh-CN-YunxiNeural", "男·阳光少年"),
    "yunjian": ("zh-CN-YunjianNeural", "男·沉稳磁性"),
    "yunyang": ("zh-CN-YunyangNeural", "男·浑厚大气"),
    "yunxia": ("zh-CN-YunxiaNeural", "男·青涩少年"),
    "xiaobei": ("zh-CN-liaoning-XiaobeiNeural", "女·东北腔"),
    "xiaoni": ("zh-CN-shaanxi-XiaoniNeural", "女·陕西腔"),
    "hiugaai": ("zh-HK-HiuGaaiNeural", "女·粤语"),
    "wanlung": ("zh-HK-WanLungNeural", "男·粤语"),
    "hsiaochen": ("zh-TW-HsiaoChenNeural", "女·台湾腔"),
    "hsiaoyu": ("zh-TW-HsiaoYuNeural", "女·台湾腔甜"),
    "yunjhe": ("zh-TW-YunJheNeural", "男·台湾腔"),
}

# 空镜关键词轮换 (模式B素材清单用)
BG_SUGGEST = [
    "黄昏天空 云层 电影感 4K 空镜",
    "雨夜霓虹 街角 湿漉漉的路面 氛围感",
    "江边灯火 倒影 夜色 静谧",
    "人物背影 孤独 逆光 电影感",
    "树影斑驳 光斑 旧时光",
    "城市夜景 万家灯火 俯瞰",
    "海面波光 浪花 辽阔",
    "旧街道 青石板 回忆",
]
CLIP_SUGGEST = [
    "离别车站 列车远去",
    "雨中撑伞 缓步走过",
    "窗边独坐 翻旧相册",
    "老街灯笼 人来人往",
    "江边夜风 点烟沉思",
    "空荡教室 落日斜照",
]


def run(cmd, timeout=60, retries=3, cwd=None):
    for i in range(retries):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
            if r.returncode == 0:
                return r
            err = (r.stderr or r.stdout).strip()[-500:]
        except subprocess.TimeoutExpired:
            err = "timeout"
        print(f"  [retry {i + 1}/{retries}] {' '.join(map(str, cmd))} failed: {err}", file=sys.stderr)
        time.sleep(3)
    raise RuntimeError(f"command failed: {' '.join(map(str, cmd))}")


def parse_segments(text):
    return [s.strip() for s in re.split(r"\n\s*\n", text) if s.strip()]


def tts_segment(voice_key, text, out_mp3, rate, pitch):
    voice, _ = VOICES[voice_key]
    chunks = [text[i : i + 1500] for i in range(0, len(text), 1500)] if len(text) > 1500 else [text]
    parts = []
    for ci, chunk in enumerate(chunks):
        p = out_mp3.with_name(f"{out_mp3.stem}_c{ci}.mp3")
        txt = out_mp3.with_name(f"{out_mp3.stem}_c{ci}.txt")
        txt.write_text(chunk, encoding="utf-8")
        run(["edge-tts", "--voice", voice, "--rate", rate, "--pitch", pitch,
             "-f", str(txt), "--write-media", str(p)], timeout=60, retries=3)
        if p.stat().st_size < 1000:
            raise RuntimeError(f"TTS output too small: {p}")
        parts.append(p)
        txt.unlink(missing_ok=True)
    if len(parts) == 1:
        shutil.move(str(parts[0]), str(out_mp3))
        return
    lst = out_mp3.with_name(out_mp3.stem + ".lst")
    lst.write_text("\n".join(f"file '{p}'" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out_mp3)],
        timeout=60)
    for p in parts:
        p.unlink(missing_ok=True)
    lst.unlink(missing_ok=True)


def duration_sec(mp3):
    r = run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(mp3)], timeout=30, retries=1)
    return float(r.stdout.strip())


def fmt_ts(sec):
    return f"{int(sec // 60)}:{sec % 60:05.2f}"


def fmt_srt(sec):
    ms = int(round((sec - int(sec)) * 1000))
    if ms >= 1000:
        ms = 999
    s = int(sec) % 60
    m = int(sec) // 60
    h = m // 60
    return f"{h:02d}:{m % 60:02d}:{s:02d},{ms:03d}"


def pick_font_size(length, orientation):
    if orientation == "vertical":
        if length <= 10:
            return 64
        if length <= 25:
            return 52
        if length <= 50:
            return 42
        return 34
    if length <= 15:
        return 76
    if length <= 40:
        return 58
    if length <= 90:
        return 46
    return 38


def check_cjk_fonts():
    try:
        fc = subprocess.run(["fc-list", ":lang=zh"], capture_output=True, text=True, timeout=10)
        if not fc.stdout.strip():
            print("⚠️  系统无中文字体, 渲染会出方框! 先执行: sudo apt install fonts-noto-cjk", file=sys.stderr)
    except Exception:
        pass


def build_srt(seg_meta):
    lines = []
    for m in seg_meta:
        lines.append(str(m["i"]))
        lines.append(f"{fmt_srt(m['start'])} --> {fmt_srt(m['end'])}")
        lines.append(m["text"].replace("\n", " "))
        lines.append("")
    return "\n".join(lines)


def build_doc(args, seg_meta, total, W, H, n_bg, bg_gen=None):
    bg_gen = bg_gen or {}
    ori = "竖屏 9:16 (1080x1920)" if args.orientation == "vertical" else "横屏 16:9 (1920x1080)"
    voices_desc = " / ".join(f"{vk}({VOICES[vk][1]})" for vk in
                             dict.fromkeys(m["vk"] for m in seg_meta))
    lines = [
        f"# 《{args.title}》剪辑详情",
        "",
        "## 基本信息",
        f"- 总时长: {fmt_ts(total)}（{len(seg_meta)} 段配音）",
        f"- 画面比例: {ori}",
        f"- 配音音色: {voices_desc}",
        "- 风格参考: B站「二狗的散文诗」类（词 + 背景图/片段 + BGM + 字幕）",
        "",
        "## 分镜表",
        "",
        "| 镜号 | 时间段 | 画面建议 | 配音文本 | 音色 | 素材文件 | 转场 |",
        "|---|---|---|---|---|---|---|",
    ]
    for m in seg_meta:
        disp = m["text"].replace("\n", "／")
        if len(disp) > 26:
            disp = disp[:26] + "…"
        if m["i"] in bg_gen:
            bg = f"背景图 ✅ images/{bg_gen[m['i']].name}"
        elif n_bg:
            bg = f"背景图{(m['i'] - 1) % len(BG_SUGGEST) + 1}"
        else:
            bg = "渐变底色"
        lines.append(
            f"| {m['i']} | {fmt_ts(m['start'])}-{fmt_ts(m['end'])} | {bg} | {disp} | "
            f"{m['style']} | audio/{m['mp3']} | 淡入淡出 0.5s |"
        )
    lines += [
        "",
        "## 素材清单",
        "",
        "### 配音（已生成 ✅ 直接拖剪映）",
    ]
    for m in seg_meta:
        lines.append(f"- `audio/{m['mp3']}` — {m['style']}，{m['dur']:.1f}s")
    if bg_gen:
        lines += ["", "### 背景图（已生成 ✅ 直接可用）"]
        for m in seg_meta:
            kw = BG_SUGGEST[(m["i"] - 1) % len(BG_SUGGEST)]
            lines.append(f"- 镜号{m['i']}: `images/{bg_gen[m['i']].name}`（意境: {kw}）")
    else:
        lines += ["", "### 背景图（需准备 🔧 每镜一张）"]
        for m in seg_meta:
            kw = BG_SUGGEST[(m["i"] - 1) % len(BG_SUGGEST)]
            lines.append(f"- 镜号{m['i']}（{fmt_ts(m['start'])}-{fmt_ts(m['end'])}）: 关键词「{kw}」→ AI生成/pexels/自己拍")
    lines += [
        "",
        "### 电影片段（可选 ⚠️ 注意版权）",
        "",
        "> ⚖️ 电影片段受著作权保护: 自娱自乐≈安全; 发B站(即使不盈利)是灰色地带, 可能被下架/限流; 商用(带货/接广告)高风险可被起诉。AI克隆演员声音属侵害声音权(民法典1023条, 已有判赔25万案例), 别碰。安全做法: 用无版权空镜/官方TTS音色。",
    ]
    for i, m in enumerate(seg_meta[: len(CLIP_SUGGEST)]):
        lines.append(f"- 镜号{m['i']}: 场景建议「{CLIP_SUGGEST[i % len(CLIP_SUGGEST)]}」")
    lines += [
        "",
        "### BGM（需准备 🔧）",
        "- 建议: 纯钢琴/弦乐 慢速抒情, 剪映音乐库搜「治愈 钢琴」「纯音乐 慢」",
        "- 音量: 配音音量的 20-30%（垫底, 别盖过人声）",
        "",
        "## 剪映操作步骤",
        "1. 新建项目 → 比例选 9:16 或 16:9（与上表一致）",
        "2. 导入 `audio/` 全部 mp3 → 按分镜表顺序拖到主轨道",
        "3. 每段配音对齐位置 → 上方轨道放对应背景图/电影片段（时长=该段时长）",
        "4. 文本 → 导入字幕 `subtitles.srt`（或识别字幕后手改）",
        "5. 添加 BGM → 音量 20-30%",
        "6. 段间加转场「叠化」0.5s",
        "7. 导出 1080P 30fps",
        "",
        "## ⚖️ 法律提示",
        "配音用的是微软 edge-tts 官方音色（不模仿真人）✅。影视片段和 AI 模仿演员声音请严格遵守上文标注的风险边界。",
        "",
    ]
    return "\n".join(lines)


def _resolve_webui():
    """返回 (token, base_url); 不可用返回 (None, None)。"""
    token = os.environ.get("AUTH_TOKEN", "")
    if not token:
        for cand in (Path(os.environ.get("HERMES_WEB_UI_HOME", "") or ".") / ".token",
                     Path(os.environ.get("HERMES_WEBUI_STATE_DIR", "") or ".") / ".token",
                     Path.home() / ".hermes-web-ui" / ".token"):
            if cand.exists():
                token = cand.read_text().strip()
                break
    base = (os.environ.get("HERMES_WEB_UI_URL", "").rstrip("/")
            or f"http://127.0.0.1:{os.environ.get('PORT', '8648')}")
    if not token or not base:
        return None, None
    return token, base


def _call_fun_codex(token, base, prompt, size, out_png):
    """调 Web UI 图像端点。返回 (ok, err_code)。err_code='missing_fun_codex_provider' 时上层切 Bing。"""
    payload = json.dumps({
        "mode": "text", "prompt": prompt, "size": size, "output_path": str(out_png),
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/api/hermes/media/apikey-image-generate",
        data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            r = json.loads(resp.read().decode("utf-8"))
        if not r.get("ok") or not r.get("output_paths"):
            raise RuntimeError(f"API error: {json.dumps(r, ensure_ascii=False)[:200]}")
        return True, None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        try:
            code = json.loads(body).get("code", "")
        except Exception:
            code = ""
        return False, code
    except Exception as e:
        return False, str(e)


def _fetch_bing_all(segs, orientation, out_dir):
    """Bing 每日壁纸兜底(免费无key): 每段拉一张风景空镜, 裁剪到目标比例。"""
    result = {}
    got = []
    idx = 0
    while len(got) < len(segs) and idx < 40:
        u = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx={idx}&n=8&mkt=zh-CN"
        try:
            with urllib.request.urlopen(u, timeout=20) as resp:
                d = json.loads(resp.read().decode("utf-8"))
            items = d.get("images", [])
            if not items:
                break
            got += items
        except Exception as e:
            print(f"⚠️  Bing 壁纸获取失败: {e}", file=sys.stderr)
            break
        idx += 8
    if not got:
        return {}
    vf = ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
          if orientation == "vertical" else
          "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080")
    for i in range(min(len(segs), len(got))):
        out_jpg = out_dir / f"bg_{i + 1:02d}.jpg"
        if out_jpg.exists() and out_jpg.stat().st_size > 10000:
            result[i + 1] = out_jpg
            continue
        raw = out_dir / f"bg_{i + 1:02d}_raw.jpg"
        try:
            urllib.request.urlretrieve("https://www.bing.com" + got[i]["url"], raw)
            run(["ffmpeg", "-y", "-i", str(raw), "-vf", vf, "-q:v", "3", str(out_jpg)],
                timeout=60, retries=1)
            raw.unlink(missing_ok=True)
            result[i + 1] = out_jpg
            print(f"    bg {i + 1:02d} ✅ Bing壁纸 {out_jpg.name}")
        except Exception as e:
            print(f"⚠️  背景图 {i + 1} Bing 下载失败: {e} (该段用渐变底色)", file=sys.stderr)
            raw.unlink(missing_ok=True)
    return result


def gen_bg_images(segs, orientation, out_dir):
    """为每段生成背景图。优先级: fun-codex (Web UI 图像端点) -> Bing 每日壁纸 -> 渐变兜底。
    返回 {段号(1-based): Path}。
    """
    if not segs:
        return {}
    out_dir.mkdir(parents=True, exist_ok=True)
    token, base = _resolve_webui()
    if token and base:
        size = "1536x1024" if orientation == "horizontal" else "1024x1536"
        result = {}
        for i, seg in enumerate(segs):
            kw = BG_SUGGEST[i % len(BG_SUGGEST)]
            out_png = out_dir / f"bg_{i + 1:02d}.png"
            if out_png.exists() and out_png.stat().st_size > 10000:
                result[i + 1] = out_png
                print(f"    bg {i + 1:02d} 复用已有: {out_png.name}")
                continue
            prompt = f"{kw}，电影感空镜，无人，柔和光线，深色调氛围，高清摄影"
            ok, err = _call_fun_codex(token, base, prompt, size, out_png)
            if ok:
                print(f"    bg {i + 1:02d} ✅ 已生成 {out_png.name} ({kw[:14]}…)")
                result[i + 1] = out_png
                continue
            if err == "missing_fun_codex_provider":
                print("    fun-codex 未配置, 改用 Bing 每日壁纸兜底…")
                out_png.unlink(missing_ok=True)
                return _fetch_bing_all(segs, orientation, out_dir)
            print(f"⚠️  背景图 {i + 1} 生成失败: {err} (该段用渐变底色)", file=sys.stderr)
            out_png.unlink(missing_ok=True)
        return result
    print("    Web UI 不可用, 改用 Bing 每日壁纸兜底…")
    return _fetch_bing_all(segs, orientation, out_dir)


def tts_dir_guard(parts_dir, segs, voice_keys):
    """内容哈希防护: 文本/音色变了就清空 parts 重配, 避免旧配音被静默复用。"""
    h = hashlib.md5(("\n\n".join(segs) + "|" + ",".join(voice_keys)).encode("utf-8")).hexdigest()
    hf = parts_dir / ".hash"
    if parts_dir.exists() and hf.exists() and hf.read_text().strip() == h:
        return True  # 同文本续跑, 可复用
    if parts_dir.exists():
        for p in parts_dir.iterdir():
            if p.is_file():
                p.unlink()
    parts_dir.mkdir(parents=True, exist_ok=True)
    hf.write_text(h, encoding="utf-8")
    return False


def run_video_mode(args, segs, voice_keys, bg_files, W, H, out_root):
    project = Path(args.project_dir or (Path.home() / "poem-video")).expanduser()
    template = Path(__file__).resolve().parent.parent / "templates" / "poem-video"
    if not project.exists():
        print(f"[1/6] 复制模板 -> {project}")
        shutil.copytree(template, project)
    work = project / "public" / "parts"
    tts_dir_guard(work, segs, voice_keys)
    imgs_dir = project / "public" / "images"
    imgs_dir.mkdir(parents=True, exist_ok=True)
    img_map = {}
    bg_gen = {}
    if bg_files:
        for i, bf in enumerate(bg_files):
            dst = imgs_dir / f"bg_{i + 1:02d}{bf.suffix.lower()}"
            if not dst.exists():
                shutil.copy2(bf, dst)
            img_map[i] = f"images/{dst.name}"
    elif args.gen_bg:
        print("    未提供 --bg-dir, 自动生成每段背景图…")
        bg_gen = gen_bg_images(segs, args.orientation, imgs_dir)

    print(f"[2/6] TTS 配音 ({len(segs)} 段, 音色轮换: {','.join(voice_keys)})")
    segs_data = []
    cursor = 0
    for i, s in enumerate(segs):
        vk = voice_keys[i % len(voice_keys)]
        mp3 = work / f"seg_{i + 1:02d}.mp3"
        if not (mp3.exists() and mp3.stat().st_size > 1000):
            tts_segment(vk, s, mp3, args.rate, args.pitch)
        dur = duration_sec(mp3)
        to_f = cursor + max(1, round(dur * FPS))
        img = None
        if bg_files:
            img = img_map[i % len(bg_files)]
        elif bg_gen and (i + 1) in bg_gen:
            img = f"images/{bg_gen[i + 1].name}"
        segs_data.append({
            "text": s,
            "audio": f"parts/seg_{i + 1:02d}.mp3",
            "from": cursor,
            "to": to_f,
            "image": img,
            "fontSize": pick_font_size(len(s), args.orientation),
            "vertical": args.vertical_text,
        })
        print(f"    seg {i + 1:02d} [{vk}] {dur:5.1f}s  {s[:24]}…" if len(s) > 24
              else f"    seg {i + 1:02d} [{vk}] {dur:5.1f}s  {s}")
        cursor = to_f
    total = cursor

    print(f"[3/6] 写 src/data.ts (总 {total / FPS:.1f}s / {total} 帧)")
    bgm_val = "null"
    if args.bgm and Path(args.bgm).exists():
        shutil.copy2(args.bgm, project / "public" / "bgm.mp3")
        bgm_val = '"bgm.mp3"'
    seg_json = ",\n".join("  " + json.dumps(sg, ensure_ascii=False) for sg in segs_data)
    data_ts = (
        "export type Segment = {\n"
        "  text: string;\n"
        "  audio: string;\n"
        "  from: number;\n"
        "  to: number;\n"
        "  image?: string;\n"
        "  fontSize: number;\n"
        "  vertical: boolean;\n"
        "};\n"
        "\n"
        f"export const FPS = {FPS};\n"
        f"export const WIDTH = {W};\n"
        f"export const HEIGHT = {H};\n"
        f"export const BGM: string | null = {bgm_val};\n"
        f"export const SEGMENTS: Segment[] = [\n{seg_json}\n];\n"
        f"export const TOTAL_FRAMES = {total};\n"
    )
    (project / "src" / "data.ts").write_text(data_ts, encoding="utf-8")

    print("[4/6] 检查中文字体")
    check_cjk_fonts()

    print("[5/6] 渲染 MP4 (首次需 npm 已装好; 若报错先 cd 项目跑 npm install)")
    out_mp4 = out_root / f"{args.title}.mp4"
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    run(["npx", "remotion", "render", "poem", str(out_mp4)], timeout=600, retries=1, cwd=str(project))

    print(f"[6/6] ✅ 完成: {out_mp4}")
    print(f"    总时长 {total / FPS:.1f}s | 音色 {','.join(voice_keys)} | 大小 "
          f"{out_mp4.stat().st_size / 1024 / 1024:.1f}MB")
    print("    如需发B站: 文案/背景图/音乐自创或无版权素材可放心; 影视片段有下架风险(见SKILL.md法律提示)")


def run_script_mode(args, segs, voice_keys, bg_files, W, H, out_root):
    audio_dir = out_root / "audio"
    tts_dir_guard(audio_dir, segs, voice_keys)
    print(f"[1/5] TTS 配音 ({len(segs)} 段, 音色轮换: {','.join(voice_keys)})")
    seg_meta = []
    base = 0.0
    for i, s in enumerate(segs):
        vk = voice_keys[i % len(voice_keys)]
        voice_full, vstyle = VOICES[vk]
        mp3 = audio_dir / f"seg_{i + 1:02d}_{vk}.mp3"
        if not (mp3.exists() and mp3.stat().st_size > 1000):
            tts_segment(vk, s, mp3, args.rate, args.pitch)
        dur = duration_sec(mp3)
        seg_meta.append({
            "i": i + 1, "text": s, "vk": vk, "voice": voice_full, "style": vstyle,
            "mp3": mp3.name, "dur": dur, "start": base, "end": base + dur,
        })
        print(f"    seg {i + 1:02d} [{vk}] {dur:5.1f}s  {s[:24]}…" if len(s) > 24
              else f"    seg {i + 1:02d} [{vk}] {dur:5.1f}s  {s}")
        base += dur
    total = base

    bg_gen = {}
    if not bg_files and args.gen_bg:
        print("    未提供 --bg-dir, 自动生成每段背景图…")
        bg_gen = gen_bg_images(segs, args.orientation, out_root / "images")

    print(f"[2/5] 背景图 ({len(bg_gen)} 段已生成)" if bg_gen else "[2/5] 背景图: 无 (渐变底色兜底)")
    print(f"[3/5] 写 subtitles.srt")
    (out_root / "subtitles.srt").write_text(build_srt(seg_meta), encoding="utf-8")

    print(f"[4/5] 写 剪辑详情.md")
    (out_root / "剪辑详情.md").write_text(
        build_doc(args, seg_meta, total, W, H, len(bg_files), bg_gen), encoding="utf-8")

    print(f"[5/5] ✅ 完成: {out_root}")
    print(f"    配音 {len(seg_meta)} 段 / 总时长 {fmt_ts(total)} / 音色: {args.voices}")
    print("    交付: 剪辑详情.md + audio/*.mp3 + subtitles.srt → 拖进剪映按分镜表剪")
    print("    ⚖️ 提示: 配音为官方TTS音色✅; 电影片段/BGM注意版权(见剪辑详情.md)")


def main():
    ap = argparse.ArgumentParser(description="散文诗/诗词视频流水线 (prose-poetry-video skill)")
    ap.add_argument("--text", required=True, help="文本文件路径(空行分段)")
    ap.add_argument("--mode", choices=["video", "script"], default="video",
                    help="video=一键出片 / script=剪辑详情+素材(剪映)")
    ap.add_argument("--title", default="散文诗", help="视频标题/文档标题")
    ap.add_argument("--voices", default="xiaoxiao", help="音色key逗号分隔,自动轮换. 可用: " + ",".join(VOICES))
    ap.add_argument("--rate", default="+4%", help="语速, 朗诵偏慢")
    ap.add_argument("--pitch", default="+0Hz", help="音高, 低沉段用 -10Hz")
    ap.add_argument("--orientation", choices=["horizontal", "vertical"], default="horizontal")
    ap.add_argument("--vertical-text", action="store_true", help="文字竖排(适合诗词)")
    ap.add_argument("--bg-dir", default=None, help="背景图目录(可选,轮换分配); 不传则自动生成")
    ap.add_argument("--gen-bg", action="store_true", default=True,
                    help="无 --bg-dir 时自动生成每段背景图(默认开, 需 Web UI 在跑)")
    ap.add_argument("--no-gen-bg", dest="gen_bg", action="store_false", help="关闭自动生成背景图")
    ap.add_argument("--bgm", default=None, help="BGM mp3(可选,Mode A用)")
    ap.add_argument("--out", default="work", help="输出目录")
    ap.add_argument("--project-dir", default=None, help="Mode A: Remotion项目目录(默认 ~/poem-video)")
    ap.add_argument("--dry-run", action="store_true", help="只解析分段打印预览")
    args = ap.parse_args()

    text = Path(args.text).read_text(encoding="utf-8")
    segs = parse_segments(text)
    if not segs:
        print("错误: 文本为空或未按空行分段", file=sys.stderr)
        sys.exit(1)
    voice_keys = [v.strip() for v in args.voices.split(",") if v.strip()]
    for v in voice_keys:
        if v not in VOICES:
            print(f"错误: 未知音色 {v}, 可用: {','.join(VOICES)}", file=sys.stderr)
            sys.exit(1)

    if args.dry_run:
        print(f"共 {len(segs)} 段, 音色轮换: {','.join(voice_keys)}")
        for i, s in enumerate(segs):
            print(f"  [{i + 1:02d}] ({voice_keys[i % len(voice_keys)]}) len={len(s)}  {s[:50]}")
        print("总字数:", sum(len(s) for s in segs))
        return

    bg_files = []
    if args.bg_dir:
        bg_dir = Path(args.bg_dir)
        bg_files = sorted([p for p in bg_dir.iterdir()
                           if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")])
        if not bg_files:
            print("⚠️  --bg-dir 下没有图片, 用渐变底色兜底", file=sys.stderr)

    W, H = (1920, 1080) if args.orientation == "horizontal" else (1080, 1920)
    out_root = Path(args.out).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    if args.mode == "video":
        run_video_mode(args, segs, voice_keys, bg_files, W, H, out_root)
    else:
        run_script_mode(args, segs, voice_keys, bg_files, W, H, out_root)


if __name__ == "__main__":
    main()
