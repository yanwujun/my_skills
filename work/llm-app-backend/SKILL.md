---
name: llm-app-backend
description: "LLM 驱动后端应用的开发模式：FastAPI + OpenAI 兼容 API。LLM 输出校验分层、评分一致性、异步任务状态机、持久化复用缓存、pytest 集成测试坑。"
---

# LLM App Backend（LLM 驱动后端应用）

Trigger: 构建调用 LLM 的后端应用（AI 出题 / AI 审核批改 / 内容生成 / 语义判定），Python FastAPI + DeepSeek/OpenAI 兼容 API。沉淀自 smart-learn-app（AI 出题→手机答题→AI 审核）实战。

## 核心原则

- **LLM 输出不可信**：所有 LLM 返回必须过 Pydantic 校验，失败重试（换温度），仍失败置 failed 状态
- **LLM 是生成器，不是计算器**：汇总/评分/一致性由后端重算强校验，绝不信任 LLM 给出的总和
- **AI 调用单出口**：`ai_client.py` 是全项目唯一直接调 LLM 的模块，模型可配置（出题/审核用不同模型）

## 1. AIClient 封装（唯一 AI 出口）

```python
class AIClient:
    def __init__(self, model=None):
        self.client = OpenAI(api_key=KEY, base_url=BASE_URL, timeout=120)
        self.model = model or DEFAULT_MODEL
    def chat_json(self, messages, temperature=0.2, max_tokens=8192, retries=2) -> dict:
        for attempt in range(retries + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model, messages=messages,
                    temperature=temperature, max_tokens=max_tokens,
                    response_format={"type": "json_object"},   # DeepSeek/OpenAI 支持
                )
                return json.loads(resp.choices[0].message.content)
            except Exception as e:
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(...)
```

要点：JSON mode 需要 prompt 里出现 "JSON" 字样；日志记录 prompt_tokens/completion_tokens（成本观测）。

## 2. LLM 输出校验分层（最重要）

**分层设计**（测试失败暴露的真实缺口：选项校验最初只放在 shape 层，schema 层没拦住）：

| 层 | 位置 | 校验内容 | 失败处理 |
|---|---|---|---|
| schema 层 | Pydantic `model_validator(mode="after")` | 字段结构：类型合法、选项数=4、填空禁带选项、必填 | 字段一进来就拒绝 |
| shape 层 | `validate_shape(cfg)` 业务方法 | 数量=配置、题型比例=配置、选项非空 | 重试（换温度） |
| 一致性层 | 后端业务校验 | 评分自洽（correct/score/max_score）、条数=题数、无幽灵 id | 重试或置 failed |

```python
class GeneratedQuestion(BaseModel):
    type: Literal["choice", "fill"]
    options: Optional[list[str]] = None
    @model_validator(mode="after")
    def check_choice_options(self):
        if self.type == "choice" and (not self.options or len(self.options) != 4):
            raise ValueError("选择题选项数必须为 4")
        return self
```

**表格驱动测试**（pytest parametrize）：每种畸形形态一个用例（缺字段/类型错/数量错/比例错/越界/幽灵 id/空集合），预期通过或拒绝。测试失败通常暴露的是**校验层放错位置**，不是测试写错。

## 3. 评分/汇总一致性（审核场景）

- 每项判定带 `correct/score/max_score`，后端校验：`correct=true → score==max_score`，`correct=false → score==0`，`score` 越界先查（顺序：越界→自洽，否则报错语义错位）
- 总分后端 `sum(score)`，不取 LLM 的汇总字段
- 容错判定：选择题集合相等（顺序无关、大小写归一）；填空题交 LLM 判定（近义算对），不字符串比对

## 4. 异步任务 + 状态机 + 轮询

耗时操作（生成 30-60s、审核 10-30s）必须异步，前端轮询：

```
Quiz:     generating → ready → failed（重试耗尽）
Attempt:  submitted → reviewing → done → failed(可 retry 重提)
```

- FastAPI `BackgroundTasks` + 后台函数第一步做状态迁移守卫（`if status != "submitted": return`）
- 状态迁移只允许在 service 层（routers 不直接改 status）
- 失败路径显式：failed 状态可重试（POST retry 重置为 submitted 再入队）
- 轮询接口返回 `{status, data?}`，未就绪不带数据，前端 2s 间隔

## 5. 持久化 + 复用缓存（避免重复调 LLM）

- SQLite 列表结构存 TEXT（JSON 字符串），schemas 层序列化；不引 JSON 列类型
- **同键复用**：`(doc_id, config_json)` 查重，ready/generating 直接返回已有（`{"reused": true}`），不再调 LLM
- **⚠️ 坑：JSON 序列化必须 `sort_keys=True` 且写入/查询两侧一致**。旧数据用无序 `json.dumps(dict)` 存的，新代码 `sort_keys=True` 查询会匹配不上（`{"count":5,"difficulty":"中等","ratio_choice":0.8}` vs `{"count":5,"ratio_choice":0.8,"difficulty":"中等"}`），导致复用失效、白白调一次 LLM。格式变更时注意存量数据兼容
- failed 状态不参与复用（同键重试新建）

## 6. pytest 集成测试坑

**monkeypatch engine 引用点**：各模块 `from ..db import engine` 在 import 时已绑定对象，`monkeypatch.setattr("app.db.engine", test_engine)` 只改 db 模块属性，**已 import 的模块引用不变**。必须逐个 patch 使用模块：

```python
for mod in ("app.db", "app.routers.documents", "app.routers.quizzes",
            "app.routers.attempts", "app.routers.analysis",
            "app.services.quiz_service", "app.services.review_service"):
    monkeypatch.setattr(f"{mod}.engine", test_engine)
```

**异步任务测试**：TestClient 同步执行 BackgroundTasks（响应返回后立即跑），配合 FakeAI 替换 AIClient 类即可无网测试全链路（doc→quiz→attempt→review）。注意未持有 engine 的模块（只收 session 参数的 service）无需 patch。

**测试 DB**：用 `sqlite:///{tmp_path}/test.db` 文件库而非 `:memory:`（BackgroundTasks 跨连接，内存库会丢数据）。

## 7. 其他实战要点

- 上传文件：解析后立即删除临时文件，只留文本入库；白名单扩展名 + 大小上限
- 安全：答案/密钥类字段不随展示接口下发（`GET` 列表响应不带 answer，答案只在审核流）
- prompt 设计：系统提示词明确 JSON 结构 + 业务规则（容错判定/打分规则），用户消息带配置和资料；资料超长截断（出题质量靠分块不靠全文）
- 环境：WSL 项目源码放 ext4（`~/`），禁 `/mnt/`（9P IO 性能灾难）

## 支持文件

- `references/quiz-review-flow.md` — smart-learn-app 完整实战记录（M1 出题链路 / M2 审核链路 / 复用验证 / 测试矩阵）
