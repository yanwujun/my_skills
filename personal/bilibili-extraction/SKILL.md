---
name: bilibili-extraction
category: social-media
description: Extract B站 (Bilibili) UP主 content — video lists, dynamics, comments — using browser cookie injection and DOM extraction when APIs are blocked by WBI/风控.
---

# B站内容提取

当需要获取B站UP主的视频列表、动态、评论等内容时使用此技能。B站的API有WBI签名和风控（412/403），**最可靠的方式是通过浏览器注入Cookie后提取DOM数据**。

## 触发条件
- 查看B站UP主的视频/动态/评论
- 用户提到B站某个UP主想了解其观点
- 需要提取B站页面中的文字内容

## 前置条件
用户需要提供 **SESSDATA** cookie值。告诉用户：
> Chrome → 打开 bilibili.com 确保已登录 → F12 → Application → Cookies → bilibili.com → 找到 SESSDATA → 双击Value复制

SESSDATA 格式示例: `4cd5ebcf%2C1783827318%2C530a6%2A11Cj...`

## 工作流程

### 1. Cookie注入
在 `bilibili.com` 首页通过 browser_console 设置 cookie 并刷新：

```js
document.cookie = "SESSDATA=<value>; domain=.bilibili.com; path=/; SameSite=None; Secure";
location.reload();
```

刷新后检查是否出现"已关注"或用户头像，确认登录生效。

### 2. 获取UP主信息
导航到 `https://space.bilibili.com/<UID>` 或 `https://space.bilibili.com/<UID>/dynamic`

### 3. 提取动态内容（纯文字动态）
使用 browser_console JS：

```js
(function() {
  let items = document.querySelectorAll('.bili-dyn-item');
  let out = [];
  for (let i = 0; i < items.length; i++) {
    let time = items[i].querySelector('.bili-dyn-time')?.textContent?.trim() || '';
    let orig = items[i].querySelector('.bili-dyn-content__orig');
    if (!orig) continue;
    let blocked = orig.querySelector('.dyn-blocked-mask');
    let text = orig.querySelector('.bili-rich-text__content');
    let t = text ? text.textContent.trim() : orig.textContent.trim().substring(0, 400);
    out.push(`[${i}] ${time}: ${blocked ? '[充电专属]' : t}`);
  }
  return out.join('\n\n---\n\n');
})()
```

**DOM选择器参考：**
- `.bili-dyn-item` — 每条动态容器
- `.bili-dyn-time` — 发布时间
- `.bili-dyn-content__orig` — 动态原始内容区
- `.bili-rich-text__content` — 富文本内容
- `.dyn-blocked-mask` — 充电专属遮罩（有此元素=需付费）
- `bili-dyn-item__desc` — 动态描述区
- `.bili-dyn-title__text` — UP主名称

### 4. 获取视频列表
视频列表页 `https://space.bilibili.com/<UID>/video` 需要登录才能加载。Cookie注入后刷新即可。视频标题中的"充电专属"标签可用来判断是否付费内容。

### 5. API方式（备选，不推荐）
B站API端点 `x/space/wbi/arc/search` 需要WBI签名，即使有SESSDATA也会返回-403。Python的 `bilibili-api` 库可处理WBI签名，但终端环境可能被412风控。优先使用浏览器方式。

**验证API登录状态：**
```
GET https://api.bilibili.com/x/web-interface/nav
```
返回 `isLogin: true` 说明cookie有效。

## 参考文件
- `references/jiangzhi-qishui-profile.md` — 战国时代_姜汁汽水 的UP主信息卡、最新动态原文、视频列表

## 注意事项
- Cookie可能跨页面导航后丢失，每次导航后检查登录状态
- 动态中的文字帖可能被设为"重要资料分享专属动态"（88元充电专属），标记为 `[充电专属]`
- 视频大部分已转为充电专属（30元/月），免费公开视频越来越少
- SESSDATA用后即弃，不落盘持久化

## 用户偏好
- 用户是B站用户，提供SESSDATA配合提取（用完即弃）
- 关注财经/地缘UP主（如 战国时代_姜汁汽水 UID:1039025435）
- 倾向于直接汇总观点而非罗列原始数据
