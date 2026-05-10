#!/usr/bin/env python3
"""
source-watch-goat — CLI veille manga/anime pour TricorderKit
Version : 0.1.0
Sources : MangaDex REST + AniList GraphQL + Jikan REST
Output  : JSON par défaut
Cache   : SQLite local (.cache/source-watch-goat.db)

Commandes :
  search-manga   <query>
  get-manga      <id>                 (MangaDex ID)
  latest-manga                        (dernières mises à jour)
  trending-manga
  search-anime   <query>
  get-anime      <id>                 (AniList ID)
  seasonal-anime [--season] [--year]
  trending-anime
  author-works   <author_name>
"""

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    import requests
except ImportError:
    print(json.dumps({"status": "error", "message": "requests non installé. Lancer : pip install requests"}))
    sys.exit(1)

# ── Config ───────────────────────────────────────────────────────────────────
VERSION       = "0.1.0"
CACHE_DB      = Path(".cache/source-watch-goat.db")
CACHE_TTL     = 900   # 15 min

MANGADEX_API  = "https://api.mangadex.org"
ANILIST_API   = "https://graphql.anilist.co"
JIKAN_API     = "https://api.jikan.moe/v4"

SAFE_COMMANDS = [
    "search-manga", "get-manga", "latest-manga", "trending-manga",
    "search-anime", "get-anime", "seasonal-anime", "trending-anime",
    "author-works"
]


