---
name: ai-tech-research
description: "搜索 GitHub Trending / AI 新闻源，分类整理 AI 开源项目，生成结构化周报。当 web_search 不可用时自动切换到浏览器 fallback。"
version: 1.0.0
tags: [research, ai, github, reporting]
---

# AI 技术研究与周报生成

搜索 GitHub Trending 及 AI 新闻源，发现热门 AI 开源项目，分类整理并生成结构化周报。支持 web_search 和浏览器 fallback 双路径。

## 触发条件

- 用户要求生成 AI 周报 / AI 项目汇总 / GitHub trending 报告
- 用户问"本周有什么热门 AI 项目"
- Cron 定时任务触发 AI 周报生成

## 执行流程

### Phase 0: 检测工具可用性

先发一条 `web_search` 测试 Firecrawl 是否在线：

```
web_search(query="test", limit=1)
```

- **成功** → 走 Phase 1（web_search 路径）
- **失败**（`Unauthorized: Invalid token`）→ 走 Phase 2（浏览器 fallback 路径），不要再重试 web_search

### Phase 1: web_search 路径（Firecrawl 可用时）

按 cron prompt 中的搜索策略执行多轮搜索，分类覆盖：

1. 综合热门：`"GitHub trending AI repositories this week"`
2. AI Agent：`"awesome AI agents GitHub trending"`
3. LLM 工具：`"LLM tools framework GitHub new project stars"`
4. AI 多模态：`"AI image video generation GitHub trending"`
5. AI 开发工具：`"AI developer tools MCP GitHub"`

每轮用 `web_extract` 获取详情，提取：项目名、简介、Star 数、语言、类别。

### Phase 2: 浏览器 fallback 路径（Firecrawl 不可用时）

这是本 skill 的核心价值 — 当 web_search 挂掉时的可靠备用方案。

#### 2a: 抓取 GitHub Trending

```javascript
// browser_navigate 到 GitHub Trending
browser_navigate(url="https://github.com/trending?since=weekly")

// 提取所有项目卡片
browser_console(expression="Array.from(document.querySelectorAll('article')).map(a => {
  const h2 = a.querySelector('h2');
  const p = a.querySelector('p');
  const stars = a.querySelectorAll('a[href*=\"/stargazers\"]');
  const forks = a.querySelectorAll('a[href*=\"/forks\"]');
  const name = h2 ? h2.textContent.trim() : '';
  const desc = p ? p.textContent.trim() : '';
  const starText = stars.length > 0 ? stars[0].textContent.replace(/[^0-9,]/g, '').trim() : '';
  const forkText = forks.length > 0 ? forks[0].textContent.replace(/[^0-9,]/g, '').trim() : '';
  const weekStars = a.textContent.match(/([\\d,]+)\\s*stars?\\s*this\\s*week/i);
  return {name, desc, star: starText, fork: forkText, weekStars: weekStars ? weekStars[1] : ''};
}).filter(p => p.name).map(p => JSON.stringify(p)).join('\\n')")
```

#### 2b: 补充分类覆盖

对 Python/TypeScript 等 AI 常用语言单独抓取：

```
browser_navigate(url="https://github.com/trending/python?since=weekly")
browser_navigate(url="https://github.com/trending/typescript?since=weekly")
```

重复 2a 的提取脚本。

#### 2c: 如需项目详情

对重点项目的 README 进行访问：

```
browser_navigate(url="https://github.com/owner/repo")
browser_snapshot(full=true)
```

### Phase 3: 分类整理

将项目分为以下类别（仅保留 AI 相关）：

| 类别 | 标签 | 判断标准 |
|------|------|----------|
| AI Agent / 智能体框架 | 🤖 | agent 框架、编排、多 agent 协作 |
| LLM / 训练 / 推理 | 🧠 | 模型训练、推理引擎、高效注意力 |
| AI 开发工具 / MCP | 🔧 | MCP 服务器、AI coding 工具、skill 系统 |
| 图像 / 视频 / 多模态 | 🎨 | 图像生成、视频生成、3D 模型 |
| 数据处理 / RAG | 📊 | 向量数据库、text-to-SQL、知识图谱 |
| AI 应用 / 产品 | 🏗️ | AI 驱动的终端应用 |
| AI 研究 | 🔬 | 学术项目、论文实现 |
| 其他 AI 相关 | 💡 | 不符合以上但值得关注的 |

排除明确非 AI 项目（Minecraft 服务器、文件传输工具、SEO 工具等）。

### Phase 4: 生成报告

#### 输出路径

```
/mnt/d/项目/个人总结/AI周报/AI周报_YYYY-MM-DD.md
```

#### 报告结构

```markdown
# 🤖 AI 开源项目周报
**日期：YYYY年MM月DD日 — MM月DD日**
**本期收录：X 个项目**

## 📈 本周亮点
[3-5 个最值得关注的项目，每个 ~80 字说明为什么重要]

## 📂 分类详情
### 🤖 AI Agent / 智能体框架
| 项目 | Star | 语言 | 简介 |
[表格 + 每个项目一段详细说明]

[其他类别同上]

## 📊 本周统计
- 总收录、类别分布表、增速 Top 5

## 🔍 趋势观察
[3-5 条趋势总结，每条 1-2 句话 + 支撑项目]
```

#### QQ 消息精简版

在最终回复中同时输出适合手机阅读的精简版（Top 5 增长 + 分类数量 + 趋势关键词）。

## 注意事项

- 只收录 AI 相关项目，非 AI 项目果断排除
- 项目数据必须真实来自 GitHub，不得编造
- 文档用中文撰写，项目名和技术名词保留英文
- 如果某个类别无项目，标注"本周无新项目"
- 目录不存在时自动创建
- 日期使用当前日期，确保格式正确（如 2026-07-27 而非 2025-07-25）
