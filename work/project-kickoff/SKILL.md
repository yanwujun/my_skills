---
name: project-kickoff
description: "新项目启动全流程：模糊想法 → 需求文档（痛点→交互方案）→ GitHub 调研现成方案（build vs reuse）→ 技术栈决策 → 工作空间搭建（README/AGENTS/docs 文档链）→ 里程碑。用户说「新开一个项目」「帮我创建/搭建一个工作空间」「做个 XX APP/系统」时使用。"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [project-kickoff, workspace, requirements, build-vs-reuse, github-research]
    related_skills: [development-planning, wsl-project-setup, ideation]
---

# 新项目启动 (Project Kickoff)

把用户的一句话想法落地成一个可开工的工作空间。后续编码交给 development-planning / coding agent。

## Trigger

- 用户说「新开一个项目」「创建/搭建一个工作空间」「我要做个 XX APP/系统」
- 想法模糊（一两句话），需要先梳理需求、调研、再定技术栈

## 核心顺序铁律

**先调研现成方案，再问技术栈。** 用户在提问技术栈时会反问「github 上有没有现成的？」——所以默认流程：需求 → 调研 → 技术栈决策 → 搭空间。不要把 clarify(技术栈) 放在调研前面。

## Step 1 · 需求梳理

- 复述拆解用户的一句话需求，**逐字保留用户原话痛点**，并落成具体交互方案（不是"已理解"式敷衍）。
- 示例：用户说「直接看整个题库有点多」→ 方案 = 一题一屏 + 进度条 + 题号导航 + 草稿保存 + 全部答完统一提交。
- 输出 `docs/需求与交互设计.md`：产品定位、核心需求（引原话）、交互方案、状态流转、开放问题清单。

## Step 2 · GitHub build-vs-reuse 调研

1. **中英双语关键词**并行 web_search：
   - 英文：`github open source <功能> from documents` / `LLM generate <东西> from PDF`
   - 中文：`github 知识库 <功能> 开源项目`（中文生态关键词完全不同，务必双语）
2. **仓库信息用 web_extract 批量拉 `github.com/<owner>/<repo>` 页面**（一次最多 5 URL）：
   页面直接含 ⭐ star / forks / watchers / 最近提交日期 / 语言 / 描述，无需认证、无需 API key。
3. 对比表固定列：`项目 | ⭐ | 技术栈 | 能力 | 活跃度 | 评价`
4. **缺口分析框架（四维度）**：题型 / 交互 / 审核 / 语言 —— 现成项目缺什么 = 你要自己做什么。常见结论：demo 项目只覆盖单题型、无移动端交互、无提交式审核。
5. 结论三选一：直接用 / fork 改造 / **自己搭**（借鉴其 prompt 与流程设计）。判断"改造成本 ≈ 重写"时推荐自己搭。
6. 调研结果存档 `docs/GitHub调研.md`（含结论先行 + 对比表 + 推荐路线）。

## Step 3 · 工作空间搭建

```
<project>/
├── README.md              # 产品一句话 + 核心痛点与解法 + 工作空间结构 + 里程碑
├── AGENTS.md              # 项目约定（给编码代理看）：技术栈、铁律、目录、规范
└── docs/
    ├── 需求与交互设计.md
    ├── GitHub调研.md
    ├── 技术方案.md         # 占位，调研定稿后填
    └── API设计.md          # 占位，接口契约先写文档再实现
```

- **位置：WSL ext4（`~/`），禁止 /mnt/d/ 等 Windows 挂载盘**（9P 协议跨系统 IO 性能灾难，见 wsl-project-setup）。
- AGENTS.md 写入用户既有约定：中文 git commit、编码用 coding agent（codex/opencode）、源码禁放 /mnt/d/。
- 交互方案给"里程碑（草案）"checklist，M1 通常是需求定稿+技术栈选型。

## Step 4 · 收尾

- 给用户交付小结：工作空间路径 + 需求文档要点 + 调研结论（推荐路线）+ 待决策点。
- 用 clarify 抛**一个**高价值决策（技术栈/方向），选项给全。

## Pitfalls

- **调研前先问技术栈 = 必被纠正**。build-vs-reuse 是用户的第一诉求。
- **Hermes Studio workflow MCP 依赖 WebUI HTTP 服务**（网关进程在跑不代表 HTTP 通；先探测 8642/5050 等端口）。连不上时：本地目录工作空间是**有效替代交付**，明确告知"WebUI 启动后可补建可视化 workflow"，不要卡住或假装建了。
- 只信 web_extract 拿到的仓库元数据（star/最近提交），README 吹的功能要对照目录结构核实。
- 现成项目调研最容易漏的维度是**中文支持**——英文出题类项目基本不支持中文内容，直接影响选型。

## 模板

- `templates/workspace-docs.md` — 工作空间文档链骨架（README + 需求文档结构），复制后改。
