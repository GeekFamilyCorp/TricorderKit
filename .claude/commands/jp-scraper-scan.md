---
description: Scan one Japanese source using the token-saving scraper pipeline.
allowed-tools: Bash, Read
---

Arguments:
- `$1` = source id
- `$2` = mode: auto|rss|http|trafilatura|playwright

Rules:
1. Run `jp-scraper scrape source "$1" --mode "$2"`.
2. Run `jp-scraper delta build --source "$1"`.
3. Run `jp-scraper report summary --source "$1"`.
4. Read only `scan_summary.md`.
5. Read `scan_delta.jsonl` only if user asks for records.
6. Never read raw HTML by default.
