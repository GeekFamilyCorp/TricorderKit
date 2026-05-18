# TricorderKit — Guide d'exploitation LLM

> Version 0.8 — 2026-05-18
> Manuel pour tout agent Claude (Claude Code ou Cowork) travaillant sur TricorderKit.

---

## Séquence de démarrage obligatoire

```
TIER 1 (toujours — ~500 tokens)
  1. BOOT_SUMMARY.md             → résumé exécutif session

TIER 2 (si BOOT_SUMMARY insuffisant — ~2 500 tokens)
  2. tasks/lessons.md            → règles préventives actives
  3. .planning/STATE.md          → état détaillé
  4. .planning/TASKS.md          → pending/in_progress seulement
  5. .planning/DECISIONS.md      → 5 dernières entrées

TIER 3 (à la demande — ~10 000 tokens)
  6. docs/00_WHAT_IS_TRICORDERKIT.md
  7. docs/01_HOW_IT_WORKS.md
  8. docs/02_WHAT_IS_IN_PLACE.md
  9. docs/03_WHAT_TO_DO_NEXT.md
  10. docs/06_workflow_standard.md
```

---

## 7 Règles non-négociables (v1.0)

| # | Règle |
|---|---|
| R1 | **CLI avant LLM** : vérifier `plugins/cli-forge/generated/` avant tout appel LLM |
| R2 | **Contrat JSON** : tout output de skill → `core/contracts/skill_output.schema.json` |
| R3 | **Dry-run first** : toute commande write → `--dry-run` disponible et testé |
| R4 | **Décisions loguées** : toute décision architecturale → DEC-NNN dans `DECISIONS.md` |
| R5 | **Risques loguées** : tout risque → entrée dans `RISKS.md` |
| R6 | **Vérification avant done** : preuve observable avant de conclure une tâche |
| R7 | **Pas de récréation** : vérifier `skills/`, `plugins/cli-forge/generated/`, `plugins/workflow-engine/` avant de créer |

**Règles additionnelles Workflow Standard v1.0 (R8→R15) :** voir `docs/06_workflow_standard.md`

---

## Pattern CLI Goat — Référence

```python
# Structure minimale d'un goat conforme
import argparse, json, sqlite3

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--format", choices=["json", "table"], default="json")
    args = parser.parse_args()

    if args.dry_run:
        print(json.dumps({"status": "dry_run", "command": args.command}))
        return

    result = execute_command(args.command)  # logique métier

    output = {
        "status": "success",
        "skill_name": "my-goat",
        "skill_version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "output": {"data": result, "next_steps": []}
    }
    print(json.dumps(output, ensure_ascii=False))

# Cache SQLite — pattern standard
def get_cached(key: str, ttl_seconds: int = 3600):
    conn = sqlite3.connect(".cache/my-goat.db")
    # ... implémentation cache
```

Goat de référence complet : `tools/github-goat/github_goat.py`

---

## Patterns d'erreurs courants

| Erreur | Cause | Solution |
|---|---|---|
| `BOOT_SUMMARY.md` introuvable | Fichier non créé | `cp BOOT_SUMMARY.md.template BOOT_SUMMARY.md` |
| `Prompt is too long` | Contexte surchargé | `/tk:pack-context` + charger TIER 1 seulement |
| Temporal worker inactif | Worker non démarré | `docker compose ps` puis `npx ts-node plugins/workflow-engine/scripts/start_worker.ts` |
| Contrat JSON non valide | Output non conforme | Lire `core/contracts/skill_output.schema.json` et adapter |
| Chemin MSIX introuvable | PATTERN-ENV-001 | Utiliser `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\` |
| Hook inerte | PATTERN-ARCH-002 | Les hooks Cowork ne s'exécutent pas — implémenter dans SKILL.md |
| SQLite en Temporal | — | Temporal requiert PostgreSQL — voir `docker-compose.yml` |

---

## Commandes de référence

```bash
# Santé système
python scripts/health_check.py
tk doctor
docker compose ps

# Validation repo
python scripts/validate_repo.py

# Hook stats
python scripts/hook_stats.py
tk hook-stats

# Tests
pytest tests/ -v
pytest tests/ --live   # tests réseau (MangaDex, AniList)

# Linked project
tk project list
tk project status japan-alliance
python tools/audit/linked_project_audit.py --project japan-alliance

# CLI goat
python tools/github-goat/github_goat.py list-repos --dry-run
python tools/github-goat/github_goat.py list-repos --format json

# Temporal workflow
tk workflow list
tk workflow start source_watch
```

---

## Procédure de fin de session

```
1. Cocher les tâches complétées dans tasks/todo.md
2. Ajouter leçons dans tasks/lessons.md si correction
3. Mettre à jour BOOT_SUMMARY.md (version, commit, prochaines tâches)
4. Mettre à jour .planning/STATE.md si phase ou plugin changé
5. Mettre à jour HOT_CACHE Obsidian (via obsidian-goat ou manuellement)
6. Git commit si changements significatifs
```

---

*TricorderKit v0.8 — GeekFamilyCorp — 2026-05-18*
