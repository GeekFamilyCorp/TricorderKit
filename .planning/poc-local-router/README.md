# PoC — Routeur SLM local (zero-token)

> Chantier **G2** de l'audit `AUDIT_INTEGRATION_5FICHIERS_2026-06.md` · DEC-022 (proposé).
> Objectif : déporter la **décision de routage** sur un petit modèle local (Ollama) au lieu
> de la facturer en tokens Claude. Le modèle facturé ne fait plus que le raisonnement final.

## Pourquoi

`model-router` et `claude-code-router` décident côté Claude → chaque décision coûte des tokens.
Ici, un SLM gratuit (Qwen 2.5 3B, < 2,5 Go RAM) choisit le **profil MCP** à charger avant de
réveiller Claude. Profils séparés ⇒ moins de « Tool Schema Bloat ».

## Pré-requis (install validée côté poste — mai 2026)

- Ollama v0.24.0 actif sur `http://localhost:11434`.
- Modèle de routage : **`qwen:1.8b`** (1.1 Go, rapide) — défaut du script.
- Embeddings (pour G3) : **`nomic-embed-text`**.
- **Aucune dépendance pip** : le routeur appelle l'API REST via `urllib` (stdlib).

```bash
# Vérifier que le serveur répond et lister les modèles
curl http://localhost:11434/api/tags
```

Variables d'environnement (optionnelles) :
- `OLLAMA_API_BASE` (défaut `http://localhost:11434`)
- `LOCAL_ROUTER_MODEL` (défaut `qwen:1.8b`)

## Utilisation

```bash
# Décision seule (n'exécute pas l'agent) — idéal pour valider le PoC
python3 local_router.py --dry-run "reprends la tâche d'hier sur les erreurs de scraping"
# -> profil = episodic

python3 local_router.py --dry-run "crée la fiche d'un nouvel éditeur dans la base"
# -> profil = domain

python3 local_router.py --dry-run "audit sécurité du dépôt et refactor du module hooks"
# -> profil = dev
```

Sans `--dry-run`, le script lance la commande agent du profil avec sa config MCP.

## Configuration

Tout est dans `profiles.json` — **aucun nom de vault ni chemin personnel en dur** :

- `default_profile` : profil de repli (utilisé si Ollama est éteint ou indécis).
- `profiles.<clé>.when` : description qui sert à orienter le SLM.
- `profiles.<clé>.mcp_config` : fichier de config MCP **filtré** à charger pour ce profil.
- `profiles.<clé>.agent_cmd` : commande de lancement de l'agent (par défaut `["claude"]`).

Créer les configs MCP par profil dans `./mcp-configs/` (un fichier par profil), ne contenant
**que** les serveurs MCP nécessaires à ce contexte de travail.

## Routage hybride (mesuré en réel, 2026-06-01)

Test sur le poste via Ollama (`qwen:1.8b`, `http://localhost:11434`) :

| Approche | Accuracy | Latence |
|---|---|---|
| SLM seul (`qwen:1.8b`) | 6/9 (0.667) | 8-33 s/appel + 40 s chargement à froid |
| **Hybride keyword→SLM** (retenu) | **9/9 (1.0)** | **~0 ms** (9/9 tranchés par mots-clés, 0 appel SLM) |

`route()` tranche d'abord par recouvrement de mots-clés (déterministe, instantané, accents
normalisés) ; le SLM n'est appelé que si la marge top1-top2 < `LOCAL_ROUTER_KEYWORD_MARGIN`
(défaut 1). Si le SLM est indisponible, repli sur le meilleur score keyword. Bug corrigé au
passage : `keep_alive=0` rechargeait le modèle à froid à chaque appel (timeout) → `keep_alive="5m"`.

> Fichiers `_*.py` / `_*_out.txt` du dossier = scripts de test/scratch (supprimables).

## Garanties de conception

- **Déterministe** : `temperature=0` + sortie contrainte par schéma JSON (`enum` strict).
- **Frugal RAM** : `keep_alive=0` décharge le modèle dès la réponse (cible i5 / 16 Go).
- **Jamais bloquant** : si Ollama est absent/éteint, repli silencieux sur `default_profile`.
- **Isolé** : aucune dépendance au code existant de TricorderKit ; suppression = sans impact.

## Étapes d'industrialisation (post-PoC)

1. Mutualiser le modèle d'embedding local (`nomic-embed-text`) avec le chantier **G3** (RAG).
2. Brancher la sortie du routeur sur le chargement réel des profils MCP de l'environnement.
3. Ajouter des tests (`pytest`) : routage déterministe sur un jeu de prompts étiquetés.
4. Logger la décision (profil + raison) vers l'observabilité (Langfuse) pour mesurer la justesse.
5. Si validé → logger DEC-022 en `Statut : Adoptée` dans `.planning/DECISIONS.md`.
