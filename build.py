#!/usr/bin/env python3
"""
Build a danluu.com-style static index of the ClickHouse blog, title-only,
with a client-side fuzzy finder.

Pipeline:
  1. Parse rss.xml -> list of {title, link, pubDate}
  2. Emit posts.json (data for the page) that index.html reads at runtime.

Usage:
  python3 build.py            # build posts.json from local rss.xml
  python3 build.py --refresh  # re-fetch rss.xml first
  python3 build.py --limit 50 # only process first N posts (debug)
"""
import argparse
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
RSS_PATH = ROOT / "rss.xml"
POSTS_JSON = ROOT / "posts.json"
AUTHORS_JSON = ROOT / "authors.json"  # cache: slug -> [names]
RSS_URL = "https://clickhouse.com/rss.xml"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) chblog-fuzzy-index/1.0"


def slugify(link: str) -> str:
    return link.rstrip("/").split("/")[-1]


def fetch(url: str, timeout=20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def maybe_refresh_rss():
    print(f"Refreshing {RSS_URL} -> {RSS_PATH}")
    data = fetch(RSS_URL)
    RSS_PATH.write_bytes(data)


def parse_rss():
    tree = ET.parse(RSS_PATH)
    items = []
    for item in tree.getroot().find("channel").findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        if not link:
            continue
        try:
            dt = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %Z")
        except ValueError:
            dt = None
        items.append(
            {
                "title": html.unescape(title),
                "link": link,
                "slug": slugify(link),
                "date": dt.strftime("%Y-%m-%d") if dt else "",
                "date_short": dt.strftime("%y/%m") if dt else "",
            }
        )
    return items


LD_RE = re.compile(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', re.S)


def find_authors(node):
    if isinstance(node, list):
        return [n for x in node for n in find_authors(x)]
    if isinstance(node, dict):
        if "author" in node:
            a = node["author"]
            a = a if isinstance(a, list) else [a]
            return [x["name"] if isinstance(x, dict) else str(x) for x in a
                    if (isinstance(x, dict) and x.get("name")) or isinstance(x, str)]
        return [n for v in node.values() for n in find_authors(v)]
    return []


def fetch_authors(link):
    try:
        page = fetch(link).decode("utf-8", "replace")
        for m in LD_RE.finditer(page):
            try:
                names = find_authors(json.loads(m.group(1)))
            except ValueError:
                continue
            if names:
                return names
        return []
    except Exception as e:
        print(f"  author fetch failed {link}: {e}")
        return None  # None = retry next time


def add_authors(posts):
    cache = json.loads(AUTHORS_JSON.read_text()) if AUTHORS_JSON.exists() else {}
    todo = [p for p in posts if p["slug"] not in cache]
    if todo:
        print(f"Fetching authors for {len(todo)} posts...")
        with ThreadPoolExecutor(8) as ex:
            for p, names in zip(todo, ex.map(lambda p: fetch_authors(p["link"]), todo)):
                if names is not None:
                    cache[p["slug"]] = names
        AUTHORS_JSON.write_text(json.dumps(cache, indent=1))
    for p in posts:
        p["authors"] = cache.get(p["slug"], [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download rss.xml")
    ap.add_argument("--limit", type=int, default=None, help="debug: cap post count")
    args = ap.parse_args()

    if args.refresh or not RSS_PATH.exists():
        maybe_refresh_rss()

    posts = parse_rss()
    if args.limit:
        posts = posts[: args.limit]

    add_authors(posts)
    posts.sort(key=lambda x: x["date"] or "", reverse=True)

    POSTS_JSON.write_text(json.dumps(posts, indent=1))
    print(f"Wrote {POSTS_JSON} with {len(posts)} posts")


if __name__ == "__main__":
    main()
