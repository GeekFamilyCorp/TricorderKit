"""
obsidian_runner.py — CLI obsidian-agent-layer
TricorderKit obsidian-agent-layer v0.1.0

Commandes :
  vault-list    Lister les vaults Obsidian configurés
  build         Construire une note (dry-run uniquement — pas d'écriture MCP)
  dry-run       Démo complète dry-run (manga Dragon Ball)

Note : Les opérations d'écriture réelles nécessitent un contexte agent Claude
       avec les outils MCP Obsidian connectés. Ce CLI exécute toujours en
       dry_run=True.

Usage :
  python plugins/obsidian-agent-layer/scripts/obsidian_runner.py vault-list
  python plugins/obsidian-agent-layer/scripts/obsidian_runner.py build "One Piece" --type manga
  python plugins/obsidian-agent-layer/scripts/obsidian_runner.py dry-run
  python plugins/obsidian-agent-layer/scripts/obsidian_runner.py build "Test" --json
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ajoute le répertoire plugin (parent de scripts/) au sys.path
_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

import json
import time
from datetime import datetime, timezone
from typing import Optional

import typer

from vault_router import list_vaults, resolve_vault, VaultId
from note_builder import NoteSpec, build_note
from obsidian_client import ObsidianClient, create_client

# -- App -----------------------------------------------------------------------

app = typer.Typer(
    name="obsidian-agent-layer",
    help="TricorderKit obsidian-agent-layer — Construction et gestion de notes Obsidian.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

SKILL_NAME    = "obsidian-agent-layer"
SKILL_VERSION = "0.1.0"


# -- Commandes ----------------------------------------------------------------

@app.command("vault-list")
def cmd_vault_list(
    output_json: bool = typer.Option(False, "--json", help="Sortie JSON"),
) -> None:
    """Liste les vaults Obsidian configurés."""
    vaults = list_vaults()

    if output_json:
        data = [
            {
                "id": vc.vault_id.value,
                "name": vc.display_name,
                "mcp_server": vc.mcp_server,
                "hot_cache": vc.hot_cache_path or None,
                "daily_log": vc.daily_log_path or None,
            }
            for vc in vaults
        ]
        print(json.dumps({"vaults": data, "count": len(data)}, ensure_ascii=False, indent=2))
        return

    typer.echo(f"\n{'─' * 50}")
    typer.echo(f"  Vaults Obsidian configurés ({len(vaults)})")
    typer.echo(f"{'─' * 50}")
    for vc in vaults:
        typer.echo(f"  [{vc.vault_id.value}]  {vc.display_name}")
        typer.echo(f"    MCP : {vc.mcp_server}")
        if vc.hot_cache_path:
            typer.echo(f"    HOT_CACHE : {vc.hot_cache_path}")
        if vc.daily_log_path:
            typer.echo(f"    Daily log : {vc.daily_log_path}")
    typer.echo("")


@app.command("build")
def cmd_build(
    title: str = typer.Argument(..., help="Titre de la note"),
    note_type: str = typer.Option("note", "--type", "-t",
                                  help="Type : manga | anime | seiyuu | studio | note"),
    author: Optional[str] = typer.Option(None, "--author", "-a", help="Auteur (manga/studio)"),
    output_json: bool = typer.Option(False, "--json", help="Sortie JSON"),
) -> None:
    """Construit une note Obsidian (dry-run — pas d'écriture MCP)."""
    start = time.monotonic()

    fields: dict = {}
    if author:
        fields["author"] = author

    spec = NoteSpec(note_type=note_type, title=title, fields=fields)
    note = build_note(spec)

    client = create_client(note_type=note_type, dry_run=True)
    _, op = client.create_structured_note(spec)
    result = client.get_result()
    duration_ms = int((time.monotonic() - start) * 1000)

    if output_json:
        print(json.dumps({
            "note_type": note.note_type,
            "title": note.title,
            "path": note.path,
            "content_length": len(note.content),
            "dry_run": True,
            "operation": op.message,
            "duration_ms": duration_ms,
        }, ensure_ascii=False, indent=2))
        return

    typer.echo(f"\n[DRY-RUN] Note construite :")
    typer.echo(f"  Type    : {note.note_type}")
    typer.echo(f"  Titre   : {note.title}")
    typer.echo(f"  Chemin  : {note.path}")
    typer.echo(f"  Taille  : {len(note.content)} caractères")
    typer.echo(f"  Durée   : {duration_ms}ms")
    typer.echo(f"\n--- Frontmatter ---")
    # Affiche uniquement le frontmatter (entre les premiers ---)
    lines = note.content.splitlines()
    in_fm = False
    for line in lines:
        if line == "---" and not in_fm:
            in_fm = True
            typer.echo(line)
        elif line == "---" and in_fm:
            typer.echo(line)
            break
        elif in_fm:
            typer.echo(line)
    typer.echo("")


@app.command("dry-run")
def cmd_dry_run() -> None:
    """Démo complète dry-run — crée une note manga Dragon Ball."""
    typer.echo("\n[DRY-RUN] obsidian-agent-layer demo\n")

    spec = NoteSpec(
        note_type="manga",
        title="Dragon Ball",
        fields={
            "title_jp": "ドラゴンボール",
            "author": "Toriyama Akira",
            "publisher": "Shueisha",
            "magazine": "Weekly Shonen Jump",
            "volumes": 42,
            "status": "Terminé",
            "source": "https://www.shueisha.co.jp",
        },
        tags=["shonen", "combat", "classic"],
        reliability="✅ Confirmé",
    )

    client = create_client(note_type="manga", dry_run=True)
    note, op = client.create_structured_note(spec)
    result = client.get_result()

    typer.echo(f"  Note construite : {note.path}")
    typer.echo(f"  Opération       : {op.message}")
    typer.echo(f"  Vault résolu    : {result.vault_id}")
    typer.echo(f"  Notes créées    : {result.notes_created}")
    typer.echo("")
    out = result.to_skill_output(duration_ms=0)
    typer.echo(f"  Statut global   : {out['status'].upper()}")
    typer.echo(f"  Résumé          : {out['output']['summary']}")
    typer.echo("")


# -- Entrée principale --------------------------------------------------------

if __name__ == "__main__":
    import io as _io
    if sys.platform == "win32":
        sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    app()
