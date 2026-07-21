---
name: wsl-development
description: WSL 本地开发环境配置与项目搭建 — 文件系统性能、Docker Desktop 集成、Node.js 版本管理、大型项目编译优化
trigger: 用户在 WSL 中新建开发项目、项目编译极慢、Docker 权限问题、WSL 相关开发环境问题
---

# WSL Development Environment

WSL 开发环境中最重要的性能规则、工具链配置和常见陷阱。

## 核心规则

### 1. 文件系统铁律

**永远不要在 `/mnt/c/`、`/mnt/d/` 等 Windows 挂载盘上做开发。**

WSL 访问 Windows 文件系统通过 9P 协议翻译层，每次 `fopen()`/`fwrite()` 都要经过 Linux→Windows 语义转换。单次操作开销不大，但密集 I/O（npm install、webpack 编译、Gatsby 生成上千页面）会放大几十到上百倍。

```
NO:  /mnt/d/project
YES: ~/project  （WSL ext4 虚拟磁盘，直通 I/O）
```

IDE 可以通过 `\\wsl$\Ubuntu\home\<user>\<project>` 从 Windows 侧打开编辑。

### 2. Docker Desktop 集成

Docker Desktop for Windows 通过 WSL Integration 在 WSL 内提供 `docker` CLI，无需在 WSL 内安装 Docker。

**首次配置：**
1. 安装 Docker Desktop for Windows
2. Settings → Resources → WSL Integration → 勾选 Ubuntu → Apply & Restart
3. WSL 终端验证：`docker ps`

**常见问题：**
- `command not found` → WSL Integration 未开启
- `permission denied on docker.sock` → 用户已在 docker 组但未重新登录。用 `sg docker -c "docker <cmd>"` 绕过

### 3. Node.js 版本管理（免 sudo）

WSL 中没有预装 nvm，而 `curl | bash` 方式安装 nvm 可能被安全策略拦截。

**使用 `n` 管理版本（通过 npm 安装，无需 sudo）：**
```bash
npm install -g n
mkdir -p ~/.local/n
export N_PREFIX=$HOME/.local/n   # 写入 ~/.bashrc 使其永久生效
n <version>                       # 如 n 24
```

`n` 自动下载二进制包，无需编译，比 nvm 更快。

### 4. 大型前端项目编译优化

像 freeCodeCamp（Gatsby + 19116 页）这类巨型项目在 WSL 上即使用 ext4 也可能极慢。

**优化策略：**
- **限制编译范围：** 用项目提供的环境变量只编译需要的模块
  ```bash
  FCC_SUPERBLOCK='responsive-web-design' pnpm run develop
  ```
  页面数从 19116 → 300，编译快 60 倍

- **增加 Node 内存：** 默认 2GB 不够，加 `--max-old-space-size=8192`

- **禁用实验性 SSR：** `GATSBY_EXPERIMENTAL_DEV_SSR=false` 速度提升明显

- **完整启动命令模板：**
  ```bash
  PATH=$HOME/.local/bin:$PATH \
  GATSBY_EXPERIMENTAL_DEV_SSR=false \
  FCC_SUPERBLOCK='superblock-name' \
  NODE_OPTIONS="--max-old-space-size=8192" \
  pnpm run develop
  ```

### 5. npm 镜像源（中国大陆网络）

npm 官方源有时巨慢，切换到国内镜像：
```bash
pnpm config set registry https://registry.npmmirror.com
```

## Pitfalls

- **`bash docker ps` 报 `cannot execute binary file`：** `bash` 前缀会把 `docker` 二进制当 shell 脚本执行。正确命令是直接 `docker ps`（不加 `bash`）。
- **superblock 名 ≠ 页面显示名：** "Python" 课程实际叫 `python-v9`，"Responsive Web Design" 叫 `responsive-web-design`。在 `curriculum/challenges/english/certifications/*.yml` 找文件名（去 .yml 后缀）。名字错了会显示空内容 "0 of 0 steps"。
- **9P 协议瓶颈：** 所有 `/mnt/` 下的文件操作都走 9P 协议。`pnpm install`、Gatsby 的 `Writing page-data.json`（数万个文件）在 `/mnt/` 下可能从几十秒变成几小时甚至卡死
- **sudo 不可用：** WSL 默认需要密码，无法在自动化中运行。用 `n`（npm 包）管理 Node，用 Docker Desktop 管理服务
- **docker group 未生效：** 新开 WSL 会话需要重新登录才生效。用 `sg docker -c "命令"` 立即生效
- **webpack 5 缓存序列化卡死：** 大量 `ProvidedDependency` 不可序列化警告 + 输出不再增长 = webpack 在死循环重试缓存。增加内存（8GB+ `--max-old-space-size=8192`）+ `GATSBY_EXPERIMENTAL_DEV_SSR=false` 能解决
- **首次编译永远最慢：** Gatsby/webpack 编译后 `.cache/` 目录缓存有效，第二次启动快很多

## 参考文件

- `references/freecodecamp-setup.md` — freeCodeCamp 项目在 WSL 中的完整搭建步骤
