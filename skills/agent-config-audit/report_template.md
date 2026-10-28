# Audit de configuration agent — <environnement> — <AAAA-MM-JJ>

## 1. Résumé exécutif
- Surface auditée : <n MCP, n hooks, n commandes/skills>
- Findings : Critique <n> · Élevé <n> · Moyen <n> · Faible <n>
- Tous les correctifs sont **PROPOSÉS** (à appliquer par l'utilisateur ; aucun contrôle modifié).

## 2. Surface inventoriée
- **MCP** : <nom → portée (lecture/écriture/exec/réseau/fs) → nécessaire ?>
- **Hooks** : <event → commande → shell → bloquant ? portable ?>
- **Commandes / slash / skills exécutant du shell** : <liste>
- **Permissions / auto-approbations** : <outils auto-approuvés>
- **Références de secrets** : <emplacements — valeurs NON lues>

## 3. Findings
| Réf | Gravité | Emplacement | Exploitabilité | Correctif proposé | Statut |
|-----|---------|-------------|----------------|-------------------|--------|
| A | Critique | ex. clé en clair dans config | exfiltration | migrer vers coffre SOPS / env root-only | ⏳ PROPOSÉ |
| C | Moyen | ex. hook ${VAR} non portable | blocage outil | rendre non bloquant + portable | ⏳ PROPOSÉ |

> Gravité : Critique / Élevé / Moyen / Faible. Statut : toujours ⏳ PROPOSÉ (l'humain applique).

## 4. Quick wins (sûrs, à appliquer en priorité)
- …

## 5. Correctifs structuraux (impact config/permissions — attente d'accord explicite)
Pour chacun : périmètre, action, risque, rollback. L'utilisateur applique.
1. …

## 6. Notes
- Audit lecture seule. Aucun secret affiché. Renvois : secrets→SOPS, applicatif→code-corrector.
