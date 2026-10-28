---
name: skill-manager
description: "Gestionnaire centralisé des skills et plugins Claude Cowork installés : inventaire multi-racines (skills autonomes, plugins, anciennes surfaces), health check à 8 critères appuyé sur quick_validate.py, détection de conflits et redondances, comparaison, archivage, changelog. S'active quand l'utilisateur parle de 'mes skills', 'inventaire skills', 'audit skills', 'health check', 'conflit skills', 'compare skill A et B', 'que fait le skill X', 'archive le skill', 'changelog skill', 'optimise mon écosystème'. Ne pas utiliser pour : créer ou améliorer un skill avec evals (→ skill-creator), détecter un skill MANQUANT pour une tâche (→ capability-scout), une veille état-de-l'art (→ god-mode)."
license: MIT
metadata:
  version: "3.1"
  author: GeekFamilyCorp
  domain: meta-management
  activation: auto
  updated: "2026-09-07"
---

# skill-manager — Inventaire, audit et hygiène de l'écosystème skills/plugins

## Mission et frontières
Inventorier, classifier, auditer, comparer, archiver, documenter les skills et plugins **installés**.
- `skill-creator` (Anthropic) = création et amélioration avec evals → lui déléguer toute demande de création/refonte profonde.
- `capability-scout` = détecter ce qui MANQUE pour une tâche → hors scope ici.
- `god-mode` = veille état-de-l'art → hors scope ici.
- `capability-scout`, `god-mode` et `memory-boot` ne sont pas publiés dans ce dépôt : ce sont des
  exemples de skills voisins, à remplacer par les vôtres.

**Limite d'écriture (PATTERN-EDIT-DUALFS-001)** : les SKILL.md vus par la session (racines `synced/*`, `/mnt/skills`, `/sessions/*`) sont un **cache lecture seule** ; les éditer ne met pas à jour le skill installé. Source de vérité = votre dépôt ou vos notes (`<skills>/<skill>/SKILL.md`). Toute amélioration se livre **en fichier** (`.skill`/`.plugin` repaquetés, puis Réglages > Fonctionnalités), jamais en hot-patch silencieux. Voir `${CLAUDE_PLUGIN_ROOT}/references/regles.md` (R34, R35/R59, R60).

## Protocole 0 — Résolution multi-racines (toujours en premier)
Aucun chemin n'est codé en dur : les racines dérivent de `$HOME` et sont tentées dans l'ordre.

| Ordre | Racine | Contenu |
|---|---|---|
| 1 | `~/.claude/skills/synced/*/<skill>/SKILL.md` | skills autonomes synchronisés |
| 2 | `~/.claude/plugins/synced/*/<plugin>/skills/*/SKILL.md` | skills livrés par un plugin |
| 3 | `/mnt/skills/*/*/SKILL.md` | skills Anthropic embarqués (public/examples) |
| 4 | `/sessions/*/mnt/.claude/skills/*` et `.remote-plugins/*` | anciennes surfaces — **repli** seulement |

Exécuter `${CLAUDE_PLUGIN_ROOT}/skills/skill-manager/scripts/inventory.sh` (POSIX sh, lecture seule) :
```sh
sh "${CLAUDE_PLUGIN_ROOT}/skills/skill-manager/scripts/inventory.sh"            # racines par défaut
sh "${CLAUDE_PLUGIN_ROOT}/skills/skill-manager/scripts/inventory.sh" --tsv      # sortie tabulée
SKILL_ROOTS="/chemin/a /chemin/b" sh .../inventory.sh                           # racines explicites
```
Colonnes : `nom | racine | lignes | mots | frontmatter OK/KO:<clés interdites> | chemins en dur (n)`.
Recouper ensuite avec le bloc `<available_skills>` du system prompt et `ListSkills` / `ListPlugins` : le système de fichiers reste la source de vérité (R51). Si aucune racine ne répond, le dire — ne pas inventer un inventaire.

Le préfixe des outils MCP dépend de la surface (`mcp__remote-devices__…` en Cowork sur le poste) : vérifier dans la liste d'outils de la session avant d'en citer un.

## Classification

| Type | Déclenchement | Exemple |
|---|---|---|
| Auto-actif | description déclenche seule | `resilient-ops` |
| Manuel | `disable-model-invocation: true`, invocation explicite | `interview-me`, `head-agent` |
| Hybride | auto + entrée manuelle documentée | `memory-boot` |
| En conflit | ≥ 3 mots-clés partagés avec un autre skill | à traiter (protocole 4) |
| Inactif | archivé ou non chargé par la surface | `status: archived` sous `metadata` |

Priorité en cas de chevauchement : skill nommé par l'utilisateur > spécialisé > généraliste > plugin marketplace > archivé.

