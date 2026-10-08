---
name: sdd-openspec-integration
description: "SDD + OpenSpec 集成：在 SDD 严格治理框架下使用 OpenSpec 轻量级增量演进"
version: "1.0"
author: "SDD Architecture Team"
license: "MIT"
tags: ["sdd", "openspec", "integration", "governance", "incremental"]
related_skills: ["sdd-spec", "sdd-plan", "sdd-tasks", "sdd-code"]
---

# SDD + OpenSpec 集成技能

> **版本：** 1.0
> **用途：** 在 SDD 严格治理框架下，集成 OpenSpec 的轻量级增量演进方法，实现灵活性与规范性的平衡。

## 何时使用

使用此技能当：
- 需要在严格业务治理下进行快速技术迭代
- 项目既有 SDD 规格文档，又希望使用 OpenSpec 的 AI 协作能力
- 需要平衡业务规则的严格性和技术实现的灵活性
- 团队同时使用 SDD 和 OpenSpec 工具链

## 核心原则

### 1. 双层治理模式
- **SDD 层**：负责业务规格的严格治理、批准规则和追溯关系
- **OpenSpec 层**：负责技术实现的增量演进、变更管理和 AI 协作

### 2. 集成边界
- SDD 的 `spec.md` 作为 OpenSpec 的输入源
- OpenSpec 的变更提案必须经过 SDD 的批准流程
- 两者共享同一个 `constitution.md` 和 `AGENTS.md`

## 工作流程

### Phase 1: SDD 规格设计（严格治理）
```markdown
1. 使用 sdd-spec 生成完整的 spec.md
2. 应用 SDD 的 9 条批准规则
3. 建立 OBJ-* → SCN-* → REQ-* → AC-* 的完整追溯链
4. 生成业务约束矩阵组（7张）
5. 标记为"已批准"状态
```

### Phase 2: OpenSpec 增量实现（灵活演进）
```markdown
1. 将 SDD 的 spec.md 映射到 OpenSpec 的 specs/ 目录
2. 使用 /opsx:propose 创建增量变更
3. 在 changes/ 目录中进行技术实现
4. 使用 /opsx:apply 实现变更
5. 使用 /opsx:archive 归档并更新主规格
```

### Phase 3: Git 分支集成（代码实现）
```markdown
1. 为每个 OpenSpec change 创建对应的 Git 分支
2. 分支命名规范：feature/change-name 或 fix/change-name
3. 根据 OpenSpec 的 tasks.md 逐项实现代码
4. 实现完成后合并到主分支
5. 归档 OpenSpec change 并清理 Git 分支
```

## 关键决策点

### 1. 规格映射策略
```markdown
SDD spec.md → OpenSpec specs/[capability]/spec.md

映射规则：
- OBJ-* → 业务背景和目标
- SCN-* → 核心场景描述
- REQ-* → 功能需求
- AC-* → 验收标准
- INV-* → 业务不变量
- NFR-* → 非功能需求
```

### 3. 变更分类处理
```markdown
变更类型 | SDD 处理 | OpenSpec 处理 | Git 分支策略 | 适用场景
--------|----------|---------------|-------------|--------
业务变更 | 需要重新批准 spec | 重新生成完整的变更包 | 独立功能分支 | 新业务功能、复杂需求
技术优化 | 无需重新批准 spec | 增量技术改进 | 快速分支/特性分支 | 性能优化、重构、代码质量
缺陷修复 | 无需重新批准 spec | 针对性修复 | hotfix 分支 | Bug 修复、紧急问题
```

### 4. 分支与 Change 对应关系
```markdown
Change 类型 | Git 分支命名 | 分支生命周期 | 合并策略
------------|---------------|-------------|----------
新功能 | feature/change-name | 创建 → 开发 → 合并 → 删除 | merge --no-ff
Bug 修复 | fix/change-name | 创建 → 开发 → 合并 → 删除 | merge --no-ff
技术优化 | perf/change-name | 创建 → 开发 → 合并 → 删除 | squash merge
紧急修复 | hotfix/change-name | 创建 → 开发 → 合并 → 删除 | merge --no-ff
```

### 3. 批准流程集成
```markdown
1. OpenSpec 变更提案必须关联 SDD 的 REQ-* 和 AC-*
2. 技术实现前，需要 SDD 的架构评审
3. 实现后，需要 SDD 的验收测试验证
4. 归档时，同步更新 SDD 的追溯关系
```

## 实施指南

### 1. 项目初始化
```bash
# 1. 初始化 SDD 项目
sdd init

# 2. 初始化 OpenSpec
openspec init

# 3. 创建集成配置
mkdir -p openspec/integration
cat > openspec/integration/sdd-mapping.json << EOF
{
  "specs_dir": "openspec/specs",
  "changes_dir": "openspec/changes",
  "archive_dir": "openspec/archive",
  "constitution": "constitution.md",
  "agents": "AGENTS.md"
}
EOF

# 4. 设置 Git 分支策略
git config branch.feature.rebase true
git config branch.fix.rebase true
git config branch.hotfix.rebase true
```

### 2. 规格映射
```bash
# 将 SDD 的 spec.md 映射到 OpenSpec
sdd-openspec-mapping spec.md openspec/specs/capability/spec.md

# 验证映射完整性
sdd-openspec-validate-mapping openspec/specs/capability/spec.md
```

