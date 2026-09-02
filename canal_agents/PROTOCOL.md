---
type: protocole
nom: canal-agents/3
maj: 2026-09-02
remplace: canal-agents/2 (sync_bus v2)
---

# canal_agents v3 — bus multi-agents (VPS `/opt/agents-hub/canal_agents`, TricorderKit `canal_agents/`)

## 1. Roster (source de vérité : `sync_bus.py` → `AGENTS`, exporté dans `bus/events.schema.json` par `schema --write`)

| Agent | Nature | Qui l'incarne |
|---|---|---|
| `claude` | interactif | Claude Cowork (poste), via `vps_exec.py` ou `ja_coord_hub` |
| `codex` | interactif | ChatGPT-Codex en session SSH Tailscale |
| `antigravity` | interactif (hérité) | sessions Antigravity |
| `qwen` | local | `bus_worker.py` (Ollama conteneur, port 32788), timer `canal-bus-watch` |
| `vps` | local, système | planner/collecte, gardiens (`health --emit` signe `vps`) |
| `all` | broadcast | — |

`chatgpt` n'est **jamais** un agent du bus : ChatGPT intervient comme session interactive (`codex`) ou via le hub `00_coordination`. Aucun processus local ne se fait passer pour lui (mission §32).

## 2. Événement

```json
{"seq":N,"id":"…","ts":"ISO+offset","from":"<agent>","to":"<agent>|all","type":"<type>",
 "task":"T-…|null","correlation_id":"T-…","reply_to":"<id de l'événement initiateur>","msg":"…","payload":{}}
```
`seq` est attribué **à l'écriture, sous verrou** (`bus/.events.lock`, `flock`) : deux écrivains simultanés ne peuvent pas obtenir le même numéro (testé : 8 processus × 25 posts → 200 seq uniques et contigus ; l'ancienne v2 produisait 9 doublons sur le même test). Journal append-only, jamais réécrit ; `rotate` archive uniquement les événements lus par tous.

## 3. Types et table d'équivalence (mission §5)

| Protocole minimal | Type bus | Émis par | Vers |
|---|---|---|---|
| TASK | `task_assign` (`dispatch`) | demandeur | exécutant |
| ACK | `ack` (`ack --event-id`) | receveur | émetteur de l'événement |
| PROGRESS | `task_progress` (`progress --percent`) | exécutant | **demandeur** |
| RESULT | `task_done` (`done --status done`) | exécutant | **demandeur** |
| ERROR | `task_failed` (`done --status failed --error`) | exécutant | **demandeur** |
| BLOCKED | `blocked` (`blocked --needs`) | exécutant | **demandeur** (escalade) |
| REQUEST | `request` (`post --type request`) | n'importe qui | agent ou `all` |
| HANDOFF | `handoff` (`post --type handoff`) | agent | agent |
| HEARTBEAT | `heartbeat` (`heartbeat --state`) | agent | `all` |
| — | `message`, `question`, `answer`, `gap`, `deliverable_ready`, `announce`, `lock`, `unlock`, `alert` | conservés de v2 | — |

**Retour au demandeur** : le record de tâche (`inbox/<exécutant>/<task>.json`) conserve `requester` et `assign_event_id` ; `claim/progress/blocked/done` répondent à `requester` (v2 répondait à `claude` en dur). Demandeur inconnu → `all`.

## 4. Cycle de vie d'une tâche

`dispatch` (assigned) → `claim` (in_progress, anti-doublon : refus si claim frais < 30 min ; reprise autorisée au-delà) → `progress`* → `blocked`* → `done --status done|failed [--archive]`. Timeouts surveillés par `health --alert` : assigned > 15 min, in_progress > 30 min, heartbeat > 15 min, verrous expirés → `alert` signés `vps` vers `all`.

## 5. Reprise et idempotence

Curseurs (`bus/cursor.<agent>`) et records de tâche écrits atomiquement (`tmp + os.replace`). Un agent redémarré relit à partir de son curseur ; un `claim` périmé peut être repris ; `done` sur une tâche déjà `done` est refusé.

## 6. Commandes

`init · heartbeat · post · dispatch · claim · progress · blocked · done · ack · task-status · tasks · lock · unlock · read · inbox · health · status · rotate · schema [--write|--check]`. Sortie JSON (`--json` ou non-TTY). `--dry-run` disponible sur les écritures (le `seq` affiché en dry-run est 0 : il n'est attribué qu'à l'écriture réelle).

## 7. Tests reproductibles

`tests/test_bus_v3.sh` (dans ce dossier) : round-trip claude→qwen→claude, codex→qwen→codex (failed + blocked), vps→claude→vps, ack, concurrence 8×25, `schema --check`. Exécuté le 2026-09-02 sur un canal jetable puis sur le VPS (voir HANDOFFS.md).
