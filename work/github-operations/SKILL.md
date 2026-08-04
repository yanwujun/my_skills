---
name: github-operations
description: "Complete GitHub workflow: auth, PR lifecycle, code review, issues, repo management, codebase inspection. One-stop skill for all GitHub operations via gh CLI or git+curl fallback."
version: 1.0.0
author: Hermes Agent (consolidated)
license: MIT
metadata:
  hermes:
    tags: [GitHub, git, PR, code-review, issues, CI, automation, gh-cli]
    related_skills: []
---

# GitHub Operations (Consolidated)

One umbrella skill covering all GitHub operations: authentication, PR lifecycle, code review, issue management, repository management, and codebase inspection. Every section shows the `gh` CLI path first, then the `git`+`curl` fallback.

## Sections

- [Section 1: Authentication Setup](#section-1-authentication-setup) — GitHub auth via token, SSH, or gh CLI
- [Section 2: Pull Request Workflow](#section-2-pull-request-workflow) — branch, commit, PR creation, CI, merge
- [Section 3: Code Review](#section-3-code-review) — local pre-push review, PR review with inline comments
- [Section 4: Issues Management](#section-4-issues-management) — create, triage, label, assign, close issues
- [Section 5: Repository Management](#section-5-repository-management) — clone, create, fork, releases, secrets, Actions
- [Section 6: Codebase Inspection](#section-6-codebase-inspection) — LOC counts, language breakdown with pygount

---

## Section 1: Authentication Setup

Sets up auth for git and GitHub API. Two paths: git-only (HTTPS tokens or SSH) or gh CLI.

### Quick detection

```bash
git --version
gh --version 2>/dev/null || echo "gh not installed"
gh auth status 2>/dev/null || echo "gh not authenticated"
```

### Git-only: HTTPS with Personal Access Token

1. Create token at https://github.com/settings/tokens with `repo`, `workflow` scopes
2. Configure:
```bash
git config --global credential.helper store
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```
3. Test: `git ls-remote https://github.com/<user>/<repo>.git`

### Git-only: SSH Key

```bash
ssh-keygen -t ed25519 -C "your@email.com" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub  # Add at https://github.com/settings/keys
ssh -T git@github.com
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

### gh CLI

```bash
gh auth login                    # Interactive browser
echo "<TOKEN>" | gh auth login --with-token  # Headless
gh auth setup-git                # Configure git creds
```

### Token extraction (for curl API calls)

```bash
# From .git-credentials
grep "github.com" ~/.git-credentials | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|'
# From .hermes/.env
grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2
```

**Support script:** `scripts/gh-env.sh` — sources auth method, user, and repo info.

---

## Section 2: Pull Request Workflow

Full PR lifecycle from branch creation to merge.

### Auth detection (standalone)

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then AUTH="gh"
else AUTH="git"; [ -z "$GITHUB_TOKEN" ] && GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r'); fi
REMOTE_URL=$(git remote get-url origin); OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1); REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

### Branch and commit

```bash
git fetch origin
git checkout main && git pull origin main
git checkout -b feat/add-user-auth
```

Branch naming: `feat/`, `fix/`, `refactor/`, `docs/`, `ci/` + description.

Conventional commits:
```
type(scope): short description

Longer body. Wrap at 72 chars.
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`.

### Create PR

**gh:** `gh pr create --title "feat: ..." --body "## Summary\n..."`

Options: `--draft`, `--reviewer user1`, `--label "bug"`, `--base develop`

**curl:**
```bash
BRANCH=$(git branch --show-current)
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d '{"title":"feat: ...","body":"## Summary...","head":"'$BRANCH'","base":"main"}'
```

### Monitor CI

**gh:** `gh pr checks` or `gh pr checks --watch`

**curl:** Poll commit status:
```bash
SHA=$(git rev-parse HEAD)
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status
```

### Auto-fix CI

1. Get failure details: `gh run list --branch $(git branch --show-current) --limit 5`
2. Fix code with `patch`/`write_file`
3. `git add . && git commit -m "fix: resolve CI failure" && git push`
4. Re-check. Loop up to 3 attempts.

### Merge

**gh:** `gh pr merge --squash --delete-branch`

**curl:**
```bash
curl -s -X PUT -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/merge \
  -d '{"merge_method":"squash","commit_title":"feat: ..."}'
git push origin --delete $BRANCH && git checkout main
```

**References:** `references/conventional-commits.md`, `references/ci-troubleshooting.md`
**Templates:** `templates/pr-body-feature.md`, `templates/pr-body-bugfix.md`

---

## Section 3: Code Review

Review local changes or open PRs.

### Reviewing local changes (pre-push)

```bash
git diff main...HEAD --stat          # Scope
git diff main...HEAD                  # Full diff
git diff main...HEAD -- src/auth.py  # Per file
# Check for issues:
git diff main...HEAD | grep -n "print(\|console\.log\|TODO\|FIXME\|debugger"
git diff main...HEAD | grep -in "password\|secret\|api_key\|token.*="
```

### Review checklist

| Area | Check |
|------|-------|
| **Correctness** | Edge cases, error paths, null handling |
| **Security** | No secrets, SQL injection, XSS, path traversal |
| **Quality** | Clear naming, DRY, single responsibility |
| **Testing** | New paths tested, happy + error cases |
| **Performance** | No N+1, blocking in async, appropriate caching |
| **Docs** | Public APIs documented, README updated |

### Present findings as:
```
## Code Review Summary
### Critical
- **src/auth.py:45** — SQL injection: use parameterized queries
### Warnings
- **src/models/user.py:23** — Plaintext password storage
### Suggestions
- **src/utils/helpers.py:8** — Duplicates logic in core/utils.py:34
### Looks Good
- Clean separation in middleware
```

### Review PR on GitHub

**gh:**
```bash
gh pr view 123; gh pr diff 123; gh pr checkout 123
gh pr review 123 --approve --body "LGTM!"
gh pr review 123 --request-changes --body "See inline comments"
```

**curl — submit review with inline comments:**
```bash
HEAD_SHA=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['head']['sha'])")
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews \
  -d '{"commit_id":"'"$HEAD_SHA"'","event":"COMMENT","body":"Review","comments":[{"path":"src/auth.py","line":45,"body":"SQL injection risk"}]}'
```

Events: `APPROVE`, `REQUEST_CHANGES`, `COMMENT`

### Full PR Review Workflow

1. Set up env: `source "scripts/gh-env.sh"`
2. Gather context: `gh pr view N; gh pr diff N --name-only`
3. Check out: `git fetch origin pull/N/head:pr-N && git checkout pr-N`
4. Read diff + full source files
5. Run automated checks: `python -m pytest`, `ruff check .`
6. Apply review checklist
7. Submit formal review
8. Clean up: `git checkout main && git branch -D pr-N`

**Reference:** `references/review-output-template.md`

---

## Section 4: Issues Management

### View issues

**gh:** `gh issue list`, `gh issue list --label "bug"`, `gh issue view 42`

**curl:**
```bash
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?state=open"
```

### Create issues

**gh:**
```bash
gh issue create --title "Bug: ..." --body "## Description\n..." --label "bug" --assignee "user"
```

**curl:**
```bash
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues \
  -d '{"title":"Bug: ...","body":"## Description\n...","labels":["bug"]}'
```

### Manage

| Action | gh | curl |
|--------|-----|------|
| Add labels | `gh issue edit 42 --add-label "bug"` | `POST /repos/o/r/issues/42/labels` |
| Assign | `gh issue edit 42 --add-assignee user` | `POST /repos/o/r/issues/42/assignees` |
| Comment | `gh issue comment 42 --body "..."` | `POST /repos/o/r/issues/42/comments` |
| Close | `gh issue close 42` | `PATCH /repos/o/r/issues/42 {"state":"closed"}` |

### Triage workflow

1. List untriaged: `gh issue list --label "needs-triage"`
2. Read and categorize each issue
3. Apply labels/priority/assignee
4. Comment with triage notes

**Templates:** `templates/bug-report.md`, `templates/feature-request.md`

---

## Section 5: Repository Management

### Clone

```bash
git clone https://github.com/owner/repo-name.git
gh repo clone owner/repo-name
```

### Create

**gh:** `gh repo create my-project --public --clone`

**curl:**
```bash
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos \
  -d '{"name":"my-project","description":"...","private":false}'
```

### Fork

**gh:** `gh repo fork owner/repo --clone`

**curl:** `POST /repos/o/r/forks` then `git clone` + add upstream remote.

### Settings

| Action | gh | curl |
|--------|-----|------|
| Edit settings | `gh repo edit --description "..."` | `PATCH /repos/o/r` |
| Topics | — | `PUT /repos/o/r/topics` |
| Branch protection | — | `PUT /repos/o/r/branches/main/protection` |

### Releases

**gh:** `gh release create v1.0.0 --title "v1.0.0" --generate-notes`

**curl:** `POST /repos/o/r/releases` then upload assets.

### GitHub Actions

**gh:** `gh workflow list`, `gh run list`, `gh run rerun <ID>`

**curl:** `GET /repos/o/r/actions/workflows`, `POST /repos/o/r/actions/runs/<ID>/rerun`

### Secrets

**gh:** `gh secret set API_KEY --body "value"`

**curl:** Encrypt with repo's public key, then `PUT /repos/o/r/actions/secrets/NAME`

**Reference:** `references/github-api-cheatsheet.md`

---

## Section 6: Codebase Inspection

Analyze repositories for lines of code, language breakdown, and code-vs-comment ratios using `pygount`.

```bash
pip install --break-system-packages pygount 2>/dev/null || pip install pygount
```

### Basic summary

```bash
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build" \
  /path/to/repo
```

### Filter by language

```bash
pygount --suffix=py --format=summary .    # Python only
pygount --suffix=py,yaml,yml --format=summary .
```

### Output formats

- `--format=summary` — summary table (recommended)
- `--format=json` — machine-readable

### Pitfalls
- Always exclude `.git`, `node_modules`, `venv` to avoid slowdowns
- Markdown shows 0 code lines (classified as comments)
- For JSON line counts, use `wc -l` directly

---

## Pitfalls

### Mixed remote identities (Gitee + GitHub / multi-account)
Users with both Gitee (SSH) and GitHub accounts commonly hit auth issues when pushing to a new GitHub remote from a headless/WSL environment:
- Gitee SSH key (`~/.ssh/id_ed25519_gitee`) does not work with GitHub
- GitHub HTTPS push in headless/WSL fails with `"No such device or address"` because there's no TTY to prompt for username/password
- No credential helper may be configured
- **Different accounts may have different git identity** (user.name / user.email) — never reuse the Gitee identity for GitHub.

**First step — verify platform and identity:**
1. **Ask which platform** (Gitee vs GitHub vs GitLab) before generating keys, setting remotes, or configuring identity.
2. **Check git identity**: `git config user.name` and `user.email` may differ per platform. GitHub pushes should use the GitHub account's name/email, not the one from note/Gitee repos.
3. **Memory may hold multi-account info** — check `memory` or `user` profile for per-platform identity before assuming.

**WSL behind HTTP proxy — diagnostics (common corporate/office network):**

```bash
# 1. Check proxy env
env | grep -i proxy

# 2. Test SSH (port 22) — often blocked by corporate proxies
ssh -o ConnectTimeout=10 -T git@github.com
# → "Connection timed out" = SSH blocked, need HTTPS

# 3. Test HTTPS through proxy
http_proxy=http://127.0.0.1:8888 https_proxy=http://127.0.0.1:8888 \
  curl -sI https://github.com -o /dev/null -w "HTTP %{http_code}"
# → "HTTP 200" = HTTPS works through proxy
```

If SSH hangs/times out but HTTPS works, **do not waste time on SSH tunnel workarounds** — go straight to HTTPS+token.

**Fix paths (in order of reliability for WSL+proxy):**

1. **HTTPS + Personal Access Token (MOST RELIABLE under proxy):** Ask for a GitHub PAT (classic, scope: `repo`) and push with proxy:
   ```bash
   git remote set-url origin https://<token>@github.com/user/repo.git
   git -c http.proxy=http://127.0.0.1:8888 push -u origin main
   ```
   To make the proxy persistent per-repo:
   ```bash
   git config http.proxy http://127.0.0.1:8888
   ```

2. **Generate a dedicated GitHub SSH key** (for networks where port 22 is open):
   ```bash
   ssh-keygen -t ed25519 -C "github-$(whoami)" -f ~/.ssh/id_ed25519_github -N ""
   cat ~/.ssh/id_ed25519_github.pub  # Add at https://github.com/settings/keys
   ```
   Configure `~/.ssh/config`:
   ```
   Host github.com
       HostName github.com
       User git
       IdentityFile ~/.ssh/id_ed25519_github
       IdentitiesOnly yes
   ```
   Or use `GIT_SSH_COMMAND`:
   ```bash
   GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_github" git push -u origin main
   ```
   **Caveat:** SSH uses port 22, which may be blocked by HTTP proxies. If SSH hangs/times out, go straight to fix path 1 (HTTPS+token). SSH-over-HTTP proxy tunnels (`nc -X connect`) can work as a last resort but are less reliable — see the dedicated subsection below.

3. **Set up `gh` CLI:** `gh auth login` for the simplest path, then `gh auth setup-git` to configure git creds automatically. Note: `gh` also needs HTTPS access through the proxy.

**Fix path 4 (last resort — SSH over HTTP proxy with nc):** If HTTPS is also blocked or token scopes are insufficient, tunnel SSH through the corporate HTTP proxy:
```bash
GIT_SSH_COMMAND='ssh -o "ProxyCommand=nc -X connect -x 127.0.0.1:8888 %h %p" \
  -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15' git push -u origin main
```
- Requires `nc` with `-X` support (OpenBSD netcat)
- First push needs `StrictHostKeyChecking=accept-new` to accept GitHub's host key
- This is less reliable than HTTPS+token — expect possible timeouts on slow connections

### Author identity unknown
Must set `git config user.name` and `user.email` before first commit, either globally or per-repo.

### HTTPS + no TTY
`fatal: could not read Username` means no credential helper and no TTY for interactive auth. See fix paths above.

### SSH permission denied
`Permission denied (publickey)` — wrong SSH key being tried. Check `ssh -vT git@github.com` and use `GIT_SSH_COMMAND` or `~/.ssh/config` to select the correct key.

## Common Prerequisites

For all sections, ensure:
```bash
command -v gh &>/dev/null && gh auth status &>/dev/null && echo "gh ready"
# or
[ -n "$GITHUB_TOKEN" ] && echo "token ready"
git config --global user.name    # Must be set
git config --global user.email   # Must be set
```