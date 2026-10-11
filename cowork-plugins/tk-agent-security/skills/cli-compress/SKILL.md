---
name: cli-compress
description: >
  Compresse les sorties de commandes shell verbeuses (git, npm, docker, kubectl, pytest, cargo…) avant
  qu'elles n'entrent dans le contexte, via le binaire rtk et le hook PreToolUse du plugin. À utiliser
  quand l'utilisateur mentionne « rtk », « sortie trop longue », « output bash massif », « git log trop long »,
  « pytest verbose », ou avant une session riche en commandes shell pour vérifier que rtk est installé.
  Ne pas utiliser pour compresser de la prose ou un contexte de conversation (→ caveman, context-compress),
  et ne jamais installer rtk sans GO explicite.
license: MIT
metadata:
  version: "2.0"
  updated: "2026-09-07"
  author: GeekFamilyCorp
---

# CLI Compress (rtk)

Le hook `PreToolUse/Bash` du plugin (`hooks/hooks.json` → `scripts/rtk-rewrite.sh`) préfixe par `rtk` les commandes supportées **si et seulement si** le binaire est présent. Sans rtk, il laisse passer la commande inchangée : rien à configurer.

## Vérifier

```bash
command -v rtk && rtk --version || echo "rtk absent : hook inactif"
```

## Installer (après GO de l'utilisateur — R53)

Installation épinglée uniquement, jamais `curl | sh` :

```bash
cargo install rtk --version <VERSION_A_EPINGLER> --locked
```

Sans Rust : `bash ${CLAUDE_PLUGIN_ROOT}/scripts/rtk-install.sh` (binaire de release + vérification SHA-256 ; le script refuse d'installer tant que version et checksums ne sont pas renseignés).

**Ne PAS lancer `rtk init -g`** : ce serait un second hook sur les mêmes commandes. Le plugin n'a qu'un mécanisme, `hooks/hooks.json`.

## Utiliser

- Transparent : une fois rtk présent, `git status`, `npm test`, `docker logs` sont réécrits par le hook.
- Manuel : `rtk <commande>` pour une commande hors liste.
- Sortie brute nécessaire (debug, copier-coller) : `RTK_OFF=1 <commande>` ; le hook respecte la variable.

Détails, liste des commandes, stratégies de compression, désactivation globale : `references/rtk.md`.

## Changelog

- 2026-09-07 — v2.0 : installation épinglée avec checksum, un seul mécanisme de hook, chiffres non mesurés retirés, doc rtk déplacée en `references/rtk.md`.
- 2026-04 — v1.x : wrapper rtk initial (`curl | sh` + `rtk init -g`).
