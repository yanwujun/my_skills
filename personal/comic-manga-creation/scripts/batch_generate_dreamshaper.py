"""Reusable batch generation script for Dreamshaper 8 via ComfyUI.
Copy to project directory and edit ITEMS list with your prompts.
Restarts ComfyUI every 4 items to prevent VRAM OOM on 6GB cards.
"""

import json, time, urllib.request, os

COMFYUI = "http://127.0.0.1:8188"
OUT_DIR = "./output"
os.makedirs(OUT_DIR, exist_ok=True)

# EDIT THIS LIST: (name, prompt, negative_prompt, seed, width, height, output_path)
ITEMS = [
    # ("page01", "masterpiece, best quality, ...", "negative prompt...", 100, 512, 768, f"{OUT_DIR}/page01.png"),
]

def make_workflow(prompt, neg, width, height, seed, steps=30, model="dreamshaper_8.safetensors"):
    return {
        "3": {"class_type": "KSampler", "inputs": {"model": ["4",0], "positive": ["6",0], "negative": ["7",0], "latent_image": ["5",0], "seed": seed, "steps": steps, "cfg": 7.5, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": model}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4",1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["4",1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3",0], "vae": ["4",2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8",0], "filename_prefix": "batch_"}}
    }

def generate(wf, outpath, timeout=120):
    data = json.dumps({"prompt": wf}).encode()
    req = urllib.request.Request(f"{COMFYUI}/api/prompt", data=data, headers={"Content-Type": "application/json"})
    pid = json.loads(urllib.request.urlopen(req, timeout=60).read())["prompt_id"]
    for i in range(timeout // 2):
        time.sleep(2)
        try:
            h = json.loads(urllib.request.urlopen(f"{COMFYUI}/history/{pid}", timeout=10).read())
        except:
            continue
        if pid in h:
            for nid, no in h[pid].get("outputs", {}).items():
                if "images" in no:
                    img = no["images"][0]
                    q = urllib.parse.urlencode({"filename": img["filename"], "subfolder": img.get("subfolder",""), "type": "output"})
                    with open(outpath, 'wb') as f:
                        f.write(urllib.request.urlopen(f"{COMFYUI}/view?{q}", timeout=30).read())
                    return os.path.getsize(outpath)
        if h.get(pid, {}).get("status", {}).get("status_str") == "error":
            return 0
    return 0

def restart_comfyui():
    """Restart ComfyUI to free VRAM fragmentation."""
    os.system("uvx --from comfy-cli comfy stop 2>/dev/null; sleep 3; uvx --from comfy-cli comfy launch --background 2>/dev/null; sleep 8")
    for _ in range(5):
        try:
            urllib.request.urlopen(f"{COMFYUI}/system_stats", timeout=10)
            return True
        except:
            time.sleep(3)
    return False

if __name__ == "__main__":
    if not ITEMS:
        print("ERROR: Edit ITEMS list before running.")
        exit(1)

    total = len(ITEMS)
    ok = 0
    for i, (name, prompt, neg, seed, w, h, outpath) in enumerate(ITEMS):
        print(f"[{i+1}/{total}] {name}  ", end="", flush=True)
        wf = make_workflow(prompt, neg, w, h, seed)
        sz = generate(wf, outpath)
        if sz and sz > 50000:
            print(f"OK {sz//1024}KB")
            ok += 1
        else:
            print(f"FAIL (size={sz})")

        if (i+1) % 4 == 0 and i < total-1:
            print("  Restarting ComfyUI...")
            restart_comfyui()

    print(f"\n{ok}/{total} succeeded")
