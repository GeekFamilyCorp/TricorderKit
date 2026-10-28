---
title: Run the heavy services on another machine
scope: Temporal, Neo4j, Qdrant on a server; vault, embeddings and workers on your workstation
status: tested (Windows workstation + Linux server, private network)
updated: 2026-10-17
---

# Run the heavy services on another machine

Neo4j, Qdrant and Temporal need several gigabytes of RAM and must stay up for
schedules to fire. On a laptop that sleeps, reboots or runs out of memory, they
silently stop — and so does everything that depends on them.

TricorderKit lets you move these three services to an always-on machine (home
server, NAS, VPS) while your notes, your embeddings model and your workers stay
on your workstation. Switching is done with **environment variables only**, and
reverting means deleting them.

## What goes where

| Component | Where | Why |
|---|---|---|
| Temporal + its PostgreSQL | **server** | durable workflows and schedules must survive your laptop sleeping |
| Neo4j (graph) | **server** | memory-hungry, always queried |
| Qdrant (vectors) | **server** | memory-hungry, always queried |
| Obsidian vault, notes | workstation | your data stays with you |
| Ollama (embeddings) | workstation | computes query embeddings locally |
| Temporal workers | workstation | they read and write your vault |

## ⚠️ Security first

- **Never expose these ports to the internet.** Use a private network between the
  two machines (Tailscale, WireGuard, a LAN).
- **Docker bypasses host firewalls such as UFW** for the ports it publishes. A
  firewall rule will not protect `0.0.0.0:6333`. Bind every published port to the
  server's **private-network IP** explicitly — the example compose does exactly
  that through `BIND_IP`.
- Qdrant has no API key by default. Keep it on the private network, or set
  `QDRANT__SERVICE__API_KEY` and give the same key to your clients.
- Secrets (database and Neo4j passwords) live in a `.env` file on the server with
  permissions `600`. They never go into the repository.

## 1. Server: start the services

Copy [`examples/remote-services/`](../examples/remote-services/) to the server,
then:

```bash
cd remote-services
cp .env.example .env && chmod 600 .env
# edit .env: BIND_IP = the server's private-network IP, then the passwords
docker compose up -d
docker compose ps        # temporal, temporal-db, neo4j: healthy ; qdrant: up
```

Check from the **workstation** that the ports answer over the private network
(7233 Temporal, 7687 Neo4j Bolt, 6333 Qdrant).

## 2. Optional: bring your existing data

Use the **same image versions** on both sides, then:

| Service | Method | Check |
|---|---|---|
| Temporal | `pg_dump -Fc` of the `temporal` and `temporal_visibility` databases, `pg_restore --no-owner` into the new PostgreSQL **before** starting Temporal | `select count(*) from executions` matches; schedules listed by `tctl schedule list` |
| Neo4j | stop it, archive the data volume (`tar czpf` from a throw-away container), extract into the new **empty** volume | same file count on both sides |
| Qdrant | same as Neo4j | `GET /collections/<name>` → same `points_count`, status `green` |

Verify every archive with `sha256sum` after the transfer. A migrated Neo4j keeps
its **own** password (it lives in the data), so `NEO4J_AUTH` is ignored and your
clients keep working unchanged. Keep the workstation volumes until you are
satisfied: they are your rollback.

## 3. Workstation: point TricorderKit at the server

Set these **user** environment variables (replace `<SERVER_IP>` with the server's
private-network IP):

| Variable | Value |
|---|---|
| `TEMPORAL_ADDRESS` | `<SERVER_IP>:7233` |
| `NEO4J_URI` | `bolt://<SERVER_IP>:7687` |
| `QDRANT_URL` | `http://<SERVER_IP>:6333` |
| `TK_QDRANT_URL` | `http://<SERVER_IP>:6333` (vault-search MCP server) |

Windows: *Settings → System → About → Advanced system settings → Environment
Variables → User variables → New*. Linux/macOS: export them in your shell profile.
Restart the programs that should see them.

What changes automatically:

- **`tools/caps`** reads the `remote_env` key of each capability
  (`tools/caps/capabilities.yaml`). When all listed variables point to another
  host, `caps ensure` probes the remote service and **never starts a local
  container**; remote capabilities are excluded from the local RAM budget and
  from pre-emption. `python tools/caps/caps.py status` shows them as
  `distant (<host>:<port>)`.
- **Workers** (`plugins/workflow-engine/scripts/start_worker.cmd`,
  `run_worker_loop.cmd`) use `TEMPORAL_ADDRESS` and skip the local Temporal start.
- **Vector search** (`plugins/graphify/scripts/search_vault.py`,
  `plugins/deep-research-core/scripts/index_qdrant.py`) uses `QDRANT_URL`.

## 4. Windows: keep the workers alive

If you start workers from the Windows Task Scheduler, use
`plugins/workflow-engine/scripts/run_worker_loop.cmd` as the task action.
The Task Scheduler kills child processes when the action exits, so a worker
launched in the background dies one second after starting. `run_worker_loop.cmd`
stays in the foreground and restarts the worker if it stops. Recommended task
settings: allow start on batteries, no execution time limit, restart on failure,
triggers *at log on* and *at startup*.

## 5. Verify

```bash
python tools/caps/caps.py status          # graph + workflows: UP, "distant (...)"
python tools/caps/caps.py selftest        # includes the remote-mode checks
python plugins/graphify/scripts/search_vault.py --query "<something you know is in your vault>"
```

On the server, `tctl --address temporal:7233 --ns default taskqueue describe --taskqueue <queue>`
(run inside the Temporal container) lists your workstation workers as pollers.

## Rollback

1. Delete the four environment variables on the workstation.
2. Restart the workers.
3. `python tools/caps/caps.py ensure graph` / `ensure workflows` starts the local
   containers again, on the volumes you kept.

Nothing on the server needs to be deleted to roll back: stop it with
`docker compose stop` when you no longer need it.
