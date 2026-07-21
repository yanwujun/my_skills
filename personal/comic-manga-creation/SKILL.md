---
name: comic-manga-creation
description: "Adapt narrative fiction (novels, short stories) into structured comic/manga projects with AI-ready panel prompts, color systems, composition guidance, and generation workflows. Covers project scaffolding, character design sheets, visual symbolism, and multi-tool AI image generation pipelines."
version: 1.0.0
author: hermes
license: MIT
metadata:
  hermes:
    tags: [comic, manga, visual-storytelling, ai-art, adaptation, prompt-engineering, midjourney, stable-diffusion]
    related_skills: [comfyui, pixel-art, claude-design, novel-writer]
---

# Comic & Manga Creation — Visual Narrative Adaptation

Adapt narrative fiction into structured comic/manga projects with AI-ready production pipelines.

## When to Use

- User asks to turn a novel/story into a comic or manga
- User wants AI-generated comic panels with consistent style
- User needs a structured visual narrative project
- User wants to create manga-style pages with AI tools

## Novel-to-Comic Adaptation Pipeline (validated workflow)

When adapting an existing novel:

1. **Read the source** — get the full novel text or chapter content
2. **Create adaptation-report.md** — map chapters→pages, decide what to cut/expand
3. **Design characters** — create `characters/characters.md` with visual descriptions + English AI prompts for each character in each age/appearance variant
4. **Generate character refs FIRST** — txt2img with Dreamshaper 8 at 512×768, white background, full body or upper body
5. **Write page prompts** — one `prompts/XX-page-name.md` per page with: 格数, 画面描述, English generation prompt, negative prompt, seed
6. **Batch generate pages** — script pattern: loop pages → submit to ComfyUI → poll → download → restart every 4 pages
7. **Overlay dialogue** — adapt `add_dialogue.py` for your project's panel layouts and dialogue text

## Project Structure Template

```
comic/{project-name}/
├── README.md                    # Project overview, story summary, usage guide
├── storyboard.md                # Panel-by-panel breakdown (page → panel mapping)
├── adaptation-report.md         # Source material analysis, chapter→page mapping, what to cut/keep
├── color-system.md              # Unified color palette, scene-specific schemes, emotional color mapping
├── composition-lighting.md      # Camera angles, framing principles, lighting systems
├── progress.md                  # Task tracking, milestones, status
├── generation-guide.md          # AI tool selection, generation workflows, tips, troubleshooting
├── characters/
│   └── characters.md            # Detailed character sheets (appearance, outfits, color palettes, expressions, AI keywords)
└── prompts/
    ├── 00-cover-{name}.md       # Cover page prompt
    ├── 01-page-{name}.md        # Page 1 prompt
    ├── ...
    └── XX-page-{name}.md        # Final page prompt
```

## Resuming an Existing Project

When the user says "继续" / "continue" / "接着做" and a comic project already exists:

1. **Check `./comic/` directory** for existing project folders
2. **Read `progress.md`** to understand current phase
3. **Check for existing output files** (PNG/JPG) — `ls -la *.png` with file sizes. Real images are >100KB; placeholder/stub files are <10KB
4. **Verify image quality** with `file` command (must show real dimensions, not "empty" or "data")
5. **Report current state** before proposing next steps — never assume work needs to be redone

**Pitfall — Don't go off on tangents**: If the user has an active comic project and says "继续", they mean THAT project. Don't interpret it as a request to work on something else (like summarizing downloaded skills or starting a new task). Check recent sessions for context if ambiguous.

**Pitfall — "继续" disambiguation**: When the user says "继续" (continue), search session history for comic/manga project context FIRST (query: "小说 漫画 comic manga"). Do NOT assume it refers to the most recent session topic — the user may have multiple active workstreams. The comic project takes priority if one exists.

**Pitfall — Progress file may be stale**: `progress.md` may not reflect actual generated files. Always cross-check with filesystem (`ls -la`, `file` command) before reporting status. If PNGs exist but progress.md says "待执行", update progress.md to match reality.

