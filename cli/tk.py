#!/usr/bin/env python3
"""
tk — TricorderKit CLI v0.2.0
Entrypoint principal pour l'écosystème TricorderKit.

Commandes :
  tk status                     → état général du système
  tk health                     → alias de doctor (health-check rapide)
  tk doctor                     → health-check détaillé tous les services
  tk rapport                    → rapport plugins depuis BOOT_SUMMARY.md + STATUS.md
  tk rapport --json             → rapport + latest_status.json
  tk report generate            → génère STATUS.md + rapport daté dans reports/
  tk report show                → affiche STATUS.md en terminal
  tk skill list                 → lister les skills disponibles
  tk workflow list              → lister les workflows disponibles
  tk vault scan                 → scanner le vault TricorderKit
  tk research run [query]       → lancer deep-research (--dry-run supporté)
  tk project list               → lister les linked_projects
  tk project status [id]        → état d'un linked_project
  tk project audit [id]         → audit complet d'un linked_project
  tk project vault scan [id]    → scanner le vault d'un linked_project
  tk project workflow list [id] → lister les workflows d'un linked_project

Options globales : --format json|md (défaut: markdown)

Usage :
  python cli/tk.py status
  python cli/tk.py status --format json
  python cli/tk.py doctor
  python cli/tk.py rapport
  python cli/tk.py rapport --json
  python cli/tk.py skill list
  python cli/tk.py workflow list
  python cli/tk.py vault scan
  python cli/tk.py report generate
  python cli/tk.py report generate --no-status-md   # rapport seul
  python cli/tk.py report show
  python cli/tk.py research run "One Piece" --dry-run
  python cli/tk.py project list
  python cli/tk.py project audit japan-alliance
  python cli/tk.py project vault scan japan-alliance
  python cli/tk.py project workflow list japan-alliance
"""

from __future__ import annotations

import argparse
import datetime
import importlib
import io
import json
import subprocess
import sys
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
REPO_ROOT             = Path(__file__).resolve().parent.parent
STATE_FILE            = REPO_ROOT / ".planning" / "STATE.md"
LINKED_PROJECTS_FILE  = REPO_ROOT / "configs" / "local" / "linked_projects.yaml"
LINKED_PROJECTS_EXAMPLE = REPO_ROOT / "configs" / "local" / "linked_projects.example.yaml"
SKILLS_DIR            = REPO_ROOT / "skills"
PLUGINS_DIR           = REPO_ROOT / "plugins"
WORKFLOWS_DIR         = REPO_ROOT / "plugins" / "workflow-engine" / "workflows"
VAULT_DIR             = REPO_ROOT / "vault"

# ─── Colors ───────────────────────────────────────────────────────────────────
def _g(s):  return f"\033[92m{s}\033[0m"
def _y(s):  return f"\033[93m{s}\033[0m"
def _r(s):  return f"\033[91m{s}\033[0m"
def _b(s):  return f"\033[1m{s}\033[0m"
def _ok(lbl, d=""): print(f"  {_g('✅')} {lbl}" + (f"  {d}" if d else ""))
def _warn(lbl, d=""): print(f"  {_y('⚠️')} {lbl}" + (f"  {d}" if d else ""))
def _fail(lbl, d=""): print(f"  {_r('❌')} {lbl}" + (f"  {d}" if d else ""))

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _yaml(path: Path) -> dict:
    try:
        import yaml
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}

def _docker(name: str) -> tuple[bool, str]:
    try:
        r = subprocess.run(["docker", "ps", "--filter", f"name={name}",
                            "--format", "{{.Status}}"],
                           capture_output=True, text=True, timeout=5)
        out = r.stdout.strip().splitlines()
        first = out[0] if out else ""
        return bool(first) and "Up" in first, first or "not running"
    except Exception:
        return False, "docker unreachable"

def _git(*args, cwd=REPO_ROOT) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True,
                              cwd=cwd, timeout=5).stdout.strip()
    except Exception:
        return ""

def _state(key: str) -> str:
    if not STATE_FILE.exists(): return "unknown"
    for line in STATE_FILE.read_text(encoding="utf-8").splitlines():
        if f"**{key}**" in line:
            return line.split(":", 1)[-1].strip().rstrip("*").strip()
    return "unknown"

def _linked_projects() -> list[dict]:
    return _yaml(LINKED_PROJECTS_FILE).get("linked_projects", [])

def _get_project(pid: str | None) -> dict | None:
    projects = _linked_projects()
    if not pid:
        return projects[0] if projects else None
    return next((p for p in projects if p.get("id") == pid), None)

# ─── JSON output helpers ──────────────────────────────────────────────────────

