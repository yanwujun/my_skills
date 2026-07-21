#!/usr/bin/env python3
"""
软考答题批改脚本 — 批改用户答题结果并制定次日学习任务

用法：
  python3 scripts/grade.py --answers "1A 2C 3B 4D 5A 6B 7C 8D 9A 10C" --case "用户案例分析答案"
  python3 scripts/grade.py --answers "1A 2C 3B 4D 5A 6B 7C 8D 9A 10C" --case "用户案例分析答案" --date 2026-05-06

输出格式：批改结果 + 错题分析 + 明日任务建议
"""
import argparse, json, sys, os
from datetime import datetime, date

# 标准答案模板（实际使用时会被替换）
STANDARD_ANSWERS = {
    "1": "B", "2": "B", "3": "B", "4": "B", "5": "C",
    "6": "A", "7": "D", "8": "A", "9": "C", "10": "D"
}

# 答案解析
ANSWER_EXPLANATIONS = {
    "1": "【B】2NF要求消除非主属性对候选键的部分函数依赖。1NF要求原子性，2NF解决部分依赖，3NF解决传递依赖。",
    "2": "【B】不可重复读。同一事务内两次读取同一行，结果不同（被其他事务修改并提交）。脏读是读到未提交的数据。",
    "3": "【B】数据结构、数据操作、数据约束是数据模型三要素（教材6.1.2节原文）。",
    "4": "【B】概念结构设计阶段使用ER图，独立于具体DBMS。",
    "5": "【C】NoSQL包括键值、列族、文档、图数据库，关系存储属于关系型数据库。",
    "6": "【A】CAP定理中，C=一致性，A=可用性，P=分区容忍性。分布式系统必须满足P，在C和A之间权衡。",
    "7": "【D】MVCC是MySQL InnoDB实现REPEATABLE READ隔离级别的机制。",
    "8": "【A】Cache Aside模式中，更新操作先更新数据库，再删除缓存。",
    "9": "【C】SAAM是SEI提出的软件架构分析方法，侧重可修改性。ATAM更全面，包含SAAM所有内容。",
    "10": "【D】2PC是两阶段提交协议，强调强一致性。TCC/Saga/本地消息表都偏向最终一致性。"
}

# 错题映射到教材章节
ERROR_TOPIC_MAP = {
    "范式": ["范式", "1NF", "2NF", "3NF", "BCNF", "函数依赖", "规范化"],
    "事务与并发": ["事务", "ACID", "脏读", "不可重复读", "幻读", "隔离级别", "锁"],
    "数据模型": ["数据模型", "三要素", "关系代数", "选择", "投影", "连接"],
    "数据库设计": ["ER图", "概念结构设计", "逻辑结构设计", "数据库设计步骤"],
    "NoSQL": ["NoSQL", "键值", "列族", "文档数据库", "图数据库"],
    "CAP理论": ["CAP", "一致性", "可用性", "分区容忍性", "BASE"],
    "缓存": ["缓存", "Cache", "穿透", "击穿", "雪崩", "Redis"],
    "架构风格": ["架构风格", "管道-过滤器", "MVC", "微服务", "SOA", "事件驱动"],
    "质量属性": ["质量属性", "性能", "可用性", "安全性", "可修改性", "SAAM", "ATAM"],
    "软件工程": ["软件开发模型", "测试", "UML", "设计模式", "CMMI"],
    "安全": ["加密", "数字签名", "PKI", "SSL", "DDoS", "安全等级"],
}

def parse_user_answers(raw_text):
    \"\"\"
    解析用户提交的答案，支持多种真实格式。
    
    支持格式：
    - 标准: "1A 2B 3C 4D 5A"
    - 紧凑句点: "1.C2.D3.A4.B5.A6.不清楚7.不清楚8.B9.B10不清楚"
    - 紧凑无分隔: "1A2B3C4D5A"
    - 中文混合: "1.不清楚 2.不会 3.B"
    - 换行分隔: "1A\\n2B\\n3C"
    
    Returns: [(题号, 答案或"不清楚"), ...]
    \"\"\"
    import re
    
    # 第一步：用正则抓取所有 "数字+分隔符+答案" 模式
    # 匹配: 1A, 1.A, 1: B, 10不清楚, 6.不清楚, 2不会
    pattern = re.compile(r'(\d+)\s*[.:、，,，]?\s*([A-Da-d]|不清[楚]?|[不没]会|不知[道]?|不会)', re.UNICODE)
    matches = pattern.findall(raw_text)
    
    if matches:
        # 标准化：统一为"不清楚"
        result = []
        for num, ans in matches:
            ans = ans.upper()
            if ans in ('不清', '不清', '清', '不', '不楚'):
                ans = '不清楚'
            elif ans in ('不会', '不知', '不知道', '不知'):
                ans = '不清楚'
            result.append((num, ans))
        return result
    
    # 第二步：如果第一步没抓到，尝试最宽松的模式——按数字切割
    # 比如 "1A2B3C4D" 这种紧凑无分隔
    tokens = re.split(r'(\d+)', raw_text)
    result = []
    i = 0
    while i < len(tokens) - 1:
        if tokens[i] == '' and tokens[i+1].isdigit():
            num = tokens[i+1]
            # 下一个tokens可能是答案
            for j in range(i+2, min(i+4, len(tokens))):
                ans = tokens[j].strip().upper()
                if ans in ('A','B','C','D','不清楚','不清'):
                    result.append((num, ans if ans == '不清楚' else ans))
                    break
            i += 2
        else:
            i += 1
    return result


