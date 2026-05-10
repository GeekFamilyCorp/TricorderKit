#!/usr/bin/env python3
"""
github-goat — CLI déterministe GitHub pour TricorderKit
Version : 0.1.0
Output : JSON par défaut
Cache  : SQLite local
"""

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print(json.dumps({"status": "error", "message": "requests non installé. Lancer : pip install requests"}))
    sys.exit(1)

# ── Config ───────────────────────────────────────────────────────────────────
GITHUB_API = "https://api.github.com"
CACHE_DB   = Path(".cache/github-goat.db")
CACHE_TTL  = 300  # secondes
TOKEN      = os.environ.get("GITHUB_TOKEN", "")
VERSION    = "0.1.0"

SAFE_COMMANDS = [
    "list-repos", "get-repo", "list-issues", "get-issue",
    "search-code", "search-repos", "list-commits", "get-commit",
    "list-prs", "get-pr", "list-branches", "get-file-contents"
]


# ── Cache SQLite ────────────────────────────────────────────────────────────────
def init_cache():
    CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            expires_at INTEGER NOT NULL
        )
    """)
    conn.commit()
    return conn


def cache_get(conn, key: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT value FROM cache WHERE key=? AND expires_at > ?",
        (key, int(time.time()))
    ).fetchone()
    return json.loads(row[0]) if row else None


def cache_set(conn, key: str, value: dict, ttl: int = CACHE_TTL):
    conn.execute(
        "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
        (key, json.dumps(value), int(time.time()) + ttl)
    )
    conn.commit()


# ── HTTP ──────────────────────────────────────────────────────────────────────
def gh_get(endpoint: str, params: dict = None) -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"

    resp = requests.get(f"{GITHUB_API}{endpoint}", headers=headers, params=params, timeout=10)
    if resp.status_code == 429:
        return {"error": "rate_limited", "retry_after": resp.headers.get("Retry-After", 60)}
    resp.raise_for_status()
    return resp.json()


# ── Commandes ───────────────────────────────────────────────────────────────────
def cmd_list_repos(args, conn, dry_run: bool) -> dict:
    if dry_run:
        return dry_run_report("list-repos", ["GET /users/{owner}/repos"], 200)
    owner = args.owner
    cache_key = f"list-repos:{owner}"
    cached = cache_get(conn, cache_key)
    if cached:
        return {"status": "success", "source": "cache", "data": cached}
    data = gh_get(f"/users/{owner}/repos", {"per_page": args.limit, "sort": "updated"})
    result = [{"name": r["name"], "stars": r["stargazers_count"], "updated": r["updated_at"],
               "language": r["language"], "url": r["html_url"]} for r in data]
    cache_set(conn, cache_key, result)
    return {"status": "success", "source": "api", "count": len(result), "data": result}


def cmd_get_repo(args, conn, dry_run: bool) -> dict:
    if dry_run:
        return dry_run_report("get-repo", [f"GET /repos/{args.owner}/{args.repo}"], 300)
    cache_key = f"get-repo:{args.owner}/{args.repo}"
    cached = cache_get(conn, cache_key)
    if cached:
        return {"status": "success", "source": "cache", "data": cached}
    data = gh_get(f"/repos/{args.owner}/{args.repo}")
    result = {
        "name": data["name"], "full_name": data["full_name"],
        "description": data.get("description"), "stars": data["stargazers_count"],
        "forks": data["forks_count"], "language": data["language"],
        "topics": data.get("topics", []), "license": data.get("license", {}).get("spdx_id"),
        "updated_at": data["updated_at"], "url": data["html_url"]
    }
    cache_set(conn, cache_key, result)
    return {"status": "success", "source": "api", "data": result}


def cmd_search_repos(args, conn, dry_run: bool) -> dict:
    if dry_run:
        return dry_run_report("search-repos", ["GET /search/repositories"], 500)
    cache_key = f"search-repos:{args.query}"
    cached = cache_get(conn, cache_key)
    if cached:
        return {"status": "success", "source": "cache", "data": cached}
    data = gh_get("/search/repositories", {"q": args.query, "per_page": args.limit, "sort": "stars"})
    result = [{"name": r["full_name"], "stars": r["stargazers_count"],
               "description": r.get("description", ""), "url": r["html_url"],
               "language": r.get("language"), "topics": r.get("topics", [])}
              for r in data.get("items", [])]
    cache_set(conn, cache_key, result)
    return {"status": "success", "source": "api", "total": data.get("total_count"), "data": result}


def cmd_list_issues(args, conn, dry_run: bool) -> dict:
    if dry_run:
        return dry_run_report("list-issues", [f"GET /repos/{args.owner}/{args.repo}/issues"], 300)
    cache_key = f"list-issues:{args.owner}/{args.repo}:{args.state}"
    cached = cache_get(conn, cache_key)
    if cached:
        return {"status": "success", "source": "cache", "data": cached}
    data = gh_get(f"/repos/{args.owner}/{args.repo}/issues",
                  {"state": args.state, "per_page": args.limit})
    result = [{"number": i["number"], "title": i["title"], "state": i["state"],
               "labels": [l["name"] for l in i.get("labels", [])],
               "created_at": i["created_at"], "url": i["html_url"]}
              for i in data if "pull_request" not in i]
    cache_set(conn, cache_key, result)
    return {"status": "success", "source": "api", "count": len(result), "data": result}


# ── Dry-run ───────────────────────────────────────────────────────────────────────
def dry_run_report(command: str, actions: list, estimated_tokens: int) -> dict:
    return {
        "status": "dry_run",
        "command": command,
        "dry_run_report": {
            "actions_that_would_run": actions,
            "estimated_tokens": estimated_tokens,
            "estimated_duration_ms": 500,
            "risk_level": "LOW"
        }
    }


# ── Output formatters ───────────────────────────────────────────────────────────────────
def format_output(result: dict, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(result, indent=2, ensure_ascii=False)
    elif fmt == "table":
        data = result.get("data", [])
        if not data or not isinstance(data, list):
            return json.dumps(result, indent=2)
        headers = list(data[0].keys())
        rows = [[str(r.get(h, "")) for h in headers] for r in data]
        widths = [max(len(h), max((len(r[i]) for r in rows), default=0)) for i, h in enumerate(headers)]
        sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
        header_row = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
        lines = [sep, header_row, sep]
        for row in rows:
            lines.append("| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(row)) + " |")
        lines.append(sep)
        return "\n".join(lines)
    return json.dumps(result, indent=2)


# ── Main ───────────────────────────────────────────────────────────────────────────
class _JsonParser(argparse.ArgumentParser):
    def error(self, message):
        print(json.dumps({"status": "error", "message": message, "recoverable": False}))
        sys.exit(1)


def main():
    parser = _JsonParser(
        description="github-goat — CLI GitHub déterministe pour TricorderKit"
    )
    parser.add_argument("--dry-run", action="store_true", help="Simuler sans effet de bord")
    parser.add_argument("--output", choices=["json", "table", "markdown"], default="json")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--version", action="version", version=f"github-goat {VERSION}")

    subparsers = parser.add_subparsers(dest="command")

    # list-repos
    p = subparsers.add_parser("list-repos")
    p.add_argument("owner")

    # get-repo
    p = subparsers.add_parser("get-repo")
    p.add_argument("owner")
    p.add_argument("repo")

    # search-repos
    p = subparsers.add_parser("search-repos")
    p.add_argument("query")

    # list-issues
    p = subparsers.add_parser("list-issues")
    p.add_argument("owner")
    p.add_argument("repo")
    p.add_argument("--state", choices=["open", "closed", "all"], default="open")

    args = parser.parse_args()

    if not args.command:
        print(json.dumps({"status": "error", "message": f"Commande requise. Disponibles : {SAFE_COMMANDS}"}))
        sys.exit(1)

    conn = init_cache()
    dry_run = args.dry_run

    dispatch = {
        "list-repos":   cmd_list_repos,
        "get-repo":     cmd_get_repo,
        "search-repos": cmd_search_repos,
        "list-issues":  cmd_list_issues,
    }

    fn = dispatch.get(args.command)
    if not fn:
        print(json.dumps({"status": "error", "message": f"Commande inconnue : {args.command}"}))
        sys.exit(1)

    try:
        result = fn(args, conn, dry_run)
        print(format_output(result, args.output))
    except requests.HTTPError as e:
        print(json.dumps({"status": "error", "message": str(e), "recoverable": True}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e), "recoverable": False}))
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
