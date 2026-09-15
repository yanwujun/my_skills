# Z-Image-Turbo on ComfyUI (NVFP4 — 6GB VRAM)

Z-Image-Turbo is Alibaba's 6B-parameter image model. Official requirement is 16GB VRAM,
but the **Comfy-Org NVFP4 quantized version runs on 6GB cards** (RTX 3050 confirmed).

## Model Files

Download from `https://hf-mirror.com/Comfy-Org/z_image_turbo` (use hf-mirror in China):

| File | Size | Destination |
|------|------|-------------|
| `split_files/diffusion_models/z_image_turbo_nvfp4.safetensors` | 4.3GB | `models/diffusion_models/` |
| `split_files/text_encoders/qwen_3_4b_fp4_mixed.safetensors` | 3.3GB | `models/text_encoders/` |
| `split_files/vae/ae.safetensors` | 320MB | `models/vae/` |

**PITFALL — `?download=true` breaks hf-mirror downloads**: Remove `?download=true` from URLs.
The correct URL format is:
```
https://hf-mirror.com/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo_nvfp4.safetensors
```
Always add `-H "User-Agent: Mozilla/5.0"` header. Downloads at ~3-4MB/s on hf-mirror.

## Workflow

Uses **standard ComfyUI built-in nodes** — no custom nodes needed:

```
UNETLoader    → z_image_turbo_nvfp4.safetensors, weight_dtype=default
CLIPLoader    → qwen_3_4b_fp4.safetensors, type=lumina2, device=default
VAELoader     → ae.safetensors (Flux VAE)
ModelSamplingAuraFlow → shift=3
EmptySD3LatentImage   → 512x768 or 768x1024
KSampler      → steps=9, cfg=1.0, sampler=euler, scheduler=simple
```

## Parameters

- **Steps**: 9 (Turbo model, CFG=0, 8 effective DiT forwards)
- **CFG**: 1.0 (no classifier-free guidance for Turbo)
- **Sampler**: euler, simple scheduler
- **Resolution**: 512×768 stable on 6GB; 768×1024 may work
- **Speed**: ~55 seconds per 512×768 image on RTX 3050 6GB
- **Peak VRAM**: ~5GB during generation
- **Seed**: positive integer only (NOT -1); use `control_after_generate: "randomize"` for random seeds

## API Format Workflow Notes

Z-Image workflows from the PNG-embedded metadata are in **editor format** (with `type`, `pos`, `size`, `links` arrays).
Must convert to **API format** before POSTing to `/api/prompt`:

- Editor format: nodes have `type`, inputs are list of `{name, type, link}` objects, separate `links` array with `[link_id, src, src_slot, tgt, tgt_slot, type]`
- API format: nodes have `class_type`, inputs is a dict `{name: value_or_link}`, links are inline `[src_node_id, src_slot]`
- Remove `Note` nodes before submission — they cause `missing_node_type` errors
- Seed must be positive integer, not -1

## Chinese Prompt Support

Z-Image-Turbo natively understands Chinese prompts (uses Qwen 3 4B text encoder).
No need to translate to English. Quality is excellent for Chinese text understanding,
Asian faces, and traditional Chinese art styles (水墨画, 汉服, 国风).
