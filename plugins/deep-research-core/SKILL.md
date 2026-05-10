# Skill : deep-research-core — TricorderKit v0.7

> Recherche autonome locale-first : collecte, deduplique, score et synthetise.

---

## Declencheurs

```text
/tk:deep-research "<requete>"
/tk:deep-research --pipeline manga "<requete>"
/tk:deep-research --pipeline github "<requete>"
/tk:deep-research --dry-run "<requete>"
```

---

## Instructions pour l'agent

### Algorithme de recherche

```text
1. Identifier le pipeline selon la requete (manga / anime / github / vendor)
2. Lire sources/trusted_sources.yml -> selectionner les sources pertinentes
3. Bloquer toute source dans blocked_sources.yml
4. Collecter en parallele (max 3 sources simultanees)
5. Dedupliquer par hash titre + similarite semantique (seuil 0.85)
6. Scorer chaque resultat (0.0 -> 1.0) selon scoring_weights
7. Filtrer : garder score >= 0.70 uniquement
8. Synthetiser en Markdown structure
9. Indexer dans Obsidian (dossier cible selon pipeline)
10. Indexer dans Qdrant si disponible
11. Retourner rapport final avec sources citees
```

### Regles importantes

- Ne jamais utiliser une source hors `trusted_sources.yml`
- Toujours citer les sources dans le rapport final
- Limiter a 500 tokens par item dans la synthese (principe atomique)
- Si Qdrant down -> continuer sans indexation vectorielle (degraded mode)
- Logguer dans `.planning/DECISIONS.md` si la recherche aboutit a une decision

### Pipelines disponibles

| Pipeline | Sources | Usage |
|---|---|---|
| manga | MangaDex, Jikan, Oricon, Natalie | Veille manga, fiches series |
| anime | AniList, AniDB, ANN | Veille anime, staff, studios |
| github | GitHub API, GitHub Search | Audit repos, scoring integration |
| vendor | Personnalise | VPS, services, comparatifs |

---

## Output format

```json
{
  "status": "success",
  "skill_name": "tk-deep-research",
  "query": "<requete>",
  "pipeline": "<pipeline>",
  "items_found": N,
  "items_after_dedup": N,
  "items_above_threshold": N,
  "report_path": "vault/reports/research_YYYY-MM-DD_<slug>.md",
  "output": {
    "summary": "...",
    "data": [...],
    "sources_used": [...]
  }
}
```

---

## Mode degrade

Si les services sont indisponibles :
- Qdrant down -> skip indexation vectorielle, continuer
- Obsidian inaccessible -> sauvegarder dans `vault/reports/` local
- Source API down -> utiliser le cache SQLite si disponible
