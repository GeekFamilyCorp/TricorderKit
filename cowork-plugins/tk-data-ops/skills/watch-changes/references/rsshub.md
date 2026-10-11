# RSSHub — fiche de déploiement et routes utiles

Vérifié le 2026-09-07 : README `github.com/DIYgod/RSSHub` (licence **AGPL-3.0**, image `diygod/rsshub`),
fichiers `lib/routes/*/namespace.ts` du dépôt pour les routes citées.

## Licence — à peser

AGPL-3.0 : utiliser RSSHub comme service local **n'impose rien** tant qu'on ne le modifie pas
pour le redistribuer ou l'exposer comme service à des tiers. Si une route maison est ajoutée et le
service ouvert à d'autres, le code de la route doit être publié sous AGPL. En usage strictement
local (127.0.0.1), pas de contrainte.

## Compose générique

```yaml
services:
  rsshub:
    image: diygod/rsshub
    container_name: veille-rsshub
    restart: unless-stopped
    ports:
      - "127.0.0.1:1200:1200"
    environment:
      - CACHE_TYPE=redis
      - REDIS_URL=redis://redis:6379/
      # - ACCESS_KEY=…   → uniquement si le port devait être exposé ; en 127.0.0.1, inutile
      # - PUPPETEER_WS_ENDPOINT=ws://browserless:3000   → routes nécessitant un navigateur
    depends_on: [redis]

  redis:
    image: redis:alpine
    restart: unless-stopped
```

Variables confirmées par le README : `CACHE_TYPE`, `REDIS_URL`, `PUPPETEER_WS_ENDPOINT`, `ACCESS_KEY`.
Port 1200 et nom du service navigateur : usage courant, **à vérifier** sur `docs.rsshub.app/deploy/`.
Un flux se lit ensuite en `http://127.0.0.1:1200/<route>`.

Méthode pour vérifier une route : la liste officielle (`docs.rsshub.app/routes/`) est rendue en
JavaScript ; plus fiable, lire `lib/routes/<namespace>/` dans le dépôt (chaque fichier déclare
`path: '/…'`, un `example` et ses paramètres).

## Quand écrire une route maison

Seulement si : pas de flux natif, pas de route existante, et la page est stable. Sinon, une
surveillance changedetection sur le bloc utile fait le même travail sans code à maintenir.
Une route maison se versionne dans un dossier privé monté dans le conteneur ; elle n'entre dans le
dépôt public que si elle ne contient ni chemin personnel ni secret (R37).

## Chaîne complète

```
site sans flux ──RSSHub──► flux RSS local ──changedetection (ou lecteur)──► notification Apprise
       ──webhook local──► fichier claude/veilles/<slug>/… + message canal_agents
```
Chaque maillon est local et sauvegardable ; aucun service tiers n'est requis.
