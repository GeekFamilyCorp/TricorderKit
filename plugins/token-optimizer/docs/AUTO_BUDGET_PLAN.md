# Plan de conception — Système d'analyse budget & auto-optimisation des tokens

> Statut : **proposition à valider** (2026-06-03). Auteur : Claude (Cowork) pour GeekFamilyCorp.
> Décisions cadres retenues : plan d'abord · offload local (Hermes/Ollama) + Google Antigravity + sous-agent Haiku · autonomie « auto-applique le sûr, propose le reste » · données via hook PostToolUse + estimation `classify.py`.

---

## 0. Objectif & principes

Construire, au-dessus du plugin `token-optimizer`, une boucle fermée qui :

1. **mesure** la consommation de tokens (et son coût relatif),
2. **analyse** où part le budget et où sont les gaspillages,
3. **agit** automatiquement sur les optimisations à faible risque, et **propose** le reste,
4. **délègue** (offload) les tâches qui n'ont pas besoin de Claude vers une cible moins chère : modèle **local** (Hermes via Ollama), **Google Antigravity** (Gemini), ou **sous-agent Haiku**.

Principes directeurs :

- **Mesurer avant d'optimiser** : aucune reco sans donnée. La métrique cible est *tokens-par-tâche-réussie*, pas *tokens-par-requête*.
- **Sûr par défaut** : l'auto-application est strictement bornée à une liste blanche d'actions réversibles et journalisées ; tout le reste passe en proposition.
- **Confidentialité d'abord** : aucune tâche sensible (legal/medical/secret/auth/paiement) n'est offloadée vers une cible externe sans tag explicite.
- **Réversibilité** : chaque action auto-appliquée est journalisée avec un rollback en un geste.

---

## 1. Vue d'ensemble (boucle)

```
                ┌─────────────────────────────────────────────┐
                │            token-optimizer (existant)        │
                │  model-router · task-classifier · caveman    │
                │  budget-tracker · context/cli-compress       │
                └───────────────┬─────────────────────────────┘
                                │ logue la conso (hook + estimation)
                                ▼
   ┌────────────────┐    ┌──────────────────┐    ┌────────────────────┐
   │ 1. CAPTURE      │──▶ │ 2. ANALYSE        │──▶ │ 3. AUTO-AMÉLIORATION │
   │ budget.json     │    │ budget-analyzer   │    │ optimizer (safe-auto │
   │ + history/      │    │ tendances/waste   │    │  / propose)          │
   └────────────────┘    └──────────────────┘    └─────────┬──────────┘
                                │                            │
                                ▼                            ▼
                         ┌──────────────┐          ┌───────────────────┐
                         │ 4. OFFLOAD    │◀────────│ règles de routage  │
                         │ ROUTER        │          │ (coût/capacité/    │
                         │ local/AG/Haiku│          │  privacy/latence)  │
                         └──────┬────────┘          └───────────────────┘
              ┌────────────────┼─────────────────┐
              ▼                ▼                 ▼
        Hermes (Ollama)   Antigravity (Gemini)  Haiku 4.5
        T1 vrac/privé     dev lourd/parallèle   T1 nécessitant Claude
```

---

## 2. Couche données — capture de la consommation

**Source retenue** : hook `PostToolUse(Task)` (déjà en place → `budget.py log-from-task`) + **estimation** via `classify.py` (ratio ~0,75 mot/token). 

**Limite assumée et explicite** : Cowork n'expose pas toujours la conso exacte par message. On travaille donc en **estimation calibrée**, pas en facturation exacte. Deux garde-fous :

- un **facteur de calibration** (`calibration_factor`) ajustable si tu compares de temps en temps avec l'usage réel de la console Anthropic (passage possible en « Export d'usage API » plus tard sans rien casser) ;
- on logue séparément `estimated: true` pour ne jamais présenter une estimation comme un chiffre exact.

**Évolution du schéma `~/.token-optimizer/budget.json`** (rétrocompatible) :

```json
{
  "version": "1.1",
  "month": "2026-06",
  "config": { "...": "inchangé (total, allocation, alerts)",
              "calibration_factor": 1.0 },
  "consumption": { "haiku": {...}, "sonnet": {...}, "opus": {...} },
  "offload": {
    "local":       { "tasks": 0, "tokens_saved_equiv": 0 },
    "antigravity": { "tasks": 0, "tokens_saved_equiv": 0 },
    "haiku_reroute": { "tasks": 0, "tokens_saved_equiv": 0 }
  },
  "events": [ { "ts": "...", "type": "task", "tier": "T2",
                "model": "sonnet", "in": 2000, "out": 1000,
                "estimated": true, "offloaded_to": null } ]
}
```

