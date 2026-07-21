---
name: business-rule-graph
description: 基于 roam-code 改造的业务规则知识图谱项目。双引擎架构：AST 确定性引擎提取规则参数，LLM 语义引擎生成业务描述。从 Java 代码提取业务规则（if-throw/状态判断/方法命名/注解），构建图谱，检测冲突。支持 SVN。
---

# Business Rule Graph

**项目地址:** https://github.com/yanwujun/business-rule-graph (public)
**本地:** /home/administrator/business-rule-graph
**基座:** roam-code (Cranot/roam-code, Apache 2.0)

## 触发条件

- "业务规则图谱" / "business rule graph" / "规则冲突检测"
- 对 business-rule-graph 项目代码的修改或讨论
- 讨论代码结构图 vs 业务规则图的区别

## 核心架构：双引擎

```
AST 确定性引擎 (extractor.py)      LLM 语义引擎 (summarizer.py)
─────────────────────────────      ─────────────────────────────
✅ tree-sitter 扫 if-throw         ✅ domain 语义分类
✅ 状态判断提取 (if getStatus)     ✅ flow 业务流程命名
✅ 枚举提取 (enum XxxStatus)       ✅ description 自然语言生成
✅ 方法命名约定匹配                 ✅ 语义归并（同规则不同写法→合并）
✅ 注解兜底                         ✅ 冲突描述生成
❌ 不调用 LLM                       ❌ 不提取参数（参数由 AST 确定）
```

**关键原则（用户纠正）：没有 LLM 不能对业务做总结。** AST 拿到的是代码事实，变不成业务语言。LLM 是内置核心，不是可选增强。

## 提取优先级（政府采购系统适配）

政府采购代码少用 Spring 注解，规则在 `if + throw` 和状态判断中：

```
优先级 1: tree-sitter 流程/判断节点（主力）
  ├── if (condition) throw new XxxException("消息")
  ├── if (x.getStatus() == OrderStatus.DRAFT)
  ├── switch (status) { case ... }
  ├── enum XxxStatus { DRAFT, SUBMITTED, ... }
  ├── throw new XxxException(...) — 独立 throw
  └── try { ... } catch (XxxException e) { ... }

优先级 2: 方法命名约定
  ├── workflow: setStatus, submit, approve, audit, review
  ├── validation: validate, check, assert, verify
  ├── data_integrity: existsBy, countBy, selectBy, findBy
  ├── calculation: calculate, compute, getDiscount, getTax
  └── process: on*, handle*, sync, push

优先级 3: 注解（兜底 + MyBatis/Redis/Spring增强）
  └── @NotNull, @Min, @Max, @PreAuthorize, @Transactional
  └── @Cacheable, @CacheEvict, @CachePut (Spring Cache)
  └── @Select, @Insert, @Update, @Delete (MyBatis)
  └── @ConfigurationProperties, @Scheduled, @Async
  └── @Retryable, @CircuitBreaker

优先级 4: MyBatis Mapper + Redis 关键词
  ├── Mapper方法: insertBatch, updateBatchById, selectByPrimaryKey...
  ├── Redis关键词: RedisLock, redisTemplate, setIfAbsent, tryLock...
  └── @Table, @Column  ORM映射
```

## 模块结构

```
src/roam/business_rules/        10个模块, 1500+行
├── models.py         RuleType 8种枚举 + BusinessRule dataclass
├── patterns.py       四级提取 (tree-sitter > 方法命名 > 注解 > MyBatis/Redis)
├── extractor.py      AST 确定性引擎
├── summarizer.py     LLM 语义引擎
├── loader.py         共享数据加载器
├── graph.py          规则图谱 (same_field/same_flow/conflicts_with/related)
├── conflict.py       冲突检测 (阈值冲突/权限移除/状态机断裂)
├── snapshot.py       规则版本快照 + diff
├── html_report.py    HTML可视化报告 (自包含,零外部依赖)
└── commands/cmd_br_extract.py  8个CLI命令

改动文件:
  src/roam/db/schema.py     4张新表 (business_rules/code_edges/edges/snapshots)
  src/roam/cli.py           8个命令注册
  src/roam/mcp_server.py    6个MCP工具 + _WORKFLOW_TOOLS预设组
```

## CLI 命令

```bash
roam business-rules extract              # AST 提取规则
roam business-rules extract --update     # 增量提取
roam business-rules summarize            # LLM 语义增强
roam business-rules graph                # 构建图谱
roam business-rules graph --stats        # 图谱统计
roam business-rules check                # 冲突检测
roam business-rules check --snapshot-id N
roam business-rules diff                 # 快照对比
roam business-rules snapshot --label "基线"
roam business-rules list                 # 列出规则(--type/--domain筛选)
roam business-rules explain <rule-id>    # 单条规则详情+关联规则
```

## SSH 配置

WSL SSH to GitHub 需要 HTTP 代理隧道：
```
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github
    IdentitiesOnly yes
    ProxyCommand nc -X connect -x 127.0.0.1:8888 %h %p
```

## 开发约定

- **Git 提交日志用中文**，格式: `类型: 简述`
- 类型: feat/fix/docs/chore/refactor
- 示例: `feat: MCP工具注册 — 6个业务规则工具加入工作流预设`

## 冲突检测类型

| 类型 | 检测方式 | 严重度 |
|------|----------|--------|
| 阈值不一致 | 同字段同操作符不同阈值 | CRITICAL |
| 权限移除 | 快照对比发现 AUTHORIZATION 规则减少 | HIGH |
| 状态机断裂 | WORKFLOW 规则转移图中死端/不可达状态 | MEDIUM |

## 已知坑点

1. **extract 会清表重建** — `business-rules extract` 执行 `DELETE FROM business_rules`，之后 conflict 的 `_auth_removed` 查不到被删规则。必须从快照的 `removed_rules` + 上一快照 `added_rules` 交叉查找。
2. **graph._detect_conflicts 需跨类型** — 不能只查 validation，要按 `params.field/value` 跨所有类型分组比对。
3. **用户纠正：没有 LLM 不能做业务总结** — AST 拿到代码事实（`if(total<100) throw`），变不成业务语言（"订单金额不低于100元"）。LLM 是内置核心，不是可选增强。
4. **政府采购代码少用注解** — 规则在 `if + throw` 和状态判断中，tree-sitter 查询必须排最高优先级。
5. **CLI 命令必须懒加载 import（CI 崩溃教训）** — 详见 `references/roam-code-integration.md`。

## 参考文件

- `references/code-graph-tool-comparison.md` — roam-code vs Graphify vs SocratiCode 选型对比
- `references/roam-code-integration.md` — CLI/MCP/DB注册模式 + 踩坑记录

## Milestone 状态

- M1: 规则提取 ✅
- M2: 图谱+冲突 ✅
- M3: 快照+MCP ✅
- 优化: list/explain/deadend ✅
- M4: MyBatis/Redis/HTML报告 ✅
- 待验证: P2040 项目实际跑通

## 变更检测（SVN 支持）

roam-code 基于文件 mtime 检测变更，不依赖 git。SVN 项目直接可用。快照用 `--label` 替代 git commit。
