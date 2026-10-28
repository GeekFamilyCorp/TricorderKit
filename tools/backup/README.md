# tools/backup — Sauvegarde & transfert dedupliques (guardrails)

Outillage **generique et reutilisable** pour sauvegarder un dossier de donnees de facon
robuste, y compris des **masses de petits fichiers** (ou robocopy /MIR et les scans I/O
s'effondrent). Rien n'est code en dur : chemins, hotes et secrets passent par arguments.

## Pourquoi

- **restic ne rescanne pas tout** comme un miroir `/MIR` : il compare via son index,
  **deduplique** et cree des **snapshots** versionnes. Bien plus rapide et sur sur de gros
  volumes, avec restauration point-in-time.
- **rclone** fournit un backend SFTP/S3 **natif** (Go pur) : la sauvegarde distante ne
  depend pas de `ssh.exe` (souvent bloque/filtre sous certains harnais Windows).
- Pour un **reservoir de centaines de milliers de petits fichiers**, la meilleure mesure
  n'est pas de le sauvegarder fichier par fichier mais de le **compacter** en une forme
  dense (JSONL, ou SQLite+FTS5 pour la recherche) : un `open()` amorti au lieu de N,
  backups instantanes, et materialisation d'un fichier a la demande. Voir la section
  « Pattern reservoir » ci-dessous.

## Scripts

### `restic_backup.py`
Sauvegarde dedupliquee a snapshots, depot **local** (disque externe) ou **distant** via
un remote rclone. Auto-init du depot. Mot de passe via `--password-file` ou
`RESTIC_PASSWORD_FILE`/`RESTIC_PASSWORD`.

```
# local
python restic_backup.py --source /chemin/data --repo /mnt/backup/mon-repo \
    --password-file ~/.secrets/restic-pass --exclude _EXPORT

# distant via remote rclone deja configure
python restic_backup.py --source /chemin/data \
    --repo "rclone:monremote:/backups/mon-repo" --password-file ~/.secrets/restic-pass
```

### `rclone_mirror.py`
Miroir incremental (rclone `sync`) vers cible locale ou distante. Remplace robocopy /MIR.

```
python rclone_mirror.py --src /chemin/data --dst /mnt/backup/data
python rclone_mirror.py --src /chemin/data --dst "monremote:/backups/data" --dry
```

## Mise en place d'un remote rclone SFTP (resume, sans valeurs privees)

```
rclone config create <nom> sftp host <HOTE> user <USER> \
    key_file <CHEMIN_CLE_PRIVEE> known_hosts_file <CHEMIN_KNOWN_HOSTS> shell_type unix
# si la host key negociee differe du type epingle :
rclone config update <nom> host_key_algorithms ssh-ed25519
```

Puis pointer `--repo "rclone:<nom>:/chemin"` (restic) ou `--dst "<nom>:/chemin"` (mirror).

## Pattern reservoir (masses de petits fichiers)

1. Conserver la **source de verite compacte** (JSONL, ou SQLite+FTS5) — 1 a quelques
   fichiers au lieu de centaines de milliers.
2. Sauvegarder cette forme compacte (instantane) + optionnellement un miroir des fichiers.
3. **Materialiser** un fichier individuel seulement quand il « gradue » (est retenu),
   depuis la source compacte. Le stockage vif reste leger et rapide.

## Garde-fous

- `--dry` d'abord pour tout miroir/sync avant ecriture reelle.
- Ne jamais committer de secret : le mot de passe restic reste dans un fichier **hors**
  du depot ; l'acces distant passe par un **remote rclone configure localement**, jamais
  par un hote/IP code en dur.
