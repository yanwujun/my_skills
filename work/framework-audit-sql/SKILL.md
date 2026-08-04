---
name: framework-audit-sql
description: "框架协议AI商品审核质量分析SQL — ai_audit_session + oper_record配对查询、准确率统计、审核理由对比、重放准备。show1-zcj(31404)专用。"
version: 1.0.0
author: hermes
metadata:
  hermes:
    tags: [框架协议, AI审核, SQL, 商品审核, 准确率]
    related_skills: [framework-contract-sql]
---

# 框架协议 AI 商品审核 SQL

## 适用环境

| 项目 | 值 |
|------|-----|
| 数据库 | **show1-zcj** `192.168.2.37:31404` |
| MCP连接ID | `show1-ezc`（需重启Hermes生效） |
| 表 | `ezc.ai_audit_session` + `ezc.oper_record` + `ezc.protocol_goods` |
| 数据范围 | `oper_record` 到 2026-07-19，`ai_audit_session` 到 2026-07-08 |

> ⚠️ 主库(31004)的 `ezc.oper_record` 已清理到2025-09，**AI审核数据只在 show1-zcj(31404) 可查**。

## 核心表

### ai_audit_session — AI审核异步会话

| 字段 | 说明 |
|------|------|
| `id` | 会话ID |
| `businessId` | 商品ID（protocol_goods.id） |
| `businessCode` | GOODS_COMPLETE_AUDIT / GOODS_MODIFY_AUDIT |
| `status` | PENDING / COMPLETED / FAILED / REPLACED |
| `resultJson` | 审核结果JSON |
| `createTime` | 会话创建时间 |

### resultJson 结构

```json
{
  "auditResult": 0,       // 0=不通过, 1=通过
  "auditReason": "...",   // AI审核理由
  "auditResultStr": "...",// 完整结果含修复建议
  "issues": [...]         // 问题数组
}
```

### oper_record — 审核流水（operType对照）

| operType | 含义 | 对应operName |
|----------|------|-------------|
| 2 | 通过 | 智能审核通过、初审通过、通过 |
| -1 | 退回 | 智能审核退回、退回 |
| -2 | 撤回 | 撤回 |
| 1 | 提交 | 提交 |

## 查询模式

### 1. AI vs 人工审核准确率（按时间段）

参考模板：`/mnt/d/平时处理文件/2026年7月/框架协议/AI商品审查准确率_按时间段查询_20260722.sql`

核心逻辑：
- AI `oper_record`（智能审核通过/退回）→ 之后最早的人工结论（初审通过/通过/退回）
- 排除 AI→人工 之间有撤回的样本
- 准确率 = AI operType 与人工 operType 一致的占比

### 2. AI+人工审核理由对比 + 商品信息 + 重放准备

参考模板：`/mnt/d/平时处理文件/2026年7月/框架协议/AI审核_商品信息_重放准备_20260722.sql`

三表关联：
```
ai_audit_session ──时间就近──→ oper_record (AI)
                              └──最近──→ oper_record (人工)
                  └──────────→ protocol_goods (商品信息)
```

⚠️ **session 与 oper_record 无外键**，匹配方式：
- 同 `businessId + businessCode`
- `oper_record.operTime >= ai_audit_session.createTime`
- 取时间最近的一条

## 分析模式

### 3. Excel导出分析（Python）

当用户提供从系统导出的审核结果Excel时，用 `pandas` 精确统计。Excel通常混合「待审核」和已审核记录。

⚠️ **关键陷阱：不要基于前N行推断全表状态。** Excel中已审核记录可能集中在文件后部（人工审核是按时间倒序或批次处理的），前面大量 `\N` 不代表全表无人工数据。**必须用Python统计整个DataFrame**，不能凭手动阅读几行下结论。

Python统计模板：
```python
import pandas as pd
df = pd.read_excel(path, dtype=str)
cc = df['结论一致性'].fillna('NULL').replace(r'\N', 'NULL', regex=False)
reviewed = df[cc.isin(['一致', '不一致'])]
pending = df[~cc.isin(['一致', '不一致'])]
print(f'已审核: {len(reviewed)}, 待审核: {len(pending)}')
print(pd.crosstab(reviewed['结论一致性'], reviewed['AI审核结论']))
```

已知的不一致模式参考：`references/audit-patterns-1.26.8.2.md`

**一键分析脚本**：`scripts/analyze_excel_audit.py` — 直接传入Excel路径，自动输出完整分析报告（总体→交叉矩阵→分目录→不一致归类）。

⚠️ **AI结论双通道陷阱**：Excel中`AI审核结论`（COMPLETED会话LLM输出）和`AI结论type`（oper_record流水）是两条独立路径。76条FAILED会话的`AI审核结论`为`\\N`，但`AI结论type=-1`表示实际被退回。分析时必须**先取AI审核结论，为\\N时回退到AI结论type**，否则会漏掉~23%的AI退回记录。

**输出报告要求：**
- 必须用精确数字，禁止估算（如"约90-100条"）
- 交叉矩阵 + 分品类统计 + 不一致原因归类三层结构
- 指出AI盲区和改进建议

## 注意事项

1. 必须先通过诊断查询确认数据存在：`/mnt/d/平时处理文件/2026年7月/框架协议/诊断_AI审核查不到数据_20260722.sql`
2. 同一商品多次审核时用时间就近匹配避免一对多错配
3. `$.auditResult` 值为 `0`(不通过)或 `1`(通过)，需用 `JSON_UNQUOTE(JSON_EXTRACT(...))` 提取
4. 商品信息 LEFT JOIN，因为 `businessId` 可能对应非 `protocol_goods` 表
5. 会话状态过滤：一般只取 `COMPLETED`，`FAILED`/`REPLACED` 不是有效审核结果
6. Excel分析时**禁止估算**——必须用Python做精确统计，用户对数字准确性要求高
7. **heredoc超时陷阱**：`python3 << 'PYEOF' ... PYEOF` 在大脚本时易触发审批超时。正确做法：先用 `write_file` 保存脚本到 `/tmp/`，再用 `terminal` 执行 `python3 /tmp/script.py`。
