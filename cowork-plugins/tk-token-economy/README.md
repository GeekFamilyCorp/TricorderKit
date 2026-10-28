# tk-token-economy v1.0.0 — PUBLIC (MIT)

Économie de tokens : routage manuel par alias de modèle (model-router), budget estimé (status/analyze/optimize), sortie compressée caveman, handoff de contexte (context-compress), documentation fraîche via Context7 (docs-fresh) ; models.json unique.

Regroupement du 2026-09-07 (audit `claude/AUDIT_SKILLS_PLUGINS_2026-09-07.md`, lot L4) : un plugin = un domaine d'usage.

## Skills

| Skill | Rôle |
|---|---|
| `budget` | Suit, analyse et optimise la consommation mensuelle de tokens ESTIMÉE par famille de modèle (fast / default / deep, voir models.json) à partir d'un fichier local. Trois modes : `status` (consommation et seuils 50/80/95 %… |
| `caveman` | Mode de réponse compressé (inspiré de JuliusBrussee/caveman et GabrielBarberini/laconic) qui supprime le remplissage, les formules de politesse et les articles superflus tout en gardant intacte la précision technique, su… |
| `context-compress` | Compresse le contexte d'une conversation longue en un résumé structuré à cinq sections (objectif, décisions, fichiers touchés, état courant, prochaines étapes) qui préserve chemins, identifiants et contraintes négociées,… |
| `docs-fresh` | Interroge la documentation officielle à jour d'une bibliothèque, d'un framework, d'un SDK ou d'une CLI via le connecteur Context7 déjà présent dans la session (resolve-library-id puis query-docs), pour éviter les API hal… |
| `model-router` | Classifie une demande en tier de complexité (T1 simple, T2 standard, T3 complexe) avec un score 0-100, choisit l'alias de modèle correspondant (fast / default / deep, identifiants dans models.json) et délègue à l'agent e… |

## Fichiers partagés

- `references/regles.md` — définitions en une ligne des règles R.. citées par les skills (source : `RULES_REGISTRY.md` du claude-vault).
- `models.json` — alias de modèles `fast` / `default` / `deep` ; seul endroit où un identifiant de modèle est écrit.

## Retour arrière

Chaque version livrée est archivée (`plugins-2026-09-07/` v1 des anciens plugins, `plugins-2026-09-07-L4/` cette version). Revenir en arrière = désactiver ce plugin dans Réglages > Fonctionnalités et réinstaller le `.plugin` précédent. Aucune donnée n'est touchée par l'installation : les skills lisent ; ce qui écrit passe par le SAS ou par un GO explicite. NO-DROP : on désactive, on ne supprime pas.

## Changelog

### 1.0.0 — 2026-09-07
- Création par regroupement (L4) à partir de tricorderkit-skills 0.4.0 / gfc-maison-ops 1.4.0 / token-optimizer 0.3.0 ; renvois inter-skills réécrits sur les nouveaux noms de plugins ; validateur Anthropic 100 %.
