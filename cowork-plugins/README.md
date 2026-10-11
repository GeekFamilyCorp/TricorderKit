# cowork-plugins — plugins Claude (Cowork / Claude Code) de TricorderKit

Cinq plugins génériques, installables tels quels dans Claude. Ils portent des méthodes de travail,
pas des données : aucun secret, aucun chemin personnel, aucune référence à un projet privé.

| Plugin | Ce qu'il apporte |
|---|---|
| `tk-token-economy` | routage de modèle par complexité, budget de tokens, compression de contexte, documentation à jour |
| `tk-agent-security` | audit en lecture seule de la configuration d'un agent, compression des sorties de commandes |
| `tk-data-ops` | graphe Neo4j, recherche hybride vecteurs + graphe, collecte web respectueuse, veille de changements |
| `tk-knowledge` | orchestration multi-agents, gestion et évaluation de skills, documentation vers skill |
| `tk-dev-discipline` | protocole de développement, débogage, revue adverse, entretien de cadrage, observabilité |

## Installer un plugin

1. Créer l'archive du plugin, son contenu à la racine (`.claude-plugin/`, `skills/`, …) :
   `cd cowork-plugins/<plugin> && python -m zipfile -c ../<plugin>.plugin .`
2. Dans Claude : Réglages → Capacités → ajouter le fichier `.plugin`.

## Licence

Le dépôt est sous licence MIT. Chaque skill indique sa propre licence dans l'en-tête de son `SKILL.md`
(champ `license:`) ; pour un fichier donné, c'est cette mention qui fait foi.

## Ce que cette version publique ne contient pas

Les cas d'usage, jeux d'évaluation et fiches de collecte propres aux projets privés de l'auteur ont
été retirés. Les skills renvoient parfois à des règles numérotées (`R37`, `R53`, …) : leur définition
en une ligne est dans `references/regles.md` de chaque plugin.
