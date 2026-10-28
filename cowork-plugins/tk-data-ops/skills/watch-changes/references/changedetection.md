# changedetection.io — fiche de déploiement et de réglage

Vérifié le 2026-09-07 : README `github.com/dgtlmoon/changedetection.io` et PyPI. Licence **Apache-2.0**.
Image Docker : `dgtlmoon/changedetection.io`.

## Compose générique (port lié à 127.0.0.1)

```yaml
services:
  changedetection:
    image: dgtlmoon/changedetection.io
    container_name: veille-changedetection
    restart: unless-stopped
    ports:
      - "127.0.0.1:5000:5000"
    volumes:
      - changedetection-data:/datastore
    environment:
      - BASE_URL=http://127.0.0.1:5000
      # Pages rendues en JavaScript : décommenter et ajouter le service navigateur ci-dessous
      # - PLAYWRIGHT_DRIVER_URL=ws://sockpuppetbrowser:3000
    # depends_on: [sockpuppetbrowser]

  # sockpuppetbrowser:
  #   image: dgtlmoon/sockpuppetbrowser
  #   restart: unless-stopped
  #   cap_add: [SYS_ADMIN]

volumes:
  changedetection-data:
```

Lancement : `docker compose up -d` (proposé, exécuté sur GO). Interface : `http://127.0.0.1:5000`.
Nom d'image du navigateur compagnon et variables associées : **à vérifier** dans le README au moment
de l'activer (l'exemple ci-dessus reprend la variable `PLAYWRIGHT_DRIVER_URL` documentée).

## Réglages d'une surveillance

| Réglage | Recommandation |
|---|---|
| Sélecteur | CSS ou XPath (1.0/2.0) sur le bloc utile ; pour une API ou un JSON embarqué : JSONPath / jq |
| Texte à ignorer | dates du jour, compteurs de vues, « il y a N minutes » |
| Fréquence | alignée sur le rythme réel de la source (quotidien pour un hebdo) |
| Méthode | « texte » par défaut ; « visuel » seulement si la mise en page est la donnée |
| User-Agent | en-tête personnalisé nommé (`NomBot/0.1 (+contact)`), identique à celui des collecteurs (R74) |
| Tags | un tag par thème de veille (`releases`, `classements`, `articles`) |

## Notifications (Apprise)

changedetection s'appuie sur Apprise : Discord, Slack, Telegram, e-mail, Teams, Rocket.Chat et
tout ce qu'Apprise sait adresser, via des URL de notification. Pour un pipeline local :

- **Webhook local** (`json://127.0.0.1:PORT/chemin`) reçu par un petit service qui écrit le fichier
  de veille et le message de bus (procédure `SKILL.md` §4).
- **E-mail dédié** si aucun service ne tourne : boîte lue par un agent, pas la boîte personnelle.

Le corps de notification peut inclure le diff ; le borner (~40 lignes) pour rester lisible.
Les secrets d'une URL Apprise (jeton Telegram, mot de passe SMTP) se saisissent dans l'interface,
jamais dans le compose versionné ; si une variable d'environnement les porte, elle vient du
gestionnaire d'identifiants.

## API REST

Interface OpenAPI intégrée : création de surveillances, tags, notifications par script. Utile pour
provisionner 20 surveillances d'un coup à partir d'une liste ; clé d'API dans les réglages, à
transmettre par en-tête depuis une variable d'environnement.

## Sauvegarde et hygiène

- Le volume `/datastore` contient historique, captures et configuration : inclus dans les sauvegardes.
- Une surveillance qu'on retire se **désactive** (NO-DROP) ; on ne la supprime qu'après export.
- Ne pas cumuler navigateur Playwright + modèle LLM lourd sur le même poste en même temps (RAM).
