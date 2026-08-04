# Spring Boot 编码规范模板（Cursor Rules + Hermes Skill 通用）

可直接复制为 `.cursor/rules/springboot-standards.mdc` 或 `~/.hermes/skills/dev/springboot-standards/SKILL.md`。

```yaml
---
alwaysApply: false
description: Java Spring Boot 编码规范：分层架构、命名约定、Redis分布式锁、MyBatis坑点、异常处理、测试要求
---

# Spring Boot 编码规范

## 分层架构

- Controller: 参数校验 + 路由，不写业务逻辑
- Service: 业务逻辑，接口 + 实现分离
- Mapper: 数据访问，XML 中写 SQL
- 禁止跨层调用（Controller 直接调 Mapper）

## 业务命名

- 代理商 = saleAgent（实体字段/方法名/变量名统一）
- 平台隔离：跨库查询带 occurPlatCode / platDomain

## 分布式锁

- 用 Redis 锁，禁止 JVM 锁（synchronized / ReentrantLock）
- 参考：OrderContractController 锁机制

## MyBatis 约定

- foreach 空集合：必须加 @Param 注解
- updateBatchById：字段策略不清理 null，需置空用 UpdateWrapper.set(column, null)
- 排序在 XML 中完成，不覆写在 Java 层

## Feign 约束

- @EnableFeignClients 的 defaultConfiguration 禁止注册 Feign.Builder
- 自定义配置只放 @FeignClient(configuration = ...) 上

## 异常处理

- 业务异常抛 BusinessException，带错误码
- 禁止 System.out.println，用 Slf4j
- Controller 层统一异常拦截

## 测试

- 改 Service 必写单元测试
- Mock 外部依赖（RPC、MQ、第三方 API）
- 测试覆盖正常路径 + 异常路径

## Git Commit

- 格式：类型:简述（feat/fix/docs/chore/refactor）
- 中文 commit message
```

## 校验清单

Agent 生成代码后自检：

- [ ] 分层正确（Controller→Service→Mapper）
- [ ] 用了 Redis 锁而非 JVM 锁
- [ ] foreach 空集合加了 @Param
- [ ] Feign.Builder 没放在 defaultConfiguration
- [ ] 异常抛的是 BusinessException
- [ ] 有单元测试
- [ ] SQL 路径写到 D 盘
