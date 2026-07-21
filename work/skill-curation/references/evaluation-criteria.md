# 归集 Skill 评估标准与已评估清单

## 评估维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 技术栈匹配 | 高 | 用户的核心技术栈（Java/Spring/MyBatis/SQL） |
| 语言 | 中 | 中文优先（ECC的docs/zh-CN/下有中文版） |
| Skill数量 | 中 | 单仓库skill越多，覆盖面越广 |
| 实用性 | 高 | 工程实践 > 理论规范 > 集合/目录类 |
| 去重 | 必须 | 同一skill的多个fork只保留最佳版本 |

## 已安装到 Hermes 的 10 个 Skill（2026-06-24）

来源: `/mnt/d/平时处理文件/skills/collected/`

| Skill | 来源仓库 | 语言 | 安装理由 |
|-------|---------|------|---------|
| springboot-patterns | affaan-m_ECC/zh-CN | 中文 | Spring Boot架构核心 |
| springboot-security | affaan-m_ECC/zh-CN | 中文 | 认证授权/CSRF/限流 |
| jpa-patterns | affaan-m_ECC/zh-CN | 中文 | JPA/Hibernate实体/查询/事务 |
| java-coding-standards | affaan-m_ECC/zh-CN | 中文 | Java编码规范 |
| database-migrations | affaan-m_ECC/zh-CN | 中文 | 数据库迁移/零停机/回滚 |
| api-design | affaan-m_ECC/en | 英文 | REST API设计模式 |
| tdd-workflow | affaan-m_ECC/en | 英文 | TDD工作流 |
| diagnosing-bugs | mattpocock_skills | 英文 | Bug诊断循环 |
| systematic-debugging | cjbpq_deep-reviewer-seek | 英文 | 假设驱动调试 |
| karpathy-guidelines | multica-ai_andrej-karpathy-skills | 英文 | LLM编码避坑 |

## 仓库质量排名（按Hermes兼容skill数）

| 仓库 | 兼容skill数 | 质量评价 |
|------|------------|---------|
| affaan-m_ECC | 782 | 极高，覆盖全栈+多语言版本 |
| materialofair_oh-my-codex | 100 | 高，Codex生态，中文skill多 |
| ThibautBaissac_rails_ai | 51 | 高，Rails专用 |
| miyago9267_dev-discipline | 17 | 中高，开发纪律/SDD/TDD |
| SallMarta_eye-hate-agent | 11 | 中，SDD专家角色 |
| cnfjlhj_ai-collab-playbook | 10 | 中，中文AI协作手册 |
| mattpocock_skills | 2 | 精，工程实战(原版) |
| JuliusBrussee_caveman | 4 | 精，Git操作 |

## 已知 Fork 去重表

| 原版 | Fork | 处理 |
|------|------|------|
| mattpocock_skills | KentwareDemo_mattpocock-skills | 跳过 |
| mattpocock_skills | amazingloft999-droid_mattpocock-skills | 跳过 |
| mattpocock_skills | lucascorrea97_skills | 跳过 |
| mattpocock_skills | WenWuZhiDao_mattpocock-skills-zh | 中文版可选用 |
| mattpocock_skills | pencil20388-eng_stop-slop-zh | 不同skill，保留 |
