"""
collect_sources.py -- TricorderKit deep-research-core
Collecte multi-source parallele avec cache SQLite et dry-run.

Usage:
    python collect_sources.py --query "One Piece" --domain manga
    python collect_sources.py --query "One Piece" --domain manga --dry-run
    python collect_sources.py --query "One Piece" --domain manga --sources mangadex jikan

Version : 0.1.0 -- 15/05/2026
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

def _fetch_mangadex(base_url: str, query: str, timeout: int) -> list:
    resp = requests.get(
        f"{base_url}/manga",
        params={"title": query, "limit": 20, "contentRating[]": ["safe", "suggestive"]},
        timeout=timeout,
    )
    resp.raise_for_status()
    items = []
    for m in resp.json().get("data", []):
        attrs = m.get("attributes", {})
        title_obj = attrs.get("title") or {}
        title = title_obj.get("en") or title_obj.get("ja") or title_obj.get("ja-ro") or str(title_obj)
        items.append({
            "id": m.get("id"),
            "title": title,
            "status": attrs.get("status"),
            "year": attrs.get("year"),
            "tags": [(t.get("attributes", {}).get("name") or {}).get("en", "") for t in attrs.get("tags", [])],
            "source": "mangadex",
            "source_url": f"https://mangadex.org/title/{m.get('id')}",
        })
    return items


def _fetch_jikan(base_url: str, query: str, timeout: int) -> list:
    resp = requests.get(f"{base_url}/manga", params={"q": query, "limit": 20}, timeout=timeout)
    resp.raise_for_status()
    items = []
    for m in resp.json().get("data", []):
        items.append({
            "id": str(m.get("mal_id")),
            "title": m.get("title"),
            "title_japanese": m.get("title_japanese"),
            "score": m.get("score"),
            "rank": m.get("rank"),
            "status": m.get("status"),
            "authors": [a.get("name") for a in m.get("authors", [])],
            "genres": [g.get("name") for g in m.get("genres", [])],
            "source": "jikan",
            "source_url": m.get("url"),
        })
    return items


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


def _fetch_anilist(base_url: str, query: str, timeout: int) -> list:
    gql = """
    query ($search: String) {
      Page(perPage: 20) {
        media(search: $search, type: ANIME) {
          id title { romaji english native }
          studios { nodes { name } }
          status season seasonYear episodes averageScore popularity
        }
      }
    }
    """
    resp = requests.post(base_url, json={"query": gql, "variables": {"search": query}}, timeout=timeout)
    resp.raise_for_status()
    items = []
    for m in resp.json().get("data", {}).get("Page", {}).get("media", []):
        t = m.get("title", {})
        items.append({
            "id": str(m.get("id")),
            "title": t.get("english") or t.get("romaji") or t.get("native"),
            "title_native": t.get("native"),
            "studios": [s.get("name") for s in m.get("studios", {}).get("nodes", [])],
            "status": m.get("status"),
            "season": f"{m.get('season')} {m.get('seasonYear')}",
            "episodes": m.get("episodes"),
            "score": m.get("averageScore"),
            "source": "anilist",
            "source_url": f"https://anilist.co/anime/{m.get('id')}",
        })
    return items


# -- Dispatch ----------------------------------------------------------------

def _dispatch(source: dict, query: str, timeout: int = 10) -> list:
    src_type = source.get("type", "api_rest")
    url = source["url"]
    name = source["name"]
    try:
        if src_type == "api_graphql":
            if "anilist" in url:
                return _fetch_anilist(url, query, timeout)
        elif src_type == "api_rest":
            if "mangadex" in url:
                return _fetch_mangadex(url, query, timeout)
            elif "jikan" in url:
                return _fetch_jikan(url, query, timeout)
            elif "github" in url:
                return _fetch_github(url, query, timeout)
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
        "skill_version": "0.1.0",
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
        default="manga",
        choices=["manga", "anime", "github", "publishers"],
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
