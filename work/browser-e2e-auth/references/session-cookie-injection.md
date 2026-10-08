# 会话注入与登录链路侦查（可粘贴片段）

在 `browser_exec` 里直接跑；`cdp(...)`、`js(...)`、`goto_url(...)`、`wait_for_load()` 都是预置 helper。
把 `<host>` 换成目标域（如 `www.example-test.gm`）。

## 1. 判浏览器是否可见

```bash
ps -eo args | grep -i chrom | grep -c -- '--headless=new'   # >=1 = headless，无窗口
```

## 2. 可以复用的“会话就绪”开头（每调用开头都跑一遍）

```python
import json, time
HOST = "www.example-test.gm"
COOKIES = [
    {"name": "Auth", "value": "<token>", "domain": ".example-test.gm", "path": "/", "secure": True, "sameSite": "None"},
    {"name": "Auth", "value": "<another-token>", "domain": ".other-test.gm", "path": "/", "secure": True, "sameSite": "None"},
]

cdp('Security.setIgnoreCertificateErrors', ignore=True)   # 自签证书必须先做

goto_url(f"https://{HOST}/")        # 先落到目标域，建立上下文
wait_for_load()
cdp('Network.setCookies', cookies=COOKIES)   # 批量；单条用 Network.setCookie(**c)

goto_url(f"https://{HOST}/<app-path>")
wait_for_load()
time.sleep(3)
print(js("""JSON.stringify({url: location.href, loginWall: /需要登录|请先登录/.test(document.body.innerText), text: document.body.innerText.slice(0,200)})"""))
```

判定成功 = `loginWall: false` 且正文已是应用界面；`document.cookie` 只能看到非 HttpOnly 的那些，看不到不代表没注入成功。

## 3. 登录墙上的按钮不跳转时，怎么找真实链路

```python
# a) 先在墙上页面装钩子，再点按钮，看它到底发什么
js("""(() => { window.__req=[];
  const _f=window.fetch; window.fetch=function(u,o){window.__req.push('fetch '+u); return _f.apply(this,arguments);};
  const _o=XMLHttpRequest.prototype.open; XMLHttpRequest.prototype.open=function(m,u){window.__req.push('xhr '+m+' '+u); return _o.apply(this,arguments);};
  return 'hooked'; })()""")

# b) 真点击（合成 .click() 偶尔不触发路由，用坐标点击更接近真人）
box = json.loads(js("""(() => {const el=[...document.querySelectorAll('button,a')].find(b=>/登录/.test(b.textContent));
  const r=el.getBoundingClientRect(); return JSON.stringify({x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)});})()"""))
click_at_xy(box["x"], box["y"])
print(js("JSON.stringify({req: window.__req, url: location.href})"))

# c) 登录页常把 OAuth 放跨源 iframe（父页读不到 contentDocument）→ 顶层打开它的 src
oauth = js("document.querySelector('iframe')?.src || ''")
if oauth:
    goto_url(oauth)
```

登录表单读法（顶层打开后就能读）：

```python
print(js("""JSON.stringify({title: document.title,
  inputs: [...document.querySelectorAll('input')].map(i=>i.type+'|'+(i.placeholder||'')),
  tabs: [...document.querySelectorAll('[role=tab],li,span')].map(e=>e.textContent.trim()).filter(t=>/登录$|验证码|证书/.test(t)&&t.length<12)}) """))
```

## 4. 确认“现在是哪个应用/会话在跑”

读应用自己发的请求，比看标题/URL 可信：

```python
js("""(() => { window.__req=[];
  const _o=XMLHttpRequest.prototype.open; XMLHttpRequest.prototype.open=function(m,u){window.__req.push(m+' '+u); return _o.apply(this,arguments);}; return 'hooked'; })()""")
# 触发一次交互（发一条消息/点一个卡片），再读
print(js("JSON.stringify((window.__req||[]).filter(u=>/balance|agent|thread/.test(u)).slice(-5))"))
```

## 5. 证据导出

```python
import os
txt = js("document.body.innerText")
p = os.path.join(os.environ.get("BH_AGENT_WORKSPACE", "."), "trace_step1.txt")
open(p, "w").write(txt)

# 折叠卡片先展开再导，否则证据是空的
print(js("""(() => { let n=0;
  [...document.querySelectorAll('div,button,span')].filter(e=>/^(execute|task|已完成)$/.test((e.textContent||'').trim()) && e.children.length<=1)
    .forEach(e=>{try{e.click(); n++;}catch(err){}}); return 'expanded '+n; })()"""))
```

## 6. 已知边界（别把它当“工具坏了”）

- daemon 空闲重启后是**全新 profile**：Cookie 与 `localStorage` 一起没了 → 回到第 2 节重注；
- 导航会清掉注入的 JS 钩子，所以钩子要“先装后触发”；加载期请求本来就抓不到；
- 自签证书的放开设置也随 daemon 重启失效，每次开头重设。
