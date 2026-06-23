---
name: agent-config-audit
description: Audit de sécurité de la CONFIGURATION DE L'AGENT lui-même (pas de l'app applicative). À utiliser pour passer en revue les serveurs MCP et leurs portées, les hooks et commandes, les permissions/auto-approbations d'outils, les secrets en clair dans les configs/hooks/env, l'exécution de code distant ou non épinglé, et l'exposition réseau de la surface agent. Déclencheurs : "audit de ma config agent", "AgentShield", "mes MCP sont-ils sûrs", "audit des hooks/permissions", "secrets en clair dans la config", "revue de sécurité du harnais". Produit un tableau de gravité + correctifs PROPOSÉS. NE MODIFIE JAMAIS les contrôles d'accès / permissions / secrets lui-même (interdit) : il PROPOSE, l'utilisateur applique. Complète code-corrector (applicatif) et le coffre SOPS (secrets au repos), sans les dupliquer.
version: "1.0"
author: claude
---

# agent-config-audit — Audit de la surface de l'agent (inspiré d'AgentShield, ECC)

> Là où `code-corrector` audite **l'application**, ce skill audite **le harnais lui-même** : ce qui peut
> exécuter du code ou exfiltrer des données à travers la config de l'agent (MCP, hooks, permissions,
> secrets). C'est l'angle mort que ni `code-corrector` (applicatif) ni le coffre SOPS (secrets au repos)
> ne couvrent. **100 % lecture seule + propositions** : aucune modification automatique des contrôles
> d'accès, permissions ou secrets — ces actions sont réservées à l'utilisateur.

## ⚖️ Règle cardinale
- **Audit en lecture seule.** Inventorier et évaluer, jamais modifier la config, les permissions, les
  partages ou les secrets. Tout correctif est **PROPOSÉ** (avec le « comment ») et appliqué par l'humain.
- Aucun secret n'est imprimé en clair : on signale *l'emplacement* d'une fuite, pas sa valeur.

## Surface à inventorier (ce qu'un agent peut faire ou fuir)
1. **Serveurs MCP** : lesquels sont déclarés, leur portée (lecture/écriture, système de fichiers, réseau,
   exécution), et s'ils sont nécessaires. Un MCP large = surface d'attaque large.
2. **Hooks** (PreToolUse/PostToolUse…) : quelles commandes s'exécutent automatiquement, sur quels events,
   avec quel shell. Pièges : expansion de variables non portable (`${VAR}` vs `%VAR%`), exécution de
   scripts distants, hooks **bloquants** par accident, code non épinglé.
3. **Commandes / slash / skills** déclenchables : exécutent-elles du shell ? avec quels droits ?
4. **Permissions & auto-approbations** : des outils dangereux (suppression, réseau, paiement, exécution)
   sont-ils auto-approuvés ? Le principe de moindre privilège est-il respecté ?
5. **Secrets** : clés/API/tokens en **clair** dans des fichiers de config, hooks, env versionnés, ou logs.
6. **Chaîne d'approvisionnement** : plugins/skills/MCP installés depuis des sources non vérifiées ;
   versions non épinglées ; mises à jour automatiques exécutant du code.
7. **Exposition réseau** : endpoints de l'agent/outils écoutant au-delà de loopback/tailnet.

## Checklist de findings (gravité : Critique / Élevé / Moyen / Faible)
- A. **Secret en clair** dans config/hook/env versionné → Critique (renvoyer vers SOPS/env root-only).
- B. **MCP en écriture/exécution non nécessaire** ou portée trop large → Élevé.
- C. **Hook auto-exécutant du code** distant / non épinglé / bloquant / `${VAR}` non portable → Élevé/Moyen.
- D. **Auto-approbation d'outils dangereux** (delete, transfert, exécution arbitraire) → Élevé.
- E. **Plugin/MCP de source non vérifiée** ou version flottante → Moyen.
- F. **Endpoint d'outil exposé** hors loopback/tailnet → Élevé selon le service.
- G. **Permissions trop larges** vs usage réel (moindre privilège) → Moyen.

## Workflow
1. **Inventaire** : lister MCP, hooks, commandes, permissions, références de secrets (sans lire les valeurs).
2. **Évaluation** : passer la checklist A–G, classer chaque finding par gravité + exploitabilité.
3. **Proposition** : pour chaque finding, le correctif (ex. « migrer ce secret vers le coffre SOPS »,
   « restreindre la portée de ce MCP », « rendre ce hook non bloquant et portable », « retirer
   l'auto-approbation de l'outil X »), **en attente d'application par l'utilisateur**.
4. **Rapport** : utiliser `report_template.md` (même dossier).

## Format de rapport
Voir `report_template.md` : Résumé → Surface inventoriée (MCP/hooks/commandes/permissions) →
Tableau findings (réf, gravité, emplacement, exploitabilité, correctif proposé, statut=PROPOSÉ) →
Quick wins → Correctifs structuraux (attente accord).

## Garde-fous
- **Lecture seule**, propositions uniquement. Modifier permissions/contrôles d'accès/secrets = interdit → l'humain le fait.
- Ne jamais imprimer une valeur de secret ; signaler l'emplacement.
- Anti-duplication : applicatif/OWASP → `code-corrector` ; secrets au repos → coffre **SOPS** ;
  durcissement profond → `security-and-hardening`. Ce skill cible **uniquement la config de l'agent**.
- R37 : générique, aucun chemin/terme privé dans le repo public.
