"""
skill_registry.py — Lecteur du registre cli-forge réel
TricorderKit v0.8 — tk-orchestrator v0.2.0

Lit plugins/cli-forge/registry.yml et retourne uniquement les CLIs
avec status: dry_run_validated ou prod_ready ET safe_for_agents: true.

Les CLIs in_progress ou pending sont exclues silencieusement (pas d'erreur).
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    raise ImportError("PyYAML requis : pip install pyyaml --break-system-packages")


# ── Constantes ────────────────────────────────────────────────────────────────

VALID_STATUSES = {"dry_run_validated", "prod_ready"}
REGISTRY_DEFAULT_PATH = "plugins/cli-forge/registry.yml"
SKILLS_DEFAULT_PATH = "skills"


# ── Modèles ────────────────────────────────────────────────────────────────

@dataclass
class CLIEntry:
    name: str
    version: str
    status: str
    path: str
    description: str
    tags: List[str] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    safe_for_agents: bool = False
    auth_required: bool = False


@dataclass
class SkillEntry:
    name: str
    path: str
    triggers: List[str] = field(default_factory=list)


# ── Chargement registry CLIs ───────────────────────────────────────────────

def load_cli_registry(
    root: Optional[Path] = None,
    registry_path: Optional[str] = None,
) -> Dict[str, CLIEntry]:
    """
    Charge le registre des CLIs depuis plugins/cli-forge/registry.yml.
    Retourne uniquement les CLIs valides pour agents (statut + safe_for_agents).

    Args:
        root: Racine du projet TricorderKit (auto-détectée si None)
        registry_path: Chemin relatif au registry (défaut: plugins/cli-forge/registry.yml)

    Returns:
        Dict nom_cli → CLIEntry pour les CLIs utilisables
    """
    if root is None:
        root = _find_project_root()

    reg_file = root / (registry_path or REGISTRY_DEFAULT_PATH)

    if not reg_file.exists():
        return {}

    with reg_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    clis: Dict[str, CLIEntry] = {}

    for entry in data.get("clis", []):
        name = entry.get("name", "")
        status = entry.get("status", "pending")
        safe = entry.get("safe_for_agents", False)

        # Filtre strict : uniquement validées et marquées safe
        if status not in VALID_STATUSES or not safe:
            continue

        clis[name] = CLIEntry(
            name=name,
            version=entry.get("version", "0.0.0"),
            status=status,
            path=str(root / entry.get("path", "")),
            description=entry.get("description", ""),
            tags=entry.get("tags", []),
            commands=entry.get("commands", []),
            safe_for_agents=safe,
            auth_required=entry.get("auth_required", False),
        )

    return clis


def find_cli_for_domain(
    domain: str,
    intent_type: str,
    clis: Dict[str, CLIEntry],
) -> Optional[CLIEntry]:
    """
    Trouve la CLI la plus adaptée pour un domaine et une intention.

    Stratégie de matching : tags > description > name
    """
    # Mapping domaine → tags prioritaires
    domain_tag_map: Dict[str, List[str]] = {
        "github": ["github", "code", "repos", "issues"],
        "manga": ["manga", "anime", "japan", "search"],
        "anime": ["anime", "anilist", "japan"],
        "ln": ["ln", "light-novel", "japan"],
        "vault": ["obsidian", "vault", "notes"],
        "system": ["system", "audit", "health"],
    }

    preferred_tags = domain_tag_map.get(domain, [domain])

    best: Optional[CLIEntry] = None
    best_score = 0

    for cli in clis.values():
        score = 0
        # Match sur les tags
        for tag in cli.tags:
            if tag in preferred_tags:
                score += 2
        # Match sur la description
        desc_lower = cli.description.lower()
        if domain in desc_lower:
            score += 1
        # Match sur le nom
        if domain in cli.name:
            score += 1

        if score > best_score:
            best_score = score
            best = cli

    return best


# ── Chargement registry Skills ──────────────────────────────────────────────

def load_skill_registry(root: Optional[Path] = None) -> Dict[str, SkillEntry]:
    """
    Scan le dossier skills/ pour les SKILL.md valides.
    Retourne un dict nom_skill → SkillEntry.

    Note: Sera remplacé par le plugin skill-registry quand disponible (STATE.md priorité A).
    """
    if root is None:
        root = _find_project_root()

    skills_dir = root / SKILLS_DEFAULT_PATH
    if not skills_dir.exists():
        return {}

    skills: Dict[str, SkillEntry] = {}

    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        triggers = _extract_triggers(skill_md)
        skills[skill_dir.name] = SkillEntry(
            name=skill_dir.name,
            path=str(skill_md),
            triggers=triggers,
        )

    return skills


def _extract_triggers(skill_md: Path) -> List[str]:
    """Extrait les mots-clés déclencheurs depuis le SKILL.md."""
    triggers = []
    try:
        content = skill_md.read_text(encoding="utf-8")
        in_triggers = False
        for line in content.splitlines():
            line_stripped = line.strip()
            if "## 🎯" in line or "## Déclencheurs" in line or "## Triggers" in line:
                in_triggers = True
                continue
            if in_triggers and line_stripped.startswith("##"):
                break
            if in_triggers and line_stripped.startswith("- "):
                # Extraire le mot-clé (après "- " et avant ":")
                kw = line_stripped[2:].split(":")[0].strip().lower()
                if kw:
                    triggers.append(kw)
    except Exception:
        pass
    return triggers


# ── Utilitaire : auto-détection racine projet ─────────────────────────────────

def _find_project_root() -> Path:
    """
    Auto-détecte la racine TricorderKit en cherchant CLAUDE.md ou README.md
    depuis le répertoire courant vers le haut.
    """
    # Priorité 1 : variable d'env explicite
    env_root = os.environ.get("TRICORDERKIT_ROOT")
    if env_root:
        return Path(env_root)

    # Priorité 2 : chercher CLAUDE.md en remontant
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "CLAUDE.md").exists():
            return parent
        if (parent / "plugins" / "cli-forge" / "registry.yml").exists():
            return parent

    # Fallback : répertoire courant
    return current
