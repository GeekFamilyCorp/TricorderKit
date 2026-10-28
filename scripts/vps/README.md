# scripts/vps — Durcissement & résilience VPS (DEC-046, Phase 1 / N4)

> Framework générique TricorderKit (public). **Aucune IP, aucun secret en dur** :
> toute la configuration sensible (hôte, dépôt Borg, passphrase) passe par des
> variables d'environnement, jamais versionnées (DEC-039 / frontière publique R37).

## Rôle

Outiller le critère **« reboot sans perte »** du plan v1.0 :

| Script | Rôle | Effet |
|---|---|---|
| `vps_doctor.sh` | Diagnostic Docker / ports / RAM-disque / Tailscale / ufw / fail2ban | **Lecture seule** |
| `backup.sh` | Sauvegarde Borg chiffrée (zstd), init idempotent, rétention/prune | **Dry-run par défaut** |
| `restore_test.sh` | Test de restauration vers un répertoire jetable + `borg check` | N'altère jamais le live |

## Exécution

Ces scripts s'exécutent **sur le VPS** (Ubuntu). Depuis le poste, l'accès passe par
**paramiko + Tailscale** (le binaire `ssh.exe` est bloqué côté Cowork). Réutiliser
**une seule** session SSH (éviter les rafales qui déclenchent fail2ban).

```bash
# Diagnostic (sûr, lecture seule)
VPS_DOCTOR_JSON=1 bash vps_doctor.sh

# Sauvegarde — simulation puis réel
export BORG_REPO=/srv/borg/tricorderkit
export BORG_PASSPHRASE="***"          # via Credential Manager / secret, jamais en clair
export BACKUP_SOURCES="/srv/exports /etc/traefik /opt/agents-hub/runs"
bash backup.sh                         # dry-run (défaut)
BACKUP_DRY_RUN=0 bash backup.sh        # exécution réelle

# Test de restauration
RESTORE_EXPECT="traefik.yml" bash restore_test.sh
```

## ⚠️ Préalables avant tout run live (à valider — Risk Guard MEDIUM/HIGH)

1. **fail2ban** a banni le poste le 2026-06-11 → vérifier le débannissement avant SSH.
2. Une **partie du durcissement est déjà faite** (2026-06-09 : ufw, Traefik en frontal,
   rebind loopback des ports internes, Tailscale, SSH fermé). `vps_doctor.sh` confirme
   l'état réel ; **ne durcir que le manquant** (Règle 6 — pas de recréation).
3. **Borg/Restic** et **Uptime Kuma** restent à installer côté VPS (pièces neuves de N4).
4. Secrets : passphrase Borg et identifiants via le coffre, jamais dans le dépôt.

## Uptime Kuma (supervision — à déployer)

Conteneur léger, derrière Traefik (auth + TLS), à brancher sur des moniteurs
TCP/HTTP des ports applicatifs vérifiés par `vps_doctor.sh`. Déploiement et
exposition = côté VPS/ops (Antigravity/Hermes via `canal_agents`), pas côté Claude.

## Planification

`backup.sh` (réel) en tâche quotidienne ; `restore_test.sh` hebdomadaire ;
`vps_doctor.sh` horaire (log seul). À terme : workflows Temporal `source_freshness` /
santé (Phase 5), pas de cron dupliqué.
