#!/usr/bin/env bash
# vps_doctor.sh — Health-check VPS (TricorderKit v1.0, DEC-046 Phase 1 / N4)
#
# Lecture seule : diagnostique Docker, ports, RAM/disque, services applicatifs,
# Tailscale, pare-feu (ufw) et fail2ban. N'effectue AUCUNE modification.
# Conçu pour exécution SUR le VPS via paramiko/Tailscale (ssh.exe bloqué côté Cowork).
#
# Aucune IP ni secret en dur (frontière publique) : tout vient de l'environnement.
#   VPS_DOCTOR_PORTS   : ports applicatifs à vérifier (défaut liste interne)
#   VPS_DOCTOR_JSON=1  : sortie JSON en plus du rapport texte
#
# Sortie : rapport ASCII. Exit 0 si OK, 1 si au moins un check CRITIQUE échoue,
#          2 sur erreur d'environnement (script lancé hors Linux/poste sans outils).
set -uo pipefail

FAIL=0
WARN=0
JSON_ITEMS=()

note()  { printf '  [OK]   %s\n' "$1"; JSON_ITEMS+=("{\"check\":\"$2\",\"status\":\"ok\"}"); }
warn()  { printf '  [WARN] %s\n' "$1"; WARN=$((WARN+1)); JSON_ITEMS+=("{\"check\":\"$2\",\"status\":\"warn\"}"); }
crit()  { printf '  [FAIL] %s\n' "$1"; FAIL=$((FAIL+1)); JSON_ITEMS+=("{\"check\":\"$2\",\"status\":\"fail\"}"); }
have()  { command -v "$1" >/dev/null 2>&1; }

echo "=== vps_doctor — $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

# 0. Environnement
if [ "$(uname -s)" != "Linux" ]; then
  echo "  [ERR] Ce script doit s'exécuter sur le VPS (Linux). Abandon." >&2
  exit 2
fi

# 1. Docker
echo "-- Docker --"
if have docker; then
  if docker info >/dev/null 2>&1; then
    note "daemon Docker actif" docker_daemon
    running=$(docker ps --format '{{.Names}}' 2>/dev/null | wc -l | tr -d ' ')
    unhealthy=$(docker ps --filter health=unhealthy --format '{{.Names}}' 2>/dev/null)
    note "conteneurs en cours : ${running}" docker_running
    if [ -n "$unhealthy" ]; then
      warn "conteneurs unhealthy : $(echo "$unhealthy" | tr '\n' ' ')" docker_unhealthy
    fi
  else
    crit "daemon Docker injoignable (permission ou service arrêté)" docker_daemon
  fi
else
  crit "docker absent du PATH" docker_present
fi

# 2. Ressources
echo "-- Ressources --"
if have free; then
  mem_avail_mb=$(free -m | awk '/^Mem:/{print $7}')
  if [ "${mem_avail_mb:-0}" -lt 512 ]; then
    warn "RAM disponible faible : ${mem_avail_mb} Mo" ram
  else
    note "RAM disponible : ${mem_avail_mb} Mo" ram
  fi
fi
disk_use=$(df -P / | awk 'NR==2{gsub("%","",$5); print $5}')
if [ "${disk_use:-0}" -ge 90 ]; then
  crit "disque / saturé à ${disk_use}%" disk
elif [ "${disk_use:-0}" -ge 80 ]; then
  warn "disque / à ${disk_use}%" disk
else
  note "disque / à ${disk_use}%" disk
fi

# 3. Ports applicatifs (écoute locale)
echo "-- Ports applicatifs (loopback/local) --"
PORTS="${VPS_DOCTOR_PORTS:-11434 6333 7474 7687 7233 5432 3001}"
if have ss; then
  listening=$(ss -ltnH 2>/dev/null | awk '{print $4}' | sed 's/.*://')
  for p in $PORTS; do
    if echo "$listening" | grep -qx "$p"; then
      note "port $p en écoute" "port_$p"
    else
      warn "port $p non en écoute (service down ou non déployé)" "port_$p"
    fi
  done
else
  warn "ss indisponible — vérification ports ignorée" ports
fi

# 4. Tailscale
echo "-- Reseau prive --"
if have tailscale; then
  if tailscale status >/dev/null 2>&1; then
    note "Tailscale actif" tailscale
  else
    warn "Tailscale installé mais non connecté" tailscale
  fi
else
  warn "tailscale absent (accès privé non vérifié)" tailscale
fi

# 5. Pare-feu
echo "-- Pare-feu / intrusion --"
if have ufw; then
  if ufw status 2>/dev/null | grep -qi 'Status: active'; then
    note "ufw actif" ufw
  else
    crit "ufw INACTIF (durcissement attendu)" ufw
  fi
else
  warn "ufw absent" ufw
fi
if have fail2ban-client; then
  if fail2ban-client ping >/dev/null 2>&1; then
    jails=$(fail2ban-client status 2>/dev/null | awk -F: '/Jail list/{print $2}' | xargs)
    note "fail2ban actif (jails: ${jails:-aucune})" fail2ban
  else
    warn "fail2ban installé mais serveur injoignable" fail2ban
  fi
else
  warn "fail2ban absent" fail2ban
fi

echo "=== Bilan : FAIL=${FAIL} WARN=${WARN} ==="
if [ "${VPS_DOCTOR_JSON:-0}" = "1" ]; then
  printf '{"fail":%d,"warn":%d,"items":[%s]}\n' "$FAIL" "$WARN" \
    "$(IFS=,; echo "${JSON_ITEMS[*]}")"
fi
[ "$FAIL" -eq 0 ]
