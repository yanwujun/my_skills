# freeCodeCamp Local Setup (WSL)

## Prerequisites

- Node.js >= 24 (check `.nvmrc`)
- pnpm >= 10 (repo uses `pnpm@10.33.3` via `packageManager` field)
- MongoDB (Docker recommended, see below)
- Git

## Setup Steps (WSL)

```bash
# 1. Clone to WSL local filesystem (NOT /mnt/d/)
git clone https://github.com/freeCodeCamp/freeCodeCamp.git ~/fcc --depth 1
cd ~/fcc

# 2. Ensure Node v24+ (via n with N_PREFIX if needed)
node --version  # should be >= 24

# 3. Copy env
cp sample.env .env
# MONGOHQ_URL defaults to mongodb://127.0.0.1:27017/freecodecamp

# 4. Install deps
CI=true pnpm install

# 5. Start MongoDB (Docker Desktop)
sg docker -c "docker run -d --name mongo -p 27017:27017 mongo:8"

# 6. Seed database
pnpm run seed

# 7. Start dev server (selective build for speed)
FCC_SUPERBLOCK='responsive-web-design' pnpm run develop
```

## Large build issue: 9P protocol overhead

freeCodeCamp's Gatsby compilation writes ~19,000 page-data.json files. On `/mnt/d/` (WSL's 9P-mounted Windows drive), each file write crosses the protocol translation layer, making the "Writing page-data.json 1/19116" step appear to hang indefinitely.

### The 9P translation path (slow):
```
Node.js (Linux binary) → WSL Linux kernel → 9P translator → Windows NTFS driver → disk
```

### Direct ext4 I/O (fast):
```
Node.js (Linux binary) → WSL Linux kernel → ext4 driver → disk
```

On WSL local ext4, the same operation completes in minutes instead of hours.

## Selective build flags

| Flag | Effect |
|------|--------|
| `FCC_SUPERBLOCK='responsive-web-design'` | Only build one certification section (~300 pages vs 19,000+) |
| `FCC_BLOCK='basic-html-and-html5'` | Only build one block |
| `FCC_CHALLENGE_ID=646cf6...` | Only build one challenge |

## Access URLs

| Service | URL |
|---------|-----|
| Client (Gatsby dev) | http://localhost:8000 |
| API | http://localhost:3000 |
| API Swagger docs | http://localhost:3000/documentation |

## MongoDB (Docker Desktop on Windows)

The `.env` uses `MONGOHQ_URL=mongodb://127.0.0.1:27017/freecodecamp?directConnection=true`. Docker Desktop's WSL integration auto-forwards ports, so `localhost:27017` works from WSL.

## Troubleshooting

- **"permission denied" on docker.sock**: `sg docker -c "docker ps"`
- **pnpm "Aborted removal of modules directory"**: `CI=true pnpm install`
- **Gatsby stuck at "Writing page-data.json"**: Check if project is on `/mnt/` — move to `~/`
- **Seed times out**: Run seed steps separately: `pnpm seed:surveys && pnpm seed:exams && DEBUG=fcc:* node ./tools/scripts/seed/seed-demo-user`
