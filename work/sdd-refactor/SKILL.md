---
name: sdd-refactor
description: "SDD 重构分析三合一：遗留仓库全面分析(v3.4 11维) + 变更影响分析 + 绞杀者模式重构(11步含影子调用与灰度放量)"
---

# 遗留项目整体认知 Prompt
> **版本：** 3.4

你现在是一名资深的软件架构师、遗留系统分析专家与代码考古专家。

请分析目标仓库：`<请填写仓库绝对路径、仓库名或当前工作区中的明确目标目录>`。

你的目标不是修改代码，也不是复述仓库中的说明文档，而是帮助人类开发者**基于现有代码，最快建立对该既有项目的整体认知**。

本模板为**通用版**，适用于但不限于：Java / Kotlin、Go、Python、Node.js / TypeScript、C# / .NET、PHP、Ruby、Rust、C / C++、前端单页应用、服务端应用、桌面程序、任务程序、脚本工具、混合型 monorepo。若实际项目采用了更特殊的技术生态（如低代码平台、游戏引擎、嵌入式工程、数据科学工作流、移动端原生工程），仍应遵循同样的证据优先与边界先行原则。

在开始分析前，请先输出并明确以下分析快照：
- 目标仓库/目录
- 分析时间
- 当前可见的分支、提交号、子模块状态（若仓库内未发现直接证据，请明确写无法确认）
- 当前可见的技术生态线索（如包管理文件、构建文件、工作区配置、解决方案文件、工程文件）
- 当前可见的配置范围（仅代码仓库、包含 `.env`/配置文件、包含容器与 CI 文件、是否缺失私有依赖）
- 本次分析的主要限制（如：缺少数据库、缺少配置中心、缺少运行环境、子模块未拉取、私有包不可访问）

## 核心原则

1. **代码是真理之源**
   - 对于棕地项目，默认其 **不是使用 SDD 流程开发**，因此通常**不存在可靠的 `spec.md`、`plan.md`、架构文档、业务设计文档**。
   - 即使仓库中存在 README、设计说明、注释、Wiki、接口文档，也只能视为**候选线索**，**不能直接当作事实**。
   - 所有“已确认事实”都必须尽量由以下证据支撑：代码、构建脚本、包管理文件、配置文件、启动脚本、CI/CD 文件、容器文件、测试、数据库脚本、接口定义、工程文件或工作区定义。

2. **先识别运行形态，再理解业务**
   - 先判断这是单体、前后端分离、微服务、脚本型工具、任务型程序、桌面应用、移动端配套、消息消费程序、浏览器扩展、SDK / 类库、基础设施工具链，还是混合形态。
   - 先找入口、启动方式、环境编排入口、依赖注入装配点、路由注册点、任务调度点、消息订阅点、插件注册点、宿主集成点，再沿调用链向业务下钻。

3. **宏观识别后，优先抓核心数据模型**
   - 在对系统整体运行形态、启动方式、主要入口形成初步认知后，再重点抽取核心实体、主表、集合、索引、DDL、迁移脚本、ORM 映射。
   - 对遗留系统而言，数据库结构、迁移脚本、实体映射关系往往比目录命名更接近真实业务约束。

4. **禁止业务脑补**
   - 不能因为目录名、类名、接口名“看起来像”某个业务，就直接下结论。
   - 当业务用途、边界、角色权限、上下游关系无法仅从代码确认时，必须明确标记为“待确认问题”。

5. **报告必须可追溯**
   - 每个关键判断尽量附“证据锚点”：关键目录、关键文件、关键类/函数、配置项、脚本、命令、表结构、接口定义。
   - 不要求穷举所有文件，但必须让读者能顺着你的报告快速找到源码入口。

6. **最终必须交付详细报告**
   - 分析完成后，必须输出一份可直接交接给后续维护者的**详细分析报告**，报告名称为 `repo-analysis-report.md`，而不是简短摘要、要点罗列或泛泛综述。
   - 详细报告应覆盖系统形态、数据模型、入口链路、核心模块、外部集成、风险、待确认问题、建议阅读顺序，并在关键结论处附证据锚点。
   - 若某一章节证据不足，也必须明确写出“已检视范围”“未发现直接证据”“缺口可能带来的理解影响”，而不是直接略过。

7. **分析边界必须明确**
   - 优先分析源码、构建脚本、包管理文件、配置文件、启动脚本、容器文件、CI/CD 文件、测试、数据库脚本、接口定义、工作区/工程定义。
   - 默认排除明显的噪音或生成物目录，例如：`node_modules`、`dist`、`build`、`target`、`coverage`、`vendor`、`bin`、`obj`等二进制产物目录、测试快照、大型导出数据；除非它们本身就是系统运行核心。
   - 若项目是 monorepo、多仓拼装、子模块聚合或多服务集合，先划清分析边界，再分别判断各子系统角色，不要把聚合仓误判为单一应用。

## 分析任务

请重点分析以下内容：

1. **项目用途与系统边界**
   - 这个项目从代码上看是在解决什么问题。
   - 它是核心业务系统、支撑系统、管理后台、SDK、数据处理任务、还是集成中台的一部分。
   - 它的边界在哪里，哪些能力在仓库内，哪些依赖外部系统。

2. **技术栈与运行形态**
   - 使用了哪些主要语言、框架、中间件、数据库、消息系统、前端技术。
   - 如何构建、如何运行、如何本地启动、如何打包、如何部署。
   - 优先查看 `Makefile`、`docker-compose.yml` / `compose.yaml`、`package.json` 的 `scripts`、`justfile`、`Taskfile.yml`、`pom.xml`、`build.gradle` / `build.gradle.kts`、`go.mod`、`Cargo.toml`、`.csproj` / `.sln`、`pyproject.toml`、`requirements.txt`、`Gemfile`、`composer.json`、`CMakeLists.txt`、启动脚本等环境编排入口。
   - 是否存在多服务、多进程、多入口、多 runtime 混合的情况。

3. **核心数据模型与 Schema/DDL**
   - 在完成系统形态、启动方式、主要入口的初步判断后，抽取核心实体、主表/集合、关键索引、关联关系、DDL/迁移脚本、ORM 实体/Mapper/Repository 对应关系。
   - 判断哪些数据模型承载真实业务约束，哪些只是 DTO、缓存镜像、搜索索引映射、历史兼容结构或临时中间表。
   - 若仓库中只能看到部分 Schema、迁移脚本或 ORM 定义，必须明确说明分析缺口。

4. **入口点与主要执行链路**
   - 识别所有重要入口，而不是只找一个。
   - 包括但不限于：
     - Web/API 入口
     - 前端页面入口
     - CLI / 脚本入口
     - 定时任务入口
     - 消息消费入口
     - 后台 Worker
     - 插件/扩展注册入口
     - SDK / 类库对外暴露入口
     - 桌面应用窗口/进程入口
     - 移动端页面/路由/宿主桥接入口
   - 特别识别请求进入核心业务前经过的鉴权、网关、过滤器、中间件、拦截器、AOP/装饰器链路。
   - 对每一类入口，给出主要执行链路和关键中间层。

5. **目录结构与模块地图**
   - 提炼关键目录，不要罗列所有文件。
   - 识别真正承载业务复杂度的模块，而不是只按目录名机械分类。
   - 标出核心模块、公共模块、基础设施模块、胶水层、历史遗留堆积区。

6. **核心业务流与主要数据流**
   - 从代码角度识别主要用例、关键实体、读写路径、状态流转。
   - 说明请求如何进入系统、如何穿过控制层/服务层/领域层/DAO 层，最终落到数据库、缓存、消息系统或外部 API。
   - 如果系统以任务流、事件流、批处理为主，则按实际形态描述，不要强行套 Web 分层。

7. **配置、数据与外部集成**
   - 配置来源在哪里：环境变量、配置文件、配置中心、命令参数、数据库。
   - 数据访问方式是什么：ORM、SQL、Repository、Mapper、文件、对象存储、第三方服务、本地嵌入式存储、缓存、搜索引擎。
   - 对外暴露什么：HTTP API、RPC、消息、Webhook、文件交换、SDK、插件接口、命令行能力。
   - 依赖了哪些关键外部系统。

