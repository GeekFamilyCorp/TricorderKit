# Exemple de référence — `rileylemm/graphrag-hybrid` (vault Markdown à frontmatter)

Vérifié le 2026-09-07 sur le README du dépôt `github.com/rileylemm/graphrag-hybrid` (licence MIT).
Le nom exact du dépôt contient un **tiret** (`graphrag-hybrid`), pas un underscore ; le dépôt frère
`rileylemm/graphrag_mcp` porte le serveur MCP.

## Ce que fait le dépôt

Système de récupération hybride pour une **documentation Markdown structurée par frontmatter
YAML** : Neo4j stocke les métadonnées, les relations et la hiérarchie de catégories ; Qdrant stocke
les embeddings des chunks (collection `document_chunks`). Trois modes : vectoriel, graphe, hybride.
Serveur MCP séparé pour interroger depuis un assistant.

| Élément | Valeur confirmée |
|---|---|
| Services Docker | Neo4j (7474 / 7687), Qdrant (6333) |
| Python | 3.9+ |
| Embeddings | modèles transformers Hugging Face (nom précis **à vérifier** dans le code) |
| LLM | non spécifié dans le README (**à vérifier**) |
| Points d'entrée | `scripts/import_docs.py`, `scripts/query_demo.py`, `test_db_connection/test_connections.py`, `AI_ENTRY.md` |
| Frontmatter attendu | `title` (requis), `category` (requis), `updated`, `related`, `key_concepts` (optionnels) |
| Taille des chunks, labels Neo4j exacts | non documentés dans le README (**à vérifier** dans le code) |

## Pourquoi c'est le même cas qu'un vault de fiches culturelles

Un vault de fiches (projets, personnes, organisations) est aussi un ensemble de Markdown à frontmatter,
avec des liens entre fiches. La correspondance est directe :

| Dépôt rileylemm | Vault de fiches |
|---|---|
| `title` | `titre` / `nom_alias` |
| `category` (hiérarchie) | `type` (projet, personne, organisation) |
| `related` (liens entre documents) | liens `[[wiki]]`, `related_ids`, `auteur`, `versions` |
| `key_concepts` | `tags`, genres |
| `updated` | `maj_le` |
| collection `document_chunks` | une collection par type de fiche, ou une seule avec `type` en payload |

## Ce qui se transpose tel quel

- **Séparation des rôles** : le graphe porte les métadonnées et les liens, Qdrant porte le texte
  découpé. Ne pas dupliquer le corps du texte dans Neo4j.
- **Import idempotent depuis le Markdown** : le script d'import relit tout le dossier et fait un
  upsert ; c'est le bon modèle pour une ré-indexation par lot (R65).
- **Trois modes exposés côté MCP** : laisser à l'appelant le choix vectoriel / graphe / hybride,
  plutôt que d'imposer l'hybride partout.
- **Test de connexions** avant l'import (`test_connections.py`) : un service arrêté ne s'annonce pas.

## Ce qui ne se transpose pas

- **Identifiant de jointure** : le dépôt s'appuie sur le titre / le chemin ; un vault de fiches doit
  utiliser son **identifiant de frontmatter** (`id: PR0123`), stable au renommage. C'est le point
  n° 1 de `SKILL.md` §3.
- **Embeddings Hugging Face directs** : dans une stack Ollama, l'embedding passe par Ollama
  (`OllamaEmbeddings`) pour n'avoir qu'un seul serveur de modèles à surveiller. Choisir un modèle
  d'embedding multilingue (le corpus mêle FR, EN, DE) et vérifier sa dimension avant de créer la
  collection.
- **Relations typées** : `related` est un lien générique ; un graphe de connaissances a besoin de relations
  nommées (`AUTEUR_DE`, `PUBLIE_EN`, `SOUTENU_PAR`) pour que la requête de voisinage explique
  quelque chose. Les dériver des champs de frontmatter, pas d'un champ fourre-tout.
- **Bibliothèque** : le dépôt a son propre code de récupération ; la version TricorderKit s'appuie
  sur `neo4j-graphrag` (`QdrantNeo4jRetriever`) pour ne pas maintenir un retriever maison.

## Lecture recommandée avant d'adapter

1. `AI_ENTRY.md` puis `scripts/import_docs.py` (modélisation réelle des nœuds et relations).
2. `scripts/query_demo.py` (comment le mode hybride fusionne les deux résultats).
3. `guides/mcp/` pour les tools exposés, à comparer avec le `.mcp.json` de `tk-knowledge`.
