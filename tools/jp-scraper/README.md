# Open Source JP Scraper Pack v0.1

Pack d'installation **100 % open source** pour créer une couche de scraping sobre en tokens destinée à TricorderKit.

Pipeline : `sources.yaml → robots/RSS/HTTP → cache → extraction → normalisation JP → delta JSONL → scan_summary.md → LLM`

## Stack open source

| Outil | Licence | Rôle |
|---|---|---|
| `feedparser` | BSD-2 | RSS / Atom |
| `httpx` | BSD-3 | HTTP client |
| `selectolax` | MIT | HTML parsing |
| `trafilatura` | Apache-2.0 | Text extraction |
| `typer` | MIT | CLI |
| `rich` | MIT | Terminal output |

## Installation

```bash
cd tools/jp-scraper
pip install -e .
```

## Commandes

```bash
jp-scraper sources audit
jp-scraper scrape source comic-natalie --mode rss
jp-scraper scrape source shonenjumpplus --mode http
jp-scraper delta build --source comic-natalie
jp-scraper report summary --source comic-natalie
```

## Règle LLM

Claude lit en priorité `scan_summary.md` puis `scan_delta.jsonl`. Jamais le HTML brut.
