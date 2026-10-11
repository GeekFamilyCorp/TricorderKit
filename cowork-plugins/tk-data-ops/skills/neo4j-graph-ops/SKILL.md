---
name: neo4j-graph-ops
description: >-
  Interroge et fait évoluer le graphe de connaissances Neo4j d'une stack locale (APOC/GDS) via le
  serveur MCP officiel neo4j/mcp : lit le schéma, formule des requêtes Cypher en LECTURE d'abord,
  propose l'écriture et ne l'exécute que sur GO, applique les patterns auteur → œuvres → adaptations
  (œuvres, auteurs, éditeurs, périodiques). À utiliser quand l'utilisateur veut « interroger
  le graphe », « quel est le schéma Neo4j », « écris-moi une requête Cypher », « relie ces fiches dans
  le graphe », « combien d'œuvres pour cet auteur », « chemins entre deux entités », « lance un
  algorithme GDS », ou pour brancher le MCP Neo4j d'un plugin. Ne pas utiliser pour une recherche
  sémantique mêlant vecteurs et graphe → graphrag-hybrid, ni pour résoudre un nom d'entité contre
  Wikidata (skill de réconciliation dédié), ni pour dédupliquer des fiches Markdown d'un vault.
license: MIT
allowed-tools: Read, Grep, Glob, Bash(python3:*), mcp__neo4j__get-schema, mcp__neo4j__read-cypher, mcp__neo4j__write-cypher, mcp__neo4j__list-gds-procedures
metadata:
  version: "0.1.0"
  author: GeekFamilyCorp
  status: public
  plugin: tk-knowledge
compatibility: Neo4j 5.x local (bolt://127.0.0.1:7687) avec APOC et GDS ; serveur MCP neo4j-mcp-server (Python 3.10+) ou binaire neo4j-mcp ; variables NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD fournies par l'environnement.
---

# neo4j-graph-ops — Le graphe, en lecture d'abord

Le graphe est la mémoire relationnelle de la stack : entités (auteurs, œuvres, éditeurs, magazines,
adaptations) et leurs liens. Une requête mal écrite en lecture coûte du temps ; une écriture mal
écrite coûte des données. D'où l'ordre : **schéma → lecture → proposition d'écriture → GO → écriture**.

## 1. Brancher le serveur MCP (une fois par plugin)

Le serveur officiel `neo4j/mcp` expose quatre tools : `get-schema`, `read-cypher`, `write-cypher`,
`list-gds-procedures`. Il se configure dans le `.mcp.json` du plugin (fourni à la racine de
`tk-knowledge`) et lit ses paramètres **uniquement** dans l'environnement :

| Variable | Rôle | Valeur |
|---|---|---|
| `NEO4J_URI` | adresse bolt | `bolt://127.0.0.1:7687` en local |
| `NEO4J_USERNAME` / `NEO4J_PASSWORD` | identifiants | jamais en clair dans un fichier versionné |
| `NEO4J_DATABASE` | base cible | `neo4j` par défaut |
| `NEO4J_READ_ONLY` | `true` désactive `write-cypher` | **`true` par défaut** ; passer à `false` seulement pour une session d'écriture décidée |

Installation : `pip install neo4j-mcp-server` (module `python -m neo4j_mcp_server`, transport stdio).
Le dépôt contient aussi un binaire Go `neo4j-mcp` (`cmd/neo4j-mcp`) ; méthode d'installation du
binaire **à vérifier** selon la plateforme. Détails et exemples : `references/mcp-neo4j.md`.

Le mot de passe vit dans le gestionnaire d'identifiants du système ou une variable de session : on ne
le lit pas, on ne l'affiche pas, on ne le colle pas dans un `.mcp.json`.

## 2. Séquence de travail

1. **Schéma d'abord** — `get-schema` avant toute requête. Les labels et types de relations réels
   priment sur ce qu'on croit savoir ; un graphe alimenté par plusieurs collecteurs dérive.
2. **Lecture** — `read-cypher` avec `LIMIT` explicite (≤ 100 par défaut) et paramètres nommés
   (`$titre`, `$id`) plutôt que des valeurs concaténées dans la chaîne.
3. **Compter avant de toucher** — pour toute modification envisagée, exécuter d'abord le `MATCH`
   correspondant avec `RETURN count(*)`. Le chiffre est annoncé à l'utilisateur.
4. **Proposer l'écriture** — présenter la requête `write-cypher` complète, le nombre de nœuds ou
   relations touchés, et la requête inverse (comment revenir en arrière). Attendre le GO.
5. **Écrire** — `MERGE` plutôt que `CREATE` (idempotence), propriétés de provenance sur chaque
   élément écrit : `source`, `collecte_le` (ISO 8601), `confiance`.
6. **Vérifier** — relire ce qui vient d'être écrit ; rendre compte avec les compteurs.

Un `DELETE` ou `DETACH DELETE` n'est jamais proposé en première intention : on marque
(`archive_le`, `remplace_par`) — principe NO-DROP. Si la suppression est vraiment demandée, elle
passe par un export préalable des éléments concernés (`references/cypher-patterns.md`, §Archivage).

## 3. Patterns du domaine

Le modèle type est **Personne → Œuvre → Adaptation**, avec éditeurs et magazines en périphérie :

```cypher
// Bibliographie d'un auteur, avec adaptations
MATCH (p:Personne {nom_jp: $nom})-[:AUTEUR_DE]->(o:Oeuvre)
OPTIONAL MATCH (o)-[:ADAPTE_EN]->(a:Adaptation)
RETURN o.titre_jp, o.titre_fr, collect(a.type) AS adaptations
ORDER BY o.debut
LIMIT 100
```

Les noms de labels ci-dessus sont **génériques** : les vrais viennent de `get-schema`. Le fichier
`references/cypher-patterns.md` rassemble les requêtes récurrentes : bibliographie, co-auteurs,
chaîne œuvre → adaptations → studio, orphelins, doublons probables par titre normalisé, provenance
d'un nœud, archivage.

## 4. GDS et APOC

`list-gds-procedures` donne ce qui est réellement installé. Les algorithmes GDS (PageRank, Louvain,
similarité de nœuds) demandent une **projection** de graphe en mémoire : la créer avec un nom daté,
la supprimer en fin de session (`gds.graph.drop`) — c'est une projection, pas une donnée. Sur un
poste partagé avec Ollama, une projection de tout le graphe peut saturer la RAM : projeter le
sous-graphe utile (labels et relations listés), jamais `*` par réflexe.

## 5. Quand le graphe ne suffit pas

- Question « sémantique » (« des œuvres qui ressemblent à … ») → `graphrag-hybrid`.
- Nom d'entité à résoudre contre une référence externe → skill de réconciliation d'entités.
- Le schéma montre des labels inattendus → les signaler, ne pas les « corriger » en silence.

## Format de réponse

1. Ce que dit le schéma (labels/relations utilisés).
2. La requête exécutée et son résultat (tableau court).
3. Si écriture proposée : requête, impact chiffré, requête inverse, **« GO ? »**.

## Changelog

- **2026-09-07 — 0.1.0** : version initiale. MCP officiel `neo4j/mcp` (4 tools, `NEO4J_READ_ONLY`),
  séquence schéma → lecture → GO → écriture, patterns auteur → œuvres → adaptations, garde-fous GDS.
