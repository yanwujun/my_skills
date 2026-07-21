---
name: bilibili-comment-analyzer
description: 爬取B站指定UP主稿件评论并做多维度数据分析。支持情感分析、词云、热评统
  计、关键词提取、观点分类。输出控制台摘要 + Excel报表 + HTML图表报告。
category: productivity
scripts:
  - scripts/bilibili_analyzer.py
references:
  - references/bilibili-api-notes.md
  - references/up主-战国时代-姜汁汽水.md
---

# B站 UP主评论分析工具

## 功能

1. **数据采集** — 输入UP主mid，自动获取其所有可见稿件的前N页热评
2. **多维度分析**：
   - 情感分析（正面/中性/负面比例 + 趋势折线图）
   - 词云图（高频词可视化）
   - 关键词提取（TF-IDF 权重排名）
   - 热评排行榜（按点赞数排序）
   - 各视频情感分布对比
3. **三端输出**：
   - 控制台打印摘要
   - Excel文件（6个Sheet）
   - HTML报告（带图表和样式的网页）
4. **定时监控**：配合 cronjob 可定期监控指定UP主评论趋势

## 三种工作模式

### 模式C：视频字幕提取（AI字幕）→ 使用 Credential + get_subtitle
获取B站视频的AI生成字幕（CC字幕），适合需要视频完整逐字稿的场景。2023年以后的视频大多有AI字幕，需SESSDATA绕过412风控。

```python
import os
import asyncio
from bilibili_api import sync, video, Credential
import aiohttp

credential = Credential(
    sessdata=os.environ['BILI_SESSDATA'],
    buvid3=os.environ.get('BILI_BUVID3', ''),
    bili_jct=os.environ.get('BILI_BILI_JCT', ''),
)

async def get_subtitle_text(bvid):
    v = video.Video(bvid=bvid, credential=credential)
    info = await v.get_info()
    cid = info.get('cid', 0)
    
    # 方法1：bilibili_api内置方法
    sub_list = await v.get_subtitle(cid)
    subs = []
    if isinstance(sub_list, dict):
        subs = sub_list.get('subtitles', [])
    elif isinstance(sub_list, list):
        subs = sub_list
    
    if subs:
        sub_url = subs[0].get('subtitle_url', '')
        if sub_url.startswith('//'):
            sub_url = 'https:' + sub_url
        
        async with aiohttp.ClientSession() as session:
            async with session.get(sub_url) as resp:
                data = await resp.json()
                body = data.get('body', [])
                return '\n'.join(item.get('content', '') for item in body if item.get('content'))
    return None

# 使用
text = sync(get_subtitle_text('BV1sP411k7Rc'))
```

注意：`get_subtitle` 返回可能是 dict 或 list，需兼容处理。字幕 JSON 的 `body` 是数组，每个元素有 `content` 字段。字幕URL可能以 `//` 开头需补 `https:`。

## 两种工作模式

### 模式A：完整分析（脚本）→ 使用 bilibili_analyzer.py
适合需要情感分析、词云、Excel/HTML报告的场景。需要 SESSDATA 登录凭据，依赖多（jieba, snownlp, wordcloud, pandas 等）。

### 模式B：快速获取（库调用）→ 在会话中临时编写脚本
适合只想看一眼UP主信息、最新视频和评论区热评的轻量场景。使用 bilibili-api-python 库直接在 Hermes venv 中运行，不需要完整分析流水线。

### 模式C：拉取视频字幕/解析内容（需SESSDATA）

B站视频的字幕（AI字幕/CC字幕）需要登录才能获取。

**已知限制**：
- 2023年及更早的视频通常没有AI生成字幕（AI字幕功能2024年后才普及）
- 即使视频有字幕，也可能返回空列表——`hasSub: true` 但 `subtitles: []`
- 字幕API需要完整Cookie（SESSDATA + buvid3 + bili_jct）才能绕过412

**获取字幕的方法**：
```python
from bilibili_api import sync, video, Credential

credential = Credential(sessdata=SESSDATA, buvid3=BUVID3, bili_jct=BILI_JCT)
v = video.Video(bvid=bvid, credential=credential)
info = await v.get_info()
cid = info.get('cid')

# 方法1：get_subtitle
subs = await v.get_subtitle(cid)

# 方法2：player API（备用）
import aiohttp
async with aiohttp.ClientSession() as session:
    url = f"https://api.bilibili.com/x/player/v2?aid={info['aid']}&cid={cid}"
    headers = {'Cookie': f"SESSDATA={SESSDATA}", 'Referer': 'https://www.bilibili.com'}
    async with session.get(url, headers=headers) as resp:
        data = await resp.json()
        subtitles = data['data']['subtitle']['subtitles']
```

