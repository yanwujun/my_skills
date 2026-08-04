# GitHub Trending Extraction Recipe

Proven JavaScript expression for extracting all project cards from GitHub Trending pages via `browser_console`.

## One-shot extraction

```javascript
Array.from(document.querySelectorAll('article')).map(a => {
  const h2 = a.querySelector('h2');
  const p = a.querySelector('p');
  const stars = a.querySelectorAll('a[href*="/stargazers"]');
  const forks = a.querySelectorAll('a[href*="/forks"]');
  const name = h2 ? h2.textContent.trim() : '';
  const desc = p ? p.textContent.trim() : '';
  const starText = stars.length > 0 ? stars[0].textContent.replace(/[^0-9,]/g, '').trim() : '';
  const forkText = forks.length > 0 ? forks[0].textContent.replace(/[^0-9,]/g, '').trim() : '';
  const weekStars = a.textContent.match(/([\d,]+)\s*stars?\s*this\s*week/i);
  return {name, desc, star: starText, fork: forkText, weekStars: weekStars ? weekStars[1] : ''};
}).filter(p => p.name).map(p => JSON.stringify(p)).join('\n')
```

## Supported URLs

| URL | Coverage |
|-----|----------|
| `https://github.com/trending?since=weekly` | All languages, ~25 repos |
| `https://github.com/trending/python?since=weekly` | Python only |
| `https://github.com/trending/typescript?since=weekly` | TypeScript only |
| `https://github.com/trending/javascript?since=weekly` | JavaScript only |

## Output fields

Each JSON line contains:
- `name` — "owner / repo" (may have `\n` artifacts, clean with `.replace(/\s+/g, ' ').trim()`)
- `desc` — project description paragraph
- `star` — total stars (comma-separated e.g. `"31,081"`)
- `fork` — total forks
- `weekStars` — stars gained this week

## Post-processing notes

- Names from GitHub's nested `<a>` structure contain `\n` and extra whitespace — normalize before display
- ~60-70% of unfiltered trending is AI-related in typical weeks
- To get more repos: scroll down with `browser_scroll(direction="down")` then re-extract
- For individual project detail: `browser_navigate(url="https://github.com/owner/repo")`

## Confirmed working

- Jul 27, 2026: 23 projects extracted from `github.com/trending?since=weekly` in a single call
- No authentication required for browsing trending
- Works from Chinese IPs (no blocks, no captcha)
