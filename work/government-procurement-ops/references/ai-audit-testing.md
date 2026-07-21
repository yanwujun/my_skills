# AI 审核 Skill 测试指南

## 目标

对 `kjxy-goods-audit`（框架协议商品智能审核）Agent 做批量回归测试。

**两种数据源**：
1. **CSV 导出**（旧方式）— Query5 SQL 导出，tab分隔，约44列
2. **XML 导出**（新方式，推荐）— 061601.xml 等，含完整 HTML 字段

**两种调用方式**：
1. **无状态** `POST /runs/wait` — 快速，不含会话上下文
2. **有状态** `POST /threads/{tid}/runs/wait`（推荐）— 含会话上下文，图片可嵌入

## 前置条件

- API: `http://192.168.2.166:30030/agents-platform/api`
- Web UI: `http://192.168.2.166:5175`
- Agent ID 通过 `GET /api/web/agents` 获取（重启后会变化）
- 当前 Agent: `6000bb28-36cc-426c-a676-3f1b7708d187`（kjxy-goods-audit-two）
- Agent 需 `enabled=true` 且 `skill_names` 包含 `kjxy-goods-audit-two`

## API 接口清单

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/api/ok` | 健康检查 |
| GET | `/api/web/agents` | 查Agent列表 |
| POST | `/api/threads` | 创建线程 |
| POST | `/api/threads/{tid}/runs/wait` | **执行审核（核心）** |
| GET | `/api/threads/{tid}` | 查线程信息 |
| GET | `/api/threads/{tid}/runs` | 查运行记录 |
| POST | `/api/threads/search` | **按agent_id搜线程** |
| GET | `/api/docs` | Swagger文档 |

## 数据准备

### XML 数据解析

XML 文件（如 `061601.xml`）为 Spreadsheet XML 格式。解析方式：

```python
def cell_data(xml):
    return [html.unescape(d) for d in re.findall(r'<Data[^>]*>(.*?)</Data>', xml, re.DOTALL)]
```

### detailImageUrls 提取（关键！）

**重要**：CSV 导出的 `goods_detail_html` 字段会被截断（约50字符），无法提取详情图。必须从 `audit_request_json` 内部的 `goodsDetailHtml` 字段提取：

```python
import sys
sys.path.insert(0, '/mnt/d/项目/gitlib/智能审核/doc')
from enrich_audit_training_data import extract_detail_image_urls

req_data = json.loads(audit_request_json_str)
gdh = req_data.get('goodsDetailHtml', '')
detail_urls_raw = extract_detail_image_urls(gdh) if gdh else []
```

### 图片URL拼接

原始路径为相对路径（如 `groupkjxy/M00/.../xxx.png`），需拼接为完整外网 URL：

```python
IMG_BASE = "https://www.ccgp-chongqing.gov.cn/djc-gateway/files"
IMG_BUSINESS = "kjxyfile50m"

def make_img_url(path):
    if not path or path.startswith('http'): return path
    path = path.strip().strip('"').strip("'")
    fname = path.split('/')[-1]
    return f"{IMG_BASE}?filePath={path}&business={IMG_BUSINESS}&fileName={fname}"
```

## 核心流程：新方案（image_url 嵌入，推荐）

### 步骤1：创建线程

```python
body = json.dumps({"assistant_id": "agents-platform"})
tid = api_post(f"{BASE_URL}/threads", body)
```

⚠️ **注意**：传 `metadata` 字段会导致 422 错误。但线程缺少 `agent_id`/`agent_name` 元数据时，Web UI 左侧列表不会显示该线程。**直接链接 `?thread_id=` 仍然可访问**。

### 步骤2：构建消息体（图片以 image_url 块嵌入）

```python
content_parts = [
    {"type": "text", "text": f"请按框架协议商品智能审核 Skill 审核以下 GoodsAiAuditRequestDTO，严格按 Skill 输出格式返回 JSON（含 auditResult、auditReason）：\n{payload_text}"}
]
# 主图
for u in req_data.get('imageUrls', []):
    if u: content_parts.append({"type": "image_url", "image_url": {"url": u}})
# 详情图
for u in req_data.get('detailImageUrls', []):
    if u: content_parts.append({"type": "image_url", "image_url": {"url": u}})

