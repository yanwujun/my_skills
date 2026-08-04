---
name: ai-sdd-workflow
description: AI 辅助的轻量级 SDD 工作流 — 用 OpenSpec 管需求规格、Cursor Rules 管编码规范，双引擎合并实现一次生成正确代码。含 alwaysApply 策略和与 Hermes Skill 的对应关系。
---

# AI-SDD 轻量工作流

当用户需要：设计 AI 编码助手的规范体系、整合 spec 工具与 Cursor Rules、搭建需求到代码的 SDD 流水线时使用。

## 核心双引擎

```
OpenSpec  →  造什么（需求规格）
Cursor Rules → 怎么造（编码规范）
       ↓
  Cursor/Claude Agent
       ↓
   一次生成正确代码
```

## OpenSpec（规格层）

- 仓库：https://github.com/Fission-AI/OpenSpec
- 核心命令：`/opsx:explore` → `/opsx:propose <feature>` → `/opsx:apply` → `/opsx:archive`
- 产物目录：`openspec/changes/<name>/`
  - `proposal.md` — 需求动因
  - `specs/` — 场景用例（WHEN...THEN 格式）
  - `design.md` — 技术方案
  - `tasks.md` — 实现清单
- 定位：比 GitHub spec-kit 轻，比 Kiro 自由

## Cursor Rules（规范层）

### `alwaysApply` 策略（关键）

```yaml
# ✅ 推荐 — 按需加载，语义匹配
alwaysApply: false
description: Java Spring Boot 编码规范：分层、命名、Redis锁、MyBatis约定

# ❌ 不推荐 — 每次注入，浪费 token
alwaysApply: true   # 仅元规则（如 knowledge-sedimentation）才该用
```

Cursor 根据 `description` 和当前任务做语义匹配。写 Spring Boot 才加载后端规则，改前端不加载。

### 规则分类建议

| 类型 | alwaysApply | 示例 |
|------|:---:|------|
| 元规则（指挥 AI 行为） | true | `knowledge-sedimentation.mdc` |
| 编码规范 | false | `conventions.mdc`、`springboot-standards.mdc` |
| 架构约束 | false | `feign-default-config.mdc` |
| 项目上下文 | false | `project-structure.mdc` |

## 与 Hermes Skill 的对应

| | Cursor Rules | Hermes Skill |
|--|:---:|:---:|
| 格式 | YAML + Markdown `.mdc` | YAML + Markdown `SKILL.md` |
| 加载方式 | `alwaysApply: false` + 语义 | `skill_view(name)` 按需 |
| 适用 | Cursor IDE | CLI / Hermes Studio |

内容互通，同一个规范可两边维护。

## 落地步骤

1. **OpenSpec** 管需求：`/opsx:propose <feature>` 生成 specs
2. **Cursor Rules** 管执行：`.cursor/rules/` 下分类放规范
3. **合并执行**：`/opsx:apply` 时 Agent 同时看到 spec + rules
4. **验证闭环**：specs 场景 → 测试用例

## 示例：Spring Boot 直采商城

```
需求：商品价格审核
  │
  ├─ OpenSpec: opsx:propose price-audit
  │   specs/price-audit.md: "WHEN 商家改价格 THEN 触发审核"
  │
  ├─ Cursor Rules 注入:
  │   conventions.mdc: saleAgent 命名，SQL 写 D 盘
  │   Feign 规则: 不全局注册 Feign.Builder
  │
  └─ opsx:apply → 一次生成合规代码
```
