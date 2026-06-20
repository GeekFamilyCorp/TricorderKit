---
name: cli-compress
description: >
  Compresse les sorties de commandes shell longues (git, npm, docker, kubectl, pytest, etc.)
  via le proxy Rust rtk (Rust Token Killer) pour economiser 60-90% de tokens avant qu'elles
  n'atteignent le contexte. Mots-cles : "rtk", "compresse mes commandes", "trop verbeux",
  "sortie trop longue", "output bash massif", "git log trop long", "pytest verbose".
---

# CLI Compress (rtk wrapper)

Intercepte les sorties de commandes shell verbeuses et les compresse avant ingestion dans le contexte via le binaire Rust `rtk`.

## Prerequis : installer rtk une fois

Installation one-shot (sans dependance, binaire Rust seul, MIT) :

```bash
# macOS / Linux / WSL
curl -fsSL https://www.rtk-ai.app/install.sh | sh

# ou via cargo si Rust est installe
cargo install rtk
```

Puis initialiser pour Claude Code :

```bash
rtk init -g
```

Cela ajoute un hook PreToolUse qui reecrit `git status` -> `rtk git status` transparent (Claude ne voit jamais la reecriture, seulement la sortie compressee).

Le plugin inclut un script d'installation convenient : `${CLAUDE_PLUGIN_ROOT}/scripts/rtk-install.sh`.

## Commandes compressees (100+ supportees)

| Categorie | Exemples |
|-----------|---------|
| Git | `git status`, `git log`, `git diff`, `git blame`, `git show` |
| GitHub CLI | `gh pr list`, `gh run view`, `gh issue list` |
| NPM / Yarn / pnpm | `npm install`, `npm test`, `npm audit` |
| Docker | `docker ps`, `docker logs`, `docker images` |
| Kubernetes | `kubectl get`, `kubectl describe`, `kubectl logs` |
| Tests | `pytest`, `jest`, `go test`, `cargo test` |
| Build | `cargo build`, `go build`, `make` |
| Lint | `eslint`, `ruff`, `clippy` |

Liste complete : `rtk list-commands`.

## Comment rtk compresse

4 strategies appliquees dans l'ordre :

1. **Filtering** : retrait des codes ANSI, spinners, progress bars, blank lines
2. **Grouping** : consolidation de lignes similaires (ex : "10 warnings of same type -> 1 line")
3. **Deduplication** : patterns repetes compresses
4. **Truncation intelligente** : on garde errors/warnings en entier, on coupe les sorties successful verbeuses

Economie typique : **60-90%** de tokens, **<10 ms** de latence ajoutee.

## Quand activer explicitement

Le hook opere de facon transparente mais on peut aussi invoquer rtk manuellement :

```bash
rtk git log --oneline -n 100
rtk pytest tests/
rtk docker logs myapp --tail 500
```

## Desactivation ponctuelle

Si l'utilisateur a besoin de la sortie brute (debug, copier-coller) :

```bash
# bypass rtk sur une commande
RTK_OFF=1 git log

# desactiver globalement
rtk disable
```

## Integration avec model-router

Quand le router prevoit une commande shell verbeuse :

1. Verifier que rtk est installe (`which rtk`)
2. Sinon, proposer l'installation avec le script inclus
3. Laisser le hook operer transparent, ne pas re-commander

## Economie cumulee estimee

Sur 100 commandes dev typiques :

- Sans rtk : ~400 000 tokens
- Avec rtk : ~80 000 tokens
- Economie : **~320 000 tokens/semaine** pour un developpeur actif

## References

- Source : https://github.com/rtk-ai/rtk
- Site officiel : https://www.rtk-ai.app/
- License : MIT, pas de phoning home, binaire auto-contenu
