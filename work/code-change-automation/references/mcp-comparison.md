# MCP 选型参考（接口测试场景）

## 可用选项

| MCP | 本质 | 截图 | 直接调 API | 需要启动额外进程 |
|-----|------|------|-----------|----------------|
| **Chrome DevTools MCP** (当前主力) | 浏览器 CDP 协议代理 | AX 树快照（非视觉截图） | ✅ `evaluate_script` + `fetch` | 需要 Chrome `--remote-debugging-port=9222` |
| **cursor-ide-browser** (内建) | Cursor IDE 内置浏览器 | ✅ 真实视觉截图 | ❌ 无 `evaluate_script`，只能通过 Swagger UI 点击操作 | 零，IDE 自带 |
| **Apifox MCP** (备选) | API 管理平台 MCP 服务 | ❌ | ✅ 直接 `call_api` | 无，但需提前导入 API 定义到 Apifox 项目 |

## 选择原则

### 接口自动回归测试（当前流程）
→ **Chrome DevTools MCP**。理由：
- `evaluate_script` + `fetch` 是程序化调用，比 Swagger UI 点按钮快 5-10 倍
- 参数可控、响应可解析、可自动化断言
- 启动 Chrome 的成本被单次环境准备摊薄

### 视觉排障 / 查看 Swagger 页面状态
→ **cursor-ide-browser**。理由：
- 零配置，截图直观
- 适合查看页面渲染、确认 Swagger 列表、调试登录流程
- 但**不适合**跑大量用例

### 正式 CI / 回归测试
→ **Apifox MCP**（如果配置了）。理由：
- 稳定，无浏览器进程
- 但需维护 API 定义同步（代码变化后需重新导入 Swagger 文档）

## 已知坑

- **不要**在 `swagger-mysql-api-test` 里自己写启动服务逻辑，委托给 `/start_app` 命令（见 SKILL.md §2.3）
- Chrome DevTools MCP 启动失败时先确认 9222 端口未被占用，再启动 Chrome
- cursor-ide-browser 每次会话需重新登录（Cookie 不跨会话持久）
