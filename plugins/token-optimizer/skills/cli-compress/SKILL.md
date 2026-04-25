---
name: cli-compress
description: >
  Compresse les sorties de commandes shell longues (git, npm, docker, kubectl, pytest, etc.)
  via le proxy Rust rtk (Rust Token Killer) pour economiser 60-90% de tokens avant qu'elles
  n'atteignent le contexte. Mots-cles : "rtk", "compresse mes commandes", "trop verbeux",
  "sortie trop longue", "output bash massif", "git log trop long", "pytest verbose".
---

# CLI Compress (rtk wrapper)

Intercepts les sorties de commandes shell verbeuses et les compresse avant ingestion dans le contexte via le binaire Rust `rtk`.

## Prerequis : installer rtk une fois

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

## Commandes compressees (100+ supportees)

| Categorie | Exemples |
|-----------|----------|
| Git | `git status`, `git log`, `git diff`, `git blame` |
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
2. **Grouping** : consolidation de lignes similaires
3. **Deduplication** : patterns repetes compresses
4. **Truncation intelligente** : garde errors/warnings en entier, coupe les sorties successful verbeuses

Economie typique : **60-90%** de tokens, **<10 ms** de latence ajoutee.

## Utilisation manuelle

```bash
rtk git log --oneline -n 100
rtk pytest tests/
rtk docker logs myapp --tail 500
```

## Desactivation ponctuelle

```bash
# bypass rtk sur une commande
RTK_OFF=1 git log

# desactiver globalement
rtk disable
```

## References

- Source : https://github.com/rtk-ai/rtk
- Site officiel : https://www.rtk-ai.app/
- License : MIT
