---
type: reference
version: 1.0
created: 2026-05-24
author: claude
status: active
project: TricorderKit
tags: [architecture, vault, instructions, multi-project]
replaces: ["Vault et arborescence.md", "Multi-linked-project.md", "a faire.md"]
---

# Instructions Adaptées — Architecture Multi-Vault TricorderKit v0.9

> Ce document remplace et consolide les trois fichiers théoriques produits antérieurement.
> Il est aligné sur les arborescences **réelles** des deux vaults (vérifiées le 2026-05-24).
> **Règle d'or : ne restructurer que ce qui est absent. Ne jamais renommer ce qui existe.**

---

## 1. Topographie réelle de l'écosystème

```
TricorderKit (Repo public — moteur générique)
    └── MangaTracker (Repo privé — linked_project ETL)
            └── Japan-Alliance vault (5 277 notes — données de production)

claude-vault (300 notes — mémoire opérationnelle de Claude)
    └── route vers → Japan-Alliance vault (lecture/écriture ciblée)
```

### Rôles confirmés

| Composant | Rôle | Nature |
|-----------|------|--------|
| **TricorderKit** | Moteur agnostique | Code, CLI, Temporal, hooks |
| **MangaTracker** | Usine ETL spécialisée | Scraping, normalisation, injection |
| **claude-vault** | Cerveau de contrôle Claude | Mémoire, roadmap, métriques, erreurs |
| **Japan-Alliance** | Base de production | Données, templates, config système |

---

## 2. Arborescences réelles (ne pas modifier sans audit)

### 2.1 claude-vault — `<claude-vault-path>`

```
claude-vault/                        300 notes · 136 dossiers
│
├── 00_SYSTEM/                       ← Cerveau opérationnel Claude
│   ├── 00_Skills/                   Référentiel skills disponibles
│   ├── 01_CLI_Reference/            Commandes CLI documentées
│   ├── 02_Prompts/                  Templates de prompts
│   ├── 03_Rules/                    Règles Markdown, conventions
│   ├── 04_Self_Learning/            Cycle d'apprentissage (LEARNING_LOOP.md)
│   ├── 05_Hot_Cache/                HOT_CACHE.md — à lire en PREMIER
│   ├── 06_Successes/                Succès documentés
│   ├── 06_Templates/                Templates système
│   ├── 07_Agents/                   Configurations agents
│   └── 08_Hooks/                    Pre/Post execution hooks
│
├── 10_INBOX/                        ← Entrées de session
│   ├── Daily_Logs/                  Logs quotidiens (YYYY-MM-DD.md)
│   ├── Raw_Captures/                Captures brutes non traitées
│   └── Session_Reviews/             Bilans de session
│
├── 20_ENTITIES/                     ← Entités connues
│   ├── Concepts/
│   ├── Projects/
│   └── Technologies/
│
├── 30_RELATIONS/                    ← Graphe de connaissance, MOC
├── 40_ERRORS/                       ← Journal d'erreurs et patterns
│   └── [MangaTracker/]              ← À CRÉER — erreurs pipeline ETL
├── 50_METRICS/                      ← Performance, qualité, stats
├── 60_ARCHIVE/                      ← Notes archivées
│
├── 70_ROADMAP/                      ← Feuilles de route par projet
│   ├── INDEX.md
│   ├── TricorderKit.md
│   ├── MangaTracker.md              Statut: pause (bloqué RISK-002)
│   └── Japan-Alliance.md
│
├── Projects/                        ← Projets actifs
│   ├── TricorderKit_Phase5_SecurityAudit.md
│   ├── TricorderKit_v0.9.1_PublicReady.md
│   └── MangaTracker/                ← À CRÉER (voir §3.1)
│       ├── Scraping_Pipelines/
│       ├── Quality_Rules/
│       └── Cache_Temps_Reel/
│
└── Working/                         ← Espace de travail temporaire
```

### 2.2 Japan-Alliance — `<vault-path>/Japan-Alliance`

