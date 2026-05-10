from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

USER_AGENT = "MangaTrackerCLI/0.1 (+https://japan-alliance.local; respectful research bot)"


def fetch_text(url: str, timeout: int = 20) -> str:
    if url == "variable":
        raise ValueError("URL variable : fournissez une URL officielle explicite.")
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=timeout) as res:
            charset = res.headers.get_content_charset() or "utf-8"
            return res.read().decode(charset, errors="replace")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Fetch échoué pour {url}: {exc}") from exc