## Workflow (8 Phases)

### Phase 1: Source Analysis
1. Read the source fiction (novel, short story, etc.)
2. Identify key scenes, emotional beats, visual moments
3. Determine page count (typically 8-15 pages for a short work)
4. Create chapter→page mapping in adaptation-report.md
5. Decide what to cut (internal monologue, exposition) vs expand (visual moments, confrontations)

### Phase 2: Character Design
For each character, create a sheet with:
- **Basic info**: age, role, personality
- **Appearance**: face shape, hair, eyes, build, skin, signature features
- **Outfit variants**: different outfits for different scenes (e.g., lab coat → court suit → 30-years-later casual)
- **Color palette**: specific hex values for each element (main color, accent, highlight)
- **Expression table**: expressions for key emotional states (常态, 震惊, 愤怒, 微笑, etc.)
- **Identification points**: 3-4 visual markers that make the character instantly recognizable
- **AI keywords**: English prompt snippet for consistent character generation

### Phase 3: Visual Symbolism
Design recurring visual motifs:
- Objects that evolve through the story (e.g., small disk → giant mirror disk)
- Numbers/text that appear repeatedly (e.g., "3.1415926535...")
- Architectural elements (e.g., dome as symbol of institution/prison)
- Handwritten documents (e.g., final manuscript page)

### Phase 4: Color System
Create color-system.md with:
- **Color philosophy**: what cold vs warm tones represent emotionally
- **Core palette**: 4-6 primary colors with hex values and usage
- **Character-specific palettes**: each character's color identity
- **Scene-specific schemes**: 8-10 scene palettes with element-by-element color breakdowns
- **Color arc**: how the overall tone shifts across the story (e.g., cold blue → warm gold)
- **Special effects**: glow, reflection, texture colors
- **AI color prompts**: template prompts for cold/warm/contrast scenes

### Phase 5: Composition & Lighting
Create composition-lighting.md with:
- **Camera angles**: when to use eye-level, low-angle, high-angle, bird's-eye, dutch angle
- **Framing principles**: centered, rule-of-thirds, diagonal, framing-within-frame, negative space
- **Panel layout systems**: standard grid (3-4 panels), mixed large/small, cinematic (2-3 wide), dense narrative (5+)
- **Lighting systems**: single source, multi-source, backlit, top-lit, ambient
- **Shot distances**: long shot, full shot, medium shot, close-up, extreme close-up
- **AI composition prompts**: template prompts for each technique

### Phase 6: Panel Prompt Engineering
Each page prompt file should contain:

```markdown
# Page XX: [Title] — [中文标题]

## 页面信息
- 文件名, 类型, 画幅比, 改编自, 分格数, 情绪关键词

## 出场角色
| 角色 | 格 | 画面占比 | 姿态 | 说明 |

## 分格设计
### 格N（位置）
- 镜头: [shot type]
- 画面: [visual description]
- 光源: [light source]
- 文字: [bubbles, narration boxes]
- 小说原文: "[original text]"

## 构图指导
[Per-panel composition notes]

## 光影指导
[Per-panel lighting notes]

## 色彩规范
| 区域 | 色值 | 说明 |

## 生成提示词
### 英文主提示词
[Detailed English prompt with style, composition, characters, colors, lighting]

### 负面提示词
[What to avoid]

### 技术参数
- Midjourney: --ar 3:4 --style raw --stylize 200 --quality 2
- Stable Diffusion: 768x1024, CFG 7.5, steps 30, sampler: dpmpp_2m + karras

## 叙事功能
[What this page achieves narratively]
```

### Phase 6.5: Storyboard Review (MANDATORY — DO NOT SKIP)

**USER CORRECTION**: The user MUST see the full storyboard with panel-by-panel prompts BEFORE any image generation. Jumping straight to generating images is a rejection-worthy error. The required sequence is:

```
1. Create storyboard with ALL pages (panel counts, shot types, dialogue, English prompts)
2. Present to user for review
3. Only after user approval → generate characters → generate pages
```

