# Skill 迁移方法：从 Cursor/外部 prompt 目录同步到 Hermes

## 场景

将外部 prompt 文件（如 SDDInAction4.0、Cursor skills）批量迁移为 Hermes 注册 skill。

## Cursor Skill 位置

- **用户级**（跨项目）：`C:\Users\Administrator\.cursor\skills\<skill-name>\SKILL.md`
- **项目级**：`<project>/.cursor/skills/<skill-name>/SKILL.md`
- 格式：YAML frontmatter（name + description）+ markdown body

## Hermes Skill 位置

- `~/.hermes/skills/<category>/<skill-name>/SKILL.md`
- 格式相同：YAML frontmatter + markdown body

## 批量迁移方法

### 方法 1：直接从 4.0 源文件写入（推荐）

```bash
python3 << 'PYEOF'
base_40 = "/mnt/d/平时处理文件/.../SDDInAction4.0"
base_hermes = "/home/administrator/.hermes/skills/sdd-architect"

skills = {
    "sdd-spec": (f"{base_40}/2.spec/spec-prompt.md", '---\nname: sdd-spec\ndescription: "描述"\n---\n\n'),
    # ... more mappings
}

for name, (src, frontmatter) in skills.items():
    dst = f"{base_hermes}/{name}/SKILL.md"
    with open(src, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(frontmatter + content)
PYEOF
```

### 方法 2：合并多个 4.0 文件到一个 skill

```bash
python3 << 'PYEOF'
base_40 = ".../SDDInAction4.0/9.debug"
dst = ".../sdd-debug/SKILL.md"
fm = '---\nname: sdd-debug\ndescription: "描述"\n---\n\n'

parts = []
for fname in ["bug-analysis.md", "bug-fix.md", "bug-fix-review.md"]:
    with open(f"{base_40}/{fname}", 'r', encoding='utf-8') as f:
        parts.append(f.read())

content = fm + "\n\n---\n\n".join(parts)
with open(dst, 'w', encoding='utf-8') as f:
    f.write(content)
PYEOF
```

## 注意事项

1. **超大文件**（>100KB）可能导致 context window 溢出，但 skill 注册本身无大小限制
2. **WSL 路径**：Windows 路径用 `/mnt/d/...` 访问
3. **双 frontmatter 问题**：如果源文件已有 YAML frontmatter，需要替换而非叠加
4. **验证**：`wc -l ~/.hermes/skills/sdd-architect/<name>/SKILL.md` 检查行数是否与源文件一致
