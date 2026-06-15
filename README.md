# Skills 仓库

个人沉淀的 Hermes Agent Skill 集合，按领域分类组织。

## 结构

```
skills/
├── README.md
├── .gitignore
├── devops/          # 运维/部署相关
├── data-science/    # 数据分析相关
├── software-development/  # 软件开发
├── productivity/    # 效率工具
├── research/        # 调研/研究
├── ...              # 其他分类
```

## Skill 格式

每个 skill 是一个目录，内含 `SKILL.md`：

```markdown
---
name: my-skill
description: 简短描述
category: devops
---

# My Skill

## 触发条件
什么时候用这个 skill

## 步骤
1. 第一步...
2. 第二步...

## 注意事项
- 踩坑记录
```

## 使用方式

将 skill 目录复制或符号链接到 `~/.hermes/skills/` 下即可被 Hermes 加载：

```bash
# 方式一：复制
cp -r devops/my-skill ~/.hermes/skills/

# 方式二：符号链接（推荐，修改即生效）
ln -s /mnt/d/平时处理文件/skills/devops/my-skill ~/.hermes/skills/
```