8. **可观测性与运行诊断线索**
   - 识别日志框架与配置、日志格式、链路追踪字段、健康检查、指标采集、Profiling、APM、审计日志、告警埋点等可观测性线索。
   - 说明线上问题排查时，开发者最可能依赖哪些日志入口、监控入口、诊断开关或排错脚本。
   - 区分仓库内可见的诊断能力，与需要依赖外部平台才能确认的能力。

9. **测试、交付与工程化现状**
   - 是否存在单元测试、集成测试、端到端测试、测试夹具。
   - 是否存在构建流水线、发布脚本、容器化配置、基础设施定义、桌面打包配置、移动端构建配置或制品发布脚本。
   - 识别工程质量现状：格式化、lint、依赖管理、版本管理、环境隔离、脚本可维护性。

10. **遗留风险、复杂区域与技术债**
   - 重点排查：
     - 核心逻辑无测试覆盖
     - 高耦合、循环依赖、超大类/超长函数
     - 配置散落、环境耦合、魔法常量
     - 安全敏感路径
     - 性能敏感路径
     - 事务/并发/缓存一致性风险
     - 历史兼容包袱与重复实现
     - 疑似僵尸代码、废弃分支、失效兼容逻辑、长期未接线但仍参与构建的模块
     - 依赖混乱、版本漂移、构建链脆弱

11. **推荐阅读顺序**
   - 面向第一次接手该项目的工程师，给出“先看什么，再看什么”的最短上手路径。
   - 阅读顺序应优先覆盖：生态识别文件、启动入口、配置装配、主链路、核心模块、数据访问、风险点。

## 工作方式要求

1. 先整体，后局部。
2. 先识别运行形态、启动方式与环境编排入口，再拆模块与业务流。
3. 先识别项目所属技术生态与工程组织方式，例如工作区、多模块、多包、多二进制、多应用壳、多端共享代码，再判断分析边界。
4. 在完成宏观识别后，优先抽取核心数据模型、Schema/DDL 与 ORM/Mapper 对应关系，再回到主链路验证业务含义。
5. 重点识别鉴权、中间件、拦截器、过滤器、AOP 等“业务前置链路”，避免误把它们遗漏为基础设施细节。
6. 若项目不是传统 Web 系统，不要强行套 Controller-Service-DAO 叙事；应改按实际形态描述，例如事件流、批处理流、插件回调链、桌面事件循环、脚本执行流、库函数调用面。
7. 分析结束后必须输出完整详细报告，不得仅输出一页式摘要、简版结论、泛化建议或缺少证据支撑的“高层概览”。
8. 基于证据，不要脑补；找不到证据时明确写“不确定”。
9. 明确区分：
   - **已确认事实**：可以被代码或配置直接证明。
   - **合理推断**：由命名、调用关系、目录结构、上下文推断，但证据尚不充分。
   - **待确认问题**：必须依赖业务人员、运维、产品、DBA 或运行环境才能确认。
10. 在 `一句话概述`、`系统形态与技术栈`、`核心数据模型与 Schema/DDL`、`关键入口与启动方式`、`目录结构与模块地图`、`核心链路与数据流`、`配置、数据存储与外部集成`、`可观测性与运行诊断线索`、`已确认风险与复杂区域` 这些章节中，每条核心结论都尽量显式标注：`[已确认事实]`、`[合理推断]` 或 `[待确认问题]`。
11. 不要罗列全部文件，只提炼关键目录、关键文件、关键入口、关键链路。
12. 不要被现有文档带偏；若文档与代码不一致，以代码为准，并在报告中指出。
13. 如果项目是多仓拼装、子模块聚合、monorepo、多服务集合，请明确指出边界，不要误判为单一应用。
14. 若缺少运行环境、私有依赖、数据库、配置中心信息，必须将其列入“待确认问题”，不要假装已经理解完整。
15. 若核心模块关系、关键调用链或服务边界较复杂，鼓励补充 1 到 2 个 Mermaid 图（如系统关系图、时序图、流程图），但图示不能替代文字证据。
16. 报告必须逐章完整输出；除非仓库内确无证据，否则不要省略任何章节，也不要把多个章节合并成一句话带过。

## 输出要求

1. 输出要服务于“第一次接手该项目的工程师快速上手”。
2. 用中文输出。
3. 最终输出必须是一份名为 `repo-analysis-report.md` 的**详细分析报告**，不是简报、摘要、会议纪要式提纲，也不是只列结论不展开论证的短答案。
4. 除 `一句话概述` 外，其余章节应尽量展开到“让后续维护者据此继续下钻源码”的程度；每个章节都应包含关键判断、判断依据、证据锚点，必要时补充分析缺口。
5. 每个核心结论尽量附上证据锚点，格式示例：
   - 证据：`src/main.ts`
   - 证据：`cmd/server/main.go`
   - 证据：`pom.xml`、`application-prod.yml`
   - 证据：`internal/order/service.go::CreateOrder`
   - 证据：`Cargo.toml`、`src/bin/server.rs`
   - 证据：`appsettings.Production.json`、`Program.cs`
   - 证据：`pyproject.toml`、`alembic/versions`
   - 证据：`CMakeLists.txt`、`src/main.cpp`
6. 优先从工作区文件、包管理文件、构建文件、环境编排文件、启动脚本判断系统如何被拉起，以及哪些目录属于同一分析边界。
7. 若项目属于 SDK、桌面端、移动端、CLI、插件体系、基础设施工具链等非典型 Web 形态，报告结构仍保持不变，但链路描述方式应贴合该形态。
8. 除 `待确认问题` 章节外，其余章节中的关键结论尽量在同一条内显式标记：`[已确认事实]`、`[合理推断]` 或 `[待确认问题]`。
9. 如果某项无法确认，请直接写：
   - “当前无法仅依据代码确认”
   - “仓库内未发现直接证据”
   - “需要结合运行环境/业务背景进一步确认”
10. 若某一章节信息不足，不得省略；应交代已检查的目录/文件范围、未确认原因、以及该缺口对后续维护的影响。
11. 若核心链路、服务关系、模块依赖较复杂，鼓励补充 Mermaid 图辅助说明，但图中结论仍需能回溯到代码证据。
12. `已确认风险与复杂区域` 章节中的每条风险必须同时包含：
   - 风险点
   - 影响范围
   - 触发原因或证据依据
   - 证据锚点
   - 初步应对思路
   若缺少这些要素，不要把它写成“已确认风险”。
13. `待确认问题` 章节中的每个问题尽量同时说明：为什么重要、会影响哪类修改、缺少什么信息才能确认。
14. `建议阅读顺序` 章节应给出带理由的阅读路径，而不只是文件清单。
15. 不输出空话、套话，不写泛泛而谈的“架构建议”。优先交付可用于继续读代码的认知地图。

请使用以下 Markdown 结构输出：

# 项目整体认知报告
## 0. 分析快照
- 目标仓库/目录：
- 分析时间：
- 分支 / Commit / 子模块状态：
- 技术生态线索：
- 可见配置与依赖范围：
- 本次分析限制：

## 1. 一句话概述
- 用一句话说明这个项目从代码上看最可能是做什么的。
- 若无法准确确认，给出“保守表述”。
- 结论前尽量加标签：`[已确认事实]` 或 `[合理推断]`。

## 2. 系统形态与技术栈
- 说明系统形态。
- 说明语言、框架、构建工具、运行依赖。
- 先点明工作区/工程组织方式，如单模块、多模块、多包、monorepo、多应用壳、插件式结构。
- 优先说明项目由哪些环境编排入口、启动脚本或构建脚本拉起。
- 标出多服务、多入口、多运行时情况。
- 关键结论前尽量加标签：`[已确认事实]`、`[合理推断]`。

## 3. 核心数据模型与 Schema/DDL
- 提炼核心实体、主表/集合、关键关联、约束、索引、迁移脚本。
- 说明代码模型与数据库模型的映射关系。
- 区分真实业务主模型、DTO、缓存镜像、搜索索引映射、历史兼容结构。