def _jprint(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


# ═══════════════════════════════════════════════════════════════════════════════
# COMMANDES
# ═══════════════════════════════════════════════════════════════════════════════

# ── status ────────────────────────────────────────────────────────────────────

def cmd_status(args):
    commit = _git("rev-parse", "--short", "HEAD")
    branch = _git("branch", "--show-current")
    services = [
        ("tricorder-neo4j",     "Neo4j   :7687"),
        ("tricorder-qdrant",    "Qdrant  :6333"),
        ("tricorder-langfuse",  "Langfuse:3001"),
        ("temporal",            "Temporal:7233"),
    ]
    svc_data = {lbl: _docker(c) for c, lbl in services}
    projects = _linked_projects()

    if args.format == "json":
        _jprint({
            "version": _state("Version"),
            "phase": _state("Phase active"),
            "commit": commit, "branch": branch,
            "services": {lbl: {"up": up, "detail": det} for lbl, (up, det) in svc_data.items()},
            "linked_projects": [
                {"id": p.get("id"), "name": p.get("name"),
                 "enabled": p.get("enabled"), "root_exists": Path(p.get("root","")).exists()}
                for p in projects
            ],
        })
        return

    print()
    print(_b("═══ TricorderKit Status ═══"))
    print(f"  Version  : {_b('v' + _state('Version'))}")
    print(f"  Phase    : {_state('Phase active')}")
    print(f"  Commit   : {commit}  [{branch}]")
    print(f"  Root     : {REPO_ROOT}")
    print()
    print(_b("Services Docker :"))
    for c, lbl in services:
        up, det = _docker(c)
        (_ok if up else _fail)(lbl, det)
    print()
    print(_b("Linked projects :"))
    if not LINKED_PROJECTS_FILE.exists():
        _warn("linked_projects.yaml manquant")
    else:
        for p in projects:
            pid, root = p.get("id","?"), Path(p.get("root","."))
            ok = p.get("enabled") and root.exists()
            (_ok if ok else _warn)(f"{p.get('name', pid)} [{pid}]",
                                   str(root) if ok else f"manquant : {root}")
    print()


# ── doctor / health ───────────────────────────────────────────────────────────

def _check_env() -> dict[str, bool]:
    """Check .env file and required environment variables."""
    import os
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return {}
    # Parse .env manually (no python-dotenv required)
    defined: set[str] = set()
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key = line.split("=", 1)[0].strip()
            val = line.split("=", 1)[1].strip()
            if val and not val.startswith("your_") and val not in ("/path/to/your/obsidian/vault",):
                defined.add(key)
    required = [
        "ANTHROPIC_API_KEY",
        "NEO4J_URI",
        "QDRANT_URL",
        "TEMPORAL_ADDRESS",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "OBSIDIAN_VAULT_PATH",
    ]
    return {k: k in defined for k in required}


def _check_plugins() -> dict[str, dict]:
    """Check each plugin has manifest.yml and optional README."""
    results = {}
    if not PLUGINS_DIR.exists():
        return results
    for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
        if not plugin_dir.is_dir():
            continue
        has_manifest = (plugin_dir / "manifest.yml").exists()
        has_readme = (plugin_dir / "README.md").exists()
        test_count = len(list((plugin_dir / "tests").glob("test_*.py"))) if (plugin_dir / "tests").exists() else 0
        results[plugin_dir.name] = {
            "manifest": has_manifest,
            "readme": has_readme,
            "tests": test_count,
        }
    return results


def cmd_doctor(args):
    v = sys.version_info
    deps = [("requests","requests"), ("httpx","httpx"), ("rich","rich"),
            ("pyyaml","yaml"), ("qdrant-client","qdrant_client"),
            ("temporalio","temporalio"), ("feedparser","feedparser")]
    dep_results = {}
    for name, mod in deps:
        try: importlib.import_module(mod); dep_results[name] = True
        except ImportError: dep_results[name] = False

    svc_list = [("tricorder-neo4j","Neo4j"), ("tricorder-qdrant","Qdrant"),
                ("tricorder-langfuse","Langfuse"), ("temporal","Temporal")]
    svc_results = {lbl: _docker(c) for c, lbl in svc_list}

    critical_files = {
        "STATE.md": STATE_FILE.exists(),
        "DECISIONS.md": (REPO_ROOT / ".planning" / "DECISIONS.md").exists(),
        "skill_output.schema.json": (REPO_ROOT / "core" / "contracts" / "skill_output.schema.json").exists(),
        "linked_projects.yaml": LINKED_PROJECTS_FILE.exists(),
        ".env": (REPO_ROOT / ".env").exists(),
    }
    env_vars = _check_env()
    plugin_results = _check_plugins()
    dirty = _git("status", "--porcelain")
    ahead = _git("rev-list", "--count", "HEAD@{u}..HEAD") or "0"
    all_up = all(up for up, _ in svc_results.values())
    env_ok = all(env_vars.values()) if env_vars else False

    if args.format == "json":
        _jprint({
            "python": f"{v.major}.{v.minor}.{v.micro}",
            "python_ok": v >= (3, 11),
            "dependencies": dep_results,
            "services": {lbl: {"up": up, "detail": det} for lbl, (up, det) in svc_results.items()},
            "critical_files": critical_files,
            "env_vars": env_vars,
            "plugins": plugin_results,
            "git": {"ahead": ahead, "dirty_count": len(dirty.splitlines()) if dirty else 0},
            "overall": "OK" if (all_up and env_ok) else "WARN",
        })
        return

    print()
    print(_b("═══ TricorderKit Doctor ═══"))
    print()

    print(_b("Python :"))
    (_ok if v >= (3, 11) else _fail)(f"Python {v.major}.{v.minor}.{v.micro}", sys.executable)
    print()

    print(_b("Dépendances :"))
    for name, ok in dep_results.items():
        (_ok if ok else _warn)(name, "" if ok else f"pip install {name}")
    print()

    print(_b("Variables d'environnement (.env) :"))
    if not (REPO_ROOT / ".env").exists():
        _fail(".env manquant", "cp .env.example .env  puis remplir les valeurs")
    elif not env_vars:
        _warn(".env présent", "impossible de parser")
    else:
        for var, ok in env_vars.items():
            (_ok if ok else _warn)(var, "" if ok else "non définie ou valeur placeholder")
    print()

    print(_b("Docker :"))
    for lbl, (up, det) in svc_results.items():
        (_ok if up else _fail)(lbl, det)
    print()

    print(_b("Plugins :"))
    for name, info in plugin_results.items():
        status = "✅" if info["manifest"] else "❌"
        readme = " README" if info["readme"] else ""
        tests = f" {info['tests']} test(s)" if info["tests"] else " 0 tests"
        print(f"  {_g(status) if info['manifest'] else _r(status)} {name:<30} manifest={'✅' if info['manifest'] else '—'}{readme}{tests}")
    print()

    print(_b("Fichiers critiques :"))
    for name, ok in critical_files.items():
        is_optional = name in ("linked_projects.yaml", ".env")
        (_ok if ok else (_warn if is_optional else _fail))(name)
    print()

    print(_b("Git :"))
    _ok(f"Branch {_git('branch', '--show-current')} @ {_git('rev-parse', '--short', 'HEAD')}")
    (_ok if ahead == "0" else _warn)(
        "Synchronisé" if ahead == "0" else f"{ahead} commit(s) non poussés")
    (_ok if not dirty else _warn)(
        "Working tree propre" if not dirty else f"{len(dirty.splitlines())} fichier(s) modifiés")
    print()

    overall_ok = all_up and env_ok
    print(f"  {_g('✅ Doctor OK') if overall_ok else _y('⚠️  Vérifier les points ci-dessus')}")
    print()


# ── skill list ────────────────────────────────────────────────────────────────

def cmd_skill_list(args):
    skills = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()) if SKILLS_DIR.exists() else []:
        if skill_dir.is_dir():
            skill_md = skill_dir / "SKILL.md"
            desc = ""
            if skill_md.exists():
                for line in skill_md.read_text(encoding="utf-8").splitlines()[:5]:
                    if line.startswith("> ") or (line and not line.startswith("#")):
                        desc = line.lstrip("> ").strip(); break
            skills.append({"id": skill_dir.name, "description": desc})

    # Skills dans plugins/
    for plugin_dir in sorted(PLUGINS_DIR.iterdir()) if PLUGINS_DIR.exists() else []:
        if plugin_dir.is_dir():
            skill_md = plugin_dir / "SKILL.md"
            if skill_md.exists():
                desc = ""
                for line in skill_md.read_text(encoding="utf-8").splitlines()[:5]:
                    if line.startswith("> ") or (line and not line.startswith("#")):
                        desc = line.lstrip("> ").strip(); break
                skills.append({"id": f"plugins/{plugin_dir.name}", "description": desc})

    if args.format == "json":
        _jprint({"skills": skills, "count": len(skills)})
        return

    print()
    print(_b(f"═══ Skills TricorderKit ({len(skills)}) ═══"))
    print()
    for s in skills:
        desc = f"  — {s['description'][:60]}" if s["description"] else ""
        print(f"  {_g('▸')} {s['id']:<35}{desc}")
    print()