`events[]` (anneau borné, ex. 2000 derniers) alimente l'analyse de tendance et la détection de gaspillage. Archivage mensuel inchangé (`history/YYYY-MM.json`).

---

## 3. Moteur d'analyse — `scripts/budget_analyzer.py` (+ skill `budget-analyzer`)

Nouveau script CLI + skill déclenché par « analyse mon budget », « où partent mes tokens », « rapport d'optimisation ».

Sorties :

- **Répartition** par modèle / par tier / par type de tâche (en équivalents-Haiku).
- **Tendance** : conso/jour, projection fin de mois vs budget, date estimée d'atteinte des seuils 50/80/95 %.
- **Détecteur de gaspillage** (heuristiques) :
  - tâches classées T3 (Opus) qui auraient pu être T2/T1 (score proche de la borne) ;
  - réponses longues sans caveman sur des T1/T2 ;
  - tâches répétitives (mêmes signatures) candidates à l'offload local ;
  - sessions à contexte long jamais compressées.
- **Opportunités chiffrées** : « X tâches T1 répétitives/mois → offload local = ~Y équiv-Haiku économisés ».
- Mode `--json` pour alimenter l'optimizer et un futur dashboard.

---

## 4. Boucle d'auto-amélioration — `scripts/optimizer.py` (+ skill `auto-optimize`)

Autonomie **« auto-applique le sûr, propose le reste »**. Deux listes strictes :

**✅ Liste blanche — AUTO-APPLIQUÉ (réversible, journalisé) :**

- ajustement des **seuils de score** T1/T2/T3 dans des bornes prédéfinies (± marges) ;
- (dé)activation du **mode caveman** par tier selon le budget restant ;
- bascule de la **politique d'escalade** budget (downgrade_one_tier / force_haiku) déjà prévue ;
- activation du **reroute Haiku** agressif quand budget > 80 % ;
- réglage du `calibration_factor`.

**🟡 Liste — PROPOSÉ (validation requise) :**

- création/modification de **skills** ou d'agents ;
- nouvelles **règles d'offload** vers local/Antigravity ;
- changement de l'**allocation** budget ou du total ;
- toute action touchant un domaine sensible.

**Traçabilité** : chaque action auto-appliquée écrit une entrée dans `~/.token-optimizer/optimizer-log.jsonl` (avant/après + raison) et un **point de rollback**. Commande `optimizer.py rollback --last`. Un récap des actions auto est inclus dans le rapport quotidien.

---

## 5. Routeur d'offload — `scripts/offload_router.py` (+ skill `offload-router`)

Décide, pour une tâche donnée, **où** elle s'exécute. Cibles et mécanismes :

| Cible | Quand | Mécanisme d'appel | Statut techniq. |
|-------|-------|-------------------|-----------------|
| **Hermes (local, Ollama)** | T1 en vrac, répétitif, **données privées**, hors-ligne OK, qualité « bonne suffit » | API locale OpenAI-compatible `http://localhost:11434/v1` | À brancher (Ollama installé requis) |
| **Google Antigravity (Gemini)** | dev lourd, multi-fichiers, tâches **parallélisables**, génération/test de code en arrière-plan | **CLI** Antigravity (TUI/headless) ou **SDK Python** ; artefacts (plans, captures) récupérés | CLI/SDK dispo (public preview) |
| **Sous-agent Haiku 4.5** | T1/T2 qui nécessitent **Claude** (contexte, ton, outils Cowork) mais pas Opus | natif `Task(subagent_type=haiku-executor)` | déjà opérationnel |
| **Claude (Sonnet/Opus)** | T2/T3 nécessitant qualité/raisonnement, ou sensible | exécution normale | défaut |

**Détails d'intégration importants :**

- **Ollama/Hermes** : fixer `num_ctx` côté modèle (Ollama plafonne à 4096 par défaut et ignore le `context_length` client → troncature silencieuse sinon). On crée un `Modelfile` dédié (`hermes3-agent`) avec `num_ctx` adapté. Modèle conseillé pour démarrer : `hermes3:8b` quantifié (rapide, suffisant T1).
- **Antigravity** : on encapsule l'appel CLI dans un wrapper qui passe un **« handoff packet »** (objectif, fichiers concernés, critères de succès) et récupère les **artefacts** pour vérification avant intégration.
- **Handoff packet** (format commun local/AG) : `{ goal, context_files[], constraints, success_criteria, return_format }`. Permet une vérification systématique du résultat avant de l'accepter.

**Vérification post-offload** : tout résultat externe (local ou Antigravity) repasse par un contrôle Claude léger (lint/tests/relecture ciblée) avant d'être considéré comme livré — l'offload réduit le coût, pas la qualité.

