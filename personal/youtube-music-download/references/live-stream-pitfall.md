# Live Stream Detection Reference

## The Problem

Many YouTube music compilation videos are actually 24/7 live streams. yt-dlp treats them as endless downloads — it gets stuck downloading chunk-by-chunk via HLS at very slow speeds (<1 MiB/s) and may never finish.

## How to identify a live stream BEFORE downloading

```bash
yt-dlp --print "%(live_status)s | %(title)s" URL
```

**Safe values:**
- `not_live` — regular video, download normally
- `was_live` — completed live broadcast, now VOD, download normally

**Unsafe values:**
- `is_live` — currently broadcasting, DO NOT attempt to download

## What a stuck live stream download looks like

The download will show symptoms like:

```
[download]  89.2% of  152.24MiB at  Unknown B/s ETA Unknown
[download]  89.2% of  152.24MiB at  Unknown B/s ETA Unknown
```

Or very slow progress with `hls_chunk_host` in the URL:
```
...hls_chunk_host/rr2---sn-ojn4v5-5w.googlevideo.com...
```

Or it creates `.part` files that grow extremely slowly:
```
-rwxrwxrwx ... 62M ... Top Hits 2026 ... .webm.part
```

## What to do

1. Kill the process: `process(action='kill', session_id='...')`
2. Clean up `.part` and `.webm` files
3. Find a non-live alternative compilation
