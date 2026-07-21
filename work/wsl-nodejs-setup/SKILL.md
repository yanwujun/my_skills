---
name: wsl-nodejs-setup
description: Set up Node.js/NPM projects in WSL — filesystem choice, Docker, registry mirrors, and large-project build optimization. Load this whenever the user asks to install or run a Node.js project in WSL.
triggers:
  - Installing or running a Node.js project in WSL
  - "install this GitHub project"
  - "clone and set up in WSL"
  - npm/pnpm install failures in WSL
  - Slow Gatsby/webpack/Vite builds in WSL
---

# WSL Node.js Project Setup

## 1. Filesystem Choice (MOST IMPORTANT)

**Never put Node.js project files on `/mnt/c/` or `/mnt/d/` (Windows drives).**

WSL accesses Windows filesystems via the 9P protocol translation layer. Every `fs.readFile()` and `fs.writeFile()` crosses the WSL kernel → 9P → Windows NTFS boundary. For projects with many small files (node_modules, Gatsby page-data, webpack chunks), this is catastrophic — builds that should take 30 seconds can take hours.

**Always clone to WSL local ext4: `~/project-name`**

- `~/` = WSL native ext4, fast I/O
- `/mnt/d/` = Windows NTFS via 9P, slow I/O
- Node.js is a Linux binary running on Linux kernel — it has no direct NTFS access
- MongoDB/Docker can stay on Windows (Docker Desktop), just the code files need to be local

If user says "install under Windows," explain that the runtime must be in WSL, and offer to put code on WSL local filesystem (accessible from Windows via `\\wsl$\Ubuntu\home\...`).

## 2. Node.js Version Management (without sudo)

User blocks `sudo` commands requiring password and `curl|bash` patterns. Use `n` via npm:

```bash
npm install -g n
mkdir -p ~/.local/n
N_PREFIX=$HOME/.local/n n <version>   # e.g., n 24
```

The binary lands at `~/.local/n/bin/node`. Prefix all commands:

```bash
PATH=$HOME/.local/bin:$PATH pnpm install
```

Suggest user add to `~/.bashrc`: `export PATH=$HOME/.local/bin:$PATH`

## 3. Docker Desktop + WSL

When Docker Desktop is installed on Windows:

1. Settings → Resources → WSL Integration → enable Ubuntu
2. Docker CLI auto-appears in WSL via `/usr/bin/docker` → symlink
3. If group membership not active: `sg docker -c "docker ps"` (no sudo needed)
4. MongoDB: `sg docker -c "docker run -d --name mongo -p 27017:27017 mongo:8"`

No Docker Engine install in WSL needed.

## 4. NPM Registry Mirror (China)

npmjs.org via proxy often yields ECONNRESET. Switch to npmmirror:

```bash
pnpm config set registry https://registry.npmmirror.com
```

For one-off use: `--registry https://registry.npmmirror.com`

## 5. Large Project Builds (Gatsby / Next.js / Webpack)

For projects that generate thousands of static pages:

- Use partial/selective builds: `FCC_SUPERBLOCK='responsive-web-design' pnpm run develop` (freeCodeCamp)
- Increase Node heap: `NODE_OPTIONS="--max-old-space-size=8192"`
- Disable SSR if not needed: `GATSBY_EXPERIMENTAL_DEV_SSR=false`
- Webpack persistent cache can stall on WSL — if stuck at "webpack.cache" warnings, the process may need more memory or a restart
- Prefer background processes with `notify_on_complete=true` for long-running builds

## 6. pnpm CI Mode

If `pnpm install` prompts about removing modules directory:

```bash
CI=true pnpm install
```

This skips the TTY confirmation check.

## Pitfalls

- Running `bash docker ps` instead of `docker ps` — the `bash` prefix tries to execute the binary as a shell script
- `rm -rf` on WSL home directory files may be blocked by user policy; use `pnpm clean` or CI mode instead
- `/mnt/d/` project clones time out on `git clone` due to filesystem overhead — prefer cloning to `~/`
- Moving directories between `/mnt/d/` and `~/` can time out (cross-fs copy); use `rsync -a --exclude='node_modules'`
