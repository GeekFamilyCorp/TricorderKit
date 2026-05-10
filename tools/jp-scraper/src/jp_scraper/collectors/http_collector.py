from pathlib import Path
import httpx
from datetime import datetime, timezone

DEFAULT_HEADERS = {
    "User-Agent": "JapanAllianceBot/0.1 (+local research; respectful crawler)",
    "Accept-Language": "ja,en;q=0.7,fr;q=0.5",
}

def fetch_url(url: str, timeout: int = 20) -> dict:
    with httpx.Client(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=timeout) as client:
        r = client.get(url)
        return {
            "url": str(r.url),
            "status_code": r.status_code,
            "headers": dict(r.headers),
            "text": r.text if r.status_code < 400 else "",
            "error": None if r.status_code < 400 else f"HTTP {r.status_code}",
        }
