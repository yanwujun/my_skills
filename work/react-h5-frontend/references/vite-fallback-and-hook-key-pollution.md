# 实录：Vite SPA fallback 与 hook 键污染（novel-learn，2026-08-06）

全链路实测揪出的两个前端坑，均为真实发生 + 验证修复。

## 坑1 实录：章节正文渲染成 index.html

现象：阅读器 `fetch('/novels/react-core/chapters/01.md')` 渲染出 Vite dev 的 index.html（含 `injectIntoGlobalHook` / `@react-refresh` / `/@vite/client`）。

诊断链（curl 与浏览器对比）：
```
curl -s http://localhost:5173/novels/react-core/chapters/01.md | head -3
# → "# 第一章 异界来客 ..."（正确！curl 能拿到）
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/novels/react-core/01.md
# → 200（路径不存在但返回 200 = SPA fallback 的 index.html）
```
根因：manifest 的 `chapter.file` 已是 `"chapters/01.md"`，Reader 又硬拼 `chapters/` 前缀 → 请求 `/novels/react-core/chapters/chapters/01.md` → 不存在 → fallback 200 + index.html。
修复：`fetch(`/novels/${id}/${file}`)`，file 自带完整相对路径，只拼一次。

## 坑2 实录：进度数据「神秘消失」（localStorage 被覆盖成空）

现象：点亮第一章后进度 8%+连击1 正常，切视图/刷新后变 0%。browser_console 直查键值：`{"completedChapters":[],...}` —— 被覆盖而非丢失。

根因链：
1. App 层 `const prog = useProgress(novel?.manifest?.id ?? '__shelf__')` —— 单个 hook 实例跨 `__shelf__` / `react-core` 两个 id 复用
2. useState 初始化只在首次挂载执行（拿到 fallback 键的空数据）
3. novelId 切换时保存 effect（依赖 `[novelId, progress]`）触发 → **用旧的空 progress 写进新键** → 覆盖真实进度

修复（React 惯用法）：删除 App 层跨 id 的 hook 实例；MapView / Reader 各自 `useProgress(manifest.id)` 挂 hook，父组件 `key={manifest.id}` 强制重挂载。

验证方法（区分「真丢」和「误报」）：
- browser_console 表达式直读：`localStorage.getItem('novel-learn:progress:react-core')`（不猜，直接看）
- 控制实验：① 不改代码直接刷新 → 数据保留（排除持久化问题）② `touch src/hooks/useProgress.js` 触发 HMR → 数据保留（排除 HMR 清空）③ 结论：清空发生在结构大改瞬间，重构后根治

## 附：零后端静态内容架构速览

```
content/<id>/  (manifest.json + chapters/*.md + tests/*.json)
      │ npm run sync:content（cp + 生成 index.json 清单，含 cover）
      ▼
web/public/novels/  →  fetch('/novels/<id>/manifest.json') 等
```
- 极简 Markdown 渲染器需支持代码围栏（```jsx），否则代码块散成文本（`fence` 状态机，十几行）
- localStorage 进度键 `novel-learn:progress:<novelId>`，导出/导入 JSON 兜底
- 页面间数据一致性：书架卡片进度与地图页进度各自从 localStorage 读，天然一致
