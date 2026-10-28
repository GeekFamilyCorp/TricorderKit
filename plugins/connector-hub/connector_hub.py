#!/usr/bin/env python3
"""
connector_hub.py — Connector Hub TricorderKit v0.8

Hub d'ingestion passif multi-sources.
Lit les déclarations sources de chaque linked_project actif,
construit un registre unifié et route vers le bon CLI.

Architecture :
  trusted_sources.yml (TK core)  ─┐                  ┌► collect_sources.py (sources core)
  sources.yaml (linked_project)  ─┼─► Connector Hub ─┤
  linked_projects.yaml (config)  ─┘                  └► CLI déclaré par le linked_project

Routage (aucune source n'est câblée en dur ici) :
  - source core (trusted_sources.yml, domaine <d>) →
      collect_sources.py --domain <d> --sources "<nom>" --query <requête>
  - source d'un linked_project → bloc `dispatch:` de son sources.yaml :
      dispatch:
        cli: scripts/ma_collecte.py      # chemin relatif à la racine du projet lié
        args: ["--since", "24h"]
    Sans bloc `dispatch:`, la source est listée mais non dispatchable.

Commandes :
  list                     → registre unifié de toutes les sources actives
  status                   → vérification de joignabilité (HTTP HEAD)
  dispatch [--source <id>] → déclenche l'ingestion d'une ou toutes les sources
  dispatch --all           → toutes les sources activées
  --dry-run                → simulation sans appel réseau ni subprocess

Usage :
  python plugins/connector-hub/connector_hub.py list
  python plugins/connector-hub/connector_hub.py list --format json
  python plugins/connector-hub/connector_hub.py status
  python plugins/connector-hub/connector_hub.py dispatch --source "arXiv API" --query "vector databases"
  python plugins/connector-hub/connector_hub.py dispatch --source research --dry-run
  python plugins/connector-hub/connector_hub.py dispatch --all --dry-run
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─── Paths ────────────────────────────────────────────────────────────────────
REPO_ROOT            = Path(__file__).resolve().parent.parent.parent
LINKED_PROJECTS_FILE = REPO_ROOT / "configs" / "local" / "linked_projects.yaml"
TRUSTED_SOURCES_FILE = REPO_ROOT / "plugins" / "deep-research-core" / "sources" / "trusted_sources.yml"
COLLECT_SOURCES      = REPO_ROOT / "plugins" / "deep-research-core" / "scripts" / "collect_sources.py"

VERSION = "0.2.0"

# Requête par défaut d'un dispatch de veille (surchargée par --query ou `watch_query` de la source)
DEFAULT_WATCH_QUERY = os.environ.get("TK_WATCH_QUERY", "local-first software")

# ─── Models ───────────────────────────────────────────────────────────────────

@dataclass
class Source:
    id: str
    name: str
    url: str
    source_type: str          # type déclaré dans sources.yaml
    reliability: str = "medium"
    language: str = "en"
    update_frequency: str = "daily"
    requires_auth: bool = False
    enabled: bool = True
    origin: str = ""          # linked_project_id ou "core"
    notes: str = ""
    domain: str = ""          # catégorie trusted_sources.yml (sources core)
    watch_query: str = ""     # requête de veille propre à la source (optionnelle)
    dispatch: Optional[dict] = None   # bloc `dispatch:` d'un linked_project (cli + args)
    project_root: Optional[Path] = None

    def matches(self, key: str) -> bool:
        """Une source est sélectionnée par id, nom, slug du nom, type ou domaine."""
        k = key.strip().casefold()
        return k in {
            self.id.casefold(),
            self.name.casefold(),
            _slug(self.name),
            self.source_type.casefold(),
            self.domain.casefold(),
        } - {""}

    def command_for(self, query: Optional[str] = None) -> Optional[list[str]]:
        """Arguments du CLI à lancer (sans l'interpréteur ni le chemin du CLI)."""
        if self.dispatch:
            return [str(a) for a in self.dispatch.get("args", [])]
        if self.origin == "core" and self.domain:
            q = query or self.watch_query or DEFAULT_WATCH_QUERY
            return ["--domain", self.domain, "--sources", self.name, "--query", q]
        return None

    @property
    def handler(self) -> Optional[dict]:
        if self.dispatch and self.dispatch.get("cli"):
            root = self.project_root or REPO_ROOT
            cli = Path(self.dispatch["cli"])
            return {
                "cli": cli if cli.is_absolute() else root / cli,
                "desc": self.dispatch.get("desc") or f"CLI déclaré par {self.origin}",
            }
        if self.origin == "core" and self.domain:
            return {
                "cli": COLLECT_SOURCES,
                "desc": f"collect_sources.py --domain {self.domain}",
            }
        return None

    @property
    def is_dispatchable(self) -> bool:
        return self.handler is not None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "type": self.source_type,
            "reliability": self.reliability,
            "language": self.language,
            "update_frequency": self.update_frequency,
            "requires_auth": self.requires_auth,
            "enabled": self.enabled,
            "origin": self.origin,
            "domain": self.domain,
            "dispatchable": self.is_dispatchable,
            "handler_desc": self.handler["desc"] if self.handler else None,
        }


