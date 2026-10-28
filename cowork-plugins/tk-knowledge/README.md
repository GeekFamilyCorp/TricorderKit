# tk-knowledge v1.0.0 — PUBLIC (MIT)

Méta-compétences TricorderKit : gestion et audit de l'écosystème de skills (skill-manager), evals de skills (skill-evals), transformation de documentation en skill (doc-to-skill), orchestration de livrables non-code (head-agent).

Regroupement du 2026-09-07 (audit `claude/AUDIT_SKILLS_PLUGINS_2026-09-07.md`, lot L4) : un plugin = un domaine d'usage.

## Skills

| Skill | Rôle |
|---|---|
| `doc-to-skill` | Transforme une source documentaire (README, doc, PDF, DOCX, page web, dépôt) en un brouillon de SKILL.md prêt à relire OU en fiche de connaissance, avec checklist de frontmatter et détection de doublon vs les skills exis… |
| `head-agent` | Orchestrateur multi-agents pour les LIVRABLES NON-CODE : recherche + synthèse, rapports, audits, veilles, dossiers structurés. Découpe une tâche trop large ou hétérogène en sous-tâches déléguées à des sous-agents via l'o… |
| `skill-evals` | Écrit, exécute et consigne les jeux d'evals des skills critiques de l'utilisateur (déclenchement, non-déclenchement, qualité, régression, token-hygiene) au format natif de skill-creator (evals.json + triggers.json), avec con… |
| `skill-manager` | Gestionnaire centralisé des skills et plugins Claude Cowork installés : inventaire multi-racines (skills autonomes, plugins, anciennes surfaces), health check à 8 critères appuyé sur quick_validate.py, détection de confl… |

## Fichiers partagés

- `references/regles.md` — définitions en une ligne des règles R.. citées par les skills (source : `RULES_REGISTRY.md` du claude-vault).
- `models.json` — alias de modèles `fast` / `default` / `deep` ; seul endroit où un identifiant de modèle est écrit.

## Retour arrière

Chaque version livrée est archivée (`plugins-2026-09-07/` v1 des anciens plugins, `plugins-2026-09-07-L4/` cette version). Revenir en arrière = désactiver ce plugin dans Réglages > Fonctionnalités et réinstaller le `.plugin` précédent. Aucune donnée n'est touchée par l'installation : les skills lisent ; ce qui écrit passe par le SAS ou par un GO explicite. NO-DROP : on désactive, on ne supprime pas.

## Changelog

### 1.0.0 — 2026-09-07
- Création par regroupement (L4) à partir de tricorderkit-skills 0.4.0 / gfc-maison-ops 1.4.0 / token-optimizer 0.3.0 ; renvois inter-skills réécrits sur les nouveaux noms de plugins ; validateur Anthropic 100 %.
