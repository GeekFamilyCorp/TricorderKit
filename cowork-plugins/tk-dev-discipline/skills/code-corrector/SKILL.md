---
name: code-corrector
description: >-
  Corrige et durcit le code d'une application web de façon disciplinée et mesurée. À utiliser quand
  l'utilisateur veut corriger les bugs d'une web app, faire un audit de sécurité (OWASP Top 10 :
  injections, XSS, CSRF, contrôle d'accès), lever les plafonds d'affichage/pagination SANS retirer
  les protections serveur, optimiser un code en préservant à 100 % le design existant, ou obtenir un
  rapport de correction structuré avec correctifs testés, y compris un composant de la stack
  personnelle (mode privé). Déclencheurs : "corrige les bugs de mon app", "audit sécurité", "OWASP",
  "déverrouille l'affichage / flux illimité", "optimise sans casser le design", "failles
  XSS/CSRF/injection". Règle cardinale : toute modification STRUCTURALE est proposée puis exécutée
  seulement après approbation explicite. Ne pas utiliser pour un débogage ponctuel d'un script ou
  d'un timer → debugging-and-error-recovery, ni pour auditer la configuration de l'agent (MCP,
  hooks, permissions) → agent-config-audit.
license: Proprietary
metadata:
  version: "1.1"
  author: GeekFamilyCorp
  langues: fr
---

# code-corrector — Correction + durcissement web, sous contrôle humain

Transforme un « corrige tout » flou en processus discipliné, testé et réversible : inventorier,
reproduire, corriger avec un test par correctif, auditer la sécurité, lever les plafonds d'affichage
sans démonter les protections serveur, préserver le design, et **proposer** toute modification
structurale avant de la faire.

Règles maison citées (R53 : confirmation avant action irréversible ou externe ; R70 : jamais de
commande par concaténation ; R43 : secret exposé = compromis) — définitions dans
`${CLAUDE_PLUGIN_ROOT}/references/regles.md`.

## Règle cardinale — approbation humaine des changements structuraux

Classer CHAQUE changement avant de l'appliquer :

- **Local / sûr (applicable directement)** : correction de bug isolé, validation ou échappement
  d'entrée, ajout de test, correctif d'une faille évidente sans changement d'API, micro-optimisation
  sans effet visuel. → appliquer, accompagné d'un test.
- **STRUCTURAL (proposer + attendre le « oui » explicite)** : schéma de données, contrat d'API, flux
  d'authentification/autorisation, architecture, dépendances, configuration de sécurité (CORS, CSP,
  sessions), suppression ou altération d'un contrôle de sécurité, toute modification visuelle, toute
  écriture sur un service en production. → ne pas exécuter ; présenter le diff envisagé + le pourquoi.

En cas de doute sur la catégorie : STRUCTURAL. Ne jamais affaiblir un contrôle de sécurité « pour que
ça marche » sans accord explicite et conscient.

## « Flux illimité » : lever les plafonds UI, garder les protections serveur

- **À lever (artificiel, présentation)** : caps codés en dur (`limit 50`), pagination qui masque des
  données accessibles, troncatures UI → pagination propre, virtualisation de liste, scroll paginé,
  streaming. Jamais tout en mémoire d'un coup.
- **À conserver (protection)** : rate-limiting, quotas anti-abus, timeouts, taille max de payload,
  garde-fous anti-DoS. Une limite qui protège est un contrôle de sécurité → STRUCTURAL.

## Deux modes

| Mode | Quand | Ce qui change |
|---|---|---|
| **Générique** (défaut) | code d'un tiers, projet public, application inconnue | rien de nommé ; rapport standard |
| **Privé** | l'utilisateur vise un composant de sa propre stack (graphe, vecteurs, workflows, gateway, agent de veille, VPS) | lire ``references/stack-privee.md` du plugin PRIVÉ gfc-ops (absent du dépôt public, R37)` : protocole PROD, composants à conserver, inventaire à revérifier |

Le mode privé ajoute en tête du rapport : composant visé, environnement (poste / VPS), mode
(lecture seule / modification approuvée). Ce fichier de référence ne franchit jamais la frontière du
dépôt public (R37).

## Workflow

1. **Inventaire & périmètre.** Cartographier front, back, endpoints, points d'entrée de données ;
   localiser les bugs signalés. Vérifier la date du jour si la logique en dépend.
2. **Reproduire avant de corriger.** Par bug : test rouge → cause racine (pas le symptôme) → correctif
   → test vert. Pas de correctif sans reproduction.
3. **Audit sécurité.** Passer la grille `references/owasp.md` (A01→A10, quatre questions par item),
   produire le tableau de gravité, corriger les failles *locales*, proposer les structurales.
4. **Flux de données.** Lever les plafonds d'affichage (section dédiée), mesurer l'impact perf.
5. **Préservation du design.** Aucune modification visuelle sans justification + accord ; si un
   correctif touche au rendu, capturer un avant/après.
6. **Rapport + tests.** Livrer selon `report_template.md` (même dossier) + les tests ajoutés.

## Exemples

**Correctif local (appliqué directement).**
Entrée : « la recherche plante quand je tape une apostrophe ».
Reproduction : `GET /search?q=l'été` → 500, stacktrace SQL. Cause : concaténation dans la requête.
Correctif : requête paramétrée. Test : `test_search_apostrophe` rouge → vert. Statut : corrigé (local),
ligne A03 du tableau.

**Modification structurale (proposée, non exécutée).**
Entrée : « les utilisateurs voient les factures des autres en changeant l'id dans l'URL ».
Cause : A01, aucune vérification d'appartenance. Le correctif minimal (vérifier `invoice.owner == user`)
est local et appliqué. Mais l'audit montre que le même défaut existe sur 6 routes : la solution propre
est un middleware d'autorisation par ressource → **changement d'architecture, proposé dans la section 6
du rapport avec diff, risque et rollback ; en attente d'accord.**

**Mode privé.**
Entrée : « le dashboard de la gateway tronque la liste des runs à 100 ».
Lecture de ``references/stack-privee.md` du plugin PRIVÉ gfc-ops (absent du dépôt public, R37)` → environnement poste, service en marche → mode lecture seule
d'abord. Diagnostic : cap UI côté template. Correctif : pagination côté client, aucun paramètre serveur
touché (le throttle reste). Rapport en-tête : composant = agent-gateway, env = poste, mode = modif
locale approuvée.

## Garde-fous

- Human-in-the-loop sur tout ce qui est structural, visuel ou prod (R53).
- Un correctif = un test ; pas de « corrigé » sans preuve exécutable.
- Jamais affaiblir un contrôle, retirer un rate-limit/CSRF/auth, ni introduire de secret en clair ;
  pas de code malveillant.
- Réversibilité : backup daté avant d'éditer un fichier sensible ; changements atomiques.
- Modèle : `default` pour la correction, `deep` seulement pour une faille d'architecture — alias dans
  `${CLAUDE_PLUGIN_ROOT}/models.json`.
- Frontières : bug d'un script ou d'un timer sans app web → `debugging-and-error-recovery` ; config de
  l'agent → `agent-config-audit` ; décision irréversible à stresser → `doubt-driven-development`.

## Changelog
- **2026-09-07 — 1.1** : absorbe `code-corrector-local` (archivé) ; checklist OWASP déplacée en
  `references/owasp.md` ; mode privé + protocole PROD en ``references/stack-privee.md` du plugin PRIVÉ gfc-ops (absent du dépôt public, R37)` (PRIVÉ, R37) ;
  renvois fantômes supprimés ; frontmatter normalisé ; trois exemples ajoutés.
- **2026-06 — 1.0** : version initiale.
