---
name: freecodecamp-dev
description: Run freeCodeCamp locally — WSL host, Docker all-in-one, or Docker infrastructure-only. Covers env vars, turbo pass-through, MongoDB setup, and Gatsby build pitfalls.
disable-model-invocation: false
---

# freeCodeCamp 本地开发

## 前置条件
- Node.js 24, pnpm 10
- MongoDB（副本集模式，`--replSet rs0` + `directConnection=true`）
- 项目路径：`~/fcc`（必须在 WSL ext4，禁放 `/mnt/d/`）

---

## 方案 A：宿主机直接跑（推荐，最快）

```bash
cd ~/fcc
# MongoDB 用 Docker：docker run -d --name mongo -p 27017:27017 mongo:8 mongod --replSet rs0
# 然后初始化副本集（见 references/mongodb-replica-set.md）

# 可选：只编译一个模块（快 10 倍+）
FCC_SUPERBLOCK='responsive-web-design' pnpm develop

# 或完整编译
pnpm develop
```

端口：API `3000`，客户端 `8000`。

---

## 方案 B：Docker 一体化镜像（自含 MongoDB）

镜像 `fcc-allinone:v3`（约 5.8GB）已构建好。一个 `docker run` 全部启动。

```bash
docker run -p 3000:3000 -p 8000:8000 --rm fcc-allinone:v3
```

**已知限制**：Docker Desktop overlay 文件系统写 Gatsby 的 19000+ page-data 文件极慢，客户端（8000 端口）可能卡在 `Writing page-data.json ... 3/19119`。API（3000 端口）不受影响，每次都能正常启动。

### 镜像构成
见 `references/Dockerfile.allinone` 和 `references/docker-entrypoint.sh`：
- 基础：`node:24-bookworm` + MongoDB 8.0 + pnpm 10
- 入口脚本：启动 mongod → 初始化副本集 → `pnpm develop`
- 所有必需环境变量已硬编码在 `ENV` 和入口脚本 `export` 中

### 镜像修改（无需重建，绕过代理拉镜像失败时可用）
```bash
docker run -d --name fcc-tmp fcc-allinone:v3 sleep infinity
docker cp turbo.json fcc-tmp:/home/node/fcc/turbo.json
docker cp new-entrypoint.sh fcc-tmp:/usr/local/bin/docker-entrypoint-allinone.sh
docker commit --change='CMD ["/usr/local/bin/docker-entrypoint-allinone.sh"]' fcc-tmp fcc-allinone:vN
docker rm -f fcc-tmp
```

---

## 必需环境变量

API 在 `api/src/utils/env.ts` 中校验以下变量（开发模式下全部 `assert.ok`）：

| 变量 | 开发模式值 |
|------|-----------|
| `MONGOHQ_URL` | `mongodb://127.0.0.1:27017/freecodecamp?directConnection=true` |
| `HOME_LOCATION` | `http://localhost:8000` |
| `API_LOCATION` | `http://localhost:3000` |
| `CURRICULUM_LOCALE` | `english` |
| `CLIENT_LOCALE` | `english` |
| `DEPLOYMENT_ENV` | `staging` |
| `FREECODECAMP_NODE_ENV` | `development` |
| `EMAIL_PROVIDER` | `nodemailer` |
| `AUTH0_CLIENT_ID` | `dev_client_id`（dummy 即可） |
| `AUTH0_CLIENT_SECRET` | `dev_client_secret` |
| `AUTH0_DOMAIN` | `dev.auth0.com` |
| `JWT_SECRET` | `a_jwt_secret` |
| `COOKIE_SECRET` | `a_cookie_secret` |
| `SESSION_SECRET` | `a_thirty_two_plus_character_session_secret` |
| `STRIPE_SECRET_KEY` | `sk_test_dummy` |
| `SOCRATES_API_KEY` | `dummy_socrates_key` |
| `SOCRATES_ENDPOINT` | `https://localhost:4000` |
| `FCC_ENABLE_DEV_LOGIN_MODE` | `true` |
| `FCC_ENABLE_SWAGGER_UI` | `true` |
| `FCC_API_LOG_LEVEL` | `info` |
| `FCC_API_LOG_TRANSPORT` | `pretty` |
| `SHOW_UPCOMING_CHANGES` | `false` |

---

## turbo.json 透传

`turbo develop` 默认只透传 `MONGOHQ_URL`。所有自定环境变量必须加入 `globalPassThroughEnv`，否则子进程（API、客户端）读不到。

见 `references/turbo.json`。

---

## Docker Desktop WSL 集成注意事项

WSL 内 `docker` 命令依赖 Docker Desktop 的 WSL 集成（`/usr/bin/docker`）。集成断开时（`docker: command not found`），回退到 Windows exe：

```bash
DOCKER="/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe"
"$DOCKER" ps
"$DOCKER" build ...
"$DOCKER" run ...
```

---

## 常见坑

1. **`EBUSY: resource busy or locked, rmdir`** — Docker volume/bind mount 挂到 Gatsby 的 `.cache` 或 `public` 目录，`gatsby clean` 的 `rmdir` 失败。不要挂载这些目录。
2. **`ERR_ASSERTION: process.env.XXX`** — 缺环境变量，对照上表补全。
3. **Gatsby page-data 卡在 3/19119** — Docker overlay I/O 瓶颈，改用宿主机直接跑或 `FCC_SUPERBLOCK` 限制模块。
4. **WSL docker 突然不可用** — Docker Desktop 重启后 WSL 集成可能断开，用 Windows exe 回退。
