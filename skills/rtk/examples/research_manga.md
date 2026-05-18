# Exemple : Recherche manga avec rtk

## Input utilisateur

```
/rtk "Dungeon Meshi" --domain manga --pipeline entity
```

## Exécution

### Étape 1 — Dry-run
```bash
python plugins/deep-research-core/scripts/collect_sources.py \
  --query "Dungeon Meshi" --domain manga --dry-run
```

Résultat attendu :
```json
{"status": "dry_run", "query": "Dungeon Meshi", "sources_available": ["mangadex", "anilist", "jikan"]}
```

### Étape 2 — Collect réel
```bash
python plugins/deep-research-core/scripts/collect_sources.py \
  --query "Dungeon Meshi" --domain manga --sources mangadex anilist
```

### Étape 3 — Score
```bash
... | python plugins/deep-research-core/scripts/score_reliability.py
```

### Étape 4 — Export
```bash
... | python plugins/deep-research-core/scripts/export_report.py --format markdown
```

## Output contractuel

```json
{
  "status": "success",
  "skill_name": "rtk",
  "output": {
    "query": "Dungeon Meshi",
    "domain": "manga",
    "results_count": 15,
    "results_above_threshold": 12,
    "report_path": "reports/research_dungeon_meshi_2026-05-18.md"
  }
}
```
