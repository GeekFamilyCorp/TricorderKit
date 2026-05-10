import feedparser
from datetime import datetime, timezone

def fetch_feed(url: str) -> list[dict]:
    parsed = feedparser.parse(url)
    records = []
    for entry in parsed.entries:
        records.append({
            "record_type": "feed_entry",
            "title": entry.get("title"),
            "url": entry.get("link"),
            "published": entry.get("published") or entry.get("updated"),
            "summary": entry.get("summary"),
            "source_method": "rss",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        })
    return records
