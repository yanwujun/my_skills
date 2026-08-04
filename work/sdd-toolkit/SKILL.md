---
name: sdd-toolkit
description: "SDD 全生命周期工具索引。所有 SDD skill 已内嵌 SDDInAction4.0 原文，无需外部加载。本 skill 提供快速导航：哪个阶段用哪个 skill。"
version: 2.0.0
triggers:
  - spec 写完了、plan 好了、tasks 有了，接下来
  - 怎么 coding、怎么 review、怎么 docker、怎么 e2e
  - bug 怎么分析、怎么修、怎么回归
  - SDD 全流程、完整流程、SDD 有哪些 skill
---

# SDD 全生命周期工具索引

所有 SDD skill 已内嵌 SDDInAction4.0 原文，**无需手动加载外部 prompt 文件**。本 skill 提供快速导航。

## 17 个 SDD Skill 总览

| # | Skill | 阶段 | 4.0 源文件 | 说明 |
|---|-------|------|-----------|------|
| 1 | `sdd-architect` | 全局 | 0.agents/ | 宪法 C1-C7 + 执行协议 S1-S4，总管 |
| 2 | `sdd-spec` | 设计 | 2.spec/ | spec.md 需求澄清 v5.0（372行原文） |
| 3 | `sdd-nfr` | 设计 | — | 非功能需求分析（spec→plan之间） |
| 4 | `sdd-plan` | 设计 | 3.plan/ | plan.md 技术方案 v3.1（236行原文） |
| 5 | `sdd-adr` | 设计 | — | 架构决策记录 |
| 6 | `sdd-tasks` | 设计 | 4.tasks/ | tasks.md 任务拆分 v3.2（118行原文） |
| 7 | `sdd-code` | 实施 | 5.coding/ | 编码实现 v3.3 + PR v2.0（125行原文） |
| 8 | `sdd-code-review` | 实施 | 6.skills/ | Java 代码评审（110行原文） |
| 9 | `sdd-converge` | 质量门禁 | — | 三阶段收敛检查：analyze→checklist→converge v1.0 |
| 10 | `sdd-openapi` | 实施 | — | OpenAPI 3.0 文档生成 |
| 11 | `sdd-e2e` | 实施 | 8.e2e/ | Playwright E2E 测试 v1.2（213行原文） |
| 12 | `sdd-debug` | 维护 | 9.debug/ | Bug 分析+修复+审查三阶段（604行原文） |
| 13 | `sdd-refactor` | 维护 | 10.maintenance/ | 仓库分析+影响分析+绞杀者重构（1865行原文） |
| 14 | `sdd-prototype` | 验证 | 11.prototype/ | 前端原型八步工作流（3533行原文） |
| 15 | `sdd-brownfield-planning` | 规划 | — | 棕地项目规划模板 |
| 16 | `sdd-ux-journey` | 验证 | — | 用户旅程图 |
| 17 | `sdd-toolkit` | 索引 | — | 本文件 |

## 完整 SDD 链路

```
棕色项目              绿色项目              日常维护
    │                     │                     │
    ▼                     ▼                     ▼
sdd-brownfield-      sdd-spec             sdd-debug
  planning               │               (分析→修复→审查)
    │                     ▼                     │
    │                 sdd-nfr                   │
    │                 sdd-plan                  │
    │                 sdd-adr                   │
    │                     │                     │
    ▼                     ▼                     │
sdd-refactor           sdd-tasks               │
(绞杀者模式)              │                     │
    │                     ▼                     │
    │                 sdd-code                  │
    │                     │                     │
    ▼                     ▼                     ▼
sdd-code-review ◄────────────────────────────────┘
    │
    ▼
sdd-converge  ← 新增：三阶段质量门禁
    │
    ▼
sdd-e2e / sdd-prototype / sdd-ux-journey
    │
    ▼
sdd-openapi
```

## 使用原则

1. **按需加载**：不要一次性加载所有 skill，根据当前阶段选择对应 skill
2. **设计阶段用 sdd-architect 统领**：它会根据任务自动引导到 spec → plan → tasks
3. **实施阶段直接加载对应 skill**：如 `sdd-code`、`sdd-code-review`
4. **所有 skill 已内嵌原文**：不需要再去 `D:\平时处理文件\...` 手动加载 prompt

## 与 SDDInAction4.0 的对应关系

每个 skill 的 SKILL.md 直接包含对应 4.0 prompt 文件的完整内容 + YAML frontmatter。
4.0 目录仅作为备份参考，实际执行时使用 Hermes skill 即可。

详见 `references/sdd-skill-map.md`。