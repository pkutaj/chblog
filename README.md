# ClickHouse Blog — danluu-style archive

A local, fast, fuzzy-searchable index of the ClickHouse blog
(https://clickhouse.com/blog), styled after https://danluu.com/ —
literally the same markup/CSS shape: a plain `<ul>` of
`<li><d>date</d><a>title</a></li>`, no images, no descriptions,
no chrome. Just a fuzzy finder over titles bolted on top.

## Run it

```bash
python3 serve.py            # opens http://127.0.0.1:8420/
```

Or just open `index.html` directly — `posts.json` is loaded via
`fetch`, which some browsers block on `file://`, so prefer the server.

## Rebuild the data (pick up new posts)

```bash
python3 build.py --refresh     # re-download rss.xml, rebuild posts.json
python3 build.py               # rebuild from the rss.xml already on disk
```

- `rss.xml` — raw feed from clickhouse.com/rss.xml (837 posts back to 2016)
- `posts.json` — {title, link, slug, date, date_short} per post

## Files

- `index.html` — the whole UI, danluu markup/CSS + fuzzy finder, vanilla JS.
- `build.py` — RSS -> posts.json.
- `serve.py` — trivial local static file server.

## Fuzzy finder

- `/` focuses the search box, `Esc` clears it
- subsequence fuzzy match (like fzf) over **titles only**
- matched characters are highlighted inline
