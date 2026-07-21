# Shopify Side Hustle Extraction Recipe

Session-tested extraction from https://www.shopify.com/blog/side-hustle-ideas

## Access method

✅ `curl` + Python `requests` with browser User-Agent — fastest and most reliable
⚠️ `browser_navigate` — may time out (CDP `Page.navigate` timeout observed Jul 2026 in cron context); use only as last resort after curl fails
❌ `web_extract` — Firecrawl-dependent, may fail

## Python extraction pattern (cron-safe)

```python
import requests, re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
resp = requests.get('https://www.shopify.com/blog/side-hustle-ideas', headers=headers, timeout=20)

# Strip scripts and styles first
html = re.sub(r'<script[^>]*>.*?</script>', '', resp.text, flags=re.DOTALL)
html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)

# Extract text from HTML
text = re.sub(r'<[^>]+>', '\n', html)
lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 25]
```

## Article structure

The article is a numbered list (1-30) organized in sections:

- **Popular online hustles for digital creators** (#1-5): YouTube channel, blog/newsletter, social media sponsorships, podcast, online surveys
- **Profitable marketing and ecommerce hustles** (#6-11): affiliate marketing, digital products, dropshipping, digital marketing services, mobile apps, reselling
- **Creative and artistic home-based side gigs** (#12-16): t-shirt design, clothing line, photography, voice-over, virtual interior design
- **Flexible side hustles for educators and communicators** (#17-20): online tutor, transcribe/translate, fitness classes, delivery
- **Hands-on and local side hustles** (#21-25): rent out home, ride-share, lawn care, pet sitting

## Key data points per hustle

Each numbered section includes:
- Time to first dollar (e.g., "1-2 weeks to create first videos")
- Difficulty level (Simple/Medium/Hard)
- Income range (e.g., "$100-$10,000+/month")
- Payment frequency
- Key stats (e.g., "2.53 billion monthly active users")

Example structure:
```
1. Monetize a YouTube channel
   1-2 weeks to create first videos
   Medium (requires basic video editing skills)
   $100-$10,000+/month
   Monthly (once you reach monetization thresholds)
```

## Search terms that find this article

The article is SEO-optimized for:
- "side hustle ideas"
- "profitable side hustle"
- "make money online"
- "work from home"

It shows up near the top of Google/Bing SERPs for these queries when search engines are working.

## Why Shopify over other sources

1. **No captcha** — no Cloudflare challenge, no security verification
2. **Structured data** — each hustle has difficulty, income, time-to-first-dollar
3. **30 hustles** — broad coverage across skill levels
4. **2026 relevance** — article updated December 2025 with 2026 projections
5. **Works via curl** — no JavaScript rendering needed, plain HTML parsing works

## Pitfall: single-pass extraction fails on structured metadata

When extracting difficulty/income fields from raw HTML text, a single-pass regex across the entire document often fails because HTML entity encoding (\u2013 vs -) and nested elements break the patterns. **Use a multi-pass approach**:

1. **Pass 1**: Extract numbered headings and their descriptions from stripped HTML
2. **Pass 2**: For each heading, find its position in the raw HTML, then scan the ~800-char window *around* that position for metadata fields

The `references/shopify-extraction.py` script implements this two-pass approach and has been confirmed working (Jun 2026, 844KB Shopify HTML, all 30 ideas extracted with income/difficulty). Copy it to `/tmp/` and run it directly.

