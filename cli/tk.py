#!/usr/bin/env python3
"""
tk — TricorderKit CLI v0.1.0
Entrypoint principal pour l'écosystème TricorderKit.

Commandes :
  tk status              → état général du système
  tk doctor              → health-check tous les services
  tk project list        → lister les linked_projects actifs
  tk project status [id] → état d'un linked_project

Usage :
  python cli/tk.py status
  python cli/tk.py doctor
  python cli/tk.py project list
  python cli/tk.py project status japan-alliance
"""

from __future__ import annotations

import argparse
import importlib
import io
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Force UTF-8 stdout sur Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─── Paths ────────────────────────────────────────────────────────────────────
REPO_ROOT             = Path(__file__).resolve().parent.parent
STATE_FILE            = REPO_ROOT / ".planning" / "STATE.md"
LINKED_PROJECTS_FILE  = REPO_ROOT / "configs" / "local" / "linked_projects.yaml"
LINKED_PROJECTS_EXAMPLE = REPO_ROOT / "configs" / "local" / "linked_projects.example.yaml"

# ─── Colors ───────────────────────────────────────────────────────────────────
def _g(s):  return f"\033[92m{s}\033[0m"   # green
def _y(s):  return f"\033[93m{s}\033[0m"   # yellow
def _r(s):  return f"\033[91m{s}\033[0m"   # red
def _b(s):  return f"\033[1m{s}\033[0m"    # bold

def _ok(label, detail=""):
    print(f"  {_g('✅')} {label}" + (f"  {detail}" if detail else ""))

def _warn(label, detail=""):
    print(f"  {_y('⚠️')} {label}" + (f"  {detail}" if detail else ""))

def _fail(label, detail=""):
    print(f"  {_r('❌')} {label}" + (f"  {detail}" if detail else ""))

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load_yaml(path: Path) -> dict:
    try:
        import yaml
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except ImportError:
        return {}
    except FileNotFoundError:
        return {}


def _docker_status(name: str) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            ["docker", "ps", "--filter", f"name={name}", "--format", "{{.Status}}"],
            capture_output=True, text=True, timeout=5,
        )
        out = r.stdout.strip().splitlines()
        out = [l for l in out if name in l or True]  # premier résultat
        first = out[0] if out else ""
        return bool(first) and "Up" in first, first or "not running"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "docker unreachable"


def _git_info(cwd: Path = REPO_ROOT) -> dict:
    def _run(*args):
        return subprocess.run(list(args), capture_output=True, text=True,
                              cwd=cwd, timeout=5).stdout.strip()
    try:
        return {
            "branch": _run("git", "branch", "--show-current"),
            "commit": _run("git", "rev-parse", "--short", "HEAD"),
            "dirty":  _run("git", "status", "--porcelain"),
            "ahead":  _run("git", "rev-list", "--count", "HEAD@{u}..HEAD"),
        }
    except Exception:
        return {}


def _state_field(key: str) -> str:
    if not STATE_FILE.exists():
        return "unknown"
    for line in STATE_FILE.read_text(encoding="utf-8").splitlines():
        if f"**{key}**" in line:
            return line.split(":", 1)[-1].strip().rstrip("*").strip()
    return "unknown"


# ─── status ───────────────────────────────────────────────────────────────────

