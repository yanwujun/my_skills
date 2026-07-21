---
name: ai-audit-regression
description: "框架协议商品智能审核 Skill 回归测试 — 通过 agents-platform API 执行批量/单条审核，对比人工金标准，生成测试报告。"
version: 2.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [qa, testing, api, audit, regression, procurement]
    related_skills: [government-procurement-ops]
---

# AI Audit Skill 回归测试

通过 agents-platform `POST /runs/wait` API 测试框架协议商品智能审核 Skill。数据源：XML 训练数据、audit log、预解析 JSON。对比 AI 预测 vs 人工金标准生成测试报告。

## 前置条件

- agents-platform API: `http://192.168.2.166:30030/agents-platform/api`
- Agent UUID **不固定** — 每次测试前动态获取（见下方 Agent Lookup）
- WSL 访问 192.168.2.166 不稳定，先 `curl` 验证；不通则走 `cmd.exe /c`（见 `references/wsl-windows-gateway.md`）

### 动态 Agent Lookup

```python
import json, urllib.request

def discover_agent(base_url: str) -> tuple[str, str]:
    req = urllib.request.Request(f"{base_url}/web/agents?page=1&page_size=10",
        headers={"Content-Type": "application/json"}, method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        agents = json.loads(resp.read().decode()).get("items", [])
    for a in agents:
        skills = str(a.get("skill_names", []) or [])
        if a.get("enabled") and "kjxy-goods-audit" in skills:
            return a["id"], a.get("skill_names", [None])[0]
    raise RuntimeError("No enabled kjxy-goods-audit agent found")
```

## 审核 Pipeline (Step1–Step7)

```
Step1 品类识别(规则) → Step2 品牌/型号/目录一致性(规则,终止型) → Step3 名称格式(规则)
→ Step4 参数符合性(规则) → Step5 图片合规(规则+LLM) → Step6 详情合规(LLM) → Step7 综合输出
```

Step2 为终止型：`brandMatch=false` / `modelMatch=false` / `catalogMatch=false` 或 `imageCount<3` 触发立即拒绝（<0.1s）。通过 Step2 的商品触发 LLM（30-120s+）。

## 输入数据格式

### XML (Excel Spreadsheet ML, ~300MB)
有表头，JSON 用 `&quot;` 转义。大文件用 streaming 解析（`references/streaming-xml-parsing.md`）。

### CSV (Tab-separated, 无表头)
多行 HTML 字段跨物理行。JSON 用 `\\\"` 转义。关键列：0=protocol_goods_id, 31=audit_request_json, 38=human_audit_result(金标准), 39=training_scenario。

### Audit Log (生产 DB 导出)
`audit_run_record` 表导出，金标准=`resultJson.auditResult`。详见 `references/audit-log-data-source.md`。

### 预解析 JSON (推荐)

| 文件 | Items | 用途 |
|------|:---:|------|
| `test_data_164.json` | 164 | 训练数据，含 training_scenario |
| `test_data_audit_log_103.json` | 103 | 生产 log，含实际审核结果 |

## 图片 URL 构建

数据中的 `imageUrls` 是相对路径。Step5 需要完整外网 URL：

```python
IMG_BASE = "https://www.ccgp-chongqing.gov.cn/djc-gateway/files"
IMG_BUSINESS = "kjxyfile50m"

def make_image_url(path):
    if not path: return path
    path = path.strip().strip('"').strip("'")
    if path.startswith('http'): return path
    # 去掉域名前缀（audit log 数据可能有 //file.ccgp-chongqing.gov.cn/ 前缀）
    path = re.sub(r'^/+file\.ccgp-chongqing\.gov\.cn/', '', path)
    path = re.sub(r'^/+www\.ccgp-chongqing\.gov\.cn/', '', path)
    path = path.lstrip('/')
    fname = path.split('/')[-1] if '/' in path else path
    return f"{IMG_BASE}?filePath={path}&business={IMG_BUSINESS}&fileName={fname}"
```

**⚠️ 注意：** `detailImageUrls` 必须从 `audit_request_json.goodsDetailHtml` 提取（XML 的 `goods_detail_html` 列被截断到 ~50 字符）。

## 金标准规则

| Scenario | 金标准来源 |
|----------|----------|
| `SCENARIO_1_AI_PASS_HUMAN_REJECT` | `human_label` — AI 过、人拒 |
| `SCENARIO_2_AI_REJECT_HUMAN_PASS` | `human_label` — AI 拒、人过（最优先修正） |
| `SCENARIO_3_BOTH_REJECT` | `ai_label` — 双拒 |
| `CONSISTENT_PASS` | `ai_label` — 双过（⚠️ 不等于数据干净，全部 `data_label_fidelity != HIGH`） |
| `AI_ONLY_*` | `ai_label` — 无人审 |

