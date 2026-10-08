---
name: browser-e2e-auth
description: Use when a browser E2E hits a login wall or captcha.
---

# 带登录态的浏览器 E2E

适用：用 Hermes 浏览器（`browser_exec`）跑内部门户/测试环境的验证、验收、E2E，
而目标站要登录。核心矛盾：**Agent 解不了滑块验证码，而它驱动的浏览器用户往往根本看不见**。

## Step 0：先判“用户看得见这个浏览器吗”（最容易白干的一步）

```bash
ps -eo args | grep -i chrom | grep -c -- '--headless=new'   # >=1 = headless，没有窗口
```

- **≥1（本机默认）**：用户拖不了滑块，说“你手动登录一下”是白等 → 走 Step 2 的 Cookie 注入。
- **0**（有窗口）：可以请用户登录，滑块由用户拖。

先把这条判完再给用户选项：给一个他看不见的窗口让他“配合一下”，是最容易被当成“用户没登”的误判。

## Step 1：自签名证书先放开，再导航

内部测试环境常是自签证书，不放开就停在 privacy error（`chrome-error://chromewebdata/`，页面读不到任何东西）：

```python
cdp('Security.setIgnoreCertificateErrors', ignore=True)
goto_url('https://<host>/')      # 顺序不能反
```

这一步每个新会话都要重做（daemon 重启就失效）。

## Step 2：登录路线（按优先级选）

| 优先级 | 路线 | 适用/代价 |
|---|---|---|
| 1 | 用户给**目标环境**的 Cookie，CDP 注入 | 快、免滑块；需要用户在已登录浏览器里复制 |
| 2 | 短信/邮箱验证码登录（码由用户在 Hermes 弹框里填） | 不用密码、不进对话；比 Cookie 多一步人为 |
| 3 | 启一个可见浏览器并把 Agent 接到它的 CDP | 只在前两条都不通时用；要改配置、更重 |

Cookie 路线的硬性要求：

- **必须来自目标环境**（跨环境 token 会被判 `code:4 请求被拒绝！` 之类的怪错，别当成代码 bug）；
- 同一个站点可能按域名分发**多份同名 cookie**（`.a.gm`、`.b.gm` 各一份）→ 全要，一起注入；
- 注入时 `domain` 带前导点、`path='/'`、`secure=True`，`sameSite` 跟源站一致（源站是 `None` 就写 `'None'`）；
- 应用自己的接口可能还要一个 `Authorization` 头（Cookie 之外）→ 只带 Cookie 可能回 403/“认证服务请求失败”。

具体调用见 `references/session-cookie-injection.md`。

## Step 3：保活会话（漏了它，Step 4/5 全会白跑）

headless daemon 空闲会被回收（`config.yaml` 的 `browser.inactivity_timeout`，默认 120s）。
重启后是**全新 profile**：注入的 Cookie 没了，`localStorage`/`sessionStorage` 也没了 →
再进应用就是**空会话**（历史找不回；`?thread_id=` 之类的查询参数会被前端丢掉，指望它恢复是徒劳）。

规则：

- **每次 `browser_exec` 开头都重注 Cookie + 重新导航**（幂等，成本极低）；
- 真机 E2E **一口气连着做完**，别隔几分钟才发一次调用；或先把 `browser.inactivity_timeout` 调大（如 900）；
- **上下文丢了就别接着写**：空会话上继续做有副作用的操作（下单、提交、写业务表）可能覆盖真实数据，宁可重开一轮。

## Step 4：进目标页 + 确认身份

- 应用入口优先**直连 URL**；很多后台是**路径段决定加载哪个应用/Agent**，走门户再点导航经常切不过去（iframe 的 `src` 在挂载时算一次就定死）。
- 身份/会话别只看标题或 URL，**读应用自己发的 XHR**（如 `…/balance?agent_name=…&agent_id=…`）——那才是当前真正在跑的东西。
- 登录墙的判据是页面文案（如“需要登录 / 请先登录以访问”），注入后要**复核文案消失**，不是假设成功。
- 进不去时先换**入口链路**，不要在墙上的按钮反复点：真实链通常是「门户右上登录 → `/login-app/login` → 该页把 `account.<host>/oauth-login?...` 放在**跨源 iframe** 里」，把那个 iframe 的 `src` 顶层打开最省事。

## Step 5：采证据（否则结论只是你的说法）

- 把页面 `document.body.innerText` **落盘**（`trace_*.txt`），归档到用户定的证据目录；
- 折叠卡片点开再读——折叠态通常只写“已完成”，真正的脚本输出/回报在展开后；
- 抓请求的 JS 钩子（fetch/XHR）必须在**触发操作之前**装：导航会清掉钩子，加载期的请求抓不到就换后续交互的请求来判；
- 报告分 **通过 / 部分通过 / 不通过**，并单列**未验证项**与**阻塞原因**；主动停手（如怕污染数据）要明说是停手，不是失败。

## 反模式

| 反模式 | 后果 | 正确做法 |
|---|---|---|
| 没判可见性就请用户“拖滑块” | 白等，且误判成用户没配合 | Step 0 先跑 `--headless=new` 判定 |
| 用 A 环境的 Cookie 打 B 环境 | 怪错误（鉴权/拒绝），误判成代码 bug | 换环境重新取 Cookie |
| 隔几分钟才发一次调用 | daemon 重启 → Cookie/会话双丢 | 每次开头重注 + 一口气跑完 |
| 拿丢了上下文的会话继续写 | 覆盖/污染真实数据 | 停下来重开一轮 |
| 钩子装晚了就说“没有这个接口” | 结论错误 | 装钩子→再触发操作；或用后续请求佐证 |

## 参考

- Cookie 注入 / 登录链路侦查 / 页面状态读取的可粘贴片段：`references/session-cookie-injection.md`