### 3. 变更管理
```bash
# 创建变更提案
/opsx:propose "技术优化：数据库查询性能提升"

# 关联 SDD 需求
echo "关联 REQ-001: 数据查询响应时间 < 200ms" >> openspec/changes/performance-improvement/proposal.md

# 创建对应的 Git 分支
git checkout -b perf/database-query-optimization

# 实现变更
/opsx:apply

# 归档并更新 SDD 追溯
/opsx:archive --update-sdd-trace

# 合并到主分支
git checkout main
git merge --no-ff perf/database-query-optimization
git branch -d perf/database-query-optimization
```

## 质量保证

### 1. 追溯关系维护
```markdown
每个 OpenSpec 变更必须：
- 关联至少一个 SDD 的 REQ-*
- 更新相关的 AC-* 验收标准
- 维护 INV-* 业务不变量
- 更新 NFR-* 非功能需求指标
```

### 2. 变更影响分析
```bash
# 分析变更对业务规则的影响
sdd-openspec-impact-analysis openspec/changes/[change-name]

# 验证业务规则一致性
sdd-openspec-rule-check openspec/specs/[capability]/spec.md
```

### 3. 验收标准验证
```markdown
OpenSpec 实现必须通过：
- SDD 的验收测试（基于 AC-*）
- OpenSpec 的集成测试
- 业务规则冲突检测
```

## 最佳实践

### 1. 变更规模控制
- 单个 OpenSpec 变更应限制在 1-2 个 REQ-* 范围内
- 技术优化变更不应影响业务逻辑
- 缺陷修复变更必须包含回归测试

### 2. 文档同步
- OpenSpec 变更后，及时更新 SDD 的追溯关系
- 保持 specs/ 目录与 spec.md 的一致性
- 维护 changes/ 和 archive/ 目录的清晰结构

### 3. AI 协作规范
- 使用 OpenSpec 的 /opsx:explore 进行技术探索
- 使用 SDD 的 sdd-spec 进行业务澄清
- 两者结合使用，确保技术实现符合业务需求

## 风险控制

### 1. 业务规则保护
```markdown
禁止行为：
- OpenSpec 变更违反 SDD 的业务不变量
- 技术实现降低验收标准
- 绕过 SDD 的批准流程
- Git 分支直接修改已批准的规格文件
```

### 2. 追溯关系完整性
```markdown
强制检查：
- 每个 REQ-* 至少关联一个 AC-*
- 每个 SCN-* 至少关联一个 REQ-* 和 AC-*
- 变更前后追溯关系保持一致
- Git 提交信息必须关联对应的 OpenSpec change
```

### 3. 分支管理风险
```markdown
分支管理规则：
- 每个OpenSpec change必须创建对应的Git分支
- 分支命名必须遵循规范：feature/xxx、fix/xxx、perf/xxx、hotfix/xxx
- 开发分支必须基于最新的main分支创建
- 完成后必须及时清理分支，避免僵尸分支
- 紧急修复必须使用hotfix分支，避免污染开发流程
```

### 4. 版本管理
```markdown
版本控制：
- SDD 的 spec.md 使用语义化版本
- OpenSpec 的变更使用时间戳+功能描述
- 归档时保留完整的变更历史
- Git 分支合并时保持提交历史的清晰性
```

## 配置选项

### 1. 集成级别
```bash
# 严格模式：所有变更都需要 SDD 批准
openspec config set integration-mode strict

# 宽松模式：技术优化变更可快速通过
openspec config set integration-mode lenient

# 混合模式：业务变更严格，技术变更宽松
openspec config set integration-mode hybrid
```

### 2. 自动化级别
```bash
# 全自动：变更自动映射和追溯
openspec config set automation-level full

# 半自动：需要人工确认关键步骤
openspec config set automation-level partial

# 手动：所有步骤都需要人工确认
openspec config set automation-level manual
```

## 故障排除

### 1. 映射失败
```bash
# 检查映射完整性
sdd-openspec-mapping-validate

# 修复映射关系
sdd-openspec-mapping-repair
```

### 2. 追溯关系断裂
```bash
# 检查追溯关系
sdd-openspec-trace-check

# 修复追溯关系
sdd-openspec-trace-repair
```

### 3. 业务规则冲突
```bash
# 检测业务规则冲突
sdd-openspec-rule-conflict

# 解决冲突
sdd-openspec-rule-resolve
```

## 配套工具

### 1. 映射工具
- `sdd-openspec-mapping`: 规格映射工具
- `sdd-openspec-validate`: 映射验证工具
- `sdd-openspec-sync`: 同步工具

### 2. 分析工具
- `sdd-openspec-impact`: 影响分析工具
- `sdd-openspec-trace`: 追溯关系工具
- `sdd-openspec-rule`: 业务规则工具

### 3. 质量工具
- `sdd-openspec-quality`: 质量检查工具
- `sdd-openspec-test`: 验收测试工具
- `sdd-openspec-audit`: 审计工具

## 总结

SDD + OpenSpec 集成技能提供了在严格治理框架下实现灵活演进的方法：

- **保持 SDD 的严格治理**：业务规格、批准规则、追溯关系
- **引入 OpenSpec 的灵活性**：增量演进、AI 协作、快速迭代
- **双层质量保证**：业务规则和技术实现的双重验证
- **完整的追溯链条**：从需求到实现的全链路追溯

通过这种集成，用户可以在保证软件质量的同时，享受现代开发工具带来的效率和灵活性。