def cmd_status(_args):
    g = _git_info()
    print()
    print(_b("═══ TricorderKit Status ═══"))
    print(f"  Version  : {_b('v' + _state_field('Version'))}")
    print(f"  Phase    : {_state_field('Phase active')}")
    print(f"  Commit   : {g.get('commit', '?')}  [{g.get('branch', '?')}]")
    print(f"  Root     : {REPO_ROOT}")
    print()
    print(_b("Services Docker :"))
    for cname, label in [
        ("tricorder-neo4j",     "Neo4j          :7687"),
        ("tricorder-qdrant",    "Qdrant         :6333"),
        ("tricorder-langfuse",  "Langfuse       :3001"),
        ("temporal",            "Temporal       :7233"),
    ]:
        up, detail = _docker_status(cname)
        (_ok if up else _fail)(label, detail)
    print()
    print(_b("Linked projects :"))
    if not LINKED_PROJECTS_FILE.exists():
        _warn("linked_projects.yaml manquant", f"créer depuis {LINKED_PROJECTS_EXAMPLE.name}")
    else:
        cfg = _load_yaml(LINKED_PROJECTS_FILE)
        for p in cfg.get("linked_projects", []):
            pid, root = p.get("id", "?"), Path(p.get("root", "."))
            ok = p.get("enabled") and root.exists()
            (_ok if ok else _warn)(f"{p.get('name', pid)} [{pid}]",
                                   str(root) if ok else f"manquant : {root}")
    print()


# ─── doctor ───────────────────────────────────────────────────────────────────

def cmd_doctor(_args):
    print()
    print(_b("═══ TricorderKit Doctor ═══"))
    print()

    # Python
    print(_b("Python :"))
    v = sys.version_info
    (_ok if v >= (3, 11) else _fail)(
        f"Python {v.major}.{v.minor}.{v.micro}", sys.executable
    )

    # Dépendances
    print()
    print(_b("Dépendances Python :"))
    for dep, mod in [("requests","requests"), ("httpx","httpx"), ("rich","rich"),
                     ("pyyaml","yaml"), ("qdrant-client","qdrant_client"),
                     ("temporalio","temporalio"), ("feedparser","feedparser")]:
        try:
            importlib.import_module(mod)
            _ok(dep)
        except ImportError:
            _warn(dep, f"manquant — pip install {dep}")

    # Docker
    print()
    print(_b("Docker containers :"))
    all_up = True
    for cname, label in [
        ("tricorder-neo4j",     "Neo4j   :7687"),
        ("tricorder-qdrant",    "Qdrant  :6333"),
        ("tricorder-langfuse",  "Langfuse:3001"),
        ("temporal",            "Temporal:7233"),
    ]:
        up, detail = _docker_status(cname)
        (_ok if up else _fail)(label, detail)
        all_up = all_up and up

    # Fichiers critiques
    print()
    print(_b("Fichiers critiques :"))
    for f in [STATE_FILE,
              REPO_ROOT / ".planning" / "DECISIONS.md",
              REPO_ROOT / "core" / "contracts" / "skill_output.schema.json",
              LINKED_PROJECTS_FILE]:
        if f.exists():
            _ok(f.relative_to(REPO_ROOT))
        else:
            if "linked_projects.yaml" in f.name:
                _warn(f.relative_to(REPO_ROOT), "à créer depuis l'example")
            else:
                _fail(f.relative_to(REPO_ROOT))

    # Git
    print()
    print(_b("Git :"))
    g = _git_info()
    if g:
        _ok(f"Branch {g['branch']} @ {g['commit']}")
        ahead = g.get("ahead", "0")
        (_ok if ahead == "0" else _warn)(
            "Synchronisé avec origin/main" if ahead == "0"
            else f"{ahead} commit(s) non poussés"
        )
        dirty = g.get("dirty", "")
        (_ok if not dirty else _warn)(
            "Working tree propre" if not dirty
            else f"{len(dirty.splitlines())} fichier(s) modifiés"
        )
    else:
        _fail("Git inaccessible")

    print()
    print(f"  {_g('✅ Doctor OK') if all_up else _y('⚠️  Certains services arrêtés')}")
    print()


# ─── project list ─────────────────────────────────────────────────────────────

