# Exemple — grill du workflow Temporal `vault_audit`

> Sujet : design de `plugins/workflow-engine/workflows/vault_audit.workflow.ts` (statut TASKS = pending).
> Démo abrégée du protocole (une question à la fois, réponse recommandée à chaque nœud).

**Pré-vol** — DECISIONS.md lu : aucun DEC ne tranche déjà l'audit vault ; DEC-016 fixe le routage ;
DEC-028 a posé le gate docs-sync (à ne pas dupliquer). STATE = Phase 4. Risk Guard estimé : **MEDIUM**.

**Q1 (Cadrage).** Que doit *prouver* l'audit vault, concrètement, qu'un test pytest ne prouve pas déjà ?
> Reco : cohérence taxonomique + dédup d'ID + frontmatter valide sur le vault le domaine (non versionné, donc hors CI). C'est le vrai gap (cf. dérive taxonomie). Sinon, redondant avec docs-sync.

**Q2 (Existant).** `obsidian-goat` ou un script couvre-t-il déjà une partie du scan ? → *exploration repo plutôt que question.*
> Constat : `plugins/cli-forge/generated/obsidian-goat/` est pending lui aussi. Donc l'audit en dépend → dépendance amont à résoudre d'abord.

**Q3 (CLI vs LLM).** Le scan est-il déterministe (donc CLI) ou nécessite-t-il du raisonnement (LLM) ?
> Reco : 100 % CLI déterministe (lecture FS + parse YAML + comparaison d'IDs). Le workflow Temporal orchestre des **activités CLI**, aucun appel LLM dans le chemin chaud. Respecte « CLI avant LLM ».

**Q4 (Contrat).** La sortie respecte-t-elle `skill_output.schema.json` ?
> Reco : oui — l'activité `run_cli` émet le JSON contractuel ; le workflow agrège en un rapport conforme.

**Q5 (Routage).** Quel dépôt ? → DEC-016.
> Reco : le **workflow + activités** = TricorderKit (moteur générique) ; les **fiches auditées** = le domaine (lecture seule). Aucun écrit vault depuis le workflow.

**Q6 (Sûreté).** Dry-run et réversibilité ?
> Reco : audit en **lecture seule par construction** (rapport only). Toute correction proposée passe par un second acte `--apply` explicite, dry-run par défaut.

**Q7 (Coût).** Budget ?
> Reco : négligeable (pas de LLM). OK.

**Q9 (Risque).** Niveau final ?
> MEDIUM (touche un vault non versionné mais en lecture seule) → gate = confirmation courte avant de loguer.

## 📋 À copier

```
## DEC-0NN — Workflow Temporal vault_audit (lecture seule, CLI-orchestré) — 2026-06-03
- **Contexte** : vault le domaine non versionné → hors CI ; besoin de prouver cohérence taxonomique + dédup d'ID + frontmatter, ce que pytest/docs-sync ne couvrent pas.
- **Décision** : `vault_audit.workflow.ts` orchestre des activités CLI déterministes (scan_files + run_cli obsidian-goat) ; aucun appel LLM en chemin chaud ; sortie JSON contractuelle ; lecture seule, corrections via second acte --apply dry-run par défaut.
- **Alternatives écartées** : audit LLM-driven (non déterministe, coûteux) ; extension du gate docs-sync (périmètre vault ≠ vitrine publique).
- **Risk Guard** : MEDIUM
- **Routage (DEC-016)** : workflow+activités → TricorderKit ; fiches → le domaine (lecture seule).
- **Dry-run / rollback** : audit read-only ; rollback = ne rien appliquer (le rapport n'altère rien).
- **Reste à faire** : livrer d'abord obsidian-goat (dépendance amont, TASKS pending) ; tests d'activités.
- **Statut** : Proposée
```
Diff STATE.md proposé : `Phase 4 — ajouter "vault_audit (design gelé, bloqué par obsidian-goat)"`.

## 📊 Notes de fiabilité
- Nœuds résolus : cadrage, CLI-vs-LLM, contrat, routage, sûreté, risque.
- Nœud **ouvert** : numérotation DEC (placeholder `0NN` → `goat next-id` avant log).
- Dépendance bloquante non levée : `obsidian-goat` (TASKS pending) — l'audit ne peut pas être livré avant.
- Aucune donnée externe → pas de sourcing requis.
