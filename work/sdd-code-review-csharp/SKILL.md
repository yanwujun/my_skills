---
name: sdd-code-review-csharp
description: "SDD C#代码评审：基于权威文档审查C#/.NET代码质量、架构边界、合宪性，含现代.NET最佳实践"
---
# C# Code Reviewer

## 核心能力
基于项目权威文档与工程上下文审查 C# 代码，重点检查：合宪性、架构边界、统一语言、可读性、可维护性、可测试性、错误处理，以及现代 .NET / C# 最佳实践。

## 适用场景
- 审查 / review C# 代码
- Review ASP.NET Core / .NET 项目代码
- 提交代码前的 C# Code Review (CR)

## 范围识别
1. 用户指定文件或目录：审查指定范围
2. 用户粘贴 C# 代码：审查粘贴内容
3. 用户只提出模糊请求：先识别或追问具体文件、模块、命名空间路径

## 边界处理
1. 缺少治理文档：只能进行通用 C#/.NET 工程审查，不能做合宪性结论
2. 涉及业务命名判断：优先读取 spec.md / plan.md
3. 只有局部片段：必须显式说明结论仅基于局部静态上下文

## 执行步骤
1. **确认审查依据**：定位 constitution.md / AGENTS.md / spec.md / plan.md
2. **确定审查范围**：识别待审查对象
3. **收集实现上下文**：Read 完整文件 + Grep 追踪引用
4. **定位架构职责**：判断代码层次（Domain/Application/Infrastructure/Presentation）
5. **深度审查**：
   - **架构与依赖**：是否违反依赖倒置？EF Core/HTTP/消息中间件是否反向污染核心层？
   - **业务建模**：实体、值对象、DTO 划分是否合理？是否适合用 record？
   - **测试**：核心逻辑是否有测试覆盖？测试是否体现 spec AC？
   - **失败显式**：Result/Exception 边界是否清晰？异常是否被用作业务控制流？
   - **极简与演进**：是否存在过度设计、过度抽象？
   - **并发与资源**：async/await 是否正确传播？IDisposable/IAsyncDisposable/CancellationToken 是否正确处理？
6. **输出报告**

## 输出格式（同 sdd-code-review-python，含 🔴🟡🟢 三级优先级）

## 审查规则
宪法至上 → 治理与事实双重裁决 → 事实先于判断 → 边界清晰 → 建设性 → 显式不确定性 → 客观无偏见

## 目标
帮助 C#/.NET 代码更合宪、更清晰、更健壮且易于演进。