**Minimum storyboard content per page**: panel count, per-panel visual description, camera/shot type, lighting direction, dialogue text, English generation prompt, negative prompt, seed. Format as a single consolidated markdown file (e.g. `storyboard-full.md`) rather than one file per page — single file is easier for the user to review. See `references/storyboard-template.md` for the exact table format.

**Pitfall — "10 pages is not enough"**: When adapting a novel, the full storyboard should cover the complete work (all acts/chapters), not just the first chapter. The user may reject a partial storyboard. Plan 60-80 pages total for a novella-length adaptation, divided into acts of 10-14 pages each. If the user says "不能只要十页" / "不全", you did not plan enough pages.

### Phase 7: Character Reference Generation (MUST come before page generation)

**USER CORRECTION — DO THIS FIRST**: Generate standalone character reference images BEFORE generating any comic pages. The user explicitly requires this order: characters → select best variants → refine faces → img2img pages.

**MANGA-ORIENTED PROMPTS**: Use `bold clean ink lines, screentone shading, chinese manhua manga art style` rather than `watercolor art style` when the user wants a manga/comic look. The watercolor style is illustration-oriented; manga style uses stronger lines and flatter shading for a comic panel aesthetic.

**The 4-step character pipeline:**

```
txt2img character variants → user picks best → img2img face refinement (denoise=0.4) → img2img comic pages (denoise=0.5-0.7)
```

**Step 7a: Generate character variations**
For each main character, generate 3 variations (different seeds, same prompt):
- Use the character's AI keywords from Phase 2
- 512x768 portrait orientation
- White/simple background
- Full body or 3/4 pose
- Save as `characters/{name}_v1.png`, `_v2.png`, `_v3.png`

**Step 7b: User selects best variants**
Show the user all variations (open folder), ask them to pick the best version of each character.

**Step 7b2: Refine character faces (optional but recommended)**
If initial character images need face improvement, use img2img with low denoise:
- Upload character image to ComfyUI input folder
- Use img2img with denoise=0.35-0.45 (preserves identity, improves face detail)
- Same prompt as txt2img but with "highly detailed face, sharp clean lines" emphasis
- Save as `characters/{name}_final.png`

**Step 7c: Generate comic pages using selected references**
Use img2img with selected character references for consistency:
- Upload character reference image to ComfyUI via `/upload/image` endpoint
- Use img2img workflow (LoadImage → VAEEncode → KSampler → VAEDecode → SaveImage)
- Set denoise strength: 0.5-0.7 (preserves character features, changes scene/background)
- Each page should reference the character who is the main focus of that scene
- The `make_img2img_workflow()` function in `references/comfyui-img2img-workflows.py` shows the node graph

### Phase 8: Image Generation & Post-Processing

**Prerequisite check (MUST do before generating):**

Before attempting any image generation, verify an image API is available:
1. Check `apikey-image-gen` skill: does `~/.hermes/config.yaml` have a `fun-codex` custom_provider?
2. Check ComfyUI: is `comfy` CLI installed? Is server running (`curl http://127.0.0.1:8188/system_stats`)?
3. Check GPU: `nvidia-smi` — if GPU available (≥6GB VRAM), ComfyUI local is viable
4. If NONE available, STOP and ask the user to provide an image generation API key before proceeding

Do NOT create all 11 prompt files (Phase 6) before confirming image generation is possible. Generate 1 test image first, verify quality, then batch the rest.

