# 08 — Context Policy

> Sémantique des **politiques de stockage** et de **confidentialité** appliquées aux sources
> de contexte (`.tricorderkit/context_sources.yaml`). C'est le garde-fou qui empêche d'aspirer
> du contenu sensible ou volatil dans la mémoire durable / le repo public.

## Politiques de stockage (`storage_policy`)

| Valeur | Sens | Quand l'utiliser |
|---|---|---|
| `store` | Conserver intégralement, durable | Faits stables qui font autorité (décisions, concepts, profil) |
| `summarize` | Ne garder qu'un résumé daté | Sources volatiles (état projet, veille, recherche web) |
| `pointer_only` | Garder une **référence**, jamais le contenu | Contenu métier / vault de domaine (hors repo public) |
| `do_not_store` | Ne jamais persister | Secrets, tokens, données personnelles sensibles |

## Niveaux de confidentialité (`privacy_level`)

| Niveau | Définition | Conséquence |
|---|---|---|
| `public` | Publiable tel quel | OK repo public |
| `internal` | Interne projet, anonymisable | Repo public seulement si anonymisé (gate R37) |
| `private` | Personnel / métier / secret | **Jamais** dans le repo public — référence uniquement |

## Rafraîchissement (`refresh_policy`)

`never` · `on_change` · `daily` · `weekly` · `on_demand`. Une source `dynamic` sans
`refresh_policy` est traitée comme périmable : la résumer plutôt que s'y fier.

## Décision de routage (pseudo-algorithme)

```
1. Détecter l'intention de la requête.
2. memory_router.yaml : intention -> source.
3. context_sources.yaml : source -> (type, storage_policy, privacy_level, refresh_policy).
4. Si privacy_level=private ET cible=repo public -> pointer_only / do_not_store.
5. Si type=dynamic -> préférer summarize + vérifier refresh_policy.
6. Charger UNE source pertinente (pas un dump) ; déléguer au module propriétaire.
```

## Garde-fous (rappel)

- **R37 / DEC-016** : le repo public ne contient ni contenu métier, ni secret, ni chemin personnel.
- **`do_not_store`** est non négociable pour tout ce qui touche aux secrets (réf. credential manager).
- Cette politique **n'écrit jamais** elle-même : elle informe le routage. La capture validée passe
  par les skills dédiés (`tk-grill` pour une décision, `memory-boot` pour le hot cache).
