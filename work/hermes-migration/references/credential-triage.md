# 凭据三审（工作版配置生成）

迁移前必须逐一核对三个文件里的凭据，工作/个人分离。**只打印 key 名和值长度，绝不打印 secret 值。**

## 脱敏审计脚本（可直接改路径复用）

```python
# .env: 只列 key 名 + 长度
for l in open(path, encoding='utf-8').read().splitlines():
    l = l.strip()
    if not l or l.startswith('#'): continue
    if '=' in l:
        k, v = l.split('=', 1)
        print(f'{k} = <有值 len={len(v.strip())}>' if v.strip() else f'{k} = <空>')

# auth.json: credential_pool 结构脱敏
def mask(obj):
    if isinstance(obj, dict):
        return {k: (mask(v) if isinstance(v,(dict,list))
                else ('<secret len=%d>'%len(v) if isinstance(v,str) and len(v)>8
                      and not k.lower() in ('name','username','email','host','url','base_url','model') else v))
                for k,v in obj.items()}
    if isinstance(obj, list): return [mask(x) for x in obj]
    return obj

# config.yaml: 递归找敏感 key（api/token/secret/key/password/auth/credential/cookie）
def walk(obj, path='', out=None, keys=('api','token','secret','key','password','auth','credential','cookie')):
    ...
```

## 判定规则（本用户基准，2026-08）

| 文件 | 个人 → 剔除 | 工作/通用 → 保留 |
|---|---|---|
| `.env` | FIRECRAWL_API_KEY（个人付费 web 工具）、GITHUB_TOKEN | DEEPSEEK_API_KEY（主 LLM，编码 agent 用）、DINGTALK_CLIENT_ID/SECRET（公司钉钉）、QQ_APP_ID/QQ_CLIENT_SECRET/QQBOT_HOME_CHANNEL（审核报告推送渠道）、TERMINAL_*/BROWSERBASE_*/DEBUG 开关（通用） |
| `auth.json` credential_pool | `copilot`（source=gh_cli → GitHub 个人 token）| `deepseek`、`custom:<内网IP>:<port>`（工作环境 LLM 网关，如 192.168.2.18:8080） |
| `config.yaml` | `mcp_servers.worldmonitor`（个人股市）、`secrets.bitwarden`（个人密码库）、`search.firecrawl_api_key` | `mcp_servers.mysql`（工作库连接）、`custom_providers[*]`（内网 provider）、`qq.extra.client_secret`、`platforms.api_server.extra.key`（本地 API server） |

## Git 凭据（一律不迁）

Gitee/GitHub 凭据位置：SSH key `~/.ssh`、gh CLI `~/.config/gh`、git `~/.gitconfig`、`GITHUB_TOKEN`（.env 通常注释掉）。**都不在打包范围**。技能里的推送流程说明（如 gitee-notes-repo）不含凭据，可随包。新机器 Git 凭据需重新配置。

## 致命陷阱：删除 key 后查残留引用

删除 FIRECRAWL_API_KEY 后，config.yaml 的 `web.backend = firecrawl` 仍引用它 → web 搜索会坏。处理：

```python
cfg['web']['backend'] = 'auto'   # 回退到自动选择后端
# 全文件验证（字符串值也要查，不只查 key）
import json
assert 'firecrawl' not in json.dumps(cfg).lower()
```

验证步骤：work-config 生成后 yaml.safe_load 重新读一遍（确认 YAML 有效、顶层键数正常），再 `tar xzf` 解包到 /tmp 实测包内文件确实无个人项，最后才交付。