@dataclass
class DispatchResult:
    source_id: str
    success: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    dry_run: bool = False
    command: list[str] = field(default_factory=list)
    duration_ms: int = 0
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "success": self.success,
            "dry_run": self.dry_run,
            "returncode": self.returncode,
            "command": [str(c) for c in self.command],
            "duration_ms": self.duration_ms,
            "error": self.error,
            "stdout_preview": self.stdout[:300] if self.stdout else "",
        }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load_yaml(path: Path) -> dict:
    try:
        import yaml
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except ImportError:
        return {}
    except FileNotFoundError:
        return {}


def _slug(name: str) -> str:
    out = "".join(c if c.isalnum() else "_" for c in name.casefold())
    return "_".join(p for p in out.split("_") if p)


def _load_linked_projects() -> list[dict]:
    cfg = _load_yaml(LINKED_PROJECTS_FILE)
    return [p for p in cfg.get("linked_projects", []) if p.get("enabled", False)]


def _sources_from_yaml(raw: dict, origin: str, project_root: Optional[Path] = None) -> list[Source]:
    """Convertit le sources.yaml d'un linked_project en liste de Source."""
    sources = []
    raw_sources = raw.get("sources", [])
    if not isinstance(raw_sources, list):
        return sources

    for s in raw_sources:
        if not isinstance(s, dict):
            continue
        dispatch = s.get("dispatch") if isinstance(s.get("dispatch"), dict) else None
        src_type = s.get("type", "").split("|")[0].strip().lower()
        sources.append(Source(
            id=s.get("id", f"{origin}_{len(sources)}"),
            name=s.get("name", ""),
            url=s.get("url", ""),
            source_type=src_type,
            reliability=str(s.get("reliability", "medium")),
            language=s.get("language", "en"),
            update_frequency=s.get("update_frequency", "daily"),
            requires_auth=bool(s.get("requires_auth", False)),
            enabled=bool(s.get("enabled", True)),
            origin=origin,
            notes=s.get("notes", ""),
            watch_query=str(s.get("watch_query", "") or ""),
            dispatch=dispatch,
            project_root=project_root,
        ))

    return sources


def _sources_from_trusted(raw: dict) -> list[Source]:
    """Convertit trusted_sources.yml (structure imbriquée) en liste de Source."""
    sources = []
    for category, items in raw.items():
        if category in ("scoring_weights",):
            continue
        if not isinstance(items, list):
            continue
        for s in items:
            if not isinstance(s, dict) or "url" not in s:
                continue
            src_type = s.get("type", "rest_api").replace("api_rest", "rest_api").lower()
            sources.append(Source(
                id=f"core_{_slug(s.get('name', '') or s['url'].split('/')[2])}",
                name=s.get("name", ""),
                url=s.get("url", ""),
                source_type=src_type,
                reliability=str(s.get("reliability", "medium")),
                language="en",
                update_frequency="daily",
                requires_auth=bool(s.get("auth_required", False)),
                enabled=True,
                origin="core",
                notes=s.get("notes", ""),
                domain=str(category),
                watch_query=str(s.get("watch_query", "") or ""),
            ))
    return sources


