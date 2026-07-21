"""
Parse edge-tts VTT subtitle file into Remotion frame-accurate TypeScript constant.

Usage:
  python3 vtt_to_subtitles.py narration.vtt 30 > subtitles.ts

  Where 30 is the FPS of your Remotion composition.
"""

import re
import sys

def ts_to_frames(ts, fps):
    parts = ts.replace(",", ".").split(":")
    h, m = int(parts[0]), int(parts[1])
    s = float(parts[2])
    total = h * 3600 + m * 60 + s
    return max(0, int(total * fps))

def main():
    vtt_path = sys.argv[1]
    fps = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    with open(vtt_path) as f:
        content = f.read()

    entries = []
    blocks = re.split(r'\n\n+', content.strip())
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 2 or lines[0].startswith("WEBVTT"):
            continue

        ts_match = re.match(r'(\S+)\s*-->\s*(\S+)', lines[1] if len(lines) > 1 else lines[0])
        if not ts_match:
            continue

        start = ts_to_frames(ts_match.group(1), fps)
        end = ts_to_frames(ts_match.group(2), fps)
        dur = max(30, end - start)  # minimum 1 second

        text = lines[2] if len(lines) > 2 else lines[0]
        if text.isdigit():
            continue
        # Replace paired ASCII double-quotes with Chinese angle quotes
        # to avoid esbuild "Unexpected backslash in JSX element" errors.
        # Strategy: swap " with 「 then 」 alternately.
        parts = text.split('"')
        clean = parts[0]
        for i, p in enumerate(parts[1:], 1):
            clean += ('「' if i % 2 == 1 else '」') + p
        text = clean

        entries.append((start, dur, text))

    # Merge very short adjacent entries
    merged = []
    i = 0
    while i < len(entries):
        start, dur, text = entries[i]
        if dur < 40 and i + 1 < len(entries):
            _, nd, nt = entries[i + 1]
            merged.append((start, dur + nd, text + nt))
            i += 2
        else:
            merged.append((start, dur, text))
            i += 1

    print(f"// Auto-generated from {vtt_path} — {len(merged)} subtitle blocks")
    print("const SUBTITLES = [")
    for start, dur, text in merged:
        print(f'  {{ start: {start}, dur: {dur}, text: "{text}" }},')
    print("];")

if __name__ == "__main__":
    main()
