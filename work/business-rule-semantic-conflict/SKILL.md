---
name: business-rule-semantic-conflict
description: 用 Hermes 宿主 LLM 做语义级规则冲突检测——发现 AST 机械对比漏掉的语义冲突（同义不同名、矛盾阈值、权限不一致等）。
argument-hint: "[project-path]"
---

# Business Rule Semantic Conflict Detection

**用途**：在 AST 冲突检测（`roam business-rules check`）之后，用 LLM 发现**语义级**冲突——AST 对比不出来的规则矛盾。

**为什么需要**：AST 只能比较完全相同字段的阈值。两个字段叫 `orderAmount` 和 `totalPrice` 但都指"订单金额"时，AST 认为无冲突。LLM 能识别这种同义不同名的矛盾。

## 触发条件

- "检查语义冲突" / "LLM 冲突检测" / "语义矛盾"
- 跑完 `roam business-rules extract` + summarize（语义化）后
- 代码里两处规则看似不冲突但含义矛盾时

## 流程

```
Step 1: AST 冲突检测 → roam business-rules check（机械对比，精确但覆盖面窄）
Step 2: 读所有已语义化的规则
Step 3: Hermes LLM 语义冲突分析 → 发现 AST 漏掉的反直觉矛盾
Step 4: 输出冲突报告
```

## Instructions

### Phase 0: Resolve project path

- If `$ARGUMENTS` has a path, resolve against CWD. Otherwise use CWD.
- Verify `.roam/index.db` has business rules with LLM-enriched domain/flow/description.

### Phase 1: Run AST conflict detection first

```bash
roam business-rules check
```

Save this output. Then proceed to find what AST missed.

### Phase 2: Read all enriched rules

```python
import sqlite3
conn = sqlite3.connect(f"{project_root}/.roam/index.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("""
    SELECT rule_id, rule_type, domain, flow, description, severity,
           source_file, source_line, source_symbol, params
    FROM business_rules
    WHERE domain != '' AND description != ''
    ORDER BY domain, flow, rule_type
""").fetchall()
conn.close()
```

Group rules by domain for LLM analysis.

### Phase 3: LLM semantic conflict analysis

For each domain, construct a prompt with ALL rules in that domain. Have the LLM look for contradictions.

---

**System prompt:**

```
你是政府采购系统的业务规则审查专家。你会收到同一业务域下的多条规则。
你的任务是发现其中可能存在的**语义矛盾**——AST 机械对比查不出来的冲突。

你需要发现以下几类矛盾：

1. **同义不同名**：两个规则描述的是同一个业务概念（如订单金额），但参数/阈值不一致
   例：规则A说 "订单金额>=100"（字段名orderAmount），规则B说 "订单总额<=50"（字段名totalPrice）
   虽然字段名不同，但都指"订单金额"，阈值矛盾

2. **业务逻辑矛盾**：两个规则的业务含义互相矛盾
   例：规则A说 "已提交的订单可以修改"，规则B说 "已提交的订单不允许修改"

3. **权限冲突**：同一操作在不同的地方有不同的权限要求
   例：规则A说 "任何登录用户都可以删除订单"，规则B说 "只有管理员可以删除订单"

4. **状态流转矛盾**：状态机的两个规则互相矛盾
   例：规则A说 "已审核→已完成"，规则B说 "已审核→已驳回"，两个都允许但业务上可能只能选一个

5. **严重度不对称**：同一业务概念的一个校验标为low，另一个标为critical
   例："金额校验"在两个地方一模一样的逻辑，一个low一个critical

输入格式：JSON数组，每条规则含 rule_id, rule_type, description, source_file, source_line, params

输出格式：JSON对象 {"conflicts": [...]}，只输出JSON。

每条冲突：
{
  "type": "semantic_threshold | business_logic | auth_conflict | status_conflict | severity_asymmetry",
  "severity": "critical | high | medium | low",
  "rule_a_id": "规则A的rule_id",
  "rule_b_id": "规则B的rule_id",
  "description": "用中文描述矛盾所在（50字以内）"
}

如果没有发现矛盾，输出 {"conflicts": []}
```

**User prompt:**

```
以下是 {domain} 域下的所有规则，请检查语义矛盾：

[
  {"rule_id": "...", "rule_type": "validation", "description": "订单金额不能低于100元", "source_file": "OrderValidator.java", "source_line": 45, "params": {"field": "total", "operator": ">=", "threshold": "100"}},
  ...
]
```

### Phase 4: Merge with AST results

Combine AST conflicts (from Phase 1) with LLM conflicts (from Phase 3).
Deduplicate by checking if the same two rule_ids already appeared in AST results.
Report combined findings.

### Phase 5: Report

Format:

```
## 冲突检测报告

### AST 机械对比 (N conflicts)
| 类型 | 严重度 | 规则A | 规则B | 说明 |
...

### LLM 语义分析 (M conflicts)
| 类型 | 严重度 | 规则A | 规则B | 说明 |
...

### 总计: N + M = TOTAL conflicts
```

## Pitfalls

1. **必须先用 AST** — AST 能精确检测的不要用 LLM 重复做
2. **按 domain 分批** — 不同 domain 的规则不太可能冲突，避免在全域扫描浪费 token
3. **忽略明显的无冲突** — 配置类规则（@Value）和数据建模规则（@Table/@Column）通常不会互相矛盾，可以跳过
4. **LLM 可能误报** — 语义冲突需要人工确认，不是所有 LLM 发现的矛盾都是真正的 bug
5. **去重** — LLM 可能重复报告 AST 已经发现的冲突，需要和 Phase 1 结果对比去重