def build_registry() -> list[Source]:
    """Construit le registre unifié depuis TricorderKit + tous les linked_projects actifs."""
    registry: list[Source] = []
    seen_ids: set[str] = set()

    # 1. Sources deep-research-core (génériques)
    if TRUSTED_SOURCES_FILE.exists():
        raw = _load_yaml(TRUSTED_SOURCES_FILE)
        for src in _sources_from_trusted(raw):
            if src.id not in seen_ids:
                registry.append(src)
                seen_ids.add(src.id)

    # 2. Sources de chaque linked_project actif
    for project in _load_linked_projects():
        project_id = project.get("id", "unknown")
        project_root = Path(project.get("root", "."))
        sources_file = project_root / "project_config" / "sources.yaml"

        if not sources_file.exists():
            continue

        raw = _load_yaml(sources_file)
        for src in _sources_from_yaml(raw, origin=project_id, project_root=project_root):
            if src.id in seen_ids:
                # Préfixer pour éviter collision
                src.id = f"{project_id}_{src.id}"
            if src.id not in seen_ids:
                registry.append(src)
                seen_ids.add(src.id)

    return registry


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_list(args) -> dict:
    registry = build_registry()
    filtered = registry if args.all else [s for s in registry if s.enabled]

    return {
        "connector_hub_version": VERSION,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "total": len(filtered),
        "dispatchable": sum(1 for s in filtered if s.is_dispatchable),
        "sources": [s.to_dict() for s in filtered],
    }


def cmd_status(args) -> dict:
    """Vérifie la joignabilité de chaque source (HTTP HEAD, timeout court)."""
    try:
        import requests as req
        has_requests = True
    except ImportError:
        has_requests = False

    registry = build_registry()
    enabled = [s for s in registry if s.enabled]
    results = []

    for src in enabled:
        if not src.url or src.url.startswith("["):
            results.append({"id": src.id, "name": src.name, "status": "SKIPPED",
                            "reason": "URL non configurée"})
            continue

        if not has_requests:
            results.append({"id": src.id, "name": src.name, "status": "UNKNOWN",
                            "reason": "requests non installé"})
            continue

        if args.dry_run:
            results.append({"id": src.id, "name": src.name, "url": src.url,
                            "status": "DRY_RUN", "reason": "simulation"})
            continue

        try:
            t0 = time.time()
            r = req.head(src.url, timeout=5, allow_redirects=True,
                         headers={"User-Agent": "TricorderKit-Research/0.8"})
            ms = int((time.time() - t0) * 1000)
            status = "OK" if r.status_code < 400 else "DEGRADED"
            results.append({"id": src.id, "name": src.name, "url": src.url,
                            "status": status, "http_code": r.status_code, "latency_ms": ms})
        except Exception as e:
            results.append({"id": src.id, "name": src.name, "url": src.url,
                            "status": "UNREACHABLE", "reason": str(e)[:80]})

    ok       = sum(1 for r in results if r["status"] == "OK")
    degraded = sum(1 for r in results if r["status"] == "DEGRADED")
    down     = sum(1 for r in results if r["status"] == "UNREACHABLE")

    return {
        "connector_hub_version": VERSION,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "summary": {"ok": ok, "degraded": degraded, "unreachable": down,
                    "skipped": len(results) - ok - degraded - down},
        "sources": results,
    }


def _dispatch_source(src: Source, dry_run: bool, query: Optional[str] = None) -> DispatchResult:
    """Déclenche l'ingestion pour une source. Retourne un DispatchResult."""
    handler = src.handler
    args = src.command_for(query)
    if not handler or args is None:
        return DispatchResult(
            source_id=src.id, success=False,
            error=(f"Source '{src.id}' non dispatchable — déclarer un bloc `dispatch:` "
                   "(cli + args) dans le sources.yaml du linked_project"),
        )

    cli_path = handler["cli"]
    if not cli_path.exists():
        return DispatchResult(
            source_id=src.id, success=False,
            error=f"CLI introuvable : {cli_path}",
        )

    command = [sys.executable, str(cli_path)] + args + ["--dry-run"]

    if dry_run:
        return DispatchResult(
            source_id=src.id, success=True, dry_run=True,
            command=command,
            stdout=f"[DRY-RUN] Commande simulée : {' '.join(str(c) for c in command)}",
        )

    # Appel réel — on retire le --dry-run ajouté ci-dessus
    real_command = [sys.executable, str(cli_path)] + args
    env = {**os.environ, "PYTHONUTF8": "1"}
    t0 = time.time()
    try:
        r = subprocess.run(
            real_command,
            capture_output=True, text=True,
            encoding="utf-8-sig", errors="replace",
            timeout=30,
            cwd=str(REPO_ROOT), env=env,
        )
        ms = int((time.time() - t0) * 1000)
        return DispatchResult(
            source_id=src.id, success=(r.returncode == 0),
            stdout=r.stdout, stderr=r.stderr,
            returncode=r.returncode, command=real_command,
            duration_ms=ms,
            error=r.stderr[:200] if r.returncode != 0 else "",
        )
    except subprocess.TimeoutExpired:
        return DispatchResult(
            source_id=src.id, success=False, command=real_command,
            error="Timeout (30s) dépassé",
        )
    except Exception as e:
        return DispatchResult(
            source_id=src.id, success=False, command=real_command,
            error=str(e),
        )