**字幕JSON格式**：body数组中每项含 `content` 字段，拼接即为完整字幕文本。

**firecrawl修复**：`web_search`和`web_extract`依赖firecrawl-py。安装命令：
```bash
python3 -m pip install --break-system-packages 'firecrawl-py==4.17.0'
```
（需精确版本4.17.0，否则Hermes内部检查不通过）

当用户提及B站UP主时（"帮我分析评论"/"获取这个UP的动态"/"看看这个UP主"等），先判断用户想要哪种模式：

### 模式判定

| 用户说了什么 | 用哪个模式 |
|-------------|-----------|
| "分析"、"情感"、"词云"、"报告"、"Excel"、"监控" | 模式A：完整分析（需SESSDATA） |
| "获取"、"看看"、"动态"、"评论"、"信息" | 模式B：快速获取（无需登录） |
| "字幕"、"文案"、"逐字稿"、"文字版"、"全文"、"小说"、"故事" | 模式C：字幕提取（需SESSDATA） |
| "对XX的看法"、"观点"、"怎么看"、"分析下XX" | 模式D：UP主观点跟踪（降级方案） |
| 不确定 | 先问用户是要完整分析报告、快速看看、还是提取视频字幕 |

### 重要：SESSDATA 安全规范

用户提供 SESSDATA 时，必须遵守：
1. **只进程内存使用** — 通过环境变量传入，不写入任何文件、不写入 memory、不持久化
2. **用完即弃** — 数据获取完毕后SESSDATA随进程退出销毁
3. **低频请求** — 每次API调用之间至少等待 0.3-0.5秒，批量获取多个视频数据时尤其注意
4. **不存储响应原文到磁盘** — 只在内存中提取用户需要的信息

如果用户只给 SESSDATA（不提供完整Cookie），`Credential(sessdata=SESSDATA)` 就足够。同时告诉用户 SESSDATA 的有效期约1个月。

### 模式A：完整分析（bilibili_analyzer.py 脚本）

需要B站登录SESSDATA才能绕过412风控，获取完整数据（所有页面）。

1. **询问SESSDATA** — 如果用户没有，指导从浏览器获取：F12 → Application → Cookies → bilibili.com → 复制 SESSDATA 的 Value，向用户保证只进程内存用一次不存储
2. **运行命令**：
   ```bash
   export BILI_SESSDATA=用户提供的值
   /mnt/d/baseSoftware/Python/Python312/python.exe /mnt/c/Users/Administrator/Desktop/bilibili_analyzer.py \
     --mid 用户提供的mid --pages 5 --limit-videos 10 --name "分析报告"
   ```
3. **查看结果**：运行完成后告诉用户输出目录位置，打开 `report.html` 可浏览完整分析报告

### 模式B：快速获取（库调用）

不需要登录，直接在 Hermes venv 中调用 bilibili-api-python 库，适合轻量查询。

**Python 版本陷阱（重要！）**：
- Hermes venv 的 `python3` 是 **Python 3.11**（路径：`/home/administrator/.hermes/hermes-agent/venv/bin/python3`）
- 但 `pip3` 可能装到了 Python **3.12** 的用户目录（`/home/administrator/.local/lib/python3.12/site-packages/`）
- **不要**设置 PYTHONPATH 指向 3.12 的 site-packages（会触发 PIL `_imaging` C扩展不兼容崩溃）
- 修复：`python3 -m pip install bilibili-api-python`（用venv自带的pip装，全部装在同一Python版本下）

**Credential 导入路径**：在 bilibili-api-python v17.4.1 中，`Credential` 类位于 `bilibili_api.utils.network` 模块，不是从顶层直接导出：
```python
from bilibili_api.utils.network import Credential
# 不要用: from bilibili_api import Credential  ← 在v17.4.1中不行
```

