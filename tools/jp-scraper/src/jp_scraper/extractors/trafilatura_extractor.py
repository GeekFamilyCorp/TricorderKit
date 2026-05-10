from datetime import datetime, timezone
import trafilatura
import json

def extract_url(url: str) -> list[dict]:
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return [{"record_type": "error", "url": url, "error": "download_failed", "source_method": "trafilatura"}]
    extracted_json = trafilatura.extract(
        downloaded,
        output_format="json",
        with_metadata=True,
        include_links=True,
        include_images=False,
        include_tables=True,
    )
    if not extracted_json:
        return [{"record_type": "error", "url": url, "error": "extract_failed", "source_method": "trafilatura"}]
    data = json.loads(extracted_json)
    return [{
        "record_type": "article",
        "title": data.get("title"),
        "url": url,
        "author": data.get("author"),
        "date": data.get("date"),
        "text": data.get("text"),
        "source_method": "trafilatura",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }]