## Health check — 8 critères (score /8)
Outil : `quick_validate.py`, qui vit dans `skills/skill-creator/scripts/quick_validate.py` du skill Anthropic **skill-creator** quand il est installé (`python3 <chemin>/quick_validate.py <dossier_du_skill>`). Il vérifie les clés de frontmatter autorisées (`name, description, license, allowed-tools, metadata, compatibility`), le kebab-case, la longueur de la description (≤ 1024, sans chevrons). S'il n'est pas installé, `inventory.sh` donne déjà la colonne frontmatter.

1. Frontmatter valide (clés autorisées uniquement ; `quick_validate.py` passe). Exception connue : `disable-model-invocation: true` (skills manuels) est valide pour Claude Code / Cowork mais rejeté par `quick_validate.py`, qui vise l'upload Skills API — ne pas compter cet écart comme un KO pour un skill manuel.
2. Déclencheurs explicites dans la description (QUOI + QUAND + « Ne pas utiliser pour → X »).
3. Instructions claires, impératives, < 500 lignes (le reste en `references/`).
4. Pas de conflit de mots-clés avec un autre skill installé.
5. Scope délimité (exclusions nommées vers le skill voisin).
6. **Version sous `metadata`** (`metadata.version`) et changelog daté en fin de fichier.
7. Exemples inclus (≥ 2 entrées → comportement attendu).
8. **Aucun chemin de session ni chemin personnel en dur** (colonne « chemins en dur » = 0).

## Rapports
- **Standard** (« liste / inventaire skills ») : résumé (nb skills par racine, plugins, alertes) + table par type + 3 recommandations.
- **Health check** : table `skill | score /8 | critères KO | action`.
- **Comparaison** : type · activation · domaine · déclencheurs · chevauchement % · recommandation (garder / fusionner / re-scoper).

## Protocoles d'action
1. **Audit complet** : Protocole 0 → classification → mots-clés → 8 critères → rapport → 3 actions priorisées.
2. **Analyse d'un skill** : failles → conflits → AVANT/APRÈS → version améliorée livrée en fichier + voie d'install.
3. **Nouveau skill** : déléguer à `skill-creator` ; rappeler R35/R59 (un plugin par famille) et R69 (vérifier le registre avant).
4. **Résolution de conflit** : garder le plus spécialisé, réécrire le généraliste avec « Ne pas utiliser pour », tester 5 requêtes.
5. **Archivage** : `metadata.status: archived` + raison + date ; vérifier les dépendances ; jamais de suppression (R31 NO-DROP).
6. **Changelog et versionning** : chaque modification datée sous `## Changelog`, `metadata.version` incrémentée.

## Détection automatique (drapeaux)
- Critique : conflit ≥ 3 mots-clés · chemin de session/personnel en dur · clé de frontmatter interdite.
- Risque : chevauchement 1-2 mots-clés · description > 1024 ou sans exclusion · référence à un outil qui n'existe pas dans la surface.
- Mineur : sans version sous metadata · sans exemples · > 500 lignes · manuel promouvable en auto.

## Exemples
- « Liste mes skills » → Protocole 0 + rapport standard.
- « Health check du plugin tk-knowledge » → `inventory.sh` sur la racine plugins + `quick_validate.py` sur chaque dossier + table /8.
- « Y a-t-il des conflits entre file-organizer et le skill de rangement du vault ? » → comparaison + recommandation.
- « Archive le skill fiche-validator » → protocole 5, proposé puis appliqué sur GO (R53).
- « Il me manque un skill pour X » → renvoyer à `capability-scout`.

## Modèles
`fast` pour l'inventaire brut, `default` pour l'audit et les rapports ; jamais `deep` pour cette tâche. Alias définis dans `${CLAUDE_PLUGIN_ROOT}/models.json` (DEC-031).

## Changelog
### v3.1 — 2026-09-07
- Frontmatter conforme (`version/author/domain/activation` → `metadata`). Protocole 0 réécrit en résolution multi-racines (`~/.claude/skills/synced`, `~/.claude/plugins/synced`, `/mnt/skills`, `/sessions/*` en repli) + script `scripts/inventory.sh` (POSIX, sans chemin en dur). Health check adossé à `quick_validate.py` (emplacement documenté) ; critère 6 reformulé « version sous metadata ». « Skill manquant » retiré du scope (→ capability-scout). Tableau de classification réparé. Outils de découverte réels (`ListSkills`, `ListPlugins`). Limite DUALFS conservée, renvoi `references/regles.md`.
### v3.0 — 2026-06-19
- Résolution dynamique du chemin de session, arborescence plugins, 8e critère, limite EDIT-DUALFS, source de vérité vault.
### v2.0 — 2026-04-15
- Perplexity → Cowork ; Protocole 0 ; support plugins ; frontière skill-creator.
### v1.0 — 2026-01-01
- Création initiale.