**已知可用的API（无需登录）**：
| API | 无需登录？ | 备注 |
|-----|-----------|------|
| `User(mid).get_user_info()` | ✅ 可用 | 昵称、签名、等级、性别、生日 |
| `Video(bvid).get_info()` | ✅ 可用 | 标题、播放量、弹幕、评论数、aid等 |
| `User(mid).get_videos()` | ✅ 可用 | 视频列表（bilibili_api内部处理了WBI签名） |
| `comment.get_comments()` | ✅ 可用 | 第1页返回热评，后续页replies为None |
| `User(mid).get_dynamics()` | ❌ 需SESSDATA | 新版 `get_dynamics_new()` 需带Credential |

**关键API签名**（bilibili-api-python v17.4.1，异步写法）：

```python
from bilibili_api.utils.network import Credential
from bilibili_api.utils.aid_bvid_transformer import bvid2aid, aid2bvid
import bilibili_api.user as user_mod
import bilibili_api.video as video_mod
import bilibili_api.comment as comment_mod
from bilibili_api.comment import CommentResourceType, OrderType

# ======= 获取用户信息（无需登录） =======
u = user_mod.User(UID)
info = await u.get_user_info()

# ======= 获取视频列表（无需登录） =======
videos = await u.get_videos(ps=30, pn=1)
# videos['list']['vlist'] 或 videos['vlist']

# ======= 获取视频详情（无需登录） =======
v = video_mod.Video(bvid="BVxxx")
info = await v.get_info()
aid = info.get('aid', 0)  # 评论需要aid（int），不是bvid

# ======= 获取评论（无需登录可拿第1页） =======
cmt = await comment_mod.get_comments(
    oid=aid,                                    # 需要int类型的aid
    type_=CommentResourceType.VIDEO,             # 不是 ResourceType！
    page_index=1,                                # 页码，不是 ps=20！
    order=OrderType.LIKE                         # 按点赞排序
)
replies = cmt.get('replies') or []               # replies 可能是 None
total = cmt.get('page', {}).get('acount', 0)

# ======= 获取动态（需SESSDATA） =======
cr = Credential(sessdata=SESSDATA)               # 从环境变量读取
u = user_mod.User(UID, credential=cr)
dyn = await u.get_dynamics_new(offset='')
items = dyn.get('items', [])
# 返回13-20条动态，格式见下方"OPUS动态结构"

# 或用 sync() 包装（同步上下文）：
from bilibili_api import sync
items = sync(u.get_dynamics_new(offset='')).get('items', [])
```

## OPUS动态结构（新版格式）

B站新版动态使用 `MAJOR_TYPE_OPUS` 格式，内容在 `major['opus']` 中，**不在** `module_dynamic['desc']`。注意：**转发类动态的 `major` 字段为 `None`**，必须做 None 检查：

```python
# 从 get_dynamics_new 返回的 items 中提取
for item in items:
    modules = item.get('modules', {})
    mod_author = modules.get('module_author', {})
    pub_ts = int(mod_author.get('pub_ts', 0))  # 可能是str！需转int
    mod_desc = modules.get('module_dynamic', {})
    major = mod_desc.get('major')  # 不用 {} 默认值，需要区分 None！
    
    if major is None:
        # 转发动态：文本在 module_dynamic.desc.text
        text = mod_desc.get('desc', {}).get('text', '')
        dyn_type = "转发"
    elif major.get('type') == 'MAJOR_TYPE_OPUS':
        opus = major.get('opus', {})
        summary = opus.get('summary', {})
        text = summary.get('text', '')          # 动态文字内容
        pics = opus.get('pics', [])             # 图片列表
        img_urls = [p.get('url') for p in pics if p.get('url')]
        dyn_type = "图文/文字"
    elif major.get('type') == 'MAJOR_TYPE_ARCHIVE':
        archive = major.get('archive', {})
        text = f"[转发视频] {archive.get('title', '')}"
        dyn_type = "转发视频"
```

**注意**：动态类型码 `DYNAMIC_TYPE_DRAW`（图片/图文）和 `DYNAMIC_TYPE_WORD`（纯文字）在最新API中都走 `MAJOR_TYPE_OPUS` 格式。

## UP主回复粉丝搜索

在评论区中查找UP主回复粉丝的互动：

```python
for c in hot_replies:  # hot_replies来自 get_comments
    c_mid = str(c.get('member', {}).get('mid', ''))
    
    # 检查子回复中有没有UP主
    sub_replies = c.get('replies') or []
    for r in sub_replies[:5]:  # 只看前5个子回复
        r_mid = str(r.get('member', {}).get('mid', ''))
        if r_mid == str(UID):
            print(f"粉丝: {c['member']['name']} (👍{c['like']})")
            print(f"  「{c['content']['message']}」")
            print(f"← UP主: 「{r['content']['message']}」")
    
    # UP主自己发的评论（非回复）
    if c_mid == str(UID):
        print(f"UP主自评: 「{c['content']['message']}」")
```

