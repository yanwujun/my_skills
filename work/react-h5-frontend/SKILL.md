---
name: react-h5-frontend
description: "Use when 开发 React 18 H5 前端（Vite+零后端）或排查 fetch 拿到 HTML/进度丢失。"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [react, vite, h5, frontend, localStorage]
    related_skills: [wsl-project-setup, llm-app-backend, project-kickoff]
---

# React 18 H5 前端开发（Vite + 零后端）

用户的个人/学习类 H5 项目（smart-learn-app、novel-learn）均为 React 18 + Vite。沉淀该类应用的架构惯例与真实踩坑（2026-08 novel-learn 全链路实测）。

## 触发场景

- 搭建 React H5 前端（Vite 脚手架，PC+手机响应式）
- 零后端架构：内容是预生成静态文件，进度/状态存 localStorage
- 遇到 fetch 拿到 HTML、进度数据「神秘消失」等前端疑难

## 架构惯例（novel-learn 模式）

- 脚手架：`npm create vite@latest <name> -- --template react`（最新模板为 React 19，API 兼容）
- 静态内容：内容源目录（如 `content/<id>/`）→ `npm run sync:content` 脚本 cp 到 `web/public/<namespace>/`，并生成 `index.json` 清单（含封面/章节数等元数据，供书架类页面用）
- 前端 `fetch('/<namespace>/<id>/manifest.json')` + 章节文件；零后端
- 进度 localStorage：键 `app:progress:<entityId>`；提供导出/导入 JSON 兜底清缓存
- 阅读进度：打开即记 `lastChapter`，列表/地图页「继续阅读」按钮跳回
- 响应式：`max-width: 720px` 居中 + `@media (max-width: 480px)` 收缩字号/按钮竖排/节点紧凑

## 坑1：Vite SPA fallback 把缺失路径返回 index.html（HTTP 200）

- 现象：fetch 静态文件（.md/.json）拿到的是 index.html 源码（含 `@react-refresh` / `/@vite/client`），**不报错不 404**
- 典型根因：路径拼接错误——file 字段已含前缀（如 `chapters/01.md`），代码又硬拼一遍 → 双重前缀
- 诊断：`curl -s <url>` 看内容；**浏览器结果与 curl 不一致 = 浏览器请求的 URL 与你想的不同**，核对拼接逻辑
- 修复：file 字段自带完整相对路径，fetch 只拼一次
- 要点：Vite dev 对不存在路径返回 **200 + index.html**（SPA fallback），「内容不对」比「404」更常见，别被 200 骗了

## 坑2：hook 状态随 props 变化 → 保存 effect 用旧 state 覆盖新键（数据「神秘消失」）

- 现象：进度写入后，切换实体/刷新后变 0%，localStorage 键被覆盖成空 JSON（不是丢失是被覆盖）
- 根因：App 层单个 `useProgress(id ?? fallback)` 实例跨多个 id 复用；useState 初始化只跑一次（拿到 fallback 空数据）；id 变化时保存 effect（依赖 `[id, progress]`）触发，**用旧的空 state 写进新键**
- 修复（React 惯用法）：每个视图组件自己挂 hook（`useProgress(id)`），父组件 `key={id}` 强制重挂载隔离；**不要跨 id 复用 hook 实例**
- 验证：browser_console 直读 localStorage 键值（不猜）；控制实验区分触发点——不改代码刷新（数据在 = 非持久化问题）、touch 文件触发 HMR（数据在 = HMR 安全），再回放代码改动定位

## 坑3：Browserbase 云浏览器会话空闲回收 → localStorage 重置（测试环境假象）

- 现象：浏览器实测中进度「神秘丢失」，连续 3 次排查（以为是 hook 覆盖 bug，还改过代码）都找不出应用问题
- 根因：**Browserbase 云浏览器会话空闲 7~13 分钟后被回收**，localStorage 随之重置 —— 不是应用 bug
- 判据：间隔较久再测就丢、立刻重测不丢；换本地浏览器完全不受影响
- 处理：别 debug 应用，换本地浏览器验证或缩短测试间隔；先把真 bug（坑2 hook 跨 id 复用）与测试环境假象区分开

## 子代理生成内容的验证

长内容（小说/题库/文档）用 delegate_task 带严格契约生成（schema + 必含块 + 计数规则写进 context），产物必须亲验：文件存在、JSON 合法、条目计数、必含块 grep。子代理自报不算数（novel-learn 16 个产物文件全部实测校验后才算通过）。

## 参考

- `references/vite-fallback-and-hook-key-pollution.md` — 两个坑的完整诊断实录与修复 diff、零后端架构速览
