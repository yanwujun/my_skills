# Skills 仓库

个人沉淀的 Hermes Agent / Cursor Skill 集合，按**公司**和**个人**分类。

## 结构

```
├── work/                 # 🔒 公司/工作相关
│   ├── cursor-sdd/       #   Cursor + SDD 方法论 skills
│   ├── ai-audit-regression/       # 框架协议智能审核
│   ├── direct-purchase-*/         # 直采商城部署/SQL
│   ├── framework-contract-sql/    # 框架协议SQL
│   ├── supply-chain-push/         # 供应链商品推送
│   ├── government-procurement-ops/ # 政府采购运维
│   ├── java-*/                    # Java 企业开发
│   ├── springboot-*/              # Spring Boot 模式
│   ├── jpa-patterns/              # JPA 最佳实践
│   ├── business-rule-graph/       # 业务规则知识图谱
│   ├── code-quality/              # 代码质量
│   ├── database-migrations/       # 数据库迁移
│   ├── wsl-*/                     # WSL 开发环境
│   ├── proxy-*/                   # 代理/网络调试
│   └── hermes-*/                  # Hermes 运维
│
├── personal/             # 🏠 个人/学习相关
│   ├── ai-weekly-video/           # AI 周报视频生成
│   ├── bilibili-*/                # B站相关
│   ├── novel-writer/              # 小说创作
│   ├── comic-manga-creation/      # 漫画改编
│   ├── *-tutor/                   # 各类通识辅导
│   ├── ruankao-*/                 # 软考辅导
│   ├── english-*/                 # 计算机英语
│   ├── coding-agents/             # AI 编程 Agent
│   ├── custom-mcp-servers/        # 自定义 MCP Server
│   ├── sdd-architect/             # SDD 架构方法论
│   ├── dws/                       # 钉钉工作空间
│   ├── minecraft-modpack-server/  # MC 服务器
│   └── ...                        # 更多
│
├── README.md
└── .gitignore
```

## Skill 格式

每个 skill 是一个目录，内含 `SKILL.md`：

```markdown
---
name: my-skill
description: 简短描述
category: devops
---

# My Skill

## 触发条件
...

## 步骤
1. ...
```

## 使用方式

将 skill 目录复制或符号链接到 Hermes / Cursor 的 skills 目录即可。

```bash
# Hermes
cp -r work/my-skill ~/.hermes/skills/

# Cursor (Windows)
cp -r work/cursor-sdd/my-skill /mnt/c/Users/.../Cursor/User/rules/
```