### 结果归一化

```python
def norm_pred(v):
    v = str(v).strip()
    if v in ('-1','0','false','False','FALSE','FAIL','fail','reject','REJECT','no','NO',
             '不通过','审核不通过','退回','智能审核退回'): return "0"
    if v in ('1','2','true','True','TRUE','PASS','pass','yes','YES',
             '通过','审核通过'): return "1"
    if '不通过' in v or '退回' in v: return "0"
    return v  # 标记人工审查
```

### Category 字段修正

测试前必须修正 `audit_request_json.category`（旧数据默认 `"通用货物"` 对家具/车辆/打印机是错的）：

```python
def classify_category(base_catalog):
    if not base_catalog: return "通用货物类"
    if any(k in base_catalog for k in ["打印机","一体机","复印机","碎纸机","扫描仪","投影仪","投影幕","LED显示屏","液晶显示器","销毁设备"]): return "办公设备类"
    if any(k in base_catalog for k in ["办公桌","电脑桌","屏风工位","会议桌","茶几","办公椅","桌前椅","会议椅","折叠椅","沙发","家具","桌类","椅类","屏风"]): return "家具类"
    if "计算机" in base_catalog: return "计算机设备类"
    if any(k in base_catalog for k in ["乘用车","轿车","SUV","越野车","新能源","汽车","客车","货车"]): return "乘用车类"
    if any(k in base_catalog for k in ["服务","咨询","维修","保养","鉴定","会计","法律","工程造价"]): return "服务类"
    return "通用货物类"
```

## API 调用

### 推荐：Stateless `POST /runs/wait`（批量回归）

快速、准确、无线程状态污染。95%+ 准确率。

### 备选：Threaded（需要 Web UI 可追溯时）

```python
# 1. 创建线程
POST /threads  →  {"thread_id": "..."}

# 2. 执行审核（支持 image_url 块嵌入）
POST /threads/{tid}/runs/wait
```

**⚠️ Threaded 模式陷阱：**
- Step2 终止可能失效（LangGraph 状态累积导致继续执行 LLM，产生假阴性）
- 运行间结果不确定（同一数据两次运行结果不同）
- 批量超过 100 次调用后服务器过载返回空响应

**推荐策略：** Phase 1 用 stateless 批量跑 → Phase 2 仅对 mismatched 项用 threaded 重跑获取 session 链接。

### 请求体（image_url 嵌入模式）

```python
content_parts = [
    {"type": "text", "text": f"请按框架协议商品智能审核 Skill 审核以下 GoodsAiAuditRequestDTO，严格按 Skill 输出格式返回 JSON（含 auditResult、auditReason）：\n{payload_json}"}
]
for u in (req_data.get('imageUrls') or []):
    content_parts.append({"type": "image_url", "image_url": {"url": make_image_url(u)}})
for u in (req_data.get('detailImageUrls') or []):
    content_parts.append({"type": "image_url", "image_url": {"url": make_image_url(u)}})
```

### 超时处理

使用 curl subprocess（`--max-time` 比 urllib timeout 可靠）：

```python
def curl_post(url, data, timeout=300):
    tmp_out = f"/tmp/audit_resp_{int(time.time()*1000000)}.json"
    cmd = ["curl", "-s", "-X", "POST", url, "-H", "Content-Type: application/json",
           "-d", data, "--max-time", str(timeout), "-o", tmp_out, "-w", "%{http_code}"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+10)
        if r.returncode == 28: return None, timeout, "timeout"
    except subprocess.TimeoutExpired:
        return None, timeout, "timeout"
    # 读取 tmp_out 返回 content
```

### 响应解析

```python
# 取最后一条无 tool_calls 的 AI 消息
content = last_ai_message["content"]
# 处理 content-as-array（image_url 嵌入时）
if isinstance(content, list):
    content = "\n".join(b.get("text","") for b in content if isinstance(b,dict) and b.get("type")=="text")
# 去 Markdown 围栏
if "```json" in content:
    content = content.split("```json")[1].split("```")[0].strip()
