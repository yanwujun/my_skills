# 一体化 Dockerfile：Node 24 + MongoDB 8 + freeCodeCamp 全量依赖

```dockerfile
FROM node:24-bookworm

# 安装 MongoDB 8.0 + 工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg curl jq \
    && curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | \
       gpg --dearmor -o /usr/share/keyrings/mongodb-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/mongodb-archive-keyring.gpg] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/8.0 main" \
       > /etc/apt/sources.list.d/mongodb-org-8.0.list \
    && apt-get update && apt-get install -y --no-install-recommends mongodb-org \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g pnpm@10

WORKDIR /home/node/fcc
COPY . .

RUN pnpm install --frozen-lockfile --ignore-scripts
RUN cd api && pnpm prisma generate

# 必需环境变量（turbo 开发模式）
ENV CURRICULUM_LOCALE=english
ENV CLIENT_LOCALE=english
ENV SHOW_UPCOMING_CHANGES=false
ENV HOME_LOCATION=http://localhost:8000
ENV API_LOCATION=http://localhost:3000
ENV DEPLOYMENT_ENV=staging
ENV FREECODECAMP_NODE_ENV=development
ENV FCC_ENABLE_DEV_LOGIN_MODE=true
ENV FCC_ENABLE_SWAGGER_UI=true
ENV FCC_API_LOG_LEVEL=info
ENV FCC_API_LOG_TRANSPORT=pretty
ENV MONGOHQ_URL=mongodb://127.0.0.1:27017/freecodecamp?directConnection=true

RUN mkdir -p /data/db

EXPOSE 3000 8000 27017

COPY docker-entrypoint-allinone.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint-allinone.sh

CMD ["/usr/local/bin/docker-entrypoint-allinone.sh"]
```

构建：
```bash
docker build -t fcc-allinone -f Dockerfile.allinone .
```