# ── workflow list ─────────────────────────────────────────────────────────────

def cmd_workflow_list(args):
    workflows = []
    for wf_dir in [WORKFLOWS_DIR, REPO_ROOT / "workflows"]:
        if wf_dir.exists():
            for f in sorted(wf_dir.rglob("*.ts")) + sorted(wf_dir.rglob("*.yml")):
                workflows.append({"id": f.stem, "path": str(f.relative_to(REPO_ROOT)), "type": f.suffix[1:]})

    if args.format == "json":
        _jprint({"workflows": workflows, "count": len(workflows)})
        return

    print()
    print(_b(f"═══ Workflows TricorderKit ({len(workflows)}) ═══"))
    print()
    for w in workflows:
        print(f"  {_g('▸')} {w['id']:<40}  [{w['type']}]  {w['path']}")
    if not workflows:
        _warn("Aucun workflow trouvé dans plugins/workflow-engine/workflows/ ou workflows/")
    print()


# ── vault scan ────────────────────────────────────────────────────────────────

def cmd_vault_scan(args):
    vault = VAULT_DIR
    if not vault.exists():
        if args.format == "json":
            _jprint({"error": f"Vault introuvable : {vault}"})
        else:
            _warn(f"Vault introuvable", str(vault))
        return

    md_files = list(vault.rglob("*.md"))
    empty = [f for f in md_files if f.stat().st_size == 0]
    no_frontmatter = []
    for f in md_files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
            if not text.strip().startswith("---"):
                no_frontmatter.append(f)
        except Exception:
            pass

    result = {
        "vault_path": str(vault),
        "total_notes": len(md_files),
        "empty_notes": len(empty),
        "no_frontmatter": len(no_frontmatter),
        "health": "OK" if not empty and not no_frontmatter else "WARN",
    }

    if args.format == "json":
        _jprint(result)
        return

    print()
    print(_b("═══ Vault Scan — TricorderKit ═══"))
    print(f"  Path     : {vault}")
    print(f"  Notes    : {len(md_files)}")
    (_ok if not empty else _warn)(f"Notes vides : {len(empty)}")
    (_ok if not no_frontmatter else _warn)(f"Sans frontmatter YAML : {len(no_frontmatter)}")
    print()


