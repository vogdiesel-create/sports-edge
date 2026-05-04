#!/usr/bin/env python3
"""
Research fetcher - runs on Pi's residential IP.
Fetches Reddit threads, forums, articles, strips HTML, saves clean text.
Zero AI tokens used. Results analyzed by one agent afterward.

Usage: python3 fetch_research.py [--output-dir /path/to/output]
"""

import requests
import json
import os
import sys
import time
import re
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

OUTPUT_DIR = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--output-dir" else os.path.expanduser("~/research-output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

REDDIT_HEADERS = {
    "User-Agent": "ResearchBot/1.0 (educational research)"
}

stats = {"fetched": 0, "failed": 0, "skipped": 0}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def save(filename, content, subdir=""):
    path = os.path.join(OUTPUT_DIR, subdir) if subdir else OUTPUT_DIR
    os.makedirs(path, exist_ok=True)
    filepath = os.path.join(path, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    stats["fetched"] += 1
    log(f"  Saved: {filepath} ({len(content)} chars)")


def fetch_url(url, headers=None, timeout=15):
    try:
        r = requests.get(url, headers=headers or HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        log(f"  FAILED: {url} - {e}")
        stats["failed"] += 1
        return None


def strip_html(html):
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def fetch_reddit_json(url, params=None):
    """Fetch Reddit JSON API with rate limiting."""
    time.sleep(2)  # Reddit rate limit: 1 req/2s
    try:
        r = requests.get(url, headers=REDDIT_HEADERS, params=params, timeout=15)
        if r.status_code == 429:
            log("  Rate limited, waiting 60s...")
            time.sleep(60)
            r = requests.get(url, headers=REDDIT_HEADERS, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log(f"  FAILED: {url} - {e}")
        stats["failed"] += 1
        return None


def extract_reddit_posts(data):
    """Extract posts from Reddit JSON listing."""
    posts = []
    if not data or "data" not in data:
        return posts
    for child in data["data"].get("children", []):
        d = child.get("data", {})
        posts.append({
            "title": d.get("title", ""),
            "selftext": d.get("selftext", ""),
            "score": d.get("score", 0),
            "num_comments": d.get("num_comments", 0),
            "url": d.get("url", ""),
            "permalink": d.get("permalink", ""),
            "author": d.get("author", ""),
            "created_utc": d.get("created_utc", 0),
        })
    return posts


def extract_reddit_comments(data, depth=0):
    """Recursively extract comments from Reddit JSON."""
    lines = []
    if not data:
        return lines
    if isinstance(data, list):
        for item in data:
            lines.extend(extract_reddit_comments(item, depth))
        return lines
    if isinstance(data, dict):
        if data.get("kind") == "Listing":
            for child in data.get("data", {}).get("children", []):
                lines.extend(extract_reddit_comments(child, depth))
        elif data.get("kind") == "t1":  # comment
            d = data.get("data", {})
            author = d.get("author", "[deleted]")
            score = d.get("score", 0)
            body = d.get("body", "")
            indent = "  " * min(depth, 4)
            lines.append(f"{indent}[{author} | {score} pts]\n{indent}{body}\n")
            if d.get("replies"):
                lines.extend(extract_reddit_comments(d["replies"], depth + 1))
        elif data.get("kind") == "t3":  # post
            d = data.get("data", {})
            lines.append(f"# {d.get('title', '')}\n")
            lines.append(f"[{d.get('author', '')} | {d.get('score', 0)} pts | {d.get('num_comments', 0)} comments]\n")
            if d.get("selftext"):
                lines.append(f"{d['selftext']}\n")
            lines.append("---\n## Comments\n")
    return lines


def fetch_reddit_thread(permalink):
    """Fetch a full Reddit thread with comments."""
    url = f"https://old.reddit.com{permalink}.json?limit=200&sort=top"
    data = fetch_reddit_json(url)
    if not data:
        return None
    lines = extract_reddit_comments(data)
    return "\n".join(lines)


# ============================================================
# RESEARCH TARGETS
# ============================================================

def fetch_reddit_searches():
    """Fetch Reddit search results for sports betting topics."""
    log("=== REDDIT SEARCHES ===")

    searches = {
        "algobetting": [
            ("MLB model", "MLB+model+OR+totals+model"),
            ("K prop strikeout", "strikeout+OR+K+prop+model"),
            ("CLV analysis", "CLV+OR+closing+line+value"),
            ("Kelly criterion", "kelly+criterion+OR+bankroll"),
            ("overfitting warning", "overfit+OR+overfitting+OR+%22don%27t+do%22"),
            ("what works", "profitable+OR+%22what+works%22+OR+results"),
            ("prop model", "prop+model+OR+player+prop"),
            ("NBA model", "NBA+model+OR+basketball"),
            ("NHL model", "NHL+model+OR+hockey"),
            ("NFL model", "NFL+model+OR+football"),
            ("failure lessons", "lost+OR+failed+OR+mistake+OR+warning"),
            ("AMA results", "AMA+OR+%22I+made%22+OR+results+OR+proof"),
        ],
        "sportsbook": [
            ("sharp MLB", "sharp+MLB+model+OR+system"),
            ("prop strategy", "player+prop+strategy+model"),
            ("getting limited", "limited+OR+banned+sportsbook"),
            ("model results", "model+results+profitable"),
        ],
    }

    for subreddit, queries in searches.items():
        for label, query in queries:
            log(f"  Searching r/{subreddit}: {label}")
            url = f"https://old.reddit.com/r/{subreddit}/search.json"
            params = {"q": query, "restrict_sr": "on", "sort": "top", "t": "all", "limit": 25}
            data = fetch_reddit_json(url, params)
            posts = extract_reddit_posts(data)

            if not posts:
                continue

            # Save search results summary
            summary = f"# r/{subreddit} search: {label}\n# Query: {query}\n# Results: {len(posts)}\n\n"
            for p in posts:
                summary += f"## [{p['score']} pts, {p['num_comments']} comments] {p['title']}\n"
                summary += f"Author: {p['author']} | URL: {p['permalink']}\n"
                if p['selftext']:
                    summary += f"{p['selftext'][:500]}\n"
                summary += "\n---\n\n"

            safe_label = label.replace(" ", "-")
            save(f"{subreddit}-{safe_label}.txt", summary, "reddit")

            # Fetch top 3 threads with full comments
            top_posts = sorted(posts, key=lambda x: x["score"], reverse=True)[:3]
            for i, p in enumerate(top_posts):
                if p["permalink"] and p["num_comments"] > 5:
                    log(f"    Fetching thread: {p['title'][:60]}...")
                    thread = fetch_reddit_thread(p["permalink"])
                    if thread:
                        save(f"{subreddit}-{safe_label}-thread-{i+1}.txt", thread, "reddit/threads")
                    time.sleep(2)


def fetch_pinnacle_articles():
    """Fetch Pinnacle betting resources."""
    log("=== PINNACLE ARTICLES ===")

    urls = [
        ("pinnacle-clv", "https://www.pinnacle.com/betting-resources/en/educational/what-is-closing-line-value-clv-in-sports-betting"),
        ("pinnacle-kelly", "https://www.pinnacle.com/betting-resources/en/betting-strategy/the-real-kelly-criterion-a-critical-analysis-of-the-popular-staking-method/hzkjtfcb3knyn9cj"),
        ("pinnacle-theory", "https://www.pinnacle.com/betting-resources/en/educational/part-two-toward-a-theory-of-everything/uwc25wvpppzj997d"),
        ("pinnacle-market-efficiency", "https://www.pinnacle.com/betting-resources/en/betting-strategy/how-efficient-is-the-sports-betting-market"),
        ("pinnacle-poisson", "https://www.pinnacle.com/betting-resources/en/betting-strategy/poisson-distribution-betting"),
        ("pinnacle-mlb-strategy", "https://www.pinnacle.com/betting-resources/en/mlb/mlb-betting-strategy"),
        ("pinnacle-expected-value", "https://www.pinnacle.com/betting-resources/en/betting-strategy/how-to-calculate-expected-value"),
    ]

    for name, url in urls:
        log(f"  Fetching: {name}")
        html = fetch_url(url)
        if html:
            text = strip_html(html)
            save(f"{name}.txt", text, "pinnacle")
        time.sleep(1)


def fetch_fangraphs_articles():
    """Fetch key FanGraphs methodology articles."""
    log("=== FANGRAPHS ARTICLES ===")

    urls = [
        ("fg-xk-formula", "https://fantasy.fangraphs.com/the-definitive-pitcher-expected-k-formula/"),
        ("fg-negbin-runs", "https://community.fangraphs.com/run-distribution-using-the-negative-binomial-distribution/"),
        ("fg-swstr-krate", "https://blogs.fangraphs.com/adventures-in-swinging-strike-rate-vs-k-rate/"),
        ("fg-matchup-k", "https://blogs.fangraphs.com/bettermatch-up-data-forecasting-strikeout-rate/"),
        ("fg-stuff-metric", "https://community.fangraphs.com/revisiting-the-stuff-metric/"),
    ]

    for name, url in urls:
        log(f"  Fetching: {name}")
        html = fetch_url(url)
        if html:
            text = strip_html(html)
            save(f"{name}.txt", text, "fangraphs")
        time.sleep(1)


def fetch_academic_papers():
    """Fetch accessible academic paper pages."""
    log("=== ACADEMIC PAPERS ===")

    urls = [
        ("walsh-calibration-2024", "https://arxiv.org/abs/2303.06021"),
        ("ml-sports-review-2024", "https://arxiv.org/abs/2410.21484"),
        ("dmochowski-optimal-2023", "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0287601"),
        ("cmp-bivariate-2024", "https://arxiv.org/abs/2409.17129"),
        ("kelly-modified-sfu", "https://www.sfu.ca/~tswartz/papers/kelly.pdf"),
        ("kelly-wharton-2023", "https://wsb.wharton.upenn.edu/wp-content/uploads/2023/05/Beggy_2023__Betting_Kelly.pdf"),
        ("uhrin-optimal-2021", "https://arxiv.org/abs/2107.08827"),
        ("simon-inefficient-2024", "https://pubsonline.informs.org/doi/abs/10.1287/mnsc.2022.00456"),
        ("tennis-welo-2022", "https://www.sciencedirect.com/science/article/abs/pii/S0377221721003234"),
    ]

    for name, url in urls:
        log(f"  Fetching: {name}")
        html = fetch_url(url)
        if html:
            text = strip_html(html)
            save(f"{name}.txt", text, "academic")
        time.sleep(1)


def fetch_betting_forums():
    """Fetch betting forum threads."""
    log("=== BETTING FORUMS ===")

    urls = [
        ("twoplustwo-sports", "https://forumserver.twoplustwo.com/40/sports-betting/"),
        ("covers-mlb", "https://www.covers.com/forum/mlb-betting-27"),
        ("sbr-mlb", "https://www.sportsbookreview.com/forum/baseball-betting"),
        ("unabated-sharps", "https://unabated.com/articles/how-do-sharps-win-at-sports-betting"),
        ("unabated-beyond-clv", "https://unabated.com/articles/beyond-clv-analyze-bet-quality-using-expected-roi"),
        ("unabated-clv-precise", "https://unabated.com/articles/getting-precise-about-closing-line-value"),
    ]

    for name, url in urls:
        log(f"  Fetching: {name}")
        html = fetch_url(url)
        if html:
            text = strip_html(html)
            save(f"{name}.txt", text, "forums")
        time.sleep(1)


def fetch_practitioner_blogs():
    """Fetch practitioner blog posts and methodology articles."""
    log("=== PRACTITIONER BLOGS ===")

    urls = [
        ("8rain-sharp-journey", "https://8rainstation.com/blog/advice-from-my-mistake-filled-journey-to-becoming-a-sharp-sports-bettor-mastering-one-sided-line-devigging"),
        ("spanky-topdown", "https://www.bettored.org/post/case-study-spanky-top-down-betting"),
        ("izwr-kprops", "https://aibettingedge.com/using-in-zone-whiff-rate-to-predict-pitcher-strikeout-mlb-prop-bets/"),
        ("kprop-spots", "https://thisdayinbaseball.com/strikeout-props-betting-how-to-identify-elite-k-over-under-spots/"),
        ("overfitting-forum", "https://www.betting-forum.com/threads/the-overfitting-problem-why-backtested-betting-systems-fail-in-production.47444/"),
        ("backtest-guide", "https://www.greatbets.co.uk/how-to-backtest-a-sports-betting-strategy-without-overfitting/"),
        ("sportsai-calibration", "https://www.sports-ai.dev/blog/ai-model-calibration-brier-score"),
        ("sportsai-clv", "https://www.sports-ai.dev/blog/closing-line-value-and-ai-model-performance"),
        ("mlbprops-tto", "https://mlbprops.com/third-time-through-order-penalty-pitcher-prop-betting-mlb.html"),
    ]

    for name, url in urls:
        log(f"  Fetching: {name}")
        html = fetch_url(url)
        if html:
            text = strip_html(html)
            save(f"{name}.txt", text, "blogs")
        time.sleep(1)


def fetch_statcast_methodology():
    """Fetch Baseball Savant and Statcast methodology pages."""
    log("=== STATCAST / SAVANT ===")

    urls = [
        ("savant-csv-docs", "https://baseballsavant.mlb.com/csv-docs"),
        ("savant-statcast-search", "https://baseballsavant.mlb.com/statcast_search"),
        ("fg-glossary-pitching", "https://library.fangraphs.com/pitching/"),
        ("fg-glossary-batting", "https://library.fangraphs.com/offense/"),
        ("fg-park-factors", "https://library.fangraphs.com/principles/park-factors/"),
    ]

    for name, url in urls:
        log(f"  Fetching: {name}")
        html = fetch_url(url)
        if html:
            text = strip_html(html)
            save(f"{name}.txt", text, "statcast")
        time.sleep(1)


def fetch_github_repos():
    """Fetch README files from relevant GitHub repos."""
    log("=== GITHUB REPOS ===")

    repos = [
        "jldbc/pybaseball",
        "BillPetti/baseballr",
        "sportsdataverse/sportsdataverse-py",
    ]

    for repo in repos:
        log(f"  Fetching: {repo}")
        url = f"https://raw.githubusercontent.com/{repo}/main/README.md"
        text = fetch_url(url)
        if not text:
            url = f"https://raw.githubusercontent.com/{repo}/master/README.md"
            text = fetch_url(url)
        if text:
            safe_name = repo.replace("/", "-")
            save(f"{safe_name}.txt", text, "github")
        time.sleep(1)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    log(f"Research fetcher starting. Output: {OUTPUT_DIR}")
    log(f"Total targets: ~80 URLs + Reddit searches")

    fetch_reddit_searches()
    fetch_pinnacle_articles()
    fetch_fangraphs_articles()
    fetch_academic_papers()
    fetch_betting_forums()
    fetch_practitioner_blogs()
    fetch_statcast_methodology()
    fetch_github_repos()

    log(f"\n=== DONE ===")
    log(f"Fetched: {stats['fetched']}")
    log(f"Failed: {stats['failed']}")
    log(f"Output dir: {OUTPUT_DIR}")

    # Write manifest
    manifest = {
        "completed": datetime.now().isoformat(),
        "stats": stats,
        "output_dir": OUTPUT_DIR,
    }
    with open(os.path.join(OUTPUT_DIR, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    log("Manifest written. Ready for analysis.")
