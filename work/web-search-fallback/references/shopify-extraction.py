#!/usr/bin/env python3
"""Proven Shopify side-hustle extraction script (cron-safe, confirmed Jun 2026).

Usage:
    curl -sL -A "Mozilla/5.0 ..." "https://www.shopify.com/blog/side-hustle-ideas" -o /tmp/shopify.html
    python3 references/shopify-extraction.py /tmp/shopify.html

Extracts 30 side hustle ideas with title, description snippet, difficulty level,
and income potential from Shopify's structured listicle article.
"""

import re
import sys

def strip_html(html_str):
    """Remove scripts, styles, and HTML tags. Returns list of non-empty lines."""
    html_str = re.sub(r'<script[^>]*>.*?</script>', '', html_str, flags=re.DOTALL | re.IGNORECASE)
    html_str = re.sub(r'<style[^>]*>.*?</style>', '', html_str, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '\n', html_str)
    # Decode common HTML entities
    for entity, char in [
        ('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'),
        ('&quot;', '"'), ('&#x27;', "'"), ('&rsquo;', "'"),
        ('&lsquo;', "'"), ('&ldquo;', '"'), ('&rdquo;', '"'),
        ('&mdash;', '\u2014'), ('&ndash;', '\u2013'),
    ]:
        text = text.replace(entity, char)
    lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 15]
    return lines


def extract(filepath):
    """Extract numbered side hustle ideas from Shopify HTML."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()

    lines = strip_html(html)
    results = []

    i = 0
    while i < len(lines):
        line = lines[i]
        # Match numbered list items: "1. Title" or "1. Title (something)"
        m = re.match(r'^(\d{1,2})[\.\)]\s+(.+)', line)
        if m and len(line) < 200:
            num = int(m.group(1))
            title = m.group(2).strip()

            # Collect description lines until next numbered item or section header
            desc_lines = []
            j = i + 1
            section_headers = [
                'popular online', 'profitable marketing', 'creative and',
                'flexible side', 'hands-on', 'what are', 'frequently asked',
            ]
            while j < len(lines) and j < i + 20:
                nl = lines[j]
                if re.match(r'^\d{1,2}[\.\)]\s+', nl) and len(nl) < 200:
                    break
                if any(nl.lower().startswith(h) for h in section_headers):
                    break
                desc_lines.append(nl)
                j += 1

            desc = ' '.join(desc_lines[:8])
            results.append((num, title, desc[:500]))
            i = j - 1
        i += 1

    return results


def extract_metadata(text, title):
    """Extract difficulty and income for a specific hustle from the raw text.

    Uses multi-pass approach: first find the title, then scan nearby text for
    structured metadata fields. More reliable than trying to parse all metadata
    in a single regex pass across the whole document.
    """
    # Find the title's position in the text
    idx = text.find(title)
    if idx == -1:
        return ('Medium', 'varies')

    window = text[idx:idx + 800]

    diff_m = re.search(
        r'(?:Setup difficulty|difficulty):\s*(Low|Medium|High)',
        window
    )
    income_m = re.search(
        r'Earning potential:\s*(\$[\d,]+[\u2013\u2014\-]\$[\d,+]+\+?/(?:month|hour|project|week))',
        window
    )

    difficulty = diff_m.group(1) if diff_m else 'Medium'
    income = income_m.group(1) if income_m else 'varies'
    return (difficulty, income)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 shopify-extraction.py <path-to-shopify.html>")
        sys.exit(1)

    filepath = sys.argv[1]
    results = extract(filepath)

    print(f"{'='*60}")
    print(f"Shopify Side Hustle Ideas — extracted {len(results)} items")
    print(f"{'='*60}")

    # Enrich with metadata if we have the raw text
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        raw = f.read()

    for num, title, desc in results:
        diff, income = extract_metadata(raw, title)
        diff_cn = {'Low': '\u7b80\u5355', 'Medium': '\u4e2d\u7b49', 'High': '\u8f83\u96be'}.get(diff, diff)
        print(f"\n{num}. {title}")
        print(f"   \u96be\u5ea6: {diff_cn} | \u6536\u5165: {income}")
        print(f"   {desc[:300]}")
