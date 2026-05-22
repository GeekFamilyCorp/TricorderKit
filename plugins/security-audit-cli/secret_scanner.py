"""
secret_scanner.py — Détection de secrets dans le code source
TricorderKit security-audit-cli v0.1.0

Détecte les clés API, tokens, mots de passe et connection strings
hardcodés dans les fichiers sources.

Patterns inspirés de gitleaks + trufflehog.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


# -- Patterns de secrets ------------------------------------------------------

@dataclass
class SecretPattern:
    """Un pattern de détection de secret."""
    id: str
    description: str
    pattern: re.Pattern
    severity: str           # CRITICAL | HIGH | MEDIUM
    false_positive_hints: list[str] = field(default_factory=list)


_PATTERNS: list[SecretPattern] = [
    SecretPattern(
        id="anthropic_api_key",
        description="Clé API Anthropic",
        pattern=re.compile(r'sk-ant-[a-zA-Z0-9\-_]{20,}'),
        severity="CRITICAL",
    ),
    SecretPattern(
        id="github_pat_classic",
        description="GitHub Personal Access Token (classic)",
        pattern=re.compile(r'ghp_[a-zA-Z0-9]{36}'),
        severity="CRITICAL",
    ),
    SecretPattern(
        id="github_pat_fine",
        description="GitHub Fine-grained PAT",
        pattern=re.compile(r'github_pat_[a-zA-Z0-9_]{82}'),
        severity="CRITICAL",
    ),
    SecretPattern(
        id="aws_access_key",
        description="Clé d'accès AWS",
        pattern=re.compile(r'AKIA[0-9A-Z]{16}'),
        severity="CRITICAL",
    ),
    SecretPattern(
        id="aws_secret_key",
        description="Clé secrète AWS",
        pattern=re.compile(r'aws[_\-]?secret[_\-]?(?:access[_\-]?)?key\s*[=:]\s*["\']?[a-zA-Z0-9/+]{40}["\']?', re.IGNORECASE),
        severity="CRITICAL",
    ),
    SecretPattern(
        id="generic_api_key",
        description="Clé API générique hardcodée",
        pattern=re.compile(
            r'(?:api[_\-]?key|apikey|api[_\-]?token)\s*[=:]\s*["\'][a-zA-Z0-9\-_\.]{16,}["\']',
            re.IGNORECASE,
        ),
        severity="HIGH",
        false_positive_hints=["your_api_key", "YOUR_API_KEY", "example", "placeholder", "xxx"],
    ),
    SecretPattern(
        id="generic_secret",
        description="Secret/password hardcodé",
        pattern=re.compile(
            r'(?:secret|password|passwd|pwd)\s*[=:]\s*["\'][^"\']{8,}["\']',
            re.IGNORECASE,
        ),
        severity="HIGH",
        false_positive_hints=["your_password", "YOUR_PASSWORD", "example", "placeholder", "changeme", "xxx", "***"],
    ),
    SecretPattern(
        id="db_connection_string",
        description="Connection string base de données avec credentials",
        # Username : ≥2 chars, pas de quotes/whitespace/@/:
        # Password : ≥6 chars (réduit les faux positifs sur des ports courts)
        # Exclut les DSN sans credentials : postgresql://localhost/db
        pattern=re.compile(
            r'(?:postgresql|mysql|mongodb|redis|sqlite)://[^"\'\s@:]{2,}:[^"\'\s@]{6,}@',
            re.IGNORECASE,
        ),
        severity="CRITICAL",
    ),
    SecretPattern(
        id="private_key_header",
        description="En-tête de clé privée PEM",
        pattern=re.compile(r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----'),
        severity="CRITICAL",
    ),
    SecretPattern(
        id="jwt_token",
        description="Token JWT complet (3 segments base64)",
        pattern=re.compile(r'eyJ[a-zA-Z0-9\-_]+\.eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+'),
        severity="HIGH",
        false_positive_hints=["example", "test", "dummy"],
    ),
]

_BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".7z",
    ".sqlite", ".db", ".bin", ".exe", ".dll", ".so",
    ".whl", ".pyc", ".pyo",
}

_SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "node_modules",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build",
}

_TEST_PATH_HINTS = {"test", "tests", "spec", "fixture", "mock", "fake", "example"}


# -- Dataclasses --------------------------------------------------------------

@dataclass
class SecretFinding:
    """Occurrence de secret détecté."""
    file_path: str
    line_number: int
    pattern_id: str
    description: str
    matched_snippet: str    # Extrait masqué (pas la valeur complète)
    severity: str
    in_test_file: bool = False


@dataclass
class SecretScanResult:
    """Résultat du scan de secrets."""
    clean: bool
    findings: list[SecretFinding] = field(default_factory=list)
    files_scanned: int = 0
    files_skipped: int = 0

    @property
    def has_critical(self) -> bool:
        return any(f.severity == "CRITICAL" for f in self.findings)

    @property
    def critical_findings(self) -> list[SecretFinding]:
        return [f for f in self.findings if f.severity == "CRITICAL"]

    @property
    def high_findings(self) -> list[SecretFinding]:
        return [f for f in self.findings if f.severity == "HIGH"]

    def to_dict(self) -> dict:
        return {
            "clean": self.clean,
            "files_scanned": self.files_scanned,
            "files_skipped": self.files_skipped,
            "findings_count": len(self.findings),
            "critical_count": len(self.critical_findings),
            "high_count": len(self.high_findings),
            "findings": [
                {
                    "file": f.file_path,
                    "line": f.line_number,
                    "pattern_id": f.pattern_id,
                    "description": f.description,
                    "snippet": f.matched_snippet,
                    "severity": f.severity,
                    "in_test_file": f.in_test_file,
                }
                for f in self.findings
            ],
        }


# -- Helpers ------------------------------------------------------------------

def _mask_secret(match: re.Match, line: str) -> str:
    """Masque la valeur du secret pour l'afficher sans l'exposer."""
    start, end = match.span()
    matched = match.group()
    if len(matched) > 20:
        return line[max(0, start - 10):start] + matched[:6] + "***MASKED***" + matched[-4:]
    return line[max(0, start - 10):start] + "***MASKED***"


def _is_false_positive(line: str, pattern: SecretPattern) -> bool:
    """Vérifie si la ligne est un faux positif connu."""
    line_lower = line.lower()
    return any(hint.lower() in line_lower for hint in pattern.false_positive_hints)


def _is_test_path(path: Path) -> bool:
    """Vérifie si le fichier appartient à un répertoire de test."""
    parts_lower = {p.lower() for p in path.parts}
    return bool(parts_lower & _TEST_PATH_HINTS)


def _is_binary_file(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:512]
        return b"\x00" in chunk
    except (OSError, PermissionError):
        return True


def _iter_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in _BINARY_EXTENSIONS:
            continue
        yield path


# -- Scan ---------------------------------------------------------------------

def _scan_file(
    file_path: Path,
    root: Path,
    patterns: list[SecretPattern],
) -> tuple[list[SecretFinding], bool]:
    """Scanne un fichier à la recherche de secrets."""
    if _is_binary_file(file_path):
        return [], True

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except (OSError, PermissionError):
        return [], True

    relative = str(file_path.relative_to(root))
    in_test = _is_test_path(file_path)
    findings: list[SecretFinding] = []

    for line_num, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue

        for pat in patterns:
            match = pat.pattern.search(line)
            if not match:
                continue
            if _is_false_positive(line, pat):
                continue

            severity = pat.severity
            if in_test and severity == "CRITICAL":
                severity = "HIGH"

            findings.append(SecretFinding(
                file_path=relative,
                line_number=line_num,
                pattern_id=pat.id,
                description=pat.description,
                matched_snippet=_mask_secret(match, line),
                severity=severity,
                in_test_file=in_test,
            ))

    return findings, False


# -- Entrée publique ----------------------------------------------------------

def scan_secrets(
    path: Path,
    custom_patterns: list[SecretPattern] | None = None,
) -> SecretScanResult:
    """
    Scanne un répertoire ou fichier à la recherche de secrets.

    Args:
        path: Répertoire ou fichier à scanner
        custom_patterns: Patterns supplémentaires (ajoutés aux défauts)

    Returns:
        SecretScanResult avec la liste des findings
    """
    patterns = _PATTERNS + (custom_patterns or [])

    all_findings: list[SecretFinding] = []
    files_scanned = 0
    files_skipped = 0

    if path.is_file():
        root = path.parent
        findings, skipped = _scan_file(path, root, patterns)
        all_findings.extend(findings)
        files_skipped += int(skipped)
        files_scanned += int(not skipped)
    elif path.is_dir():
        root = path
        for file_path in _iter_files(root):
            findings, skipped = _scan_file(file_path, root, patterns)
            all_findings.extend(findings)
            if skipped:
                files_skipped += 1
            else:
                files_scanned += 1
    else:
        raise FileNotFoundError(f"Chemin introuvable : {path}")

    return SecretScanResult(
        clean=len(all_findings) == 0,
        findings=all_findings,
        files_scanned=files_scanned,
        files_skipped=files_skipped,
    )


# -- CLI standalone -----------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python secret_scanner.py <path> [--json]", file=sys.stderr)
        sys.exit(1)

    target = Path(sys.argv[1])
    as_json = "--json" in sys.argv

    result = scan_secrets(target)

    if as_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        if result.clean:
            print(f"✅ Aucun secret détecté — {result.files_scanned} fichiers scannés")
        else:
            print(f"🔴 {len(result.findings)} secret(s) détecté(s) sur {result.files_scanned} fichiers :")
            for f in result.findings:
                icon = "🔴" if f.severity == "CRITICAL" else "🟠"
                test_note = " [test]" if f.in_test_file else ""
                print(f"  {icon} [{f.severity}]{test_note} {f.file_path}:{f.line_number}")
                print(f"     {f.description} — {f.matched_snippet}")

    sys.exit(0 if result.clean else (2 if result.has_critical else 1))
