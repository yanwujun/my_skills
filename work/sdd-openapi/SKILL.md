---
name: sdd-openapi
description: "SDD OpenAPI 生成：从 plan.md API契约→标准 OpenAPI 3.0 JSON/YAML"
---
# SDD OpenAPI — API 文档生成

基于 `plan.md` §3 的 API 契约，生成 OpenAPI 3.0 规范文件。

## 执行方式
1. 从 `plan.md` §3 提取所有端点、Method、Request/Response
2. 推断缺失信息（Content-Type → application/json, 认证方式 → Bearer Token）
3. 对推断项显式标注 `假设：xxx，待确认`
4. 生成 `openapi.yaml`

## 生成规则

### Endpoint 提取
- 路径必须与 plan.md 完全一致
- parameters 区分为 path/query/header
- requestBody 标注 required

### Schema 推断
- 从 DTO 字段类型推断 JSON Schema
- 枚举字段标注 enum
- 必填字段根据 spec.md AC 推断

### 错误响应
- 每个端点至少包含 `200` 和对应错误码的 response
- 错误码从 plan.md §4 错误码规范读取
- 统一错误格式：`{ "code": "ERROR_CODE", "message": "..." }`

### 元信息
- info.title = spec.md 项目名称
- info.version = spec.md 版本号

## 质量规则
- 所有推断标注 `# [推断] 来源：xxx，待确认`
- 不得虚构不存在的 endpoint
- 返回结构必须可追溯至 plan.md DTO 定义