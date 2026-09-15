# Batch Image Generation via ComfyUI REST API

Pattern for generating multiple images from a list of prompts using ComfyUI's
REST API directly (no workflow JSON file needed — build the workflow in Python).

## When to use

- Generating a series of related images (comic pages, product shots, character sheets)
- You have a list of prompts and want to iterate automatically
- You need to save outputs to specific filenames

## Core pattern

```python
import json, os, time, urllib.request, urllib.parse

COMFYUI_URL = "http://127.0.0.1:8188"

def make_sd15_workflow(prompt, negative, width, height, seed, steps=25):
    """Build an SD 1.5 txt2img workflow dict (API format)."""
    return {
        "3": {"class_type": "KSampler", "inputs": {
            "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
            "latent_image": ["5", 0], "seed": seed, "steps": steps,
            "cfg": 7.5, "sampler_name": "euler_ancestral",
            "scheduler": "karras", "denoise": 1.0
        }},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {
            "ckpt_name": "v1-5-pruned-emaonly.safetensors"
        }},
        "5": {"class_type": "EmptyLatentImage", "inputs": {
            "width": width, "height": height, "batch_size": 1
        }},
        "6": {"class_type": "CLIPTextEncode", "inputs": {
            "text": prompt, "clip": ["4", 1]
        }},
        "7": {"class_type": "CLIPTextEncode", "inputs": {
            "text": negative, "clip": ["4", 1]
        }},
        "8": {"class_type": "VAEDecode", "inputs": {
            "samples": ["3", 0], "vae": ["4", 2]
        }},
        "9": {"class_type": "SaveImage", "inputs": {
            "images": ["8", 0], "filename_prefix": "batch"
        }}
    }

def queue_and_wait(workflow, timeout_per_image=120):
    """Submit workflow, poll until done, return output image bytes."""
    data = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(
        f"{COMFYUI_URL}/api/prompt", data=data,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=60)
    prompt_id = json.loads(resp.read())["prompt_id"]
    
    for _ in range(timeout_per_image):
        time.sleep(1)
        history = json.loads(
            urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10).read()
        )
        if prompt_id not in history:
            continue
        outputs = history[prompt_id].get("outputs", {})
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                img = node_output["images"][0]
                params = urllib.parse.urlencode({
                    "filename": img["filename"],
                    "subfolder": img.get("subfolder", ""),
                    "type": "output"
                })
                return urllib.request.urlopen(
                    f"{COMFYUI_URL}/view?{params}", timeout=30
                ).read()
        status = history[prompt_id].get("status", {})
        if status.get("status_str") == "error":
            raise RuntimeError(f"ComfyUI error: {history[prompt_id]['status']}")
    raise TimeoutError("Image generation timed out")

def batch_generate(pages, output_dir, restart_every=4):
    """
    Generate a batch of images.
    
    pages: list of dicts with keys: file, prompt, negative, width, height
    output_dir: where to save PNGs
    restart_every: restart ComfyUI server every N images (prevents OOM on low VRAM)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for i, page in enumerate(pages):
        # Restart server to prevent VRAM fragmentation on low-VRAM cards
        if restart_every and i > 0 and i % restart_every == 0:
            import subprocess
            subprocess.run(["uvx", "--from", "comfy-cli", "comfy", "restart"],
                         capture_output=True, timeout=30)
            time.sleep(5)  # Wait for server ready
        
        seed = 42 + i * 1000
        workflow = make_sd15_workflow(
            page["prompt"], page["negative"],
            page["width"], page["height"], seed
        )
        
        print(f"[{i+1}/{len(pages)}] {page['file']}...")
        try:
            img_bytes = queue_and_wait(workflow)
            output_path = os.path.join(output_dir, page["file"])
            with open(output_path, "wb") as f:
                f.write(img_bytes)
            print(f"  ✓ {len(img_bytes)//1024}KB")
        except Exception as e:
            print(f"  ✗ {e}")
```

## VRAM considerations

| GPU VRAM | SD 1.5 (512×768) | SDXL (1024×1024) | restart_every |
|----------|------------------|------------------|---------------|
| 6 GB     | ✓ OK            | ✗ OOM likely     | 4-5           |
| 8 GB     | ✓ OK            | ✓ tight          | 8             |
| 12 GB+   | ✓ OK            | ✓ OK             | 0 (no restart)|

## Prompt tips for manga/comic style

- Always include `manga style` or `manga art style` at the start
- Add `best quality, masterpiece` for quality boost
- Negative prompt should include: `low quality, blurry, deformed, ugly, bad anatomy, text, watermark`
- For character consistency, include the same character description in every prompt
- SD 1.5 works best with shorter, focused prompts (~50-100 words)
- Use `euler_ancestral` sampler with `karras` scheduler for manga style
