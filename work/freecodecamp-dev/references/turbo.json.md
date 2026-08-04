# turbo.json：开发模式必需透传的环境变量

`turbo develop` 默认只透传 `MONGOHQ_URL`。所有自定义环境变量必须加入 `globalPassThroughEnv`，否则子进程读不到这些变量，导致 `ERR_ASSERTION`。

```json
{
  "$schema": "https://v2-10-0.turborepo.dev/schema.json",
  "globalPassThroughEnv": [
    "MONGOHQ_URL", "HOME_LOCATION", "API_LOCATION",
    "CURRICULUM_LOCALE", "CLIENT_LOCALE", "DEPLOYMENT_ENV",
    "FREECODECAMP_NODE_ENV", "FCC_ENABLE_DEV_LOGIN_MODE",
    "FCC_ENABLE_SWAGGER_UI", "FCC_API_LOG_LEVEL", "FCC_API_LOG_TRANSPORT",
    "AUTH0_CLIENT_ID", "AUTH0_CLIENT_SECRET", "AUTH0_DOMAIN",
    "SESSION_SECRET", "COOKIE_SECRET", "JWT_SECRET",
    "EMAIL_PROVIDER", "STRIPE_SECRET_KEY",
    "SOCRATES_API_KEY", "SOCRATES_ENDPOINT",
    "SHOW_UPCOMING_CHANGES"
  ],
  "tasks": {
    "build": { "dependsOn": ["setup"], "outputs": ["dist/**"] },
    "develop": { "dependsOn": ["setup"], "cache": false, "persistent": true },
    "lint": { "dependsOn": ["setup"] },
    "setup": { "dependsOn": ["^build"] },
    "test": { "dependsOn": ["setup"] },
    "test-content": { "dependsOn": ["setup"] },
    "type-check": { "dependsOn": ["setup"] },
    "//#lint-root": {
      "dependsOn": ["@freecodecamp/shared#build"]
    }
  },
  "remoteCache": { "signature": true }
}
```
