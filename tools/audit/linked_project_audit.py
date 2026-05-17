#!/usr/bin/env python3
"""
linked_project_audit.py — Audit complet d'un linked_project
TricorderKit v0.8

Vérifie :
  - existence et structure du répertoire
  - statut Git (branch, commit, dirty, sync)
  - présence des fichiers critiques (project.yaml, vault, workflows, sources)
  - cohérence des chemins déclarés dans project.yaml
  - absence de secrets exposés (patterns basiques)
  - cohérence avec la config TricorderKit (linked_projects.yaml)

Usage :
  python tools/audit/linked_project_audit.py --project japan-alliance
  python tools/audit/linked_project_audit.py --project japan-alliance --format json
  python tools/audit/linked_project_audit.py --list
"""

from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─── Paths ────────────────────────────────────────────────────────────────────
REPO_ROOT            = Path(__file__).resolve().parent.parent.parent
LINKED_PROJECTS_FILE = REPO_ROOT / "configs" / "local" / "linked_projects.yaml"

# ─── Colors ───────────────────────────────────────────────────────────────────
def _g(s): return f"\033[92m{s}\033[0m"
def _y(s): return f"\033[93m{s}\033[0m"
def _r(s): return f"\033[91m{s}\033[0m"
def _b(s): return f"\033[1m{s}\033[0m"

