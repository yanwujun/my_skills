# ComfyUI on WSL with Low VRAM (RTX 3050 / 6GB)

## Verified Setup (RTX 3050 6GB, WSL Ubuntu, CUDA 13.1)

### Install Steps

```bash
# comfy-cli via uvx (pipx often missing in WSL)
uvx --from comfy-cli comfy --skip-prompt tracking disable
uvx --from comfy-cli comfy --skip-prompt install --nvidia

# Fix missing deps that comfy-cli leaves behind
~/comfy/ComfyUI/.venv/bin/pip install sqlalchemy alembic pyyaml blake3 tqdm aiohttp scipy psutil

# Download model (see model table below)
cd ~/comfy/ComfyUI/models/checkpoints/
curl -L -o dreamshaper_8.safetensors \
  -H "User-Agent: Mozilla/5.0" \
  "https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors"

# Launch
uvx --from comfy-cli comfy launch --background
```

### Model Recommendations (6GB VRAM)

| Model | File | Size | Quality | Best For |
|-------|------|------|---------|----------|
| SD 1.5 | v1-5-pruned-emaonly.safetensors | 4.0GB | ★★ | General, poor style |
| **Dreamshaper 8** | dreamshaper_8.safetensors | 2.0GB | ★★★★ | Manga/anime (SD 1.5-based) |
| **Z-Image-Turbo NVFP4** | z_image_turbo_nvfp4.safetensors | 4.2GB | ★★★★★ | **Best quality 6GB** (6B param, 4-bit) |
| SDXL base | sd_xl_base_1.0.safetensors | 6.5GB | ★★★★ | Won't fit |

### Common Pitfalls

1. **Missing deps**: ComfyUI install doesn't resolve all deps. Always run the pip install line above.
2. **Model download corruption**: `comfy model download` can timeout. Use `curl -L` directly. Verify with `ls -lh` (>100MB) and `file` (must say "data", not "ASCII text").
3. **HuggingFace redirects**: Some URLs return 15-byte HTML. Add `-H "User-Agent: Mozilla/5.0"` to curl.
4. **OOM after 4-6 images**: ComfyUI leaks VRAM on low-end cards. Restart between batches: `uvx --from comfy-cli comfy stop && sleep 2 && uvx --from comfy-cli comfy launch --background`
5. **Server 500 errors**: Usually means model file is corrupted. Re-download.
6. **Free VRAM check**: `curl -s http://127.0.0.1:8188/system_stats | grep vram_free`

### Batch Generation

Use the REST API directly for batch work (more reliable than run_workflow.py for large batches):
```python
import json, urllib.request
data = json.dumps({"prompt": workflow_dict}).encode()
req = urllib.request.Request("http://127.0.0.1:8188/api/prompt", data=data,
    headers={"Content-Type": "application/json"})
result = json.loads(urllib.request.urlopen(req, timeout=60).read())
prompt_id = result["prompt_id"]
# Poll history/{prompt_id} until outputs appear
```

See `comic-manga-creation/scripts/comfyui_batch_generate.py` for a complete working example.

### Z-Image-Turbo NVFP4 (6GB VRAM, 6B params)

Best quality model for RTX 3050 6GB. Native Chinese prompt support, 9 steps. Timing: ~55s at 512×768, ~95s at 768×1024.

**Download (use hf-mirror.com in China, CRITICAL: NO `?download=true` param):**

**⚠️ PITFALL — `?download=true` kills speed**: Adding `?download=true` to hf-mirror URLs causes download speeds to drop from ~3.7MB/s to ~50KB/s (a 3.3GB file takes 23 minutes instead of 1.4 hours). NEVER append query params to the resolve URLs.
```bash
# DiT model (4.2GB) → models/diffusion_models/
curl -L -H "User-Agent: Mozilla/5.0" \
  -o ~/comfy/ComfyUI/models/diffusion_models/z_image_turbo_nvfp4.safetensors \
  "https://hf-mirror.com/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo_nvfp4.safetensors"

# Text Encoder FP4 (3.3GB) → models/text_encoders/
curl -L -H "User-Agent: Mozilla/5.0" \
  -o ~/comfy/ComfyUI/models/text_encoders/qwen_3_4b_fp4.safetensors \
  "https://hf-mirror.com/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b_fp4_mixed.safetensors"

# VAE (320MB) → models/vae/
curl -L -H "User-Agent: Mozilla/5.0" \
  -o ~/comfy/ComfyUI/models/vae/z_image_ae.safetensors \
  "https://hf-mirror.com/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors"
```

**Workflow config (API format):**
- UNETLoader: `z_image_turbo_nvfp4.safetensors`, weight_dtype=default
- CLIPLoader: `qwen_3_4b_fp4.safetensors`, type=lumina2
- VAELoader: `z_image_ae.safetensors`
- EmptySD3LatentImage: 512×768 or 768×1024
- KSampler: euler/simple, 9 steps, CFG=1.0, seed ≥ 0
- ModelSamplingAuraFlow: shift=3

**API format note:** Editor-format workflows from PNG metadata use `type`+`links` arrays. Must convert to API format: `class_type`+`inputs` dict, resolve link IDs to `[source_node_id, output_slot]`. The `/api/prompt` endpoint rejects editor format.

**VRAM:** Peak ~5GB at 512×768, ~5.5GB at 768×1024. Restart ComfyUI after 4-5 generations to avoid OOM from VRAM fragmentation.

**⚠️ PITFALL — `comfy restart` does not exist**: Use `uvx --from comfy-cli comfy stop && sleep 2 && uvx --from comfy-cli comfy launch --background` instead.

**⚠️ PITFALL — `Note` node blocks submission**: The example workflow from ComfyUI_examples contains a `Note` node (decorative comment). The `/api/prompt` endpoint rejects it with "Node 'Note' not found". Always remove the Note node from API-format workflows before submitting.

**⚠️ PITFALL — Seed must be ≥ 0**: KSampler `seed` input rejects -1 ("value smaller than min of 0"). Use `random.randint(1, 2**32)` for random seeds and set `control_after_generate` to "randomize".

**⚠️ PITFALL — Editor vs API format**: Workflows embedded in PNG metadata are editor format (use `type` + `links` arrays). Must convert to API format (`class_type` + `inputs` dict) before POSTing to `/api/prompt`. Link IDs must be resolved to `[source_node_id, output_slot]` arrays.

Reference workflow: `workflows/z_image_turbo_nvfp4.json`
