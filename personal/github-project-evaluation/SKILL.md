---
name: github-project-evaluation
description: Use when 评估GitHub组织/仓库（'这个项目怎么样'）。REST API直查star与活跃度，含评价框架。
tags: [github, research, evaluation]
---

# GitHub 项目/组织评估

## 触发条件

- 用户发一个 GitHub 链接问"这个项目怎么样 / 值得用吗 / 靠谱吗"
- 技术选型前调研现成项目（对比 star、活跃度、功能缺口）——用户固定习惯
- 需要精确仓库数据（star/fork/最近提交/License），不想靠搜索摘要的模糊描述

## 前置：工具可用性

- 首选 web_search + web_extract（Firecrawl 在线时直接抓 org 页/README 即可）
- Firecrawl 报错（`Unauthorized: Invalid token` 或 `Payment Required: Insufficient credits`）→ **整个会话放弃 web_search/web_extract，不再重试**，直接走 GitHub REST API 路线
- GitHub API 需要代理：`export HTTPS_PROXY=http://127.0.0.1:8888 HTTP_PROXY=http://127.0.0.1:8888`（sing-box，与 gh 命令同款）

## 核心流程：GitHub REST API（curl 直查，免 HTML 抓取）

### 1. 判定链接是组织还是个人账号（必做！）

```bash
curl -s --max-time 30 "https://api.github.com/orgs/<NAME>" -o /tmp/org.json
curl -s --max-time 30 "https://api.github.com/users/<NAME>" -o /tmp/user.json
```

- `/orgs/` 返回 404 → 它是 User 账号。**github.com/<Name> 经常是占坑/休眠个人号**（实例：github.com/PrimeIntellect = 2010 年注册的 0 仓库个人号，真身是 PrimeIntellect-ai 组织，2023 年创建、65 仓库）
- 找真身：`/search/users?q=<NAME>&per_page=10`，过滤 `items[].type == "Organization"`
- user.json 的 `type/public_repos/followers/created_at/blog` 一眼看出规模与年龄

### 2. 拉仓库列表（star 排序是回答"怎么样"的正确姿势）

```bash
curl -s --max-time 30 "https://api.github.com/orgs/<NAME>/repos?per_page=100&sort=stars&order=desc" -o /tmp/repos.json
```

- `sort=stars` 看人气；`sort=updated` 看最近在忙什么（两个都拉，信息互补）
- 解析模板（**必须防 dict 错误响应**）：

```python
import json
d = json.load(open('/tmp/repos.json'))
if isinstance(d, dict):          # API 错误 {"message":"Not Found"} 不能当列表迭代
    print('API error:', d.get('message')); raise SystemExit
for r in d:
    print(f"{r['stargazers_count']:>6}★ {r['forks_count']:>5}f | {r['name']:<38} | {(r['description'] or '')[:70]} | {r['pushed_at'][:10]}")
```

- 单仓库元数据：`/repos/<ORG>/<REPO>`（created_at / pushed_at / license / topics / archived / default_branch）

### 3. 读 README 定"它到底做什么"

```bash
curl -s --max-time 30 "https://raw.githubusercontent.com/<ORG>/<REPO>/main/README.md" -o /tmp/readme.md
```

- 分支不一定是 main，404 时查 repo.json 的 `default_branch`（老仓库是 master）
- 长 README 用 read_file 分段读；重点看：核心抽象/卖点、安全警告、provider/依赖支持、License、是否基于别家项目二次开发（README 致谢部分）

## 评价框架（输出给用户的结构）

1. **基本盘表格**：星数 / Fork / 成立时间（repo age）/ 最近推送 / 语言 / License。星数必须配年龄与 pushed_at 一起看——3 个月 17K 星的新项目 vs 5 年老项目含义完全不同
2. **它是什么**：一句话定位 + 核心卖点（从 README 提炼，别抄搜索摘要）
3. **生态与接入**：模型/provider 支持、能否对接用户已有栈（DeepSeek key、OpenAI 兼容端点、WSL、已有 coding agent 工作流）
4. **优点 + 风险/短板**：活跃度（几天内有推送 = 认真迭代）、open issues 数、年龄太新的项目要当小白鼠、agent 类工具的安全模型（是否沙箱）
5. **针对用户的结论**：结合用户实际场景给建议（如"你已有 codex/opencode 工作流，不建议立刻迁移，可当第二选项装来对比"）

## 注意事项

- 全程中文输出，项目名/技术名词保留英文
- 数据必须来自 API 实测不得编造；每个结论（尤其"活跃/不活跃"）要有数据支撑
- 回答时把用户自己的技术栈代入对比（用户用 codex/opencode、DeepSeek、WSL、Hermes）
- 未认证 API 限额 60 次/小时，组织调研足够；超限加 `-H "Authorization: token <PAT>"`
- 脚本一律 write_file 到 /tmp 再执行（curl 管道给解释器会被安全扫描拦）
- 组织若有 60+ 仓库，先按 star 排序看头部，别全量读

## 与相关技能的分工

- 周报 / trending 采集（抓热门项目列表）→ ai-tech-research
- 本技能专注：用户点名一个具体项目/组织时的深度评估
