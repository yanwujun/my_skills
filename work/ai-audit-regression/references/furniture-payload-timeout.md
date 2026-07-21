# Furniture Category Items with Full 国标 Text Cause API Timeouts

Furniture category items (会议桌, 办公桌, 沙发, 会议椅, 折叠椅, etc.) embed the complete national standard text in their `standardDescription` field or paramPairs. This produces payloads of 5,000-15,000+ characters per JSON body, causing the agents-platform API to hang or timeout.

## Affected Categories

All furniture categories in the framework agreement data:
- 会议桌, 办公桌, 会议椅, 办公椅, 沙发, 折叠椅, 茶几, 桌前椅, 屏风工位, 电脑桌

## Symptom

- Threaded `/threads/{id}/runs/wait` hangs indefinitely even with `--max-time 300`
- `subprocess.TimeoutExpired` after the full timeout period
- curl process remains alive and must be killed manually
- **Stateless** `/runs/wait` handles these items correctly (returns within normal time)

## Root Cause

The `standardDescription` field in furniture items contains the full text of national standards (GB/T, QB/T, etc.) — thousands of characters of dense technical text. When this is embedded in the API payload JSON, the agent's LLM hits context or recursion limits.

Example payload size for a typical furniture item (会议桌/渝新晟):
```
standardDescription length: ~8,000 chars
Total JSON payload: ~12,000 chars (before image_url blocks)
```

## Mitigation

1. **Use stateless mode** for furniture items — stateless handles large payloads correctly
2. **Reduce timeout** to 180s for threaded mode when furniture items are unavoidable
3. **Expect T/O** — accept that some furniture items will time out and mark them as T/O
4. **Skip in targeted retests** — if re-running only mismatched items, skip known problem items (会议桌/渝新晟)

## Real Example (2026-06-26)

会议桌/渝新晟: threaded mode caused curl to hang for 10+ minutes despite 300s `--max-time`. Stateless mode handled it normally. The item was skipped in the threaded retest batch.
