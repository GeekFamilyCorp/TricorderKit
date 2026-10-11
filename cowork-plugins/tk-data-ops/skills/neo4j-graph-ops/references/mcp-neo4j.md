# Serveur MCP officiel Neo4j — fiche de branchement

Source vérifiée le 2026-09-07 : `github.com/neo4j/mcp` (README) et `neo4j.com/docs/mcp/current/client-configuration/`.

## Ce qui est confirmé

- Dépôt hybride : cœur **Go** (`cmd/neo4j-mcp`, `go.mod`, goreleaser) + paquet **PyPI**
  `neo4j-mcp-server` documenté comme méthode d'installation principale.
- Transport : **stdio**.
- Tools exposés : `get-schema`, `read-cypher`, `write-cypher`, `list-gds-procedures`.
- Variables d'environnement : `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` (requises) ;
  `NEO4J_DATABASE` (défaut `neo4j`), `NEO4J_READ_ONLY` (`true` → tools d'écriture désactivés),
  `NEO4J_TELEMETRY`, `NEO4J_LOG_LEVEL`, `NEO4J_LOG_FORMAT`, `NEO4J_SCHEMA_SAMPLE_SIZE`.

## À vérifier

- Licence exacte du dépôt (fichiers `LICENSE.txt` + `NOTICE.txt` présents, nom non lu).
- Installation du binaire Go (`go install github.com/neo4j/mcp/cmd/neo4j-mcp@latest` ? release
  GitHub ? image Docker ?) — non documentée sur la page client-configuration.
- Support de la syntaxe `${VAR:-défaut}` dans le `.mcp.json` d'un plugin Claude Code (la forme
  `${VAR}` est sûre ; si le défaut n'est pas honoré, définir la variable explicitement).

## Configuration plugin (`.mcp.json`, à la racine de tk-knowledge)

```json
{
  "mcpServers": {
    "neo4j": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "neo4j_mcp_server"],
      "env": {
        "NEO4J_URI": "${NEO4J_URI}",
        "NEO4J_USERNAME": "${NEO4J_USERNAME}",
        "NEO4J_PASSWORD": "${NEO4J_PASSWORD}",
        "NEO4J_DATABASE": "${NEO4J_DATABASE:-neo4j}",
        "NEO4J_READ_ONLY": "${NEO4J_READ_ONLY:-true}",
        "NEO4J_TELEMETRY": "false"
      }
    }
  }
}
```

Variante binaire : `"command": "neo4j-mcp"`, sans `args`.

## Fournir les variables sans les écrire

- Windows : Credential Manager + un lanceur qui exporte les variables dans la session du client
  (jamais dans un fichier du dépôt).
- Linux/macOS : `direnv` avec `.envrc` ignoré par git, ou le trousseau du système.
- Test de présence sans affichage : `python -c "import os,sys; sys.exit(0 if os.environ.get('NEO4J_PASSWORD') else 1)"`.

## Test de branchement

1. Démarrer le client ; demander « liste les tools MCP Neo4j » → 4 tools attendus (3 si `READ_ONLY`).
2. `get-schema` → doit retourner labels et relations.
3. `read-cypher` : `RETURN 1 AS ok`.
4. `write-cypher` doit être absent ou refusé tant que `NEO4J_READ_ONLY=true`.

## Neo4j local : rappels

- Port bolt 7687, navigateur 7474, tout en 127.0.0.1 (pas d'exposition LAN).
- APOC et GDS sont des plugins du conteneur ; `list-gds-procedures` confirme leur présence réelle.
- Un conteneur arrêté ne s'annonce pas : en cas d'erreur de connexion, vérifier l'état du service
  avant de suspecter la configuration.
