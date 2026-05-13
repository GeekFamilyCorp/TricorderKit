# Standard d'implémentation Typer pour CLIs cli-forge

> Référence : `plugins/cli-forge/cli_manifest.schema.json` (manifest)
> Référence : `core/contracts/skill_output.schema.json` (output) — DEC-005
> Décision d'adoption : DEC-010 — 13/05/2026

## 0. Portée

Ce document décrit **comment implémenter une CLI Typer** qui respecte les
contrats officiels TricorderKit. Les schémas JSON restent l'autorité de fait :
ce document n'invente aucun nouveau standard, il documente l'implémentation
Python conforme.

S'applique à toute **nouvelle** CLI cli-forge créée après le 13/05/2026.
Les CLIs argparse existantes (`github-goat`, `source-watch-goat`) sont
tolérées en mode `framework: argparse_legacy` jusqu'à migration via PR
dédiée.

## 1. Framework

- **Par défaut** : Typer ≥ 0.12 (Click 8.2+)
- **Toléré (legacy)** : argparse (CLIs préexistantes uniquement)
- **Interdit** : autres frameworks (click direct, fire, ad-hoc)

## 2. Contrat technique

### 2.1 Exposer `app` au niveau module

```python
import typer
app = typer.Typer(help="Description courte de la CLI")
```

`app` doit être importable depuis le module racine pour permettre :
- les tests CliRunner (`from tools.<cli>.<cli> import app`)
- l'inscription dans `pyproject.toml` `[project.scripts]`

### 2.2 `--help` et `--version`

`--help` est géré nativement par Typer.

`--version` est une option globale sur le callback racine :

```python
def _version_callback(value: bool) -> None:
    if value:
        typer.echo("tk-installer 0.1.0")
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True,
        help="Affiche la version et quitte.",
    )
) -> None:
    pass
```

### 2.3 `--output {pretty|json}`

Toute commande qui produit un résultat structuré doit accepter `--output`.

- `pretty` (défaut) : sortie humaine via `rich.console.Console(stderr=True)`
- `json` : un seul payload JSON sur stdout, **rien d'autre**

### 2.4 Schéma JSON de sortie — `skill_output.schema.json`

**Le format JSON est imposé par `core/contracts/skill_output.schema.json`.**
Aucune réinvention. Champs obligatoires :

| Champ | Type | Contrainte |
|---|---|---|
| `status` | string | `success` / `partial` / `error` / `dry_run` |
| `skill_name` | string | `<cli-name>.<command>` (ex: `tk-installer.status`) |
| `skill_version` | string | semver `X.Y.Z` |
| `timestamp` | string | ISO 8601 date-time avec suffixe `Z` |
| `output` | object | contient au moins `output.summary` |
| `output.summary` | string | ≤ 500 caractères, obligatoire |

Champs conditionnels :

- `output.data` : structure libre selon la commande
- `output.files_created` : `string[]` — fichiers créés ou modifiés
- `output.next_steps` : `string[]`, max 5 éléments
- `error` (si `status=error`) : `{code, message, recoverable, rollback_available}`
- `dry_run_report` (si `status=dry_run`) : `{actions_that_would_run, estimated_tokens, estimated_duration_ms, risk_level}`

Champs recommandés :

- `duration_ms` : int
- `tokens_used` : `{input, output, total}`

Exemple minimal conforme :

```json
{
  "status": "success",
  "skill_name": "tk-installer.status",
  "skill_version": "0.1.0",
  "timestamp": "2026-05-13T08:30:00Z",
  "duration_ms": 142,
  "output": {
    "summary": "3/7 phases verified. 0 blocker.",
    "data": { "phases": { } },
    "next_steps": ["Avancer sur phase_25_quality_guard."]
  }
}
```

### 2.5 `--dry-run` pour toute commande destructive

Toute commande qui crée, modifie ou supprime un fichier ou un état distant
doit accepter `--dry-run`.

En mode dry-run :
- Aucune écriture disque
- Aucun appel réseau modifiant un état
- Le payload de retour a `status: "dry_run"` et contient un `dry_run_report`
  conforme au schéma (`actions_that_would_run`, `risk_level`)

### 2.6 Exit codes standardisés

| Code | Sens |
|---|---|
| 0 | Succès (`status: success` ou `status: dry_run`) |
| 1 | Erreur métier attendue (`status: partial` ou `status: error` simple) |
| 2 | Mauvais usage CLI (géré auto par Typer) |
| 3 | Environnement KO (Python/Git/Docker absent, repo root introuvable) |
| 4 | Gate de phase bloquée |
| 5 | Conflit anti-écrasement (fichier existe sans `--force`) |
| ≥10 | Erreurs spécifiques par CLI, documentées dans son README |

