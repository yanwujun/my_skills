---
name: gitee-notes-repo
description: "Push personal experiences/summaries to user's Gitee note repository. When user says '记一下这个经验', '帮我存到note仓库', or similar — auto-commit and push to their personal knowledge base."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Gitee, Notes, Git, Personal-Knowledge-Base, Automation]
    related_skills: [github-repo-management]
---

# Gitee Personal Notes Repository

User maintains a personal experience/summary repository on Gitee at `git@gitee.com:shenbufan/note.git`, cloned to `~/note`.

## Trigger Phrases

When the user says anything like:
- "记一下这个经验/总结：..."
- "帮我存到note仓库"
- "提交到仓库"
- "新总结：..."

Proceed with the workflow below. **No need to ask for confirmation** — the user has explicitly requested this be automated.

## Workflow

### 1. SSH Authentication

The SSH key is at `~/.ssh/id_ed25519_gitee` (non-default filename). The `.ssh/config` file **cannot be written** due to Hermes security restrictions, so use one of these methods for any git operation:

**Method A — SSH Agent (preferred for multi-step workflows):**
```bash
# Start agent and add key (session-scoped)
eval $(ssh-agent)
ssh-add ~/.ssh/id_ed25519_gitee
# Then git commands work normally
```

**Method B — GIT_SSH_COMMAND (preferred for single git commands):**
```bash
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_gitee" git push origin master
```

### 2. Add/Update Content

Navigate to `~/note` and determine where the content fits:

```bash
cd ~/note
```

**Repository structure:**
```
~/note/
├── 大家软件/          # Work experience summaries (main target)
│   ├── dev1环境相关.md
│   ├── test1_show环境相关.md
│   ├── 各平台测试账号.md
│   ├── 各平台相关接口.md
│   └── 发布部署经验.md
├── A/                # Another category
├── README.md
└── README.en.md
```

**Rules for file placement:**
- Work/deployment experiences → `大家软件/` directory
- Create a new `.md` file if the topic is distinct from existing files
- Append to existing `.md` file if it's a natural addition to an existing topic
- Use Markdown with `###` headings for each entry

### 3. Commit and Push

```bash
# Git identity
GIT_NAME="凡"
GIT_EMAIL="1043769802@qq.com"

# Stage all changes
git add .

# Commit with descriptive Chinese message
git -c user.name="$GIT_NAME" -c user.email="$GIT_EMAIL" commit -m "新增：<简短描述经验主题>"

# Push (use GIT_SSH_COMMAND since .ssh/config can't be written)
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_gitee" git push origin master
```

### 4. Confirm to User

After successful push, briefly confirm what was pushed so the user knows it's done.

## Commit Message Conventions

| Prefix | Usage |
|--------|-------|
| `新增：` | New experience/note entry |
| `更新：` | Updating existing content |
| `修复：` | Fixing incorrect info |

## Verification

After setup, verify with:
```bash
ssh -i ~/.ssh/id_ed25519_gitee -T git@gitee.com
# Expected: "Hi @shenbufan! You've successfully authenticated..."
```

## Pitfalls

- 🔴 `.ssh/config` **cannot be written** — do NOT attempt to write this file. Always use `GIT_SSH_COMMAND` or `ssh-add` + `ssh-agent`.
- 🔴 The SSH key file is `id_ed25519_gitee`, **not** the default `id_ed25519`. Git will fail with "Permission denied" if the wrong key is used.
- 🔴 SSH agent is **session-scoped** — if multiple git commands are needed across separate tool calls, use `GIT_SSH_COMMAND` per-command instead.
- ✅ If `ssh -T git@gitee.com` works but `git push` fails, the most common cause is the non-standard key filename. Use `GIT_SSH_COMMAND` to fix.
- ✅ If the key was added as a Deploy Key (not account-level SSH key), ensure "允许推送" (write access) is enabled on the repository settings page.
