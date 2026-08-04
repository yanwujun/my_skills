---
name: baoyu
description: "Visual content creation suite from baoyu-skills: article illustration, knowledge comics, and infographics — all using Type × Style × Palette consistency with image_generate tool."
version: 1.0.0
author: Hermes Agent (consolidated from 宝玉/JimLiu's baoyu-skills)
license: MIT
metadata:
  hermes:
    tags: [baoyu, illustration, comic, infographic, image-generation, creative]
    related_skills: []
---

# Baoyu Visual Content Creation Suite

Consolidated umbrella for three content types from the baoyu-skills collection. All use the same **Type × Style × Palette** design system and the `image_generate` tool.

## Sections

### Section A: Article Illustrator

Analyze articles, identify illustration positions, generate images with consistent Type × Style × Palette.

**Three dimensions:** Type (infographic/scene/flowchart/comparison/framework/timeline), Style (rendering approach), Palette (color scheme).

**Output structure:** `{output-dir}/` with `outline.md`, `prompts/NN-{type}-{slug}.md`, and `NN-{type}-{slug}.png`.

**Workflow:** Detect reference images → Analyze content → Confirm settings (clarify) → Generate outline → Generate prompts (BLOCKING: save before image gen) → Generate images → Finalize with markdown insertion.

**Principles:** Visualize concepts (not metaphors), use article data for labels, prompt files are reproducibility records, strip secrets.

**References:** `references/baoyu-article-illustrator/` — workflow.md, styles.md, style-presets.md, prompt-construction.md, usage.md

### Section B: Knowledge Comics

Educational/biography/tutorial comics (知识漫画) with art style × tone combinations.

**Options:** Art (ligne-claire/manga/realistic/ink-brush/chalk/minimalist), Tone (neutral/warm/dramatic/romantic/energetic/vintage/action), Layout (standard/cinematic/dense/splash/mixed/webtoon/four-panel), Aspect (3:4/4:3/16:9).

**Presets:** ohmsha (manga+neutral), wuxia (ink-brush+action), shoujo (manga+romantic), concept-story (manga+warm), four-panel (minimalist+neutral).

**File structure:** `comic/{topic-slug}/` with storyboard.md, characters/, prompts/, and PNG files.

**Workflow:** Analyze → Confirm → Storyboard + characters → Prompts (BLOCKING) → Character sheet (multi-page) → Generate pages via image_generate → Report.

**Pitfalls:** image_generate may not exist everywhere (fallback available), always use absolute paths for curl -o, use absolute paths for downloads to avoid stale-CWD footgun.

**References:** `references/baoyu-comic/` — analysis-framework.md, character-template.md, storyboard-template.md, ohmsha-guide.md, workflow.md, partial-workflows.md, auto-selection.md, and art-styles/ tones/ presets/ layouts/ subdirectories.

### Section C: Infographics

21 layouts × 21 styles for information visualization (信息图).

**Layouts:** bento-grid (default), linear-progression, binary-comparison, comparison-matrix, hierarchical-layers, tree-branching, hub-spoke, structural-breakdown, iceberg, bridge, funnel, isometric-map, dashboard, periodic-table, comic-strip, story-mountain, jigsaw, venn-diagram, winding-roadmap, circular-flow, dense-modules.

**Styles:** craft-handmade (default), claymation, kawaii, storybook-watercolor, chalkboard, cyberpunk-neon, bold-graphic, aged-academia, corporate-memphis, technical-schematic, origami, pixel-art, ui-wireframe, subway-map, ikea-manual, knolling, lego-brick, pop-laboratory, morandi-journal, retro-pop-grid, hand-drawn-edu.

**Keyword shortcuts:** 高密度信息大图→dense-modules, 信息图→bento-grid+craft-handmade.

**Workflow:** Analyze → Structured content → Recommend combinations → Confirm → Generate prompt → Generate image → Report.

**Principles:** Preserve data faithfully (no summarization), strip secrets, one message per section, consistent style.

**References:** `references/baoyu-infographic/` — analysis-framework.md, structured-content-template.md, base-prompt.md, layouts/ and styles/ subdirectories.

## Common Toolchain

All three use: `image_generate` (returns URL, must download), aspect mapping (16:9→landscape, 9:16→portrait, 1:1→square), `write_file` for output, `clarify` for confirmation.

**Universal pitfalls:** image_generate may not exist in all environments, always use absolute paths for curl downloads, strip secrets from source content, Step 2 confirmation is mandatory.