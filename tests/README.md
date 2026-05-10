# tests/ — TricorderKit v0.7

Suite de tests : contrats CLI, evals skills, sécurité.

## Structure

```text
tests/
├── cli_contracts/     # Tests de contrats des CLIs (output schema)
├── evals/             # Eval non-régression des skills
└── security/          # Tests d'audit sécurité
```

## Lancer les tests

```bash
# Contrats CLI
python tests/cli_contracts/test_github_goat.py
python tests/cli_contracts/test_source_watch_goat.py

# Validation repo
python scripts/validate_repo.py

# Validation manifests CLI
python plugins/cli-forge/scripts/validate_cli_manifest.py --all
```

## Règle

Tout skill modifié -> test eval obligatoire avant merge.  
Toute CLI enregistrée -> contract test obligatoire avant `prod_ready`.
