"""
pattern_checker.py — Détection d'anti-patterns de sécurité dans le code
TricorderKit security-audit-cli v0.1.0

Détecte les constructions dangereuses : eval(), subprocess shell=True,
os.system(), pickle.loads() sur input non validé, etc.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


# -- Règles de détection ------------------------------------------------------

@dataclass
class PatternRule:
    """Règle de détection d'anti-pattern."""
    id: str
    description: str
    pattern: re.Pattern
    severity: str               # HIGH | MEDIUM | LOW
    exclude_path_hints: list[str] = field(default_factory=list)
    justification_comment: str = ""   # Commentaire qui neutralise le finding


_RULES: list[PatternRule] = [
    PatternRule(
        id="eval_usage",
        description="Utilisation de eval() — exécution de code arbitraire",
        pattern=re.compile(r'\beval\s*\('),
        severity="HIGH",
        exclude_path_hints=["test", "tests"],
        justification_comment="# nosec eval",
    ),
    PatternRule(
        id="subprocess_shell_true",
        description="subprocess avec shell=True — injection de commande possible",
        pattern=re.compile(r'subprocess\.[a-z_]+\s*\([^)]*shell\s*=\s*True'),
        severity="HIGH",
        justification_comment="# nosec shell",
    ),
    PatternRule(
        id="os_system",
        description="os.system() — exécution shell non contrôlée",
        pattern=re.compile(r'\bos\.system\s*\('),
        severity="HIGH",
        justification_comment="# nosec os.system",
    ),
    PatternRule(
        id="pickle_loads",
        description="pickle.loads() sur données non validées",
        pattern=re.compile(r'\bpickle\.loads\s*\('),
        severity="HIGH",
        exclude_path_hints=["test", "tests"],
        justification_comment="# nosec pickle",
    ),
    PatternRule(
        id="yaml_load_unsafe",
        description="yaml.load() sans Loader sécurisé (utiliser yaml.safe_load)",
        pattern=re.compile(r'\byaml\.load\s*\(\s*(?!.*Loader\s*=\s*yaml\.Safe)'),
        severity="MEDIUM",
        justification_comment="# nosec yaml",
    ),
    PatternRule(
        id="hardcoded_tmp_path",
        description="Chemin /tmp hardcodé — risque de symlink attack",
        pattern=re.compile(r'["\']\/tmp\/[^"\']+["\']'),
        severity="LOW",
    ),
    PatternRule(
        id="debug_pdb",
        description="Point d'arrêt pdb laissé en production",
        pattern=re.compile(r'\bimport\s+pdb\b|\bpdb\.set_trace\s*\(\s*\)'),
        severity="MEDIUM",
        exclude_path_hints=["test", "tests"],
    ),
]

_BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp",
    ".pdf", ".zip", ".tar", ".gz", ".sqlite", ".db",
    ".bin", ".exe", ".dll", ".whl", ".pyc", ".pyo",
}

_SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "node_modules",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build",
}

_SOURCE_EXTENSIONS = {".py", ".pyw", ".sh", ".bash", ".zsh", ".yaml", ".yml", ".toml"}


# -- Dataclasses --------------------------------------------------------------

@dataclass
class PatternFinding:
    """Occurrence d'anti-pattern détecté."""
    file_path: str
    line_number: int
    rule_id: str
    description: str
    line_content: str       # Ligne (tronquée à 120 chars)
    severity: str
    suppressed: bool = False    # True si commentaire nosec présent


@dataclass
class PatternCheckResult:
    """Résultat de la vérification des patterns."""
    clean: bool
    findings: list[PatternFinding] = field(default_factory=list)
    files_scanned: int = 0
    files_skipped: int = 0

    @property
    def has_critical(self) -> bool:
        return False

    @property
    def active_findings(self) -> list[PatternFinding]:
        """Findings non supprimés."""
        return [f for f in self.findings if not f.suppressed]

    def to_dict(self) -> dict:
        active = self.active_findings
        return {
            "clean": self.clean,
            "files_scanned": self.files_scanned,
            "files_skipped": self.files_skipped,
            "findings_count": len(active),
            "suppressed_count": len(self.findings) - len(active),
            "findings": [
                {
                    "file": f.file_path,
                    "line": f.line_number,
                    "rule_id": f.rule_id,
                    "description": f.description,
                    "content": f.line_content,
                    "severity": f.severity,
                }
                for f in active
            ],
        }


