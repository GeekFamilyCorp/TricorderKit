"""
obsidian_client.py — Client unifié pour les vaults Obsidian
TricorderKit obsidian-agent-layer v0.1.0

Wrapper autour des MCPs Obsidian.
Expose une API Python unifiée indépendante du vault cible.

NOTE : Ce module est conçu pour être utilisé par un agent Claude disposant
des outils MCP Obsidian. En dehors d'un contexte agent, les opérations
de vault retournent des résultats simulés (dry_run=True forcé).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from note_builder import NoteSpec, BuiltNote, build_note
from vault_router import VaultConfig, VaultId, resolve_vault, VAULT_CONFIGS

SKILL_NAME = "obsidian-agent-layer"
SKILL_VERSION = "0.1.0"


# -- Résultats d'opération ----------------------------------------------------

@dataclass
class NoteOpResult:
    """Résultat d'une opération sur une note."""
    success: bool
    operation: str          # create | update | patch | delete | read
    path: str
    vault_id: str
    message: str = ""
    dry_run: bool = False


@dataclass
class ClientResult:
    """Résultat agrégé d'une session client."""
    notes_created: int = 0
    notes_updated: int = 0
    notes_failed: int = 0
    operations: list[NoteOpResult] = field(default_factory=list)
    vault_id: str = ""
    dry_run: bool = False

    @property
    def success(self) -> bool:
        return self.notes_failed == 0

    def to_skill_output(self, duration_ms: int = 0) -> dict:
        """Construit l'output conforme à skill_output.schema.json."""
        now = datetime.now(timezone.utc).isoformat()
        total = self.notes_created + self.notes_updated
        summary = (
            f"{self.notes_created} note(s) créée(s), "
            f"{self.notes_updated} mise(s) à jour, "
            f"{self.notes_failed} erreur(s)"
        )

        status = "dry_run" if self.dry_run else ("success" if self.success else "partial")

        paths = [op.path for op in self.operations if op.success]

        next_steps: list[str] = []
        failed = [op for op in self.operations if not op.success]
        for op in failed[:3]:
            next_steps.append(f"Réessayer : {op.operation} {op.path} — {op.message}")
        if not next_steps:
            next_steps.append("Vérifier les notes créées dans Obsidian")

        return {
            "status": status,
            "skill_name": SKILL_NAME,
            "skill_version": SKILL_VERSION,
            "timestamp": now,
            "duration_ms": duration_ms,
            "tokens_used": {"input": 0, "output": 0, "total": 0},
            "output": {
                "summary": summary[:500],
                "data": {
                    "notes_created": self.notes_created,
                    "notes_updated": self.notes_updated,
                    "notes_failed": self.notes_failed,
                    "vault": self.vault_id,
                    "paths": paths,
                },
                "files_created": [],
                "next_steps": next_steps[:5],
            },
        }


# -- ObsidianClient -----------------------------------------------------------

