---
name: react-vite-webapp
description: "Use when 做 React+Vite 零后端 Web 应用（SPA fallback 劫持 fetch 等坑）。"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [react, vite, frontend, localStorage, hooks]
    related_skills: [project-kickoff, grill-me, wsl-project-setup]
---

# React + Vite 零后端 Web 应用

用户验证过的模式：React 18 + Vite，零后端（静态内容 + localStorage），H5 响应式，`npm run dev` 即用。应用于 smart-learn-app（FastAPI 版）与 novel-learn（零后端版）等学习工具。

## 触发

- 用户要做一个本地 Web 小工具/单页应用（学习、工具类）
- 涉及 React 状态 + localStorage 持久化 + 静态内容加载

## 架构模式（经过验证）

- 内容作为静态文件放 `web/public/<app>/`；`scripts/sync-content.mjs` 从上游目录（如 `~/<项目>/content/`）同步并生成 `index.json` 书架清单
- 数据加载：`fetch('/<app>/manifest.json')` + `fetch('/<app>/<file>')`（Markdown/文本）
- 进度：localStorage 单键 JSON（`prefix:<id>`），配导出/导入按钮兜底清缓存
- 视图：React 状态机（shelf → map → reader → quiz），**每视图组件自行挂 useProgress(id)，父组件 `<View key={id}>` 隔离**

## 关键坑（本技能核心价值）

### 1. Vite SPA fallback 静默劫持 fetch（最常见）
- 现象：浏览器 fetch 拿到 **index.html** 内容（渲染出 HTML 文本），无 console 报错
- 根因：请求路径不存在（拼错/双重前缀），Vite dev server 对未知路径一律返回 index.html（HTTP 200）
- 诊断：`curl -s <同路径>` 对比——存在返回真实内容，不存在返回 index.html；浏览器与 curl 结果不一致即路径错
- 教训：动态拼路径 `/${id}/${file}` 时先确认 `file` 是否已含目录前缀（本次 bug：file=`chapters/01.md` 又拼了 `chapters/` → 双重前缀）

### 2. React hook 跨 key 复用 → 旧 state 覆盖新数据（数据丢失级 bug）
- 现象：切换视图/数据源后，localStorage 里原数据被写成空 JSON（`completedChapters:[]` 等）
- 根因：`useState` 初始化只在**首次挂载**执行；同一 hook 实例参数（如 novelId）变化时，保存 effect（依赖 `[key, state]`）会用**旧 state** 写入**新 key**
- 修复：每个视图组件各自挂 `useProgress(id)`，父组件用 `<View key={manifest.id}>` 强制重挂载（React 惯用法）
- 防御：保存 effect 跳过"未加载"状态（如 `updatedAt === null` 时不落盘）

### 3. 云浏览器会话回收 → localStorage 重置（测试环境假象，先排查再改代码）
- 现象：浏览器实测时进度"神秘丢失"，代码审查无 bug
- 根因：Browserbase 云浏览器**空闲 7~13 分钟后会话回收**，localStorage 重置；本地浏览器无此问题
- 排查顺序：①dev server 日志（`process log` 看有无 full reload/error）②控制实验（连续操作保留 vs 长间隔后丢失）③时间间隔相关性
- 取证：在 `main.jsx` 注入 `Storage.prototype.setItem` 拦截器 + **sessionStorage 记录**（full reload 不丢 sessionStorage），故意制造场景抓写入者

### 4. 极简 Markdown 渲染器要点（零依赖）
- 覆盖 `##`、`**粗体**`、`- 列表`、`> 引用`、```` ``` ```` 代码围栏（fence 状态机 toggle）
- **代码围栏必须处理**——LLM 生成的小说/文档代码块很多，漏了会把 ``` 当散文本渲染

## 验证流程（功能完成即用）

1. `npm run build` 确认语法（Vite 8 快，~200ms）
2. dev server 起后 `curl` 抽查静态资源路径（防 SPA fallback 陷阱）
3. 浏览器实测核心闭环：数据写入 → 刷新保留 → 切视图保留（三个都过才叫持久化 OK）
4. 改动进度数据后用 console 查 localStorage 确认结构

## 相关

- project-kickoff：项目启动流程（需求梳理 → GitHub 调研 → 工作空间）
- grill-me：需求盘问（12 轮收敛决策后写需求文档定稿）
- wsl-project-setup：WSL 项目位置铁律（源码禁放 /mnt/d/）
