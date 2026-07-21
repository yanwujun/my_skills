---
name: government-procurement-ops
description: "政府采购系统运维（直采商城+框架协议）— 线上问题记录、测试环境配置、需求管理、发布工作流。SQL 查询请加载 direct-purchase-sql 或 framework-contract-sql。"
version: 2.0.0
author: hermes
license: MIT
metadata:
  hermes:
    tags: [政府采购, 直采商城, 框架协议, 运维, 智采商城, 行采家]
    related_skills: [direct-purchase-sql, framework-contract-sql, direct-purchase-deploy]
---

# 政府采购系统运维

运维总入口——线上问题记录、测试环境、需求管理、发布流程。具体 SQL 查询请加载 [direct-purchase-sql](direct-purchase-sql) 或 [framework-contract-sql](framework-contract-sql)。

## 通用配置

### 数据库连接

| 项目 | 值 |
|------|-----|
| show1 主机 / 端口 | 192.168.2.37 / 31004 |
| test3 主机 / 端口 | 192.168.2.2 / 31004 |
| 用户 | root |
| 密码 | mysql |

**MCP MySQL 连接：**

| connection_id | host | database | 环境 |
|---|---|---|---|
| `default` | 192.168.2.37 | xcj_mall_base | show1 |
| `ezc` | 192.168.2.37 | ezc | show1 |
| `trade` | 192.168.2.37 | trade | show1 |
| `stddata` | 192.168.2.37 | stddata | show1 |
| `test3` | 192.168.2.2 | test3 | test3 |

### 数据库访问规则

| 环境 | 允许 | 禁止 | 原因 |
|------|------|------|------|
| show1 / test3 | MCP MySQL 工具 | terminal pymysql 直连 | MCP 天然禁止 DDL |

### 注意事项（通用）

1. **DML 前必先备份到 test 库**，SELECT 确认影响范围
2. 跨库注意库前缀：`xcj_mall_base.TG_Goods` vs `trade.TB_B_StockDir` vs `ezc.project`
3. 递归 CTE 需 MySQL 8.0+
4. `trade.TF_Orders` 和 `xcj_mall_base.order_contract` 是两个库，关联注意库前缀
5. **SQL 文件保存规范** → 见 [direct-purchase-sql](direct-purchase-sql) 或 [framework-contract-sql](framework-contract-sql) 的 "📁 SQL文件保存约定" 章节

---

## 第1章：线上问题记录

### 直采商城问题记录

主记录文件：`/mnt/d/平时处理文件/直采商城-线上问题记录.md`

```markdown
### [问题编号] YYYY-MM-DD 问题简述

**发现时间**：YYYY-MM-DD HH:mm
**发现人**：
**影响范围**：□ 全部用户  □ 部分用户  □ 仅后台管理
**严重程度**：□ P0(紧急)  □ P1(严重)  □ P2(一般)  □ P3(轻微)

#### 问题现象
描述用户看到什么、报什么错。

#### 根因分析
数据库层面/代码层面/配置层面的直接原因。

#### 处理过程
1. 第一步（时间）：操作内容
2. 第二步（时间）：操作内容

#### 验证确认
处理后的验证结果，用户确认情况。

#### 预防措施
- 改进点1
- 改进点2
```

### 框架协议问题记录

主记录文件：`/mnt/d/平时处理文件/框架协议-线上问题记录.md`，格式同上。

---

## 第2章：测试环境配置

| 项目 | 值 |
|------|-----|
| 前端 | https://zc-mall.xcjshow1.gm |
| 网关 | https://www.xcjshow1.gm/xcj-gateway |
| 登录 | https://www.xcjshow1.gm/login-app/login |
| Swagger (本地) | http://127.0.0.1:25325/xcjmallbase/doc.html |
| 供应商凭证 | ssss / GmsoftTest_1997 / 111111 |
| 平台凭证 | admin / GmsoftTest_1997 / 111111 |
| ZGC OAuth | zcsc_zdzs:123456 (base64) |

详细配置见 `references/test-env-config.md`。

---

## 第3章：需求管理与升级文档

### 需求分析分类

1. **按类型**：A功能缺失 > C优化提升 > B交易规则 > 系统异常
2. **按功能模块**：统计 Top N，识别热点
3. **按状态**：待开发/已完成/已关闭
4. **按优先级**：高→中→低

### 外包任务拆分

| 可直接外包 | 需定义接口后外包 | 不可外包 |
|-----------|-----------------|---------|
| 纯后端 CRUD、第三方对接、报表导出、Bug 修复 | 权限控制、审核流程、状态流转（需先给接口规范） | 核心架构、核心业务流程、交易逻辑 |

### 升级说明文档

版本管理根目录：`/mnt/d/项目/svn/P2040直采与框架协议/版本管理/`

规范要点：
- 每模块拆为"后端需求"+"前端需求"两子节
- 后端聚焦：API入参、鉴权、业务规则、数据变更、状态流转
- 前端聚焦：页面位置、UI组件、交互流程、角色区分
- 状态流转用 → 箭头，业务规则用编号列表
- 删除多余空行，节间用 `---` 分隔

详细模板见 `references/version-planning-editor.md`。

---

## 第4章：AI 审核 Skill 测试

完整测试指南见 [ai-audit-regression](ai-audit-regression) skill。

**速查流程：**

1. 从 XML/JSON 解析数据
2. 提取 `detailImageUrls`，拼完整外网 URL
3. 创建线程 → 图片以 `image_url` 块嵌入 → `POST /runs/wait`
4. 解析结果（去 Markdown 围栏 → JSON → auditResult）
5. 归一化（PASS/FAIL → 1/0）
6. 生成报告（含逐条明细和会话链接）

---

## 第5章：发布工作流

完整流程见 [direct-purchase-deploy](direct-purchase-deploy) skill。

**速查命令：**

```bash
# 1. 发布 lib
cmd.exe /c 'chcp 65001 >nul && D: && cd D:\\项目\\svn\\P2040直采与框架协议\\C2服务网关\\直采商城\\pub\\branches\\current\\lib && call release.bat'

# 2. 发布 weblib（等步骤1完成后）
cmd.exe /c 'chcp 65001 >nul && D: && cd D:\\项目\\svn\\P2040直采与框架协议\\C2服务网关\\直采商城\\pub\\branches\\current\\weblib && call release.bat'

# 3. 发布模块 — cr 模式（仅打包）
cmd.exe /c 'chcp 65001 >nul && echo current,test3,xcj,cr,trade > %temp%\\pub_params.txt && D: && cd D:\\项目\\svn\\P2040直采与框架协议\\C2服务网关\\直采商城\\ZCtrlCenter && call script\\发布程序到指定环境.bat %temp%\\pub_params.txt'
```

---

## SQL 查询入口

本 skill **不再内联 SQL 模板**。需要查询时，按领域加载对应 skill：

| 领域 | 加载 | 库范围 |
|------|------|--------|
| 直采商城商品/供应商/协议/订单 | `direct-purchase-sql` | xcj_mall_base + stddata |
| 框架协议征集/商品/导购/成交 | `framework-contract-sql` | ezc + trade |
| 供应链商品推送 | `supply-chain-push` | API 调用 |
| AI 审核回归测试 | `ai-audit-regression` | agents-platform API |

## References

- `references/test-env-config.md` — 测试环境配置详情
- `references/version-planning-editor.md` — 版本规划编辑指南
- `references/publish-workflow.md` — 发布工作流详情
- `references/sync-guide-dir.md` — 导购目录同步