---

## 6. Matrice de décision d'offload (résumé)

Score sur 4 axes → cible :

- **Coût** (tokens estimés) : élevé → favoriser local/AG.
- **Capacité requise** : raisonnement/architecture → Claude ; dev volumineux → AG ; transformation simple → local.
- **Confidentialité** : sensible → **jamais** d'externe non taggé (local OK si machine de confiance, sinon Claude).
- **Latence/parallélisme** : besoin parallèle/asynchrone → AG (sous-agents) ; immédiat court → Haiku/local.

La règle conservatrice gagne (comme pour le budget). En cas de doute → Claude.

---

## 7. Garde-fous & sécurité

- **Filtre confidentialité** avant tout offload externe : patterns sensibles (réutilise `SENSITIVE_PATTERNS` de `classify.py`) → blocage offload externe, exécution Claude.
- **Aucun secret** (clés, tokens, .env) transmis à une cible externe ; détection + masquage.
- **Auto-apply borné** : uniquement la liste blanche §4, toujours réversible, jamais sur du sensible.
- **Vérification** systématique des sorties offloadées.
- **Kill switch** : `TKO_NO_OFFLOAD=1` et `optimizer.py disable` pour tout figer.

---

## 8. Automatisation planifiée

- **Quotidien (matin)** : rapport budget + actions auto-appliquées de la veille + alertes seuils (on réutilise/raffine `scheduled-tasks/daily-budget-morning-check`).
- **Hebdomadaire** : analyse de gaspillage + propositions d'optimisation (skills/règles) à valider.
- **Mensuel (1er)** : archivage + bilan d'économies (tokens & équivalent coût) + recalibration.

---

## 9. Roadmap par lots (incrémental, chaque lot livrable & testé)

| Lot | Contenu | Dépendances | Valeur |
|-----|---------|-------------|--------|
| **L1 — Données & analyse** | schéma budget v1.1 + `events[]`, `budget_analyzer.py` + skill, rapport `--json` | rien (budget.py déjà là) | visibilité immédiate |
| **L2 — Auto-amélioration sûre** | `optimizer.py` (liste blanche + log + rollback), intégration au rapport quotidien | L1 | gains auto sans risque |
| **L3 — Offload Haiku agressif** | règles de reroute Haiku dans model-router, comptage des économies | L1 | gain rapide, 0 dépendance externe |
| **L4 — Offload local (Hermes/Ollama)** | `Modelfile` hermes3-agent, wrapper client, filtre confidentialité, vérif | Ollama installé | gros gain sur T1 vrac/privé |
| **L5 — Offload Antigravity** | wrapper CLI/SDK, handoff packet, récupération d'artefacts, vérif | Antigravity installé | dev lourd déporté |
| **L6 — Dashboard & boucle complète** | dashboard HTML (conso, économies, offload), automatisations hebdo/mensuelle | L1-L5 | pilotage |

Proposition : démarrer par **L1 → L2 → L3** (valeur immédiate, zéro dépendance externe), puis L4/L5 une fois Ollama et Antigravity confirmés installés.

---

## 10. Risques & limites connues

- **Estimation ≠ facturation exacte** : Cowork n'expose pas la conso réelle ; chiffres approximatifs (calibration possible). À valider avant de prendre des décisions financières dessus.
- **Bug plateforme `${CLAUDE_PLUGIN_ROOT}`** non expansé dans les hooks Cowork (déjà documenté) : tant qu'il persiste, l'instance `rpm/` garde des chemins absolus.
- **Qualité du modèle local** : Hermes 8B convient aux T1 ; ne pas lui confier de T2/T3. Plafond de qualité à respecter via le filtre de capacité.
- **Antigravity en preview** : surface CLI/SDK susceptible d'évoluer ; on isole l'intégration derrière un wrapper pour amortir les changements.
- **Dépendances externes** requièrent installation/maj côté machine (Ollama, Antigravity) — hors périmètre du plugin seul.

---

## 11. Décisions à valider avant construction

1. **Ordre des lots** : OK pour L1 → L2 → L3 d'abord (puis L4/L5) ?
2. **Modèle local** : Hermes 3 8B pour démarrer, ou autre (70B si GPU costaud) ? Ollama est-il déjà installé ?
3. **Antigravity** : CLI ou SDK Python ? déjà installé et authentifié ?
4. **Bornes d'auto-apply** : valider les marges d'ajustement des seuils (ex. ±5 points) avant d'autoriser l'auto-application.
5. **Cible de budget mensuel** réelle (le défaut est 20 M équiv-Haiku) pour calibrer les alertes.
