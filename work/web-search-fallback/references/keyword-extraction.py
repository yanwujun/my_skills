#!/usr/bin/env python3
"""
Keyword-based HTML content extraction for side hustle / topic research.
Strips all HTML tags, then finds sentences containing target keywords.
General-purpose — works on any HTML page regardless of structure.

Usage: python3 keyword-extraction.py <html_file> [keyword_file]
  - html_file: path to downloaded HTML
  - keyword_file: optional path to file with one keyword per line
    (defaults to side-hustle/finance keywords)

Output: numbered list of relevant sentence fragments to stdout.
"""

import re
import sys

# Default keywords for side hustle / work-from-home / online money topics
DEFAULT_KEYWORDS = [
    'side hustle', 'work from home', 'online job', 'freelance', 'remote', 'gig',
    'earn money', 'make money', 'passive income', 'affiliate', 'dropship',
    'print on demand', 'youtube', 'tiktok', 'blog', 'virtual assistant',
    'transcription', 'proofread', 'tutor', 'coach', 'consult', 'social media',
    'ai ', 'chatgpt', 'prompt', 'sell', 'course', 'podcast', 'voiceover',
    'graphic design', 'web dev', 'coding', 'data entry', 'survey', 'rental',
    'delivery', 'pet sitting', 'dog walk', 'housesit', 'clean',
    'handyman', 'landscap', 'uber', 'doordash', 'instacart', 'taskrabbit',
    'notion', 'canva', 'copywriting', 'seo', 'ads', 'marketing',
    'etsy', 'ebay', 'amazon', 'shopify', 'pinterest', 'instagram',
    'bookkeep', 'notary', 'voice over', 'narrat', 'test websit', 'usertest',
    'data annotat', 'self-publish', 'kdp', 'kindle', 'stock photo', 'stock video',
    'music licens', 'car rent', 'storage', 'parking', 'laundry', 'meal prep',
    'personal chef', 'cater', 'bake', 'cake', 'candle', 'soap', 'jewel',
    't-shirt', 'merch', 'merchandise', 'flipping', 'resell',
    'focus group', 'research study', 'mystery shop',
    'language', 'translat', 'teach english', 'teach online',
    'fitness', 'yoga', 'meditat', 'wellness', 'nutrition',
    'virtual event', 'online communit', 'membership', 'subscription',
    'newsletter', 'email market', 'lead gen', 'saas', 'nocode',
    'bubble', 'webflow', 'zapier', 'automation', 'workflow',
    'digital product', 'template', 'preset', 'lightroom', 'filter',
    'moderat', 'community manag', 'customer support', 'chat support',
    'app test', 'game test', 'beta test',
    'crypto', 'nft', 'web3', 'defi',
    '3d print', 'laser engrave', 'cnc', 'woodwork',
    'plant', 'garden', 'microgreen', 'mushroom', 'hydroponic',
]


def load_keywords(filepath=None):
    """Load keywords from file or use defaults."""
    if filepath:
        try:
            with open(filepath) as f:
                return [line.strip().lower() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Keyword file not found: {filepath}, using defaults", file=sys.stderr)
    return DEFAULT_KEYWORDS


def extract_text(html):
    """Strip HTML tags and entities, return clean text."""
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'&#[0-9]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def find_relevant(text, keywords, min_len=30, max_len=400):
    """Split text into sentences, return those matching any keyword."""
    # Also filter out CSS/JS garbage that survives stripping
    garbage_patterns = [
        'font-', 'padding', 'margin', ':where', 'rem', 'rgb', 'rgba',
        'var(', '@media', 'important', 'px', 'flex', 'grid', 'display:',
        'box-shadow', 'border-', 'background', 'transition'
    ]

    sentences = text.split('.')
    results = []
    for s in sentences:
        s = s.strip()
        if len(s) < min_len or len(s) > max_len:
            continue
        if any(g in s.lower() for g in garbage_patterns):
            continue
        low = s.lower()
        if any(kw in low for kw in keywords):
            results.append(s)
    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 keyword-extraction.py <html_file> [keyword_file]")
        sys.exit(1)

    html_file = sys.argv[1]
    keyword_file = sys.argv[2] if len(sys.argv) > 2 else None

    with open(html_file, encoding='utf-8', errors='replace') as f:
        html = f.read()

    keywords = load_keywords(keyword_file)
    text = extract_text(html)
    results = find_relevant(text, keywords)

    print(f"Extracted {len(results)} relevant segments from {len(text)} chars\n")
    for i, line in enumerate(results, 1):
        print(f"{i}. {line}.\n")


if __name__ == '__main__':
    main()
