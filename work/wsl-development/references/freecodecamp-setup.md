# freeCodeCamp WSL Setup Reference

## Environment

- Node.js >= 24, pnpm >= 10
- MongoDB (any accessible instance)
- Project cloned to WSL local filesystem (`~/fcc` NOT `/mnt/d/`)

## Quick Start

```bash
# 0. Ensure Node 24
PATH=$HOME/.local/bin:$PATH
node --version  # should be v24.x

# 1. Clone
git clone https://github.com/freeCodeCamp/freeCodeCamp.git ~/fcc --depth 1
cd ~/fcc

# 2. Registry mirror (China)
pnpm config set registry https://registry.npmmirror.com

# 3. Install deps
pnpm install

# 4. Configure env
cp sample.env .env
# Edit .env: MONGOHQ_URL=mongodb://127.0.0.1:27017/freecodecamp?directConnection=true

# 5. MongoDB via Docker Desktop
sg docker -c "docker run -d --name mongo -p 27017:27017 mongo:8"

# 6. Seed data
pnpm run seed

# 7. Start (single superblock for speed — THIS IS THE KEY)
# Without FCC_SUPERBLOCK, Gatsby compiles 19,116 pages → hours/crash.
# With it: ~300 pages → bootstrap in 30s, page-data in <1s.
PATH=$HOME/.local/bin:$PATH \
GATSBY_EXPERIMENTAL_DEV_SSR=false \
FCC_SUPERBLOCK='python-v9' \
NODE_OPTIONS="--max-old-space-size=8192" \
pnpm run develop

# 8. Access
# Browser: http://localhost:8000
# API docs: http://localhost:3000/documentation
```

## Superblock Names

Superblock names DO NOT match the displayed curriculum titles.
Find the correct name by checking `curriculum/challenges/english/certifications/*.yml`:

| Display Name | Superblock (yml basename) |
|---|---|
| Responsive Web Design | `responsive-web-design` |
| JavaScript | `javascript-v9` |
| Front End Development Libraries | `front-end-development-libraries-v9` |
| Python | `python-v9` |
| Relational Databases | `relational-databases-v9` |
| Back End Development and APIs | `back-end-development-and-apis-v9` |
| (legacy) Python for Everybody | `python-for-everybody` |
| (legacy) Scientific Computing with Python | `scientific-computing-with-python` |
| Full Stack Developer | `full-stack-developer-v9` |

**Note:** If you see empty content (0 of 0 steps) after selecting a superblock, you likely used the WRONG name. The correct name is the yml filename without extension.

## Performance Notes

- Full compile (all superblocks): 19116 pages, WSL will hang → **always use FCC_SUPERBLOCK**
- Selective compile (one superblock): ~150-300 pages, bootstrap ~30s, page-data <1s
- `GATSBY_EXPERIMENTAL_DEV_SSR=false` removes SSR overhead, critical for speed
- `NODE_OPTIONS="--max-old-space-size=8192"` prevents webpack cache serialization from stalling
- Webpack first compile still takes 15-30 min but progresses; subsequent runs use `.cache/`
- MongoDB: Docker Desktop works from WSL via `localhost` without extra config
