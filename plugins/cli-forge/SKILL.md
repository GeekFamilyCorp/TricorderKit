---
name: cli-forge
description: >
  S'active quand l'utilisateur demande de créer, modifier, tester ou
  référencer une CLI Python dans TricorderKit. Déclencheurs : "nouvelle
  CLI", "convertir argparse en Typer", "ajouter au registry", "template
  CLI", "test CliRunner", "tk-installer", "github-goat", "jp-scraper",
  "mangatracker-cli", "source-watch-goat".
version: 0.2.0
author: GeekFamilyCorp
license: TBD
domain: tooling
activation: explicit
compatibility: [claude, generic-agents]
tested_with: [claude-opus-4-7]
security: scan-required-before-publish
status: prototype
token_hygiene:
  reuse_first: true
  minimal_patch: true
---

# cli-forge — Skill

## Rôle

Guider la création et la maintenance de CLIs cli-forge conformes aux
contrats officiels TricorderKit :

- Manifest : `plugins/cli-forge/cli_manifest.schema.json`
- Output : `core/contracts/skill_output.schema.json` (DEC-005)
- Implémentation Typer : `docs/cli_forge_typer_standard.md` (DEC-010)

## Quand m'activer

- Création d'une nouvelle CLI (`tk-*`, `mangatracker-*`, `jp-*`, autres)
- Conversion d'une CLI argparse legacy vers Typer (PR dédiée obligatoire)
- Audit d'une CLI existante face aux contrats
- Ajout d'une entrée dans `plugins/cli-forge/registry.yml`
- Génération des tests CliRunner manquants

## Quand NE PAS m'activer

- Modification métier d'une CLI déjà conforme (utiliser code-change-minimizer)
- Question Webflow / Client-First (hors scope tooling Python)
- Script Python sans interface CLI (un module utilitaire ne passe pas par cli-forge)

## Procédure pour créer une nouvelle CLI

1. **Lire** `docs/cli_forge_typer_standard.md`
2. **Copier** le template `plugins/cli-forge/templates/typer_cli.py.j2`
3. **Implémenter** dans `tools/<cli_name>/<cli_name>.py` (snake_case package, kebab-case commande)
4. **Exposer `app`** au niveau module
5. **Supporter** : `--help`, `--version`, `--output {pretty,json}`,
   `--dry-run` si destructif, `--force` si écrasement
6. **Émettre** un payload conforme à `skill_output.schema.json` (champs requis :
   status, skill_name, skill_version, timestamp, output.summary)
7. **Tester** via le template `templates/typer_test.py.j2` → `tests/cli_contracts/test_<cli>.py`
8. **Valider le manifest** : `python plugins/cli-forge/scripts/validate_cli_manifest.py <path>`
9. **Inscrire** au registry avec `framework: typer` et `status: dry_run_validated`
10. **Tests verts** : `pytest tests/cli_contracts/test_<cli>.py -v`

## Anti-patterns interdits

- `input()` interactif
- `print()` mélangé au JSON sur stdout
- Conversion automatique argparse → Typer (PR dédiée requise)
- Écraser un fichier existant sans `--force` + backup
- Réinventer le payload JSON (le schéma fait foi)
- Coupler la CLI à un serveur MCP

## Référence canonique

En cas de divergence entre ce skill et les fichiers ci-dessous, **les
schémas et les docs `docs/` font foi** :

- `core/contracts/skill_output.schema.json`
- `plugins/cli-forge/cli_manifest.schema.json`
- `docs/cli_forge_typer_standard.md`