## 4. 关键入口与启动方式
- 列出主要入口点。
- 说明各入口对应的启动方式、注册方式、主链路起点。
- 若存在 SDK、CLI、桌面端、移动端、插件宿主等入口，也应纳入同级分析。
- 重点说明鉴权、中间件、过滤器、拦截器、AOP/装饰器链路。
- 每个入口尽量附证据锚点，并显式区分已确认与推断部分。

## 5. 目录结构与模块地图
- 只提炼关键目录与核心模块。
- 标出业务核心区、基础设施区、公共组件区、历史遗留区。
- 对“历史遗留区”或“胶水层”的判断若证据不足，请标记为 `[合理推断]`。

## 6. 核心链路与数据流
- 按最重要的 2 到 5 条链路展开。
- 说明调用路径、关键模块、关键数据落点、外部交互点。
- 对每条链路尽量使用“入口 -> 中间层 -> 数据落点 / 外部交互”的形式描述，并标注结论类型。
- 若不适合用请求链路表达，可改为“触发源 -> 调度/路由/回调层 -> 核心处理 -> 数据落点 / 外部交互”。

## 7. 配置、数据存储与外部集成
- 配置来源与环境差异。
- 数据访问方式与主要存储。
- 外部系统依赖与接口暴露方式。
- 对仓库内无法直接确认的环境差异，明确标记为 `[待确认问题]`。

## 8. 可观测性与运行诊断线索
- 说明日志、指标、追踪、健康检查、审计或排错脚本的可见线索。
- 标出开发者排查线上问题时最可能依赖的入口。
- 对需要结合外部平台才能确认的监控能力，明确标记为 `[待确认问题]`。

## 9. 测试、构建与交付现状
- 测试覆盖现状。
- 构建、打包、发布、容器化、流水线现状。
- 工程化成熟度的关键观察。

## 10. 已确认风险与复杂区域
- 只写有证据支撑的风险。
- 说明风险出现在哪些模块、为什么危险、会影响什么。
- 每条风险建议使用固定格式：`风险点 / 影响范围 / 触发原因 / 证据 / 初步应对思路`。
- 若发现疑似僵尸代码、废弃接口、失效兼容分支，应明确写出其调用缺失或证据不足的依据。

## 11. 待确认问题
- 列出当前无法仅凭代码确认、但会显著影响理解和后续修改的问题。
- 对每个问题尽量说明其影响范围、缺失信息来源、以及若不确认可能导致的误判。

## 12. 建议阅读顺序
- 给出最短上手路径。
- 尽量按“生态识别文件 -> 入口 -> 配置 -> 主链路 -> 核心模块 -> 数据访问 -> 风险点”的顺序组织。
- 尽量说明为什么先看这一部分、看完后应获得什么认知，再进入下一部分。

## 13. 证据索引
- 汇总报告中反复引用的关键文件、关键目录、关键类/函数，便于读者二次下钻。
- 若存在高频引用的启动脚本、配置文件、CI/CD 文件、SQL 脚本、容器文件，也一并列出。


---

# 遗留项目变更影响面分析 Prompt
> **版本：** 3.4

你现在是一名资深的软件架构师、遗留系统维护专家与代码影响面分析专家。

请分析目标仓库：`<请填写仓库绝对路径、仓库名或当前工作区中的明确目标目录>`。

当前需要对既有系统进行一项功能或业务变更。你的目标不是立刻生成或修改代码，而是帮助人类开发者**在动手编码前，基于现有代码与配置，完成一次可落地、可追溯、可直接指导实施的变更影响面分析**，从而尽量缩小修改范围、提前暴露兼容性风险，并形成安全的实施顺序。

变更目标：
> `<请填写本次变更目标、问题背景或需求描述>`

本模板为**通用版**，适用于但不限于：Java / Kotlin、Go、Python、Node.js / TypeScript、C# / .NET、PHP、Ruby、Rust、C / C++、前端单页应用、服务端应用、桌面程序、任务程序、脚本工具、混合型 monorepo。若实际项目采用了更特殊的技术生态（如低代码平台、游戏引擎、嵌入式工程、数据科学工作流、移动端原生工程），仍应遵循同样的证据优先、范围收敛与边界先行原则。

在开始分析前，请先输出并明确以下分析快照：
- 目标仓库/目录
- 变更目标
- 分析时间
- 当前可见的分支、提交号、子模块状态（若仓库内未发现直接证据，请明确写无法确认）
- 当前可见的技术生态线索（如包管理文件、构建文件、工作区配置、解决方案文件、工程文件）
- 当前可见的配置范围（仅代码仓库、包含 `.env`/配置文件、包含容器与 CI 文件、是否缺失私有依赖）
- 本次分析的主要限制（如：缺少数据库、缺少配置中心、缺少运行环境、子模块未拉取、私有包不可访问）

## 核心原则

1. **代码是真理之源**
   - 对于棕地项目，默认其 **不是使用 SDD 流程开发**，因此通常**不存在可靠的变更设计文档、完整影响面说明、可信赖的实现计划**。
   - 即使仓库中存在 README、设计说明、注释、Wiki、接口文档、需求文字，也只能视为**候选线索**，**不能直接当作事实**。
   - 所有“已确认事实”都必须尽量由以下证据支撑：代码、构建脚本、包管理文件、配置文件、启动脚本、CI/CD 文件、容器文件、测试、数据库脚本、接口定义、工程文件或工作区定义。

2. **先定位变更触点，再评估影响半径**
   - 先识别本次变更从哪里进入系统：用户入口、API、消息、定时任务、CLI、SDK、插件、桌面事件、移动端桥接或内部调度点。
   - 再沿调用链向内追踪，区分直接修改点、间接影响点、兼容性边界、部署与运维影响，而不是一开始就泛泛枚举大量可能相关目录。

3. **像外科医生一样精准**
   - 只圈定必须触碰的代码、配置、脚本、表结构、接口契约与测试。
   - 严禁把“顺手优化”“顺手重构”“看起来也可以一起改”的内容混入必改范围；若确有必要，只能列为“可选顺带治理项”，不得伪装成必改项。

4. **禁止影响面脑补**
   - 不能因为目录名、类名、接口名“看起来相关”，就直接认定必须修改。
   - 当依赖关系、运行时装配、动态注册、反射调用、配置开关、灰度逻辑或外部系统契约无法仅从代码确认时，必须明确标记为“待确认问题”。

5. **报告必须可追溯**
   - 每个关键判断尽量附“证据锚点”：关键目录、关键文件、关键类/函数、配置项、脚本、命令、表结构、接口定义。
   - 不要求穷举所有文件，但必须让读者能顺着你的报告快速找到修改入口、风险点与验证点。

6. **最终必须交付详细报告**
   - 分析完成后，必须输出一份可直接交接给后续维护者的**详细影响面分析报告**，报告名称为 `change-impact-analysis-report.md`，而不是简短摘要、要点罗列或泛泛综述。
   - 详细报告应覆盖变更入口、直接修改点、级联影响、契约风险、数据与配置影响、测试回归、实施顺序、待确认问题，并在关键结论处附证据锚点。
   - 若某一章节证据不足，也必须明确写出“已检视范围”“未发现直接证据”“缺口可能带来的实施风险”，而不是直接略过。

7. **分析边界必须明确**
   - 优先分析源码、构建脚本、包管理文件、配置文件、启动脚本、容器文件、CI/CD 文件、测试、数据库脚本、接口定义、工作区/工程定义。
   - 默认排除明显的噪音或生成物目录，例如：`node_modules`、`dist`、`build`、`target`、`coverage`、`vendor`、`bin`、`obj`等二进制产物目录、测试快照、大型导出数据；除非它们本身就是变更影响核心。
   - 若项目是 monorepo、多仓拼装、子模块聚合或多服务集合，先划清分析边界，再分别判断哪些子系统必须修改、哪些只是被动受影响、哪些当前无直接证据表明需要触碰。

## 分析任务

请重点分析以下内容：

