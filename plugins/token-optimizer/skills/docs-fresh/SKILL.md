---
name: docs-fresh
description: >
  Injecte la documentation officielle a jour de toute bibliotheque ou framework via le MCP Context7 (Upstash), pour eviter les hallucinations d'API et le code obsolete. Mots-cles : "use context7", "docs a jour", "verifie la doc officielle", "documentation fraiche", "API de X", "signature de X", "comment utiliser [lib]", "la derniere version de [framework]".
---

# Docs Fresh (Context7 wrapper)

Declenche l'injection de docs fraiches via le serveur MCP Context7 quand une tache implique une bibliotheque, un framework ou une API externe.

## Prerequis

Le serveur MCP Context7 doit etre declare dans `.mcp.json` du plugin (cf `${CLAUDE_PLUGIN_ROOT}/.mcp.json`). Il est inclus par defaut dans ce plugin.

Pour le configurer manuellement en dehors du plugin :

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

## Quand declencher

- L'utilisateur mentionne une bibliotheque precise : React, Next.js, Vue, FastAPI, Django, Supabase, Prisma, TanStack Query, Zod, Langchain, Anthropic SDK, etc.
- L'utilisateur demande "comment utiliser X", "l'API de X", "la signature de X"
- Je m'apprete a ecrire du code utilisant une API tiers
- L'utilisateur ecrit explicitement **"use context7"** dans son prompt

## Procedure

1. **Resoudre l'ID de la bibliotheque** via l'outil MCP `resolve-library-id` :

   ```
   resolve-library-id({ libraryName: "Next.js" })
   ```

   Retour : `/vercel/next.js`

2. **Recuperer les docs pertinentes** via `query-docs` :

   ```
   query-docs({
     libraryId: "/vercel/next.js",
     query: "server actions with form validation"
   })
   ```

3. **Integrer le snippet** dans la reponse ou le contexte du sous-agent.

## Benefices token

D'apres Upstash, Context7 :

- Reduit le contexte moyen de **65%** vs injection massive de docs
- Reduit la latence de **38%**
- Elimine les hallucinations d'API (APIs inexistantes, parametres obsoletes)

## Bonnes pratiques

- **Formuler la requete de facon ciblee** : "useEffect cleanup pattern" plutot que "react docs"
- **Combiner avec model-router** : meme avec docs fraiches, une implementation critique passe par Opus
- **Cacher localement** : Context7 gere son propre cache cote serveur, ne pas re-requeter dans le meme tour
- **Tomber gracieusement** : si Context7 est indisponible, prevenir l'utilisateur et proposer la recherche web comme fallback

## Exemples de prompts utilisateur qui declenchent ce skill

- "Ecris un hook React pour l'infinite scroll avec TanStack Query" (lib = TanStack Query)
- "Comment configurer RLS dans Supabase ?" (lib = Supabase)
- "use context7 : quelle est la signature actuelle de messages.create() dans le SDK Anthropic ?"
- "Migration Next.js 14 vers 15, quoi checker ?"

## References

- Source : https://github.com/upstash/context7
- Blog : https://upstash.com/blog/new-context7
- Package NPM : `@upstash/context7-mcp`
