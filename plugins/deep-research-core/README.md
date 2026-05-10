# deep-research-core — Plugin TricorderKit v0.7

> Moteur de recherche autonome local-first pour TricorderKit.

---

## Pourquoi deep-research-core ?

Les agents TricorderKit ont besoin de recherches structurées, sourcées et indexées — pas de réponses improvisées.

Ce plugin transforme une requête en rapport Markdown sourcé, indexé dans Obsidian et le vault RAG (Qdrant).

---

## Pipeline cognitif

```text
Requête utilisateur
        ↓
Source Selector (trusted_sources.yml)
        ↓
Collecte multi-source parallèle
        ↓
Déduplication (hash + similarité sémantique)
        ↓
Score de fiabilité (0.0 → 1.0)
        ↓
Synthèse Markdown structurée
        ↓
Indexation Obsidian + Qdrant (RAG)
        ↓
Rapport final sourcé
```

---

## Cas d'usage

- Veille MangaTracker (nouvelles sorties, classements Oricon)
- Veille AnimeTracker (saison en cours, studios, staff)
- Enrichissement fiches mangakas / éditeurs japonais
- Audits de repos GitHub (scoring, intégration TricorderKit)
- Recherche approfondie VPS / infra

---

## Commandes TricorderKit

```bash
/tk:deep-research "<requête>"      # Lance une recherche complète
/tk:deep-research --pipeline manga # Utilise le pipeline manga
/tk:deep-research --dry-run "<q>"  # Simule sans recherche réelle
```

---

## Structure du plugin

```text
plugins/deep-research-core/
├── README.md                          ← ce fichier
├── SKILL.md
├── sources/
│   ├── trusted_sources.yml            ← sources fiables autorisées
│   ├── blocked_sources.yml            ← sources bloquées
│   └── japanese_sources.yml           ← sources japonaises spécifiques
├── pipelines/
│   ├── manga_sources_research.yml     ← pipeline manga
│   ├── anime_staff_research.yml       ← pipeline anime/staff
│   ├── github_research.yml            ← pipeline GitHub
│   └── vendor_research.yml            ← pipeline vendeurs / VPS
└── scripts/
    ├── collect_sources.py             ← collecte multi-source
    ├── score_reliability.py           ← scoring fiabilité
    ├── deduplicate_findings.py        ← déduplication
    └── export_report.py               ← export rapport Markdown
```

---

## Inspiré de

- `LearningCircuit/local-deep-research` — moteur de recherche autonome local

---

*Version 0.1.0 — 10/05/2026*
