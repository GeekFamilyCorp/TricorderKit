#!/usr/bin/env python3
"""
obsidian-goat — CLI déterministe Obsidian Vault pour TricorderKit
Version : 0.1.0 — 2026-05-18
Output  : JSON par défaut
Cache   : SQLite local (métadonnées + timestamps)

Commandes disponibles :
  read-note       <path> [--vault <vault>]
  write-note      <path> --content <content> [--vault <vault>] [--dry-run]
  update-hot-cache --content <content> [--dry-run]
  append-log      --date <YYYY-MM-DD> --entry <text> [--dry-run]
  check-note      <path> [--vault <vault>]
  list-notes      <folder> [--vault <vault>]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Config ───────────────────────────────────────────────────────────────────
VERSION   = "0.1.0"
CACHE_DB  = Path(os.environ.get("OBSIDIAN_GOAT_CACHE", ".cache/obsidian-goat.db"))
CACHE_TTL = 300  # secondes

# Chemins vaults depuis ENV ou defaults TricorderKit
VAULT_PATHS = {
    "claude-vault":    os.environ.get("OBSIDIAN_VAULT_PATH",
                                      r"C:\Users\sebas\Documents\Claude\claude-vault"),
    "japan-alliance":  os.environ.get("OBSIDIAN_JAPAN_VAULT_PATH",
                                      r"C:\Users\sebas\Documents\obsidian\Japan-Alliance"),
}

# Chemins standards dans le vault TricorderKit
HOT_CACHE_PATH    = "00_SYSTEM/05_Hot_Cache/HOT_CACHE.md"
DAILY_LOG_FOLDER  = "10_INBOX/Daily_Logs"

SAFE_COMMANDS = [
    "read-note", "write-note", "update-hot-cache",
    "append-log", "check-note", "list-notes"
]


# ── Cache SQLite ──────────────────────────────────────────────────────────────
def init_cache() -> sqlite3.Connection:
    CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key        TEXT PRIMARY KEY,
            value      TEXT NOT NULL,
            expires_at INTEGER NOT NULL
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


def cache_set(conn: sqlite3.Connection, key: str, value: dict, ttl: int = CACHE_TTL):
    conn.execute(
        "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
        (key, json.dumps(value), int(time.time()) + ttl)
    )
    conn.commit()


# ── Utilitaires vault ─────────────────────────────────────────────────────────
def resolve_vault(vault_name: str) -> Path:
    """Résout le chemin absolu d'un vault par nom."""
    path_str = VAULT_PATHS.get(vault_name)
    if not path_str:
        raise ValueError(f"Vault inconnu: '{vault_name}'. Disponibles: {list(VAULT_PATHS.keys())}")
    return Path(path_str)


def resolve_note_path(vault_root: Path, note_path: str) -> Path:
    """Résout le chemin absolu d'une note dans un vault."""
    p = vault_root / note_path
    if not p.suffix:
        p = p.with_suffix(".md")
    return p


def build_output(status: str, command: str, data: dict, dry_run: bool = False) -> dict:
    """Construit l'output contractuel skill_output.schema.json."""
    return {
        "status": status,
        "skill_name": "obsidian-goat",
        "skill_version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "output": {
            "command": command,
            "dry_run": dry_run,
            **data,
            "next_steps": []
        }
    }


def dry_run_report(command: str, ops: list[str], tokens_estimated: int = 50) -> dict:
    return build_output("dry_run", command, {
        "operations": ops,
        "tokens_estimated": tokens_estimated,
        "message": "Dry-run: aucune écriture effectuée"
    }, dry_run=True)


# ── Commandes ─────────────────────────────────────────────────────────────────
def cmd_read_note(args, conn: sqlite3.Connection, dry_run: bool) -> dict:
    """Lit une note depuis le vault."""
    vault_root = resolve_vault(args.vault)
    note_path  = resolve_note_path(vault_root, args.path)

    cache_key = f"read-note:{args.vault}:{args.path}"
    cached = cache_get(conn, cache_key)
    if cached and not dry_run:
        return build_output("success", "read-note", {**cached, "source": "cache"})

    if not note_path.exists():
        return build_output("error", "read-note", {
            "path": str(note_path),
            "message": f"Note introuvable: {args.path}"
        })

    content = note_path.read_text(encoding="utf-8")
    stat    = note_path.stat()
    result  = {
        "path":     args.path,
        "vault":    args.vault,
        "content":  content,
        "size":     stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "source":   "disk"
    }
    cache_set(conn, cache_key, {k: v for k, v in result.items() if k != "source"})
    return build_output("success", "read-note", result)


