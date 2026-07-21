# Image Generation Approaches for Comic Projects

## Decision Matrix

| Method | Quality | Cost | Speed | VRAM | Setup Time |
|--------|---------|------|-------|------|------------|
| apikey-image-gen (GPT Image) | ★★★★ | API credits | ~30s/image | N/A | 1 min (needs fun-codex key) |
| ComfyUI + SD 1.5 | ★★ | Free | ~15s/image | 4GB+ | 20-30 min (WSL) |
| ComfyUI + Dreamshaper 8 | ★★★★ | Free | ~15s/image | 4GB+ | 20-30 min (WSL) |
| ComfyUI + SDXL | ★★★★ | Free | ~30s/image | 8GB+ | 20-30 min (WSL) |
| ComfyUI + Flux Dev fp8 | ★★★★★ | Free | ~60s/image | 12GB+ | 20-30 min (WSL) |
| Midjourney | ★★★★★ | Subscription | ~30s/image | N/A | Manual (Discord) |
| DALL-E 3 | ★★★★ | API credits | ~30s/image | N/A | Via ChatGPT Plus |

## Method 1: apikey-image-gen (Recommended if API key available)

Requires: `fun-codex` provider in `~/.hermes/config.yaml`

```yaml
custom_providers:
  - name: fun-codex
    base_url: https://api.apikey.fun/v1
    api_key: <your-key>
    model: gpt-5.5
    api_mode: codex_responses
```

Generate via Hermes Web UI endpoint:
```bash
curl -sS -X POST "http://127.0.0.1:8648/api/hermes/media/apikey-image-generate" \
  -H "Authorization: Bearer $(cat ~/.hermes-web-ui/.token)" \
  -H 'Content-Type: application/json' \
  -d '{
    "mode": "text",
    "prompt": "<English prompt from prompts/*.md>",
    "size": "1024x1536",
    "output_path": "/absolute/path/to/output.png"
  }'
```

Size options for 3:4 ratio: `1024x1536`

## Method 2: ComfyUI + Stable Diffusion (Local, Free)

Requires: NVIDIA GPU ≥6GB VRAM, ~20-30 min setup on WSL

### WSL Installation Pitfalls

**pipx not available**: WSL Debian/Ubuntu often lacks pipx. Use `uvx` instead:
```bash
# Install via uvx (no pipx needed)
uvx --from comfy-cli comfy --version
```

**Missing dependencies after install**: ComfyUI install via comfy-cli may leave deps unresolved. After install, manually install in the venv:
```bash
~/comfy/ComfyUI/.venv/bin/pip install sqlalchemy alembic pyyaml blake3 tqdm aiohttp scipy psutil
```

**Model download timeout**: `comfy model download` may timeout for large files. Use direct curl instead:
```bash
cd ~/comfy/ComfyUI/models/checkpoints/
curl -L -o v1-5-pruned-emaonly.safetensors \
  "https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors" \
  --progress-bar
```

**Incomplete model download → safetensors error**: If ComfyUI throws `SafetensorError: incomplete metadata`, the model file is corrupted (usually from a timed-out download). Delete and re-download:
```bash
rm ~/comfy/ComfyUI/models/checkpoints/<model>.safetensors
# Re-download with curl -L (follow redirects)
```

**HuggingFace redirect issue**: Some HF model URLs return HTML redirect pages (15 bytes) instead of actual files. Always verify file size after download:
```bash
ls -lh ~/comfy/ComfyUI/models/checkpoints/<model>.safetensors
# Should be ~2-4GB for SD 1.5 class models, NOT 15 bytes
```

**ComfyUI crashes after multiple generations**: On low-VRAM cards, ComfyUI may crash/hang after 4-6 consecutive generations. Restart between batches:
```bash
uvx --from comfy-cli comfy stop
sleep 2
uvx --from comfy-cli comfy launch --background
sleep 5
```

### Model Recommendations for 6GB VRAM

| Model | Size | Quality (manga) | Notes |
|-------|------|-----------------|-------|
| v1-5-pruned-emaonly | 4.0GB | ★★ | Vanilla SD 1.5, poor manga quality |
| **Dreamshaper 8** | 2.0GB | ★★★★ | **Best for manga on 6GB**, anime-tuned |
| SDXL base | 6.5GB | ★★★★ | Won't fit in 6GB VRAM |

**Dreamshaper 8 download** (recommended):
```bash
cd ~/comfy/ComfyUI/models/checkpoints/
curl -L -o dreamshaper_8.safetensors \
  -H "User-Agent: Mozilla/5.0" \
  "https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors"
```

### Full Setup (WSL + RTX 3050 6GB)

```bash
# 1. Install comfy-cli via uvx
uvx --from comfy-cli comfy --skip-prompt tracking disable

# 2. Install ComfyUI
uvx --from comfy-cli comfy --skip-prompt install --nvidia

# 3. Fix missing deps
~/comfy/ComfyUI/.venv/bin/pip install sqlalchemy alembic pyyaml blake3 tqdm aiohttp scipy psutil

# 4. Download Dreamshaper 8 (NOT vanilla SD 1.5)
cd ~/comfy/ComfyUI/models/checkpoints/
curl -L -o dreamshaper_8.safetensors \
  -H "User-Agent: Mozilla/5.0" \
  "https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors"

# 5. Verify model
ls -lh dreamshaper_8.safetensors  # Should be ~2.0GB
file dreamshaper_8.safetensors    # Should say "data", not "ASCII text"

# 6. Launch
uvx --from comfy-cli comfy launch --background
sleep 5
curl -s http://127.0.0.1:8188/system_stats  # Verify server

# 7. Generate using batch script
python3 ~/.hermes/skills/creative/comic-manga-creation/scripts/comfyui_batch_generate.py
```

## Batch Generation Script Pattern

The reusable script is at `scripts/comfyui_batch_generate.py`. To use for your project:

1. Copy the script to your project directory
2. Edit the `PAGES` list with your prompts (extract from `prompts/*.md` files)
3. Set `MODEL` to your checkpoint filename
4. Run: `python3 generate_comic.py`

The script handles: workflow construction → API submission → polling → output download.

## Prompt Engineering Tips for Comic Panels

- Always include "manga art style" or "comic panel style" at the start
- Specify aspect ratio explicitly (3:4 portrait for single panels)
- Include lighting direction and color temperature
- Character descriptions must be consistent across all panels (copy from characters.md)
- Add "detailed, professional quality, sharp lines" for cleaner output
- Negative prompt: "low quality, blurry, deformed, extra fingers, watermark"
- For Dreamshaper 8: add "masterpiece, best quality" at end of positive prompt
