# Z-Image-Turbo NVFP4 Setup (6GB VRAM)

Z-Image-Turbo is Alibaba's 6B parameter DiT model. The full BF16 version
requires 16GB+ VRAM, but the Comfy-Org NVFP4 quantized version runs on **6GB**.

## Model Files (Comfy-Org Single-File Format)

Use Comfy-Org's single-file wrappers, NOT Tongyi-MAI's diffusers format:

| Component | File | Size | Location |
|-----------|------|------|----------|
| DiT (NVFP4) | `z_image_turbo_nvfp4.safetensors` | 4.2GB | `models/diffusion_models/` |
| Text Encoder (FP4) | `qwen_3_4b_fp4_mixed.safetensors` | 3.3GB | `models/text_encoders/` |
| VAE (Flux AE) | `ae.safetensors` | 320MB | `models/vae/` |

Source: `https://hf-mirror.com/Comfy-Org/z_image_turbo` (use hf-mirror in China,
NOT huggingface.co which is blocked by GFW).

## Download (China / GFW)

```bash
# VAE first (small, validates mirror works)
curl -L -H "User-Agent: Mozilla/5.0" \
  -o ~/comfy/ComfyUI/models/vae/z_image_ae.safetensors \
  "https://hf-mirror.com/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors"

# DiT NVFP4
curl -L -H "User-Agent: Mozilla/5.0" \
  -o ~/comfy/ComfyUI/models/diffusion_models/z_image_turbo_nvfp4.safetensors \
  "https://hf-mirror.com/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo_nvfp4.safetensors"

# Text Encoder FP4
curl -L -H "User-Agent: Mozilla/5.0" \
  -o ~/comfy/ComfyUI/models/text_encoders/qwen_3_4b_fp4.safetensors \
  "https://hf-mirror.com/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b_fp4_mixed.safetensors"
```

**CRITICAL:** Do NOT append `?download=true` to hf-mirror URLs — it causes
redirect loops that result in 0 bytes/sec downloads.

## Workflow Setup

Get the example workflow from:
`https://comfyanonymous.github.io/ComfyUI_examples/z_image/`

Download `z_image_turbo_example.png` — it has the workflow embedded as PNG metadata.

### Editor → API Format Conversion

The embedded workflow is editor format (nodes have `type`, not `class_type`).
Must convert to API format before submitting to `/api/prompt`:

- Replace `"type"` with `"class_type"`
- Convert `inputs` from list to dict: `{"input_name": value_or_link}`
- Links become `["src_node_id", src_slot]` arrays
- Remove `pos`, `size`, `flags`, `mode`, `order`, `properties`, `color`, `bgcolor`
- Remove Note nodes (they cause `missing_node_type` errors in API mode)
- `widgets_values` become named `inputs` dict entries (e.g. `seed`, `steps`, `cfg`)

### Key Parameters for 6GB VRAM

- Resolution: **512×768** (safe), 768×1024 may OOM
- Steps: 9 (Turbo model, 8 NFEs)
- CFG: 1.0 (guidance should be 0 for Turbo)
- Sampler: euler, scheduler: simple
- Text encoder type: `lumina2`

## Nodes Required

All standard ComfyUI built-in nodes — no custom nodes needed:
- UNETLoader → loads DiT model
- CLIPLoader → loads text encoder (type=lumina2)
- VAELoader → loads VAE
- ModelSamplingAuraFlow → shift=3
- EmptySD3LatentImage → generates 16-channel latents (not 4 like SD1.5)
- KSampler → euler/simple, steps=9, cfg=1
- CLIPTextEncode → prompt encoding
- VAEDecode + SaveImage

## Chinese Prompt Support

Z-Image-Turbo natively supports Chinese prompts. Excellent for:
- 国风/水墨画
- 亚洲人脸
- 中文文字渲染
- 汉服、古建筑等传统文化元素

## Performance (RTX 3050 6GB)

- Generation time: ~55 seconds for 512×768
- VRAM usage: ~5GB peak (within 6GB budget)
- Output: ~600KB PNG