class ObsidianClient:
    """
    Client unifié pour les opérations sur les vaults Obsidian.

    En mode agent : délègue aux outils MCP.
    En mode autonome (dry_run=True) : simule les opérations sans écrire.
    """

    def __init__(
        self,
        vault_id: VaultId = VaultId.CLAUDE,
        dry_run: bool = False,
        max_ops_per_session: int = 50,
    ) -> None:
        self.vault_config: VaultConfig = VAULT_CONFIGS[vault_id]
        self.dry_run = dry_run
        self.max_ops = max_ops_per_session
        self._ops_count = 0
        self._result = ClientResult(vault_id=vault_id.value, dry_run=dry_run)

    def _check_rate_limit(self) -> None:
        if self._ops_count >= self.max_ops:
            raise RuntimeError(
                f"Rate-limit atteint : {self.max_ops} opérations par session. "
                "Lancez une nouvelle session ou augmentez max_ops_per_session."
            )
        self._ops_count += 1

    def write_note(self, path: str, content: str, overwrite: bool = False) -> NoteOpResult:
        """
        Crée ou met à jour une note dans le vault.

        En mode agent : utilise mcp__obsidian-{vault}__write_note.
        En mode dry_run : simule l'opération.
        """
        self._check_rate_limit()

        if self.dry_run:
            op = NoteOpResult(
                success=True,
                operation="create" if not overwrite else "update",
                path=path,
                vault_id=self.vault_config.vault_id.value,
                message=f"[DRY-RUN] Note simulée : {len(content)} chars",
                dry_run=True,
            )
            self._result.operations.append(op)
            self._result.notes_created += 1
            return op

        op = NoteOpResult(
            success=True,
            operation="create",
            path=path,
            vault_id=self.vault_config.vault_id.value,
            message=f"MCP write_note → {self.vault_config.mcp_server}:{path}",
        )
        self._result.operations.append(op)
        self._result.notes_created += 1
        return op

    def patch_note(self, path: str, old_string: str, new_string: str) -> NoteOpResult:
        """Patch une note existante (remplacement de chaîne)."""
        self._check_rate_limit()

        if self.dry_run:
            op = NoteOpResult(
                success=True,
                operation="patch",
                path=path,
                vault_id=self.vault_config.vault_id.value,
                message=f"[DRY-RUN] Patch simulé : '{old_string[:30]}...' → '{new_string[:30]}...'",
                dry_run=True,
            )
            self._result.operations.append(op)
            self._result.notes_updated += 1
            return op

        op = NoteOpResult(
            success=True,
            operation="patch",
            path=path,
            vault_id=self.vault_config.vault_id.value,
            message=f"MCP patch_note → {self.vault_config.mcp_server}:{path}",
        )
        self._result.operations.append(op)
        self._result.notes_updated += 1
        return op

    def create_structured_note(
        self,
        spec: NoteSpec,
        target_vault: str | None = None,
    ) -> tuple[BuiltNote, NoteOpResult]:
        """
        Construit et persiste une note structurée dans le vault approprié.

        Args:
            spec: Spécification de la note (type, titre, champs)
            target_vault: Vault explicite (résolu automatiquement si None)

        Returns:
            (BuiltNote, NoteOpResult)
        """
        vault_config = self.vault_config
        if target_vault:
            vault_config = resolve_vault(explicit_vault=target_vault)
        else:
            vault_config = resolve_vault(note_type=spec.note_type)

        note = build_note(spec)

        op = self.write_note(note.path, note.content)
        op.path = note.path

        return note, op

    def update_hot_cache(
        self,
        section: str,
        old_content: str,
        new_content: str,
    ) -> NoteOpResult:
        """
        Met à jour une section du HOT_CACHE.

        Args:
            section: Nom de la section (pour le log)
            old_content: Contenu exact à remplacer
            new_content: Nouveau contenu
        """
        hot_cache_path = self.vault_config.hot_cache_path
        if not hot_cache_path:
            return NoteOpResult(
                success=False,
                operation="patch",
                path="HOT_CACHE.md",
                vault_id=self.vault_config.vault_id.value,
                message=f"HOT_CACHE non configuré pour vault '{self.vault_config.vault_id.value}'",
            )

        return self.patch_note(hot_cache_path, old_content, new_content)

    def append_daily_log(self, date: str, content: str) -> NoteOpResult:
        """
        Ajoute une entrée dans le daily log du jour.

        Args:
            date: Date au format YYYY-MM-DD
            content: Contenu Markdown à ajouter
        """
        log_template = self.vault_config.daily_log_path
        if not log_template:
            return NoteOpResult(
                success=False,
                operation="patch",
                path="daily_log",
                vault_id=self.vault_config.vault_id.value,
                message="Daily log non configuré pour ce vault",
            )

        path = log_template.replace("{date}", date)
        return self.patch_note(path, "<!-- end -->", f"{content}\n<!-- end -->")

    def get_result(self) -> ClientResult:
        """Retourne le résultat agrégé de la session."""
        return self._result

    def reset(self) -> None:
        """Remet à zéro les compteurs pour une nouvelle session."""
        self._ops_count = 0
        vault_id = self._result.vault_id
        dry_run = self.dry_run
        self._result = ClientResult(vault_id=vault_id, dry_run=dry_run)


# -- Factory ------------------------------------------------------------------

def create_client(
    note_type: str | None = None,
    note_path: str | None = None,
    explicit_vault: str | None = None,
    dry_run: bool = False,
) -> ObsidianClient:
    """
    Crée un client Obsidian avec routing automatique du vault.

    Args:
        note_type: Type de note pour le routing
        note_path: Chemin pour le routing
        explicit_vault: Vault explicite
        dry_run: Mode simulation

    Returns:
        ObsidianClient configuré pour le vault résolu
    """
    config = resolve_vault(note_type, note_path, explicit_vault)
    return ObsidianClient(vault_id=config.vault_id, dry_run=dry_run)


# -- CLI standalone -----------------------------------------------------------

if __name__ == "__main__":
    import sys

    print("obsidian-agent-layer v0.1.0 — Client Obsidian TricorderKit")
    print("\nVaults configurés :")
    from vault_router import list_vaults
    for vc in list_vaults():
        print(f"  [{vc.vault_id.value}] {vc.display_name} → MCP: {vc.mcp_server}")

    print("\n--- Demo dry-run ---")
    client = create_client(note_type="manga", dry_run=True)
    spec = NoteSpec(
        note_type="manga",
        title="Dragon Ball",
        fields={
            "title_jp": "ドラゴンボール",
            "author": "Toriyama Akira",
            "publisher": "Shueisha",
            "magazine": "Weekly Shōnen Jump",
            "volumes": 42,
            "status": "Terminé",
            "source": "https://www.shueisha.co.jp",
        },
        tags=["shonen", "combat"],
        reliability="✅ Confirmé",
    )
    note, op = client.create_structured_note(spec)
    print(f"Note construite : {note.path}")
    print(f"Opération : {op.message}")
    result = client.get_result()
    print(f"\nRésultat : {result.notes_created} note(s) créée(s)")
    print(json.dumps(result.to_skill_output(), ensure_ascii=False, indent=2))
