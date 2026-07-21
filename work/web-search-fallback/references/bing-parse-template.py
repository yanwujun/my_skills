"""
Bing search results parser — reusable template.

Usage:
  1. curl search results to /tmp/bing_results.html
  2. Run this script: python3 bing-parse-template.py

This script reads from /tmp/bing_results.html and prints
ranked search results (title, URL, description).
"""

import re, html

def parse_bing(filepath: str) -> list[tuple[str, str, str]]:
    """Parse Bing search results HTML into (title, url, description) tuples."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    results = re.findall(r'<li class="b_algo"[^>]*>(.*?)</li>', content, re.DOTALL)
    parsed = []

    for r in results:
        title_m = re.search(
            r'<h2[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r, re.DOTALL
        )
        desc_m = re.search(r'<p[^>]*>(.*?)</p>', r, re.DOTALL)

        if title_m:
            title = html.unescape(re.sub(r'<[^>]+>', '', title_m.group(2)))
            url = title_m.group(1)
            desc = html.unescape(
                re.sub(r'<[^>]+>', '', desc_m.group(1))
            ) if desc_m else ''
            parsed.append((title, url, desc[:300]))

    return parsed


def fetch_article_text(url: str, timeout: int = 15) -> str:
    """Fetch a web article and return its text content (tags/scripts stripped)."""
    import urllib.request, urllib.error

    req = urllib.request.Request(url, headers={
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    resp = urllib.request.urlopen(req, timeout=timeout)
    content = resp.read().decode('utf-8', errors='replace')

    # Strip scripts, styles, tags
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
    content = re.sub(r'<[^>]+>', ' ', content)
    content = html.unescape(content)
    content = re.sub(r'\s+', ' ', content).strip()
    return content


if __name__ == '__main__':
    results = parse_bing('/tmp/bing_results.html')
    print(f"Found {len(results)} results\n")
    for i, (t, u, d) in enumerate(results, 1):
        print(f"{i}. {t}")
        print(f"   URL: {u}")
        print(f"   {d}")
        print()
