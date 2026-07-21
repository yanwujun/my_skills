# B站 API 笔记

## 重要更新（2026-05-14）

**bilibili-api-python v17.4.1 在 Hermes venv (Python 3.11) 中已验证。**

部分API实际上已无需SESSDATA即可工作——bilibili_api 内部自动处理了WBI签名和请求头。

## API不需要登录的情况

| API | 无需登录？ | 实测说明 |
|-----|-----------|---------|
| `User(mid).get_user_info()` | ✅ 正常工作 | 返回昵称、签名、等级、性别、生日等 |
| `Video(bvid).get_info()` | ✅ 正常工作 | 返回标题、播放量、弹幕数、aid等 |
| `User(mid).get_videos(ps=30, pn=1)` | ✅ 正常工作 | 返回视频列表（内部处理了WBI签名，不会412） |
| `comment.get_comments()` | ✅ 第1页可用 | 返回前3条热评（replies字段），后续页replies为None |
| `User(mid).get_dynamics()` | ❌ 需要登录 | 返回 code=-101 账号未登录 |

**重要**：`get_videos()` 不返回 `list.vlist` 结构，而是直接在 `vlist` 字段（取决于API版本），用前先打印 `json.dumps(result, ...)` 看看结构。

## API 正确签名（v17.4.1）

```python
from bilibili_api import user, video, comment, sync, Credential

# 获取用户信息
u = user.User(UID)
info = sync(u.get_user_info())

# 获取视频列表
videos = sync(u.get_videos(ps=30, pn=1))

# 获取视频详情
v = video.Video(bvid="BVxxx")
info = sync(v.get_info())

# 获取评论 —— 注意参数名！
cmt = sync(comment.get_comments(
    oid=aid,                                      # 视频aid（从get_info获取）
    type_=comment.CommentResourceType.VIDEO,       # 不是 ResourceType 或 ResourceType.VIDEO
    page_index=1,                                  # 不是 ps=20！
    order=comment.OrderType.LIKE,                  # 不是 OrderBy！
))
# 返回值：
replies = cmt.get('replies') or []  # replies 可能是 None，需要处理
page_info = cmt.get('page', {})
total = page_info.get('acount', 0)  # 总评论数

# 获取动态（需登录）
cred = Credential(sessdata="xxx")
u = user.User(UID, credential=cred)
dyn = sync(u.get_dynamics(offset=0, need_top=True))
# dyn['items'] 包含动态列表
```

## Credential 构造

```python
from bilibili_api import Credential

# 仅SESSDATA就够了（大部分场景）
cred = Credential(sessdata="你的SESSDATA值")

# 完整版
cred = Credential(
    sessdata="xxx",
    bili_jct="xxx",  # 可选
    buvid3="xxx",     # 可选
    dedeuserid="xxx", # 可选
)

# 传入API
user.User(mid, credential=cred)
bili_comment.get_comments(aid, CommentResourceType.VIDEO, credential=cred)
```

## 请求头修改

```python
from bilibili_api import HEADERS
HEADERS.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...',
    'Referer': 'https://www.bilibili.com/',
})
```

注意：v17版本没有 `bilibili_api.network` 模块，不要用 `from bilibili_api import network`。

## 环境变量

推荐通过环境变量传入SESSDATA，避免在命令行暴露：
```bash
export BILI_SESSDATA=你的SESSDATA值
python3 bilibili_analyzer.py --mid 12345678
```

## Hermes venv Python 版本问题

**常见陷阱**：`pip3 install bilibili-api-python` 默认装在 **Python 3.12** 的用户目录
（`/home/administrator/.local/lib/python3.12/site-packages/`），但 Hermes venv 的
`python3` 是 **Python 3.11**，导入时会报 ModuleNotFoundError。

**修复方法**：
```bash
python3 -m pip install bilibili-api-python
# 这会用 venv 内部的 pip 装到正确的 Python 3.11 site-packages
```

验证安装：
```bash
python3 -c "import bilibili_api; print('OK')"
```

## 已知坑点

1. **412风控** — 直接curl访问API会被412拦截，但 `bilibili_api` 库内部处理了WBI签名，多数情况可绕过
2. **replies 可能为 None** — `cmt.get('replies')` 可能返回 `None`，始终用 `cmt.get('replies') or []` 安全
3. **get_dynamics() 需登录** — 即使bilibili_api库也无法匿名获取动态列表
4. **Windows GBK编码** — 脚本已自动处理
5. **PYTHONPATH缺失** — 如果遇到导入问题，加 `PYTHONPATH=$HOME/.local/lib/python3.12/site-packages`
6. **Python版本** — 确保 `pip3` 和 `python3` 对应同一个Python版本（用 `which python3 && python3 -V` 检查）
7. **B站2026年6月加严反爬** — space视频列表页（`/video`）对未登录用户强制弹登录窗口或一直"拼命加载中…"，浏览器访问也受阻。动态页、评论区同样需登录。`get_videos()` API可能在无WBI签名时也412。此时降级为session_search+标题分析。
8. **充电专属泛滥** — 财经类UP主（如战国时代_姜汁汽水）已将大部分新视频转为充电专属（30元/月），标题可见但内容不可见。需在输出中标注局限性。