```
Japan_Alliance/                      5 277 notes · 687 dossiers
│
├── 00_System/                       ← Gouvernance du vault
│   ├── 00_A_Lire_Avant_Agir/        Règles à lire avant d'agir — PRIORITÉ MAX
│   ├── 01_Organigramme/
│   ├── 02_Regles_ID/                Convention d'ID des fiches (TP/SY/etc.)
│   ├── 03_Manifestes_Migration/
│   │   └── TRICORDERKIT_RAPPORTS/   Rapports Cowork 7h30 et 18h
│   ├── 04_MangaTracker_System/      Config intégration Cowork↔TricorderKit
│   └── 05_Routing_Sources/          Routage par source de donnée
│
├── 01_Mangas & Light Novels/        ← BDD mangas (production)
├── 02_Anime & Production/           ← BDD animés et studios
├── 03_Personnes_Culture/            ← Mangakas, seiyū, réalisateurs
├── 04_Jeux_Video_Arcade/            ← BDD jeux vidéo japonais
├── 05_Industrie_Sources/            ← Éditeurs, magazines, sources
├── 06_Lieux_Tourisme/               ← Lieux emblématiques
├── 07_Produits_Derives/             ← Goodies, figurines, merchandising
├── 08_Site_JapanAlliance/           ← Architecture site web
├── 09_Evenements/                   ← Events, conventions, sorties
│
├── 90_Templates/                    Templates (⚠️ voir anomalie A1)
├── 94_IA_Automatisation/            ← Système IA (ne pas réorganiser)
├── 97_A_Trier/                      ⚠️ Zone non-triée
├── 98_Migration_Reports/
├── 99_Migration_Backups/
│
└── _Inbox_Global/                   ← Sas de validation MangaTracker
    ├── 01_Mangas_LN/
    ├── 02_Anime/
    ├── 03_Personnes/
    ├── 04_JV_Arcade/
    ├── 05_Industrie/
    ├── 07_Produits/
    └── 99_Non_classe/
```

---

## 3. Éléments à créer (delta minimal)

### 3.1 claude-vault : Zone opérationnelle MangaTracker

**Chemin** : `Projects/MangaTracker/`

```
Projects/MangaTracker/
├── README.md               Rôle, périmètre, lien vers 70_ROADMAP/MangaTracker.md
├── Scraping_Pipelines/     Configs scrapers : cibles, sélecteurs CSS/JSON, fréquences
├── Quality_Rules/          Règles de validation et correction des fiches avant injection
└── Cache_Temps_Reel/       Fichiers temporaires générés pendant le scraping (auto-purgés)
```

### 3.2 Japan-Alliance : Structure _Inbox_Global/

| Sous-dossier Inbox | Cible de production après validation |
|--------------------|--------------------------------------|
| `01_Mangas_LN/` | `01_Mangas & Light Novels/01_Fiches/` |
| `02_Anime/` | `02_Anime & Production/` |
| `03_Personnes/` | `03_Personnes_Culture/` |
| `04_JV_Arcade/` | `04_Jeux_Video_Arcade/` |
| `05_Industrie/` | `05_Industrie_Sources/` |
| `07_Produits/` | `07_Produits_Derives/` |
| `99_Non_classe/` | À trier manuellement |

---

## 4. Protocole d'intégration MangaTracker → Japan-Alliance

### 4.1 Flux de données complet

```
MangaTracker ETL (Repo privé)
  1. Scrape source (MangaUpdates / BookWalker / Oricon / Comic Natalie)
  2. Normalise via Quality_Rules
  3. Dépose dans _Inbox_Global/{type}/ (Japan-Alliance)
       ↓
  4. Workflow Temporal (tk:eval-inbox) analyse le sas
     → Vérifie format + doublons (via Qdrant ou grep vault)
     → Valide les 6 points de contrôle (voir §4.2)
       ↓
  5a. Fiche valide → déplace vers BDD de production
  5b. Fiche rejetée → log dans 40_ERRORS/MangaTracker/ (claude-vault)
```

> **Règle absolue** : MangaTracker ne doit JAMAIS écrire directement dans les
> dossiers de production. Toujours passer par l'Inbox.

### 4.2 6 points de contrôle

1. **Intégrité** : champs `title`, `author`, `publisher` présents et non vides
2. **Cohérence** : mangaka/studio lié existe dans le vault (grep ou Qdrant)
3. **Doublons** : même titre romanisé différemment — vérifier ID unique
4. **Sources** : URL officielle présente et non cassée
5. **Tags/genres** : cohérence avec `17_Taxonomies_Tags/`
6. **Complétude** : score ≥ 80% avant validation vers production

