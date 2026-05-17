#!/usr/bin/env python3
"""
local_vs_github_audit.py — Audit diff local vs GitHub
TricorderKit v0.8

Compare l'état local d'un dépôt (TricorderKit ou linked_project) avec son remote GitHub :
  - commits locaux non poussés
  - commits GitHub non récupérés
  - fichiers modifiés non commités
  - branches divergentes
  - statut général de synchronisation

Usage :
  python tools/audit/local_vs_github_audit.py
  python tools/audit/local_vs_github_audit.py --project japan-alliance
  python tools/audit/local_vs_github_audit.py --format json
  python tools/audit/local_vs_github_audit.py --all
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

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

# ─── Model ────────────────────────────────────────────────────────────────────
@dataclass
class RepoAudit:
    name: str
    root: Path
    remote_url: str = ""
    branch: str = ""
    local_commit: str = ""
    remote_commit: str = ""
    commits_ahead: int = 0
    commits_behind: int = 0
    dirty_files: list[str] = field(default_factory=list)
    untracked_files: list[str] = field(default_factory=list)
    fetch_error: str = ""

    @property
    def is_synced(self) -> bool:
        return (self.commits_ahead == 0 and self.commits_behind == 0
                and not self.dirty_files and not self.fetch_error)

    @property
    def status(self) -> str:
        if self.fetch_error: return "ERROR"
        if self.commits_behind > 0: return "BEHIND"
        if self.commits_ahead > 0: return "AHEAD"
        if self.dirty_files: return "DIRTY"
        return "SYNCED"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load_yaml(path: Path) -> dict:
    try:
        import yaml
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except ImportError:
        return {}
    except FileNotFoundError:
        return {}

def _git(cwd: Path, *args, timeout: int = 15) -> tuple[str, str, int]:
    """Retourne (stdout, stderr, returncode)."""
    try:
        r = subprocess.run(["git", *args], capture_output=True, text=True,
                           cwd=cwd, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", 1
    except FileNotFoundError:
        return "", "git not found", 1


def audit_repo(name: str, root: Path) -> RepoAudit:
    audit = RepoAudit(name=name, root=root)

    if not root.exists():
        audit.fetch_error = f"Répertoire introuvable : {root}"
        return audit

    # Remote
    out, _, rc = _git(root, "remote", "get-url", "origin")
    audit.remote_url = out if rc == 0 else "(no remote)"

    # Branch
    out, _, _ = _git(root, "branch", "--show-current")
    audit.branch = out or "unknown"

    # Local commit
    out, _, _ = _git(root, "rev-parse", "--short", "HEAD")
    audit.local_commit = out or "unknown"

    # Fetch pour avoir l'état remote à jour
    _, err, rc = _git(root, "fetch", "origin", "--quiet", timeout=20)
    if rc != 0:
        audit.fetch_error = f"git fetch échoué : {err[:100]}"

    # Remote commit
    out, _, rc = _git(root, "rev-parse", "--short", f"origin/{audit.branch}")
    audit.remote_commit = out if rc == 0 else "unknown"

    # Commits ahead / behind
    out, _, rc = _git(root, "rev-list", "--count", f"origin/{audit.branch}..HEAD")
    if rc == 0 and out.isdigit():
        audit.commits_ahead = int(out)

    out, _, rc = _git(root, "rev-list", "--count", f"HEAD..origin/{audit.branch}")
    if rc == 0 and out.isdigit():
        audit.commits_behind = int(out)

    # Dirty files
    out, _, _ = _git(root, "status", "--porcelain")
    if out:
        for line in out.splitlines():
            status = line[:2].strip()
            fname  = line[3:].strip()
            if status == "??":
                audit.untracked_files.append(fname)
            else:
                audit.dirty_files.append(f"[{status}] {fname}")

    return audit


def audit_log_table(audit: RepoAudit, n: int = 5) -> list[str]:
    """Retourne les N derniers commits sous forme de lignes."""
    out, _, _ = _git(audit.root, "log", "--oneline", f"-{n}", "--no-walk",
                     "--decorate=short")
    return out.splitlines() if out else []

# ─── Output ───────────────────────────────────────────────────────────────────

def _print_repo(audit: RepoAudit) -> None:
    icons = {"SYNCED": _g("✅ SYNCED"), "AHEAD": _y("⬆ AHEAD"),
             "BEHIND": _r("⬇ BEHIND"), "DIRTY": _y("~ DIRTY"), "ERROR": _r("❌ ERROR")}
    print()
    print(_b(f"  ── {audit.name} ──"))
    print(f"    Root       : {audit.root}")
    print(f"    Remote     : {audit.remote_url}")
    print(f"    Branch     : {audit.branch}")
    print(f"    Local      : {audit.local_commit}")
    print(f"    Remote     : {audit.remote_commit}")
    print(f"    Status     : {icons.get(audit.status, audit.status)}")

    if audit.fetch_error:
        print(f"    {_y('⚠️')} Fetch : {audit.fetch_error}")
    if audit.commits_ahead:
        print(f"    {_y('⬆')} {audit.commits_ahead} commit(s) locaux non poussés")
    if audit.commits_behind:
        print(f"    {_r('⬇')} {audit.commits_behind} commit(s) distants non récupérés")
    if audit.dirty_files:
        print(f"    {_y('~')} {len(audit.dirty_files)} fichier(s) modifiés :")
        for f in audit.dirty_files[:5]:
            print(f"        {f}")
        if len(audit.dirty_files) > 5:
            print(f"        ...et {len(audit.dirty_files) - 5} autres")
    if audit.untracked_files:
        print(f"    {_y('?')} {len(audit.untracked_files)} fichier(s) non suivis")

    recent = audit_log_table(audit, 3)
    if recent:
        print(f"    Récents :")
        for line in recent:
            print(f"        {line}")


def print_markdown_all(audits: list[RepoAudit]) -> None:
    print()
    print(_b("═══ Local vs GitHub Audit — TricorderKit ═══"))
    for a in audits:
        _print_repo(a)
    print()

    all_synced = all(a.is_synced for a in audits)
    if all_synced:
        print(f"  {_g('✅ Tous les dépôts sont synchronisés.')}")
    else:
        issues = [a for a in audits if not a.is_synced]
        print(f"  {_y(f'⚠️  {len(issues)} dépôt(s) à synchroniser.')}")
    print()


def print_json_all(audits: list[RepoAudit]) -> None:
    out = []
    for a in audits:
        out.append({
            "name": a.name, "root": str(a.root), "branch": a.branch,
            "remote_url": a.remote_url, "local_commit": a.local_commit,
            "remote_commit": a.remote_commit, "status": a.status,
            "commits_ahead": a.commits_ahead, "commits_behind": a.commits_behind,
            "dirty_files": a.dirty_files, "fetch_error": a.fetch_error,
        })
    print(json.dumps(out, ensure_ascii=False, indent=2))

# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="local_vs_github_audit.py — Diff local vs GitHub (TricorderKit + linked_projects)"
    )
    parser.add_argument("--project", "-p", help="ID du linked_project seulement (ex: japan-alliance)")
    parser.add_argument("--all", "-a", action="store_true", help="Auditer TricorderKit + tous les linked_projects")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    audits: list[RepoAudit] = []

    if args.project:
        # Seulement le linked_project demandé
        cfg = _load_yaml(LINKED_PROJECTS_FILE)
        p = next((x for x in cfg.get("linked_projects", []) if x.get("id") == args.project), None)
        if not p:
            print(_r(f"❌ Projet '{args.project}' absent de linked_projects.yaml"), file=sys.stderr)
            sys.exit(1)
        audits.append(audit_repo(p.get("name", args.project), Path(p.get("root", "."))))
    else:
        # TricorderKit lui-même
        audits.append(audit_repo("TricorderKit", REPO_ROOT))

        if args.all or not args.project:
            # Tous les linked_projects actifs
            cfg = _load_yaml(LINKED_PROJECTS_FILE)
            for p in cfg.get("linked_projects", []):
                if p.get("enabled", False):
                    audits.append(audit_repo(p.get("name", p.get("id")), Path(p.get("root", "."))))

    if args.format == "json":
        print_json_all(audits)
    else:
        print_markdown_all(audits)

    all_ok = all(a.is_synced for a in audits)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
