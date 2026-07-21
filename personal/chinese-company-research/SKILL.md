---
name: chinese-company-research
description: Research Chinese companies when web_search and browser tools are blocked by anti-bot captchas — workarounds, alternative data sources, and what info to extract for legal/business analysis
trigger: User asks to look up a Chinese company's background, credit info, legal disputes, registered capital, shareholders, or similar for any purpose (due diligence, lawsuit prep, supplier check, work injury, contract dispute)
tags: [chinese-company, due-diligence, legal-research, work-injury, captcha-workaround]
---

# Chinese Company Research

## The Problem

From WSL/cloud environments, **all major Chinese commercial sites actively block automated access**:

| Site | Block pattern |
|------|--------------|
| Baidu (搜索) | CAPTCHA forced |
| Qichacha (企查查) | 405 error from curl/browser |
| Tianyancha (天眼查) | Empty page / captcha |
| AiqiCha (爱企查) | Baidu CAPTCHA |
| Sogou (搜狗) | Anti-spider page |
| Bing (cn.bing.com) | No results for exact Chinese company names (JS-dependent) |
| Google | "Sorry" page (automated query flag) |
| gsxt.gov.cn | Times out (firewall) |

**Do NOT waste time retrying these.** Recognize immediately and pivot to alternative approaches.

## Step 1: Gather user-provided identifiers (always ask first)

Before searching, ask the user for as many of these as possible:

- **统一社会信用代码** (Unified Social Credit Code) — 18-digit — found on contracts, pay stubs, receipts, invoices
- **公司全称** (exact legal name) — confirm character-by-character
- **注册地址** (registered address)
- **法人代表** (legal representative name)
- **User's relationship to the company** — employee? supplier? customer?
- **Purpose of lookup** — contract dispute, work injury, supplier evaluation, investment?

## Step 2: Try quick-hit searches first

These sometimes work from the environment:

```bash
# Bing — wrap in quotes for exact match
curl -s "https://www.bing.com/search?q=%22<URL-ENCODED-COMPANY-NAME>%22&cc=cn" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Baidu API (limited search scope, works for some)
curl -s "https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=6899&query=<COMPANY-NAME>&format=json"
```

## Step 3: Pivot to user-assisted approaches (most reliable)

When automated tools fail, **ask the user to check themselves** and report back:

### Method A: WeChat Mini-Programs (easiest)
1. Open WeChat → Discover → Mini Programs
2. Search for "天眼查" or "企查查" mini-program
3. Search the company name — shows registration, legal risks, shareholders instantly
4. Take screenshots or share links with you

### Method B: Direct websites (phone/desktop browser)
- **国家企业信用信息公示系统**: https://www.gsxt.gov.cn/ — official, free, reliable
- **天眼查**: https://www.tianyancha.com/
- **企查查**: https://www.qichacha.com/
- **爱企查**: https://aiqicha.baidu.com/
- **中国裁判文书网** (legal judgments): https://wenshu.court.gov.cn/

### Method C: Ask the user to get key documents
For work injury / labor cases specifically:
- 劳动合同 (employment contract)
- 工资条/银行流水 (pay stubs / bank records showing salary)
- 工伤保险参保证明 (social insurance proof) — check via 12333 or 渝快办 app
- 医院诊断证明、病历、医疗费票据
- 微信聊天记录（与老板/HR关于治疗费、工资的对话）

## Step 4: What to extract from the company info

Depending on the user's goal, extract and analyze these dimensions:

### For work injury / labor dispute leverage:
| Data point | Why it matters |
|-----------|---------------|
| **注册资本** vs **实缴资本** | Low registered + low paid-in = the company may have limited assets; act fast to preserve claims |
| **法律诉讼记录** | Past labor disputes, judgments against them — shows pattern |
| **行政处罚记录** | Past labor bureau fines,社保违规 |
| **经营状态** | "存续" vs "注销" vs "吊销" — a dying company is harder to collect from |
| **股东/法人变更** | If they transferred assets recently, that's important |
| **分支机构** | If it's a franchise or brand chain, there may be a parent company to hold accountable |
| **参保人数** | How many employees they actually cover with social insurance — 0 or 1-3 suggests they didn't buy 工伤保险 |

### For business / supplier due diligence:
- 成立时间、经营范围、行政许可
- 法定代表人对外投资和关联企业
- 知识产权（商标、专利）
- 年报信息（营业收入、净利润 — if publicly available）

## Step 5: Legal avenues for work injury cases specifically

If the user's scenario is 工伤 (work injury):

1. **工伤认定** — If not yet done: the employer must file within 30 days; if they won't, the employee/surrogate can self-file within 1 year at the local 人社局
2. **劳动能力鉴定** — After认定, get 伤残等级鉴定 (1-10级) to determine compensation amount
3. **社保局 vs 公司责任** — If company paid 工伤保险: most costs covered by insurance fund. If NOT (common for small companies): the company must pay ALL costs themselves.
4. **One-time payments** (if company refuses): 一次性伤残补助金 + 一次性医疗补助金 + 一次性就业补助金
5. **Escalation path**: 劳动监察大队 (12333) → 劳动仲裁 → 法院起诉

## Common Pitfalls

- ❌ Wasting time retrying captcha-blocked sites — recognize the pattern and pivot immediately
- ❌ Asking the user to "check on Baidu" — give specific app/site names instead (e.g., "打开微信搜天眼查小程序")
- ❌ Assuming the company has工伤保险 — small companies often don't; ask explicitly
- ❌ Only asking for the company name — also ask for 统一社会信用代码 from the start
- ❌ Giving legal advice without disclaimers — state clearly you're not a lawyer

## Related Skills

- `government-procurement-ops` — shares the government context
- `gitee-notes-repo` — save company research results to notes

## Verification

After the user reports back with info:
- Confirm 统一社会信用代码 format (18 chars, alphanumeric)
- Confirm 经营状态 is active
- Cross-reference any provided legal case info with known judgments
