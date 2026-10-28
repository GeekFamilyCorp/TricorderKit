"""
collect_sources.py -- TricorderKit deep-research-core
Collecte multi-source parallele avec cache SQLite et dry-run.

Usage:
    python collect_sources.py --query "vector databases" --domain github
    python collect_sources.py --query "local-first software" --domain research --dry-run
    python collect_sources.py --query "temporal workflows" --domain research --sources "arXiv API"

Version : 0.2.0 -- 27/10/2026
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

# -- Paths -------------------------------------------------------------------
PLUGIN_DIR = Path(__file__).parent.parent
SOURCES_FILE = PLUGIN_DIR / "sources" / "trusted_sources.yml"
BLOCKED_FILE = PLUGIN_DIR / "sources" / "blocked_sources.yml"

# -- Logging -----------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    stream=sys.stderr,
)
log = logging.getLogger("collect_sources")


def _resolve_cache_db() -> Path:
    """Fallback /tmp si le mount Windows ne supporte pas SQLite (file locking)."""
    primary = PLUGIN_DIR.parent.parent / "data" / "deep_research" / "cache.sqlite"
    try:
        primary.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(primary))
        conn.execute("CREATE TABLE IF NOT EXISTS _probe (x TEXT)")
        conn.close()
        return primary
    except Exception:
        fallback = Path("/tmp/tricorderkit_deep_research_cache.sqlite")
        log.warning("SQLite mount Windows incompatible -- fallback cache: %s", fallback)
        return fallback


# -- Cache SQLite ------------------------------------------------------------

class SourceCache:
    def __init__(self, db_path: Path) -> None:
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def _key(self, source_name: str, query: str) -> str:
        return hashlib.sha256(f"{source_name}:{query}".lower().encode()).hexdigest()

    def get(self, source_name: str, query: str) -> list | None:
        key = self._key(source_name, query)
        now = datetime.now(timezone.utc).isoformat()
        row = self.conn.execute(
            "SELECT data, expires_at FROM cache WHERE key = ?", (key,)
        ).fetchone()
        if row and row[1] > now:
            log.info("[cache] HIT -- %s / %s", source_name, query[:40])
            return json.loads(row[0])
        return None

    def set(self, source_name: str, query: str, data: list, ttl_seconds: int) -> None:
        key = self._key(source_name, query)
        now = datetime.now(timezone.utc)
        expires = datetime.fromtimestamp(now.timestamp() + ttl_seconds, tz=timezone.utc)
        self.conn.execute(
            "INSERT OR REPLACE INTO cache (key, data, created_at, expires_at) VALUES (?,?,?,?)",
            (key, json.dumps(data), now.isoformat(), expires.isoformat()),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


# -- Source loader -----------------------------------------------------------

class SourceLoader:
    def __init__(self, sources_file: Path, blocked_file: Path) -> None:
        with open(sources_file, encoding="utf-8") as f:
            self._trusted: dict = yaml.safe_load(f)
        self._blocked: set = set()
        if blocked_file.exists():
            with open(blocked_file, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                self._blocked = {s.get("name", "") for s in data.get("blocked", [])}

    def get_sources(self, domain: str) -> list:
        sources = self._trusted.get(domain, [])
        if not isinstance(sources, list):
            return []
        return [s for s in sources if s.get("name") not in self._blocked]

    def get_scoring_weights(self) -> dict:
        return self._trusted.get("scoring_weights", {})


# -- Fetchers ----------------------------------------------------------------

_USER_AGENT = "TricorderKit deep-research (https://github.com/GeekFamilyCorp/TricorderKit)"
_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def _fetch_github(base_url: str, query: str, timeout: int) -> list:
    import os
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(
        f"{base_url}/search/repositories",
        params={"q": query, "sort": "stars", "per_page": 20},
        headers=headers,
        timeout=timeout,
    )
    resp.raise_for_status()
    items = []
    for r in resp.json().get("items", []):
        items.append({
            "id": str(r.get("id")),
            "title": r.get("full_name"),
            "description": r.get("description"),
            "stars": r.get("stargazers_count"),
            "language": r.get("language"),
            "topics": r.get("topics", []),
            "updated_at": r.get("updated_at"),
            "source": "github",
            "source_url": r.get("html_url"),
        })
    return items


def parse_arxiv_atom(xml_text: str) -> list:
    """Parse un flux Atom arXiv en items normalises (fonction pure, testable hors reseau)."""
    import xml.etree.ElementTree as ET

    root = ET.fromstring(xml_text)
    items = []
    for entry in root.findall("atom:entry", _ATOM_NS):
        def _text(tag: str) -> str:
            node = entry.find(f"atom:{tag}", _ATOM_NS)
            return " ".join((node.text or "").split()) if node is not None else ""

        entry_id = _text("id")
        items.append({
            "id": entry_id.rsplit("/", 1)[-1] if entry_id else "",
            "title": _text("title"),
            "summary": _text("summary"),
            "authors": [
                " ".join((a.findtext("atom:name", default="", namespaces=_ATOM_NS)).split())
                for a in entry.findall("atom:author", _ATOM_NS)
            ],
            "published": _text("published"),
            "updated_at": _text("updated"),
            "source": "arxiv",
            "source_url": entry_id,
        })
    return items


def _fetch_arxiv(base_url: str, query: str, timeout: int) -> list:
    resp = requests.get(
        base_url,
        params={"search_query": f"all:{query}", "start": 0, "max_results": 20},
        headers={"User-Agent": _USER_AGENT},
        timeout=timeout,
    )
    resp.raise_for_status()
    return parse_arxiv_atom(resp.text)


def _fetch_hackernews(base_url: str, query: str, timeout: int) -> list:
    resp = requests.get(
        base_url,
        params={"query": query, "tags": "story", "hitsPerPage": 20},
        headers={"User-Agent": _USER_AGENT},
        timeout=timeout,
    )
    resp.raise_for_status()
    items = []
    for h in resp.json().get("hits", []):
        object_id = str(h.get("objectID"))
        items.append({
            "id": object_id,
            "title": h.get("title"),
            "points": h.get("points"),
            "num_comments": h.get("num_comments"),
            "updated_at": h.get("created_at"),
            "source": "hackernews",
            "source_url": h.get("url") or f"https://news.ycombinator.com/item?id={object_id}",
        })
    return items


def _fetch_wikipedia(base_url: str, query: str, timeout: int) -> list:
    from urllib.parse import quote

    title = quote(query.strip().replace(" ", "_"), safe="")
    resp = requests.get(
        f"{base_url.rstrip('/')}/page/summary/{title}",
        headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
        timeout=timeout,
    )
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    data = resp.json()
    return [{
        "id": str(data.get("pageid", "")),
        "title": data.get("title"),
        "description": data.get("extract"),
        "updated_at": data.get("timestamp"),
        "source": "wikipedia",
        "source_url": (data.get("content_urls", {}).get("desktop", {}) or {}).get("page"),
    }]


# -- Dispatch ----------------------------------------------------------------

def _dispatch(source: dict, query: str, timeout: int = 10) -> list:
    src_type = source.get("type", "api_rest")
    url = source["url"]
    name = source["name"]
    try:
        if src_type == "api_atom":
            if "arxiv" in url:
                return _fetch_arxiv(url, query, timeout)
        elif src_type == "api_rest":
            if "github" in url:
                return _fetch_github(url, query, timeout)
            elif "hn.algolia" in url:
                return _fetch_hackernews(url, query, timeout)
            elif "wikipedia" in url:
                return _fetch_wikipedia(url, query, timeout)
        log.info("[%s] Pas de collecteur pour type=%s -- skip", name, src_type)
    except requests.RequestException as exc:
        log.error("[%s] Erreur reseau: %s", name, exc)
    except Exception as exc:
        log.error("[%s] Erreur: %s", name, exc)
    return []


# -- Collecte parallele ------------------------------------------------------

def collect(
    query: str,
    domain: str,
    source_names: list | None,
    loader: SourceLoader,
    cache: SourceCache,
    dry_run: bool = False,
    max_workers: int = 3,
) -> list:
    sources = loader.get_sources(domain)
    if source_names:
        sources = [s for s in sources if s["name"].lower() in {n.lower() for n in source_names}]

    if not sources:
        log.warning("Aucune source pour le domaine '%s'", domain)
        return []

    log.info("Sources: %s", [s["name"] for s in sources])

    if dry_run:
        log.info("[dry-run] Simulation -- aucun appel reseau")
        return [
            {
                "id": f"dry-{i}",
                "title": f"[DRY-RUN] Resultat {i+1} depuis {s['name']}",
                "source": s["name"].lower().replace(" ", "_"),
                "source_url": s["url"],
            }
            for i, s in enumerate(sources[:5])
        ]

    all_results: list = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for source in sources:
            cached = cache.get(source["name"], query)
            if cached is not None:
                all_results.extend(cached)
                continue
            fut = executor.submit(_dispatch, source, query)
            futures[fut] = source

        for fut in as_completed(futures):
            source = futures[fut]
            try:
                items = fut.result()
                time.sleep(0.2)
                cache.set(source["name"], query, items, source.get("cache_ttl", 900))
                all_results.extend(items)
                log.info("[%s] %d items", source["name"], len(items))
            except Exception as exc:
                log.error("[%s] Echec: %s", source["name"], exc)

    return all_results


# -- Output contract ---------------------------------------------------------

def build_output(query: str, domain: str, results: list, dry_run: bool) -> dict:
    return {
        "status": "success",
        "skill_name": "deep-research-core:collect_sources",
        "skill_version": "0.2.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "output": {
            "summary": f"{'[DRY-RUN] ' if dry_run else ''}{len(results)} items -- domain={domain} query={query!r}",
            "data": {
                "query": query,
                "domain": domain,
                "dry_run": dry_run,
                "total_items": len(results),
                "items": results,
            },
            "next_steps": ["score_reliability.py"],
        },
    }


# -- CLI ---------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Collecte multi-source TricorderKit")
    parser.add_argument("--query", required=True, help="Terme de recherche")
    parser.add_argument(
        "--domain",
        default="github",
        help="Domaine declare dans trusted_sources.yml (ex. github, research)",
    )
    parser.add_argument("--sources", nargs="*", help="Filtrer sources specifiques")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", default="json", choices=["json", "table"])
    args = parser.parse_args()

    loader = SourceLoader(SOURCES_FILE, BLOCKED_FILE)
    cache_db = _resolve_cache_db()
    cache = SourceCache(cache_db)

    try:
        results = collect(
            query=args.query,
            domain=args.domain,
            source_names=args.sources,
            loader=loader,
            cache=cache,
            dry_run=args.dry_run,
        )
        output = build_output(args.query, args.domain, results, args.dry_run)

        if args.output == "table":
            print(f"\n{'TITRE':<50} {'SOURCE':<15}")
            print("-" * 67)
            for item in results[:30]:
                print(f"{str(item.get('title',''))[:49]:<50} {str(item.get('source',''))[:14]:<15}")
        else:
            print(json.dumps(output, ensure_ascii=False, indent=2))
    finally:
        cache.close()


if __name__ == "__main__":
    main()