**Generation options (ordered by quality on 6GB VRAM):**
- **Z-Image-Turbo NVFP4** (BEST for 6GB, USE THIS FIRST for Chinese content): Alibaba 6B DiT model, NVFP4 4-bit quantized — fits 6GB VRAM. ~55s/image at 512×768. **Native Chinese prompt support — write prompts in Chinese directly, no English translation needed.** Excellent Asian faces, 国风/水墨画, ethnic minority clothing detail (苗族/藏族/etc.). For ANY Chinese comic/manga project, start here. Parameters: steps=9, cfg=1.0, sampler=euler, scheduler=simple, shift=3. Download via ModelScope (faster in China): `curl -L -o ~/comfy/ComfyUI/models/diffusion_models/z_image_turbo_nvfp4.safetensors "https://www.modelscope.cn/api/v1/models/Comfy-Org/z_image_turbo/repo?Revision=master&FilePath=split_files/diffusion_models/z_image_turbo_nvfp4.safetensors"`. Full setup in comfyui skill `references/wsl-low-vram-setup.md`.
- **Dreamshaper 8** (FALLBACK, for non-Chinese / Japanese-style content): SD 1.5-tuned for anime/manga, 2GB, ~18s/image at 512×768. English prompts only. Steps=30, cfg=7.5, sampler=dpmpp_2m, scheduler=karras. ⚠️ Produces poor results for Chinese ethnic/minority content — faces look Japanese, clothing details are generic. If the user says "效果不好" on Chinese content, switch to Z-Image-Turbo.

**Model selection rule**: If the project involves Chinese settings (苗寨/民国/古风), Chinese characters, or the user writes prompts in Chinese → use Z-Image-Turbo. If the project is Japanese manga style or generic anime → Dreamshaper 8 is faster and adequate.

**⚠️ PITFALL — Resolution determines clarity**: At 512×768, text and faces can appear blurry/muddy. When the user complains about clarity, bump to 768×1024 FIRST before trying other fixes. The resolution is almost always the bottleneck, not the prompt or model. Timing jumps from ~55s to ~95s at the higher resolution.

**Batch generation with Dreamshaper 8 (proven pattern)**: On 6GB VRAM with Dreamshaper 8, generate pages sequentially in a single Python script. Pattern: loop items, POST workflow to `/api/prompt`, poll `/history/{pid}`, download output. Key detail: restart ComfyUI every 4 items to prevent VRAM fragmentation OOM (`uvx --from comfy-cli comfy stop; sleep 3; launch --background; sleep 8; verify /system_stats`). Generates ~18 items in ~5 minutes at 512×768. See `scripts/batch_generate_dreamshaper.py` for the reusable script. Script pattern: load base API workflow JSON, loop pages modifying `prompt['6']['inputs']['text']`, `prompt['3']['inputs']['seed']`, POST to `/api/prompt`, wait 65-100s (resolution-dependent), poll queue until empty, copy latest output. Each page is a single full-page composition — multi-panel layouts are described in the prompt, not assembled from separate generations. This approach takes ~60-70s/page at 512×768, ~95-105s/page at 768×1024. Must restart ComfyUI every 4-5 pages to avoid VRAM fragmentation OOM. See `references/z-image-turbo-batch-pattern.md`.

### Phase 9: Dialogue & Text Overlay

**USER REQUIREMENT**: Comic pages MUST have dialogue bubbles and narration. Never deliver raw AI images without text.

Use PIL/Pillow to add text after generation:

```python
from PIL import Image, ImageDraw, ImageFont

def get_cjk_font(size=20):
    """Get a CJK-capable font. Check these paths in order:"""
    candidates = [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",      # WenQuanYi (Linux)
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/msyh.ttc",                           # Microsoft YaHei (Windows)
        "/System/Library/Fonts/PingFang.ttc",                   # macOS
    ]
    for fp in candidates:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()

# Speech bubble: white rounded rect + text + tail triangle
# Narration box: dark rounded rect + white text
# Title: large text with stroke outline, centered
# Anger bubble: red background, white text
```

Text overlay types:
- `title` — centered, large font, stroke outline
- `subtitle` — centered, smaller, semi-transparent
- `narrate` — dark box, white text, top-left positioned
- `bubble` — white rounded rect with tail, black text
- `bubble_anger` — red rounded rect, white text
- `narrate_end` — centered, bottom of page, for epilogue text

### Phase 10: Final Assembly
- Select best candidates from multiple generations
- Color correction for consistency across pages
- Fix AI artifacts (hands, text, proportions)
- Add special effects (glow, speed lines)
- Assemble panels into full pages with gutters

## Key Pitfalls

