"""
vault_router.py — Routing vault Obsidian
TricorderKit obsidian-agent-layer v0.1.0

Résout le vault cible (claude-vault / notes-vault / custom)
à partir du type de note, du chemin, ou d'un paramètre explicite.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


# -- Vault IDs ----------------------------------------------------------------

class VaultId(str, Enum):
    CLAUDE = "claude-vault"
    NOTES = "notes-vault"
    CUSTOM = "custom"


# -- Configuration vault ------------------------------------------------------

@dataclass
class VaultConfig:
    """Configuration d'un vault Obsidian."""
    vault_id: VaultId
    mcp_server: str                         # Nom du serveur MCP
    display_name: str
    hot_cache_path: str = ""
    daily_log_path: str = ""                # {date} est remplacé à l'exécution
    index_path: str = ""


# Configurations des vaults connectés
VAULT_CONFIGS: dict[VaultId, VaultConfig] = {
    VaultId.CLAUDE: VaultConfig(
        vault_id=VaultId.CLAUDE,
        mcp_server="obsidian-claude-vault",
        display_name="Claude Vault",
        hot_cache_path="00_SYSTEM/05_Hot_Cache/HOT_CACHE.md",
        daily_log_path="10_INBOX/Daily_Logs/{date}.md",
    ),
    VaultId.NOTES: VaultConfig(
        vault_id=VaultId.NOTES,
        mcp_server="obsidian-notes-vault",
        display_name="Notes Vault",
        index_path="00_SYSTEM/INDEX.md",
    ),
}


# -- Règles de routing par type de note ---------------------------------------

_TYPE_TO_VAULT: dict[str, VaultId] = {
    # Notes Vault (contenu thématique)
    "manga": VaultId.NOTES,
    "anime": VaultId.NOTES,
    "seiyuu": VaultId.NOTES,
    "studio": VaultId.NOTES,
    "mangaka": VaultId.NOTES,
    "editeur": VaultId.NOTES,
    "magazine": VaultId.NOTES,
    "goodie": VaultId.NOTES,
    "lieu": VaultId.NOTES,
    "evenement": VaultId.NOTES,
    # Claude Vault (système)
    "daily_log": VaultId.CLAUDE,
    "hot_cache": VaultId.CLAUDE,
    "decision": VaultId.CLAUDE,
    "pattern": VaultId.CLAUDE,
    "memory": VaultId.CLAUDE,
    "projet": VaultId.CLAUDE,
    "note": VaultId.CLAUDE,
}

_PATH_PREFIX_TO_VAULT: list[tuple[str, VaultId]] = [
    ("Mangas/", VaultId.NOTES),
    ("Animes/", VaultId.NOTES),
    ("Personnes/", VaultId.NOTES),
    ("Studios/", VaultId.NOTES),
    ("Editeurs/", VaultId.NOTES),
    ("Magazines/", VaultId.NOTES),
    ("00_SYSTEM/", VaultId.CLAUDE),
    ("10_INBOX/", VaultId.CLAUDE),
    ("Projects/", VaultId.CLAUDE),
    (".planning/", VaultId.CLAUDE),
]


# -- Résolution du vault ------------------------------------------------------

class VaultRouterError(Exception):
    """Impossible de résoudre le vault cible."""


def resolve_vault(
    note_type: str | None = None,
    note_path: str | None = None,
    explicit_vault: str | None = None,
) -> VaultConfig:
    """
    Résout la configuration du vault cible.

    Priorité :
    1. explicit_vault (paramètre direct)
    2. note_type (type de note)
    3. note_path (préfixe du chemin)
    4. Défaut → claude-vault

    Args:
        note_type: Type de note (manga, anime, daily_log, etc.)
        note_path: Chemin relatif dans le vault
        explicit_vault: ID vault explicite

    Returns:
        VaultConfig du vault résolu
    """
    if explicit_vault:
        try:
            vid = VaultId(explicit_vault)
            if vid in VAULT_CONFIGS:
                return VAULT_CONFIGS[vid]
        except ValueError:
            pass
        raise VaultRouterError(f"Vault inconnu : '{explicit_vault}'. Valides : {[v.value for v in VaultId]}")

    if note_type:
        norm = note_type.lower().strip()
        vid = _TYPE_TO_VAULT.get(norm)
        if vid and vid in VAULT_CONFIGS:
            return VAULT_CONFIGS[vid]

    if note_path:
        for prefix, vid in _PATH_PREFIX_TO_VAULT:
            if note_path.startswith(prefix) or note_path.startswith(prefix.lower()):
                if vid in VAULT_CONFIGS:
                    return VAULT_CONFIGS[vid]

    return VAULT_CONFIGS[VaultId.CLAUDE]


def get_vault_config(vault_id: VaultId) -> VaultConfig:
    """Récupère la config d'un vault par ID."""
    if vault_id not in VAULT_CONFIGS:
        raise VaultRouterError(f"Vault non configuré : {vault_id}")
    return VAULT_CONFIGS[vault_id]


def list_vaults() -> list[VaultConfig]:
    """Liste tous les vaults configurés."""
    return list(VAULT_CONFIGS.values())