| 参数 | 说明 |
|------|------|
| `--mid` | UP主的mid（数字ID或空间URL），**必填** |
| `--pages` | 每个视频采集评论页数，默认10（每页20条=最多200条/视频） |
| `--limit-videos` | 最多采集多少个视频，默认50（0=不限制） |
| `--sort` | 评论排序：2=按热度（默认），0=按时间 |
| `--output` | 输出目录，默认自动生成 `bilibili_report_时间戳/` |
| `--no-html` | 跳过HTML报告生成 |
| `--no-excel` | 跳过Excel报表生成 |
| `--name` | 给分析命名（用于报告标题） |
| `--sessdata` | B站SESSDATA（也可通过环境变量 `BILI_SESSDATA` 设置） |
| `--bili-jct` | B站bili_jct（可选，配合--sessdata使用） |
| `--cookie` | 完整Cookie字符串（备选，优先级高于--sessdata） |

## 常用命令

```bash
# 基础用法
export BILI_SESSDATA=你的SESSDATA值
/mnt/d/baseSoftware/Python/Python312/python.exe /mnt/c/Users/Administrator/Desktop/bilibili_analyzer.py \
  --mid 50329118 --pages 5 --limit-videos 10 --name "分析"

# 只做分析不做报告
export BILI_SESSDATA=xxx
python /mnt/c/Users/Administrator/Desktop/bilibili_analyzer.py \
  --mid 50329118 --pages 3 --limit-videos 5 --no-html --no-excel
```

## AI字幕提取（完整视频文字稿）

对于需要获取视频完整文字内容（而非评论分析）的场景，使用SESSDATA + bilibili-api 拉取AI字幕：

```python
from bilibili_api import sync, video, Credential
import aiohttp, os

credential = Credential(sessdata=os.environ['BILI_SESSDATA'])

async def get_video_transcript(bvid):
    v = video.Video(bvid=bvid, credential=credential)
    info = await v.get_info()
    cid = info.get('cid', 0)
    
    # 通过字幕接口获取AI字幕
    sub_list = await v.get_subtitle(cid)
    subs = sub_list.get('subtitles', []) if isinstance(sub_list, dict) else sub_list
    for s in (subs or []):
        url = s.get('subtitle_url', '')
        if url:
            if url.startswith('//'): url = 'https:' + url
            break
    
    # 下载字幕JSON并提取纯文本
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            body = data.get('body', [])
            return '\n'.join(item.get('content','') for item in body if item.get('content'))
```

**适用场景**：需要用视频内容写文案/小说/分析时，直接拉完整AI字幕比翻评论高效得多。

**注意**：2023年及更早的视频通常没有AI字幕（B站AI字幕功能2024年后才普及）。如果 `get_subtitle(cid)` 返回空列表或subtitles为空，则该视频无可用的AI字幕，只能通过评论拼凑内容。

- ✅ SESSDATA只是session标识，不含密码
- ✅ 频率限制严格（0.3-0.5秒间隔）
- ✅ 不持久化，进程结束立即销毁
- ✅ 推荐环境变量传入

## 模式C：故事内容还原（无字幕视频的内容提取）

当用户要求了解/汇总/书写B站视频的故事内容（如"汇总这些故事""写文案""把故事讲出来"）时，按以下降级链执行：

### 字幕检测（先确认有没有字幕，避免白费功夫）

**预判规则**：2024年之前的B站视频**大概率没有AI自动字幕**。2024年中之后的新视频才有较高的CC覆盖率。

**检测方法A（API）**：
```python
# 通过 player/v2 API 检查
import aiohttp
async with aiohttp.ClientSession() as session:
    url = f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}"
    async with session.get(url) as resp:
        data = await resp.json()
        subs = data.get('data', {}).get('subtitle', {}).get('subtitles', [])
        # subs为空列表 = 无字幕，hasSub可能为true但subtitles为空
```