### 2.7 Aucun secret en stdout/stderr

- Pas de token, mot de passe, clé API affiché
- Sanitisation obligatoire si la CLI manipule des credentials
- Couvert par un test paramétrisé `TestNoSecretsLeaked`

### 2.8 Tests CliRunner obligatoires

Localisation : `tests/cli_contracts/test_<cli_name>.py`.

Classes de tests minimales :

- `TestContractHelp` — au moins 1 test sur `--help`
- `TestContractVersion` — au moins 1 test sur `--version`
- `TestSchemaXXX` — pour chaque commande, valider les `required` du schéma
- `TestNoSecretsLeaked` — test paramétrisé sur toutes les commandes
- `TestExitCodes` — vérifier 0/2 au minimum

Référence d'implémentation : `tests/cli_contracts/test_tk_installer.py`.

## 3. Conventions

### 3.1 Nommage

- Commande shell : `kebab-case` (`tk-installer`, `mangatracker-cli`)
- Module Python : `snake_case` (`tk_installer.py`)
- Option Typer : `--kebab-case`
- Paramètre Python : `snake_case`

### 3.2 Structure de fichier

**CLI internes simples** (orchestrateurs, outils internes) : flat

```text
tools/<cli_name>/
├── __init__.py
├── README.md
└── <cli_name>.py            # exporte `app`
```

**CLIs métier livrables** (`jp-scraper`, `mangatracker-cli`) : src layout

```text
tools/<cli-name>/
├── pyproject.toml
├── README.md
├── requirements.txt
├── src/<cli_name>/
│   ├── __init__.py
│   ├── cli.py               # exporte `app`
│   └── ...
```

### 3.3 Logs vs sortie

- `print()` est interdit en mode `--output json` (pollue stdout)
- Utiliser `rich.console.Console(stderr=True)` ou `logging` pour les messages humains
- En mode JSON : **un seul** payload JSON sur stdout, **rien d'autre**

### 3.4 Anti-écrasement

Toute commande qui écrit un fichier existant doit :

1. Vérifier la présence du fichier
2. Refuser sans `--force` (exit code 5, `error.code: "FILE_EXISTS"`)
3. Créer un backup dans `reports/install/backups/YYYY-MM-DD/` avant écrasement avec `--force`
4. Documenter le backup dans `output.files_created`

## 4. Inscription dans le registry

Toute CLI doit être ajoutée à `plugins/cli-forge/registry.yml` avec une
entrée conforme au format du registry. Au minimum :

```yaml
  - name: <cli-name>
    version: X.Y.Z
    status: pending | dry_run_validated | prod_ready
    path: tools/<cli_name>/<cli_name>.py
    manifest: tools/<cli_name>/manifest.yml
    description: ...
    service: ...
    auth_required: false | true
    safe_for_agents: false | true
    dry_run_tested: true
    dry_run_date: "YYYY-MM-DD"
    prod_audit_done: false
    framework: typer | argparse_legacy        # extension v0.8 / DEC-010
    tags: [...]
    commands: [...]
```

Le manifest CLI lui-même doit valider contre
`plugins/cli-forge/cli_manifest.schema.json`. Note : pour les CLIs internes
(catégorie `internal-tool`), le champ `source_api` du schéma manifest est
contraignant et fera l'objet d'une PR séparée pour assouplir le contrat.

## 5. Anti-patterns interdits

- ❌ `input()` interactif (CLIs non-interactives uniquement)
- ❌ Mélanger logs humains et JSON sur stdout
- ❌ Écraser un fichier sans backup
- ❌ Quitter sans exit code explicite
- ❌ Laisser remonter une exception Python brute à l'utilisateur
- ❌ Coupler la CLI à un serveur MCP (autonomie obligatoire)
- ❌ Afficher secrets/tokens en stdout/stderr
- ❌ Réinventer le payload JSON (le schéma `skill_output.schema.json` fait foi)

## 6. Migration argparse → Typer

Pour les CLIs argparse existantes :

1. Marquer `framework: argparse_legacy` dans `registry.yml`
2. Créer une issue de migration dédiée
3. **Ne jamais** convertir automatiquement (conversion auto interdite)
4. Migration via PR dédiée avec tests CliRunner

## 7. Référence d'implémentation

- CLI Typer de référence : `tools/tk_installer/tk_installer.py`
- Tests CliRunner de référence : `tests/cli_contracts/test_tk_installer.py`
- Schéma manifest : `plugins/cli-forge/cli_manifest.schema.json`
- Schéma output : `core/contracts/skill_output.schema.json`
- Validateur manifest : `python plugins/cli-forge/scripts/validate_cli_manifest.py --all`
