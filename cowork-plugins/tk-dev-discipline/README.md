# tk-dev-discipline v1.0.0 — PUBLIC (MIT)

Discipline de développement TricorderKit : cadrage (interview-me), protocole spec→plan→sous-agents→tests→ship (dev-protocol), revue adverse (doubt-driven-development), débogage par cause racine, correction/durcissement web OWASP (code-corrector), observabilité des automatisations.

Regroupement du 2026-09-07 (audit `claude/AUDIT_SKILLS_PLUGINS_2026-09-07.md`, lot L4) : un plugin = un domaine d'usage.

## Skills

| Skill | Rôle |
|---|---|
| `code-corrector` | Corrige et durcit le code d'une application web de façon disciplinée et mesurée. À utiliser quand l'utilisateur veut corriger les bugs d'une web app, faire un audit de sécurité (OWASP Top 10 : injections, XSS, CSRF, cont… |
| `debugging-and-error-recovery` | Débogage discipliné par cause racine pour scripts Python, VPS (systemd/Docker/SFTP), pipelines de veille et automatisations maison. À utiliser quand un test échoue, un build casse, un timer ou une tâche planifiée ne prod… |
| `dev-protocol` | Applique un protocole de développement discipliné à une tâche non triviale : brainstorm socratique → spec courte → plan écrit avec checkpoints → implémentation incrémentale par sous-agents avec revue à deux étages (confo… |
| `doubt-driven-development` | Soumet une décision non triviale à une revue adverse à contexte frais AVANT de la valider — trois modes d'échec concrets, recoupement sur la source réelle, réversibilité vérifiée, dry-run. À utiliser quand la justesse pr… |
| `interview-me` | Extrait ce que l'utilisateur veut réellement par un entretien une-question-à-la-fois (outil AskUserQuestion), jusqu'à ~95 % de confiance sur l'intention, le périmètre, les contraintes, le critère de réussite et le format de … |
| `observability-and-instrumentation` | Rend le comportement des automatisations VISIBLE et diagnosticable — logs structurés JSON, compteurs de fin de run, heartbeats, alertes sur seuil — pour les timers systemd, tâches planifiées, pipelines de veille et scrip… |

## Fichiers partagés

- `references/regles.md` — définitions en une ligne des règles R.. citées par les skills (source : `RULES_REGISTRY.md` du claude-vault).
- `models.json` — alias de modèles `fast` / `default` / `deep` ; seul endroit où un identifiant de modèle est écrit.

## Retour arrière

Chaque version livrée est archivée (`plugins-2026-09-07/` v1 des anciens plugins, `plugins-2026-09-07-L4/` cette version). Revenir en arrière = désactiver ce plugin dans Réglages > Fonctionnalités et réinstaller le `.plugin` précédent. Aucune donnée n'est touchée par l'installation : les skills lisent ; ce qui écrit passe par le SAS ou par un GO explicite. NO-DROP : on désactive, on ne supprime pas.

## Changelog

### 1.0.0 — 2026-09-07
- Création par regroupement (L4) à partir de tricorderkit-skills 0.4.0 / gfc-maison-ops 1.4.0 / token-optimizer 0.3.0 ; renvois inter-skills réécrits sur les nouveaux noms de plugins ; validateur Anthropic 100 %.