def cmd_write_note(args, conn: sqlite3.Connection, dry_run: bool) -> dict:
    """Écrit ou remplace une note dans le vault."""
    vault_root = resolve_vault(args.vault)
    note_path  = resolve_note_path(vault_root, args.path)
    exists     = note_path.exists()

    if dry_run:
        return dry_run_report("write-note", [
            f"{'OVERWRITE' if exists else 'CREATE'} {note_path}"
        ], 100)

    if exists and not args.force:
        return build_output("error", "write-note", {
            "path":    str(note_path),
            "message": f"Note existe déjà: {args.path}. Utiliser --force pour écraser ou check-note d'abord."
        })

    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(args.content, encoding="utf-8")

    # Invalider le cache
    cache_key = f"read-note:{args.vault}:{args.path}"
    conn.execute("DELETE FROM cache WHERE key=?", (cache_key,))
    conn.commit()

    return build_output("success", "write-note", {
        "path":   args.path,
        "vault":  args.vault,
        "action": "overwritten" if exists else "created",
        "size":   len(args.content.encode("utf-8"))
    })


def cmd_update_hot_cache(args, conn: sqlite3.Connection, dry_run: bool) -> dict:
    """Met à jour le HOT_CACHE dans le vault TricorderKit (claude-vault)."""
    vault_root = resolve_vault("claude-vault")
    hot_cache  = resolve_note_path(vault_root, HOT_CACHE_PATH)

    if dry_run:
        return dry_run_report("update-hot-cache", [
            f"WRITE {hot_cache}"
        ], 500)

    hot_cache.parent.mkdir(parents=True, exist_ok=True)

    # Ajouter un timestamp en tête si absent
    content = args.content
    if not content.startswith("# HOT_CACHE"):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        content = f"<!-- Mis à jour: {now} -->\n{content}"

    hot_cache.write_text(content, encoding="utf-8")

    # Invalider le cache
    conn.execute("DELETE FROM cache WHERE key LIKE '%HOT_CACHE%'")
    conn.commit()

    return build_output("success", "update-hot-cache", {
        "path":    HOT_CACHE_PATH,
        "vault":   "claude-vault",
        "action":  "updated",
        "size":    len(content.encode("utf-8")),
        "updated": datetime.now(timezone.utc).isoformat()
    })


def cmd_append_log(args, conn: sqlite3.Connection, dry_run: bool) -> dict:
    """Ajoute une entrée dans le Daily Log Obsidian."""
    vault_root = resolve_vault("claude-vault")

    # Déterminer la date
    if args.date:
        date_str = args.date
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # Valider le format date
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return build_output("error", "append-log", {
            "message": f"Format date invalide: '{date_str}'. Attendu: YYYY-MM-DD"
        })

    log_path = resolve_note_path(vault_root, f"{DAILY_LOG_FOLDER}/{date_str}.md")

    if dry_run:
        return dry_run_report("append-log", [
            f"APPEND to {log_path}"
        ], 100)

    # Créer le fichier si absent avec frontmatter minimal
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        frontmatter = (
            f"---\ntype: log\ntags: [\"#daily-log\"]\n"
            f"status: raw\ncreated: \"{date_str}\"\nauthor: claude\n---\n\n"
            f"# Daily Log — {date_str}\n\n"
        )
        log_path.write_text(frontmatter, encoding="utf-8")

    # Ajouter l'entrée
    timestamp  = datetime.now(timezone.utc).strftime("%H:%M")
    entry_text = f"\n## {timestamp} — {args.entry}\n"

    with log_path.open("a", encoding="utf-8") as f:
        f.write(entry_text)

    return build_output("success", "append-log", {
        "date":    date_str,
        "path":    f"{DAILY_LOG_FOLDER}/{date_str}.md",
        "vault":   "claude-vault",
        "entry":   args.entry,
        "appended_at": datetime.now(timezone.utc).isoformat()
    })


def cmd_check_note(args, conn: sqlite3.Connection, dry_run: bool) -> dict:
    """Vérifie l'existence d'une note dans le vault (anti-doublon R7)."""
    vault_root = resolve_vault(args.vault)
    note_path  = resolve_note_path(vault_root, args.path)
    exists     = note_path.exists()

    result = {
        "path":   args.path,
        "vault":  args.vault,
        "exists": exists,
    }

    if exists:
        stat = note_path.stat()
        result.update({
            "size":     stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        })

    return build_output("success", "check-note", result)


