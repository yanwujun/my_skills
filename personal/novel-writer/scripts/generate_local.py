#!/usr/bin/env python3
"""
Generate comic page images using local diffusers + Tiny SD model.
Fallback method when `image_generate` tool is unavailable.

Usage:
  python3 generate_local.py comic/{slug}/

Reads prompts from comic/{slug}/prompts/*.md
Outputs PNGs to comic/{slug}/

Prerequisites:
  pip install --break-system-packages diffusers transformers
  NVIDIA GPU with CUDA
  HuggingFace network access (proxy may be needed in WSL)
"""
import torch, sys, os, time
from pathlib import Path

# ── Proxy config (uncomment if in WSL) ──
# os.environ['HTTP_PROXY'] = 'http://127.0.0.1:8888'
# os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:8888'
# os.environ['http_proxy'] = 'http://127.0.0.1:8888'
# os.environ['https_proxy'] = 'http://127.0.0.1:8888'

os.environ['HF_HOME'] = os.path.expanduser('~/.cache/huggingface')

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_local.py comic/{slug}/")
        sys.exit(1)

    comic_dir = Path(sys.argv[1])
    if not comic_dir.exists():
        print(f"Directory not found: {comic_dir}")
        sys.exit(1)

    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"GPU: {torch.cuda.get_device_name(0)} ({vram:.1f}GB)")

    # ── Load model ──
    t0 = time.time()
    from diffusers import StableDiffusionPipeline
    print("Loading OFA-Sys/small-stable-diffusion-v0...", flush=True)
    pipe = StableDiffusionPipeline.from_pretrained(
        "OFA-Sys/small-stable-diffusion-v0",
        torch_dtype=torch.float32,
        safety_checker=None,
        requires_safety_checker=False,
    )
    pipe = pipe.to("cuda")
    print(f"  Loaded in {time.time()-t0:.1f}s", flush=True)

    # ── Collect prompts ──
    prompts_dir = comic_dir / 'prompts'
    prompt_files = sorted(prompts_dir.glob('*.md'))
    if not prompt_files:
        print(f"No prompt files found in {prompts_dir}")
        print("Falling back to inline generation (no prompt files needed).")
        return

    total = len(prompt_files)
    for i, pf in enumerate(prompt_files, 1):
        name = pf.stem  # e.g. "00-cover-circle-truth"
        out_path = comic_dir / f"{name}.png"

        # Skip existing
        if out_path.exists() and out_path.stat().st_size > 1000:
            print(f"[{i}/{total}] {name} - skip (exists)", flush=True)
            continue

        # Extract prompt from markdown
        text = pf.read_text()
        lines = text.split('\n')
        in_prompt = False
        prompt_lines = []
        for line in lines:
            if line.strip().startswith('## Generation Prompt'):
                in_prompt = True
                continue
            if in_prompt:
                if line.strip().startswith('#') or line.strip().startswith('---'):
                    break
                prompt_lines.append(line)
        prompt = '\n'.join(prompt_lines).strip()
        if not prompt:
            print(f"[{i}/{total}] {name} - no prompt found, skipping", flush=True)
            continue

        # ⚠️ CRITICAL: Tiny SD model chokes on prompts > 500 chars
        # Truncate to safe length
        if len(prompt) > 500:
            prompt = prompt[:500]
            print(f"  (prompt truncated to 500 chars)", flush=True)

        print(f"[{i}/{total}] {name} - 512x768...", flush=True)
        t1 = time.time()
        try:
            image = pipe(
                prompt=prompt,
                num_inference_steps=50,
                guidance_scale=7.5,
                width=512,
                height=768,
            ).images[0]
            image.save(str(out_path))
            kb = out_path.stat().st_size // 1024
            print(f"  ✓ {kb}KB ({time.time()-t1:.1f}s)", flush=True)
        except Exception as e:
            print(f"  ✗ FAILED: {e}", flush=True)
            continue

    # ── Summary ──
    print(f"\n=== DONE ===", flush=True)
    for f in sorted(comic_dir.glob('*.png')):
        print(f"  {f.name} ({f.stat().st_size//1024} KB)", flush=True)

if __name__ == '__main__':
    main()
