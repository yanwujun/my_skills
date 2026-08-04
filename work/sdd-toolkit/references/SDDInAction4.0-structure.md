# SDDInAction4.0 全量目录结构

> 来源：`D:\平时处理文件\2026年7月\SDD\SDDInAction4.0\`
> 对应书籍：`SDDInAction.pdf`（260页，2026年4月版，作者20年+架构经验）
> 本文件为 `sdd-toolkit` + `sdd-architect` 的联合参考。

---

## 完整目录树

```
SDDInAction4.0/
├── 0.agents/
│   ├── constitution.md              # 项目宪法 C1-C7（不可协商）
│   ├── AGENTS.md                    # AI Agent 执行 SOP S1-S5
│   ├── AGENTS-Combined.md           # 宪法+SOP 合并版（单文件注入）
│   ├── AGENTS-Combined-NonSDD.md    # 非 SDD 项目版（无 spec/plan/tasks 体系）
│   ├── CLAUDE.md                    # @导入 constitution + AGENTS
│   └── andrej-karpathy-CLAUDE.md    # Karpathy 风格 AGENTS 参考
├── 1.git/
│   ├── C++.gitignore
│   ├── CSharp.gitignore
│   ├── Python.gitignore
│   ├── frontend.gitignore
│   └── springboot.gitignore
├── 2.spec/
│   └── spec-prompt.md               # v5.0 需求澄清 → spec.md
├── 3.plan/
│   ├── web/
│   │   ├── plan-prompt-web-java.md
│   │   ├── plan-prompt-web-python.md
│   │   └── plan-prompt-web-csharp.md
│   ├── cli/
│   │   ├── plan-prompt-cli-java.md
│   │   ├── plan-prompt-cli-python.md
│   │   ├── plan-prompt-cli-csharp.md
│   │   └── plan-prompt-cli-cpp.md
│   └── db/
│       └── db-design-prompt.md
├── 4.tasks/
│   ├── tasks-prompt-web.md
│   └── tasks-prompt-cli.md
├── 5.coding/
│   ├── coding-prompt.md             # v3.3 任务实现
│   └── pr-prompt.md                 # PR 描述生成
├── 6.skills/
│   ├── JavaCodeReview/SKILL.md
│   ├── PythonCodeReview/SKILL.md
│   ├── CSharpCodeReview/SKILL.md
│   ├── CppCodeReview/SKILL.md
│   └── LogAnalysis/SKILL.md
├── 7.docker/
│   ├── backend-java-docker-prompt.md
│   ├── backend-python-docker-prompt.md
│   ├── backend-csharp-docker-prompt.md
│   ├── backend-cpp-docker-prompt.md
│   └── frontend-docker-prompt.md
├── 8.e2e/
│   ├── e2e-playwright-sdd-prompt.md
│   └── e2e-playwright-manual-prompt.md
├── 9.debug/
│   ├── bug-analysis.md              # v2.4 根因分析（只分析不修改）
│   ├── bug-fix.md                   # v2.6 修复实施（先测试后修复）
│   └── bug-fix-review.md           # 修复审查
├── 10.maintenance/
│   ├── repo-analysis.md
│   ├── change-impact-analysis.md
│   └── strangler_fig_pattern.md
└── 11.prototype/
    ├── 01-requirement-mapping-prompt.md
    ├── 02-prototype-planning-prompt.md
    ├── 03-prototype-creation-prompt.md
    ├── 04-prototype-presentation-prompt.md
    ├── 05-feedback-synthesis-prompt.md
    ├── 06-prototype-adjustment-prompt.md
    ├── 07-prototype-evaluation-prompt.md
    ├── 08-prototype-handoff-prompt.md
    └── README.md
```

---

## SDDInAction.pdf 书籍章节映射

| 章 | 页码范围 | 对应 4.0 模块 | 亮点 |
|---|---|---|---|
| 0. AI Coding 现状与趋势 | p1-15 | 无 | StackOverflow 调查数据、4大趋势 |
| 1. AI 如何编码（LLM 原理） | p16-27 | 无 | 鹦鹉vs乌鸦、涌现、章鱼测试 |
| 2. 规范驱动开发 SDD | p52-68 | 2/3/4 | 会议室预约完整案例 |
| 3. 搭建 SDD 开发环境 | p69-105 | 0.agents | 宪法设计思路详解、长期记忆vs短期记忆 |
| 4. 从模糊想法到 spec.md | p106-138 | 2.spec | 5轮需求澄清实况 + Prompt 逐行分析 |
| 5. 从 spec 到 plan.md（Java） | p139-155 | 3.plan | plan prompt 设计思路深度剖析 |
| 6. 从 plan 到 tasks.md（Java） | p156-170 | 4.tasks | DDD+TDD+Surgical Delivery 三合一 |
| 7. 从 tasks 到源代码（Java） | p171-174 | 5.coding | 新会话避免上下文稀释 |
| 8. Skills 介绍 | p175-186 | 6.skills | 渐进式披露、SRP、description 写作 |
| 9. 协同审查 Review/Commit/PR | p187-200 | 6.skills | Code Review Skill + /commit + PR |
| 10. 人工验证 | p202-211 | 无 | JWT 鉴权等 4 个实际问题修复 |
| 11. 容器化部署 | p212-227 | 7.docker | Dockerfile 逐行分析 |
| 12. 线上问题诊断 | p228-234 | 9.debug | 人工注入 NPE → AI 诊断实战 |
| 13. E2E 测试 | p235-245 | 8.e2e | Playwright MCP 操作演示 |
| 14. 代码重构 | p246-248 | 10.maintenance | 重构点提取 + 小步提交 |
| 15. 生成技术文档 | p249-251 | 无 | README 自动生成 prompt |
| 总结/展望 | p252-260 | 无 | 古法编程 vs AI、Copilot 翻车案例 |
