#!/usr/bin/env python3
"""Batch-generate comic pages via ComfyUI REST API.
Usage: python3 generate_comic.py
Requires: ComfyUI server running at http://127.0.0.1:8188
"""
import json
import os
import sys
import time
import urllib.request
import urllib.parse

COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL = "dreamshaper_8.safetensors"  # Best for manga on 6GB VRAM

def make_workflow(prompt, negative_prompt, width, height, seed, steps=25):
    return {
        "3": {"class_type": "KSampler", "inputs": {
            "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
            "latent_image": ["5", 0], "seed": seed, "steps": steps,
            "cfg": 7.5, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0
        }},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": MODEL}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative_prompt, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "comic_page"}}
    }

# PAGES: override in your project or edit below
PAGES = [
    {"file": "00-cover.png", "prompt": "manga art style, dramatic cinematic, masterpiece, best quality",
     "neg": "low quality, blurry, deformed, ugly, bad anatomy, text, watermark", "w": 512, "h": 768},
]

def queue_prompt(workflow):
    data = json.dumps({"prompt": workflow}).encode('utf-8')
    req = urllib.request.Request(f"{COMFYUI_URL}/api/prompt", data=data, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req, timeout=60)
    return json.loads(resp.read())

def get_history(prompt_id):
    resp = urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10)
    return json.loads(resp.read())

def download_image(filename, subfolder, output_path):
    params = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": "output"})
    resp = urllib.request.urlopen(f"{COMFYUI_URL}/view?{params}", timeout=30)
    with open(output_path, 'wb') as f:
        f.write(resp.read())

def generate_page(page, index):
    seed = 42 + index * 1000
    workflow = make_workflow(page["prompt"], page["neg"], page["w"], page["h"], seed)
    print(f"[{index+1}/{len(PAGES)}] Generating {page['file']}...")
    result = queue_prompt(workflow)
    prompt_id = result["prompt_id"]
    for _ in range(120):
        time.sleep(2)
        history = get_history(prompt_id)
        if prompt_id in history:
            outputs = history[prompt_id].get("outputs", {})
            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    img = node_output["images"][0]
                    output_path = os.path.join(OUTPUT_DIR, page["file"])
                    download_image(img["filename"], img.get("subfolder", ""), output_path)
                    print(f"  ✓ Saved: {output_path}")
                    return True
            status = history[prompt_id].get("status", {})
            if status.get("status_str") == "error":
                print(f"  ✗ Error generating {page['file']}")
                return False
    print(f"  ✗ Timeout generating {page['file']}")
    return False

if __name__ == "__main__":
    try:
        resp = urllib.request.urlopen(f"{COMFYUI_URL}/system_stats", timeout=5)
        stats = json.loads(resp.read())
        vram = stats["devices"][0]["vram_free"] / 1024**3
        print(f"ComfyUI ready. Free VRAM: {vram:.1f} GB")
    except Exception as e:
        print(f"Error: ComfyUI not reachable: {e}")
        sys.exit(1)
    success = 0
    for i, page in enumerate(PAGES):
        if generate_page(page, i):
            success += 1
    print(f"\nDone! {success}/{len(PAGES)} pages generated.")
