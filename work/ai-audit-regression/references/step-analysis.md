# metadata.step 分析

## 概述

LangGraph 执行每个 thread 时会在 checkpoint state 的 `metadata.step` 字段记录当前步数。
该值反映 Agent 走到了多深：
- step=3~9：规则层终止（Step2 品牌/型号不匹配，快速拒绝）
- step=50~70：走到 LLM 图片/详情分析（Step5/6）
- step=80~99：完整走完全流程

## 2026-07-08 统计（185 threads, 184 valid）

| 指标 | 值 |
|------|:---:|
| 最小值 | 3 |
| 最大值 | 99 |
| 平均值 | 50.0 |
| 中位数 | 55 |

分布峰值：step=9 (27次, 14.7%) — Step2 终止最常见

## 查询方法

```bash
# 1. 获取所有 thread
curl -s http://192.168.2.166:30030/agents-platform/api/threads/search \
  -X POST -H "Content-Type: application/json" -d '{"limit":500}' > threads.json

# 2. 逐个获取 state
for tid in $(python -c "import json; [print(t['thread_id']) for t in json.load(open('threads.json'))]"):
  curl -s "http://192.168.2.166:30030/agents-platform/api/threads/$tid/state" \
    | python -c "import json,sys; d=json.load(sys.stdin); print(d.get('metadata',{}).get('step','N/A'))"
done

# 3. 统计
# min, max, avg, distribution
```

## 解读

- **step < 10**: 99% 是 Step2 终止（brandMatch/modelMatch/catalogMatch = false）。响应极快 (< 1s)
- **step 30-70**: 经过了 LLM 调用，但可能提前终止
- **step > 80**: 完整流程，含图片分析 + 详情文本分析
