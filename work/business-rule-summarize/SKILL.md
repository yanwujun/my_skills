---
name: business-rule-summarize
description: 用 Hermes 宿主 LLM 对 AST 提取的业务规则做语义增强（domain/flow/description），无需额外 API Key。
argument-hint: "[project-path] [--force]"
---

# Business Rule Summarize

**用途**：给 AST 引擎提取的原始业务规则补充业务语义（domain、flow、description），使用 Hermes 自己的 LLM，不需要额外 API Key。

**和 `roam business-rules summarize` 的区别**：
- `roam business-rules summarize` 需要自己在环境变量配 OPENAI_API_KEY，独立调用外部 API
- 本 skill 直接用 Hermes 的 LLM 处理，和 understand-anything 一样零配置

## 触发条件

- "给业务规则做语义化" / "补充业务语义" / "规则 LLM 增强"
- "给规则打标签" / "标注业务域"
- 提取完规则后想补充 domain/flow/description

## 流程

```
Step 1: 确保有原始规则 → roam business-rules extract (if needed)
Step 2: 从 DB 读规则，分批（50条/批）
Step 3: Hermes LLM 语义增强 → domain/flow/description/severity/merge_with
Step 4: UPDATE 写回 SQLite
```

## Instructions

### Phase 0: Resolve project path

- If `$ARGUMENTS` has a path, resolve against CWD
- Otherwise use CWD as project root
- Verify `.roam/index.db` exists; if not, tell user to run `roam index` first

### Phase 1: Extract rules (if needed)

```bash
roam business-rules extract
```

Check if the `business_rules` table has rows:

```python
import sqlite3
conn = sqlite3.connect(f"{project_root}/.roam/index.db")
count = conn.execute("SELECT COUNT(*) FROM business_rules").fetchone()[0]
conn.close()
```

If count == 0, run extract and re-check.

### Phase 2: Read rules needing enrichment

Query rules where `domain = ''` or `description = ''`:

```python
conn = sqlite3.connect(f"{project_root}/.roam/index.db")
conn.row_factory = sqlite3.Row
rows = conn.execute(
    "SELECT * FROM business_rules WHERE domain = '' OR description = '' ORDER BY source_file, source_line"
).fetchall()
conn.close()
```

If no rules need enrichment, tell user "所有规则已标注语义，无需处理" and stop.

### Phase 3: Batch-process through Hermes LLM

Process rules in batches of up to 50. For each batch, construct this prompt:

---

**System prompt:**

```
你是政府采购系统的业务分析师。你会收到一批从 Java 代码中自动提取的业务规则。
你的任务是对每条规则补充业务语义。

输入格式：每条规则包含 rule_id, rule_type, source_file, source_line, source_symbol, params, annotations

输出格式：JSON 对象 {"rules": [...]}，只输出 JSON，不要任何解释文字。

对每条规则输出：
- rule_id: 保持原样
- domain: 业务域（订单管理/供应商管理/商品管理/支付管理/审核管理/合同管理/框架协议/直采商城/系统管理）
- flow: 业务流程（下单/支付/审核/发货/签约/退款/同步/提交/审批 等，尽量精确）
- description: 自然语言业务描述（30字以内，用业务用语）
- severity: critical/high/medium/low
- merge_with: 如果与输入中另一条规则是同一规则的不同写法，填对方的 rule_id；否则 null

关键规则：
- description 必须用业务语言，不要复制代码
- domain 根据业务含义分类，不要依赖包名
- 发现同一业务含义的不同写法应标记 merge_with（如 total>=100 和 amount<100则抛异常）
- 不要修改 rule_id
```

**User prompt (batch N):**

```
请对以下业务规则补充语义：

[
  {"rule_id": "...", "rule_type": "validation", "source_file": "...", "source_line": 145, "source_symbol": "validateAmount", "params": {"field": "total", "operator": ">=", "threshold": "100", "exception_message": "订单金额不能低于100元"}},
  ...
]
```

Output the JSON directly in your response, then parse it and update the DB.

### Phase 4: Update DB

For each enriched rule, UPDATE:

```python
conn = sqlite3.connect(f"{project_root}/.roam/index.db")
for rule in enriched_rules:
    conn.execute(
        """UPDATE business_rules 
           SET domain=?, flow=?, description=?, severity=?, merge_with=?, updated_at=datetime('now')
           WHERE rule_id=?""",
        (rule["domain"], rule["flow"], rule["description"], rule["severity"], rule.get("merge_with"), rule["rule_id"])
    )
conn.commit()
conn.close()
```

### Phase 5: Report

Show summary:
- Total rules processed: N
- Domain distribution
- Merged rules count (those with merge_with non-null)

## Pitfalls

1. **不要用 `--agent` 模式** — 那是独立 CLI 的手动导出流程。本 skill 直接在 Hermes 对话中处理。
2. **LLM 输出只取 JSON** — 解析前 strip 掉可能的 markdown 代码块标记（```json ... ```）
3. **SQLite 写入冲突** — 如果 `roam dashboard-serve` 或其他进程在读 DB，先停掉
4. **大项目分批** — 超过 500 条规则时，提示用户分批处理（每批 50-100 条），避免 token 超限
5. **保留原始规则** — UPDATE 只改 domain/flow/description/severity/merge_with，不碰 rule_id/rule_type/params/hash
6. **rule_id 必须用 DB 真实值** — AST 提取器生成的 rule_id 格式是 `文件路径:行号:@注解名`，不能自己构造。必须先用 `SELECT rule_id, source_file, source_symbol FROM business_rules` 读出真值，构造 prompt 时用真实 rule_id，更新时也用真实 rule_id 匹配。
