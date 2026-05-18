# Skill: rtk — Research TricorderKit

> Version 0.1.0 — 2026-05-18
> Wrapper Cowork vers le pipeline deep-research-core CLI.
> Exécute collect → dedup → score → export → index en pipeline complet.

---

## Triggers

```text
/tk:research "<query>"
/rtk "<query>"
rtk
deep research
lance une recherche
recherche approfondie sur
pipeline de recherche
```

---

## Prérequis

Avant d'exécuter ce skill, vérifier :
1. `plugins/deep-research-core/` présent dans le repo
2. `sources/trusted_sources.yml` contient les sources du domaine
3. Qdrant optionnel (dégradé sans indexation vectorielle)

---

## Instructions agent

### Séquence d'exécution

```text
ÉTAPE 1 — Intent extraction
  → Extraire : query, domain, pipeline, dry_run
  → domain par défaut : "general"
  → pipeline par défaut : "content"

ÉTAPE 2 — Pre-execution check (R3 dry-run)
  → Exécuter collect_sources.py --dry-run d'abord
  → Valider que les sources sont disponibles
  → Afficher preview avant exécution réelle

ÉTAPE 3 — Collect (CLI goat)
  python plugins/deep-research-core/scripts/collect_sources.py \
    --query "<query>" \
    --domain <domain> \
    [--sources <liste>] \
    [--dry-run]

ÉTAPE 4 — Score + Dedup (pipe)
  <output_collect> | python plugins/deep-research-core/scripts/score_reliability.py

ÉTAPE 5 — Export rapport
  python plugins/deep-research-core/scripts/export_report.py \
    --input <scored_results> \
    --format markdown

ÉTAPE 6 — Index Qdrant (si disponible)
  python plugins/deep-research-core/scripts/index_qdrant.py \
    --input <scored_results> \
    --collection <domain>
  → Si Qdrant down : continuer sans indexation (log warning)

ÉTAPE 7 — Output contractuel JSON
  → Retourner au format skill_output.schema.json
```

### Sélection du pipeline

| Pipeline | Cas d'usage |
|---|---|
| `content` | Veille contenu, fiches entités, news |
| `entity` | Auteurs, éditeurs, studios, personnes |
| `github` | Audit repos, scoring intégrations |
| `vendor` | Services, comparatifs, VPS |

### Règles importantes

- **CLI avant LLM (R1)** : toujours exécuter les scripts Python, jamais synthétiser de mémoire
- **Dry-run (R3)** : toujours valider collect en `--dry-run` avant exécution réelle
- Ne jamais utiliser de source hors `trusted_sources.yml`
- Citer les sources dans le rapport final
- Limiter à 500 tokens par item (principe atomique Obsidian)
- Si Qdrant indisponible → continuer en mode dégradé, logger le warning
- Loguer dans `.planning/DECISIONS.md` si la recherche mène à une décision architecturale

---

## Commandes de référence

```bash
# Dry-run (vérification sources)
python plugins/deep-research-core/scripts/collect_sources.py \
  --query "One Piece" --domain manga --dry-run

# Pipeline complet
python plugins/deep-research-core/scripts/collect_sources.py \
  --query "One Piece" --domain manga \
  | python plugins/deep-research-core/scripts/score_reliability.py \
  | python plugins/deep-research-core/scripts/export_report.py --format markdown

# Avec indexation Qdrant
python plugins/deep-research-core/scripts/index_qdrant.py \
  --collection manga --input results.json
```

---

## Format de sortie contractuel

```json
{
  "status": "success",
  "skill_name": "rtk",
  "skill_version": "0.1.0",
  "timestamp": "2026-05-18T10:00:00Z",
  "output": {
    "query": "One Piece",
    "domain": "manga",
    "pipeline": "content",
    "results_count": 12,
    "results_above_threshold": 8,
    "threshold": 0.70,
    "report_path": "reports/research_one_piece_2026-05-18.md",
    "qdrant_indexed": true,
    "sources_used": ["mangadex", "anilist", "jikan"],
    "top_results": [],
    "next_steps": ["Vérifier doublon avec fiche existante", "Indexer dans Obsidian si nouveau"]
  },
  "metadata": {
    "dry_run": false,
    "tokens_estimated": 800,
    "pipeline_steps": ["collect", "dedup", "score", "export", "index"]
  }
}
```

---

## Gestion d'erreurs

| Erreur | Cause probable | Action |
|---|---|---|
| `trusted_sources.yml introuvable` | Plugin non installé | Vérifier `plugins/deep-research-core/sources/` |
| `Qdrant connection refused` | Service Docker arrêté | Mode dégradé — continuer sans index vectoriel |
| `0 résultats collectés` | Sources down ou query trop précise | Élargir query, vérifier réseau |
| `score < 0.70 pour tous` | Données peu fiables | Reporter `🟠 À vérifier` dans le rapport |
| `Jikan 504` | Rate limit Jikan (connu) | Non bloquant — ignorer et continuer |

---

## Intégration caveman (R15)

Quand ce skill est appelé par un sous-agent ou dans un pipeline inter-agents :

```json
{
  "status": "ok",
  "task": "rtk_research",
  "data": {
    "results": 8,
    "report": "reports/research_xxx.md",
    "qdrant": true
  },
  "tokens_used": 1200,
  "next_action": "docmancer_index"
}
```

---

*TricorderKit v0.8 — GeekFamilyCorp — 2026-05-18*
