# 容器入口脚本：启动 MongoDB + 初始化副本集 + pnpm develop

```bash
#!/bin/bash
set -e

echo "=== 启动 MongoDB ==="
mongod --replSet rs0 --bind_ip_all --dbpath /data/db --logpath /tmp/mongod.log --fork

echo "=== 等待 MongoDB 就绪 ==="
until mongosh --quiet --eval "db.adminCommand('ping')" > /dev/null 2>&1; do
  sleep 1
done
echo "MongoDB 已启动"

echo "=== 初始化副本集 ==="
mongosh --quiet --eval '
  try {
    rs.initiate({_id: "rs0", members: [{_id: 0, host: "127.0.0.1:27017"}]})
  } catch (err) {
    if(err.codeName !== "AlreadyInitialized") throw err;
  }
'

echo "=== 等待副本集就绪 ==="
until mongosh --quiet --eval "rs.status().ok" | grep -q '^1$' 2>/dev/null; do
  sleep 1
done
echo "副本集已就绪"

echo "=== 启动 freeCodeCamp ==="

# ---- 必需环境变量 ----
export MONGOHQ_URL="mongodb://127.0.0.1:27017/freecodecamp?directConnection=true"
export CURRICULUM_LOCALE=english
export CLIENT_LOCALE=english
export SHOW_UPCOMING_CHANGES=false
export HOME_LOCATION=http://localhost:8000
export API_LOCATION=http://localhost:3000
export DEPLOYMENT_ENV=staging
export FREECODECAMP_NODE_ENV=development
export FCC_ENABLE_DEV_LOGIN_MODE=true
export FCC_ENABLE_SWAGGER_UI=true
export FCC_API_LOG_LEVEL=info
export FCC_API_LOG_TRANSPORT=pretty

# ---- Auth0（开发模式用 dummy 值）----
export AUTH0_CLIENT_ID=dev_client_id
export AUTH0_CLIENT_SECRET=dev_client_secret
export AUTH0_DOMAIN=dev.auth0.com

# ---- Session / JWT ----
export SESSION_SECRET=a_thirty_two_plus_character_session_secret
export COOKIE_SECRET=a_cookie_secret
export JWT_SECRET=a_jwt_secret

# ---- API 校验需要 ----
export EMAIL_PROVIDER=nodemailer
export STRIPE_SECRET_KEY=sk_test_dummy
export SOCRATES_API_KEY=dummy_socrates_key
export SOCRATES_ENDPOINT=https://localhost:4000

exec pnpm develop
```