# ── research run ─────────────────────────────────────────────────────────────

def cmd_research_run(args):
    query = getattr(args, "query", None) or "test query"
    dry_run = getattr(args, "dry_run", False)
    collect_script = REPO_ROOT / "plugins" / "deep-research-core" / "scripts" / "collect_sources.py"

    if args.format == "json":
        _jprint({
            "query": query, "dry_run": dry_run,
            "collect_script": str(collect_script),
            "script_exists": collect_script.exists(),
            "status": "dry_run" if dry_run else "ready",
        })
        return

    print()
    print(_b("═══ Deep Research ═══"))
    print(f"  Query    : {query}")
    print(f"  Dry-run  : {dry_run}")
    print(f"  Script   : {collect_script}")
    print()

    if not collect_script.exists():
        _fail("Script collect_sources.py introuvable")
        return

    if dry_run:
        _ok("Dry-run OK — script disponible, aucune exécution réseau")
        print(f"\n  Commande réelle :")
        print(f"    python {collect_script} --query \"{query}\"")
        print()
        return

    # Exécution réelle
    _ok("Lancement collect_sources.py...")
    try:
        result = subprocess.run(
            [sys.executable, str(collect_script), "--query", query],
            cwd=REPO_ROOT, timeout=60
        )
        (_ok if result.returncode == 0 else _fail)(
            "Terminé" if result.returncode == 0 else f"Erreur (code {result.returncode})")
    except Exception as e:
        _fail(f"Erreur : {e}")
    print()


# ── project list ──────────────────────────────────────────────────────────────

def cmd_project_list(args):
    projects = _linked_projects()

    if args.format == "json":
        _jprint({"linked_projects": [
            {"id": p.get("id"), "name": p.get("name"), "domain": p.get("domain"),
             "enabled": p.get("enabled"), "root": p.get("root"),
             "root_exists": Path(p.get("root","")).exists()}
            for p in projects
        ], "count": len(projects)})
        return

    if not LINKED_PROJECTS_FILE.exists():
        print(); _warn("linked_projects.yaml manquant"); print(); return

    print()
    print(_b("═══ Linked Projects ═══"))
    print()
    print(f"  {'ID':<20} {'NOM':<22} {'DOMAINE':<32} {'EN':<4}  ROOT")
    print("  " + "─" * 95)
    for p in projects:
        pid, root = p.get("id","?"), Path(p.get("root","."))
        en, exists = p.get("enabled", False), root.exists()
        en_s = _g("yes") if en else _y("no")
        root_s = (_g(str(root)) if exists else _r(str(root) + " ⚠️")) if en else str(root)
        print(f"  {pid:<20} {p.get('name',pid):<22} {p.get('domain','—'):<32} {en_s:<4}  {root_s}")
    print()


# ── project status ────────────────────────────────────────────────────────────