# JSON 解析 + 归一化
pred = json.loads(content)
pred["auditResult"] = norm_pred(pred.get("auditResult",""))
```

## 测试脚本

| 脚本 | 用途 |
|------|------|
| `scripts/run_xml_batch_v2.py` | 全量回归，stateless，支持 --items --timeout |
| `scripts/test_per_catalog.py` | 每目录 3 S2 + 3 CP，双模式（stateless bulk + threaded mismatch re-run） |
| `scripts/test_mismatches.py` | 仅重测已知失败项，threaded，streaming 解析 |
| `scripts/test_json_batch_threaded.py` | JSON 数据源测试，支持 image_url |
| `scripts/test_json_37cat.py` | 37 目录回归，支持断点续传（TXT 增量输出） |
| `scripts/test_remain_stateless.py` | Stateless 重测，支持 skip-set |

## 常见工作流

### A: 全量回归 → `run_xml_batch_v2.py`
```bash
python3 -u scripts/run_xml_batch_v2.py /mnt/d/.../061601.xml --items 5 --timeout 180
```

### B: 每目录对比 + session 链接 → `test_per_catalog.py`
```bash
python3 -u scripts/test_per_catalog.py > /tmp/percat.log 2>&1
```
产出 MD 报告到 `D:\项目\gitlib\智能审核\doc\测试报告_*.md`

### C: 仅重测失败项 → `test_mismatches.py`
编辑 TARGETS 列表 → `python3 -u scripts/test_mismatches.py > /tmp/retest.log 2>&1`

### D: 修改 Skill 后验证（3-5 条） → 即席脚本
```python
data = json.load(open('/mnt/d/项目/gitlib/智能审核/doc/线上数据/test_data_164.json'))
targets = [("A4彩色打印机", "佳能（Canon）"), ...]
# 逐条创建线程 → 执行 → 打印 pred + reason + Web UI 链接
```

## 报告模板

必须包含四部分：

1. **Summary** — 总数/匹配/不匹配/错误，按目录分布
2. **逐条明细** — 三列对比（人工/fast/skill），AI 原审核原因，skill 原因，会话链接
3. **Mismatch 分析** — 根因分类
4. **优化建议**

> ⚠️ 逐条明细必须有，不能只 grep 日志尾部。`/tmp/` 日志会被清理。

## 评价指标

| 指标 | 计算 |
|------|------|
| 总体一致率 | match_count / total |
| 按 Scenario | 分组统计 |
| 按 Catalog | 分组统计 |
| 假拒绝率 | gold=1, pred=0（SCENARIO_2 焦点） |
| 假通过率 | gold=0, pred=1（SCENARIO_1 焦点） |

---

## Pitfalls（集中汇总）

### 调用可靠性
- **Stateless 优于 Threaded** — threaded 有假阴性、不确定、过载问题
- **`ERR(empty)` = 服务器过载** — 立即停，重启 agents-platform
- **`subprocess.TimeoutExpired`** — curl_post 必须 try/except，否则脚本崩溃

### 数据准备
- **detailImageUrls** 从 `audit_request_json.goodsDetailHtml` 提取，不用 XML 列（被截断）
- **imageUrls 域名前缀** — audit log 数据有 `//file.ccgp-chongqing.gov.cn/` 前缀，必须 strip
- **category 字段** — 测试前用 `classifyCategory()` 修正，否则 Skill 用错规则
- **CONSISTENT_PASS 不要按 HIGH fidelity 过滤** — 全部 1,301 条都是非 HIGH

### 编码
- **Windows GBK 崩溃** — 脚本头加 `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')`，cmd 加 `chcp 65001`，避免 emoji

### 批测韧性
- **增量 TXT 输出** — 长批次用 pipe 分隔的 TXT 追加，不用 JSON（崩溃后不可恢复）
- **断点续传** — 记录已完成的目录，跳过重跑

### 特殊数据
- **打印机目录 LLM 重** — 几乎每条都触发 Step5，每条 50-120s
- **家具国标文本** — 含数千字国标的 payload 导致 threaded 挂死，stateless 正常

## References

| 文件 | 内容 |
|------|------|
| `references/audit-log-data-source.md` | 生产 audit log 数据源 schema |
| `references/column-mapping.md` | CSV/XML 列映射 |
| `references/streaming-xml-parsing.md` | 300MB XML streaming 解析 |
| `references/wsl-windows-gateway.md` | WSL→Windows 命令执行 |
| `references/windows-encoding-fix.md` | Windows GBK 编码修复 |
| `references/item-selection-strategy.md` | 品牌去重选样算法 |
| `references/report-output.md` | 报告格式规范 |
| `references/cached-test-data.md` | 预解析 JSON 数据说明 |
| `references/consitent-pass-case-study.md` | CONSISTENT_PASS 案例 |
| `references/furniture-payload-timeout.md` | 家具国标超时处理 |
