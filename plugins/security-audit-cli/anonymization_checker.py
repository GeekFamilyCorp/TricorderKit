"""
anonymization_checker.py — Vérification anonymisation avant push public
TricorderKit security-audit-cli v0.1.0

Détecte la présence de termes privés dans des fichiers destinés au repo public.
Bloquant : exit code 2 si terme CRITICAL trouvé.

Termes privés par défaut (depuis manifest.yml) :
  - Japan-Alliance   (nom projet privé)
  - MangaTracker     (nom app privée)
  - mangatracker-cli (nom CLI privée)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


# -- Termes privés par défaut -------------------------------------------------

DEFAULT_PRIVATE_TERMS: list[str] = [
    "Japan-Alliance",
    "MangaTracker",
    "mangatracker-cli",
]

# Extensions binaires à ignorer
_BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".7z",
    ".sqlite", ".db", ".bin", ".exe", ".dll", ".so",
    ".whl", ".pyc", ".pyo",
}

# Dossiers à ignorer
_SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "node_modules",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build",
    ".pytest_tmp", "reports",
}


# -- Dataclasses --------------------------------------------------------------

@dataclass
class AnonViolation:
    """Occurrence d'un terme privé détecté."""
    file_path: str      # Chemin relatif du fichier
    line_number: int    # Numéro de ligne (1-indexed)
    term: str           # Terme privé détecté
    line_content: str   # Contenu de la ligne (tronqué à 120 chars)
    severity: str = "CRITICAL"


@dataclass
class AnonCheckResult:
    """Résultat de la vérification d'anonymisation."""
    clean: bool
    violations: list[AnonViolation] = field(default_factory=list)
    files_scanned: int = 0
    files_skipped: int = 0
    terms_checked: list[str] = field(default_factory=list)

    @property
    def has_critical(self) -> bool:
        return any(v.severity == "CRITICAL" for v in self.violations)

    def violations_by_term(self) -> dict[str, list[AnonViolation]]:
        result: dict[str, list[AnonViolation]] = {}
        for v in self.violations:
            result.setdefault(v.term, []).append(v)
        return result

    def to_dict(self) -> dict:
        return {
            "clean": self.clean,
            "files_scanned": self.files_scanned,
            "files_skipped": self.files_skipped,
            "terms_checked": self.terms_checked,
            "violations_count": len(self.violations),
            "violations": [
                {
                    "file": v.file_path,
                    "line": v.line_number,
                    "term": v.term,
                    "content": v.line_content,
                    "severity": v.severity,
                }
                for v in self.violations
            ],
        }


# Fichier d'exclusion (pattern glob, un par ligne, # = commentaire)
_IGNORE_FILE = ".check-anon-ignore"


def _load_ignore_patterns(root: Path) -> list[str]:
    """Charge les patterns d'exclusion depuis .check-anon-ignore à la racine."""
    ignore_path = root / _IGNORE_FILE
    if not ignore_path.exists():
        return []
    lines = ignore_path.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.startswith("#")]


def _is_ignored(file_path: Path, root: Path, patterns: list[str]) -> bool:
    """Vérifie si un fichier correspond à un pattern d'exclusion."""
    import fnmatch
    relative = file_path.relative_to(root)
    rel_str  = str(relative).replace("\\", "/")
    for pattern in patterns:
        if fnmatch.fnmatch(rel_str, pattern):
            return True
        if fnmatch.fnmatch(file_path.name, pattern):
            return True
    return False


# -- Itérateurs de fichiers ---------------------------------------------------

def _iter_files(root: Path) -> Iterator[Path]:
    """Itère récursivement sur les fichiers texte d'un répertoire."""
    ignore_patterns = _load_ignore_patterns(root)
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in _BINARY_EXTENSIONS:
            continue
        if ignore_patterns and _is_ignored(path, root, ignore_patterns):
            continue
        yield path


def _is_binary_file(path: Path) -> bool:
    """Vérifie si un fichier est binaire (lecture partielle)."""
    try:
        chunk = path.read_bytes()[:512]
        return b"\x00" in chunk
    except (OSError, PermissionError):
        return True


# -- Scan d'un fichier --------------------------------------------------------

def _scan_file(
    file_path: Path,
    root: Path,
    patterns: list[tuple[str, re.Pattern]],
) -> tuple[list[AnonViolation], bool]:
    if _is_binary_file(file_path):
        return [], True

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except (OSError, PermissionError):
        return [], True

    relative = str(file_path.relative_to(root))
    violations: list[AnonViolation] = []

    for line_num, line in enumerate(content.splitlines(), start=1):
        for term, pattern in patterns:
            if pattern.search(line):
                violations.append(AnonViolation(
                    file_path=relative,
                    line_number=line_num,
                    term=term,
                    line_content=line.strip()[:120],
                ))

    return violations, False


# -- Entrée publique ----------------------------------------------------------

def check_anonymization(
    path: Path,
    private_terms: list[str] | None = None,
) -> AnonCheckResult:
    """
    Vérifie qu'un répertoire ou fichier ne contient aucun terme privé.

    Args:
        path: Répertoire ou fichier à scanner
        private_terms: Liste des termes privés à détecter (défaut: DEFAULT_PRIVATE_TERMS)

    Returns:
        AnonCheckResult avec la liste des violations
    """
    terms = private_terms or DEFAULT_PRIVATE_TERMS

    patterns: list[tuple[str, re.Pattern]] = [
        (term, re.compile(re.escape(term), re.IGNORECASE))
        for term in terms
    ]

    all_violations: list[AnonViolation] = []
    files_scanned = 0
    files_skipped = 0

    if path.is_file():
        root = path.parent
        violations, skipped = _scan_file(path, root, patterns)
        all_violations.extend(violations)
        files_skipped += int(skipped)
        files_scanned += int(not skipped)
    elif path.is_dir():
        root = path
        for file_path in _iter_files(root):
            violations, skipped = _scan_file(file_path, root, patterns)
            all_violations.extend(violations)
            if skipped:
                files_skipped += 1
            else:
                files_scanned += 1
    else:
        raise FileNotFoundError(f"Chemin introuvable : {path}")

    return AnonCheckResult(
        clean=len(all_violations) == 0,
        violations=all_violations,
        files_scanned=files_scanned,
        files_skipped=files_skipped,
        terms_checked=terms,
    )


def check_file_anonymization(
    file_path: Path,
    private_terms: list[str] | None = None,
) -> AnonCheckResult:
    """Raccourci pour vérifier un fichier unique."""
    return check_anonymization(file_path, private_terms)


# -- CLI standalone -----------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python anonymization_checker.py <path> [--json]", file=sys.stderr)
        sys.exit(1)

    target = Path(sys.argv[1])
    as_json = "--json" in sys.argv

    result = check_anonymization(target)

    if as_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        if result.clean:
            print(f"✅ Anonymisation OK — {result.files_scanned} fichiers scannés, aucun terme privé")
        else:
            print(f"🔴 {len(result.violations)} violation(s) détectée(s) sur {result.files_scanned} fichiers :")
            for term, viols in result.violations_by_term().items():
                print(f"\n  Terme : '{term}' ({len(viols)} occurrence(s))")
                for v in viols[:5]:
                    print(f"    {v.file_path}:{v.line_number}  →  {v.line_content}")
                if len(viols) > 5:
                    print(f"    … +{len(viols) - 5} autres")

    sys.exit(0 if result.clean else 2)
