# SDD Skill 覆盖地图

> 记录 Hermes 中 SDD 相关 skill 与 SDDInAction4.0 工具集的对应关系。
> 两个 skill 联合覆盖 SDDInAction4.0 全部 11 个模块（缺 1.git/ 辅助模板）。

## Hermes SDD Skills

| Skill | 覆盖 4.0 阶段 |
|---|---|
| `sdd-architect` | Phase 1-4: 分析 → spec → plan → tasks |
| `sdd-toolkit` | Phase 5-11: coding → review → docker → e2e → debug → maintenance → prototype |

**注意**：`sdd-architect` 核心链路原文写的是「sdd-code skill」但实际不存在，正确的是 `sdd-toolkit`。搜索 SDD skill 时应两个都查。

## SDDInAction4.0 全覆盖矩阵

| 4.0 模块 | 负责 skill | 说明 |
|---|---|---|
| 0.agents/ | sdd-toolkit | constitution.md + AGENTS.md 全局注入 |
| 1.git/ | 未覆盖 | .gitignore 模板（Java/C#/Python/C++/前端） |
| 2.spec/ | sdd-architect | spec-prompt.md v5.0 |
| 3.plan/ | sdd-architect | web/cli 多技术栈 plan prompt |
| 4.tasks/ | sdd-architect | web/cli tasks prompt |
| 5.coding/ | sdd-toolkit | coding-prompt + pr-prompt |
| 6.skills/ | sdd-toolkit | 5 个 Code Review skill + LogAnalysis |
| 7.docker/ | sdd-toolkit | 5 个多技术栈 Dockerfile prompt |
| 8.e2e/ | sdd-toolkit | Playwright SDD + Manual prompt |
| 9.debug/ | sdd-toolkit | bug-analysis → bug-fix → bug-fix-review 三阶段 |
| 10.maintenance/ | sdd-toolkit | repo-analysis, change-impact, strangler_fig |
| 11.prototype/ | sdd-toolkit | 8 步原型工作流 |

## SDDInAction.pdf vs 4.0 vs Skills

- **PDF (260页)**: 教材，含 AI Coding 背景、设计原理讲解、会议室预约完整案例、宪法设计哲学
- **4.0 目录 (50+文件)**: 可执行工具集，所有 prompt 和 skill 模板
- **Hermes skills (2个)**: 4.0 的索引层，按需加载 prompt 文件执行

## 已知限制

1. Prompt 路径硬编码为 `D:\平时处理文件\2026年7月\SDD\SDDInAction4.0\`，仅 Windows 环境可用
2. `1.git/` 的 5 个 .gitignore 模板未被任何 skill 引用
3. 4.0/6.skills/ 下的 5 个 Code Review SKILL.md 仅为文件模板，未注册为 Hermes skill
4. `sdd-architect` 核心链路引用不存在的 `sdd-code`，应为 `sdd-toolkit`（待手动修复）
