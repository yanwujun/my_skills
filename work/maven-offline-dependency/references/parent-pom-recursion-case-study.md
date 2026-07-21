# Parent POM 递归解析实战记录

> 来源：2026-05-13 真实项目（xcj-mallbase + malltrade），两个项目的依赖合并到一个本地仓库用于其他项目编译。

## 背景

从 `D:\apache-maven\localRepository3.6.3` 复制两个项目的依赖到目标仓库：

| 来源 | 条目数 |
|---|---|
| `malltrade-dependency-list.txt`（dependency:list 输出） | ~590 行 |
| xcj-mallbase `dependency:tree` 输出 | ~383 行 / 349 个 artifact |
| **去重合并后的初始复制** | **478 个 artifact** |

## 问题

用户发现 `djc-stddata-1.0.2.pom` 不在目标仓库中。这个文件在源仓库存在，但**不在任何依赖清单中**。

## 根因

`dependency:list` 和 `dependency:tree` 只输出 jar 依赖。**父 POM 链永远不会出现在这些输出中**。Maven 编译时却会沿着 `<parent>` 链向上解析，所以所有父 POM 也必须复制。

## 递归解析结果

| 递归轮次 | 新增 parent POM | 说明 |
|---|---|---|
| 第1轮 | 150 (149成功, 1个源不存在) | 直接父 POM |
| 第2轮 | 38 | 祖父 POM 层级 |
| 第3轮 | 9 | 曾祖父 POM 层级 |
| 第4轮 | 2 | 更深层次 |
| 第5轮 | 0 | 链已完整 |

**最终：478 → 676 artifact，+198 个 parent POM（占初始的 41%）**

## BOM import 检查

扫描发现 59 个 BOM import（`<type>pom</type><scope>import</scope>`）：
- 55 个使用了属性占位符（如 `${spring.version}`）→ 源仓库也不存在，这些是 Spring Boot 父 POM 通过 property 继承解析的，**可忽略**
- 4 个有具体版本号且在源仓库存在 → 已补全复制

## 关键数据

- 初始 jar 依赖：478 artifact
- 递归后总 artifact：676 artifact（+41%）
- 总文件数：4,932 个
- 总大小：412.6 MB
- 最终编译通过：✓

## 经验

1. **不要只信任 dependency:list/tree 的输出** — 它只给你 jar 依赖，而 Maven 编译还需要 parent 链的全部 POM。
2. **parent POM 递归是强制步骤** — 本项目需要 5 轮递归才能解析完整，这可能因项目依赖深度而异。
3. **占位符 BOM 可忽略** — `${xxx.version}` 格式的 BOM import 在源仓库也不存在目录，因为它们是通过编译时的 property 继承解析的。只要实际依赖的版本 jar 已经复制了就行。
4. **同一个 artifact 的多个版本都保留** — 如 `djc-stddata` 有 8 个版本在源仓库，但只有 `1.0.2-SNAPSHOT` 和 `1.1.5-SNAPSHOT` 被引用为父 POM。`1.0.2`（release）不被任何依赖链引用，复制它是冗余的（但用户希望的话可以补）。
