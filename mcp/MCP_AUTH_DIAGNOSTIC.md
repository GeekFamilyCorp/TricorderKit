# MCP Auth Diagnostic — Protocole de résolution rapide

> **Origine** : Post-mortem session 2026-05-11.  
> Erreur d'authentification GitHub MCP résolue en ~3h alors que la cause
> (mauvais nom de variable d'environnement) aurait pu être trouvée en 30 secondes.  
> Ce document empêche de répéter ce pattern.

---

## Post-mortem : la boucle d'erreur

| Étape | Action tentée | Temps | Résultat |
|-------|--------------|-------|----------|
| 1 | Test écriture MCP → 401 | — | Échec |
| 2 | Supposé token invalide/révoqué | 20 min | ❌ Mauvaise piste |
| 3 | Vérifié/édité le fichier config | 15 min | Token présent mais ignoré |
| 4 | Redémarré Claude × 4 | 40 min | ❌ Toujours 401 |
| 5 | Supposé token révoqué par GitHub secret scanning | 15 min | ❌ Mauvaise piste |
| 6 | Régénéré un nouveau token | 20 min | ❌ Toujours 401 |
| 7 | Identifié le bon chemin MSIX | 15 min | Progrès partiel |
| **8** | **Lu le source MCP (`utils.js`)** | **2 min** | **✅ Cause trouvée** |

**Cause réelle** : la config utilisait `GITHUB_TOKEN` mais le MCP attendait `GITHUB_PERSONAL_ACCESS_TOKEN`.  
**L'étape 8 aurait dû être l'étape 2.**

---

## Protocole — Erreur 401 / "Requires authentication" sur un MCP

### ÉTAPE 1 — Lire le code source du MCP immédiatement

C'est la **première action**, pas la dernière.

Localiser le fichier `utils.js` ou `index.js` du MCP dans le cache npx :

```
# Windows (Claude Desktop MSIX)
C:\Users\<user>\AppData\Local\npm-cache\_npx\<hash>\node_modules\@modelcontextprotocol\server-<nom>\dist\

# Exemple pour server-github :
C:\Users\<username>\AppData\Local\npm-cache\_npx\3dfbf5a9eea4a1b3\node_modules\@modelcontextprotocol\server-github\dist\common\utils.js
```

Chercher `process.env.` dans ce fichier pour trouver le **nom exact** attendu :

```javascript
// Ce qu'on cherche dans le source :
if (process.env.GITHUB_PERSONAL_ACCESS_TOKEN) {   // ← nom exact
    headers["Authorization"] = `Bearer ${process.env.GITHUB_PERSONAL_ACCESS_TOKEN}`;
}
```

> **Règle d'or** : ne jamais supposer le nom de la variable. Le lire dans le source.

---

### ÉTAPE 2 — Vérifier que la config utilise exactement ce nom

Sur **Claude Desktop Windows (MSIX)**, le vrai chemin du fichier config est :

```
# ✅ Chemin réel (MSIX sandbox)
C:\Users\<username>\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json

# ❌ Chemin apparent (redirigé, ne reflète pas toujours l'état réel)
C:\Users\<username>\AppData\Roaming\Claude\claude_desktop_config.json
```

Vérifier que la clé `env` contient **exactement** le nom trouvé à l'étape 1 :

```json
// ❌ Mauvais — ignoré silencieusement
"env": { "GITHUB_TOKEN": "ghp_..." }

// ✅ Correct
"env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..." }
```

---

### ÉTAPE 3 — Vérifier la valeur du token

- La valeur n'est pas un placeholder (`COLLER_VOTRE_TOKEN_ICI`, `YOUR_TOKEN_HERE`, `***`)
- Le token n'est pas expiré → vérifier sur `github.com/settings/tokens`
- Le token a les bons scopes :
  - Écriture GitHub : scope `repo` (pas seulement `public_repo`)

---

### ÉTAPE 4 — Redémarrer Claude complètement

**Une seule fois**, après avoir corrigé la config. Pas avant.

- Windows : clic droit icône barre des tâches système → **Quitter**  
  (pas juste fermer la fenêtre — le process MCP doit être tué)
- Relancer Claude Desktop
- Le MCP recharge les variables d'environnement depuis la config au démarrage

---

### ÉTAPE 5 — Retester

Si toujours 401 après ces 4 étapes → le token lui-même est invalide.  
Régénérer sur GitHub et reprendre à l'étape 2.

---

## Référence : variables d'environnement des MCPs courants

| MCP package | Variable attendue | Vérifié le | Statut |
|-------------|------------------|------------|--------|
| `@modelcontextprotocol/server-github` | `GITHUB_PERSONAL_ACCESS_TOKEN` | 2026-05-11 | ❌ Déprécié (avril 2025) |
| `ghcr.io/github/github-mcp-server` (Docker) | `GITHUB_PERSONAL_ACCESS_TOKEN` | 2026-05-17 | ✅ Officiel actif |

> Mettre à jour ce tableau à chaque nouveau MCP ajouté au projet.

---

## KI-003 — Migration GitHub MCP (résolu le 17/05/2026)

**Problème** : `@modelcontextprotocol/server-github` déprécié en avril 2025. Développement déplacé vers `github/github-mcp-server`.

**Solution appliquée** : migration vers l'image Docker officielle `ghcr.io/github/github-mcp-server`.

Config dans `claude_desktop_config.json` (chemin MSIX réel) :

```json
"github": {
  "command": "docker",
  "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "<TOKEN>"
  }
}
```

**Prérequis** : Docker Desktop actif. La variable `GITHUB_PERSONAL_ACCESS_TOKEN` est inchangée.

**Redémarrage Claude Desktop requis** après modification de la config.

**Changement de nommage des outils** (important) : le nouveau serveur expose des outils regroupés.

| Ancien outil (`server-github`) | Nouvel outil (`github-mcp-server`) |
|---|---|
| `get_issue` / `list_issues` / `create_issue` | `issue_read` / `issue_write` |
| `get_pull_request` / `list_pull_requests` | `pull_request_read` |
| `create_pull_request_review` | `pull_request_review_write` |
| `get_me` | `get_me` (inchangé) |
| `list_commits` / `get_commit` | `get_commit` / `list_branches` |
| `search_issues` / `search_repositories` | `issue_read` (filtres intégrés) |

**Vérifié le 17/05/2026** — `get_me` retourne `GeekFamilyCorp` ✅

---

## Sécurité des tokens

### Ne jamais partager un token en clair dans le chat

GitHub scanne automatiquement les conversations et révoque les tokens détectés.  
Un token partagé dans le chat doit être considéré **compromis immédiatement**.

**Si ça arrive :**
1. Aller sur `github.com/settings/tokens`
2. Révoquer le token exposé
3. En générer un nouveau
4. Mettre à jour la config

### Règle `.env` / config

- Les tokens vont dans `.env` (jamais commité — voir `.gitignore`)
- La config `claude_desktop_config.json` n'est pas versionnée
- Ne jamais logger un token dans un fichier de doc ou de vault

---

## Lien avec l'architecture MSIX (Windows)

Claude Desktop est packagé en MSIX sur Windows. Cela crée une **asymétrie de chemins** :

| Vue | Chemin |
|-----|--------|
| Apparent (`%APPDATA%`) | `C:\Users\<username>\AppData\Roaming\Claude\` |
| Réel (MSIX sandbox) | `C:\Users\<username>\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\` |

Les outils externes (scripts, PowerShell, outils tiers) **doivent utiliser le chemin réel** pour lire ou écrire la config.

---

## Références

- `mcp/README_MCP_POLICY.md` — politique générale d'usage des MCPs
- `.mcp.json` — configuration MCP du projet
- `.env.example` — variables d'environnement requises
