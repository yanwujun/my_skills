#!/usr/bin/env python3
"""
Daily GitHub skill crawler — lightweight, no full clone.
Uses GitHub API to list files and downloads only skill-relevant files.
"""
import json
import os
import re
import subprocess
import sys
import time
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

# ── Configuration ──────────────────────────────────────────────
SKILLS_REPO = "/mnt/d/平时处理文件/skills"
COLLECTED_DIR = os.path.join(SKILLS_REPO, "collected")
TRACKING_FILE = os.path.join(SKILLS_REPO, ".crawler_tracking.json")

ENV = {**os.environ, "https_proxy": "http://127.0.0.1:8888", "http_proxy": "http://127.0.0.1:8888"}

SEARCH_QUERIES = [
    "awesome cursor rules",
    "cursorrules collection",
    ".cursorrules .mdc",
    "claude skills .claude",
    "CLAUDE.md skills agent",
    "SKILL.md collection agent",
    "mattpocock skills claude",
    "github copilot instructions rules",
    "windsurf rules cascade",
    "openspec rules agent",
    "ai coding agent prompts rules",
    "agent rules prompts collection",
    "cursor rules 中文",
    "AI编程规则",
]

SKILL_TOPICS = {
    "cursorrules", "cursor-rules", "cursor-ai", "claude-code", "claude-skills",
    "ai-agent-tools", "ai-rules", "agent-skills", "coding-agent",
    "prompt-engineering", "rules-for", "context-engineering",
    "ai-coding", "agentic-ai"
}

SKILL_FILE_NAMES = {
    ".cursorrules", "CLAUDE.md", "SKILL.md", "SKILLS.md",
    ".github/copilot-instructions.md", ".windsurfrules",
    ".ai-rules.md", "README.md",
}

SKILL_FILE_DIRS = ["skills", "rules", "commands", "prompts", "cursor-rules", ".cursor/rules", ".claude"]


def curl(url, accept="application/vnd.github.v3+json"):
    try:
        result = subprocess.run(
            ["curl", "-s", "--connect-timeout", "15", "--max-time", "30",
             "-H", f"Accept: {accept}", url],
            capture_output=True, text=True, timeout=35, env=ENV
        )
        return result.stdout.strip()
    except:
        return ""


def search_github(query, per_page=8):
    encoded = quote(query)
    url = f"https://api.github.com/search/repositories?q={encoded}&sort=stars&order=desc&per_page={per_page}"
    resp = curl(url)
    if not resp:
        return []
    try:
        return json.loads(resp).get("items", [])
    except:
        return []


def is_skill_repo(repo):
    name = (repo.get("full_name", "") + " " + repo.get("description", "")).lower()
    topics = set(t.lower() for t in repo.get("topics", []))
    signals = ["cursor", "claude", "skill", "rule", "command", "prompt",
               "agent", "copilot", "instructions", "windsurf", "openspec"]
    has_signal = any(s in name for s in signals)
    has_topic = bool(topics & SKILL_TOPICS)
    skip = ["app", "sdk", "framework", "library", "package",
            "platform", "server", "api gateway", "client sdk",
            "boilerplate", "saas template", "studio"]
    is_app = any(f in name for f in skip)
    return (has_signal or has_topic) and not is_app


def categorize_repo(repo):
    text = (repo.get("description", "") + " " + " ".join(repo.get("topics", []))).lower()
    cats = {
        "software-development": ["code", "coding", "developer", "programming", "java", "python", "typescript", "spring"],
        "devops": ["devops", "deploy", "docker", "kubernetes", "infrastructure"],
        "data-science": ["data", "analytics", "ml ", "ai model", "training"],
        "mlops": ["mlops", "fine-tuning", "llm", "model serving"],
        "productivity": ["productivity", "notion", "docs", "writing"],
        "creative": ["creative", "design", "art", "animation"],
        "media": ["media", "youtube", "audio", "music"],
    }
    for cat, kws in cats.items():
        if any(kw in text for kw in kws):
            return cat
    return "software-development"


def list_repo_tree(full_name):
    owner, repo = full_name.split("/")
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    resp = curl(url)
    if not resp:
        return []
    try:
        data = json.loads(resp)
        tree = data.get("tree", [])
    except:
        return []

    all_files = []
    for item in tree:
        path = item.get("path", "")
        if item.get("type") != "blob":
            continue
        if path in SKILL_FILE_NAMES:
            all_files.append(path)
        elif any(path.startswith(d + "/") for d in SKILL_FILE_DIRS):
            if path.endswith((".md", ".mdc", ".cursorrules", ".txt")):
                all_files.append(path)
        elif "/" not in path and path.endswith(".md") and path not in all_files:
            all_files.append(path)

    return sorted(all_files)[:30]


