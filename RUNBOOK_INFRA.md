# RUNBOOK_INFRA — Exploitation infrastructure Docker

> Runbook opérationnel. Architecture de référence : `docs/INFRA.md`.
> **Convention shell** : chaque bloc est étiqueté `bash` (Linux / Git Bash / WSL / `docker exec`) ou `powershell` (PowerShell Windows natif). Ne pas mélanger.
> **Secrets** : jamais en clair ici. Les identifiants viennent de `.env` (variables `NEO4J_PASSWORD`, `POSTGRES_PASSWORD`…).
> **Chemins** : `<TRICORDERKIT_ROOT>` = racine du projet sur votre poste. La remplacer par le chemin réel à l'exécution (jamais en dur dans un fichier versionné — frontière publique DEC-026/R37).

---

## 1. Vérification rapide

Statut global de tous les conteneurs :

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Filtrer les services critiques :

```bash
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "filemaster|agent-gateway|tricorder"
```

Ressources (snapshot) :

```bash
docker stats --no-stream
```

---

## 2. Accès aux services

| Service | URL | Auth |
|---|---|---|
| FileAI Master | http://localhost:9000 | — |
| Agent Gateway | http://localhost:8080 | — |
| Temporal UI | http://localhost:8081 | — |
| Langfuse | http://localhost:3001 | — |
| Neo4j Browser | http://localhost:7474 | user/mot de passe via `.env` |

> Neo4j : utiliser `NEO4J_USER` / `NEO4J_PASSWORD` définis dans `.env`. Ne pas saisir d'identifiant en clair dans un fichier versionné.

---

## 3. Tests de connectivité

```bash
# Qdrant — sonde de vivacité réelle (pas de /healthz sur cette image)
curl http://127.0.0.1:6333/collections

# Temporal — santé du cluster
tctl --address localhost:7233 cluster health

# Neo4j — Browser
curl http://127.0.0.1:7474/browser/

# Langfuse — health
curl http://127.0.0.1:3001/api/v1/health
```

---

## 4. Logs & debugging

```bash
# Logs temps réel
docker logs -f tricorder-temporal
docker logs -f tricorder-qdrant
docker logs -f tricorder-neo4j
docker logs -f filemaster-ai
docker logs -f agent-gateway

# Dernières 50 lignes
docker logs --tail 50 tricorder-temporal

# Depuis X minutes
docker logs --since 10m tricorder-qdrant
```

---

## 5. Redémarrage

```bash
# Un seul service
docker restart tricorder-temporal

# Tous les services Tricorder
cd "<TRICORDERKIT_ROOT>"
docker compose restart
```

Recréation complète (⚠️ conteneurs recréés ; les données persistent tant que les volumes ne sont pas supprimés) :

```bash
cd "<TRICORDERKIT_ROOT>"
docker compose down
docker compose up -d
```

---

## 6. Inspection détaillée

Commandes neutres (`bash`) :

```bash
docker inspect tricorder-temporal
docker port tricorder-neo4j
```

Variantes avec parsing JSON — **PowerShell uniquement** (`ConvertFrom-Json` n'existe pas en bash) :

```powershell
docker inspect tricorder-qdrant --format='{{json .Mounts}}' | ConvertFrom-Json
docker inspect tricorder-temporal --format='{{json .Config.Env}}' | ConvertFrom-Json
```

Équivalent bash (avec `jq`) :

```bash
docker inspect tricorder-qdrant --format='{{json .Mounts}}' | jq
docker inspect tricorder-temporal --format='{{json .Config.Env}}' | jq
```

---

## 7. Gestion des volumes

```bash
docker volume ls
docker volume inspect tricorder_qdrant_data
docker volume rm tricorder_qdrant_data   # ⚠️ destructif
```

---

## 8. Nettoyage & maintenance

```bash
docker system df                  # utilisation disque Docker
docker volume prune -f            # volumes orphelins
docker container prune -f         # conteneurs arrêtés
docker image prune -a             # images non utilisées
docker system prune -a --volumes  # ⚠️ destructif : tout le non-utilisé
```

---

## 9. Outils internes (docker exec)

```bash
# Temporal
docker exec -it tricorder-temporal tctl cluster health
docker exec -it tricorder-temporal tctl workflow list

# Neo4j — le mot de passe vient de l'environnement, ne pas l'écrire en dur
docker exec -it tricorder-neo4j cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" "SHOW DATABASES"

# PostgreSQL Temporal
docker exec -it tricorder-temporal-db psql -U temporal -d temporal -c "\dt"
```

> Sous PowerShell, remplacer `$NEO4J_USER` / `$NEO4J_PASSWORD` par `$env:NEO4J_USER` / `$env:NEO4J_PASSWORD`.

---

## 10. Backups

### Qdrant (volume → archive)

Le mapping de volume Docker se note `nom_volume:/chemin_interne`. Le dossier hôte de destination doit exister.

```powershell
# PowerShell — destination Windows
docker run --rm -v tricorder_qdrant_data:/data -v C:\Backups:/backup alpine `
  tar czf /backup/qdrant_backup.tar.gz -C /data .
```

```bash
# bash — destination Linux/WSL
docker run --rm -v tricorder_qdrant_data:/data -v /backups:/backup alpine \
  tar czf /backup/qdrant_backup.tar.gz -C /data .
```

### PostgreSQL (dump SQL)

```bash
docker exec tricorder-temporal-db pg_dump -U temporal temporal > temporal_backup.sql
docker exec tricorder-langfuse-db pg_dump -U langfuse langfuse > langfuse_backup.sql
```

Restore :

```bash
docker exec -i tricorder-temporal-db psql -U temporal temporal < temporal_backup.sql
```

---

## 11. Troubleshooting

### Temporal reste UNHEALTHY
```bash
docker logs tricorder-temporal | tail -100
# redémarrer le binôme DB + service
docker restart tricorder-temporal-db
docker restart tricorder-temporal
# patienter 2-3 min après redémarrage (normal)
```

### Qdrant ne répond pas
```bash
curl http://127.0.0.1:6333/collections   # sonde réelle
docker restart tricorder-qdrant
docker logs -f tricorder-qdrant
```

### Neo4j inaccessible
```bash
docker logs tricorder-neo4j | tail -50
docker restart tricorder-neo4j
curl http://127.0.0.1:7474/browser/
```

### Espace disque plein
```bash
docker system df
docker image prune -a
docker volume prune -f
docker system prune -a --volumes   # ⚠️ dernier recours, destructif
```

---

## 12. Seuils d'alerte à surveiller

- Temporal en UNHEALTHY > 10 min
- Qdrant CPU > 5 % soutenu
- RAM hôte > 50 %
- Disque > 50 %
- Présence de `ERROR` dans les logs Temporal / Neo4j / Qdrant

---

## 13. Checklist de démarrage

- [ ] `docker ps` : conteneurs attendus running
- [ ] FileAI Master : http://localhost:9000
- [ ] Agent Gateway : http://localhost:8080
- [ ] Temporal UI : http://localhost:8081
- [ ] Neo4j Browser : http://localhost:7474
- [ ] Qdrant : `curl http://127.0.0.1:6333/collections`
- [ ] Langfuse : http://localhost:3001
- [ ] Ressources nominales : `docker stats`

---

*Runbook opérationnel — sans état daté ni secret. Architecture : `docs/INFRA.md`.*