def cmd_project_status(args):
    pid = getattr(args, "project_id", None)
    p = _get_project(pid)
    if not p:
        if args.format == "json":
            _jprint({"error": f"Projet '{pid}' introuvable"})
        else:
            _fail(f"Projet '{pid}' introuvable")
        sys.exit(1)

    root = Path(p.get("root", "."))
    paths_check = {k: (root / v).exists() for k, v in p.get("paths", {}).items()}
    git_branch = _git("branch", "--show-current", cwd=root) if root.exists() else ""
    git_commit = _git("rev-parse", "--short", "HEAD", cwd=root) if root.exists() else ""

    if args.format == "json":
        _jprint({
            "id": p.get("id"), "name": p.get("name"), "domain": p.get("domain"),
            "github_repo": p.get("github_repo"), "enabled": p.get("enabled"),
            "root": str(root), "root_exists": root.exists(),
            "paths": paths_check,
            "git": {"branch": git_branch, "commit": git_commit},
        })
        return

    print()
    print(_b(f"═══ Projet : {p.get('name', pid)} [{p.get('id', pid)}] ═══"))
    print(f"  GitHub   : {p.get('github_repo', '—')}")
    print(f"  Domaine  : {p.get('domain', '—')}")
    print(f"  Activé   : {_g('oui') if p.get('enabled') else _y('non')}")
    print(f"  Root     : {root}")
    print()
    print(_b("Répertoires :"))
    for k, v in p.get("paths", {}).items():
        full = root / v
        print(f"  {k:<12} {_g('✅') if full.exists() else _r('❌')}  {full}")
    if git_branch:
        print()
        print(_b("Git :"))
        _ok(f"Branch {git_branch} @ {git_commit}")
    print()


# ── project audit ─────────────────────────────────────────────────────────────

def cmd_project_audit(args):
    pid = getattr(args, "project_id", None)
    audit_script = REPO_ROOT / "tools" / "audit" / "linked_project_audit.py"

    if not audit_script.exists():
        if args.format == "json":
            _jprint({"error": "tools/audit/linked_project_audit.py introuvable"})
        else:
            _fail("linked_project_audit.py introuvable")
        sys.exit(1)

    cmd = [sys.executable, str(audit_script)]
    if pid: cmd += ["--project", pid]
    cmd += ["--format", args.format if args.format != "md" else "markdown"]
    subprocess.run(cmd, cwd=REPO_ROOT)


# ── project vault scan ────────────────────────────────────────────────────────

def cmd_project_vault_scan(args):
    pid = getattr(args, "project_id", None)
    p = _get_project(pid)
    if not p:
        _fail(f"Projet '{pid}' introuvable"); sys.exit(1)

    root = Path(p.get("root", "."))
    vault_rel = p.get("paths", {}).get("vault", "vault/")
    vault = root / vault_rel

    if not vault.exists():
        if args.format == "json":
            _jprint({"error": f"Vault introuvable : {vault}"})
        else:
            _warn("Vault introuvable", str(vault))
        return

    md_files = list(vault.rglob("*.md"))
    empty = [f for f in md_files if f.stat().st_size == 0]
    no_frontmatter = [f for f in md_files
                      if not f.read_text(encoding="utf-8", errors="ignore").strip().startswith("---")]

    result = {
        "project_id": p.get("id"), "vault_path": str(vault),
        "total_notes": len(md_files), "empty_notes": len(empty),
        "no_frontmatter": len(no_frontmatter),
        "health": "OK" if not empty and not no_frontmatter else "WARN",
    }

    if args.format == "json":
        _jprint(result); return

    print()
    print(_b(f"═══ Vault Scan — {p.get('name', pid)} ═══"))
    print(f"  Path     : {vault}")
    print(f"  Notes    : {len(md_files)}")
    (_ok if not empty else _warn)(f"Notes vides : {len(empty)}")
    (_ok if not no_frontmatter else _warn)(f"Sans frontmatter : {len(no_frontmatter)}")
    print()


# ── project workflow list ─────────────────────────────────────────────────────

def cmd_project_workflow_list(args):
    pid = getattr(args, "project_id", None)
    p = _get_project(pid)
    if not p:
        _fail(f"Projet '{pid}' introuvable"); sys.exit(1)

    root = Path(p.get("root", "."))
    wf_rel = p.get("paths", {}).get("workflows", "workflows/")
    wf_dir = root / wf_rel

    workflows = []
    if wf_dir.exists():
        for f in sorted(wf_dir.rglob("*.yml")) + sorted(wf_dir.rglob("*.yaml")) + sorted(wf_dir.rglob("*.ts")):
            workflows.append({"id": f.stem, "path": str(f.relative_to(root)), "type": f.suffix[1:]})

    if args.format == "json":
        _jprint({"project_id": p.get("id"), "workflows": workflows, "count": len(workflows)})
        return

    print()
    print(_b(f"═══ Workflows — {p.get('name', pid)} ({len(workflows)}) ═══"))
    print()
    if not workflows:
        _warn(f"Aucun workflow trouvé dans {wf_dir}")
    else:
        for w in workflows:
            print(f"  {_g('▸')} {w['id']:<40}  [{w['type']}]  {w['path']}")
    print()