1. **变更意图与系统边界**
   - 本次变更从代码上看最可能在解决什么问题。
   - 该变更属于缺陷修复、行为调整、性能优化、兼容性修复、安全修复、架构治理、接口扩展，还是混合型变更。
   - 它的边界在哪里，哪些能力在仓库内可控，哪些依赖外部系统、运行环境、数据库或上下游服务。

2. **技术栈与受影响运行形态**
   - 当前系统使用了哪些主要语言、框架、中间件、数据库、消息系统、前端技术。
   - 本次变更会落在哪些运行时、进程、服务、二进制、页面入口、Worker、任务、插件宿主或构建产物上。
   - 优先查看 `Makefile`、`docker-compose.yml` / `compose.yaml`、`package.json` 的 `scripts`、`justfile`、`Taskfile.yml`、`pom.xml`、`build.gradle` / `build.gradle.kts`、`go.mod`、`Cargo.toml`、`.csproj` / `.sln`、`pyproject.toml`、`requirements.txt`、`Gemfile`、`composer.json`、`CMakeLists.txt`、启动脚本等环境编排入口。

3. **变更入口与核心调用链**
   - 识别本次变更对应的主要入口点，而不是只找一个函数。
   - 包括但不限于：
     - Web/API 入口
     - 前端页面入口
     - CLI / 脚本入口
     - 定时任务入口
     - 消息消费入口
     - 后台 Worker
     - 插件/扩展注册入口
     - SDK / 类库对外暴露入口
     - 桌面应用窗口/进程入口
     - 移动端页面/路由/宿主桥接入口
   - 特别识别请求进入核心逻辑前经过的鉴权、网关、过滤器、中间件、拦截器、AOP/装饰器链路。
   - 对每一类入口，给出“触发源 -> 中间层 -> 核心处理 -> 数据落点 / 外部交互”的主链路。

4. **必须修改的直接影响点**
   - 精确识别必须触碰的文件、类、函数、配置项、SQL、脚本、接口定义、测试夹具。
   - 区分：
     - 必须修改：不改就无法实现目标或无法保证正确性
     - 建议同步修改：不一定阻塞，但否则容易引入不一致
     - 当前无证据需要修改：名字看似相关，但调用链或装配链尚未证明
   - 对每个必须修改点尽量说明“为什么必须改”“改动目标是什么”“与哪条主链路相关”。

5. **级联影响与隐性依赖**
   - 识别本次变更会波及哪些未直接修改的模块、下游系统、数据结构、缓存键、索引、消息格式、序列化协议、任务编排或构建流程。
   - 重点排查动态注册、反射、事件总线、配置开关、灰度逻辑、共享 DTO、公共库、基类、模板方法、代码生成物、历史兼容分支。
   - 判断哪些是已确认的级联影响，哪些只是高风险怀疑点。

6. **契约、数据与配置影响**
   - 评估 API 签名、数据库 Schema、消息格式、缓存结构、文件格式、配置项、环境变量、Feature Flag、权限模型是否受影响。
   - 若涉及数据模型、Schema/DDL、迁移脚本、ORM 映射、序列化结构变更，说明兼容性方向：向前兼容、向后兼容、双写过渡、一次性切换，还是当前无法确认。
   - 区分“代码内可完成的变更”和“必须依赖运维/DBA/平台协作的变更”。

7. **安全、权限、中间件与可观测性影响**
   - 识别该变更是否会影响鉴权、授权、租户隔离、数据脱敏、审计日志、安全校验、中间件行为。
   - 识别日志、指标、追踪、告警、审计、诊断开关是否需要同步调整，或者哪些现有观测点可以用于回归验证。
   - 如果变更可能引发线上排障难度上升，应明确指出。

8. **测试覆盖与回归策略**
   - 当前是否已有单元测试、集成测试、端到端测试、契约测试、回归用例覆盖该链路。
   - 哪些测试必须新增、修改或补强，哪些现有测试可能失效。
   - 若缺少自动化测试，也要说明可执行的人工验证路径、冒烟路径、回归重点与上线前检查项。

9. **实施顺序与回滚思路**
   - 给出安全、最小化的实施顺序：先改什么，后改什么，最后验证什么。
   - 若存在灰度、双写、开关控制、数据迁移、跨服务联动、版本兼容窗口，应明确指出。
   - 若需要回滚，说明最可能的回滚边界与高风险步骤。

## 工作方式要求

1. 先整体，后局部。
2. 先识别变更入口、运行形态与环境编排入口，再收敛到直接修改点与级联影响。
3. 先识别项目所属技术生态与工程组织方式，例如工作区、多模块、多包、多二进制、多应用壳、多端共享代码，再判断分析边界。
4. 若涉及核心数据模型、Schema/DDL、缓存结构、消息结构、接口契约，必须优先确认其兼容性边界，再评估具体修改点。
5. 重点识别鉴权、中间件、拦截器、过滤器、AOP 等“业务前置链路”，避免漏掉真实生效路径。
6. 若项目不是传统 Web 系统，不要强行套 Controller-Service-DAO 叙事；应改按实际形态描述，例如事件流、批处理流、插件回调链、桌面事件循环、脚本执行流、库函数调用面。
7. 分析结束后必须输出完整详细报告，不得仅输出一页式摘要、简版结论、泛化建议或缺少证据支撑的“高层概览”。
8. 基于证据，不要脑补；找不到证据时明确写“不确定”。
9. 明确区分：
   - **已确认事实**：可以被代码、配置或明确调用关系直接证明。
   - **合理推断**：由命名、调用关系、目录结构、上下文推断，但证据尚不充分。
   - **待确认问题**：必须依赖业务人员、运维、产品、DBA、平台团队或运行环境才能确认。
10. 在 `变更意图与范围概述`、`受影响系统形态与技术栈`、`核心调用链路图谱`、`必须修改的文件清单`、`级联影响与风险雷达`、`契约、数据与配置影响`、`测试与回归策略建议`、`已确认风险与复杂区域` 这些章节中，每条核心结论都尽量显式标注：`[已确认事实]`、`[合理推断]` 或 `[待确认问题]`。
11. 不要罗列全部文件，只提炼关键目录、关键文件、关键入口、关键链路、关键契约边界。
12. 不要被现有文档带偏；若文档与代码不一致，以代码为准，并在报告中指出。
13. 如果项目是多仓拼装、子模块聚合、monorepo、多服务集合，请明确指出本次变更究竟影响哪几个子系统，不要误判为“全仓都要改”。
14. 若缺少运行环境、私有依赖、数据库、配置中心、消息平台信息，必须将其列入“待确认问题”，不要假装已经理解完整。
15. 若核心调用链、跨服务依赖或兼容性边界较复杂，鼓励补充 1 到 2 个 Mermaid 图（如系统关系图、时序图、流程图），但图示不能替代文字证据。
16. 报告必须逐章完整输出；除非仓库内确无证据，否则不要省略任何章节，也不要把多个章节合并成一句话带过。

## 输出要求

1. 输出要服务于“指导工程师安全、有序地进行代码修改”。
2. 用中文输出。
3. 最终输出必须是一份名为 `change-impact-analysis-report.md` 的**详细影响面分析报告**，不是简报、摘要、会议纪要式提纲，也不是只列结论不展开论证的短答案。
4. 除 `一句话概述` 不存在外，其余章节应尽量展开到“让后续实施者据此继续下钻源码、修改代码并安排验证”的程度；每个章节都应包含关键判断、判断依据、证据锚点，必要时补充分析缺口。
5. 每个核心结论尽量附上证据锚点，格式示例：
   - 证据：`src/main.ts`
   - 证据：`cmd/server/main.go`
   - 证据：`pom.xml`、`application-prod.yml`
   - 证据：`internal/order/service.go::CreateOrder`
   - 证据：`Cargo.toml`、`src/bin/server.rs`
   - 证据：`appsettings.Production.json`、`Program.cs`
   - 证据：`pyproject.toml`、`alembic/versions`
   - 证据：`CMakeLists.txt`、`src/main.cpp`
