# Model VRAM Requirements for Low-VRAM GPUs (≤6GB)

Quick lookup for which models can/can't run on 6GB cards (RTX 3050, GTX 1660, etc.).

## Compatible (tested on 6GB)

| Model | File Size | VRAM Usage | Quality | Notes |
|-------|-----------|------------|---------|-------|
| Dreamshaper 8 (SD 1.5-based) | ~2GB | ~3-4GB | Good (best for 6GB) | 512×768 stable, 4-6 consecutive gens before OOM risk |
| SD 1.5 pruned-emaonly | ~4GB | ~5-6GB | Decent | Tight, may OOM at higher resolutions |

## NOT Compatible (won't fit 6GB)

| Model | Params | File Size | Min VRAM | Notes |
|-------|--------|-----------|----------|-------|
| SDXL | 2.6B | ~6.5GB | 8GB | Won't load on 6GB |
| Z-Image-Turbo | 6B | ~30GB (BF16) | **16GB** | 6B DiT, even Q2_K GGUF (3.5GB DiT) + FP4 text encoder (3.3GB) + VAE (320MB) = 7GB+ minimum. Not viable on 6GB. |
| Flux Dev fp8 | 12B | ~12GB | 12GB+ | Way too large |

## Z-Image-Turbo Details

- **HuggingFace:** `Tongyi-MAI/Z-Image-Turbo` (mirror: `hf-mirror.com/Tongyi-MAI/Z-Image-Turbo`)
- **Architecture:** Single-Stream DiT (S3-DiT), Diffusers format
- **ComfyUI wrapper:** `Comfy-Org/z_image_turbo` (has NVFP4 quantization at 4.3GB for DiT)
- **GGUF quantized:** `unsloth/Z-Image-Turbo-GGUF` (Q2_K: 3.5GB, Q4_K_M: 4.8GB for DiT only)
- **Text encoder:** Qwen 3 4B (~7.7GB BF16, ~3.3GB FP4)
- **Generated resolution:** 1024×1024 typical
- **8 steps** inference (Turbo), no CFG (guidance_scale=0)
- **Verdict for 6GB:** Cannot run — even with Q2_K GGUF + FP4 text encoder, total model + runtime memory exceeds 6GB

## Downloading Behind GFW

Use `hf-mirror.com` as HuggingFace mirror:
```bash
# API search
curl -s "https://hf-mirror.com/api/models?search=MODEL_NAME&limit=5"

# Check model files/sizes
curl -s "https://hf-mirror.com/api/models/ORG/MODEL?blobs=true"

# Download with resume support
curl -L -C - -H "User-Agent: Mozilla/5.0" \
  "https://hf-mirror.com/ORG/MODEL/resolve/main/file.safetensors" \
  -o file.safetensors
```

Always verify file size after download — HF redirects can produce truncated files.
