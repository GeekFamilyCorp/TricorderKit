# rtk (Rust Token Killer) — aide-mémoire

Source : https://github.com/rtk-ai/rtk · site : https://www.rtk-ai.app/ · licence MIT, binaire auto-contenu.
Chiffres d'économie : voir la page du projet ; aucun chiffre n'a été mesuré par GeekFamilyCorp.

## Installation épinglée (jamais `curl | sh`)

```bash
cargo install rtk --version <VERSION_A_EPINGLER> --locked
# ou : bash ${CLAUDE_PLUGIN_ROOT}/scripts/rtk-install.sh  (binaire de release + SHA-256, variables à renseigner)
```

Ne PAS lancer `rtk init -g` : ce plugin installe déjà son hook PreToolUse (`hooks/hooks.json` →
`scripts/rtk-rewrite.sh`). Deux hooks sur les mêmes commandes se marcheraient dessus. R53 : l'installation
elle-même attend le GO de l'utilisateur.

## Commandes couvertes par le hook du plugin

`git gh npm yarn pnpm docker kubectl pytest jest cargo go make eslint ruff clippy` (liste dans
`scripts/rtk-rewrite.sh` ; liste complète côté rtk : `rtk list-commands`).

## Stratégies de compression de rtk

1. Filtrage : codes ANSI, spinners, barres de progression, lignes vides.
2. Regroupement : lignes similaires consolidées.
3. Déduplication : motifs répétés.
4. Troncature : erreurs et avertissements gardés entiers, sorties de succès verbeuses coupées.

## Invocation manuelle

```bash
rtk git log --oneline -n 100
rtk pytest tests/
rtk docker logs myapp --tail 500
```

## Désactivation

```bash
RTK_OFF=1 git log      # bypass sur une commande (respecté par le hook du plugin)
rtk disable            # désactivation globale côté rtk
```
