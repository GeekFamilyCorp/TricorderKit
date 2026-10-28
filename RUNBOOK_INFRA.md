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

> **Automatise** : `scripts/backup_db.ps1` fait tout (pg_dump Temporal + Langfuse, tar Qdrant a chaud, tar Neo4j avec arret bref, retention 14 j) et est branche en tache planifiee Windows quotidienne 03h30 ("TricorderKit DB Backup"). Restore a blanc valide (dump -> base temporaire -> drop). Les commandes ci-dessous restent la reference manuelle.

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


## 14. Secrets des serveurs MCP (Windows Credential Manager)

> Principe (DEC-039) : aucun token en clair dans les fichiers de config des clients MCP.
> Le secret vit dans le Credential Manager Windows ; un wrapper l'injecte au lancement.

### Stocker le secret (une fois, invite masquee - le token ne touche ni historique ni transcript)

```powershell
cmdkey /generic:<nom-credential> /user:token /pass
```

### Lecteur de credential - get-secret.ps1 (a cote du wrapper)

```powershell
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class CredMan {
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  public struct CREDENTIAL {
    public int Flags; public int Type; public string TargetName; public string Comment;
    public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
    public int CredentialBlobSize; public IntPtr CredentialBlob; public int Persist;
    public int AttributeCount; public IntPtr Attributes; public string TargetAlias; public string UserName;
  }
  [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  public static extern bool CredRead(string target, int type, int flags, out IntPtr credentialPtr);
  [DllImport("advapi32.dll")]
  public static extern bool CredFree(IntPtr cred);
  public static string GetPassword(string target) {
    IntPtr p;
    if (!CredRead(target, 1, 0, out p)) return null;
    CREDENTIAL c = (CREDENTIAL)Marshal.PtrToStructure(p, typeof(CREDENTIAL));
    string s = (c.CredentialBlobSize > 0) ? Marshal.PtrToStringUni(c.CredentialBlob, c.CredentialBlobSize / 2) : null;
    CredFree(p);
    return s;
  }
}
"@
$t = [CredMan]::GetPassword("<nom-credential>")
if ($t) { Write-Output $t } else { exit 1 }
```

### Wrapper de lancement - serveur-mcp-wrapper.cmd (pointe par la config du client MCP)

```bat
@echo off
for /f "usebackq delims=" %%t in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0get-secret.ps1" ^< nul`) do set "MON_TOKEN=%%t"
if "%MON_TOKEN%"=="" (
  echo ERREUR: credential introuvable 1>&2
  exit /b 1
)
docker run -i --rm -e MON_TOKEN ghcr.io/exemple/serveur-mcp
```

Config client : `"command": "cmd.exe", "args": ["/c", "<chemin>\\serveur-mcp-wrapper.cmd"]` - plus aucun champ `env` avec secret.

### Pieges connus (tous rencontres et resolus)

1. **PowerShell seul comme wrapper stdio = EOF immediat** : PowerShell consomme le pipe stdin au lieu de le transmettre au processus natif. Le wrapper DOIT etre un `.cmd` (handles bruts).
2. **`for /f` fait heriter stdin au PowerShell imbrique** qui le consomme aussi : toujours `^< nul` sur l'appel imbrique.
3. **Config client UTF-8 SANS BOM obligatoire** : `Set-Content -Encoding UTF8` (PS 5.1) ecrit un BOM -> le client ne parse plus la config au redemarrage et la REINITIALISE (perte de tous les serveurs declares). Ecrire via `[IO.File]::WriteAllText($path, $contenu, [Text.UTF8Encoding]::new($false))`.
4. **Read-Host en collage multiligne** capture une ligne vide -> credential au blob vide. Preferer `cmdkey ... /pass` qui invite lui-meme.

### Test standalone du wrapper (sans dependre d'un redemarrage du client)

```bat
(type init.json & ping -n 10 127.0.0.1 >nul) | serveur-mcp-wrapper.cmd
```

ou `init.json` contient un message JSON-RPC `initialize`. Le `ping` maintient stdin ouvert (le serveur quitte sur EOF). Reponse `serverInfo` attendue sur stdout. Verifier aussi la validite du token via l'API du service (sans jamais l'afficher).

### Rotation du secret

1. Regenerer le token chez le fournisseur (avec date d'expiration).
2. `cmdkey /generic:<nom-credential> /user:token /pass` (ecrase l'existant).
3. Revoquer l'ancien token et VERIFIER le rejet (appel API -> 401 attendu).
4. Purger tout backup de config contenant l'ancien secret.