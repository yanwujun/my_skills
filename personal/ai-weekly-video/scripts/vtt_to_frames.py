#!/usr/bin/env python3
"""Parse VTT subtitle file into Remotion frame-aligned TypeScript array.

Usage:
    python3 vtt_to_frames.py public/narration_YYYYMMDD.vtt

Output: TypeScript array of { from, to, text } with 30fps frame numbers.
"""

import re, sys

vtt_path = sys.argv[1] if len(sys.argv) > 1 else "public/narration.vtt"

with open(vtt_path) as f:
    vtt = f.read()

cues = []
for block in vtt.strip().split("\n\n"):
    lines = block.strip().split("\n")
    if len(lines) < 2:
        continue
    
    time_match = re.match(
        r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[.,](\d{3})",
        lines[1]
    )
    if not time_match:
        continue
    
    h1, m1, s1, ms1, h2, m2, s2, ms2 = [int(x) for x in time_match.groups()]
    start_s = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
    end_s = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000
    
    text = "".join(lines[2:])
    cues.append({
        "start_f": int(start_s * 30),
        "end_f": int(end_s * 30),
        "text": text,
        "start_s": start_s,
        "end_s": end_s,
    })

print("const SUBTITLES = [")
for c in cues:
    escaped = c["text"].replace("\\", "\\\\").replace('"', '\\"')
    print(f'  {{ from: {c["start_f"]}, to: {c["end_f"]}, text: "{escaped}" }},')
print("];")
print(f"\n// {len(cues)} cues, {cues[-1]['end_s']:.1f}s, DURATION={cues[-1]['end_f']}")
