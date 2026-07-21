#!/usr/bin/env python3
"""
ComfyUI img2img workflows for character refinement and comic page generation.

Two use cases:
1. Character refinement: improve face details while keeping identity (denoise=0.35-0.45)
2. Comic page generation: use character reference to generate scene (denoise=0.5-0.7)

Requires: ComfyUI server running at http://127.0.0.1:8188
"""
import json
import os
import time
import urllib.request
import urllib.parse

COMFYUI_URL = "http://127.0.0.1:8188"
NEG = "low quality, blurry, deformed, ugly, bad anatomy, extra fingers, mutated hands, poorly drawn face, disfigured, bad proportions, text, watermark, jpeg artifacts, multiple people"

# ── Upload image to ComfyUI input folder ──────────────────────────────
def upload_image(filepath):
    """Upload a local image to ComfyUI's input folder. Returns the server-side filename."""
    import mimetypes
    filename = os.path.basename(filepath)
    mime = mimetypes.guess_type(filepath)[0] or "image/png"
    boundary = "----FormBoundary7MA4"
    with open(filepath, 'rb') as f:
        file_data = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{COMFYUI_URL}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

# ── img2img workflow builder ──────────────────────────────────────────
def make_img2img_workflow(prompt, ref_image_name, width, height, seed, denoise=0.5, steps=30, model="dreamshaper_8.safetensors"):
    """
    Build an img2img workflow JSON.
    
    Nodes:
      11 (LoadImage) → 10 (VAEEncode) → 3 (KSampler) → 8 (VAEDecode) → 9 (SaveImage)
                                          ↑
                              4 (Checkpoint) → 6 (CLIP+) / 7 (CLIP-)
    
    Args:
        prompt: positive prompt text
        ref_image_name: filename in ComfyUI input folder (from upload_image)
        width/height: output dimensions
        seed: random seed
        denoise: 0.0=preserve original, 1.0=full generation. 
                 0.35-0.45 = face refinement (keeps identity)
                 0.5-0.7 = scene generation from character ref
        steps: sampling steps (30 recommended for quality)
        model: checkpoint filename
    """
    return {
        "3": {"class_type": "KSampler", "inputs": {
            "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["10", 0],
            "seed": seed, "steps": steps, "cfg": 7.5, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": denoise
        }},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": model}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "img2img"}},
        "10": {"class_type": "VAEEncode", "inputs": {"pixels": ["11", 0], "vae": ["4", 2]}},
        "11": {"class_type": "LoadImage", "inputs": {"image": ref_image_name}}
    }

# ── txt2img workflow builder (for comparison) ─────────────────────────
def make_txt2img_workflow(prompt, width, height, seed, steps=30, model="dreamshaper_8.safetensors"):
    """Standard txt2img workflow."""
    return {
        "3": {"class_type": "KSampler", "inputs": {
            "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0],
            "seed": seed, "steps": steps, "cfg": 7.5, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0
        }},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": model}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "txt2img"}}
    }

# ── Submit and wait for result ────────────────────────────────────────
def queue_and_wait(workflow, output_path):
    """Submit workflow to ComfyUI, wait for completion, download result."""
    data = json.dumps({"prompt": workflow}).encode('utf-8')
    req = urllib.request.Request(f"{COMFYUI_URL}/api/prompt", data=data, headers={'Content-Type': 'application/json'})
    result = json.loads(urllib.request.urlopen(req, timeout=120).read())
    prompt_id = result["prompt_id"]
    
    for _ in range(180):  # max 6 minutes
        time.sleep(2)
        history = json.loads(urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10).read())
        if prompt_id in history:
            outputs = history[prompt_id].get("outputs", {})
            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    img = node_output["images"][0]
                    params = urllib.parse.urlencode({
                        "filename": img["filename"],
                        "subfolder": img.get("subfolder", ""),
                        "type": "output"
                    })
                    imgdata = urllib.request.urlopen(f"{COMFYUI_URL}/view?{params}", timeout=30).read()
                    with open(output_path, 'wb') as f:
                        f.write(imgdata)
                    return True
            if history[prompt_id].get("status", {}).get("status_str") == "error":
                return False
    return False

# ── Example: character refinement ─────────────────────────────────────
def refine_character(input_path, output_path, prompt, seed=42):
    """Refine a character image (improve face details while keeping identity)."""
    print(f"Uploading {os.path.basename(input_path)}...", end=" ")
    upload_result = upload_image(input_path)
    print(f"→ {upload_result['name']}")
    
    print(f"Refining (denoise=0.4)...", end=" ")
    wf = make_img2img_workflow(prompt, upload_result["name"], 512, 768, seed, denoise=0.4, steps=35)
    success = queue_and_wait(wf, output_path)
    print("✓" if success else "✗")
    return success

# ── Example: comic page from character ref ─────────────────────────────
def generate_comic_page(ref_image_path, output_path, scene_prompt, seed, denoise=0.55, w=768, h=512):
    """Generate a comic page scene using a character reference image."""
    print(f"Uploading ref {os.path.basename(ref_image_path)}...", end=" ")
    upload_result = upload_image(ref_image_path)
    print(f"→ {upload_result['name']}")
    
    print(f"Generating scene (denoise={denoise})...", end=" ")
    wf = make_img2img_workflow(scene_prompt, upload_result["name"], w, h, seed, denoise=denoise)
    success = queue_and_wait(wf, output_path)
    print("✓" if success else "✗")
    return success

if __name__ == "__main__":
    # Example usage
    CHAR_DIR = "/path/to/characters"
    OUTPUT_DIR = "/path/to/output"
    
    # 1. Refine a character
    # refine_character(
    #     os.path.join(CHAR_DIR, "hero_v1.png"),
    #     os.path.join(CHAR_DIR, "hero_final.png"),
    #     "manga style, highly detailed face, 1boy, black hair, blue eyes, portrait"
    # )
    
    # 2. Generate comic page from character ref
    # generate_comic_page(
    #     os.path.join(CHAR_DIR, "hero_final.png"),
    #     os.path.join(OUTPUT_DIR, "01-page.png"),
    #     "manga style, hero standing in rain, dramatic lighting, city background",
    #     seed=42
    # )
    pass
