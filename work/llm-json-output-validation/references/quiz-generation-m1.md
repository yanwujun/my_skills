# Worked example: smart-learn-app M1 (DeepSeek 出题)

Source session: 2026-08-03, `~/smart-learn-app/server/`. FastAPI + SQLModel + openai SDK (DeepSeek base_url).

## The models (schemas.py)

```python
class GeneratedQuestion(BaseModel):
    """AI 出题输出单题。LLM 返回必须通过本模型校验才落库。"""
    type: Literal["choice", "fill"]
    stem: str
    options: Optional[list[str]] = None
    answer: str
    explanation: str
    knowledge_point: str = ""

    @model_validator(mode="after")
    def check_choice_options(self) -> "GeneratedQuestion":
        """选择题必须恰好 4 个非空选项；填空题禁止带选项。"""
        if self.type == "choice":
            if not self.options or len(self.options) != 4:
                raise ValueError(f"选择题选项数必须为 4，实际 {len(self.options) if self.options else 0}")
            if not all(str(o).strip() for o in self.options):
                raise ValueError("选择题选项不能为空")
        elif self.options is not None:
            raise ValueError("填空题不应包含选项")
        return self


class QuizGenerationResult(BaseModel):
    questions: list[GeneratedQuestion] = Field(min_length=1)

    def validate_shape(self, cfg: QuizConfig) -> None:
        """业务级校验：数量与题型比例符合配置。"""
        if len(self.questions) != cfg.count:
            raise ValueError(f"题目数量 {len(self.questions)} != 配置 {cfg.count}")
        choice_n = sum(1 for q in self.questions if q.type == "choice")
        expected = round(cfg.count * cfg.ratio_choice)
        if choice_n != expected:
            raise ValueError(f"选择题数量 {choice_n} != 期望 {expected}")
```

## Retry loop (quiz_service.py, background task)

```python
for attempt in range(2):  # schema 校验失败重试（换温度）
    try:
        result = _generate_once(messages, 0.2 if attempt == 0 else 0.7)
        result.validate_shape(cfg)
        break
    except Exception as e:
        last_err = e
        logger.warning("出题校验第 %s 次失败: %s", attempt + 1, e)
if result is None:
    raise RuntimeError(f"出题校验连续失败: {last_err}")  # → quiz.status = "failed"
```

## The bug the tests caught (before fix)

Options validation lived ONLY in `validate_shape()`. Consequences:
- `QuizGenerationResult.model_validate({"questions": [choice with NO options ×8, fill ×2]})` → **passed** (options is Optional)
- `model_validate(choice with 2 options)` → **passed**
- Schema-layer test `expect_ok=False` → DID NOT RAISE → 4 test failures

Fix: moved option-structure rules into `GeneratedQuestion.model_validator` (schema layer). All 13 tests passed after also re-splitting test expectations per layer (count mismatch is a SHAPE test, not a schema test).

## Test layout that works

- `TestSchemaValidation.test_payload_validation[payload-expect_ok]` — parametrized 9-row matrix (valid ×2, missing top key, empty list, bad type, missing options, 2 options, empty option, fill-with-options)
- `TestShapeValidation` — count mismatch (11 vs 10), ratio mismatch (9 choice vs expected 8), schema-layer option check, valid-10-passes-shape

## End-to-end check (M1 acceptance)

```bash
curl -s -X POST localhost:8000/api/documents -F 'title=x' -F 'content=<学习文本>'
curl -s -X POST localhost:8000/api/quizzes -H 'Content-Type: application/json' \
  -d '{"doc_id": 1, "config": {"count": 5, "ratio_choice": 0.8, "difficulty": "简单"}}'
# poll:
curl -s localhost:8000/api/quizzes/1   # status: generating → ready; questions WITHOUT answer field
```

Result: 5 questions (4 choice + 1 fill), ratio `round(5*0.8)=4` exact, no answer leakage in client DTO.
