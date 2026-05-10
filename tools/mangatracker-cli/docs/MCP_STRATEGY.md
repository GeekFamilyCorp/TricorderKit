# Stratégie MCP

## Décision

Ne pas créer un MCP par cible métier au départ.

Créer d'abord un CLI robuste, puis exposer seulement quelques actions MCP :

- lancer une commande CLI ;
- lire les exports ;
- synchroniser Obsidian ;
- synchroniser kintone ;
- générer un rapport ;
- auditer les sources.

## MCP japonais retenus comme écosystème adjacent

- `kintone/mcp-server` : back-office de données et workflow.
- `cli-kintone` : import/export de records.

## Pourquoi

Le CLI est meilleur pour le batch, les exports et la limitation des appels agents. Le MCP est meilleur pour l'orchestration et la manipulation contrôlée des données validées.
