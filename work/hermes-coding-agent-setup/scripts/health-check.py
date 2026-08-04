#!/usr/bin/env python3
"""Quick health check for all coding agents accessible from Hermes."""
import subprocess
import sys

CHECKS = [
    ("Codex CLI", ["codex", "--version"]),
    ("Codex Auth", ["codex", "login", "status"]),
    ("Claude Code", ["claude", "--version"]),
    ("OpenCode CLI", ["opencode", "--version"]),
    ("OpenCode Auth", ["opencode", "auth", "list"]),
    ("OpenCode Models", ["opencode", "models"]),
]

HERMES_CHECKS = [
    ("Approval Timeout", ["hermes", "config", "get", "approvals.timeout"]),
    ("Command Allowlist", ["hermes", "config", "get", "command_allowlist"]),
]

all_ok = True

print("=== Coding Agent Health ===")
for name, cmd in CHECKS:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        status = "OK" if result.returncode == 0 else f"ERR({result.returncode})"
        print(f"  [{status}] {name}")
        if result.returncode != 0:
            print(f"    stderr: {result.stderr.strip()[:200]}")
            all_ok = False
    except FileNotFoundError:
        print(f"  [MISS] {name} — command not found")
        all_ok = False
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] {name}")
        all_ok = False

print("\n=== Hermes Approval Config ===")
for name, cmd in HERMES_CHECKS:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        print(f"  {name}: {result.stdout.strip()}")
    except Exception as e:
        print(f"  {name}: ERROR — {e}")

sys.exit(0 if all_ok else 1)