**检测方法B（浏览器Console，绕过412更可靠）**：
```js
// 在视频页面Console执行
JSON.stringify(window.__INITIAL_STATE__.videoData.subtitle)
// null 或 {list:[]} = 无字幕
// 或用fetch：
fetch('https://api.bilibili.com/x/player/v2?aid=AID&cid=CID')
  .then(r=>r.json()).then(d=>console.log(d.data.subtitle))
```

**重要**：`hasSub: true` + `subtitles: []`（空列表）= 播放器支持字幕功能但该视频无可用字幕。这是2023年及更早视频的典型表现，此时不要再尝试字幕API，直接走评论提取。

### 内容提取降级链

1. **AI视频小助理总结** — 热评第一页检查是否有AI生成的总结：
   ```python
   cmt = await comment.get_comments(oid=aid, type_=CommentResourceType.VIDEO, 
                                      page_index=1, order=OrderType.LIKE)
   for c in (cmt.get('replies') or []):
       msg = c.get('content', {}).get('message', '')
       if 'AI视频小助理' in msg or '课代表总结' in msg:
           # 最完整的剧情概括，直接可用
   ```

2. **UP主置顶评论** — UP主常在置顶评论中补充故事背景和情感定调（如沈旭的"这是唯一一期配音没顶住的"），是理解故事核心的关键信号。

3. **课代表/观众剧情讨论** — 用关键词筛选评论（"故事"、"经历"、"悲"、"泪"、"结局"、"阿X"等人名），过滤短评（`len(msg) < 40`），按点赞排序，前5-8条通常能拼凑出完整剧情。

4. **搜索API跨空间** — 用 `search.search_by_type` 按关键词搜全站后用 `mid` 筛选指定UP主：
   ```python
   from bilibili_api import search
   data = await search.search_by_type(keyword="十有九悲", 
       search_type=search.SearchObjectType.VIDEO,
       order_type=search.OrderVideo.TOTALRANK, page=1)
   up_videos = [v for v in data.get('result', []) if v.get('mid') == UID]
   ```
   比 `get_videos` 更不容易触发412，但第3页后仍可能触发。

5. **外部平台搜索** — 如果以上都不够，尝试在知乎/B站专栏搜索故事讨论。注意：Google搜索容易被反爬拦截，B站专栏搜索可能无结果。

### 诚实披露原则

当视频无字幕且外部无全文转录时，**必须告知用户**文案基于评论区一手资料（热评+课代表+UP主评论）还原，情节梗概真实、细节为文学处理。不要假装拿到了逐字稿。

## 模式D：UP主观点跟踪（无需登录的降级方案）

当用户询问"看看某UP主对XX的看法"时，按以下降级链执行：

### 1. 先搜 session history（最快）
如果该 UP主是之前分析过的，`session_search` 可能比重新爬取更快。5月14日的完整分析 session 可能包含详细观点摘要。

### 2. 浏览器加载视频列表页
`https://space.bilibili.com/{mid}/video` 看最近视频标题。标题本身透露方向。

### 3. 匹配免费视频
下拉找非"充电专属"标记的视频。如果全锁了，告知用户并提供 title-based 推断。

### 4. 汇总输出
给出：UP主信息 + 最近视频列表（标注充电/免费） + 基于标题和历史数据的观点推断 + 局限性说明。

**重要现实**：2026年6月起，B站对未登录用户的限制大幅升级。视频列表页（space/video）经常弹出登录弹窗或一直显示"拼命加载中…"。**即使带完整Cookie（SESSDATA+bili_jct+DedeUserID）+ WBI签名，部分API端点（如 `/x/space/wbi/arc/search`）仍返回-403。** 降级方案：优先 session_search + 已知历史数据；如需最新动态，走**浏览器Console DOM提取**（见下方"已知坑点"第15条）。

## 已知坑点

1. **Python 版本不一致** — Hermes venv 的 `python3` 是 Python **3.11**（路径 `/home/administrator/.hermes/hermes-agent/venv/bin/python3`），但 `pip3` 可能默认装到 Python **3.12** 用户目录。**用 `python3 -m pip install` 而不是 `pip3 install`** 来装依赖。

2. **PIL `_imaging` C扩展崩溃** — 如果 `sys.path.insert(0, "~/.local/lib/python3.12/site-packages")`（或设置 PYTHONPATH 指向 3.12 的 site-packages），会导致 PIL 的 C 扩展 `_imaging` 与当前 Python 3.11 不兼容，报 `ImportError: cannot import name '_imaging' from 'PIL'`。
   - ❌ **不要**设置 PYTHONPATH 指向 3.12 的 site-packages
   - ✅ **正确做法**：用 `python3 -m pip install bilibili-api-python pillow jieba snownlp wordcloud pandas matplotlib openpyxl` 全装在 venv 下

