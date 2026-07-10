# backup_db.ps1 - Sauvegarde des volumes DB TricorderKit (RUNBOOK section 10 / DEC-040)
# pg_dump (Temporal, Langfuse) + archives tar (Qdrant a chaud, Neo4j avec arret bref).
# Usage : powershell -NoProfile -ExecutionPolicy Bypass -File scripts\backup_db.ps1
param(
  [string]$BackupRoot = "$env:USERPROFILE\Backups\TricorderKit",
  [int]$RetentionDays = 14,
  [switch]$SkipNeo4j
)
$ErrorActionPreference = "Continue"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$dest = Join-Path $BackupRoot $stamp
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$log = Join-Path $dest "backup.log"
$failures = 0
function Log([string]$m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Tee-Object -FilePath $log -Append }

Log "=== Backup TricorderKit -> $dest ==="

# 0. Garde : si Docker/les conteneurs ne tournent pas, rien a sauvegarder -> skip propre (pas d'echec).
$dockerOk = $false
try { docker info *> $null; if ($LASTEXITCODE -eq 0) { $dockerOk = $true } } catch { $dockerOk = $false }
$containers = if ($dockerOk) { (docker ps --filter "name=tricorder" --format "{{.Names}}") } else { $null }
if (-not $dockerOk -or -not $containers) {
  Log "Docker indisponible ou aucun conteneur tricorder-* actif -> backup DB saute (rien a sauvegarder). exit 0"
  exit 0
}

# 1. PostgreSQL (dumps via cmd pour redirection en octets bruts - pas de BOM PowerShell)
foreach ($db in @(@{c="tricorder-temporal-db";u="temporal";n="temporal"}, @{c="tricorder-langfuse-db";u="langfuse";n="langfuse"})) {
  $out = Join-Path $dest "$($db.n).sql"
  cmd /c "docker exec $($db.c) pg_dump -U $($db.u) $($db.n) > `"$out`"" 2>>$log
  # Un pg_dump valide (meme base vide) commence par l'en-tete "PostgreSQL database dump".
  # On valide sur l'en-tete plutot qu'un seuil de taille : une base vierge (Langfuse fraichement recreee)
  # produit un dump legitime mais petit qui ne doit PAS etre compte comme un echec.
  $head = if (Test-Path $out) { (Get-Content $out -TotalCount 8 -ErrorAction SilentlyContinue) -join "`n" } else { "" }
  if ($LASTEXITCODE -eq 0 -and $head -match 'PostgreSQL database dump') {
    $kb = [math]::Round((Get-Item $out).Length/1KB)
    if ($kb -lt 1) { Log "pg_dump $($db.n) : OK (base vide/quasi-vide, ${kb} Ko)" } else { Log "pg_dump $($db.n) : OK ($kb Ko)" }
  }
  else { Log "pg_dump $($db.n) : ECHEC"; $failures++ }
}

# 2. Qdrant (archive a chaud du volume)
docker run --rm -v tricorder_qdrant_data:/data -v "${dest}:/backup" alpine tar czf /backup/qdrant.tar.gz -C /data . 2>>$log
if ($LASTEXITCODE -eq 0) { Log "qdrant tar : OK ($([math]::Round((Get-Item "$dest\qdrant.tar.gz").Length/1MB,1)) Mo)" } else { Log "qdrant tar : ECHEC"; $failures++ }

# 3. Neo4j (arret bref pour coherence des fichiers - community edition, pas de backup online)
if (-not $SkipNeo4j) {
  docker stop tricorder-neo4j *>>$log
  docker run --rm -v tricorder_neo4j_data:/data -v "${dest}:/backup" alpine tar czf /backup/neo4j.tar.gz -C /data . 2>>$log
  $tarOk = ($LASTEXITCODE -eq 0)
  docker s