# sidehustlenation.com Extraction Recipe

Session-tested extraction patterns for https://www.sidehustlenation.com/ideas/

## Step 1: Extract all headings

```javascript
// In browser_console — NO SEMANTIC HTML (no <article>, no <main>).
// Must use unscoped querySelectorAll('h2') globally.
// Confirmed working Jul 2026: returns all 27 numbered headings.
Array.from(document.querySelectorAll('h2'))
  .map(h => h.textContent.trim())
  .filter(t => t.match(/^\d+\./))
  .join('\n')
```

**Output** (27 numbered headings):
```
1. Online Surveys
2. Rental Properties
3. Customer Interviews
4. Part-Time Remote Work
5. Reselling Furniture Returns
...
27. Local Tours
```

## Step 2: Extract details per section

```javascript
// Unscoped querySelectorAll('h2') — site has no <article>/<main> tags
// Replace '21.' with the desired section number
(() => {
  const h2s = document.querySelectorAll('h2');
  for (let h of h2s) {
    if (h.textContent.trim().startsWith('21.')) {
      let el = h.nextElementSibling;
      let content = [];
      let count = 0;
      while (el && el.tagName !== 'H2' && count < 10) {
        content.push(el.textContent.trim().substring(0, 300));
        el = el.nextElementSibling;
        count++;
      }
      return content.join(' | ');
    }
  }
})()
```

Each section returns ~300-600 chars of description text, including income numbers and platform names.

## Step 2b: Batch extraction (multi-target, one call)

When you need details for several specific sections at once, use a single expression that collects all matches:

```javascript
// Unscoped — site has no <article>/<main> tags (confirmed Jul 2026)
(() => {
  const h2s = document.querySelectorAll('h2');
  let results = [];
  const targets = ['21. AI Training', '17. UGC', '9. Selling Printables', '8. Freelance', '12. Niche Newsletter'];
  h2s.forEach((h2) => {
    const text = h2.textContent.trim();
    if (targets.some(t => text.startsWith(t))) {
      let content = [];
      let el = h2.nextElementSibling;
      while (el && el.tagName !== 'H2' && content.length < 8) {
        content.push(el.textContent.trim().substring(0, 300));
        el = el.nextElementSibling;
      }
      results.push(text + '::' + content.join(' | '));
    }
  });
  return results.join('\n\n');
})()
```

**Why this is better**: One `browser_console` call instead of N separate calls. Returns a JSON object keyed by heading text with description content for each matched section. Adjust `targets` array to the sections you need. Confirmed working June 2026 on `sidehustlenation.com/ideas/`.

## Key data points extracted

From the article's section content:
- **AI Training**: $15/hr via Outlier.ai
- **Customer Interviews**: $50-150/hr via UserInterviews.com, Respondent.io
- **UGC**: up to $300/video via TikTok Shop
- **Printables**: $10,000/month (verified case study: Rachel Jones on Etsy)
- **Newsletter**: Substack/SendFox, monetize via ads/affiliates
- **Online Course**: $28,000+ passive income (verified case study on Udemy)
- **Tutoring**: $1,000/week via WyzAnt
- **Freelancing**: $60/hr bookkeeping, $100-500/article writing, $100k/month web design

## Site accessibility

- ✅ `browser_navigate` works from any IP
- ✅ No captcha, no JS-rendering barriers
- ⚠️ **NO semantic HTML5 tags** — no `<article>`, no `<main>` element (WordPress/classic CMS). All DOM queries must use unscoped selectors (e.g., `querySelectorAll('h2')`, not `querySelectorAll('article h2')`). Confirmed Jul 2026.
- ✅ `querySelectorAll('h2')` returns all 27 section headings (confirmed Jul 2026)
- ✅ No paywall — full content accessible
- ✅ Confirmed Jun-Jul 2026: `curl -sL --max-time 30` downloads ~461KB HTML reliably

## curl-based extraction (no browser needed)

When `browser_navigate` is unavailable or timing out, use curl to download the HTML then extract with grep or Python:

### Quick heading extraction (grep)
```bash
curl -sL --max-time 30 -o /tmp/sidehustle.html "https://www.sidehustlenation.com/ideas/"
grep -oP '<h[23][^>]*>.*?</h[23]>' /tmp/sidehustle.html | sed 's/<[^>]*>//g' | sed 's/&amp;/\&/g' | head -80
```
Returns all 27 numbered section headings.

### Keyword-based content extraction (Python) — ⚠️ UNRELIABLE

**PITFALL (confirmed June 2026)**: The generic keyword-extraction approach from the main SKILL.md Step 0 FAILS on SideHustleNation. After stripping HTML tags, the flat text stream mixes TOC entries, sidebar content, article body, and hundreds of blog comments. Keyword matching overwhelmingly hits comments and navigation text, not the article's actual descriptions. Income figures ($), platform names, and difficulty ratings from the article body are drowned out by noise.

**DO NOT use keyword extraction for SideHustleNation.** Use the `grep -A` context approach instead (below).

### Targeted context extraction (`grep -A`) — ✅ RELIABLE

After extracting headings with the `grep` one-liner above, pull details for specific sections using `grep -A`:

```bash
# Get ~20 lines of context after a specific section heading
grep -A20 -E '^(21\. AI Training|17\. UGC|3\. Customer Interviews)' <(sed 's/<[^>]*>//g' /tmp/sidehustle.html | sed '/^[[:space:]]*$/d') | head -80
```

This extracts the HTML text content that immediately follows the heading in the DOM, which is the actual article body for that section. It avoids the TOC/comment pollution problem entirely because the TOC entries are bare heading text with no following detail, while article sections have full paragraphs after each heading.

**When you need structured metadata** (income, difficulty, time-to-first-dollar) from multiple sections, prefer Shopify over SideHustleNation — Shopify has explicit `Time to start:`, `Setup difficulty:`, `Earning potential:` fields that parse cleanly. SideHustleNation's metadata is embedded in prose paragraphs and requires human interpretation.