# ── Cache SQLite ────────────────────────────────────────────────────────────────
def init_cache() -> sqlite3.Connection:
    CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key        TEXT PRIMARY KEY,
            value      TEXT NOT NULL,
            source     TEXT NOT NULL,
            expires_at INTEGER NOT NULL,
            created_at INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watch_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            query      TEXT,
            source     TEXT,
            result_ids TEXT,
            ran_at     INTEGER
        )
    """)
    conn.commit()
    return conn


def cache_get(conn: sqlite3.Connection, key: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT value FROM cache WHERE key=? AND expires_at > ?",
        (key, int(time.time()))
    ).fetchone()
    return json.loads(row[0]) if row else None


def cache_set(conn: sqlite3.Connection, key: str, value: dict, source: str, ttl: int = CACHE_TTL):
    now = int(time.time())
    conn.execute(
        "INSERT OR REPLACE INTO cache (key, value, source, expires_at, created_at) VALUES (?,?,?,?,?)",
        (key, json.dumps(value, ensure_ascii=False), source, now + ttl, now)
    )
    conn.commit()


# ── HTTP helpers ───────────────────────────────────────────────────────────────────
def http_get(url: str, params: dict = None, timeout: int = 10) -> dict:
    resp = requests.get(url, params=params, timeout=timeout)
    if resp.status_code == 429:
        retry = int(resp.headers.get("Retry-After", 60))
        return {"_rate_limited": True, "retry_after": retry}
    resp.raise_for_status()
    return resp.json()


def http_post(url: str, payload: dict, timeout: int = 10) -> dict:
    resp = requests.post(url, json=payload, timeout=timeout)
    if resp.status_code == 429:
        return {"_rate_limited": True, "retry_after": 60}
    resp.raise_for_status()
    return resp.json()


# ── Dry-run ───────────────────────────────────────────────────────────────────────
def dry_run_report(command: str, actions: list, est_tokens: int, risk: str = "LOW") -> dict:
    return {
        "status": "dry_run",
        "skill_name": "source-watch-goat",
        "skill_version": VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "command": command,
        "output": {"summary": f"Dry-run {command} — simulation sans appel réseau"},
        "dry_run_report": {
            "actions_that_would_run": actions,
            "estimated_tokens": est_tokens,
            "estimated_duration_ms": 1200,
            "risk_level": risk
        }
    }


# ── MangaDex ──────────────────────────────────────────────────────────────────────
def normalize_manga(m: dict) -> dict:
    """Normalise un objet manga MangaDex en format TricorderKit."""
    attrs = m.get("attributes", {})
    relationships = m.get("relationships", [])

    title = attrs.get("title", {})
    title_str = title.get("fr") or title.get("en") or title.get("ja-ro") or next(iter(title.values()), "")

    authors  = [r["attributes"]["name"] for r in relationships
                if r["type"] == "author" and "attributes" in r]
    artists  = [r["attributes"]["name"] for r in relationships
                if r["type"] == "artist" and "attributes" in r]
    cover_id = next((r["attributes"].get("fileName") for r in relationships
                     if r["type"] == "cover_art" and "attributes" in r), None)
    cover_url = f"https://uploads.mangadex.org/covers/{m['id']}/{cover_id}" if cover_id else None

    tags = [t.get("attributes", {}).get("name", {}).get("en", "")
            for t in attrs.get("tags", [])]

    return {
        "id":          m["id"],
        "source":      "mangadex",
        "title":       title_str,
        "title_en":    title.get("en"),
        "title_ja":    title.get("ja"),
        "status":      attrs.get("status"),
        "year":        attrs.get("year"),
        "authors":     authors,
        "artists":     artists,
        "tags":        [t for t in tags if t],
        "languages":   attrs.get("availableTranslatedLanguages", []),
        "rating":      attrs.get("contentRating"),
        "cover_url":   cover_url,
        "updated_at":  attrs.get("updatedAt"),
    }


def cmd_search_manga(args, conn, dry_run: bool) -> dict:
    if dry_run:
        query_hint = args.query or "<query>"
        return dry_run_report("search-manga", [f"GET {MANGADEX_API}/manga?title={query_hint}"], 400)
    if not args.query:
        return {"status": "error", "message": "Argument requis : query", "recoverable": False}

    key = f"mdx:search:{args.query}:{args.limit}"
    cached = cache_get(conn, key)
    if cached:
        return {"status": "success", "source": "cache", "count": len(cached), "data": cached}

    data = http_get(f"{MANGADEX_API}/manga", {
        "title": args.query, "limit": args.limit,
        "includes[]": ["author", "artist", "cover_art"],
        "contentRating[]": ["safe", "suggestive"],
        "order[relevance]": "desc"
    })
    if data.get("_rate_limited"):
        return {"status": "error", "message": "Rate limited MangaDex", "retry_after": data["retry_after"]}

    results = [normalize_manga(m) for m in data.get("data", [])]
    cache_set(conn, key, results, "mangadex")
    return {"status": "success", "source": "api", "count": len(results), "data": results}


def cmd_get_manga(args, conn, dry_run: bool) -> dict:
    if dry_run:
        return dry_run_report("get-manga", [f"GET {MANGADEX_API}/manga/{args.manga_id}"], 300)
    key = f"mdx:manga:{args.manga_id}"
    cached = cache_get(conn, key)
    if cached:
        return {"status": "success", "source": "cache", "data": cached}
    data = http_get(f"{MANGADEX_API}/manga/{args.manga_id}", {"includes[]": ["author", "artist", "cover_art"]})
    if "data" not in data:
        return {"status": "error", "message": f"Manga {args.manga_id} introuvable"}
    result = normalize_manga(data["data"])
    cache_set(conn, key, result, "mangadex", ttl=3600)
    return {"status": "success", "source": "api", "data": result}


def cmd_latest_manga(args, conn, dry_run: bool) -> dict:
    if dry_run:
        return dry_run_report("latest-manga", [f"GET {MANGADEX_API}/manga?order[updatedAt]=desc"], 400)
    key = f"mdx:latest:{args.limit}"
    cached = cache_get(conn, key)
    if cached:
        return {"status": "success", "source": "cache", "count": len(cached), "data": cached}
    data = http_get(f"{MANGADEX_API}/manga", {
        "limit": args.limit, "includes[]": ["author", "artist", "cover_art"],
        "contentRating[]": ["safe", "suggestive"], "order[updatedAt]": "desc"
    })
    if data.get("_rate_limited"):
        return {"status": "error", "message": "Rate limited MangaDex"}
    results = [normalize_manga(m) for m in data.get("data", [])]
    cache_set(conn, key, results, "mangadex", ttl=600)
    return {"status": "success", "source": "api", "count": len(results), "data": results}


def cmd_trending_manga(args, conn, dry_run: bool) -> dict:
    """Trending via Jikan (MAL top manga)."""
    if dry_run:
        return dry_run_report("trending-manga", [f"GET {JIKAN_API}/top/manga"], 350)
    key = f"jikan:top-manga:{args.limit}"
    cached = cache_get(conn, key)
    if cached:
        return {"status": "success", "source": "cache", "count": len(cached), "data": cached}
    data = http_get(f"{JIKAN_API}/top/manga", {"limit": min(args.limit, 25)})
    if data.get("_rate_limited"):
        return {"status": "error", "message": "Rate limited Jikan"}
    results = [{
        "id":          str(m.get("mal_id")),
        "source":      "jikan",
        "title":       m.get("title"),
        "title_en":    m.get("title_english"),
        "title_ja":    m.get("title_japanese"),
        "rank":        m.get("rank"),
        "score":       m.get("score"),
        "scored_by":   m.get("scored_by"),
        "popularity":  m.get("popularity"),
        "status":      m.get("status"),
        "authors":     [a.get("name") for a in m.get("authors", [])],
        "genres":      [g.get("name") for g in m.get("genres", [])],
        "volumes":     m.get("volumes"),
        "published":   m.get("published", {}).get("string"),
        "cover_url":   m.get("images", {}).get("jpg", {}).get("large_image_url"),
        "url":         m.get("url"),
    } for m in data.get("data", [])]
    cache_set(conn, key, results, "jikan", ttl=1800)
    return {"status": "success", "source": "api", "count": len(results), "data": results}


# ── AniList ───────────────────────────────────────────────────────────────────────
ANILIST_SEARCH_QUERY = """
query ($search: String, $perPage: Int) {
  Page(page: 1, perPage: $perPage) {
    media(search: $search, type: ANIME) {
      id title { romaji english native }
      status episodes season seasonYear
      averageScore popularity
      studios(isMain: true) { nodes { name } }
      staff(sort: RELEVANCE) { nodes { name { full } } }
      genres tags { name rank }
      coverImage { large }
      description(asHtml: false)
      siteUrl
    }
  }
}
"""

ANILIST_SEASONAL_QUERY = """
query ($season: MediaSeason, $year: Int, $perPage: Int) {
  Page(page: 1, perPage: $perPage) {
    media(season: $season, seasonYear: $year, type: ANIME, sort: POPULARITY_DESC) {
      id title { romaji english native }
      status episodes averageScore popularity
      studios(isMain: true) { nodes { name } }
      genres coverImage { large }
      siteUrl
    }
  }
}
"""

ANILIST_TRENDING_QUERY = """
query ($perPage: Int) {
  Page(page: 1, perPage: $perPage) {
    media(sort: TRENDING_DESC, type: ANIME) {
      id title { romaji english native }
      status episodes averageScore trending popularity
      studios(isMain: true) { nodes { name } }
      genres coverImage { large }
      siteUrl
    }
  }
}
"""


def normalize_anilist(m: dict) -> dict:
    return {
        "id":          str(m.get("id")),
        "source":      "anilist",
        "title":       m.get("title", {}).get("romaji"),
        "title_en":    m.get("title", {}).get("english"),
        "title_ja":    m.get("title", {}).get("native"),
        "status":      m.get("status"),
        "episodes":    m.get("episodes"),
        "season":      m.get("season"),
        "year":        m.get("seasonYear"),
        "score":       m.get("averageScore"),
        "popularity":  m.get("popularity"),
        "trending":    m.get("trending"),
        "studios":     [s.get("name") for s in m.get("studios", {}).get("nodes", [])],
        "genres":      m.get("genres", []),
        "tags":        [t.get("name") for t in (m.get("tags") or []) if t.get("rank", 0) >= 60],
        "cover_url":   m.get("coverImage", {}).get("large"),
        "description": (m.get("description") or "")[:300],
        "url":         m.get("siteUrl"),
    }


def cmd_search_anime(args, conn, dry_run: bool) -> dict:
    if dry_run:
        return dry_run_report("search-anime", [f"POST {ANILIST_API} (GraphQL search)"], 450)
    key = f"al:search:{args.query}:{args.limit}"
    cached = cache_get(conn, key)
    if cached:
        return {"status": "success", "source": "cache", "count": len(cached), "data": cached}
    data = http_post(ANILIST_API, {"query": ANILIST_SEARCH_QUERY,
                                    "variables": {"search": args.query, "perPage": args.limit}})
    if data.get("_rate_limited"):
        return {"status": "error", "message": "Rate limited AniList"}
    media = data.get("data", {}).get("Page", {}).get("media", [])
    results = [normalize_anilist(m) for m in media]
    cache_set(conn, key, results, "anilist")
    return {"status": "success", "source": "api", "count": len(results), "data": results}


def cmd_seasonal_anime(args, conn, dry_run: bool) -> dict:
    season = (args.season or _current_season()).upper()
    year   = args.year or datetime.now().year
    if dry_run:
        return dry_run_report("seasonal-anime", [f"POST {ANILIST_API} (seasonal {season} {year})"], 500)
    key = f"al:seasonal:{season}:{year}:{args.limit}"
    cached = cache_get(conn, key)
    if cached:
        return {"status": "success", "source": "cache", "season": season, "year": year,
                "count": len(cached), "data": cached}
    data = http_post(ANILIST_API, {"query": ANILIST_SEASONAL_QUERY,
                                    "variables": {"season": season, "year": year, "perPage": args.limit}})
    if data.get("_rate_limited"):
        return {"status": "error", "message": "Rate limited AniList"}
    media = data.get("data", {}).get("Page", {}).get("media", [])
    results = [normalize_anilist(m) for m in media]
    cache_set(conn, key, results, "anilist", ttl=3600)
    return {"status": "success", "source": "api", "season": season, "year": year,
            "count": len(results), "data": results}


def cmd_trending_anime(args, conn, dry_run: bool) -> dict:
    if dry_run:
        return dry_run_report("trending-anime", [f"POST {ANILIST_API} (trending)"], 450)
    key = f"al:trending:{args.limit}"
    cached = cache_get(conn, key)
    if cached:
        return {"status": "success", "source": "cache", "count": len(cached), "data": cached}
    data = http_post(ANILIST_API, {"query": ANILIST_TRENDING_QUERY,
                                    "variables": {"perPage": args.limit}})
    if data.get("_rate_limited"):
        return {"status": "error", "message": "Rate limited AniList"}
    media = data.get("data", {}).get("Page", {}).get("media", [])
    results = [normalize_anilist(m) for m in media]
    cache_set(conn, key, results, "anilist", ttl=900)
    return {"status": "success", "source": "api", "count": len(results), "data": results}


def cmd_author_works(args, conn, dry_run: bool) -> dict:
    if dry_run:
        return dry_run_report("author-works",
            [f"GET {JIKAN_API}/people?q={args.author_name}",
             f"GET {JIKAN_API}/people/{{id}}/manga"], 600)
    key = f"jikan:author:{args.author_name}"
    cached = cache_get(conn, key)
    if cached:
        return {"status": "success", "source": "cache", "data": cached}
    search = http_get(f"{JIKAN_API}/people", {"q": args.author_name, "limit": 5})
    if search.get("_rate_limited"):
        return {"status": "error", "message": "Rate limited Jikan"}
    people = search.get("data", [])
    if not people:
        return {"status": "success", "message": f"Auteur '{args.author_name}' non trouvé", "data": []}
    person = people[0]
    pid = person.get("mal_id")
    time.sleep(0.5)
    works_data = http_get(f"{JIKAN_API}/people/{pid}/manga")
    if works_data.get("_rate_limited"):
        return {"status": "error", "message": "Rate limited Jikan (works)"}
    works = [{
        "title": w.get("manga", {}).get("title"),
        "role":  w.get("position"),
        "url":   w.get("manga", {}).get("url"),
        "cover": w.get("manga", {}).get("images", {}).get("jpg", {}).get("image_url"),
    } for w in works_data.get("data", [])]
    result = {
        "author":   person.get("name"),
        "name_en":  person.get("name"),
        "birthday": person.get("birthday"),
        "about":    (person.get("about") or "")[:300],
        "url":      person.get("url"),
        "works":    works,
    }
    cache_set(conn, key, result, "jikan", ttl=3600)
    return {"status": "success", "source": "api", "data": result}


# ── Utils ───────────────────────────────────────────────────────────────────────────
def _current_season() -> str:
    m = datetime.now().month
    if m in (1, 2, 3):   return "WINTER"
    if m in (4, 5, 6):   return "SPRING"
    if m in (7, 8, 9):   return "SUMMER"
    return "FALL"


def format_output(result: dict, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(result, indent=2, ensure_ascii=False)
    elif fmt == "table":
        data = result.get("data")
        if isinstance(data, list) and data:
            keys = ["title", "source", "score", "year", "status", "authors"]
            rows = [[str(r.get(k, "—")) for k in keys] for r in data]
            widths = [max(len(k), max((len(r[i]) for r in rows), default=0))
                      for i, k in enumerate(keys)]
            sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
            hdr = "| " + " | ".join(k.ljust(widths[i]) for i, k in enumerate(keys)) + " |"
            lines = [sep, hdr, sep]
            for row in rows:
                lines.append("| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(row)) + " |")
            lines.append(sep)
            return "\n".join(lines)
    return json.dumps(result, indent=2, ensure_ascii=False)


# ── Main ───────────────────────────────────────────────────────────────────────────
class _JsonParser(argparse.ArgumentParser):
    def error(self, message):
        print(json.dumps({"status": "error", "message": message, "recoverable": False}))
        sys.exit(1)


def main():
    parser = _JsonParser(description="source-watch-goat — CLI veille manga/anime pour TricorderKit")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output",  choices=["json", "table"], default="json")
    parser.add_argument("--limit",   type=int, default=20)
    parser.add_argument("--version", action="version", version=f"source-watch-goat {VERSION}")

    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("search-manga"); p.add_argument("query", nargs="?", default=None)
    p = sub.add_parser("get-manga");    p.add_argument("manga_id")
    sub.add_parser("latest-manga")
    sub.add_parser("trending-manga")
    p = sub.add_parser("search-anime"); p.add_argument("query")
    p = sub.add_parser("seasonal-anime")
    p.add_argument("--season", choices=["WINTER","SPRING","SUMMER","FALL"], default=None)
    p.add_argument("--year",   type=int, default=None)
    sub.add_parser("trending-anime")
    p = sub.add_parser("author-works"); p.add_argument("author_name")

    args = parser.parse_args()

    if not args.command:
        print(json.dumps({"status": "error",
                          "message": f"Commande requise. Disponibles : {SAFE_COMMANDS}"}))
        sys.exit(1)

    conn = init_cache()
    dispatch = {
        "search-manga":   cmd_search_manga,
        "get-manga":      cmd_get_manga,
        "latest-manga":   cmd_latest_manga,
        "trending-manga": cmd_trending_manga,
        "search-anime":   cmd_search_anime,
        "seasonal-anime": cmd_seasonal_anime,
        "trending-anime": cmd_trending_anime,
        "author-works":   cmd_author_works,
    }

    fn = dispatch.get(args.command)
    if not fn:
        print(json.dumps({"status": "error", "message": f"Commande inconnue : {args.command}"}))
        sys.exit(1)

    try:
        result = fn(args, conn, args.dry_run)
        print(format_output(result, args.output))
    except requests.HTTPError as e:
        print(json.dumps({"status": "error", "message": str(e), "recoverable": True}))
        sys.exit(1)
    except requests.ConnectionError:
        print(json.dumps({"status": "error",
                          "message": "Connexion impossible — mode offline disponible via cache",
                          "recoverable": True}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e), "recoverable": False}))
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