def cmd_dispatch(args) -> dict:
    registry = build_registry()
    enabled  = [s for s in registry if s.enabled and s.is_dispatchable]
    temporal_flag = getattr(args, "temporal", False)

    if args.source:
        targets = [s for s in enabled if s.matches(args.source)]
        if not targets:
            all_ids = [s.id for s in registry]
            return {
                "connector_hub_version": VERSION,
                "error": f"Source '{args.source}' introuvable ou non dispatchable",
                "available_ids": all_ids[:20],
            }
    elif args.all:
        targets = enabled
    else:
        return {
            "connector_hub_version": VERSION,
            "error": "Spécifier --source <id|type> ou --all",
        }

    # ── Mode Temporal : déléguer à dispatch_temporal.py ──────────────────────
    if temporal_flag:
        return _dispatch_via_temporal(targets, args)

    # ── Mode CLI direct (comportement par défaut) ─────────────────────────────
    results = []
    for src in targets:
        result = _dispatch_source(src, dry_run=args.dry_run, query=getattr(args, "query", None))
        results.append(result.to_dict())

    success_count = sum(1 for r in results if r["success"])
    return {
        "connector_hub_version": VERSION,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "mode": "cli-direct",
        "dispatched": len(results),
        "success": success_count,
        "failed": len(results) - success_count,
        "results": results,
    }


def _dispatch_via_temporal(targets: list, args) -> dict:
    """Délègue le dispatch à Temporal via dispatch_temporal.py."""
    # Le workflow reçoit des noms de sources ; chaque activité rappelle
    # `connector_hub.py dispatch --source <nom>` (routage centralisé ici).
    source_names = sorted({s.name or s.id for s in targets})
    dispatch_script = REPO_ROOT / "plugins" / "connector-hub" / "scripts" / "dispatch_temporal.py"

    if not dispatch_script.exists():
        return {
            "connector_hub_version": VERSION,
            "error": f"dispatch_temporal.py introuvable: {dispatch_script}",
            "suggestion": "Vérifier plugins/connector-hub/scripts/",
        }

    interval = getattr(args, "interval", 60)
    # --dry-run is a global flag (before subcommand) in dispatch_temporal.py
    cmd = [sys.executable, str(dispatch_script)]
    if args.dry_run:
        cmd.append("--dry-run")
    cmd += ["dispatch",
            "--workflow", "source-watch",
            "--source"] + source_names
    cmd += ["--interval", str(interval)]

    env = {**os.environ, "PYTHONUTF8": "1"}
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=15, cwd=str(REPO_ROOT), env=env,
        )
        if r.stdout.strip():
            result = json.loads(r.stdout.strip())
        else:
            result = {"status": "error", "message": r.stderr.strip()[:500]}
        return {
            "connector_hub_version": VERSION,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "dry_run": args.dry_run,
            "mode": "temporal",
            "sources": source_names,
            "temporal_result": result,
        }
    except subprocess.TimeoutExpired:
        return {
            "connector_hub_version": VERSION,
            "error": "Timeout dispatch_temporal.py (15s)",
            "suggestion": "Vérifier que Temporal est démarré: docker compose ps",
        }
    except json.JSONDecodeError as e:
        return {
            "connector_hub_version": VERSION,
            "error": f"Output non-JSON de dispatch_temporal: {e}",
        }


# ─── Output formatters ────────────────────────────────────────────────────────

def _c(code: str, s: str) -> str:
    """Couleur ANSI si stdout est un terminal."""
    if not sys.stdout.isatty():
        return s
    colors = {"g": "\033[92m", "y": "\033[93m", "r": "\033[91m", "b": "\033[1m"}
    return f"{colors.get(code, '')}{s}\033[0m"


