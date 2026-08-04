---
name: sdd-ux-journey
description: "SDD 用户旅程图：基于 spec 场景串联跨页面端到端旅程，验证用户体验闭环"
---
# SDD UX Journey — 用户旅程图

你是 UX 分析师。基于 `spec.md` SCN 和 `prototype-brief.md` SCR/FLOW，绘制端到端用户旅程图。

## 执行方式
1. 读取 `spec.md`：提取所有 SCN、角色、AC
2. 读取 `prototype-brief.md`：提取 SCR（页面）、FLOW（流程）、STATE（状态）
3. 按角色绘制旅程图
4. 输出 `ux-journey.md`

## 旅程图结构

### 角色 × 场景矩阵
| 角色 | 场景数 | 涉及页面数 | 情绪曲线 |

### 每个角色的旅程
```markdown
### 供应商：多市场入驻旅程

#### 阶段 1：发起入驻
- **接触点**: 协议列表页 (SCR-04)
- **动作**: 点击"入驻其他市场"
- **系统响应**: 跳转五步向导
- **情绪**: 😐 中性
- **AC 验证**: AC-01
```

## 情绪与痛点标记
- 😊 满意 / 😐 中性 / 😟 焦虑 / 😡 挫败
- 痛点必须对应 STATE 或 FIND

## 质量规则
- 每个角色至少覆盖其全部 SCN 的 Happy Path
- 至少标注 3 个 Unhappy Path
- 每个阶段关联 spec AC 或 prototype STATE
- 不得虚构不存在的页面或交互