### Character Consistency
AI generates different-looking characters across panels. Mitigations:
- Always lead prompts with the same character description
- Use seed values (SD) or reference images (MJ)
- Consider training a LoRA for the main character (SD)
- Post-process to correct inconsistencies

### Chinese Text Generation
AI cannot reliably generate Chinese characters. Solution:
- NEVER rely on AI for text in panels
- Always add text (bubbles, narration) in post-processing
- Use comic fonts (not system fonts) for authenticity

### Hand Rendering
AI generates unnatural hands. Mitigations:
- Use ControlNet Hand model (Stable Diffusion)
- Avoid extreme hand close-ups in panel design
- Post-process hand corrections

### HuggingFace Model Downloads
Some HuggingFace URLs return redirect pages (15 bytes "Entry not found") instead of actual model files. Always:
- Add `-H "User-Agent: Mozilla/5.0"` header to curl
- Verify downloaded file size (>100MB for SD models) with `ls -lh`
- Verify it's binary data (not ASCII text) with `file` command
- If file is <1MB, the download failed — try a different URL or use `huggingface-cli download`

### ComfyUI WSL Setup Notes
On WSL with NVIDIA GPU:
- Install comfy-cli via `uvx --from comfy-cli comfy` (avoids pipx/pip issues)
- Install deps in the ComfyUI venv: `~/comfy/ComfyUI/.venv/bin/pip install -r requirements.txt`
- If missing specific packages (sqlalchemy, alembic, pyyaml, tqdm, etc.), install individually
- ComfyUI server: `uvx --from comfy-cli comfy launch --background` on port 8188
- Restart between model changes: `uvx --from comfy-cli comfy stop` then `launch`
- 6GB VRAM works with SD 1.5 / Dreamshaper 8 at 512x768 or 768x512

### add_dialogue.py Adaptation
The bundled `add_dialogue.py` script is a template designed for `圆的囚徒` project. For new projects you MUST:
- Change panel layout coordinates (the script uses 768×1024; adapt for your canvas size)
- Rewrite the `PAGES` dict with your actual dialogue data
- Update `SPEAKER_COLORS` for your characters
- Adjust font sizes for your resolution (512×768 → use font size 22 for dialogue, 16 for labels)
- Change `PROJ` variable to point to your project pages directory

### Panel Assembly
Combining separately-generated panels into a cohesive page is manual work:
- Use Photoshop/GIMP/Clip Studio Paint
- Maintain consistent gutter width (2-3px white)
- Ensure visual flow guides the eye correctly
- Check that adjacent panels have consistent lighting direction

### ComfyUI VRAM Management (6GB cards)
On RTX 3050 6GB, ComfyUI accumulates VRAM fragmentation across generations. Restart every 4-5 pages:
```bash
uvx --from comfy-cli comfy stop; sleep 3
uvx --from comfy-cli comfy launch --background; sleep 8
# Verify: curl -s http://127.0.0.1:8188/system_stats
```
Do NOT skip the restart — skipped restarts cause mid-batch OOM crashes.
- Use Photoshop/GIMP/Clip Studio Paint
- Maintain consistent gutter width (2-3px white)
- Ensure visual flow guides the eye correctly
- Check that adjacent panels have consistent lighting direction

### Do NOT copy outputs to Desktop or work folders
**User preference**: Save generated images to the project directory ONLY
(`~/comic/{project}/`). Do NOT copy to `/mnt/c/Users/*/Desktop/` or any
Windows desktop path. Do NOT copy to `D:\平时处理文件\` — that is for work
content only. Creative/personal projects go under `D:\项目\个人总结\experience\`
or equivalent. The user accesses files directly via WSL path.

### Auto-Dialogue Script
Use `scripts/add_dialogue.py` for automated bubble/narration overlay:
- Panel-layout-driven: defines panel layouts once, text auto-positions
- Edit `PAGES` dict to add dialogue data per page
- Supports 5 bubble types: narration (dark box), speech (white oval + tail),
  shout (red jagged), plus speaker labels with color coding
- Finds CJK font automatically (WenQuanYi, Microsoft YaHei, PingFang)
- Run: `python3 add_dialogue.py [page_ids...]`

### Generation Script Pattern
Use this pattern for ComfyUI batch generation (Python + urllib, no external deps):
```python
import json, os, time, urllib.request, urllib.parse