body = {
    "assistant_id": "agents-platform",
    "input": {"messages": [{"role": "user", "content": content_parts}]},
    "config": {"configurable": {"agent_id": AGENT_ID, "recursion_limit": 100}},
    "metadata": {"agent_id": AGENT_ID, "graph_id": "agents-platform"}
}
```

### 步骤3：调用审核

```python
resp = api_post(f"{BASE_URL}/threads/{tid}/runs/wait", body, timeout=60)
```

### 步骤4：解析响应（去Markdown围栏）

```python
c = ""  # AI回复文本
for m in reversed(msgs):
    if m.get("type")=="ai" and not m.get("tool_calls"):
        raw = m.get("content","")
        if isinstance(raw, list):
            texts = [b.get("text","") for b in raw if isinstance(b,dict) and b.get("type")=="text"]
            raw = "\n".join(texts)
        c = raw; break

# 去Markdown围栏
clean = c
if "```json" in clean:
    clean = clean.split("```json")[1].split("```")[0].strip()
elif "```" in clean:
    parts = [p for i,p in enumerate(clean.split("```")) if i%2==1]
    if parts: clean = max(parts,key=len).strip()

try:
    pj = json.loads(clean)
    pred = str(pj.get("auditResult","?"))
    reason = pj.get("auditReason","")[:120]
except:
    # 自然语言回退
    ar = "0" if ('不通过' in c[:200] or 'auditResult: "0"' in c) else \
         "1" if ('通过' in c[:200] or 'auditResult: "1"' in c) else "parse_err"
    pred = ar; reason = c[:100]
```

## 结果归一化

```python
def norm(v):
    v = str(v).strip()
    if v in ('-1','0','退回','审核不通过','不通过','智能审核退回','否','FAIL'): return "0"
    if v in ('2','1','通过','审核通过','PASS'): return "1"
    return v
```

新 skill `kjxy-goods-audit-two` 返回格式不统一：有的返回 `"1"`/`"0"`，有的返回 `"PASS"`/`"FAIL"`，需要归一化。

## 线程ID记录（重要！）

**每条审核务必记录 `thread_id`**，否则跑完后无法追溯审核过程。

```python
print(f"tid={tid}")  # 记录到日志
# 在结果中保存
all_results.append({"pred": pred, "tid": tid, ...})
```

运行结束后，可通过 `POST /api/threads/search` 查询线程：

```python
resp = api_post(f"{BASE_URL}/threads/search",
    json.dumps({"agent_id": AGENT_ID, "limit": 200}))
threads = json.loads(resp)  # 返回线程列表
```

⚠️ **已知限制**：`GET /api/threads/{tid}/runs` 返回的 run 中 `output` 字段为空（`{}`），**无法从存储的 run 中获取 AI 回复内容**。审核原因只能在调用时实时获取，过后无法追溯。

## 测试策略

### 每目录5条，品牌不重复

```python
seen = set()
sel = []
for d in items:
    br = d['base_brand']
    if br not in seen or len(sel) < 5:
        if len(sel) < 5:
            sel.append(d)
            seen.add(br)
```

### 超时处理

每条设 60s 超时（urllib.request.urlopen timeout）。超时后记录为 T/O，继续下一条，不阻塞整个目录。

## 常见问题

| 问题 | 原因 | 处理 |
|------|------|------|
| `HTTP 422: Unprocessable Content` | 请求体格式不对 | 检查 `content` 格式：旧版要字符串，新版要数组 |
| `HTTP 404: Thread or assistant not found` | 线程已过期或agent重启 | 重新创建线程 |
| `agent 不存在: XXXX` | Agent ID变更 | 重新 `GET /api/web/agents` 获取新ID |
| `goods_detail_html` 被截断 | CSV导出限制（50字符） | 改用 `audit_request_json.goodsDetailHtml` |
| `output: {}` 空输出 | API不持久化AI回复 | 必须在调用时实时获取，过后无法追溯 |
| Web UI看不到线程 | 线程缺 `agent_id`/`agent_name` 元数据 | 直接URL访问 `?thread_id=`，或创建时加metadata |
| `brandMatch=false` 误判 | 全半角括号归一化未覆盖 | 新skill已改为"辅助信号不终止"，由LLM复核 |

## 测试报告模板

报告需包含以下维度：
1. **汇总**（总样本、一致/不一致、一致率、目录分布）
2. **逐条明细**（含品牌型号、fast/人工/skill三维对比、会话链接）
3. **不一致样本分析**（按目录分组，含会话链接）
4. **排序**（一致率低→高排列，标识重点改善目录）
5. **之前已测目录**（如有）
