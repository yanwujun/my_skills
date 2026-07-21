# Z-Image-Turbo Batch Comic Generation Pattern

Proven execute_code pattern for generating comic pages sequentially with Z-Image-Turbo NVFP4 via ComfyUI REST API.

## Base Workflow (API Format)

The workflow uses built-in ComfyUI nodes only — no custom nodes required:

- `UNETLoader`: loads `z_image_turbo_nvfp4.safetensors` from `models/diffusion_models/`
- `CLIPLoader`: loads `qwen_3_4b_fp4.safetensors` (type=lumina2) from `models/text_encoders/`
- `VAELoader`: loads `z_image_ae.safetensors` from `models/vae/`
- `EmptySD3LatentImage`: resolution (512×768 or 768×1024)
- `ModelSamplingAuraFlow`: shift=3
- `KSampler`: steps=9, cfg=1.0, sampler=euler, scheduler=simple, seed ≥ 0
- 2× `CLIPTextEncode`: positive + negative prompts
- `VAEDecode`, `SaveImage`

## Batch Script Pattern

```python
import json, random, time
from hermes_tools import terminal

# Load base workflow (pre-converted to API format)
with open('/tmp/z_image_api.json') as f:
    wf = json.load(f)

# Remove Note node if present
wf.pop('15', None)

# Set shared params
wf['7']['inputs']['text'] = '模糊 低分辨率 像素化 变形 文字扭曲 低质量'
wf['3']['inputs']['steps'] = 9

pages = [("id", "name", "Chinese prompt string"), ...]

for pid, name, prompt in pages:
    wf['6']['inputs']['text'] = prompt
    wf['3']['inputs']['seed'] = random.randint(1, 2**32)
    
    payload = {"client_id": "comic", "prompt": wf}
    with open('/tmp/z_image_payload.json', 'w') as f:
        json.dump(payload, f, ensure_ascii=False)
    
    r = terminal(
        'curl -s -X POST http://127.0.0.1:8188/prompt '
        '-H "Content-Type: application/json" '
        '-d @/tmp/z_image_payload.json',
        timeout=10
    )
    resp = json.loads(r['output'])
    if 'error' in resp:
        print(f"ERROR: {resp['error']}")
        break
    
    # Wait for generation (55s 512×768, 95s 768×1024)
    time.sleep(95)
    
    # Poll until queue empty
    for _ in range(15):
        qr = terminal('curl -s http://127.0.0.1:8188/queue', timeout=5)
        q = json.loads(qr['output'])
        if not q['queue_running'] and not q['queue_pending']:
            break
        time.sleep(5)
    
    # Get latest output
    lr = terminal('ls -t ~/comfy/ComfyUI/output/Z-Image_*.png | head -1', timeout=5)
    latest = lr['output'].strip()
    terminal(f'cp {latest} ~/comic/project/{pid}-page.png', timeout=5)
    print(f"Page {pid} {name}: OK")
```

## Resolution Guidelines

| Resolution | Time | VRAM Peak | Quality | Use When |
|------------|------|-----------|---------|----------|
| 512×768 | ~55s | ~5.0GB | Acceptable | Quick drafts, character designs |
| 768×1024 | ~95s | ~5.5GB | Good | Final pages with text elements |

## Key Pitfalls

1. **?download=true kills hf-mirror speed** — drops from 3.7MB/s to 50KB/s
2. **Note node blocks /api/prompt** — must remove before submitting
3. **Seed must be ≥ 0** — KSampler rejects -1, use `random.randint(1, 2**32)`
4. **No `comfy restart`** — use `stop && launch --background`
5. **VRAM fragmentation** — restart ComfyUI every 4-5 pages
6. **Editor format ≠ API format** — workflows in PNG metadata need conversion (link IDs → `[source_node, output_slot]`)
7. **User expects clarity** — if they complain, bump resolution first before tweaking prompts
