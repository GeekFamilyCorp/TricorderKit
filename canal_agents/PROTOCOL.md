---
type: protocole
nom: canal-agents/2
maj: 2026-06-14
remplace: tk-realtime/1 (_sync_antigravity, deprecie)
---

# 🔌 canal_agents — Bus de communication multi-agents (générique)

> **Canal unique** de coordination entre tous les agents : `claude`, `codex`, `antigravity`, `qwen`, … .
> Transport fichier **append-only**, lecture par **curseur** (anti-staleness), **zéro token LLM**.
> Déterministe, stdlib Python 3.11+. Moteur : `scripts/sync_bus.py`.

## 1. Participants (roster)

Défini dans `scripts/sync_bus.py` → `AGENTS`. Ajouter un agent = l'ajouter au tuple `AGENTS`
(ex. `("claude", "antigravity", "codex", "qwen")`). Chaque agent a un curseur et une inbox.

## 2. Transport

- `bus/events.jsonl` — **append-only**, 1 événement JSON/ligne. Jamais réécrit ni tronqué.
- `bus/cursor.<agent>` — nb de lignes déjà consommées par l'agent (source de vérité ; **on ne se fie jamais au mtime**).
- `STATUS.json` — état machine-lisible (heartbeats + curseurs + inbox_pending par agent).

### Schéma d'événement
```json
{"seq":N,"ts":"<ISO+02:00>","from":"<agent>","to":"<agent>|all","type":"<type>","ref":"T-...|null","payload":{}}
```

## 3. Commandes (`python scripts/sync_bus.py <cmd>`)

| Famille | Commandes | Rôle |
|---|---|---|
| Présence | `init`, `heartbeat <agent> --state`, `status`, `health` | cycle de vie / état du canal |
| Messagerie | `post --from <agent> --to <agent>`, `read --agent <agent>`, `inbox` | échanges append-only par curseur |
| Tâches | `dispatch --from <agent>`, `claim`, `done`, `task-status`, `tasks` | cycle de vie des tâches déléguées |
| Verrou | `lock`, `unlock` | exclusivité pour écritures sensibles (ex. vault) |
| Maintenance | `rotate` | rotation du journal d'événements |

États valides : `idle`, `working`, `blocked`, `offline`, `error`.

## 4. Cadence

- Poll du bus ~60 s : chaque agent lit au-delà de son curseur, traite, réécrit son curseur, émet un `heartbeat`.
- Un heartbeat de plus de ~30 min ⇒ agent considéré offline (session plantée), tâche réclamable par un autre.

## 5. Règles d'or

- Verrou **uniquement** pour les écritures partagées (ex. intégration vault) ; la messagerie bus est en append concurrent sûr.
- Ne jamais conclure « canal muet » sur une absence apparente : **compter les lignes réelles** via le curseur (`health`).
- Contenu métier (fiches, données projet) : il transite par référence, **jamais** stocké dans le repo public (cf. règle « repos = backup, vaults = données »).

## 6. Personnalisation

Aucun chemin personnel codé en dur : le moteur résout ses dossiers en relatif (`Path(__file__).parent`).
Le **runtime** (`bus/`, `STATUS.json`, `outbox/`, `budget/`, inboxes, config machine) reste **local/privé** ;
seul ce protocole + `scripts/sync_bus.py` (moteur générique) sont publiés.
