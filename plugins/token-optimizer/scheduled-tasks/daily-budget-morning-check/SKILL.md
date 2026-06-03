---
name: daily-budget-morning-check
description: Notification matinale du statut budget tokens - ingestion conso reelle, auto-optimisation puis rappel quotidien a 8h30
---

Tu es Claude en mode Cowork pour Sebastien. Lance le controle matinal du budget tokens.

Toutes les commandes python s'executent en **python Windows** via Desktop Commander
(`C:\Python314\python.exe`), JAMAIS le python3 du sandbox Linux (il viserait un budget.json
different -> split-brain). Chemin scripts du plugin (instance rpm), note `<scripts>` ci-dessous :
`<scripts>` = dossier `scripts/` de l'instance rpm du plugin token-optimizer.

## Etape 1 - Ingestion de la conso REELLE (obligatoire avant lecture)

`track_usage.py` lit la conso facturee dans les transcripts (source de verite, idempotent).
Lance-le AVANT toute lecture :

```
mcp__Desktop_Commander__start_process(
  command: $env:PYTHONIOENCODING="utf-8"; Start-Process -FilePath "C:\Python314\python.exe" -ArgumentList '"<scripts>/track_usage.py","--json" -NoNewWindow -Wait -RedirectStandardOutput "<repo>/_budget_ingest.json"
  timeout_ms: 60000)
```

Si python introuvable : `where.exe python` ou `Get-ChildItem C:\ -Filter python.exe -Recurse -Depth 4`.

## Etape 2 - Auto-optimisation sure (reversible)

Applique la liste blanche d'optimisations selon la pression budget (drapeaux `auto_state`,
reversibles, journalises) :

```
Start-Process "C:\Python314\python.exe" -ArgumentList '"<scripts>/optimizer.py","apply' -NoNewWindow -Wait -RedirectStandardOutput "..._opt.txt"
```

Lis le resultat : note les drapeaux changes (caveman_default / haiku_reroute / force_haiku /
score_bias) pour les mentionner dans le rapport. Aucun effet sur le modele du fil principal
(choix utilisateur) ; ces drapeaux pilotent le dispatch des sous-agents et la verbosite.

## Etape 3 - Lecture du statut

```
Start-Process "C:\Python314\python.exe" -ArgumentList '"<scripts>/budget.py","status","--json' -NoNewWindow -Wait -RedirectStandardOutput "..._budget_status.json"
```

Champs : `total_used_equivalent`, `total_budget_tokens`, `total_ratio`, `alert`,
`per_model{haiku,sonnet,opus}.ratio`, `escalation_policy`.

## Etape 4 - Analyse

- Budget journalier estime = `total_budget_tokens` / 30.
- Alerte selon `total_ratio` : OK < 50% | INFO 50-70% | ATTENTION 70-80% | CRITIQUE > 80%.
- Modele au ratio le plus eleve (rappel : Opus est le poste dominant).

## Etape 5 - Notification Slack

DM Slack a Sebastien, court (5 lignes max) :
- Statut global 1 ligne (X% consomme, niveau d'alerte).
- Modele le plus consomme + ratio (souvent Opus -> surveiller le sous-budget Opus).
- Drapeaux auto-optimisation actives si changement (Etape 2).
- LEVIER PRINCIPAL si Opus domine : rappeler que ~97% du cout = sessions Opus du fil principal
  -> suggerer de basculer les sessions non critiques sur Sonnet et d'appliquer la Session
  Rotation (nouveau fil tous les 15-20 messages) pour reduire le cache_read. Ce levier est
  un choix utilisateur, aucun script ne peut l'automatiser.
- Encouragement court si tout est OK.

## Notes techniques

- Ecriture budget TOUJOURS cote Windows -> fichier canonique `~/.token-optimizer/budget.json`.
- `track_usage.py` = seule source d'ecriture de la conso (hook PostToolUse retire, anti double comptage).
- Nettoie les fichiers temporaires `_budget_ingest.json` / `_budget_status.json` / `_opt.txt` apres lecture.
- En cas d'echec apres 3 tentatives, envoyer quand meme un Slack signalant l'indisponibilite.