6. 优先从工作区文件、包管理文件、构建文件、环境编排文件、启动脚本判断变更会影响哪些运行边界、哪些目录属于同一修改范围。
7. 若项目属于 SDK、桌面端、移动端、CLI、插件体系、基础设施工具链等非典型 Web 形态，报告结构仍保持不变，但链路描述方式应贴合该形态。
8. 除 `待确认业务规则与问题清单` 章节外，其余章节中的关键结论尽量在同一条内显式标记：`[已确认事实]`、`[合理推断]` 或 `[待确认问题]`。
9. 如果某项无法确认，请直接写：
   - “当前无法仅依据代码确认”
   - “仓库内未发现直接证据”
   - “需要结合运行环境/业务背景进一步确认”
10. 若某一章节信息不足，不得省略；应交代已检查的目录/文件范围、未确认原因、以及该缺口对后续实施的影响。
11. 若核心链路、跨服务影响、模块依赖较复杂，鼓励补充 Mermaid 图辅助说明，但图中结论仍需能回溯到代码证据。
12. `必须修改的文件清单` 章节中，尽量区分“必须修改 / 建议同步修改 / 当前无证据需要修改”。
13. `级联影响与风险雷达`、`已确认风险与复杂区域` 章节中的每条风险必须同时包含：
   - 风险点
   - 影响范围
   - 触发原因或证据依据
   - 证据锚点
   - 初步应对思路
   若缺少这些要素，不要把它写成“已确认风险”。
14. `待确认业务规则与问题清单` 章节中的每个问题尽量同时说明：为什么重要、会影响哪类修改、缺少什么信息才能确认。
15. `推荐的实施顺序` 章节应给出带理由的修改与验证顺序，而不只是文件清单。
16. 不输出空话、套话，不写泛泛而谈的“重构建议”。优先交付可用于继续实施的认知地图与风险边界。

请使用以下 Markdown 结构输出：

# 业务变更影响面分析报告
## 0. 分析快照
- 目标仓库/目录：
- 变更目标：
- 分析时间：
- 分支 / Commit / 子模块状态：
- 技术生态线索：
- 可见配置与依赖范围：
- 本次分析限制：

## 1. 变更意图与范围概述
- 说明这次变更在代码上最可能要解决什么问题。
- 区分修复类、优化类、兼容类、扩展类、安全类或治理类变更。
- 结论前尽量加标签：`[已确认事实]`、`[合理推断]`。

## 2. 受影响系统形态与技术栈
- 说明涉及的系统形态、语言、框架、运行时、构建方式。
- 点明本次变更波及哪些服务、模块、页面、任务、进程或二进制。
- 说明工作区/工程组织方式，如单模块、多模块、多包、monorepo、多应用壳、插件式结构。

## 3. 核心调用链路图谱
- 列出本次变更涉及的主要入口点。
- 说明各入口对应的主链路起点、中间层、数据落点与外部交互点。
- 重点说明鉴权、中间件、过滤器、拦截器、AOP/装饰器链路。
- 若不适合用请求链路表达，可改为“触发源 -> 调度/路由/回调层 -> 核心处理 -> 数据落点 / 外部交互”。

## 4. 必须修改的文件清单
- 精确到目录、文件、类、函数、配置项、脚本、SQL 或测试。
- 尽量区分：`必须修改`、`建议同步修改`、`当前无证据需要修改`。
- 每项尽量说明修改原因、修改目标、关联链路与证据。

## 5. 级联影响与风险雷达
- 说明未直接修改但可能受影响的模块、服务、数据结构、缓存、消息、构建链路。
- 区分已确认的级联影响与高风险怀疑点。
- 重点关注动态装配、共享 DTO、公共库、反射、事件总线、兼容分支。

## 6. 契约、数据与配置影响
- 评估 API、数据库 Schema、消息格式、缓存结构、文件格式、配置项、环境变量、Feature Flag 是否受影响。
- 说明兼容性方向与迁移方式。
- 区分代码内可完成项与需要外部协作的项。

## 7. 安全、权限、中间件与可观测性影响
- 说明鉴权、授权、审计、脱敏、租户隔离、中间件行为是否受影响。
- 说明日志、指标、追踪、告警、审计或排障入口是否需要同步调整。
- 对仓库内无法直接确认的线上观测能力，明确标记为 `[待确认问题]`。

## 8. 测试与回归策略建议
- 说明当前测试覆盖现状。
- 说明必须新增、修改或补强的测试。
- 若缺少自动化测试，给出可执行的人工验证与回归路径。

## 9. 已确认风险与复杂区域
- 只写有证据支撑的风险。
- 说明风险出现在哪些模块、为什么危险、会影响什么。
- 每条风险建议使用固定格式：`风险点 / 影响范围 / 触发原因 / 证据 / 初步应对思路`。

## 10. 待确认业务规则与问题清单
- 列出当前无法仅凭代码确认、但会显著影响修改方案与实施边界的问题。
- 对每个问题尽量说明其影响范围、缺失信息来源、以及若不确认可能导致的误判。

## 11. 推荐的实施顺序
- 给出安全、最小化的实施顺序。
- 尽量说明为什么先做这一部分、完成后应验证什么、下一步再做什么。
- 若涉及灰度、双写、开关控制、迁移或回滚边界，也应明确说明。

## 12. 证据索引
- 汇总报告中反复引用的关键文件、关键目录、关键类/函数，便于读者二次下钻。
- 若存在高频引用的启动脚本、配置文件、CI/CD 文件、SQL 脚本、容器文件，也一并列出。


---

# 基于接口隔离的绞杀者重构流程

## 执行流程

```text
特征测试保护
    ↓
识别改造边界
    ↓
从旧代码提取接口
    ↓
旧模块实现接口
    ↓
上层依赖接口
    ↓
引入分发器
    ↓
新模块实现接口并委托未完成方法
    ↓
按函数逐步替换
    ↓
影子调用与结果比对
    ↓
灰度放量
    ↓
旧模块下线
```

---

# 1. 用特征测试保护旧行为

## 目标

在改造旧代码之前，先用测试记录当前系统行为。

这类测试的目的不是证明旧代码设计正确，而是锁定旧代码当前的外部行为，防止重构过程中产生意外变化。

---

## 示例代码

```csharp
using NUnit.Framework;

[TestFixture]
public class LegacyOrderPriceServiceTests
{
    [Test]
    public void CalculatePrice_WhenCustomerIsVip_ShouldApplyVipDiscount()
    {
        var service = new LegacyOrderPriceService();

        var order = new Order
        {
            CustomerLevel = "VIP",
            Items =
            {
                new OrderItem
                {
                    ProductId = "P001",
                    UnitPrice = 100,
                    Quantity = 2
                }
            }
        };

        var result = service.CalculatePrice(order);

        Assert.That(result, Is.EqualTo(180));
    }

    [Test]
    public void CalculateDiscount_WhenCustomerIsVip_ShouldReturnDiscountAmount()
    {
        var service = new LegacyOrderPriceService();

        var order = new Order
        {
            CustomerLevel = "VIP",
            Items =
            {
                new OrderItem
                {
                    ProductId = "P001",
                    UnitPrice = 100,
                    Quantity = 2
                }
            }
        };

        var result = service.CalculateDiscount(order);

        Assert.That(result, Is.EqualTo(20));
    }

    [Test]
    public void CalculateTax_ShouldReturnTaxBasedOnFinalPrice()
    {
        var service = new LegacyOrderPriceService();

        var order = new Order
        {
            CustomerLevel = "VIP",
            Items =
            {
                new OrderItem
                {
                    ProductId = "P001",
                    UnitPrice = 100,
                    Quantity = 2
                }
            }
        };

        var result = service.CalculateTax(order);

        Assert.That(result.TaxAmount, Is.EqualTo(10.8m));
        Assert.That(result.TaxRate, Is.EqualTo(0.06m));
    }
}
```

---

# 2. 识别改造边界

## 目标

明确本次改造的对象不是整个系统，而是某个可控的业务能力边界。

例如，本次只改造订单价格计算能力：

```text
订单价格计算
├── CalculatePrice
├── CalculateDiscount
└── CalculateTax
```

