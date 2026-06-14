---
type: protocole
nom: tk-realtime/1
projet: TricorderKit (pont generique ; projet lie configurable)
maj: 2026-06-04
remplace: "battement horaire XX:01 / XX:10"
---

# 🔌 Protocole temps-réel Claude ⇄ Antigravity (tk-realtime/1)

> Objectif : canal quasi-temps-réel + **offload** des tâches longues et de la recherche web
> vers Antigravity. Claude garde l'intégration vault et la QA.

## 1. Transport — bus fichier append-only

- `bus/events.jsonl` — **append-only**, 1 événement JSON par ligne. Jamais réécrit, jamais tronqué.
- Lecture par **curseur** (anti-staleness) : chaque agent lit `bus/cursor.<agent>` (= nb de lignes déjà consommées), traite les lignes au-delà, puis réécrit son curseur. **On ne se fie jamais au mtime du mount** (cause du faux « SO muet »).
- `bus/.wake` — courtoisie : touché à chaque émission. Optionnel ; le curseur reste la source de vérité.

### Schéma d'événement
```json
{"id":"EVT-...","ts":"<ISO+02:00>","from":"claude|antigravity","type":"<type>","ref":"T-...|null","payload":{}}
```
Types : `channel.up` · `heartbeat` · `task.request` · `task.progress` · `task.result` · `note` · `arbitrage.needed`.

## 2. Cadence

- Poll **toutes les 60 s** du bus (vs battement horaire — déprécié).
- À chaque poll : émettre un `heartbeat` et mettre à jour son `agents.<nom>` dans `STATUS.json`.
- `STATUS.json` = état machine-lisible (heartbeats + compteurs). Capteur : `scripts/health_check.py`.

## 3. Verrou

- Verrou conservé **uniquement pour les écritures vault** (intégration de fiches). La messagerie bus ne pose pas de verrou (append concurrent sûr).

## 4. Contrat d'OFFLOAD (cœur du dispositif)

Claude **délègue à Antigravity** : (a) **recherche web**, (b) **enrichissements longs / sweeps**, (c) sourcing multi-pages. Claude **garde** : intégration vault, QA/scoring, arbitrages.

### Cycle
1. **Claude** dépose `commands/antigravity_inbox/<ISO>__<slug>.md` (frontmatter `type: task_request`) **et** émet un event `task.request` (`ref` = id tâche).
2. **Antigravity** exécute, peut émettre des `task.progress`, puis dépose `commands/claude_inbox/<ISO>__<slug>.md` (`type: task_result`) **et** émet `task.result`.
3. **Claude** intègre / QA, archive les deux fichiers dans `commands/archive/`.

### Schéma task_request (frontmatter)
```yaml
type: task_request
id: T-AAAA-MM-JJ-NNN
from: claude
to: antigravity
kind: web_research | long_enrich | sweep | sourcing
priority: low | normal | high
deadline: <ISO|null>
status: queued
```
Corps : `# Objectif` · `# Livrable attendu` · `# Sources autorisées/exclues` (Wikipedia exclu) · `# Critères d'acceptation`.

### Schéma task_result (frontmatter)
```yaml
type: task_result
ref: T-AAAA-MM-JJ-NNN
from: antigravity
status: done | partial | blocked
sources: [ ... ]   # 2 min. concordantes ou 1 primaire officielle
```

## 5. Règles d'or héritées de l'audit 2026-06-04

- Ne jamais conclure « pipeline muet » sur une absence apparente : **compter les fichiers réels** (health_check.py).
- Ne jamais marquer ✅ un champ dont **2 sources divergent** → `conflit_a_arbitrer`.
- Un id MAL bas + date/éditeur incohérents = **appariement à revérifier** avant livraison.
