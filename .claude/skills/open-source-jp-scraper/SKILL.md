# Open Source Web Scraper Skill

Use this skill when Claude must collect information from websites with minimal token usage.

## Tool priority

1. `your-scraper sources audit`
2. `your-scraper scrape source <id> --mode auto`
3. `your-scraper delta build --source <id>`
4. `your-scraper report summary --source <id>`
5. Read `scan_summary.md`
6. Read `scan_delta.jsonl` only when necessary

> Adapt `your-scraper` to your actual CLI tool name (see `tools/` directory).

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
