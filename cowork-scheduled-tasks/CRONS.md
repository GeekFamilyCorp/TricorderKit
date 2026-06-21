# Tâches planifiées Cowork — manifeste des crons (2026-06-21)

Sauvegarde des prompts (`<id>/SKILL.md`) + des plannings. Le registre des crons vit dans l'app Claude
(effacé à la réinstallation) — **réinjecter les crons ci-dessous** via le planificateur Cowork après réinstall.
Les prompts, eux, sont ici (réinstallables).

## Actives (8 + agent hebdo)
| Tâche | Cron (heure locale poste) | Rôle |
|---|---|---|
| analyse-japan-alliance | `0 2 * * *` | bilan nuit Japan-Alliance (T2/Sonnet) |
| ops-monitor | `30 3,9,15,21 * * *` | sonde bus canal_agents + sessions Cowork (T1/Haiku) — FUSION coordination+dispatch |
| pipeline-quarantaine | `30 5,13,20 * * *` | promote VPS→quarantaine + modération (T2/Sonnet) — FUSION promote+backlog |
| japan-alliance-tricorderkit-7h30 | `30 7 * * *` | rapport matinal Ollama (T1/Haiku) |
| rollout-japan-alliance | `0 12 * * *` | graduation fiches au canon (GO humain) |
| veille-quotidienne-japon | `0 23 * * *` | contrôle QA veille |
| weekly-ecosystem-audit | `0 4 * * 0` | grand audit écosystème (dimanche) |
| weekly-news-digest | `0 8 * * 1` | digest hebdo (lundi) |
| vps-model-scout | `30 10 * * 3` | veille + test sandbox LLM/SLM sur le VPS (mercredi) — proposition only |

## Désactivées (fusionnées/terminées — conservées pour historique)
- coordination-agents, dispatch-task-monitor → fusionnées dans **ops-monitor**
- ja_promotequarantine, backlog-japan-alliance-4h → fusionnées dans **pipeline-quarantaine**
- watch-fiches-fill-deliverable → tâche one-day du 20/06 terminée

## One-time périmées (historique, ne pas réactiver)
- calibrate-quota-governor (14/06), codex-retour-quota (19/06), rappel-plafonds-quota-governor (13/06), investig-limites-gemini-antigravity (17/06)

> Note : le planificateur applique un léger jitter de quelques minutes au dispatch. Voir aussi la mémoire
> persistante Cowork `scheduled-tasks-crons.md` (source de vérité des crons).
