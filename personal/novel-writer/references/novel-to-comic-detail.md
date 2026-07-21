# 小说转漫画 (Novel to Comic) — 工作原理

> Detailed adaptation workflow for novel-to-comic conversion.
> Referenced from the **Chapter 7: 小说转漫画改编** section in the main SKILL.md.

## Output Structure

```
comic/{slug}/
├── source-{slug}.md              # Original novel (backup)
├── storyboard.md                 # Comic storyboard
├── characters/                   # Character visual design
│   ├── characters.md             # Comic character designs
│   └── characters.png            # Character reference image (optional)
├── prompts/                      # Page generation prompts
│   ├── 00-cover-{slug}.md
│   └── 01-page-{slug}.md
├── 00-cover-{slug}.png           # Cover image
├── 01-page-{slug}.png            # Page images
└── adaptation-report.md          # Adaptation report
```

## Adaptation Flow

```
[Read novel] → [Analyze adaptability] → [Confirm style] → [Character comic design] → [Storyboarding] → [Generate prompts] → [Generate images]
```

### Step 1: Read novel content
Check `novel/{slug}/` for existing novel-writer output, or read user-provided file.
Save source to `source-{slug}.md`.

### Step 2: Adaptability analysis
Write to `adaptation-report.md`:
- Novel type, estimated comic page count, adaptation difficulty
- Chapter→page mapping table
- Content to cut/merge/add
- Main characters summary

### Step 3: Style confirmation
From `baoyu-comic` style options:
- Ink-brush + action (wuxia/xianxia)
- Manga + dramatic (sci-fi)
- Ligne-claire + warm (urban/romance)
- Realistic + dramatic (mystery)

### Step 4: Character comic design
Write to `characters/characters.md`:
- Comic appearance (face/hair/eyes/build/signature features)
- Costume design (daily/battle/color palette)
- Expression set (normal/angry/surprised/smug)
- Recognition points (3-5 distinguishing features)

### Step 5: Storyboard
Format:
```markdown
## Page N / Total M
**File**: NN-page-{slug}.png
**Adapted from**: Chapter X "Title"
### Panel layout
[panel count + layout type]
#### Panel 1 (position: [top/mid/bottom/full])
**Novel text**: "[corresponding paragraph]"
**Visual**: shot type, characters, scene, dialogue/voiceover
```

### Step 6: Generate prompts
Each page gets a prompt file with:
- Characters in this page (visual features for consistency)
- Scene summary
- Generation prompt (art style + tone + characters + panel composition + scene details + dialogue text)

### Step 7: Generate images
Priority: image_generate tool → apikey-image-gen via Web UI → local diffusers

## Key Principles

- **Character consistency is the biggest risk**: Every page prompt MUST include full visual description of appearing characters
- **Narrative to visual**: "He clenched his fist in anger" → separate panels for gripping motion + facial expression close-up
- **Dialogue compression**: Keep only key dialogue, show environment through visuals
- **Panel count**: Standard 3-5 panels/page, action scenes 2-3 large panels, dialogue 4-6 panels