# ── rapport ──────────────────────────────────────────────────────────────────

def _parse_boot_field(text: str, key: str) -> str:
    """Extract value from a BOOT_SUMMARY.md table row like `| key | value |`."""
    for line in text.splitlines():
        if f"| {key}" in line or f"| **{key}**" in line:
            parts = line.split("|")
            if len(parts) >= 3:
                return parts[2].strip()
    return "—"


def _parse_status_table(text: str) -> list[dict]:
    """Parse the plugin table from STATUS.md."""
    modules = []
    in_table = False
    for line in text.splitlines():
        if "| Plugin |" in line:
            in_table = True
            continue
        if in_table and line.startswith("|---|"):
            continue
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 5:
                modules.append({
                    "plugin": parts[0],
                    "status": parts[1],
                    "cli": parts[2],
                    "tests": parts[3],
                    "docs": parts[4],
                    "production_ready": parts[5] if len(parts) > 5 else "—",
                })
        elif in_table and not line.startswith("|"):
            in_table = False
    return modules


def _parse_next_task(text: str) -> str:
    """Return first pending (non-✅) numbered task from BOOT_SUMMARY.md Prochaines tâches."""
    import re
    in_tasks = False
    for line in text.splitlines():
        if "## Prochaines tâches" in line:
            in_tasks = True
            continue
        if in_tasks and line.startswith("## "):
            break
        if in_tasks and re.match(r"^\d+\.", line.strip()):
            # done if line contains ✅ or `✅`
            if "✅" not in line:
                return re.sub(r"^\d+\.\s*", "", line.strip())
    return "Aucune tâche en attente"


def _parse_tests(tests_info: str) -> tuple[int, int]:
    """Extract PASS/FAIL counts from a string like '**413 PASS** (…), 15 skipped'."""
    import re
    clean = tests_info.replace("**", "").replace("(", " ").replace(")", " ")
    tests_pass = tests_fail = 0
    for m in re.finditer(r"(\d+)\s+PASS", clean):
        tests_pass = int(m.group(1))
    for m in re.finditer(r"(\d+)\s+FAIL", clean):
        tests_fail = int(m.group(1))
    return tests_pass, tests_fail


def cmd_rapport(args):
    boot_md   = REPO_ROOT / "BOOT_SUMMARY.md"
    status_md = REPO_ROOT / "STATUS.md"
    reports_dir = REPO_ROOT / "reports" / "status"

    boot_text   = boot_md.read_text(encoding="utf-8")   if boot_md.exists()   else ""
    status_text = status_md.read_text(encoding="utf-8") if status_md.exists() else ""

    version    = _parse_boot_field(boot_text, "Version")
    tests_info = _parse_boot_field(boot_text, "Tests")
    blockers   = _parse_boot_field(boot_text, "Blockers actifs")
    next_task  = _parse_next_task(boot_text)
    modules    = _parse_status_table(status_text)
    tests_pass, tests_fail = _parse_tests(tests_info)
    today      = datetime.date.today().isoformat()

    reports_dir.mkdir(parents=True, exist_ok=True)

    # Build report content
    table_rows = "\n".join(
        f"| {m['plugin']} | {m['status']} | {m['cli']} | {m['tests']} | {m['docs']} | {m['production_ready']} |"
        for m in modules
    )
    md_content = f"""\
# Rapport TricorderKit — {today}

> Généré automatiquement par `tk rapport` — {version}

---

## Modules actifs

| Plugin | Status | CLI | Tests | Docs | Production-ready |
|---|---|---|---|---|---|
{table_rows}

---

## Tests

| PASS | FAIL |
|---|---|
| {tests_pass} | {tests_fail} |

---

## Session

- **Dernière session** : {today}
- **Blockers actifs** : {blockers}

---

## Prochaine tâche

{next_task}

---

*Auto-généré — TricorderKit — {today}*
"""
    latest_md = reports_dir / "latest_status.md"
    latest_md.write_text(md_content, encoding="utf-8")

    # Update BOOT_SUMMARY.md "Dernière session"
    if boot_md.exists():
        updated_lines = []
        for line in boot_text.splitlines():
            if "| Dernière session |" in line:
                parts = line.split("|")
                if len(parts) >= 3:
                    parts[2] = f" {today} "
                    line = "|".join(parts)
            updated_lines.append(line)
        boot_md.write_text("\n".join(updated_lines), encoding="utf-8")

    # JSON output
    data = {
        "generated": today,
        "version": version,
        "tests": {"pass": tests_pass, "fail": tests_fail},
        "blockers": blockers,
        "next_task": next_task,
        "modules": modules,
    }
    if getattr(args, "json_output", False):
        latest_json = reports_dir / "latest_status.json"
        latest_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.format == "json":
        _jprint(data)
        return

    print()
    print(_b(f"═══ Rapport TricorderKit — {today} ═══"))
    print()
    print(_b("Modules actifs :"))
    for m in modules:
        prod = m["production_ready"]
        icon = _g("✅") if "✅" in prod else (_y("⚠️") if "⚠️" in prod else _r("❌"))
        print(f"  {icon} {m['plugin']:<30}  {m['status']}")
    print()
    print(_b("Tests :"))
    _ok(f"{tests_pass} PASS")
    if tests_fail:
        _fail(f"{tests_fail} FAIL")
    print()
    print(_b("Session :"))
    print(f"  Dernière session : {today}")
    print(f"  Blockers         : {blockers}")
    print()
    print(_b("Prochaine tâche :"))
    print(f"  {next_task}")
    print()
    _ok(f"Rapport écrit → {latest_md}")
    if getattr(args, "json_output", False):
        _ok(f"JSON écrit     → {reports_dir / 'latest_status.json'}")
    print()