COMFYUI_URL = "http://127.0.0.1:8188"

def make_workflow(prompt, neg, width, height, seed, steps=30, model="dreamshaper_8.safetensors"):
    return {
        "3": {"class_type": "KSampler", "inputs": {
            "model": ["4",0], "positive": ["6",0], "negative": ["7",0], "latent_image": ["5",0],
            "seed": seed, "steps": steps, "cfg": 7.5, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0
        }},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": model}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4",1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["4",1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3",0], "vae": ["4",2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8",0], "filename_prefix": "comic"}}
    }

def queue_and_wait(workflow, output_path):
    data = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(f"{COMFYUI_URL}/api/prompt", data=data, headers={"Content-Type": "application/json"})
    pid = json.loads(urllib.request.urlopen(req, timeout=60).read())["prompt_id"]
    for _ in range(180):
        time.sleep(2)
        h = json.loads(urllib.request.urlopen(f"{COMFYUI_URL}/history/{pid}", timeout=10).read())
        if pid in h:
            for nid, no in h[pid].get("outputs", {}).items():
                if "images" in no:
                    img = no["images"][0]
                    params = urllib.parse.urlencode({"filename": img["filename"], "subfolder": img.get("subfolder",""), "type": "output"})
                    with open(output_path, 'wb') as f:
                        f.write(urllib.request.urlopen(f"{COMFYUI_URL}/view?{params}", timeout=30).read())
                    return True
            return h[pid].get("status",{}).get("status_str") != "error"
    return False
```

### Delegation Timeout
For large documentation tasks (creating 5+ files), delegation to sub-agents may timeout (600s). Direct execution with `execute_code` or sequential `write_file` calls is more reliable.

## Tool-Specific Notes

### Midjourney
- Discord-based workflow
- Best for: concept art, style exploration, high-quality finals
- Limitations: no local control, paid subscription, limited Chinese text support

### Stable Diffusion / Z-Image-Turbo (via ComfyUI)
- Local installation required (see comfyui skill)
- Best for: batch generation, LoRA training, ControlNet-guided composition
- **For manga/anime on 6GB VRAM**: Use **Z-Image-Turbo NVFP4** (best quality, Chinese prompts) or **Dreamshaper 8** (`dreamshaper_8.safetensors`)
- **Z-Image-Turbo NVFP4**: steps=9, cfg=1.0, sampler=euler, 512×768, ~55s/image. Full setup in comfyui skill
- **Dreamshaper 8**: steps=30, cfg=7.5, sampler=dpmpp_2m, 512×768. Download: `curl -L -o dreamshaper_8.safetensors -H "User-Agent: Mozilla/5.0" "https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors"`
- **SDXL needs ≥8GB VRAM** — will not run on RTX 3050 6GB
- **Vanilla SD 1.5 produces poor manga results** — use an anime-tuned model

### DALL-E 3
- Available via ChatGPT Plus
- Best for: complex scenes, natural language prompts
- Limitations: slower, less style control, no local execution

## References

- `references/image-generation-approaches.md` — practical comparison of apikey-image-gen, ComfyUI+SD, Midjourney, DALL-E with setup commands and batch generation script patterns
- `scripts/comfyui_batch_generate.py` — reusable batch generation script for ComfyUI REST API (edit PAGES list for your project)

The example project at `./comic/circle-truth/` demonstrates all phases:
- `storyboard.md` — 10-page panel breakdown from a 5-chapter novel
- `characters/characters.md` — 4 main + 3 minor character sheets with full detail
- `color-system.md` — 8-scene color scheme with hex values
- `composition-lighting.md` — Complete camera/lighting/framing reference
- `prompts/*.md` — 11 AI-ready page prompts with English generation text
- `generation-guide.md` — Multi-tool generation workflow
