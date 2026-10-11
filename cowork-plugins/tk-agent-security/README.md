# tk-agent-security v1.0.0 — PUBLIC (MIT)

Sécurité de la surface agent : audit lecture seule de la configuration (MCP, hooks, permissions, secrets en clair, code non épinglé) et compression CLI rtk avec installation épinglée.

Regroupement du 2026-09-07 (audit `claude/AUDIT_SKILLS_PLUGINS_2026-09-07.md`, lot L4) : un plugin = un domaine d'usage.

## Skills

| Skill | Rôle |
|---|---|
| `agent-config-audit` | Audit de sécurité en lecture seule de la CONFIGURATION DE L'AGENT lui-même (pas de l'application) — serveurs MCP et leurs portées, hooks et commandes, permissions et auto-approbations d'outils, secrets en clair dans les … |
| `cli-compress` | Compresse les sorties de commandes shell verbeuses (git, npm, docker, kubectl, pytest, cargo…) avant qu'elles n'entrent dans le contexte, via le binaire rtk et le hook PreToolUse du plugin. À utiliser quand l'utilisateur men… |

## Fichiers partagés

- `references/regles.md` — définitions en une ligne des règles R.. citées par les skills (source : `RULES_REGISTRY.md` du claude-vault).
- `models.json` — alias de modèles `fast` / `default` / `deep` ; seul endroit où un identifiant de modèle est écrit.

## Retour arrière

Chaque version livrée est archivée (`plugins-2026-09-07/` v1 des anciens plugins, `plugins-2026-09-07-L4/` cette version). Revenir en arrière = désactiver ce plugin dans Réglages > Fonctionnalités et réinstaller le `.plugin` précédent. Aucune donnée n'est touchée par l'installation : les skills lisent ; ce qui écrit passe par le SAS ou par un GO explicite. NO-DROP : on désactive, on ne supprime pas.

## Changelog

### 1.0.0 — 2026-09-07
- Création par regroupement (L4) à partir de tricorderkit-skills 0.4.0 / gfc-maison-ops 1.4.0 / token-optimizer 0.3.0 ; renvois inter-skills réécrits sur les nouveaux noms de plugins ; validateur Anthropic 100 %.