# ── report generate / show ───────────────────────────────────────────────────

def cmd_report_generate(args):
    """Délègue à scripts/generate_status.py pour produire STATUS.md + rapport daté."""
    generate_script = REPO_ROOT / "scripts" / "generate_status.py"
    if not generate_script.exists():
        if args.format == "json":
            _jprint({"error": "scripts/generate_status.py introuvable"})
        else:
            _fail("scripts/generate_status.py introuvable")
        sys.exit(1)

    cmd = [sys.executable, str(generate_script), "--report"]
    if getattr(args, "no_status_md", False):
        cmd.append("--no-status-md")
    if args.format == "json":
        cmd += ["--output", "json"]

    result = subprocess.run(cmd, cwd=REPO_ROOT)
    sys.exit(result.returncode)


def cmd_report_show(args):
    """Affiche STATUS.md courant (ou le génère s'il n'existe pas)."""
    status_md = REPO_ROOT / "STATUS.md"
    if not status_md.exists():
        _warn("STATUS.md absent — génération en cours...")
        cmd_report_generate(args)
        return

    if args.format == "json":
        _jprint({
            "path": str(status_md),
            "size": status_md.stat().st_size,
            "content": status_md.read_text(encoding="utf-8"),
        })
        return

    print(status_md.read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════════════════════════════
# PARSER
# ═══════════════════════════════════════════════════════════════════════════════

def _add_format(p: argparse.ArgumentParser):
    p.add_argument("--format", choices=["markdown", "json", "md"],
                   default="markdown", help="Format de sortie (défaut: markdown)")

def main():
    parser = argparse.ArgumentParser(
        prog="tk", description="TricorderKit CLI v0.2.0 — Agentic Knowledge OS",
    )
    parser.add_argument("--version", action="version", version="tk 0.9.0")
    _add_format(parser)
    sub = parser.add_subparsers(dest="command", metavar="<commande>")

    # ── status ──
    p_status = sub.add_parser("status", help="État général du système")
    _add_format(p_status)

    # ── health ──
    p_health = sub.add_parser("health", help="Health-check rapide (alias doctor)")
    _add_format(p_health)

    # ── doctor ──
    p_doctor = sub.add_parser("doctor", help="Health-check détaillé tous les services")
    _add_format(p_doctor)

    # ── skill ──
    p_skill = sub.add_parser("skill", help="Commandes skills")
    _add_format(p_skill)
    sk_sub = p_skill.add_subparsers(dest="skill_cmd", metavar="<sous-commande>")
    p_sl = sk_sub.add_parser("list", help="Lister les skills disponibles")
    _add_format(p_sl)

    # ── workflow ──
    p_wf = sub.add_parser("workflow", help="Commandes workflows")
    _add_format(p_wf)
    wf_sub = p_wf.add_subparsers(dest="wf_cmd", metavar="<sous-commande>")
    p_wl = wf_sub.add_parser("list", help="Lister les workflows disponibles")
    _add_format(p_wl)

    # ── vault ──
    p_vault = sub.add_parser("vault", help="Commandes vault TricorderKit")
    _add_format(p_vault)
    vault_sub = p_vault.add_subparsers(dest="vault_cmd", metavar="<sous-commande>")
    p_vs = vault_sub.add_parser("scan", help="Scanner le vault TricorderKit")
    _add_format(p_vs)

    # ── research ──
    p_res = sub.add_parser("research", help="Commandes deep-research")
    _add_format(p_res)
    res_sub = p_res.add_subparsers(dest="res_cmd", metavar="<sous-commande>")
    p_rr = res_sub.add_parser("run", help="Lancer deep-research")
    p_rr.add_argument("query", nargs="?", default="test query", help="Requête de recherche")
    p_rr.add_argument("--dry-run", action="store_true", help="Simuler sans appel réseau")
    _add_format(p_rr)

    # ── project ──
    p_project = sub.add_parser("project", help="Commandes linked_project")
    _add_format(p_project)
    pr_sub = p_project.add_subparsers(dest="project_cmd", metavar="<sous-commande>")

    p_pl = pr_sub.add_parser("list", help="Lister les projets")
    _add_format(p_pl)

    p_ps = pr_sub.add_parser("status", help="État d'un projet")
    p_ps.add_argument("project_id", nargs="?", help="ID projet (ex: japan-alliance)")
    _add_format(p_ps)

    p_pa = pr_sub.add_parser("audit", help="Audit complet d'un projet")
    p_pa.add_argument("project_id", nargs="?", help="ID projet")
    _add_format(p_pa)

    p_pvs = pr_sub.add_parser("vault", help="Commandes vault du projet")
    _add_format(p_pvs)
    pvault_sub = p_pvs.add_subparsers(dest="pvault_cmd")
    p_pvsc = pvault_sub.add_parser("scan", help="Scanner le vault du projet")
    p_pvsc.add_argument("project_id", nargs="?", help="ID projet")
    _add_format(p_pvsc)

    p_pwl = pr_sub.add_parser("workflow", help="Commandes workflow du projet")
    _add_format(p_pwl)
    pwf_sub = p_pwl.add_subparsers(dest="pwf_cmd")
    p_pwll = pwf_sub.add_parser("list", help="Lister les workflows du projet")
    p_pwll.add_argument("project_id", nargs="?", help="ID projet")
    _add_format(p_pwll)

    # ── rapport ──
    p_rapport = sub.add_parser("rapport",
                                help="Rapport plugins depuis BOOT_SUMMARY.md + STATUS.md")
    p_rapport.add_argument("--json", dest="json_output", action="store_true",
                           help="Générer aussi reports/status/latest_status.json")
    _add_format(p_rapport)

    # ── report ──
    p_report = sub.add_parser("report", help="Dashboard observabilité — STATUS.md + rapports")
    _add_format(p_report)
    rep_sub = p_report.add_subparsers(dest="report_cmd", metavar="<sous-commande>")

    p_rg = rep_sub.add_parser("generate",
                               help="Génère STATUS.md + rapport daté dans reports/")
    p_rg.add_argument("--no-status-md", action="store_true",
                      help="Ne pas écrire STATUS.md (rapport seul)")
    _add_format(p_rg)

    p_rs = rep_sub.add_parser("show", help="Affiche STATUS.md en terminal")
    _add_format(p_rs)

    # ── parse ──
    args = parser.parse_args()

    # Propager --format depuis le parser global si non spécifié dans sous-commande
    if not hasattr(args, "format") or args.format is None:
        args.format = "markdown"

    dispatch = {
        "status":   cmd_status,
        "health":   cmd_doctor,
        "doctor":   cmd_doctor,
        "rapport":  cmd_rapport,
    }

    if args.command in dispatch:
        dispatch[args.command](args)
    elif args.command == "skill":
        if getattr(args, "skill_cmd", None) == "list":
            cmd_skill_list(args)
        else:
            p_skill.print_help()
    elif args.command == "workflow":
        if getattr(args, "wf_cmd", None) == "list":
            cmd_workflow_list(args)
        else:
            p_wf.print_help()
    elif args.command == "vault":
        if getattr(args, "vault_cmd", None) == "scan":
            cmd_vault_scan(args)
        else:
            p_vault.print_help()
    elif args.command == "research":
        if getattr(args, "res_cmd", None) == "run":
            cmd_research_run(args)
        else:
            p_res.print_help()
    elif args.command == "project":
        pc = getattr(args, "project_cmd", None)
        if pc == "list":      cmd_project_list(args)
        elif pc == "status":  cmd_project_status(args)
        elif pc == "audit":   cmd_project_audit(args)
        elif pc == "vault":
            if getattr(args, "pvault_cmd", None) == "scan":
                cmd_project_vault_scan(args)
            else:
                p_pvs.print_help()
        elif pc == "workflow":
            if getattr(args, "pwf_cmd", None) == "list":
                cmd_project_workflow_list(args)
            else:
                p_pwl.print_help()
        else:
            p_project.print_help()
    elif args.command == "report":
        rc = getattr(args, "report_cmd", None)
        if rc == "generate":
            cmd_report_generate(args)
        elif rc == "show":
            cmd_report_show(args)
        else:
            p_report.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    main()
