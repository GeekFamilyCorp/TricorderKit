# tk-orchestrator — Skill Orchestrateur Principal
> Version : 0.2.0 — 15/05/2026  
> Ancrage : TricorderKit v0.8 — Phase 4 active  
> Statut : Spec validée, implémentation à démarrer

---

## 🎯 Rôle & déclencheurs

L'orchestrateur est le **point d'entrée unique** de toutes les commandes `/tk:*`. Il ne remplace pas le MainBrain v1.5 — il s'y insère comme **Étape 0** (avant la Skill Selector, la CLI Selector et les autres sélecteurs existants).

### Déclencheurs
- **Priorité absolue** sur toute commande `/tk:*`
- Mots-clés naturels : `orchestrate`, `route`, `chain`, `sequence`, `pipeline`, `budget`, `token-optimize`
- Commandes CLI : `/tk:orchestrate`, `/tk:route`, `/tk:chain`, `/tk:budget-check`

### Ce qu'il N'EST PAS
- ❌ Un remplacement du MainBrain v1.5
- ❌ Un doublon de `tk-boot` (il consomme les données déjà chargées par boot, il ne relit pas les mêmes fichiers)
- ❌ Un plugin `skill-registry` (ce plugin est prévu dans STATE.md comme priorité A — l'orchestrateur doit le consommer quand il sera disponible)

---

## ⚠️ Préconditions — ce qui existe déjà (v0.8)

| Ressource | Chemin | Statut |
|---|---|---|
| Contrat output JSON | `core/contracts/skill_output.schema.json` | ✅ v1.0.0 actif |
| Registry CLIs | `plugins/cli-forge/registry.yml` | ✅ Schéma réel défini |
| MainBrain v1.5 | `core/mainbrain/MainBrain_v1.5.md` | ✅ Actif |
| Skill tk-boot | `skills/tk-boot/SKILL.md` | ✅ Opérationnel |
| Cache SQLite github-goat | `.cache/github-goat.db` | ✅ Existant |
| Cache SQLite source-watch | `.cache/source-watch-goat.db` | ✅ Existant |
| Hook token_budget_guard | `.claude/hooks/token_budget_guard.py` | ✅ Actif |
| STATE.md | `.planning/STATE.md` | ✅ v0.8, Phase 4 active |
| DECISIONS.md | `.planning/DECISIONS.md` | ✅ DEC-001 à DEC-007 |

> **Note critique** : `source-watch-goat` est `in_progress` dans le registry (pas encore `dry_run_validated`). L'orchestrateur NE DOIT PAS l'utiliser en prod jusqu'à validation.

---

## 🔄 Intégration dans MainBrain v1.5

```diff
# core/mainbrain/MainBrain_v1.5.md — Algorithme de décision

+ ÉTAPE 0 — Orchestrator Check (NOUVEAU — PRIORITÉ ABSOLUE)
+   → Si la commande commence par /tk: ou correspond à un pattern orchestrable
+   → Charger tk-orchestrator EN PREMIER
+   → Lire les données déjà en cache (tk-boot doit avoir été exécuté)
+   → Router vers Étape 1–7 via l'orchestrateur
+   → Si l'orchestrateur retourne "no_match" → continuer normalement Étape 1

  ÉTAPE 1 — Intent Router         (inchangé)
  ÉTAPE 2a — Skill Selector       (inchangé, appelé PAR l'orchestrateur)
  ÉTAPE 2b — CLI Selector         (inchangé, appelé PAR l'orchestrateur)
  ...
```

---

## 🖥️ Double Interface

L'orchestrateur expose **deux interfaces** qui partagent la même logique métier :

### Interface A — CLI Python (`orchestrator.py`)
- Invoquée par Claude via `Bash` ou `subprocess`
- Entrée : `stdin` ou arguments CLI
- Sortie : JSON sur `stdout`
- Isolation : niveau subprocess (vrai isolement mémoire)
- Usage : workflows automatisés, tests, chaînage script

### Interface B — Skill Cowork (`SKILL.md`)
- Invoquée par Claude directement en session naturelle
- Entrée : langage naturel ou commande `/tk:*`
- Sortie : rapport Markdown + JSON interne
- Isolation : contextuelle (Claude ne charge que les fichiers listés dans les préconditions)
- Usage : sessions interactives, debug, exploration

> **Règle d'arbitrage** : Si une CLI Python peut exécuter la tâche → utiliser l'Interface A. L'Interface B est pour les cas où la CLI n'existe pas encore ou pour les interactions nécessitant du raisonnement.

---

## ⚙️ Phases d'exécution

### Phase 0 — Vérification du cache tk-boot
```text
Si tk-boot a déjà été exécuté cette session :
  → Lire le résultat en cache (.cache/orchestrator.db, table session_context)
  → NE PAS relire STATE.md, TASKS.md, DECISIONS.md (déjà chargés)
Sinon :
  → Logger un warning : "tk-boot non exécuté — données de session absentes"
  → Continuer avec les données disponibles
```

### Phase 1 — Intent Parsing & Routing
```text
1. Analyser la commande (pattern matching multi-domaine, voir ci-dessous)
2. Classifier : query | action | workflow | research | audit
3. Identifier domaine(s) avec scoring : manga | github | vault | system | anime | ln
4. En cas d'ambiguïté multi-domaine → utiliser le score de confiance (≥ 0.6 requis)
5. Consulter registry.yml pour les CLIs disponibles (status: dry_run_validated | prod_ready uniquement)
```

**Scoring multi-domaine** — si plusieurs domaines dépassent 0.5 de confiance, appliquer la règle de priorité :
1. `system` (toujours prioritaire si détecté)
2. `vault` (opérations Obsidian)
3. `github` (opérations code/repos)
4. `manga` / `anime` / `ln` (domaines media configurables)

### Phase 2 — Token Budget Allocation

```python
# Heuristique : 1 token ≈ 4 caractères (UTF-8)
def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)

def allocate_budget(intent_type: str, input_text: str) -> dict:
    base = 200  # orchestration elle-même
    action_budgets = {
        "query": 300,
        "action": 500,
        "workflow": 1000,
        "research": 1500,
        "audit": 800
    }
    input_tokens = estimate_tokens(input_text)
    allocated = base + action_budgets.get(intent_type, 300)
    safety_buffer = int(allocated * 0.20)  # 20% buffer sécurité
    return {
        "allocated": allocated,
        "safety_buffer": safety_buffer,
        "effective_budget": allocated - safety_buffer,
        "input_estimated": input_tokens
    }
```

### Phase 3 — Tool Selection (CLI-first)

**Priorité stricte** :
1. **CLI enregistrée** dans `registry.yml` avec `status: dry_run_validated` ou `prod_ready` ET `safe_for_agents: true` → UTILISER
2. **Skill** dans `skills/` avec `SKILL.md` valide → CHARGER
3. **Workflow** dans `plugins/workflow-engine/workflows/` → DÉCLENCHER
4. **Aucun** → retourner `"no_match"` + fallback LLM raisonné

> ⚠️ `source-watch-goat` est actuellement `in_progress` — NE PAS sélectionner jusqu'à passage en `dry_run_validated`.

### Phase 4 — Exécution Isolée

```text
┌─────────────────────────────────────────────┐
│ 1. Ouvrir contexte tool (subprocess ou scope) │
│ 2. Vérifier budget avant exécution           │
│ 3. Exécuter avec budget alloué               │
│ 4. Capturer output JSON                      │
│ 5. Valider contre skill_output.schema.json   │
│ 6. Fermer contexte IMMÉDIATEMENT             │
│ 7. Libérer références (gc.collect() si CLI)  │
└─────────────────────────────────────────────┘
```

### Phase 5 — Enchâînement avec politique de défaillance

**Politique : Abort + rapport partiel**

```text
Pour chaque step dans la chaîne (max 5 steps) :
  Si step.status == "success" :
    → Continuer au step suivant
    → Passer output.data comme input du step suivant
  Si step.status == "error" :
    → ARRÊTER immédiatement (abort)
    → Marquer les steps suivants comme "skipped"
    → Retourner rapport partiel (steps réussis + step échoué + raison)
    → NE PAS masquer l'erreur
  Si steps > 5 :
    → Forcer l'arrêt (protection boucle infinie)
    → Status : "chain_limit_exceeded"
```

### Phase 6 — Logging & Reporting

```text
Si décision architecturale → logger dans .planning/DECISIONS.md (DEC-008+)
Si état modifié → mettre à jour .planning/STATE.md
Produire output JSON conforme skill_output.schema.json v1.0.0
```

---

## 📤 Output Contract (conforme skill_output.schema.json v1.0.0)

```json
{
  "status": "success|partial|error|dry_run",
  "skill_name": "tk-orchestrator",
  "skill_version": "0.2.0",
  "timestamp": "2026-05-15T10:00:00Z",
  "duration_ms": 342,
  "tokens_used": {
    "input": 120,
    "output": 222,
    "total": 342
  },
  "output": {
    "summary": "Routed 'liste repos Claude' → github-goat:list-repos — 2 steps, 342 tokens",
    "data": {
      "intent": {
        "type": "query",
        "domain": "github",
        "confidence": 0.9,
        "entities": ["claude"]
      },
      "routing": {
        "selected_tool": "github-goat",
        "tool_type": "cli",
        "command": "list-repos",
        "args": {"query": "claude", "limit": 10},
        "registry_status": "dry_run_validated"
      },
      "token_budget": {
        "allocated": 500,
        "effective": 400,
        "used": 342,
        "remaining": 58,
        "safety_buffer": 100
      },
      "execution_chain": [
        {"step": 1, "tool": "github-goat", "status": "success", "tokens": 120},
        {"step": 2, "tool": "obsidian-mcp", "status": "success", "tokens": 222}
      ],
      "chain_policy": "abort_on_failure",
      "chain_limit": 5
    },
    "decisions_logged": ["DEC-008"],
    "next_steps": ["Vérifier résultats dans vault", "Lancer source-watch-goat quand prod_ready"]
  },
  "dry_run_report": null
}
```

**En cas d'erreur en chaîne** :
```json
{
  "status": "partial",
  "output": {
    "summary": "Chain aborted at step 2/3 — obsidian-mcp write failed (MEDIUM risk unconfirmed)",
    "data": {
      "execution_chain": [
        {"step": 1, "tool": "github-goat", "status": "success", "tokens": 120},
        {"step": 2, "tool": "obsidian-mcp", "status": "error", "error": "...", "tokens": 0},
        {"step": 3, "tool": "vault-audit-goat", "status": "skipped", "tokens": 0}
      ]
    }
  },
  "error": {
    "code": "CHAIN_ABORTED_STEP_2",
    "message": "obsidian-mcp : fichier cible verrouillé",
    "recoverable": true,
    "rollback_available": false
  }
}
```

---

## 🛡️ Risk Guard intégré

| Niveau | Critères | Comportement |
|---|---|---|
| LOW | Lecture seule, CLI `prod_ready` ou `dry_run_validated` | Exécuter directement |
| MEDIUM | Écriture locale, appel API read, CLI `in_progress` | Confirmation courte obligatoire |
| HIGH | Écriture Obsidian, push GitHub, appel API write | Plan détaillé + confirmation explicite |
| CRITICAL | Suppression, shell destructif, `status: pending` | Refus systématique + escalade |

> Les CLIs avec `status: pending` ou absentes du registry sont automatiquement classées **CRITICAL**.

---

## 🧩 Intégrations (réalité v0.8)

| Tool | Type | Status registry | Utilisable |
|---|---|---|---|
| `github-goat` | CLI | `dry_run_validated` | ✅ Oui |
| `source-watch-goat` | CLI | `in_progress` | ❌ Non (en attente validation) |
| `obsidian-goat` | CLI | `planned` | ❌ Non |
| `vault-audit-goat` | CLI | `planned` | ❌ Non |
| Obsidian MCP | MCP | — | ✅ Via mcp.json |
| `tk-boot` skill | Skill | — | ✅ Consommer son cache |
| workflow-engine | Workflow | scaffold OK | ⚠️ Temporal non déployé |

---

## 🗂️ Structure de fichiers à créer

```
TricorderKit_Project/skills/tk-orchestrator/
├── SKILL.md                  ← Ce fichier
├── orchestrator.py           ← CLI Python (Interface A)
├── manifest.yml              ← Compatible cli-forge
├── router/
│   ├── intent_classifier.py  ← Scoring multi-domaine
│   └── skill_registry.py     ← Lecture registry.yml réel
├── budget/
│   ├── token_tracker.py      ← Heuristique 4 chars/token
│   └── session_cache.py      ← Lecture cache tk-boot (SQLite)
├── context/
│   ├── context_manager.py    ← Isolation subprocess/scope
│   └── chain_executor.py     ← Abort-on-failure policy
└── tests/
    ├── test_routing.py
    ├── test_token_budget.py
    ├── test_chain_abort.py   ← NOUVEAU : test politique défaillance
    └── test_schema_compliance.py  ← NOUVEAU : validation output schema
```

---

## 🚀 Commandes CLI

```bash
# Depuis TricorderKit_Project/
python skills/tk-orchestrator/orchestrator.py --dry-run route "liste les repos Claude"
python skills/tk-orchestrator/orchestrator.py budget-check --intent research --input "$(cat query.txt)"
python skills/tk-orchestrator/orchestrator.py chain --steps '[
  {"tool":"github-goat","cmd":"list-repos","args":{"query":"claude"}},
  {"tool":"obsidian-mcp","cmd":"write-note","args":{"title":"Résultats"}}
]'
python skills/tk-orchestrator/orchestrator.py route --validate-schema "surveille One Piece"
```

---

## 📋 Manifest `manifest.yml` (compatible cli-forge)

```yaml
name: tk-orchestrator
version: "0.2.0"
description: "Meta-skill orchestrateur — routing multi-domaine + abort-on-failure + double interface CLI/Cowork"
service: tricorderkit-core
language: python
entrypoint: orchestrator.py
token_budget: 200
cache:
  backend: sqlite
  ttl_seconds: 300
  path: .cache/orchestrator.db
  session_context_table: session_context  # Partage avec tk-boot
dry_run: true
output_format: json
output_schema: core/contracts/skill_output.schema.json
safe_commands:
  - route
  - chain
  - budget-check
  - dry-run
priority: HIGHEST
orchestration:
  cli_first: true
  registry_path: plugins/cli-forge/registry.yml
  min_cli_status: dry_run_validated  # N'utiliser que des CLIs validées
  context_isolation: true
  token_optimization: heuristic_4chars_per_token
  chain_max_steps: 5
  chain_policy: abort_on_failure
  auto_logging: true
  boot_cache_aware: true  # Lire le cache tk-boot si disponible
```

---

## 🧪 Critères de succès & Tests

```bash
# 1. Validation manifest contre schéma cli-forge
python plugins/cli-forge/scripts/validate_cli_manifest.py --file skills/tk-orchestrator/manifest.yml

# 2. Dry-run routing
python skills/tk-orchestrator/orchestrator.py --dry-run route "liste les repos Claude"

# 3. Validation output schema
python skills/tk-orchestrator/orchestrator.py route "teste le schéma" | python -c "
import json, sys, jsonschema
output = json.load(sys.stdin)
schema = json.load(open('core/contracts/skill_output.schema.json'))
jsonschema.validate(output, schema)
print('✅ Schema OK')
"

# 4. Test abort-on-failure
pytest skills/tk-orchestrator/tests/test_chain_abort.py -v

# 5. Test multi-domaine ambiguïté
python skills/tk-orchestrator/orchestrator.py route "surveille les sorties manga sur le repo BookWalker"
# Attendu : domain=manga (score 0.8) > github (score 0.5) → sélection manga

# 6. Suite complète
pytest skills/tk-orchestrator/tests/ -v
```

**Critères de validation** :
- Output JSON conforme à `skill_output.schema.json` v1.0.0 (champ `skill_name` pas `skill`, `tokens_used.input/output/total`)
- Chain abort retourne `status: partial` avec `execution_chain` complet (steps skipped inclus)
- Aucune CLI avec `status: in_progress` ou `pending` n'est sélectionnée sans passer MEDIUM risk
- Cache tk-boot lu en priorité si disponible (0 relecture de STATE.md/DECISIONS.md)
- Budget token : jamais > `effective_budget` (= allocated - safety_buffer 20%)

---

## ⚠️ Points de vigilance (mis à jour)

| Risque | Impact | Mitigation |
|---|---|---|
| Schema mismatch v1.0.0 | Output rejeté par eval-lab | Valider avec jsonschema avant tout merge |
| CLI `in_progress` utilisée | Comportement non garanti | Filtre strict `min_cli_status: dry_run_validated` dans manifest |
| Double lecture STATE.md (boot + orch.) | Gaspillage tokens | Partage de table SQLite `session_context` entre tk-boot et orchestrateur |
| Domaine ambigu (manga + github) | Mauvais routing | Scoring multi-domaine avec seuil 0.6 + règle priorité documentée |
| Boucle infinie d'enchâînement | Token explosion | `chain_max_steps: 5` + status `chain_limit_exceeded` |
| Contexte non libéré (CLI mode) | Fuite mémoire | `del` explicite + `gc.collect()` + subprocess isolé |
| `skill-registry` plugin absent | Scan skills/ lent | Scan local jusqu'à création du plugin (priorité A dans STATE.md) |
| Temporal non déployé | Workflows inaccessibles | Vérifier `workflow-engine` status avant routing vers workflows |

---

## 📚 Références

- `core/contracts/skill_output.schema.json` — v1.0.0 (contrat de sortie réel)
- `plugins/cli-forge/registry.yml` — schéma réel des CLIs
- `core/mainbrain/MainBrain_v1.5.md` — architecture d'intégration (Étape 0)
- `skills/tk-boot/SKILL.md` — skill à consommer, pas dupliquer
- `.planning/STATE.md` — v0.8, Phase 4 active
- DEC-005 : Output JSON obligatoire
- DEC-006 : Rate limiting token par workflow
- DEC-007 : 1 idée = 1 node (100–500 tokens)
- **DEC-008 (à logger)** : Orchestrator-First Pattern — 15/05/2026

---

## 🚀 Prochaines actions (ordonnées)

1. **Logger DEC-008** dans `.planning/DECISIONS.md` (décision architecturale Orchestrator-First)
2. **Mettre à jour STATE.md** : Phase 4 → ajouter `tk-orchestrator: en développement`
3. **Créer le squelette** : `mkdir -p skills/tk-orchestrator/{router,budget,context,tests}`
4. **Implémenter `orchestrator.py`** v0.2.0 avec routing multi-domaine + abort-on-failure
5. **Partager le cache SQLite** avec tk-boot (table `session_context`)
6. **Ajouter les tests de contrat** : `tests/cli_contracts/test_orchestrator.py`
7. **Valider le manifest** contre `plugins/cli-forge/cli_manifest.schema.json`
8. **Attendre `source-watch-goat`** → `dry_run_validated` avant intégration

---

## 📋 À copier — DEC-008 pour DECISIONS.md

```markdown
### DEC-008 — Orchestrator-First Pattern
- **Date** : 15/05/2026
- **Statut** : Acceptée
- **Décision** : Créer tk-orchestrator comme skill prioritaire (Étape 0 du MainBrain v1.5) pour le routing multi-domaine et l'optimisation token
- **Raison** : Réduire les tokens en chargeant uniquement le contexte nécessaire, appliquer CLI-first systématiquement, unifier les deux interfaces (CLI Python + Cowork)
- **Alternatives rejetées** : Router directement dans MainBrain (trop couplé, non testable), LLM-only routing (trop coûteux), duplication tk-boot (redondance)
- **Impact** : Toutes les commandes /tk:* passent par cet orchestrateur ; min_cli_status = dry_run_validated ; gains token estimés 30–60% ; source-watch-goat intégré seulement après passage prod_ready
```

---

## 📊 Notes de fiabilité

| Élément | Niveau | Commentaire |
|---|---|---|
| Schéma JSON output | ✅ Confirmé | Ancré sur `skill_output.schema.json` v1.0.0 réel |
| Registry CLIs | ✅ Confirmé | Ancré sur `registry.yml` réel v0.1.0 |
| Intégration MainBrain | ✅ Confirmé | Injection Étape 0 vérifiée contre `MainBrain_v1.5.md` réel |
| État projet | ✅ Confirmé | v0.8 Phase 4, vérifié dans `STATE.md` du 15/05/2026 |
| `source-watch-goat` exclu | ✅ Confirmé | `in_progress` dans registry — exclusion documentée |
| Token counting heuristique | 🟡 Probable | 4 chars/token valide pour latin ; moins précis pour texte japonais (kanji ~1-2 chars/token) |

---

*tk-orchestrator v0.2.0 — Spec révisée 15/05/2026 — TricorderKit v0.8*
