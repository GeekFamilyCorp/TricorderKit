from datetime import datetime, timezone
from urllib.parse import urljoin
from selectolax.parser import HTMLParser

def _text(node):
    if not node:
        return None
    return " ".join(node.text(separator=" ").split())

def extract_listing(html: str, base_url: str, profile: dict) -> list[dict]:
    tree = HTMLParser(html)
    items = tree.css(profile.get("item", "article, li"))
    records = []
    for item in items[:100]:
        title_node = item.css_first(profile.get("title", "h1,h2,h3,.title"))
        link_node = item.css_first(profile.get("url", "a"))
        date_node = item.css_first(profile.get("date", "time,.date"))
        summary_node = item.css_first(profile.get("summary", "p"))
        href = link_node.attributes.get("href") if link_node else None
        title = _text(title_node)
        if not title and link_node:
            title = _text(link_node)
        if not title:
            continue
        records.append({
            "record_type": "listing_item",
            "title": title,
            "url": urljoin(base_url, href) if href else None,
            "date": _text(date_node),
            "summary": _text(summary_node),
            "source_method": "http_selectolax",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        })
    return records
