#!/usr/bin/env python3
"""
Helper: read_exam_plan.py — determine today's study topic from a markdown plan file.

Usage:
    python3 read_exam_plan.py /path/to/plan.md [today_date]
    
    If today_date omitted, uses current date.
    Supports dates like: 2026-05-07, 5/7, May 7 2026.

Output: JSON with today's topic, week/day info, and remaining days.
"""

import re
import sys
import json
from datetime import date, datetime

def parse_plan(plan_path: str) -> dict:
    """Parse a markdown study plan into a structured schedule."""
    with open(plan_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    plan = {
        "exam_date": None,
        "weeks": [],
        "topics_by_date": {},
    }
    
    current_week = None
    current_week_dates = None
    
    for line in lines:
        line_stripped = line.strip()
        
        # Detect exam date: "考试日期 | **2026-05-23**"
        m = re.search(r'(\d{4}-\d{2}-\d{2})', line)
        if m and "考试" in line and not plan["exam_date"]:
            plan["exam_date"] = m.group(1)
        
        # Detect week headers: "## 第一周" or "## Week 1"
        m = re.search(r'##\s*(第[一二三四五六七八九十]+周|Week\s+\d+|第\d+周)', line)
        if m:
            current_week = m.group(1)
            continue
        
        # Detect date assignments: "### 5/6（周三）" or "### 2026-05-06"
        m = re.search(r'###\s*(\d{1,2})[/.-](\d{1,2})', line)
        if m and current_week:
            month, day = int(m.group(1)), int(m.group(2))
            # Heuristic: if month > 12, it's likely the day first
            if month > 12:
                month, day = day, month
            # Determine year from exam date
            if plan["exam_date"]:
                year = int(plan["exam_date"][:4])
            else:
                year = 2026
            topic = _extract_topic(line, lines[lines.index(line)+1:lines.index(line)+5] if lines.index(line)+5 < len(lines) else [])
            plan["topics_by_date"][f"{year}-{month:02d}-{day:02d}"] = {
                "week": current_week,
                "topic": topic,
                "raw_line": line_stripped,
            }
    
    return plan


def _extract_topic(line: str, next_few: list[str]) -> str:
    """Extract the study topic from a line and its context."""
    # Remove date/emoji prefix
    topic = re.sub(r'^###\s*.*?[—\-]?\s*', '', line).strip()
    # If topic is still a day marker, look at next lines
    if len(topic) < 5 or re.match(r'^[日月一二三四五六七八九十]', topic):
        for nl in next_few:
            nl = nl.strip()
            if nl and not nl.startswith("#") and not nl.startswith("-") and len(nl) > 5:
                topic = nl[:60]
                break
    return topic


def get_today_info(plan_path: str, today_str: str | None = None) -> dict:
    """Get what to study today based on plan."""
    today = date.today() if today_str is None else datetime.strptime(today_str, "%Y-%m-%d").date()
    
    plan = parse_plan(plan_path)
    
    today_key = today.strftime("%Y-%m-%d")
    match = plan["topics_by_date"].get(today_key, {})
    
    # Remaining days
    if plan["exam_date"]:
        exam = datetime.strptime(plan["exam_date"], "%Y-%m-%d").date()
        remaining = (exam - today).days
    else:
        remaining = None
    
    # Get plan for current and next few days
    upcoming = []
    for key in sorted(plan["topics_by_date"].keys()):
        if key >= today_key:
            upcoming.append({key: plan["topics_by_date"][key]})
    
    return {
        "today": today_key,
        "exam_date": plan["exam_date"],
        "remaining_days": remaining,
        "todays_plan": match,
        "todays_week": match.get("week"),
        "todays_topic": match.get("topic"),
        "upcoming": upcoming[:7],  # next 7 days
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 read_exam_plan.py <plan.md> [date]")
        sys.exit(1)
    
    plan_path = sys.argv[1]
    today_str = sys.argv[2] if len(sys.argv) > 2 else None
    
    info = get_today_info(plan_path, today_str)
    print(json.dumps(info, ensure_ascii=False, indent=2))
