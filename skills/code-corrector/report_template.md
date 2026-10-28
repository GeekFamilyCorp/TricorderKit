# Rapport de correction & durcissement — <app> — <AAAA-MM-JJ>

## 1. Résumé exécutif
- État général : <ok / à risque / critique>
- Bugs corrigés : <n> · Vulnérabilités traitées : <n corrigées / m proposées>
- Modifications structurales **en attente de votre approbation** : <n>

## 2. Bugs corrigés
| # | Symptôme | Cause racine | Correctif | Test (rouge→vert) |
|---|----------|--------------|-----------|-------------------|
| 1 |          |              |           |                   |

## 3. Vulnérabilités (audit OWASP Top 10)
| Réf | Faille | Gravité | Exploitable | Statut |
|-----|--------|---------|-------------|--------|
| A03 | ex. XSS réfléchi | Élevé | oui | ✅ corrigé (local) |
| A01 | ex. IDOR | Critique | oui | ⏳ **proposé — attente accord** |

> Gravité : Critique / Élevé / Moyen / Faible. Statut : ✅ corrigé (local) · ⏳ proposé (structural, attente accord).

## 4. Flux de données (affichage)
- Plafonds d'affichage **levés** (artificiels) : <liste + méthode : pagination / virtualisation / streaming>
- Protections serveur **conservées** (rate-limit, throttle, quotas, timeouts) : <liste — NON modifiées>
- Impact performance mesuré : <avant → après>

## 5. Design / visuel
- Changements visuels : <aucun> | <liste justifiée + avant/après>

## 6. Modifications STRUCTURALES proposées (⏳ en attente d'approbation)
Pour chacune : périmètre, diff envisagé, raison, risque, plan de rollback.
1. …

## 7. Tests ajoutés
- Unitaires : <n> · Intégration : <n> · Couverture des correctifs : <%>

## 8. Recommandations (maintenabilité, perf, sécurité)
- …