此时不处理：

```text
订单创建
库存扣减
支付处理
发票生成
消息通知
```

---

## 建议记录改造边界

```markdown
## 改造范围

本次改造对象：订单价格计算模块。

### 包含能力

- 订单价格计算
- 折扣计算
- 税费计算

### 暂不包含

- 订单创建
- 库存扣减
- 支付处理
- 发票生成
- 消息通知

### 旧模块

- `LegacyOrderPriceService`

### 上游调用方

- `OrderApplicationService`
- `CheckoutService`
- `InvoicePreviewService`
```

---

# 3. 从旧代码中提取接口

## 目标

根据旧模块当前对外提供的能力，提取接口。

注意，第一版接口不追求完美领域模型，而是追求：

```text
兼容旧逻辑
稳定调用方
隔离依赖关系
支持后续替换
```

---

## 示例代码

```csharp
public interface IOrderPriceService
{
    decimal CalculatePrice(Order order);

    decimal CalculateDiscount(Order order);

    TaxResult CalculateTax(Order order);
}
```

---

## 不推荐的做法

不要在第一步就重设计成过于理想化的接口：

```csharp
public interface IPricingDomainService
{
    PricingDecision MakePricingDecision(PricingContext context);
}
```

这类接口可能更合理，但不适合作为第一步隔离接口。

第一步的目标是：

```text
从旧代码中提取接口，而不是重新设计系统。
```

---

# 4. 让旧模块实现接口

## 目标

让旧模块实现刚提取出的接口。

此时仍然不改变旧代码业务逻辑。

---

## 示例代码

```csharp
public class LegacyOrderPriceService : IOrderPriceService
{
    public decimal CalculatePrice(Order order)
    {
        var basePrice = order.Items.Sum(x => x.UnitPrice * x.Quantity);

        if (order.CustomerLevel == "VIP")
        {
            basePrice *= 0.9m;
        }

        return basePrice;
    }

    public decimal CalculateDiscount(Order order)
    {
        if (order.CustomerLevel == "VIP")
        {
            return order.Items.Sum(x => x.UnitPrice * x.Quantity) * 0.1m;
        }

        return 0;
    }

    public TaxResult CalculateTax(Order order)
    {
        var price = CalculatePrice(order);

        return new TaxResult
        {
            TaxAmount = price * 0.06m,
            TaxRate = 0.06m
        };
    }
}
```

---

# 5. 将上层代码改为依赖接口

## 改造前

```csharp
public class CheckoutService
{
    private readonly LegacyOrderPriceService _priceService;

    public CheckoutService(LegacyOrderPriceService priceService)
    {
        _priceService = priceService;
    }

    public decimal PreviewPrice(Order order)
    {
        return _priceService.CalculatePrice(order);
    }
}
```

---

## 改造后

```csharp
public class CheckoutService
{
    private readonly IOrderPriceService _priceService;

    public CheckoutService(IOrderPriceService priceService)
    {
        _priceService = priceService;
    }

    public decimal PreviewPrice(Order order)
    {
        return _priceService.CalculatePrice(order);
    }
}
```

---

## DI 注册

```csharp
services.AddScoped<IOrderPriceService, LegacyOrderPriceService>();
```

这一阶段完成后，系统结构变为：

```text
CheckoutService
    ↓
IOrderPriceService
    ↓
LegacyOrderPriceService
```

此时仍然只有旧实现，业务行为不应发生变化。

---

# 6. 引入新模块骨架

## 目标

创建一个新的模块，同样实现 `IOrderPriceService`。

但是新模块不需要一次性实现所有方法。

已经重构的方法使用新逻辑，尚未重构的方法委托旧模块。

---

## 示例代码

```csharp
public class ModernOrderPriceService : IOrderPriceService
{
    private readonly IOrderPriceService _legacy;

    public ModernOrderPriceService(IOrderPriceService legacy)
    {
        _legacy = legacy;
    }

    public decimal CalculatePrice(Order order)
    {
        // 新实现
        var total = order.Items.Sum(x => x.UnitPrice * x.Quantity);

        var discountRate = order.CustomerLevel switch
        {
            "VIP" => 0.1m,
            "SVIP" => 0.15m,
            _ => 0m
        };

        return total * (1 - discountRate);
    }

    public decimal CalculateDiscount(Order order)
    {
        // 尚未重构，委托旧模块
        return _legacy.CalculateDiscount(order);
    }

    public TaxResult CalculateTax(Order order)
    {
        // 尚未重构，委托旧模块
        return _legacy.CalculateTax(order);
    }
}
```

---

## 当前状态

```text
ModernOrderPriceService
├── CalculatePrice      新实现
├── CalculateDiscount   委托旧实现
└── CalculateTax        委托旧实现
```

这种模式可以避免一次性重写所有逻辑。

---

# 7. 引入请求分发器

## 目标

请求分发器也实现同一个接口，用于决定请求走旧模块还是新模块。

结构如下：

```text
上层业务代码
    ↓
IOrderPriceService
    ↓
OrderPriceServiceDispatcher
    ├── LegacyOrderPriceService
    └── ModernOrderPriceService
```

---

## 灰度策略接口

```csharp
public interface IGrayReleasePolicy
{
    bool ShouldUseModern(string routingKey, string methodName);
}
```

---

## 基于比例的灰度策略

```csharp
public class PercentageGrayReleasePolicy : IGrayReleasePolicy
{
    private readonly Dictionary<string, int> _methodRatios;

    public PercentageGrayReleasePolicy(Dictionary<string, int> methodRatios)
    {
        _methodRatios = methodRatios;
    }

    public bool ShouldUseModern(string routingKey, string methodName)
    {
        if (!_methodRatios.TryGetValue(methodName, out var ratio))
        {
            return false;
        }

        if (ratio <= 0)
        {
            return false;
        }

        if (ratio >= 100)
        {
            return true;
        }

        var hash = Math.Abs(HashCode.Combine(routingKey, methodName));

        return hash % 100 < ratio;
    }
}
```

这里使用 `routingKey` 做稳定路由，避免同一个用户或订单在多次请求中随机切换实现。

---

## 请求分发器实现

```csharp
public class OrderPriceServiceDispatcher : IOrderPriceService
{
    private readonly IOrderPriceService _legacy;
    private readonly IOrderPriceService _modern;
    private readonly IGrayReleasePolicy _grayPolicy;

    public OrderPriceServiceDispatcher(
        IOrderPriceService legacy,
        IOrderPriceService modern,
        IGrayReleasePolicy grayPolicy)
    {
        _legacy = legacy;
        _modern = modern;
        _grayPolicy = grayPolicy;
    }

    public decimal CalculatePrice(Order order)
    {
        if (_grayPolicy.ShouldUseModern(order.CustomerId, nameof(CalculatePrice)))
        {
            return _modern.CalculatePrice(order);
        }

        return _legacy.CalculatePrice(order);
    }

    public decimal CalculateDiscount(Order order)
    {
        if (_grayPolicy.ShouldUseModern(order.CustomerId, nameof(CalculateDiscount)))
        {
            return _modern.CalculateDiscount(order);
        }

        return _legacy.CalculateDiscount(order);
    }

    public TaxResult CalculateTax(Order order)
    {
        if (_grayPolicy.ShouldUseModern(order.CustomerId, nameof(CalculateTax)))
        {
            return _modern.CalculateTax(order);
        }

        return _legacy.CalculateTax(order);
    }
}
```

---

# 8. 注册新旧模块与分发器

## 问题

如果直接这样注册会产生循环依赖：

```csharp
services.AddScoped<IOrderPriceService, OrderPriceServiceDispatcher>();
services.AddScoped<IOrderPriceService, LegacyOrderPriceService>();
services.AddScoped<IOrderPriceService, ModernOrderPriceService>();
```

因为多个实现都绑定到同一个接口后，分发器很难区分旧实现和新实现。

---

## 推荐做法：使用显式包装接口

```csharp
public interface ILegacyOrderPriceService : IOrderPriceService
{
}

public interface IModernOrderPriceService : IOrderPriceService
{
}
```

