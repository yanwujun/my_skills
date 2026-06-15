---
name: skill-template
description: Skill 编写模板和规范
category: productivity
---

# Skill 编写模板

## 触发条件
- 新发现一个可复用的工作流（5步以上或有踩坑点）
- 某个流程被用户修正或补充过
- 用户说"记住这个做法"

## 标准结构

### YAML 前置元数据

```yaml
---
name: skill-name       # 小写+连字符，唯一
description: 一句话描述
category: devops       # 所属分类目录
---
```

### 正文内容

```markdown
# Skill 名称

## 触发条件
什么场景下应该加载这个 skill

## 步骤
1. 第一步：具体命令或操作
2. 第二步：...
   ```bash
   # 附上完整命令
   ```
3. 第三步：验证方法

## 验证
如何确认操作成功

## 注意事项 / 踩坑记录
- 已知问题
- 环境依赖
- 备选方案
```
