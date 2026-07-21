# VTT Sync Guide — Complete Recipe

## 1. Generate VTT alongside MP3

```bash
edge-tts --voice zh-CN-YunxiNeural --rate=+12% \
  -f narration.txt \
  --write-media public/narration.mp3 \
  --write-subtitles public/narration.vtt
```

## 2. Parse VTT to frame numbers

```python
import re

vtt = open("public/narration.vtt").read()
cues = []
for block in vtt.strip().split("\n\n"):
    lines = block.strip().split("\n")
    if len(lines) < 2: continue
    m = re.match(r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[.,](\d{3})", lines[1])
    if not m: continue
    h1,m1,s1,ms1, h2,m2,s2,ms2 = [int(x) for x in m.groups()]
    start_s = h1*3600 + m1*60 + s1 + ms1/1000
    end_s = h2*3600 + m2*60 + s2 + ms2/1000
    text = "".join(lines[2:])
    cues.append({
        "from": int(start_s * 30),
        "to": int(end_s * 30),
        "text": text,
    })

for c in cues:
    print(f"  {{ from: {c['from']}, to: {c['to']}, text: \"{c['text']}\" }},")
```

## 3. Embed in Video.tsx

```tsx
const SUBTITLES = [
  { from: 3, to: 99, text: "这周我翻 GitHub..." },
  // ... paste all parsed cues here
];

const ActiveSub: React.FC = () => {
  const frame = useCurrentFrame();
  const sub = SUBTITLES.find((s) => frame >= s.from && frame < s.to);
  if (!sub) return null;
  const opacity = interpolate(
    frame,
    [sub.from, sub.from + 4, sub.to - 4, sub.to],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  return (
    <div style={{ position: "absolute", bottom: 100, left: "50%",
      transform: "translateX(-50%)", opacity, zIndex: 10 }}>
      <div style={{ background: "rgba(0,0,0,0.72)", backdropFilter: "blur(14px)",
        borderRadius: 14, padding: "14px 34px", maxWidth: "88vw", textAlign: "center",
        border: "1px solid rgba(255,255,255,0.06)" }}>
        <p style={{ color: "#e8e8ee", fontSize: 34, fontWeight: 500, margin: 0,
          lineHeight: 1.5 }}>{sub.text}</p>
      </div>
    </div>
  );
};
```

## 4. Group cues into scenes, assign visuals

Each scene: `{from, durationInFrames, component}` aligned to VTT frame numbers.

Example:
```
Cue 34: frame 4415-4555 "第一，Agent 在向桌面和办公渗透..."
Cue 35: frame 4555-4739 "第二，LLM 基础设施在成熟..."
→ Scene "Summary": from=4415, duration=324, Component=<SummarySlide />
```

## 5. Verify

```bash
ffprobe -v quiet -show_entries format=duration -of csv=p=0 public/narration.mp3
# e.g. 169.56 → durationInFrames = 5088 (floor(169.56 * 30))
```
