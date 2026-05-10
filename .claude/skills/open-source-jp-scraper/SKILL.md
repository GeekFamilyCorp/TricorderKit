# Open Source JP Scraper Skill

Use this skill when Claude must collect information from Japanese websites with minimal token usage.

## Tool priority

1. `jp-scraper sources audit`
2. `jp-scraper scrape source <id> --mode auto`
3. `jp-scraper delta build --source <id>`
4. `jp-scraper report summary --source <id>`
5. Read `scan_summary.md`
6. Read `scan_delta.jsonl` only when necessary

## Forbidden by default

- Reading raw HTML
- Reading full DOM snapshots
- Sending full pages to LLM
- Using browser fallback before RSS/HTTP/trafilatura
- Ignoring robots.txt

## Output expected

Return:
- new records
- changed records
- errors
- source reliability
- next command