### 4.3 Matrice de permissions

| Dossier | Cowork | TricorderKit CLI | MangaTracker ETL |
|---------|--------|-----------------|-----------------|
| `_Inbox_Global/{type}/` | ❌ | ✅ lecture | ✅ écriture |
| `01_Mangas & LN/`, `02_Anime/`… | ✅ lecture | ✅ lecture+écriture | ❌ direct interdit |
| `94_IA_Automatisation/01_MangaTracker/` | ✅ lecture | ✅ lecture+écriture | ❌ interdit |
| `90_Templates/` | ❌ interdit | ❌ interdit | ❌ interdit |
| `40_ERRORS/MangaTracker/` (claude-vault) | ✅ lecture | ✅ lecture+écriture | ✅ écriture |

---

## 5. Anomalies documentées (ne pas modifier sans audit dédié)

| # | Anomalie | Localisation | Impact | Action recommandée |
|---|----------|-------------|--------|-------------------|
| A1 | Double `90_` | `90_Taxonomies/` + `90_Templates/` dans JA | Confusion d'indexation MCP | Audit dédié — renommer `90_Templates/` → `95_Templates/` |
| A2 | Double `91_` | `91_System_Manifestes/` + `91_Workflow_QA/` dans JA | Idem | Audit dédié — renommer `91_Workflow_QA/` → `96_Workflow_QA/` |
| A3 | Dossier artefact | `Japan-Alliance/` à l'intérieur du vault JA | Faible | Vérifier contenu, supprimer si vide |
| A4 | Zone non-triée | `97_A_Trier/` dans JA | Pollution BDD progressive | Programmer session de tri |

---

## 6. Multi-project support — État et roadmap

### 6.1 Ce qui est déjà résolu

| Besoin | Solution en place |
|--------|-------------------|
| Multi-vault routing | Deux MCPs Obsidian distincts : `obsidian-claude-vault` + `obsidian-japan-alliance` |
| Isolation des données | Chaque vault = namespace MCP distinct, zéro contamination croisée |
| Annonce projet actif au boot | HOT_CACHE.md → BOOT_SUMMARY.md |
| Suivi roadmap par projet | `70_ROADMAP/{projet}.md` dans claude-vault |

### 6.2 Ce qui reste à implémenter

1. **Registre de projets** dans `configs/shared/defaults.yaml`
2. **Commandes CLI** : `tk project init/switch/list`
3. **Mise à jour `/tk:boot`** avec contexte projet actif
4. **Tag `project_name`** dans toutes les traces Langfuse
5. **`project_id` comme namespace** dans Qdrant + Supabase RLS
6. **`tk doctor` multi-projet**

---

## 7. Séquence de boot adaptée (lazy-load)

```text
TIER 1 — Toujours (~500 tokens)
  claude-vault: 00_SYSTEM/05_Hot_Cache/HOT_CACHE.md
  claude-vault: 70_ROADMAP/{projet_actif}.md

TIER 2 — Si TIER 1 insuffisant (~2 500 tokens)
  claude-vault: tasks/lessons.md
  claude-vault: .planning/STATE.md (items pending/in_progress uniquement)
  JA vault:     00_System/00_A_Lire_Avant_Agir/ (README.md)

TIER 3 — À la demande uniquement (~10 000 tokens)
  claude-vault: .planning/RISKS.md, docs/00→06
  JA vault:     94_IA_Automatisation/01_MangaTracker/
```

---

## 8. Niveaux de fiabilité des données

| Niveau | Condition | Marquage frontmatter |
|--------|-----------|---------------------|
| ✅ Confirmé | Source officielle ou 2 sources concordantes | `status: confirmé` |
| 🟡 Probable | Source secondaire fiable, en attente confirmation | `status: probable` |
| 🟠 À vérifier | Wiki, forum, source communautaire | `status: à_vérifier` |
| 🔴 Incomplet | Donnée manquante ou contradictoire | `status: incomplet` |

---

*Version 1.0 — 2026-05-24 — Aligné sur vaults réels · Remplace Vault et arborescence.md + Multi-linked-project.md + a faire.md*
