# QUEUE.md — File d'attente token hygiene

> Créé : 2026-05-22
> Objectif : planifier les actions token hygiene restantes, à lancer dès que le quota Claude est disponible (toutes les 5h).
> Statut : mise à jour après chaque action complétée.

---

## Statut des actions

| # | Action | Environnement | Durée estimée | Statut | Slot |
|---|---|---|---|---|---|
| ✅ | CLAUDE.md v0.9 + cowork-boot skill | Claude.ai + GitHub MCP | 15 min | **DONE** | 2026-05-22 |
| 1 | Mettre à jour instructions Space Cowork Japan-Alliance | Manuel (interface Cowork) | 10 min | **DONE ✅** | 2026-05-22 |
| 4 | Générer BOOT_SUMMARY_JA.md dans claude-vault | Claude Code | 20 min | **DONE ✅** | 2026-05-22 |
| 5 | Générer session_capsule_v0.9_JA.json à jour | Claude Code | 10 min | **DONE ✅** | 2026-05-22 |

> Action 3 (migration memory-boot + token-optimizer) → **déjà complétée en M1** (voir BOOT_SUMMARY.md)

---

## Action 1 — Mettre à jour les instructions Space Cowork Japan-Alliance

**Statut : DONE ✅ — 2026-05-22**
**Environnement** : Manuel dans l'interface Claude Cowork
**Durée** : 10 min
**Sans Claude Code ni quota**

### Instructions

Ouvrir les instructions du Space Claude Cowork Japan-Alliance.
Vérifier que les blocs suivants sont présents. Sinon, les ajouter.

**Bloc 1 — Template Routing (obligatoire)**

Coller la table complète de `skills/cowork-boot/SKILL.md` section "Template Routing".
Règle à ajouter : "Ne charger un template que si le mot-clé déclencheur est présent dans la requête."

**Bloc 2 — Extended Thinking (obligatoire)**

```
Do not use extended thinking unless I explicitly ask for it with the keyword [THINK].
Disable extended thinking for: fiche filling, web search, template generation, CLI execution.
```

**Bloc 3 — Session Rotation (obligatoire)**

```
Ouvrir un nouveau fil toutes les 15–20 messages.
Avant de fermer : générer une session_capsule JSON compacte.
Coller la capsule en premier message du nouveau fil.
```

**Bloc 4 — Boot léger (obligatoire)**

```
Au début de chaque session : lire BOOT_SUMMARY_JA.md uniquement.
Ne charger les autres fichiers que si nécessaire.
Ne jamais charger tous les templates au démarrage.
```

### Critère de validation
- [x] Instructions Space mises à jour
- [x] Template routing présent
- [x] Extended Thinking désactivé par défaut
- [x] Session rotation configurée
- [x] Boot lazy-load configuré

---

## Action 4 — Créer BOOT_SUMMARY_JA.md dans claude-vault

**Statut : DONE ✅ — 2026-05-22**
**Environnement** : Claude Code
**Durée** : 20 min
**Quota requis** : oui

### Instructions pour Claude Code

Créer `BOOT_SUMMARY_JA.md` dans le vault `claude-vault` Obsidian.
Source de vérité : `BOOT_SUMMARY.md` TricorderKit (247 tests, v0.9 M2, commit `dd6902f`).
Destination : `claude-vault/20_ENTITIES/Projects/BOOT_SUMMARY_JA.md`

Structure cible (~400 tokens) :

```markdown
# BOOT_SUMMARY_JA — Japan-Alliance
> Mis à jour : [DATE]. Ne pas éditer manuellement.

## Version & statut
Version : v0.9 | Dernière session : [DATE] | Statut : [active|pause]

## Phase active
[Nom de la phase] — [description courte]

## Tâche prioritaire
> [Une seule action concrète]

## Tâches en cours
- [ ] [tâche 1]
- [ ] [tâche 2]

## Patterns actifs
| Code | Règle |
|---|---|
| ARCH-001 | Hooks Cowork inertes → comportement dans SKILL.md |

## Dernières décisions
| Code | Résumé |
|---|---|
| DEC-010 | linked_project : TK exécute, JA stocke |

## Pour aller plus loin (lazy-load)
- Templates → skills/cowork-boot/SKILL.md (routing conditionnel)
- State détaillé → STATE_JA.md
- Décisions → .planning/DECISIONS.md
```

### Critère de validation
- [x] Fichier créé dans `claude-vault/20_ENTITIES/Projects/`
- [x] Taille ≤ 500 tokens
- [x] Source de vérité : BOOT_SUMMARY.md (247 tests, v0.9 M2, dd6902f)
- [x] Frontmatter YAML (project, version, commit, type)

---

## Action 5 — Générer session_capsule_v0.9_JA.json

**Statut : DONE ✅ — 2026-05-22**
**Environnement** : Claude Code
**Durée** : 10 min
**Quota requis** : oui

### Instructions pour Claude Code

Générer `vault/session_capsule_v0.9_JA.json` dans TricorderKit
(fichier de référence — la version active reste dans claude-vault).

Structure :

```json
{
  "project": "Japan-Alliance",
  "linked_engine": "TricorderKit",
  "version": "v0.9",
  "status": "active",
  "domain": "manga/anime/ln/bdd/saas",
  "architecture": {
    "tricorderkit": "exécute",
    "mangatracker": "spécialise",
    "japan_alliance": "stocke"
  },
  "phase_active": "v0.9 M3 — Observabilité + tests live",
  "vault_claude": "<claude-vault-path>",
  "vault_ja": "<vault-path>/Japan-Alliance",
  "session_rules": [
    "CLI avant LLM",
    "Output JSON obligatoire",
    "Dry-run avant write",
    "Ne pas recréer l'existant",
    "Mettre à jour BOOT_SUMMARY_JA après changement",
    "Extended Thinking désactivé sauf [THINK]",
    "Rotation session toutes les 15-20 messages"
  ],
  "open_tasks": [
    "B3 — Tests live deep-research (MangaDex + AniList)",
    "M4 — Observabilité bout-en-bout (Langfuse hooks)",
    "Push GitHub TricorderKit v0.9 M2 complet"
  ],
  "next_action": "Voir BOOT_SUMMARY_JA.md dans claude-vault",
  "resume_prompt": "Lire BOOT_SUMMARY_JA.md. Charger les templates uniquement si mot-clé déclencheur présent. Mode CLI-first, no speculation."
}
```

### Critère de validation
- [x] Fichier généré dans `vault/session_capsule_v0.9_JA.json`
- [x] Copie dans `claude-vault/` pour usage Cowork
- [x] `session_rules` complètes (7 règles)
- [x] `open_tasks` alignées avec BOOT_SUMMARY.md (5 tâches dans le fichier)

---

## Critères de clôture

La QUEUE est terminée quand :
- [x] Action 1 validée (instructions Space mises à jour)
- [x] Action 4 validée (BOOT_SUMMARY_JA.md créé)
- [x] Action 5 validée (session_capsule_v0.9_JA.json créé)
- [ ] Une session Cowork Japan-Alliance démarre sans charger les 47 templates
- [ ] Le budget tokens de boot est ≤ 500 tokens (TIER 1 seul)

---

*Mis à jour : 2026-05-22 — Actions 1, 4, 5 DONE — Token Hygiene Plan v0.9*