def cmd_list_notes(args, conn: sqlite3.Connection, dry_run: bool) -> dict:
    """Liste les notes d'un dossier dans le vault."""
    vault_root  = resolve_vault(args.vault)
    folder_path = vault_root / args.folder

    cache_key = f"list-notes:{args.vault}:{args.folder}"
    cached = cache_get(conn, cache_key)
    if cached:
        return build_output("success", "list-notes", {**cached, "source": "cache"})

    if not folder_path.exists():
        return build_output("error", "list-notes", {
            "folder":  args.folder,
            "message": f"Dossier introuvable: {args.folder}"
        })

    notes = []
    for p in sorted(folder_path.rglob("*.md")):
        stat = p.stat()
        notes.append({
            "path":     str(p.relative_to(vault_root)),
            "name":     p.stem,
            "size":     stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        })

    data = {
        "folder": args.folder,
        "vault":  args.vault,
        "count":  len(notes),
        "notes":  notes,
        "source": "disk"
    }
    cache_set(conn, cache_key, {k: v for k, v in data.items() if k != "source"})
    return build_output("success", "list-notes", data)


# ── Formatage output ──────────────────────────────────────────────────────────
def format_output(result: dict, fmt: str) -> str:
    if fmt == "table":
        command = result.get("output", {}).get("command", "?")
        status  = result.get("status", "?")
        lines   = [f"Command : {command}", f"Status  : {status}"]
        for k, v in result.get("output", {}).items():
            if k not in ("command", "dry_run", "next_steps"):
                lines.append(f"{k:12}: {v}")
        return "\n".join(lines)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    class JsonArgumentParser(argparse.ArgumentParser):
        def error(self, message):
            sys.stdout.write(json.dumps({"status": "error", "message": message, "recoverable": True}) + "\n")
            sys.stdout.flush()
            sys.exit(2)

    parser = JsonArgumentParser(
        description=f"obsidian-goat v{VERSION} — CLI déterministe Obsidian pour TricorderKit"
    )
    parser.add_argument("--dry-run",  action="store_true", help="Simuler sans écrire")
    parser.add_argument("--output",   choices=["json", "table"], default="json")
    parser.add_argument("--version",  action="version", version=f"obsidian-goat {VERSION}")

    subparsers = parser.add_subparsers(dest="command")

    # read-note
    p = subparsers.add_parser("read-note", help="Lire une note")
    p.add_argument("path",  help="Chemin relatif au vault (ex: Mangas/One_Piece.md)")
    p.add_argument("--vault", default="claude-vault")

    # write-note
    p = subparsers.add_parser("write-note", help="Écrire/créer une note")
    p.add_argument("path",    help="Chemin relatif au vault")
    p.add_argument("--content", required=True, help="Contenu Markdown de la note")
    p.add_argument("--vault",   default="claude-vault")
    p.add_argument("--force",   action="store_true", help="Écraser si la note existe")

    # update-hot-cache
    p = subparsers.add_parser("update-hot-cache", help="Mettre à jour le HOT_CACHE Obsidian")
    p.add_argument("--content", required=True, help="Nouveau contenu Markdown du HOT_CACHE")

    # append-log
    p = subparsers.add_parser("append-log", help="Ajouter une entrée dans le Daily Log")
    p.add_argument("--entry", required=True, help="Texte de l'entrée à ajouter")
    p.add_argument("--date",  default=None,  help="Date YYYY-MM-DD (défaut: aujourd'hui)")

    # check-note
    p = subparsers.add_parser("check-note", help="Vérifier l'existence d'une note (anti-doublon)")
    p.add_argument("path",  help="Chemin relatif au vault")
    p.add_argument("--vault", default="claude-vault")

    # list-notes
    p = subparsers.add_parser("list-notes", help="Lister les notes d'un dossier")
    p.add_argument("folder", help="Dossier relatif au vault (ex: Mangas/)")
    p.add_argument("--vault", default="claude-vault")

    args = parser.parse_args()

    if not args.command:
        print(json.dumps({
            "status": "error",
            "message": f"Commande requise. Disponibles: {SAFE_COMMANDS}"
        }))
        sys.exit(1)

    conn    = init_cache()
    dry_run = args.dry_run

    dispatch = {
        "read-note":        cmd_read_note,
        "write-note":       cmd_write_note,
        "update-hot-cache": cmd_update_hot_cache,
        "append-log":       cmd_append_log,
        "check-note":       cmd_check_note,
        "list-notes":       cmd_list_notes,
    }

    fn = dispatch.get(args.command)
    if not fn:
        sys.stdout.write(json.dumps({"status": "error", "message": f"Commande inconnue: {args.command}"}) + "\n"); sys.stdout.flush()
        sys.exit(1)

    try:
        result = fn(args, conn, dry_run)
        out = format_output(result, args.output)
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
    except ValueError as e:
        sys.stdout.write(json.dumps({"status": "error", "message": str(e), "recoverable": True}) + "\n")
        sys.stdout.flush()
        sys.exit(1)
    except Exception as e:
        sys.stdout.write(json.dumps({"status": "error", "message": str(e), "recoverable": False}) + "\n")
        sys.stdout.flush()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