---

## 旧模块实现旧接口

```csharp
public class LegacyOrderPriceService : ILegacyOrderPriceService
{
    public decimal CalculatePrice(Order order)
    {
        var basePrice = order.Items.Sum(x => x.UnitPrice * x.Quantity);

        if (order.CustomerLevel == "VIP")
        {
            basePrice *= 0.9m;
        }

        return basePrice;
    }

    public decimal CalculateDiscount(Order order)
    {
        if (order.CustomerLevel == "VIP")
        {
            return order.Items.Sum(x => x.UnitPrice * x.Quantity) * 0.1m;
        }

        return 0;
    }

    public TaxResult CalculateTax(Order order)
    {
        var price = CalculatePrice(order);

        return new TaxResult
        {
            TaxAmount = price * 0.06m,
            TaxRate = 0.06m
        };
    }
}
```

---

## 新模块实现新接口

```csharp
public class ModernOrderPriceService : IModernOrderPriceService
{
    private readonly ILegacyOrderPriceService _legacy;

    public ModernOrderPriceService(ILegacyOrderPriceService legacy)
    {
        _legacy = legacy;
    }

    public decimal CalculatePrice(Order order)
    {
        var total = order.Items.Sum(x => x.UnitPrice * x.Quantity);

        var discountRate = order.CustomerLevel switch
        {
            "VIP" => 0.1m,
            "SVIP" => 0.15m,
            _ => 0m
        };

        return total * (1 - discountRate);
    }

    public decimal CalculateDiscount(Order order)
    {
        return _legacy.CalculateDiscount(order);
    }

    public TaxResult CalculateTax(Order order)
    {
        return _legacy.CalculateTax(order);
    }
}
```

---

## 分发器依赖明确实现

```csharp
public class OrderPriceServiceDispatcher : IOrderPriceService
{
    private readonly ILegacyOrderPriceService _legacy;
    private readonly IModernOrderPriceService _modern;
    private readonly IGrayReleasePolicy _grayPolicy;

    public OrderPriceServiceDispatcher(
        ILegacyOrderPriceService legacy,
        IModernOrderPriceService modern,
        IGrayReleasePolicy grayPolicy)
    {
        _legacy = legacy;
        _modern = modern;
        _grayPolicy = grayPolicy;
    }

    public decimal CalculatePrice(Order order)
    {
        if (_grayPolicy.ShouldUseModern(order.CustomerId, nameof(CalculatePrice)))
        {
            return _modern.CalculatePrice(order);
        }

        return _legacy.CalculatePrice(order);
    }

    public decimal CalculateDiscount(Order order)
    {
        if (_grayPolicy.ShouldUseModern(order.CustomerId, nameof(CalculateDiscount)))
        {
            return _modern.CalculateDiscount(order);
        }

        return _legacy.CalculateDiscount(order);
    }

    public TaxResult CalculateTax(Order order)
    {
        if (_grayPolicy.ShouldUseModern(order.CustomerId, nameof(CalculateTax)))
        {
            return _modern.CalculateTax(order);
        }

        return _legacy.CalculateTax(order);
    }
}
```

---

## DI 注册

```csharp
services.AddScoped<ILegacyOrderPriceService, LegacyOrderPriceService>();
services.AddScoped<IModernOrderPriceService, ModernOrderPriceService>();

services.AddSingleton<IGrayReleasePolicy>(_ =>
{
    return new PercentageGrayReleasePolicy(new Dictionary<string, int>
    {
        [nameof(IOrderPriceService.CalculatePrice)] = 5,
        [nameof(IOrderPriceService.CalculateDiscount)] = 0,
        [nameof(IOrderPriceService.CalculateTax)] = 0
    });
});

services.AddScoped<IOrderPriceService, OrderPriceServiceDispatcher>();
```

此时所有上层业务仍然只依赖：

```csharp
IOrderPriceService
```

但实际执行入口已经变成：

```text
IOrderPriceService
    ↓
OrderPriceServiceDispatcher
    ├── LegacyOrderPriceService
    └── ModernOrderPriceService
```

---

# 9. 支持影子调用与结果比对

## 目标

在真正切流之前，可以让正式结果仍然来自旧模块，同时旁路执行新模块，并记录新旧结果差异。

适合：

```text
无副作用
只读计算
可重复执行
不会修改外部状态
```

不适合直接用于：

```text
写数据库
发消息
扣库存
调用支付
发送短信
```

---

## 对比结果记录接口

```csharp
public interface IResultComparer
{
    void Compare<T>(
        string methodName,
        string routingKey,
        T legacyResult,
        T modernResult);
}
```

---

## 简单实现

```csharp
public class LoggingResultComparer : IResultComparer
{
    private readonly ILogger<LoggingResultComparer> _logger;

    public LoggingResultComparer(ILogger<LoggingResultComparer> logger)
    {
        _logger = logger;
    }

    public void Compare<T>(
        string methodName,
        string routingKey,
        T legacyResult,
        T modernResult)
    {
        if (!EqualityComparer<T>.Default.Equals(legacyResult, modernResult))
        {
            _logger.LogWarning(
                "Modern result differs from legacy. Method={MethodName}, RoutingKey={RoutingKey}, Legacy={LegacyResult}, Modern={ModernResult}",
                methodName,
                routingKey,
                legacyResult,
                modernResult);
        }
    }
}
```

---

## 支持影子调用的分发器

```csharp
public class ShadowOrderPriceServiceDispatcher : IOrderPriceService
{
    private readonly ILegacyOrderPriceService _legacy;
    private readonly IModernOrderPriceService _modern;
    private readonly IResultComparer _resultComparer;

    public ShadowOrderPriceServiceDispatcher(
        ILegacyOrderPriceService legacy,
        IModernOrderPriceService modern,
        IResultComparer resultComparer)
    {
        _legacy = legacy;
        _modern = modern;
        _resultComparer = resultComparer;
    }

    public decimal CalculatePrice(Order order)
    {
        var legacyResult = _legacy.CalculatePrice(order);
        var modernResult = _modern.CalculatePrice(order);

        _resultComparer.Compare(
            nameof(CalculatePrice),
            order.CustomerId,
            legacyResult,
            modernResult);

        // 正式结果仍然返回旧模块结果
        return legacyResult;
    }

    public decimal CalculateDiscount(Order order)
    {
        var legacyResult = _legacy.CalculateDiscount(order);
        var modernResult = _modern.CalculateDiscount(order);

        _resultComparer.Compare(
            nameof(CalculateDiscount),
            order.CustomerId,
            legacyResult,
            modernResult);

        return legacyResult;
    }

    public TaxResult CalculateTax(Order order)
    {
        var legacyResult = _legacy.CalculateTax(order);
        var modernResult = _modern.CalculateTax(order);

        // TaxResult 是对象，需要自定义比较逻辑
        if (legacyResult.TaxAmount != modernResult.TaxAmount ||
            legacyResult.TaxRate != modernResult.TaxRate)
        {
            _resultComparer.Compare(
                nameof(CalculateTax),
                order.CustomerId,
                legacyResult,
                modernResult);
        }

        return legacyResult;
    }
}
```

---

# 10. 按函数逐步替换

## 目标

新模块不要求一次性替代旧模块，而是按函数逐步替换。

---

## 替换计划示例

| 阶段 | 新模块实现 | 委托旧模块 | 灰度比例 |
|---|---|---|---|
| 第 1 阶段 | 无 | 全部 | 0% |
| 第 2 阶段 | CalculatePrice | CalculateDiscount, CalculateTax | 5% |
| 第 3 阶段 | CalculatePrice | CalculateDiscount, CalculateTax | 30% |
| 第 4 阶段 | CalculatePrice, CalculateDiscount | CalculateTax | 10% |
| 第 5 阶段 | CalculatePrice, CalculateDiscount, CalculateTax | 无 | 100% |
| 第 6 阶段 | 新模块 | 旧模块下线 | 100% |

---

## 新模块逐步演进示例

### 第一版：只替换价格计算

