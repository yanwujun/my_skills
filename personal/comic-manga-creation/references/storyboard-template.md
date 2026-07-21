# Storyboard Template — Per-Page Format

Each page in the storyboard MUST include ALL of the following fields. Present as a single consolidated markdown file (e.g. `storyboard-full.md`), NOT one file per page.

## Page Header Template

```markdown
### P{N} · {Page Title}（{格数}格）

**叙事功能**：{What this page achieves in the story}

**格1（{位置：上左/上宽/整页等}）**：
{Visual description — what the reader sees}
- 镜头：{shot type: 中景/特写/全景/俯视/仰视}
- 光源：{lighting direction and quality}
- 对白："{dialogue}" / 旁白："{narration text}"

**格2（{位置}）**：
...

| 元素 | 值 |
|------|-----|
| 镜头 | ... |
| 光源 | ... |
| 色调 | ... |
| 焦点 | ... |

**英文提示词**：
\`\`\`
masterpiece, best quality, {panel-count}-panel manga page, ...
\`\`\`

**负面提示词**：
\`\`\`
western style, anime large eyes, ...
\`\`\`
```

## Real Example (from Aya project, Page 1)

```markdown
### P1 · 百草枯（1格整页）

**叙事功能**：倒叙钩子。先让读者看到终点——穿新娘服的女孩在喝农药。

**格1（整页）**：幽暗苗族婚房。梳妆台前，阿雅侧坐，穿黑色鱼苗新娘服（蝴蝶纹样）。手持深绿色百草枯瓶凑到唇边。镜中映出她平静得诡异的脸。窗外一线苍白晨光，桌上银蝴蝶坠子项链。

| 元素 | 值 |
|------|-----|
| 镜头 | 中景，略俯视 |
| 光源 | 左侧窗外冷白晨光 + 梳妆台暖黄烛光 |
| 色调 | 深黑主调，一点暖黄一点冷白 |
| 焦点 | 百草枯瓶口与嘴唇之间的空隙 |
```

## Required Per-Page Fields Checklist

- [ ] Page number and title
- [ ] Panel count and layout description
- [ ] Per-panel visual description (what the reader sees)
- [ ] Per-panel shot type (中景/特写/全景/俯视/仰视)
- [ ] Per-panel lighting direction
- [ ] Per-panel dialogue or narration text
- [ ] English generation prompt for the full page
- [ ] Negative prompt
- [ ] Seed number
