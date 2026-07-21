---
name: wsl-project-setup
description: Set up and run large Node.js/JS web projects on WSL with optimal performance — filesystem placement, Docker Desktop integration, build optimization, and toolchain setup.
tags: [wsl, nodejs, docker, performance, gatsby, webpack, filesystem]
---

# WSL Project Setup

When installing or running a large Node.js/JS project (Gatsby, Next.js, webpack-heavy monorepos) on WSL, filesystem placement is the #1 performance factor.

## Trigger

Use this skill when:
- Setting up any Node.js project on WSL that involves heavy I/O (Gatsby, webpack, Next.js, monorepo with many packages)
- A project cloned to `/mnt/d/` or `/mnt/c/` is inexplicably slow
- User says "install to Windows" but the project only runs on Linux

## Core rule: WSL local filesystem over /mnt/

**Rust**
```
# WRONG — /mnt/ runs through 9P protocol translation layer
git clone ... /mnt/d/project

# RIGHT — WSL local ext4, direct kernel I/O
git clone ... ~/project
```

The 9P protocol overhead amplifies with file count. A Gatsby project writing 19,000 page-data.json files on `/mnt/d/` can hang for hours; on `~/` it completes in minutes.

**When to use /mnt/ despite the cost:**
- Small projects with few I/O operations
- Source-only repos (no node_modules, no build output on /mnt/)
- The user explicitly wants Windows-side access via Explorer path

**Windows-side access to WSL files:** VS Code and File Explorer can access `\\wsl$\Ubuntu\home\<user>\project` from Windows.

## Docker Desktop + WSL pattern

```
Docker Desktop (Windows)  ←→  WSL (Linux)
    mongo:8                    freeCodeCamp code on ~/fcc
    localhost:27017  ──TCP──   MONGOHQ_URL=mongodb://127.0.0.1:27017
```

Steps:
1. Install Docker Desktop for Windows (personal use is free)
2. Settings → Resources → WSL Integration → enable for Ubuntu → Apply & Restart
3. Docker CLI auto-appears in WSL via `/mnt/wsl/docker-desktop/cli-tools/usr/bin/docker`
4. If `docker ps` gives "permission denied", use `sg docker -c "docker ps"` (group membership may need refresh)
5. Run MongoDB: `sg docker -c "docker run -d --name mongo -p 27017:27017 mongo:8"`

## Node.js version management without sudo

Use `n` with `N_PREFIX`:

```bash
npm install -g n
mkdir -p ~/.local/n
N_PREFIX=$HOME/.local/n n 24  # or version from .nvmrc
```

Add to `~/.bashrc`:
```bash
export N_PREFIX=$HOME/.local/n
export PATH=$N_PREFIX/bin:$PATH
```

## Build optimization: selective builds

For large projects (freeCodeCamp, large Gatsby sites), compile only what you need:

```bash
# freeCodeCamp: build one curriculum section instead of all 19,000+ pages
FCC_SUPERBLOCK='responsive-web-design' pnpm run develop

# Other flags: FCC_BLOCK, FCC_CHALLENGE_ID
```

This reduces page count from 19,000+ to ~300, bootstrap time from hours to under a minute.

## pnpm: bypass TTY confirmation

When pnpm asks for confirmation in non-interactive shells:

```bash
CI=true pnpm install
```

## Pitfalls

- **"Permission denied" on docker.sock**: User is in `docker` group but current shell session doesn't have it yet. Use `sg docker -c "<command>"` or restart terminal.
- **`/mnt/d/` I/O stall**: Gatsby "Writing page-data.json 1/19116" with no progress for >1 minute = likely 9P overhead. Move to WSL local.
- **`cp -r /mnt/d/project ~/project` times out on node_modules**: Use `rsync -a --exclude='node_modules'` then reinstall deps.
- **pnpm "Aborted removal of modules directory"**: Set `CI=true`.

## References

- [references/freecodecamp-setup.md](references/freecodecamp-setup.md) — Full freeCodeCamp local setup guide with Docker MongoDB, selective builds, and troubleshooting.
