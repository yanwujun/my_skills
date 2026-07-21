# Skill 审计工作流

用 writing-great-skills 规范审计现有 skill 的实战流程。

## 步骤

### 1. 确定范围

先确认审计哪些 skill。skill 多时（100+）按类别分批：
- 问用户"先审哪类？"提供分类选项
- 优先审经常使用的 skill（用 session_search 查调用频率）
- 一次审计控制在 7-15 个，避免 context 溢出

### 2. 批量加载

用 `skill_view(name)` 并行加载所有目标 skill。7 个以内一次调用，更多分批。

### 3. 逐项审查

对照 writing-great-skills 的 7 个维度：

| 维度 | 检查点 |
|------|--------|
| Invocation | `disable-model-invocation` 设置是否合理 |
| Description | 前置 leading word？触发词裁掉实现细节？ |
| Hierarchy | 步骤有完成标准？reference 用 context pointer？ |
| Pruning | 有无重复？no-op？Negation？ |
| Leading words | 是否用了预训练紧凑概念？ |
| Split | 是否该拆分（独立 leading word / premature completion）？ |

### 4. 跨 skill 检查

不只看单个 skill，还要检查跨 skill 问题：
- **Duplication** — 同一段内容出现在多个 skill 中
- **Single source of truth** — 改一个事实需改多个地方
- **Overlap** — 两个 skill 功能高度重叠

### 5. 分级修复

| 优先级 | 标准 | 操作 |
|:--:|------|------|
| P0 | 重复/单源违反/膨胀严重 | 重构或拆分 |
| P1 | 沉积/描述含实现细节 | 裁剪/重写 |
| P2 | 轻微冗余 | patch 小修 |

### 6. 报告格式

```markdown
| Skill | 状态 | 主要问题 |
|-------|:----:|------|
| xxx | ✅/⚠️/❌ | 具体问题描述 |
```

## 踩坑

- **跨系统 skill 不算重复**：用户说"两个系统"时，各自保留
- **swagger-mysql-api-test 式膨胀**：认证内容在 §0.4/§2.4.7/§4.1.1 出现 3 次 → 合并到一处，其余改为指针
- **修正后验证**：用 skill_view 重新加载确认修复生效
- **不要删了又补**：patch 前确认要替换的是唯一块，避免误删其他部分