def download_file(full_name, filepath):
    owner, repo = full_name.split("/")
    # Try main branch first
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{filepath}"
    resp = curl(url, accept="text/plain")
    if not resp or "404: Not Found" in resp:
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{filepath}"
        resp = curl(url, accept="text/plain")
        if not resp or "404: Not Found" in resp:
            return None
    return resp


def load_tracking():
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE) as f:
            return json.load(f)
    return {"repos": {}, "last_run": None}


def save_tracking(tracking):
    os.makedirs(os.path.dirname(TRACKING_FILE), exist_ok=True)
    with open(TRACKING_FILE, "w") as f:
        json.dump(tracking, f, indent=2, ensure_ascii=False)


def main():
    os.makedirs(COLLECTED_DIR, exist_ok=True)
    tracking = load_tracking()
    
    t0 = time.time()
    all_found = {}
    
    for query in SEARCH_QUERIES:
        repos = search_github(query, per_page=8)
        for repo in repos:
            fn = repo["full_name"]
            if fn not in tracking["repos"] and is_skill_repo(repo) and fn not in all_found:
                all_found[fn] = repo
        time.sleep(1.2)

    print(f"Searched {len(SEARCH_QUERIES)} queries, found {len(all_found)} new repos "
          f"({time.time() - t0:.0f}s)")
    
    if not all_found:
        print("No new repos. Up to date.")
        tracking["last_run"] = datetime.now(timezone.utc).isoformat()
        save_tracking(tracking)
        return

    total_files = 0
    new_collected = []
    
    for fn, repo in all_found.items():
        stars = repo["stargazers_count"]
        print(f"  {fn} (★{stars})", end=" ")
        
        files = list_repo_tree(fn)
        if not files:
            print("- no matching files")
            tracking["repos"][fn] = {
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "stars": stars, "skipped": True, "url": repo["html_url"]
            }
            continue

        category = categorize_repo(repo)
        dest = os.path.join(COLLECTED_DIR, category, fn.replace("/", "_"))
        os.makedirs(dest, exist_ok=True)
        
        downloaded = []
        for f in files[:15]:
            content = download_file(fn, f)
            if content and len(content) > 50:
                file_dest = os.path.join(dest, f)
                os.makedirs(os.path.dirname(file_dest), exist_ok=True)
                with open(file_dest, "w", encoding="utf-8") as fh:
                    fh.write(content)
                downloaded.append(f)
                total_files += 1
        
        tracking["repos"][fn] = {
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "stars": stars, "category": category,
            "files": downloaded, "url": repo["html_url"]
        }
        new_collected.append((fn, stars, len(downloaded)))
        print(f"→ {len(downloaded)} files [{category}]")
        time.sleep(0.8)

    tracking["last_run"] = datetime.now(timezone.utc).isoformat()
    save_tracking(tracking)
    
    os.chdir(SKILLS_REPO)
    subprocess.run("git add collected/ .crawler_tracking.json", shell=True, capture_output=True)
    
    status = subprocess.run("git status --porcelain collected/", shell=True, 
                           capture_output=True, text=True)
    if not status.stdout.strip():
        print("No changes to commit.")
        return

    repos_str = ", ".join(f"{n}(★{s})" for n, s, _ in new_collected[:5])
    if len(new_collected) > 5:
        repos_str += f" +{len(new_collected)-5} more"
    msg = f"collect: {len(new_collected)} skill repos [{total_files} files] - {repos_str}"
    subprocess.run(["git", "commit", "-m", msg], capture_output=True, env=ENV)

    # Push (needs GITHUB_TOKEN env var)
    token = os.environ.get("GITHUB_TOKEN", "")
    pushed = False
    if token:
        remote_url = f"https://{token}@github.com/yanwujun/my_skills.git"
        subprocess.run(["git", "remote", "set-url", "origin", remote_url], capture_output=True)
        push_result = subprocess.run(["git", "push", "origin", "master"],
                                     capture_output=True, text=True, timeout=30, env=ENV)
        pushed = push_result.returncode == 0
        subprocess.run(["git", "remote", "set-url", "origin", "git@github.com:yanwujun/my_skills.git"],
                      capture_output=True)
    
    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.0f}s: {len(new_collected)} repos, {total_files} files, "
          f"push={'OK' if pushed else 'FAILED (set GITHUB_TOKEN for auto-push)'}")


if __name__ == "__main__":
    main()