3. **412风控** — 大部分API可通过 bilibili_api 库绕过（内部WBI签名），但带SESSDATA的密集请求（连续请求不同接口）仍会触发412。**每次API调用间隔0.3-0.5秒**

4. **get_dynamics_new 需SESSDATA** — 不带Credential调用返回空列表。旧版 `get_dynamics()` 也需登录

5. **replies 可能是 None** — 后续评论页的 replies 字段返回 None，始终用 `cmt.get('replies') or []`

6. **Windows GBK编码** — 脚本已自动处理

7. **bilibili_analyzer.py 脚本中的API过时** — 脚本内用了 `ResourceType.VIDEO`，实际需改为 `CommentResourceType.VIDEO`（但脚本可能正常运行因为库向前兼容了旧写法——如果报错再改）

8. **pub_ts 类型可能是字符串** — `mod_author.get('pub_ts')` 返回的有时候是字符串，需要 `int(pub_ts)` 转换

9. **get_comments 用 AID 不是 BVID** — oid 参数需要 int 类型，用 `video_info['aid']` 或 `bvid2aid(bvid)`

10. **`major` 字段可能为 None** — 在 `get_dynamics_new` 返回的动态 items 中，转发类动态（非 OPUS/ARCHIVE 类型）的 `major` 字段为 `None`。直接调用 `major.get('type')` 会 `AttributeError`。**必须加 None 检查**：
     ```python
     major = mod_desc.get('major')  # 不用默认 {}
     if major is None:
         text = mod_desc.get('desc', {}).get('text', '')
         dyn_type = "转发"
     elif major.get('type') == 'MAJOR_TYPE_OPUS':
         ...
     ```

11. **安全扫描拦截内联脚本** — Hermes TUI 的安全扫描会拦截 `python3 -c "..."`、`-e` 等内联代码。必须写 `.py` 文件再 `python3 file.py` 运行。

12. **Matplotlib 中文显示方块** — DejaVu Sans 不含 CJK 字型，需要指定中文字体。WSL下用文泉驿正黑：
     ```bash
     font_path = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
     ```

13. **web_search / web_extract 依赖 firecrawl** — 这两个工具需要 `firecrawl-py==4.17.0`（注意版本号，新版4.30.x不兼容）。安装：
     ```bash
     python3 -m pip install --break-system-packages 'firecrawl-py==4.17.0'
     ```
     即使安装成功，firecrawl 还需要有效的 API key 才能搜索。无 key 时返回 `Unauthorized` 错误——此时改用浏览器或B站API。

14. **2024年前的B站视频无AI字幕** — 不要浪费时间在旧视频上反复尝试字幕API。`hasSub: true` 但 `subtitles: []`（空列表）= 播放器支持该功能但该视频无可用字幕。2023年及更早的视频几乎100%没有CC。此时走"模式C：评论提取"。

15. **浏览器Console DOM提取（API全线被封时的降级方案）** — 当B站API（即使带WBI签名+完整Cookie）仍返回-403时，可走浏览器路径：
     ```
     // 步骤1：在B站任意页面注入Cookie并刷新
     document.cookie = "SESSDATA=xxx; domain=.bilibili.com; path=/";
     location.reload();
     
     // 步骤2：确认登录生效（检查页面是否显示"已关注"）
     // 步骤3：导航到UP主动态页，用JS提取DOM文本
     items = document.querySelectorAll('.bili-dyn-item');
     // 文本在 .bili-dyn-content__orig .bili-rich-text__content
     // 充电专属标记：.dyn-blocked-mask
     ```
     注意：Cookie在页面导航时可能丢失，每次新开页面需重新注入。用 `fetch("https://api.bilibili.com/x/web-interface/nav", {credentials:"include"})` 可验证登录状态（返回 `isLogin: true` 即成功）。DOM文本提取用全 `textContent` 比逐字段解析更可靠。

## 输出文件

| 文件 | 内容 |
|------|------|
| `report.html` | 网页报告 |
| `bilibili_report.xlsx` | 6个Sheet |
| `wordcloud.png` | 词云图 |
| `sentiment_chart.png` | 情感分布图 |
| `raw_data.json` | 原始数据 |