# ─── Secret patterns (basiques — gitleaks couvre le reste) ───────────────────
SECRET_PATTERNS = [
    (r"sk-ant-[A-Za-z0-9\-_]{20,}", "Anthropic API key"),
    (r"ghp_[A-Za-z0-9]{36}", "GitHub Personal Token"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
    (r"(?i)(password|passwd|secret|api_key)\s*=\s*[\"'][^\"']{6,}", "Hardcoded credential"),
    (r"postgresql://[^:]+:[^@]+@", "DB connection string with password"),
]

# ─── Result model ─────────────────────────────────────────────────────────────
@dataclass
class Finding:
    level: str      # OK | WARN | ERROR
    category: str
    message: str
    detail: str = ""

@dataclass
class AuditResult:
    project_id: str
    project_name: str
    root: str
    findings: list[Finding] = field(default_factory=list)

    def ok(self, cat, msg, detail=""):
        self.findings.append(Finding("OK", cat, msg, detail))

    def warn(self, cat, msg, detail=""):
        self.findings.append(Finding("WARN", cat, msg, detail))

    def error(self, cat, msg, detail=""):
        self.findings.append(Finding("ERROR", cat, msg, detail))

    @property
    def errors(self):   return [f for f in self.findings if f.level == "ERROR"]
    @property
    def warnings(self): return [f for f in self.findings if f.level == "WARN"]
    @property
    def oks(self):      return [f for f in self.findings if f.level == "OK"]

    @property
    def score(self) -> str:
        if not self.errors and not self.warnings: return "PASS"
        if self.errors: return "FAIL"
        return "WARN"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load_yaml(path: Path) -> dict:
    try:
        import yaml
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except ImportError:
        return {}
    except FileNotFoundError:
        return {}

def _git(cwd: Path, *args) -> str:
    try:
        return subprocess.run(
            ["git", *args], capture_output=True, text=True, cwd=cwd, timeout=10
        ).stdout.strip()
    except Exception:
        return ""

def _scan_secrets(root: Path, private_terms: list[str]) -> list[tuple[str, str, str]]:
    """Retourne [(filepath, line_content, pattern_name)]"""
    hits = []
    all_patterns = SECRET_PATTERNS + [
        (re.escape(t), f"private_term:{t}") for t in private_terms if t
    ]
    extensions = {".py", ".ts", ".js", ".yaml", ".yml", ".json", ".md", ".env", ".sh"}
    for f in root.rglob("*"):
        if not f.is_file(): continue
        if f.suffix not in extensions: continue
        if any(part.startswith(".") for part in f.parts): continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
            for pattern, name in all_patterns:
                for m in re.finditer(pattern, text):
                    line_no = text[:m.start()].count("\n") + 1
                    hits.append((str(f.relative_to(root)), f"L{line_no}: {m.group()[:60]}", name))
        except Exception:
            pass
    return hits

# ─── Audit functions ──────────────────────────────────────────────────────────

def audit_structure(result: AuditResult, root: Path, project_cfg: dict) -> None:
    """Vérifie l'existence du répertoire et des sous-dossiers critiques."""
    if not root.exists():
        result.error("structure", f"Répertoire introuvable", str(root))
        return
    result.ok("structure", "Répertoire racine existe", str(root))

    paths = project_cfg.get("paths", {})
    critical = ["vault", "workflows", "skills", "reports"]
    for key in critical:
        rel = paths.get(key, key + "/")
        full = root / rel
        if full.exists():
            result.ok("structure", f"paths.{key} existe", str(rel))
        else:
            result.warn("structure", f"paths.{key} manquant", str(rel))

    # project_config/
    pc = root / "project_config"
    if pc.exists():
        result.ok("structure", "project_config/ présent")
        for f in ["project.yaml", "sources.yaml"]:
            if (pc / f).exists():
                result.ok("structure", f"project_config/{f} présent")
            else:
                result.warn("structure", f"project_config/{f} manquant")
    else:
        result.error("structure", "project_config/ absent — fichiers de config métier manquants")


def audit_git(result: AuditResult, root: Path) -> None:
    """Vérifie l'état Git du linked_project."""
    branch = _git(root, "branch", "--show-current")
    if not branch:
        result.error("git", "Pas de dépôt Git ou git inaccessible")
        return
    result.ok("git", f"Branch : {branch}")

    commit = _git(root, "rev-parse", "--short", "HEAD")
    result.ok("git", f"Commit : {commit}")

    dirty = _git(root, "status", "--porcelain")
    if dirty:
        lines = dirty.splitlines()
        result.warn("git", f"{len(lines)} fichier(s) non commité(s)")
    else:
        result.ok("git", "Working tree propre")

    remote = _git(root, "remote", "get-url", "origin")
    if remote:
        result.ok("git", f"Remote origin : {remote}")
    else:
        result.warn("git", "Pas de remote origin configuré")

    # Vérifier si privé (heuristique : GitHub + pas de fork public visible)
    if "github.com" in remote and not remote.startswith("http"):
        result.ok("git", "Remote semble privé (SSH)")
    elif "github.com" in remote:
        result.warn("git", "Remote HTTP — vérifier que le dépôt est bien privé sur GitHub")


def audit_project_config(result: AuditResult, root: Path) -> dict:
    """Charge et valide project.yaml."""
    pc_file = root / "project_config" / "project.yaml"
    if not pc_file.exists():
        result.error("config", "project_config/project.yaml absent")
        return {}

    cfg = _load_yaml(pc_file)
    if not cfg:
        result.error("config", "project_config/project.yaml vide ou YAML invalide")
        return {}

    required = ["project_id", "project_name", "domain", "data_policy", "paths", "execution"]
    for k in required:
        if k in cfg:
            result.ok("config", f"project.yaml.{k} présent")
        else:
            result.warn("config", f"project.yaml.{k} manquant")

    if not cfg.get("private_terms"):
        result.warn("config", "private_terms non définis — risque de fuite lors d'un push public")
    else:
        result.ok("config", f"{len(cfg['private_terms'])} private_terms déclarés")

    return cfg


def audit_secrets(result: AuditResult, root: Path, private_terms: list[str]) -> None:
    """Scan basique de secrets et termes privés."""
    hits = _scan_secrets(root, private_terms)
    if not hits:
        result.ok("secrets", "Aucun secret ou terme privé détecté dans les fichiers sources")
        return
    for filepath, line, name in hits[:10]:
        result.error("secrets", f"[{name}] {filepath}", line)
    if len(hits) > 10:
        result.error("secrets", f"...et {len(hits) - 10} autres occurrences")


def audit_consistency(result: AuditResult, root: Path, tk_config: dict, project_id: str) -> None:
    """Vérifie la cohérence avec la config TricorderKit."""
    projects = tk_config.get("linked_projects", [])
    p = next((x for x in projects if x.get("id") == project_id), None)
    if not p:
        result.warn("consistency", f"Projet '{project_id}' absent de linked_projects.yaml")
        return
    result.ok("consistency", f"Déclaré dans linked_projects.yaml")

    declared_root = Path(p.get("root", "."))
    if declared_root.resolve() == root.resolve():
        result.ok("consistency", f"Chemins cohérents entre linked_projects.yaml et répertoire réel")
    else:
        result.warn("consistency",
                    f"Divergence de chemin",
                    f"déclaré: {declared_root} | réel: {root}")

    if not p.get("enabled"):
        result.warn("consistency", "Projet désactivé dans linked_projects.yaml")
    else:
        result.ok("consistency", "Projet activé")


# ─── Main audit ───────────────────────────────────────────────────────────────

def run_audit(project_id: str) -> AuditResult:
    tk_config = _load_yaml(LINKED_PROJECTS_FILE)
    projects = tk_config.get("linked_projects", [])
    p = next((x for x in projects if x.get("id") == project_id), None)

    if not p:
        result = AuditResult(project_id, project_id, "unknown")
        result.error("config", f"Projet '{project_id}' absent de linked_projects.yaml")
        return result

    root = Path(p.get("root", "."))
    result = AuditResult(project_id, p.get("name", project_id), str(root))

    audit_structure(result, root, p)
    audit_git(result, root)
    project_cfg = audit_project_config(result, root)
    private_terms = project_cfg.get("private_terms", [])
    audit_secrets(result, root, private_terms)
    audit_consistency(result, root, tk_config, project_id)

    return result


# ─── Output formatters ────────────────────────────────────────────────────────

def print_markdown(result: AuditResult) -> None:
    icons = {"OK": _g("✅"), "WARN": _y("⚠️"), "ERROR": _r("❌")}
    print()
    print(_b(f"═══ Audit linked_project : {result.project_name} [{result.project_id}] ═══"))
    score_color = _g if result.score == "PASS" else (_r if result.score == "FAIL" else _y)
    print(f"  Score : {score_color(result.score)}  |  "
          f"{_g(str(len(result.oks)) + ' OK')}  "
          f"{_y(str(len(result.warnings)) + ' WARN')}  "
          f"{_r(str(len(result.errors)) + ' ERROR')}")
    print(f"  Root  : {result.root}")
    print()

    categories = {}
    for f in result.findings:
        categories.setdefault(f.category, []).append(f)

    for cat, findings in categories.items():
        print(_b(f"  {cat.upper()} :"))
        for f in findings:
            icon = icons.get(f.level, "·")
            detail = f"  — {f.detail}" if f.detail else ""
            print(f"    {icon} {f.message}{detail}")
        print()


def print_json(result: AuditResult) -> None:
    out = {
        "project_id": result.project_id,
        "project_name": result.project_name,
        "root": result.root,
        "score": result.score,
        "summary": {
            "ok": len(result.oks),
            "warn": len(result.warnings),
            "error": len(result.errors),
        },
        "findings": [
            {"level": f.level, "category": f.category,
             "message": f.message, "detail": f.detail}
            for f in result.findings
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="linked_project_audit.py — Audit d'un linked_project TricorderKit"
    )
    parser.add_argument("--project", "-p", help="ID du projet (ex: japan-alliance)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--list", action="store_true", help="Lister les projets disponibles")
    args = parser.parse_args()

    if args.list:
        cfg = _load_yaml(LINKED_PROJECTS_FILE)
        for p in cfg.get("linked_projects", []):
            print(f"  {p.get('id','?'):<20} {p.get('name','?')}")
        return

    if not args.project:
        parser.print_help()
        sys.exit(1)

    result = run_audit(args.project)

    if args.format == "json":
        print_json(result)
    else:
        print_markdown(result)

    sys.exit(0 if result.score == "PASS" else 1)


if __name__ == "__main__":
    main()
