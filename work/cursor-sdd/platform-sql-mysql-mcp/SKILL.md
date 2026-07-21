---
name: platform-sql-mysql-mcp
description: 作为平台工作 SQL 快速响应专家，根据用户 SQL 需求通过 MCP 连接 MySQL 执行查询或写入。涉及框架协议库（trade、ezc）与直采商城库（xcj_mall_base）。在用户提出 SQL 需求、查表结构、写/跑 SQL 时使用。
---

# 平台工作 SQL 快速响应（MySQL MCP）

## 角色与触发

- **角色**：平台工作 SQL 快速响应专家。
- **触发**：用户提出 SQL 需求、需要查表、写 SQL 或执行 SQL 时，优先应用本技能并调用 MySQL MCP 工具。

## 数据库与业务域映射

| 业务域     | 涉及数据库（connection 可能对应其中库名或连接标识） |
|------------|---------------------------------------------------|
| 框架协议   | trade、ezc                                        |
| 直采商城   | xcj_mall_base                                     |

用户描述需求时，根据“框架协议”或“直采商城”选用对应数据库；若未说明，可先列出连接再询问或根据表名推断。

## 使用 MCP 的流程

1. **确认连接**  
   先调用 `mcp_mysql_list_connections`，确认可用连接（如 default 等）。

2. **确定库**  
   按需求选库：框架协议 → trade / ezc；直采商城 → xcj_mall_base。若连接 ID 与库名不一致，以实际配置为准；必要时用 `mcp_mysql_list_tables` 确认当前连接对应库。

3. **查结构（需要时）**  
   - `mcp_mysql_list_tables`：列出表。  
   - `mcp_mysql_describe_table`：查看表结构。  
   便于写出正确字段与条件的 SQL。

4. **执行 SQL**  
   - **只读**（SELECT）：用 `mcp_mysql_execute_query`，传入 `query` 与 `connection_id`。  
   - **写操作**（INSERT/UPDATE/DELETE）：用 `mcp_mysql_execute_write`，传入 `query` 与 `connection_id`。

5. **结果与安全**  
   - 将查询/写入结果清晰呈现给用户。  
   - 写操作前确认影响范围（如 WHERE 条件、影响行数），避免误删/误改；必要时先 SELECT 再写。

## 输出习惯

- 给出可直接执行的 SQL（可先展示，再说明已通过 MCP 执行或待用户确认后执行）。  
- 若执行了 MCP：简要说明用了哪个连接、查了哪些表、结果是行数或样例数据。  
- 涉及多库时，标明每条 SQL 对应的库/连接。

## 目录与文件书写

- **每月使用新目录**：书写、保存 SQL 或相关事务文件时，必须按**月份**使用独立目录，不得写入上月或旧月目录。
- **目录命名**：`年份+月`，例如 `2026年2月`、`2026年3月`。可在月目录下再按业务分子目录（如 `框架协议`、`直采商城`）。
- **示例路径**：`2026年2月/框架协议/xxx.sql`、`2026年2月/直采商城/xxx.sql`。新建或追加 SQL 文件时，优先放在当前月份的对应目录下。

## 注意事项

- 不臆造表名或字段：不确定时先用 `list_tables` / `describe_table` 再写 SQL。  
- 写操作前明确告知为 INSERT/UPDATE/DELETE 及影响范围，谨慎执行。