def print_markdown(data: dict, command: str) -> None:
    if command == "list":
        sources = data.get("sources", [])
        print()
        print(_c("b", f"═══ Connector Hub — Registre sources [{data['total']} total, {data['dispatchable']} dispatchables] ═══"))
        print()
        for s in sources:
            status = _c("g", "✅") if s["enabled"] else _c("y", "⏸")
            dispatch = _c("g", "→") if s["dispatchable"] else _c("y", "✗")
            print(f"  {status} {dispatch}  {s['id']:<30} [{s['type']:<10}]  {s['name']}")
        print()

    elif command == "status":
        sources = data.get("sources", [])
        summary = data.get("summary", {})
        print()
        print(_c("b", "═══ Connector Hub — Statut sources ═══"))
        print(f"  {_c('g', str(summary.get('ok', 0)) + ' OK')}  "
              f"{_c('y', str(summary.get('degraded', 0)) + ' DEGRADED')}  "
              f"{_c('r', str(summary.get('unreachable', 0)) + ' DOWN')}")
        print()
        for s in sources:
            st = s["status"]
            icon = {"OK": _c("g", "✅"), "DEGRADED": _c("y", "⚠️"),
                    "UNREACHABLE": _c("r", "❌"), "SKIPPED": "·",
                    "DRY_RUN": "~", "UNKNOWN": "?"}.get(st, "?")
            lat = f" ({s.get('latency_ms', '')}ms)" if st == "OK" else ""
            print(f"  {icon}  {s['id']:<30}  {st}{lat}")
        print()

    elif command == "dispatch":
        results = data.get("results", [])
        print()
        print(_c("b", f"═══ Connector Hub — Dispatch [{data['dispatched']} lancés, {data['success']} OK] ═══"))
        if data.get("dry_run"):
            print(_c("y", "  ⚠️  Mode DRY-RUN — aucun appel réseau effectué"))
        print()
        for r in results:
            icon = _c("g", "✅") if r["success"] else _c("r", "❌")
            ms = f" ({r.get('duration_ms', 0)}ms)" if not r.get("dry_run") else " (simulé)"
            cmd_str = " ".join(r.get("command", [])[-3:]) if r.get("command") else ""
            print(f"  {icon}  {r['source_id']:<30}  {cmd_str}{ms}")
            if r.get("error"):
                print(f"         {_c('r', r['error'])}")
        print()


def print_json_output(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="connector_hub",
        description="Connector Hub TricorderKit v0.8 — Hub d'ingestion passif multi-sources",
    )
    parser.add_argument("--version", action="version", version=f"connector_hub {VERSION}")

    # Parent parser pour --format (hérité par chaque sous-commande)
    fmt_parent = argparse.ArgumentParser(add_help=False)
    fmt_parent.add_argument("--format", choices=["markdown", "json", "md"], default="markdown",
                            help="Format de sortie (défaut: markdown)")

    sub = parser.add_subparsers(dest="command", metavar="<commande>")

    # list
    p_list = sub.add_parser("list", parents=[fmt_parent],
                             help="Lister toutes les sources déclarées")
    p_list.add_argument("--all", action="store_true",
                        help="Inclure les sources désactivées")

    # status
    p_status = sub.add_parser("status", parents=[fmt_parent],
                               help="Vérifier la joignabilité des sources")
    p_status.add_argument("--dry-run", action="store_true")

    # dispatch
    p_dispatch = sub.add_parser("dispatch", parents=[fmt_parent],
                                 help="Déclencher l'ingestion d'une ou plusieurs sources")
    p_dispatch.add_argument("--source", "-s", default=None,
                            help="ID, nom, type ou domaine de source (ex: \"arXiv API\", core_github_api, research)")
    p_dispatch.add_argument("--query", "-q", default=None,
                            help=f"Requête de veille pour les sources core (défaut: watch_query de la source, sinon {DEFAULT_WATCH_QUERY!r})")
    p_dispatch.add_argument("--all", "-a", action="store_true",
                            help="Dispatcher toutes les sources actives")
    p_dispatch.add_argument("--dry-run", action="store_true",
                            help="Simulation — affiche les commandes sans les exécuter")
    p_dispatch.add_argument("--temporal", action="store_true",
                            help="Déclencher via Temporal (source-watch.workflow) au lieu du CLI direct")
    p_dispatch.add_argument("--interval", type=int, default=60,
                            help="Intervalle en minutes pour le workflow Temporal (défaut: 60)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    fmt = args.format

    dispatch = {
        "list":     cmd_list,
        "status":   cmd_status,
        "dispatch": cmd_dispatch,
    }

    fn = dispatch.get(args.command)
    if not fn:
        print(json.dumps({"error": f"Commande inconnue : {args.command}"}))
        sys.exit(1)

    data = fn(args)

    if fmt in ("json",):
        print_json_output(data)
    else:
        print_markdown(data, args.command)


if __name__ == "__main__":
    main()