def cmd_project_list(_args):
    print()
    print(_b("═══ Linked Projects ═══"))
    print()
    if not LINKED_PROJECTS_FILE.exists():
        _warn("linked_projects.yaml manquant")
        print(f"\n  Créer depuis : {LINKED_PROJECTS_EXAMPLE}\n")
        sys.exit(1)
    cfg = _load_yaml(LINKED_PROJECTS_FILE)
    if not cfg:
        print("  ⚠️  PyYAML non installé — pip install pyyaml\n")
        sys.exit(1)
    projects = cfg.get("linked_projects", [])
    if not projects:
        print("  Aucun projet déclaré.\n")
        return
    print(f"  {'ID':<20} {'NOM':<22} {'DOMAINE':<32} {'EN':<4}  ROOT")
    print("  " + "─" * 95)
    for p in projects:
        pid    = p.get("id", "?")
        name   = p.get("name", pid)
        domain = p.get("domain", "—")
        root   = p.get("root", "?")
        en     = p.get("enabled", False)
        exists = Path(root).exists()
        en_str = _g("yes") if en else _y("no")
        root_s = (_g(root) if exists else _r(root + " ⚠️")) if en else root
        print(f"  {pid:<20} {name:<22} {domain:<32} {en_str:<4}  {root_s}")
    print()


# ─── project status ───────────────────────────────────────────────────────────

def cmd_project_status(args):
    if not LINKED_PROJECTS_FILE.exists():
        print(_r("❌ linked_projects.yaml manquant"), file=sys.stderr)
        sys.exit(1)
    cfg = _load_yaml(LINKED_PROJECTS_FILE)
    if not cfg:
        print("⚠️  PyYAML non installé — pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    projects = cfg.get("linked_projects", [])
    pid = getattr(args, "project_id", None)
    if not pid:
        pid = projects[0].get("id") if projects else None
        if pid:
            print(f"  (Aucun ID fourni — affichage de '{pid}')\n")
    p = next((x for x in projects if x.get("id") == pid), None)
    if not p:
        print(_r(f"❌ Projet '{pid}' introuvable"), file=sys.stderr)
        sys.exit(1)

    root = Path(p.get("root", "."))
    print()
    print(_b(f"═══ Projet : {p.get('name', pid)} [{pid}] ═══"))
    print()
    print(f"  GitHub   : {p.get('github_repo', '—')}")
    print(f"  Domaine  : {p.get('domain', '—')}")
    print(f"  Activé   : {_g('oui') if p.get('enabled') else _y('non')}")
    print(f"  Root     : {root}")
    print()

    print(_b("Répertoires :"))
    for key, rel in p.get("paths", {}).items():
        full = root / rel
        state = _g("✅") if full.exists() else _r("❌ manquant")
        print(f"  {key:<12} {state}  {full}")
    print()

    if root.exists():
        print(_b("Git :"))
        g = _git_info(root)
        if g:
            _ok(f"Branch {g['branch']} @ {g['commit']}")
            (_ok if not g["dirty"] else _warn)(
                "Working tree propre" if not g["dirty"]
                else f"{len(g['dirty'].splitlines())} fichier(s) modifiés"
            )
        else:
            _fail("Git inaccessible")
    print()


# ─── CLI parser ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="tk",
        description="TricorderKit CLI v0.1.0 — Agentic Knowledge OS",
    )
    sub = parser.add_subparsers(dest="command", metavar="<commande>")

    # status
    sub.add_parser("status", help="État général du système")

    # doctor
    sub.add_parser("doctor", help="Health-check tous les services")

    # project
    p_project = sub.add_parser("project", help="Commandes linked_project")
    p_sub = p_project.add_subparsers(dest="project_cmd", metavar="<sous-commande>")
    p_sub.add_parser("list", help="Lister les linked_projects")
    p_status = p_sub.add_parser("status", help="État d'un linked_project")
    p_status.add_argument("project_id", nargs="?", help="ID du projet (ex: japan-alliance)")

    args = parser.parse_args()

    dispatch = {
        "status":  cmd_status,
        "doctor":  cmd_doctor,
    }

    if args.command in dispatch:
        dispatch[args.command](args)
    elif args.command == "project":
        if args.project_cmd == "list":
            cmd_project_list(args)
        elif args.project_cmd == "status":
            cmd_project_status(args)
        else:
            p_project.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