def grade_answers(user_answers_str, standard_answers=None):
    \"\"\"批改选择题，支持多种输入格式\"\"\"
    if standard_answers is None:
        standard_answers = STANDARD_ANSWERS.copy()
    
    results = []
    correct_count = 0
    total = 0
    wrong_topics = set()
    
    # 解析用户答案
    items = parse_user_answers(user_answers_str)
    
    if not items:
        # 回退：按空格拆分后逐项解析
        tokens = user_answers_str.strip().split()
        for item in tokens:
            item = item.strip().upper()
            if not item:
                continue
            import re
            m = re.match(r'(\d+)[.:]?\s*([A-Da-d]|不清楚)', item)
            if m:
                items.append((m.group(1), m.group(2) if m.group(2) != '不清楚' else '不清楚'))
    
    for num, user_ans in items:
        standard = standard_answers.get(num, "?")
        total += 1
        
        # "不清楚"一律算错
        if user_ans == '不清楚':
            expl = ANSWER_EXPLANATIONS.get(num, "无解析")
            results.append(f"  ❌ 第{num}题: 未作答(不清楚), 正确答案{standard}")
            results.append(f"     {expl}")
            for topic, keywords in ERROR_TOPIC_MAP.items():
                if any(kw in expl for kw in keywords):
                    wrong_topics.add(topic)
            continue
        
        if user_ans == standard:
            results.append(f"  ✅ 第{num}题: {user_ans} ✓")
            correct_count += 1
        else:
            expl = ANSWER_EXPLANATIONS.get(num, "无解析")
            results.append(f"  ❌ 第{num}题: 你的{user_ans}, 正确答案{standard}")
            results.append(f"     {expl}")
            for topic, keywords in ERROR_TOPIC_MAP.items():
                if any(kw in expl for kw in keywords):
                    wrong_topics.add(topic)
    
    accuracy = correct_count / total * 100 if total > 0 else 0
    
    return {
        "total": total,
        "correct": correct_count,
        "accuracy": accuracy,
        "wrong_topics": wrong_topics,
        "details": results,
        "parsed_answers": [(n, a) for n, a in items]
    }

def grade_case(case_answer):
    """案例分析批改（简化版 — 由LLM判断）"""
    # 这里只是占位，实际由Hermes Agent根据具体题目分析
    return {
        "score": "待批改",
        "feedback": "请将案例分析答案提交后，由软考助手逐条批改",
        "todos": []
    }

def suggest_next_plan(grade_result, current_date_str=None):
    """根据批改结果建议明日计划"""
    if current_date_str:
        d = datetime.strptime(current_date_str, "%Y-%m-%d").date()
    else:
        d = date.today()
    
    accuracy = grade_result["accuracy"]
    wrong_topics = grade_result["wrong_topics"]
    
    suggestions = []
    
    if accuracy >= 90:
        suggestions.append("🏆 正确率优秀！明日可以继续按原计划推进。")
    elif accuracy >= 70:
        suggestions.append("👍 良好，但还有提升空间。明日计划推进的同时，建议留30分钟回顾错题。")
    elif accuracy >= 50:
        suggestions.append("📚 需要加强！建议明日减少新内容，重点复习错题涉及的章节。")
    else:
        suggestions.append("⚠️ 基础较薄弱！建议明日放缓进度，先巩固今天的内容再学新的。")
    
    if wrong_topics:
        topic_str = "、".join(sorted(wrong_topics)[:5])
        suggestions.append(f"📌 需要重点复习的知识领域：{topic_str}")
        suggestions.append(f"🔍 建议查看教材对应章节，做专项练习题巩固。")
    
    # 根据日期动态调整
    exam_date = date(2026, 5, 23)
    remaining = (exam_date - d).days
    
    if remaining <= 5:
        suggestions.append(f"⚡ 距离考试仅剩{remaining}天，建议以模拟题和错题回顾为主，不要贪多。")
    elif remaining <= 14:
        suggestions.append(f"📅 距离考试还有{remaining}天，建议按计划稳步推进，周末做全真模拟。")
    else:
        suggestions.append(f"📅 距离考试还有{remaining}天，时间充裕，可以稳扎稳打。")
    
    return suggestions

def main():
    parser = argparse.ArgumentParser(description="软考答题批改工具")
    parser.add_argument("--answers", help="选择题答案，如 '1A 2C 3B 4D 5A'")
    parser.add_argument("--case", help="案例分析答案文本")
    parser.add_argument("--date", help="答题日期 (YYYY-MM-DD)")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    args = parser.parse_args()
    
    output = {}
    
    if args.answers:
        result = grade_answers(args.answers)
        output["grades"] = result
        
        if not args.json:
            print("=" * 50)
            print(f"📊 选择题批改结果")
            print("=" * 50)
            for d in result["details"]:
                print(d)
            print("-" * 30)
            print(f"总分: {result['correct']}/{result['total']}")
            print(f"正确率: {result['accuracy']:.0f}%")
    
    if args.case:
        case_result = grade_case(args.case)
        output["case"] = case_result
        
        if not args.json:
            print()
            print("=" * 50)
            print("📝 案例分析批改")
            print("=" * 50)
            print(f"评分: {case_result['score']}")
            print(f"反馈: {case_result['feedback']}")
    
    if args.answers:
        suggestions = suggest_next_plan(output.get("grades", {}), args.date)
        output["suggestions"] = suggestions
        
        if not args.json:
            print()
            print("=" * 50)
            print("📅 明日学习建议")
            print("=" * 50)
            for s in suggestions:
                print(f"  {s}")
    
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
