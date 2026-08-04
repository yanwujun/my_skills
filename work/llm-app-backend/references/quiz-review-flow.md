# smart-learn-app 实战记录（M1 出题链路 + M2 审核链路）

项目：`~/smart-learn-app`（WSL ext4）。AI 学习 APP：上传文档 → AI 出题（选择+填空）→ 手机逐题作答（考试/练习双模式）→ AI 审核 → 错题本。

技术栈：FastAPI + SQLModel/SQLite + DeepSeek（deepseek-chat）｜React 18 + Vite + antd-mobile（H5，M3 未开始）。

## M1 出题链路（已验证端到端）

- 文档解析：PyMuPDF(pdf) / python-docx(docx) / txt/md，上传后临时文件立即删除
- 切块：1500 字符 + 200 overlap，优先段落边界
- 异步出题：POST /api/quizzes → 202 + BackgroundTasks → generating → ready/failed
- 校验链：AIClient.chat_json(JSON mode) → QuizGenerationResult.model_validate（schema）→ validate_shape（数量/比例/选项数）
- 验证：5 题真实生成（4 选择+1 填空，round(5*0.8)=4），8 秒完成，题目质量合格；GET 响应无 answer 字段

## M2 审核链路（已验证代码+测试，curl 验证被审批拦截待补）

- Attempt 状态机：exam(submitted→reviewing→done/failed, retry 重置)；practice(创建即 done，逐题 check 判定)
- 审核 prompt：系统提示词含容错规则（填空近义算对）+ 打分规则（score 只能是 0 或 max_score）+ JSON 结构
- 一致性校验：条数=题数、无幽灵 id、max_score=1、correct/score 自洽（**先查越界再查自洽**，否则报错语义错位——测试暴露后调整）
- 练习单题判定：选择题本地集合比对（大小写/顺序容错），填空 LLM 判定
- 错题聚合：仅 done 的 exam attempt；同题去重 + wrong_count + 最近一次答案；错多排前
- 复用：同 doc+config 命中（sort_keys=True 统一），旧数据无序 JSON 导致首次复用失效（踩坑）

## 测试矩阵

| 文件 | 覆盖 | 数量 |
|---|---|---|
| test_schema_validation.py | schema/shape 分层表格驱动（9 用例 parametrize + shape 4 用例） | 13 |
| test_review_scoring.py | 一致性 6 场景 + 选择本地比对 7 场景 | 14 |
| test_analysis.py | 错题聚合去重/过滤/填空 | 4 |
| test_quiz_reuse.py | TestClient + FakeAI 全链路：复用/换配置新建/failed 不复用 | 3 |

共 34 通过。关键坑：engine monkeypatch 引用点、TestClient 同步跑 BackgroundTasks、tmp 文件库。

## 出题 prompt 骨架

```
system: 资深出题专家。题目必须基于资料；选择题单选恰 4 选项；填空答案简洁；
        每题 knowledge_point；必须输出 JSON：{"questions":[{type, stem, options?, answer, explanation, knowledge_point}]}
user: 出题配置：共 N 题，选择题 X 题、填空 Y 题，难度 D。\n\n学习资料：\n{chunks}
```

## 审核 prompt 骨架

```
system: 阅卷专家。填空近义算对；选择题一致才对（多选顺序无关）；
        score 只能 0 或 max_score；correct 与 score 必须自洽；输出 items + weakness。
user: 批改以下 N 题：{题目+标准答案+用户答案 JSON}
```
