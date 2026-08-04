---
name: weekly-tech-report
description: "Generate weekly AI/tech open-source trend reports — discover trending GitHub projects via browser, categorize by domain, produce structured markdown reports. Used when web_search is unavailable or for cron-based weekly reporting."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [reporting, github, trending, ai, weekly]
---

# Weekly Tech Report Generator

Generate structured weekly reports on AI/tech open-source projects. Designed for scenarios where `web_search` is broken (Firecrawl token invalid) — uses browser-based GitHub Trending extraction as the primary data source.

## Trigger conditions

- User asks for "AI周报", "本周项目", "tech weekly report", or similar
- Cron job that generates periodic tech trend reports
- `web_search` tool is down and you need to discover trending projects

## Workflow

### Step 1: Extract projects from GitHub Trending

Navigate to the trending page and extract all projects in one `browser_console` call:

```javascript
Array.from(document.querySelectorAll('article')).map(a => {
  const h2 = a.querySelector('h2');
  const p = a.querySelector('p');
  const stars = a.querySelectorAll('a[href*="/stargazers"]');
  const forks = a.querySelectorAll('a[href*="/forks"]');
  const name = h2 ? h2.textContent.trim() : '';
  const desc = p ? p.textContent.trim().replace(/\n\s*/g, ' ') : '';
  const starText = stars.length > 0 ? stars[0].textContent.replace(/[^0-9,]/g, '').trim() : '';
  const forkText = forks.length > 0 ? forks[0].textContent.replace(/[^0-9,]/g, '').trim() : '';
  const weekStars = a.textContent.match(/([\d,]+)\s*stars?\s*this\s*week/i);
  return JSON.stringify({
    name: name.replace(/\n\s*/g, ' '),
    desc, star: starText, fork: forkText,
    weekStars: weekStars ? weekStars[1] : ''
  });
}).join('\n')
```

Filter by language: append `?since=weekly` to `github.com/trending/python` etc.

### Step 2: Filter to AI-relevant projects

Exclude non-tech projects (games, file transfer tools, SEO, CMS, etc.). Keep:
- AI/ML frameworks, agents, LLM tools
- Developer tools (MCP, code intelligence, skills)
- AI applications (tutoring, intelligence dashboards)
- AI-adjacent infrastructure (gateways, vector DBs)

### Step 3: Categorize

Group into standard categories:
- 🤖 AI Agent / 智能体框架
- 🧠 LLM / 训练 / 推理
- 🔧 AI 开发工具 / MCP / 插件
- 🎨 AI 图像 / 视频 / 多模态
- 📊 AI 数据 / RAG / 知识库
- 🏗️ AI 应用 / 产品
- 💡 其他

### Step 4: Write report

Save to `D:\项目\个人总结\AI周报\AI周报_YYYY-MM-DD.md` (Windows) or equivalent.

Report structure:
1. **本周亮点** — top 3-5 projects with 100-word explanations
2. **分类详情** — table + detailed descriptions per project
3. **本周统计** — totals, category distribution, top 5 by growth
4. **趋势观察** — 3-5 trend bullets synthesized from the data

## Pitfalls

- **web_search down is common**: The cron job's Firecrawl token expires periodically. Don't retry web_search — go straight to browser-based GitHub Trending.
- **Don't visit individual repos**: The trending page already has name, description, stars, forks, and weekly growth. Only visit individual repos if you need README details for a highlight project.
- **Language filtering helps**: For AI reports, `github.com/trending?since=weekly` (all languages) is better than Python-only, since many AI dev tools are TypeScript/Rust.

## Related

- Cron job: `85a077573fb0` (AI周报 - Saturday 9am)
- Report output dir: `/mnt/d/项目/个人总结/AI周报/`