```csharp
public class ModernOrderPriceService : IModernOrderPriceService
{
    private readonly ILegacyOrderPriceService _legacy;

    public ModernOrderPriceService(ILegacyOrderPriceService legacy)
    {
        _legacy = legacy;
    }

    public decimal CalculatePrice(Order order)
    {
        var total = order.Items.Sum(x => x.UnitPrice * x.Quantity);

        var discountRate = order.CustomerLevel switch
        {
            "VIP" => 0.1m,
            "SVIP" => 0.15m,
            _ => 0m
        };

        return total * (1 - discountRate);
    }

    public decimal CalculateDiscount(Order order)
    {
        return _legacy.CalculateDiscount(order);
    }

    public TaxResult CalculateTax(Order order)
    {
        return _legacy.CalculateTax(order);
    }
}
```

---

### 第二版：继续替换折扣计算

```csharp
public class ModernOrderPriceService : IModernOrderPriceService
{
    private readonly ILegacyOrderPriceService _legacy;

    public ModernOrderPriceService(ILegacyOrderPriceService legacy)
    {
        _legacy = legacy;
    }

    public decimal CalculatePrice(Order order)
    {
        var total = GetTotal(order);
        var discount = CalculateDiscount(order);

        return total - discount;
    }

    public decimal CalculateDiscount(Order order)
    {
        var total = GetTotal(order);

        var discountRate = order.CustomerLevel switch
        {
            "VIP" => 0.1m,
            "SVIP" => 0.15m,
            _ => 0m
        };

        return total * discountRate;
    }

    public TaxResult CalculateTax(Order order)
    {
        return _legacy.CalculateTax(order);
    }

    private static decimal GetTotal(Order order)
    {
        return order.Items.Sum(x => x.UnitPrice * x.Quantity);
    }
}
```

---

### 第三版：完整替换税费计算

```csharp
public class ModernOrderPriceService : IModernOrderPriceService
{
    public decimal CalculatePrice(Order order)
    {
        var total = GetTotal(order);
        var discount = CalculateDiscount(order);

        return total - discount;
    }

    public decimal CalculateDiscount(Order order)
    {
        var total = GetTotal(order);

        var discountRate = order.CustomerLevel switch
        {
            "VIP" => 0.1m,
            "SVIP" => 0.15m,
            _ => 0m
        };

        return total * discountRate;
    }

    public TaxResult CalculateTax(Order order)
    {
        var price = CalculatePrice(order);

        return new TaxResult
        {
            TaxAmount = price * 0.06m,
            TaxRate = 0.06m
        };
    }

    private static decimal GetTotal(Order order)
    {
        return order.Items.Sum(x => x.UnitPrice * x.Quantity);
    }
}
```

此时新模块已经不再依赖旧模块。

---

# 11. 灰度放量

## 目标

每替换一个函数，都不直接全量上线，而是逐步放量。

---

## 配置示例

```json
{
  "GrayRelease": {
    "CalculatePrice": 5,
    "CalculateDiscount": 0,
    "CalculateTax": 0
  }
}
```

---

## 读取配置的灰度策略

```csharp
public class ConfigurableGrayReleasePolicy : IGrayReleasePolicy
{
    private readonly IConfiguration _configuration;

    public ConfigurableGrayReleasePolicy(IConfiguration configuration)
    {
        _configuration = configuration;
    }

    public bool ShouldUseModern(string routingKey, string methodName)
    {
        var ratio = _configuration.GetValue<int>($"GrayRelease:{methodName}");

        if (ratio <= 0)
        {
            return false;
        }

        if (ratio >= 100)
        {
            return true;
        }

        var hash = Math.Abs(HashCode.Combine(routingKey, methodName));

        return hash % 100 < ratio;
    }
}
```

---

## 放量过程

```text
0% → 1% → 5% → 10% → 30% → 50% → 100%
```

每次放量前需要检查：

```text
错误率
响应时间
核心业务指标
新旧结果差异率
异常日志
用户投诉
数据库写入一致性
```

---

# 12. 快速回滚

## 目标

当新实现出现问题时，可以立即切回旧实现。

---

## 回滚方式

将配置从：

```json
{
  "GrayRelease": {
    "CalculatePrice": 30
  }
}
```

调整为：

```json
{
  "GrayRelease": {
    "CalculatePrice": 0
  }
}
```

此时请求分发器会重新全部走旧模块：

```text
IOrderPriceService
    ↓
OrderPriceServiceDispatcher
    ↓
LegacyOrderPriceService
```

---

# 13. 旧模块下线

## 目标

当所有方法都已经由新模块稳定承接后，可以删除旧模块。

---

## 下线前检查

| 检查项 | 要求 |
|---|---|
| 新模块覆盖率 | 接口中的所有方法均由新模块实现 |
| 灰度比例 | 已经稳定运行 100% |
| 结果对比 | 无不可接受差异 |
| 监控指标 | 错误率、延迟、业务指标稳定 |
| 回归测试 | 全部通过 |
| 上游依赖 | 不再直接依赖旧模块 |
| 配置清理 | 灰度配置不再需要 |
| 代码引用 | 旧模块无生产引用 |

---

## 下线后的 DI 注册

```csharp
services.AddScoped<IOrderPriceService, ModernOrderPriceService>();
```

旧的注册可以删除：

```csharp
services.RemoveAll<ILegacyOrderPriceService>();
services.RemoveAll<IModernOrderPriceService>();
services.RemoveAll<IGrayReleasePolicy>();
```

最终结构：

```text
CheckoutService
    ↓
IOrderPriceService
    ↓
ModernOrderPriceService
```

---

# 14. 最终流程总结

完整流程如下：

```text
1. 为旧模块补充特征测试
2. 识别棕地改造边界
3. 从旧模块当前行为中提取接口
4. 让旧模块实现接口
5. 将上层业务代码改为依赖接口
6. 引入新模块骨架
7. 未完成的新模块方法委托旧模块
8. 引入请求分发器
9. 通过灰度策略控制新旧实现切换
10. 使用影子调用进行新旧结果对比
11. 按函数逐步替换旧实现
12. 按比例逐步放量
13. 出现问题时快速回滚到旧实现
14. 新模块完全稳定后下线旧模块
```

---

# 15. 推荐工程纪律

## 1. 每一步都必须可回滚

不要做不可逆的大规模修改。

---

## 2. 每一步都必须有测试保护

至少包括：

```text
特征测试
单元测试
集成测试
回归测试
新旧结果对比测试
```

---

## 3. 接口初期以兼容为主

第一版接口的目标不是优雅，而是隔离。

---

## 4. 新模块内部可以重新设计

新模块虽然对外实现旧接口，但内部可以逐步采用：

```text
DDD
Clean Architecture
策略模式
领域服务
值对象
规则引擎
配置化策略
```

---

## 5. 委托旧模块的方法必须登记

例如：

```markdown
## ModernOrderPriceService 替换进度

| 方法 | 当前状态 | 计划 |
|---|---|---|
| CalculatePrice | 已新实现 | 灰度中 |
| CalculateDiscount | 委托旧模块 | 下一阶段替换 |
| CalculateTax | 委托旧模块 | 最后替换 |
```

---

## 6. 影子调用必须谨慎使用

只读计算类逻辑可以直接影子调用。

有副作用的逻辑必须谨慎，例如：

```text
写数据库
发消息
发短信
扣库存
调支付
调用第三方接口
```

这些场景需要使用：

```text
幂等键
事务隔离
Mock 外部依赖
事件旁路
只记录不提交
沙箱环境
```

---

# 16. 精简版方法论表达

> 对棕地系统进行安全重构时，应先通过特征测试锁定旧行为，再从旧模块中提取兼容接口，使上层业务代码不再直接依赖旧实现。随后引入同样实现该接口的新模块，新模块可以先只实现部分方法，未完成的方法继续委托旧模块。通过请求分发器在旧实现与新实现之间进行稳定路由、影子调用、结果比对和灰度放量。随着新模块逐步覆盖接口中的所有能力，旧模块承担的职责不断减少，最终在验证充分、可回滚路径完整的前提下下线旧模块。
