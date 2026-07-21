---
name: java-debug-checklist
description: >-
  高频 Java/Spring 调试清单。用户说"为什么没生效"/"还是不行"/"有问题"时优先对照此清单排查。
  覆盖：MyBatis排序、Solr查询、iframe交互、Feign扫描、事务代理、平台隔离。
---

# Java 调试清单（用户高频踩坑）

当用户反馈"没生效"、"还是不行"、"有问题"时，先过此清单再深入排查。

## 1. MyBatis 排序不生效

- **症状**: XML 有 ORDER BY，但查询结果顺序不对。
- **原因**: Java 层（`Page.orders()` / `result.setOrders()`）覆盖了 XML 排序。
- **排查**: 打断点检查 Page/result 的 orders 属性，去掉 Java 层默认排序。

## 2. MyBatis 写入 null 失败

- **症状**: `updateById(entity)` 后 DB 字段保留旧值。
- **原因**: MyBatis-Plus 默认 `FieldStrategy.NOT_NULL`，null 字段不生成 SET。
- **修法**: 用 `LambdaUpdateWrapper.set(Entity::getField, null)` 显式置空。

## 3. MyBatis foreach 空集合报错

- **症状**: 传入空 List 时报 SQL 语法错误。
- **原因**: `<foreach collection="list">` 空集合生成异常 SQL。
- **修法**: 加 `@Param("list")` 并在调用前判空，或 XML 加 `<if test="list != null and list.size() > 0">`。

## 4. Spring 事务同类调用不生效

- **症状**: 同类中 A 方法调 B 方法，B 的 `@Transactional` 无效。
- **原因**: Spring AOP 代理机制，`this.method()` 绕过代理。
- **修法**: 注入自身 `@Autowired private XxxService self`，用 `self.method()`。

## 5. Feign Client 扫描不到

- **症状**: 新模块的 `@FeignClient` 报 No bean found。
- **原因**: `@EnableFeignClients(basePackages)` 未覆盖新包路径。
- **排查**: 检查启动类 `@EnableFeignClients` 的 `basePackages` 配置。

## 6. Solr 负条件 OR 组合

- **症状**: `(-a:[* TO *]) OR (-b:[* TO *])` 无结果，单独条件有。
- **原因**: Solr 对 OR 组合负条件的解析与直觉不同。
- **修法**: 负条件组合用 `fq` 分离；确认 Solr 版本行为。

## 7. iframe 内 fixed 定位失效

- **症状**: iframe 内 `position: fixed` 元素不浮动到父页。
- **原因**: fixed 相对 iframe 视口，非父窗口。iframe 无法感知父窗口滚动。
- **修法**: 用 `window.parent.document` 或 `postMessage` 跨窗口通信。

## 8. 平台数据串了（跨环境）

- **症状**: test3 环境查到 show1 的数据。
- **原因**: SQL 缺少 `occurPlatCode` / `platDomain` 过滤。
- **排查**: 所有跨库查询检查是否有平台隔离条件。

## 9. Maven 多模块依赖

- **症状**: 新模块编译/运行找不到依赖类。
- **排查**: 确认父 pom `<module>` 包含新模块；`mvn install` 安装到本地仓库。

## 10. Stream 排序 NPE

- **症状**: `Comparator.comparing(Entity::getX)` NPE。
- **原因**: 键提取器返回 null 时 `compareTo` 抛 NPE。
- **修法**: `Comparator.comparing(Entity::getX, Comparator.nullsFirst(naturalOrder()))`。
