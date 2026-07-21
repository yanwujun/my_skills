---
name: youtube-music-download
description: Download music/audio from YouTube as MP3 — search for compilations, individual songs, or playlists. Covers yt-dlp audio extraction, live-stream detection, batch downloading, and WSL path handling.
tags: [music, youtube, audio, download, mp3, yt-dlp, ffmpeg]
---

# YouTube Music Download

Download music from YouTube as MP3 files using yt-dlp + ffmpeg. Supports searching for compilations, downloading specific videos, and batch processing.

## Prerequisites

- `yt-dlp` installed (`pip3 install yt-dlp --break-system-packages`)
- `ffmpeg` installed (`which ffmpeg`)

## Trigger conditions

- User asks to download music, songs, audio from YouTube
- User wants popular/hot/trending music compilations
- User needs audio extraction from any YouTube video to MP3

## Step 1: Search YouTube

Use yt-dlp's built-in YouTube search to find content without needing a browser:

```bash
# Search for compilations/playlists
yt-dlp --flat-playlist --print "%(title)s | %(webpage_url)s" "ytsearch20:search terms here"

# Examples:
yt-dlp --flat-playlist --print "%(title)s | %(webpage_url)s" "ytsearch20:2025 2026 热门歌曲 抖音"
yt-dlp --flat-playlist --print "%(title)s | %(webpage_url)s" "ytsearch20:2025 top hits playlist"
```

`--flat-playlist` keeps it fast — metadata only, no download.

## Step 2: CRITICAL — Check live_status BEFORE downloading

Many YouTube music compilations are actually **live streams** (24/7 radio-style). yt-dlp will get stuck on these, downloading at <1 MiB/s indefinitely or timing out. Always check first:

```bash
yt-dlp --print "%(live_status)s | %(title)s" URL1 URL2 URL3
```

- `not_live` or `was_live` → safe to download
- `is_live` → skip it, find another source

**This is the #1 pitfall.** Never skip this check.

## Step 3: Download with audio extraction

```bash
yt-dlp -x --audio-format mp3 --audio-quality 0 -o "/path/%(title)s.%(ext)s" URL1 URL2 URL3
```

Flags:
- `-x`: extract audio only
- `--audio-format mp3`: convert to MP3
- `--audio-quality 0`: best quality
- `-o`: output template (use `%(title)s.%(ext)s` for named files)

## Step 4: Run in background for large files

Downloads over ~50MB should use background mode with notification:

Use `terminal(background=true, notify_on_complete=true, timeout=600)`.

## Step 5: Clean up artifacts

yt-dlp leaves behind `.webm` (original) and `.part` (partial) files. Clean after completion:

```bash
rm -f "/path/"*.webm "/path/"*.part
```

## WSL: Windows drive paths

WSL mounts Windows drives under `/mnt/`:
- `C:\` → `/mnt/c/`
- `F:\音乐\` → `/mnt/f/音乐/`

Use `powershell.exe` to check drive existence if not mounted:
```bash
powershell.exe -Command "Get-PSDrive G -ErrorAction SilentlyContinue"
```

`sudo mount` may need password which is blocked — use `/mnt/<letter>/` for already-mounted drives.

## Pitfalls

1. **Live stream trap**: Most "24/7 music" compilation videos are live streams. ALWAYS check `live_status` first.
2. **Slow downloads**: Some videos have throttled CDN — try a different compilation source if speed drops below 1 MiB/s for extended periods.
3. **File cleanup**: `.webm` and `.part` files accumulate. Clean them after each batch.
4. **Filename length**: YouTube titles can be very long. The `%(title)s` template preserves the full title. This is fine on NTFS (Windows drives) but watch path length on Linux filesystems.
5. **yt-dlp JS runtime warning**: `WARNING: [youtube] No supported JavaScript runtime could be found` is cosmetic — downloads still work. Only relevant for very new YouTube formats.
