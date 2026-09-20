---
name: singbox-proxifier-troubleshooting
description: Use when sing-box/Proxifier 代理异常（断网、国内站418、Cursor挂）。
---

# sing-box + Proxifier 代理排查

## 环境结构（用户机器）

```
应用 → Proxifier(SOCKS5 127.0.0.1:8888)  或  Windows系统代理(8888)
     → sing-box(mixed inbound 8888) → 节点(vless REALITY / http)
```

- GUI.for.SingBox 在 `D:\baseSoftware\singbox\`；配置库 `data/profiles.yaml`（GUI 编辑），运行时生成 `data/sing-box/config.json`
- 规则集：远程 `testingcf.jsdelivr.net`（不稳定，7 天缓存）→ 本地副本放 `D:\baseSoftware\singbox\rules\`
- clash API：`http://127.0.0.1:20123`（secret 见 profiles.yaml 的 experimental.clash_api）
- 从 WSL 可直接访问这些端口（WSL→Windows localhost 转发）
- ⚠️ 本机 WSL interop 禁用：不能跑 powershell.exe/reg.exe；`NTUSER.DAT` 被 Windows 独占锁，读不了注册表 → 系统代理状态只能让用户自己看

## 诊断工具（优先用，别猜）

1. **活动连接/规则实况**（最有价值）：
   ```bash
   curl -H "Authorization: Bearer <secret>" http://127.0.0.1:20123/connections
   ```
   每条连接有 `rule`（命中的规则）和 `chains`（出站链）→ 直接看出走没走节点、被哪条规则拦
2. **对比复现**：`curl -x http://127.0.0.1:8888 <url>` vs `curl --noproxy '*' <url>`；状态码/耗时差异即定位（418/超时=走了海外节点被拦；0.1s=直连正常）
3. **DNS 视角**：`curl -s "https://dns.alidns.com/resolve?name=X&type=A"`（国内视角，判断是否国内 IP）
4. **规则集内容验证**（本地 .srs 是 zlib 压缩二进制，strings 搜不到）：
   `https://cdn.jsdelivr.net/gh/v2fly/domain-list-community@master/data/<file>`
   - `cn` = `tld-cn` + `geolocation-cn`（后者又 include 一堆 `category-*-cn`）→ 查域名要顺着 include 链找（例：cursor.sh 在 `category-ai-!cn`→`cursor`）
5. sing-box 日志（GUI 内）开 debug/trace 能看到 `sniffer`、`rule_set` 命中详情

## 五个高频坑

### 1. 开 Proxifier 但没开代理 → 全断网
Proxifier 的 `Default` 规则若指向代理，所有未匹配流量都被送 8888；代理没跑就全断。
**修**：`.ppx` 里 `Default` 改 `Direct`（`%APPDATA%\Proxifier4\Profiles\Default.ppx`，UTF-8 XML，可用 python ET 解析验证），同时启用 `sing-box-latest.exe → Direct`（防代理自身流量环路）。
⚠️ 改 .ppx 必须在 Proxifier 退出时改——它退出时会把内存配置写回覆盖。

### 2. 域名规则对 IP 目标全部失效
Proxifier 的 `AutoModeDetection` 会自己解析域名，SOCKS5 发出去的是 **IP** → sing-box 的 GeoSite/域名规则（含自加的 `cursor.sh`）**统统不命中**，只能靠 IP 规则或 final。
- `ViaProxy`（让 Proxifier 交域名给代理解析）实测被 AutoModeDetection 压制，无效
- 后果：Cursor 这类应用只能靠 `final → 🐟漏网之鱼 → 节点` 兜底 → **final 绝对不能改直连**

### 3. 全局 sniff 规则会破坏 Cursor
`{"action":"sniff","network":"tcp","sniffer":["tls","http","quic"]}` 会缓冲/嗅探**所有** TCP（包括客户端连 127.0.0.1:8888 的本地代理 socket），实测导致 Cursor 网络诊断的 **SSL / Authentication 必失败**。已在用户环境回滚，不要再用。

### 4. 国内网站被 WAF 拦（418 / 风控）
机制：域名**不在 GeoSite-CN 清单** → 不匹配域名直连规则 → 落到 `final → 节点` → 海外 IP 访问国内站 → WAF 拦（本例返回 **418 I'm a teapot**，响应头带 `HWWAFSESID`）。
- 为什么 GeoIP-CN 没救它：sing-box 的 IP 类规则需要目标 IP，**域名目标默认不解析** → IP 规则不匹配
**治本**：在 GeoIP 规则之前插一条无条件 resolve：
```yaml
      - id: ID_rs7k2m4v
        type: inline
        enable: true
        payload: '{}'
        invert: false
        action: resolve
        outbound: ""
        sniffer: []
        strategy: default
        server: ""
```
（GUI 里对应：类型=内联、载荷 `{}`、动作=解析DNS）→ 生成 `{"action":"resolve"}`，实测 djc123.com 418 → 204，且不影响 Cursor。

### 5. GUI 版本兼容
- **<1.26 不支持 file 类型规则集**：直接在 profiles.yaml 写 `type: file` + path，生成 config.json 时 **path 丢失** → 内核启动失败（GUI 也起不来）
- 1.26+ 的本地规则集走两步机制：先在「规则集」页加规则集入库（`data/rulesets.yaml`），再在 profile 路由设置里引用（`type: local` + 规则集 ID）
- 升级方式：GitHub releases `GUI-for-Cores/GUI.for.SingBox` → 解压替换 exe（内存/进程占用时先退出 GUI；exe 可先改名备份）

## 改配置流程（严格遵守）

1. 备份：`cp data/profiles.yaml data/profiles.yaml.bak-<时间>`
2. **让用户完全退出 GUI**（运行中改文件，GUI 退出时会写回覆盖）
3. 改 `data/profiles.yaml`：规则条目字段 `{id, type, enable, payload, invert, action, outbound, sniffer, strategy, server}`；ID 形如 `ID_` + 8 位小写字母数字；规则集引用用规则集 id
4. 验证：`python3 -c "import yaml; yaml.safe_load(open('data/profiles.yaml',encoding='utf-8'))"`；再模拟生成检查（inline 载荷要 `json.loads`）
5. 用户重开 GUI → 启动内核 → 用 clash API + 对比 curl 验证
6. 出问题立刻用备份回滚（cp 回来）

## 已确认结论
- Cursor 靠 `final → 🐟漏网之鱼 → 节点` 兜底（因 Proxifier 发 IP）
- `prod.authentication.cursor.sh` 报 `Failed to fetch` 是 **Cursor 应用层问题**：它发明文 HTTP，而目标 80 端口无服务（HTTPS 443 走代理正常）；与代理配置无关，不影响聊天
- 规则集远程源（jsdelivr）不稳定是"国内网站时好时坏"的诱因之一；resolve 规则可让环境不再依赖域名清单收录完整度
