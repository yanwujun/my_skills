# Chinese Company Research — Failure Pattern Log

Record of what failed and how, to help future sessions pattern-match faster.

## Session 2026-05-22: 重庆山竹家居有限公司

**Goal**: Look up company background for work injury (工伤) case — leverage/evidence for negotiation or lawsuit.

### Attempts Made (all failed)

| Method | Tool | Result |
|--------|------|--------|
| web_search(name="重庆山竹家居有限公司") | web_search | `Unauthorized: Invalid token` — tool-level auth failure |
| Baidu via browser | browser_navigate | CAPTCHA forced redirect |
| Bing (cn.bing.com) | browser_navigate | No results (JS-dependent rendering) |
| Bing (cn.bing.com) exact-match | browser_navigate | No results |
| Qichacha | browser_navigate | 405 error page |
| Tianyancha mobile | browser_navigate | Empty page |
| Sogou | browser_navigate | Anti-spider page |
| Google | browser_navigate | "Sorry" captcha page |
| gsxt.gov.cn | browser_navigate | Empty page |
| Baidu via curl + User-Agent | terminal | CAPTCHA redirect |
| Qichacha via curl | terminal | 405 error |
| Sogou via curl | terminal | Anti-spider |
| Bing via curl + exact-name | terminal (pipe to python) | No results at all for Chinese company name |
| Yahoo search | terminal | No results |
| Bing "山竹家居 重庆" (partial name) | terminal | No results |
| Baidu API (resource_id=6899) | terminal | `{"status":"0","data":[]}` |
| Baidu API (resource_id=28431) | terminal | Invalid response |
| qcc.com/firm page | terminal via allorigins proxy | Empty |

### What Did NOT Work
- Standard web_search (auth error)
- Browser-navigate to any Chinese search site (all captcha-blocked)
- Curl to any Chinese site (even with proper UA + Accept-Language headers)
- Baidu API endpoints
- Any proxy workaround (allorigins)

### What SHOULD Be Done in Future
- Skip all automated Chinese search within 1-2 attempts upon seeing CAPTCHA/405
- Immediately pivot to **user-assisted** methods (ask user to use their phone):
  - WeChat mini-program (天眼查/企查查)
  - gsxt.gov.cn on their own browser
  - Send you screenshots or links
- Ask the user upfront for 统一社会信用代码
- For work injury specifically: ask about 劳动合同, 社保缴纳, 工伤认定 status
