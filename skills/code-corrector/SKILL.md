---
name: code-corrector
description: Correcteur et durcisseur de code web, discipliné et mesuré. À utiliser quand l'utilisateur veut corriger les bugs d'une web app, faire un audit de sécurité (OWASP Top 10 : injections, XSS, CSRF, contrôle d'accès), lever les plafonds d'affichage/pagination SANS retirer les protections serveur, optimiser un code en préservant à 100% le design existant, ou produire un rapport de correction structuré avec correctifs testés. Déclencheurs : "corrige les bugs de mon app", "audit sécurité", "OWASP", "déverrouille l'affichage / flux illimité", "optimise sans casser le design", "failles XSS/CSRF/injection". RÈGLE CARDINALE : toute modification STRUCTURALE est PROPOSÉE puis exécutée seulement après approbation explicite de l'utilisateur. NE PAS utiliser pour une revue de style pure (déléguer code-review-and-quality) ni un débogage ponctuel trivial.
version: "1.0"
author: claude
---

# code-corrector — Correction + durcissement web, sous contrôle humain

> Transforme un « corrige tout » flou en **processus discipliné, testé et réversible** : on inventorie,
> on reproduit, on corrige avec un test par correctif, on audite la sécurité (OWASP Top 10), on lève les
> plafonds d'affichage **sans démonter les protections serveur**, on préserve le design, et on **propose**
> toute modification structurale avant de la faire. Complète, sans dupliquer, les skills existants :
> `security-and-hardening`, `code-review-and-quality`, `test-driven-development`,
> `debugging-and-error-recovery`, `performance-optimization` — délègue-leur les approfondissements.

## ⚖️ Règle cardinale — approbation humaine des changements structuraux

Classe CHAQUE changement avant de l'appliquer :

- **Local / sûr (applicable directement)** : correction de bug isolé, validation/échappement d'entrée,
  ajout de test, correctif d'une faille évidente sans changement d'API, micro-optimisation sans effet
  visuel. → applique, accompagné d'un test.
- **STRUCTURAL (PROPOSER + ATTENDRE le « oui » explicite de l'utilisateur)** : changement de schéma de
  données, de contrat d'API, de flux d'authentification/autorisation, d'architecture, de dépendances,
  de configuration de sécurité (CORS, CSP, sessions), suppression/altération d'un contrôle de sécurité,
  ou toute modification visuelle. → **n'exécute pas**, présente le diff envisagé + le pourquoi, demande l'aval.

En cas de doute sur la catégorie : traiter comme STRUCTURAL. Ne jamais affaiblir un contrôle de sécurité
« pour que ça marche » sans accord explicite et conscient.

## ⚠️ « Flux illimité » : lever les plafonds UI, garder les protections serveur

Le besoin « affichage illimité » est légitime côté expérience, dangereux s'il est appliqué au serveur.

- **À lever (artificiel, côté présentation)** : caps d'affichage codés en dur (`limit 50`), pagination
  qui masque des données accessibles, troncatures UI. → remplacer par **pagination propre /
  virtualisation de liste / scroll infini paginé / streaming**, sans charger tout en mémoire d'un coup.
- **À CONSERVER (protection, jamais retirer sans accord)** : rate-limiting et throttling d'API, quotas
  anti-abus, timeouts, taille max de payload, garde-fous anti-DoS. Les retirer = créer une faille.
- Règle : on supprime une *limite d'affichage*, jamais une *limite de protection*. Une « limite » qui
  protège contre l'abus est un contrôle de sécurité → catégorie STRUCTURAL.

## Workflow (phases)

1. **Inventaire & périmètre.** Cartographier la stack (front, back, endpoints, points d'entrée de
   données), repérer où vivent les bugs signalés. Vérifier la **date du jour** si la logique en dépend.
2. **Reproduire avant de corriger.** Pour chaque bug : reproduire (test rouge), comprendre la cause
   racine (pas le symptôme), corriger, prouver par le test (vert). Pas de correctif sans reproduction.
3. **Audit sécurité OWASP Top 10.** Passer la liste ci-dessous, produire un **tableau gravité** (critique/
   élevé/moyen/faible), corriger les failles *locales* directement, **proposer** les correctifs structuraux.
4. **Flux de données.** Lever les plafonds d'affichage artificiels (cf. section dédiée) en gardant les
   protections serveur. Mesurer l'impact perf (pas de régression).
5. **Préservation du design.** Aucune modification visuelle sans justification + accord. Si un correctif
   touche au rendu, capturer un avant/après (screenshot/visual diff) et le présenter.
6. **Rapport + tests.** Livrer le rapport structuré (template ci-dessous) + les tests ajoutés
   (unitaires/intégration). Recommander les durcissements de maintenabilité/perf restants.

## Checklist OWASP Top 10 (2021) — à parcourir systématiquement

A01 Contrôle d'accès défaillant · A02 Défaillances cryptographiques · A03 Injection (SQL/NoSQL/cmd/XSS) ·
A04 Conception non sécurisée · A05 Mauvaise configuration de sécurité (CORS/CSP/headers) ·
A06 Composants vulnérables/obsolètes · A07 Identification & authentification défaillantes ·
A08 Manque d'intégrité des données/logiciels · A09 Journalisation & supervision insuffisantes ·
A10 SSRF. Pour chaque item : présent ? exploitable ? gravité ? correctif local ou structural ?

## Format de rapport (livrable)

Utiliser `report_template.md` (même dossier). Structure : Résumé exécutif → Bugs corrigés (cause→correctif→
test) → Vulnérabilités (tableau gravité + statut : corrigé / **proposé (attente accord)**) → Flux de données
(plafonds levés vs protections conservées) → Design (changements visuels justifiés) → Modifications
STRUCTURALES proposées (diff + raison, **en attente d'approbation**) → Tests ajoutés → Recommandations.

## Garde-fous

- **Human-in-the-loop** sur tout ce qui est structural ou visuel (cf. règle cardinale).
- **Un correctif = un test.** Pas de « corrigé » sans preuve exécutable.
- **Jamais** affaiblir un contrôle de sécurité, retirer un rate-limit/CSRF/auth, ni introduire de secret
  en clair. Ne pas écrire ni « débloquer » de code malveillant.
- **Réversibilité** : sauvegarder avant d'éditer un fichier sensible (backup daté) ; changements atomiques.
- **Intégration écosystème** : si le repo a des gates (frontière publique, docs-sync) et un pattern de
  selftest, les respecter ; consigner le passage (journal de correction) si une boucle de réflexion existe.
- **Anti-duplication** : approfondissement sécurité → `security-and-hardening` ; revue qualité →
  `code-review-and-quality` ; tests → `test-driven-development` ; perf → `performance-optimization`.
  code-corrector = l'**orchestrateur** qui cadre, séquence et rend compte.