# -- Helpers ------------------------------------------------------------------

def _is_binary_file(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:512]
        return b"\x00" in chunk
    except (OSError, PermissionError):
        return True


def _iter_source_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in _SOURCE_EXTENSIONS:
            continue
        yield path


def _path_has_hint(path: Path, hints: list[str]) -> bool:
    parts_lower = {p.lower() for p in path.parts}
    return any(h.lower() in parts_lower for h in hints)


# -- Scan ---------------------------------------------------------------------

def _scan_file(
    file_path: Path,
    root: Path,
    rules: list[PatternRule],
) -> tuple[list[PatternFinding], bool]:
    if _is_binary_file(file_path):
        return [], True

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except (OSError, PermissionError):
        return [], True

    relative = str(file_path.relative_to(root))
    findings: list[PatternFinding] = []

    for line_num, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()

        for rule in rules:
            if rule.exclude_path_hints and _path_has_hint(file_path, rule.exclude_path_hints):
                continue

            if not rule.pattern.search(line):
                continue

            suppressed = bool(
                rule.justification_comment
                and rule.justification_comment.lower() in stripped.lower()
            )

            findings.append(PatternFinding(
                file_path=relative,
                line_number=line_num,
                rule_id=rule.id,
                description=rule.description,
                line_content=stripped[:120],
                severity=rule.severity,
                suppressed=suppressed,
            ))

    return findings, False


# -- Entrée publique ----------------------------------------------------------

def check_patterns(
    path: Path,
    custom_rules: list[PatternRule] | None = None,
    include_suppressed: bool = False,
) -> PatternCheckResult:
    """
    Vérifie un répertoire ou fichier pour les anti-patterns de sécurité.

    Args:
        path: Répertoire ou fichier à scanner
        custom_rules: Règles supplémentaires
        include_suppressed: Inclure les findings supprimés par # nosec

    Returns:
        PatternCheckResult avec la liste des findings actifs
    """
    rules = _RULES + (custom_rules or [])
    all_findings: list[PatternFinding] = []
    files_scanned = 0
    files_skipped = 0

    if path.is_file():
        root = path.parent
        if path.suffix.lower() in _SOURCE_EXTENSIONS and not _is_binary_file(path):
            findings, _ = _scan_file(path, root, rules)
            all_findings.extend(findings)
            files_scanned += 1
        else:
            files_skipped += 1
    elif path.is_dir():
        root = path
        for file_path in _iter_source_files(root):
            findings, skipped = _scan_file(file_path, root, rules)
            all_findings.extend(findings)
            if skipped:
                files_skipped += 1
            else:
                files_scanned += 1
    else:
        raise FileNotFoundError(f"Chemin introuvable : {path}")

    active = [f for f in all_findings if not f.suppressed]
    return PatternCheckResult(
        clean=len(active) == 0,
        findings=all_findings if include_suppressed else active,
        files_scanned=files_scanned,
        files_skipped=files_skipped,
    )


# -- CLI standalone -----------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pattern_checker.py <path> [--json]", file=sys.stderr)
        sys.exit(1)

    target = Path(sys.argv[1])
    as_json = "--json" in sys.argv

    result = check_patterns(target)

    if as_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        active = result.active_findings
        if result.clean:
            print(f"✅ Aucun anti-pattern — {result.files_scanned} fichiers scannés")
        else:
            print(f"🟠 {len(active)} anti-pattern(s) sur {result.files_scanned} fichiers :")
            for f in active:
                icon = {"HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(f.severity, "⚪")
                print(f"  {icon} [{f.severity}] {f.file_path}:{f.line_number} — {f.description}")
                print(f"     {f.line_content}")

    sys.exit(0 if result.clean else 1)
