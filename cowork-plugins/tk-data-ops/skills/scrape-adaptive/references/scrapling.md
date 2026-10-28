# Scrapling — fiche technique

Vérifié le 2026-09-07 : README `github.com/D4Vinci/Scrapling`, docs `scrapling.readthedocs.io`
(pages `spiders/getting-started`, `parsing/adaptive`) et `docs/ai/mcp-server.md`.

## Confirmé

| Point | Valeur |
|---|---|
| Licence | BSD-3-Clause |
| Python | ≥ 3.10 |
| Installation | `pip install scrapling` (parseur seul) ; `pip install "scrapling[fetchers]"` puis `scrapling install` (navigateurs et dépendances) ; extras `[ai]` (MCP), `[shell]`, `[all]` |
| Fetchers | `Fetcher` / `FetcherSession` (HTTP, empreinte TLS) · `DynamicFetcher` / `DynamicSession` (Playwright) · `StealthyFetcher` / `StealthySession` (anti-bot) |
| Spider | `Spider` (type Scrapy) ; templates `CrawlSpider`, `SitemapSpider`, `ShopifySpider` |
| Adaptatif | `adaptive=True` (global ou `Selector(html, adaptive=True, url=...)`), `auto_save=True` à la sélection, `adaptive_domain` pour traiter deux domaines comme un seul ; stockage SQLite local par domaine |
| MCP | commande `scrapling-mcp` (stdio ; `--http` pour HTTP), 13 tools ; nécessite `pip install "scrapling[ai]"` + `scrapling install` |
| CLI | `scrapling shell`, `scrapling extract get|fetch|stealthy-fetch URL sortie` |

## Attributs Spider (page getting-started)

`name`, `start_urls`, `allowed_domains` (set), `robots_txt_obey` (bool : respecte `Disallow`,
`Crawl-delay`, `Request-rate`), `download_delay`, `concurrent_requests`,
`concurrent_requests_per_domain`, `autothrottle_enabled` ; méthode `async def parse(self, response)`
(générateur asynchrone qui `yield` des dicts).

```python
from scrapling.spiders import Spider, Response

class Nouveautes(Spider):
    name = "nouveautes"
    start_urls = ["https://exemple.org/nouveautes"]
    allowed_domains = {"exemple.org"}
    robots_txt_obey = True
    download_delay = 2.0
    concurrent_requests_per_domain = 1
    autothrottle_enabled = True

    async def parse(self, response: Response):
        for item in response.css(".item", auto_save=True):
            yield {"titre": item.css("h2::text").get(), "url": response.url}

Nouveautes().start()
```

## À vérifier

- Nom exact du paramètre de checkpoint pour pause/reprise (`crawldir` selon le README, non
  documenté sur la page getting-started) et le format de reprise.
- Manière de fixer le `User-Agent` sur un `Spider` (en-têtes par défaut vs par requête).
- Signature exacte de `Fetcher.get(url, headers=...)` et prise en compte de `headers` avec
  l'empreinte TLS (le script passe `headers={"User-Agent": ...}` ; à confirmer sur la version installée).

## Tools du serveur MCP (`scrapling-mcp`)

One-shot : `make_request`, `bulk_get`, `fetch`, `bulk_fetch`, `stealthy_fetch`, `bulk_stealthy_fetch`.
Session : `open_session`, `open_request_session`, `close_session`, `list_sessions`, `session_fetch`,
`session_make_request`, `screenshot`.

Configuration client :
```json
{ "mcpServers": { "scrapling": { "command": "scrapling-mcp" } } }
```
Sur Windows, donner le chemin complet de l'exécutable (`where scrapling-mcp`). Ces tools n'appliquent
**pas** notre discipline (robots avec UA, throttle, provenance) : ils servent à explorer une page
à la main, pas à faire tourner un collecteur.

## Adaptatif — mode d'emploi

1. Première collecte : `page.css('.titre', auto_save=True)` (l'élément existe).
2. Après refonte : `page.css('.titre', adaptive=True)` relocalise par similarité (balise, texte,
   attributs, parents, voisins).
3. Variante manuelle : `page.save(element, 'id')` / `page.retrieve('id')` / `page.relocate(data)`.
4. Le SQLite adaptatif est un état : sauvegarder avec le collecteur, ne jamais le supprimer
   (NO-DROP), le versionner par date si on le réinitialise.

## Limites et éthique

Le projet lui-même précise : usage éducatif et de recherche, respect des lois, des conditions
d'utilisation et de `robots.txt`. `StealthyFetcher` (contournement de défis anti-bot) ne s'emploie
que sur une cible qui **autorise** la collecte ; il ne transforme pas un refus en autorisation.
