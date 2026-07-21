# Graphify vs 业务规则知识图谱：互补分析

> 分析日期：2026-07-20
> 来源：https://github.com/Graphify-Labs/graphify (v8, 91k+ stars)

## Graphify 是什么

AI 编码助手技能，将任意文件夹（代码/文档/PDF/图片/视频）映射为可查询的知识图谱。作为 `/graphify` 命令在 Claude Code、Cursor、Codex、Hermes 等 20+ 平台运行。

### 核心能力速览

| 能力 | 实现方式 |
|------|---------|
| 代码结构图 | tree-sitter AST 解析 ~40 种语言，纯本地，不上传代码 |
| 节点类型 | file, function, class, module, concept |
| 边类型 | imports, calls, inherits, depends_on, tested_by 等 |
| 社区检测 | Leiden 算法分子系统 |
| 查询方式 | query（自然语言）、path（最短路径）、explain（单节点） |
| 增量更新 | `--update` 只重建变更文件；`hook install` git commit 自动触发 |
| MCP 服务 | `python -m graphify.serve graph.json` 暴露为 MCP 工具 |
| PR 分析 | `graphify prs` 支持 PR dashboard、triage、conflicts |

### Graphify "conflicts" 的真相

`graphify prs --conflicts` 检测的是**结构层合并风险**：
> "PR #42 和 PR #57 都改了 auth 模块的文件 → 合并时可能产生代码冲突"

这是 merge-order risk，**不是业务规则冲突**。它回答不了：
> "OrderService 把金额下限从 100 改成了 50，但 PaymentService 还是按 100 校验 → 用户下单成功但付不了款"

## 层级对比：互补，不重叠

```
层级          Graphify 覆盖              业务规则系统覆盖
─────────────────────────────────────────────────────────
结构层        ✅ 文件→函数→类→调用关系    ❌ 不涉及
              tree-sitter AST 精确解析

语义层        ❌ 不涉及                    ✅ 业务约束提取
              Graphify 的节点是           （订单金额≥100、
              代码符号，不是业务规则       供应商必须审核通过、
                                          状态流转必须按顺序）

冲突检测      ✅ 合并风险（同社区PR）      ✅ 业务规则一致性
              结构层冲突                   （跨文件/跨服务的
                                          规则参数不一致）
```

## 推荐架构：Graphify 做底座

```
Graphify（代码结构图 graph.json）
    │  节点：file/function/class/module
    │  边：   imports/calls/inherits/depends_on
    │
    ▼  为每个代码节点补充业务语义
业务规则层（规则提取 → 规则图谱 → 冲突检测）
    │  节点：business_rule
    │        ├── rule_type: validation/authorization/calculation/workflow/...
    │        ├── properties: {threshold: 100, field: "Order.total", operator: ">="}
    │        └── domain/flow: 订单管理/用户下单流程
    │
    │  边：   implements → 指向 Graphify 代码节点（函数/类）
    │        constrains → 指向被约束的数据模型（实体字段）
    │        conflicts_with → 指向冲突的规则
    │        belongs_to_flow → 指向业务流程
    │
    ▼  输出
冲突报告 / 规则溯源 / 影响分析
```

### 选择 Graphify 做底座的好处
- 省掉代码结构层全部工作量（AST 解析 40+ 语言、增量更新、图存储、HTML 可视化、MCP 服务）
- 专注在业务规则提取和冲突检测这两个独特功能
- Graphify 已有 `graphify hermes install` 支持 Hermes 集成

### 代价
- 依赖外部工具（但活跃维护，91k+ stars）
- SVN 项目需适配（`diff-to-business-rules` 也只支持 git diff）

## 安装与使用

```bash
# 安装
uv tool install graphifyy
graphify install

# 在 Hermes 中注册
graphify hermes install

# 构建知识图谱
/graphify .

# 查询
graphify query "auth 模块和数据库之间有什么联系？"
graphify path "UserService" "DatabasePool"
graphify explain "RateLimiter"

# MCP 服务
python -m graphify.serve graph.json --transport http --port 8080
```

## 关键限制（对业务规则系统的影响）

1. **Graphify 不提取业务规则** — 只做代码结构分析，需要在其之上构建业务规则层
2. **Graphify 不做规则冲突检测** — `--conflicts` 是结构层合并风险，不是语义层冲突
3. **需要 LLM 直通或 API key** — 文档/PDF/图片的语义提取需要 LLM 后端（代码部分纯本地）

## 相关工具对比

| 工具 | 覆盖层 | 提取方式 | 冲突检测 |
|------|--------|----------|---------|
| Graphify | 代码结构 | tree-sitter AST | 结构层（PR合并风险） |
| CodeGraph | 代码结构 | 静态分析 | 无 |
| diff-to-business-rules | 业务规则 | LLM 读 diff | 无（仅文档生成） |
| **business-rule-graph（目标）** | **业务规则** | **AST + LLM 混合** | **业务层（规则一致性）** |
