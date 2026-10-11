---
name: scrape-adaptive
description: >-
  Collecte des pages web de façon robuste et respectueuse avec Scrapling (BSD-3 : parseur adaptatif
  qui retrouve un élément après refonte du site, spiders pause/reprise, robots.txt, serveur MCP natif)
  et Playwright en repli pour les pages rendues en JavaScript. À utiliser quand l'utilisateur veut
  « scraper », « récupérer les nouveautés d'un site », « extraire une liste de titres/dates/prix »,
  « mon sélecteur ne marche plus depuis la refonte », « crawler un catalogue avec reprise », « brancher
  le MCP Scrapling », ou préparer un collecteur pour un site exigeant (encodage, rythme,
  conditions d'usage). Applique robots.txt lu avec le User-Agent déclaré, throttle,
  provenance de chaque donnée, inventaire des données locales avant tout nouveau collecteur.
  Fournit scripts/fetch_adaptive.py (--dry-run). Ne pas utiliser pour surveiller un changement de page
  dans le temps → watch-changes, ni pour consommer une API ou un flux RSS déjà existant (appel direct).
license: MIT
allowed-tools: Read, Grep, Glob, Bash(python3:*), WebFetch
metadata:
  version: "0.1.0"
  author: GeekFamilyCorp
  status: public
  plugin: tk-knowledge
compatibility: Python 3.10+ ; scrapling[fetchers] (+ `scrapling install` pour les navigateurs) ; Playwright en repli ; réseau sortant vers les cibles. Aucun service de la stack n'est requis.
---

# scrape-adaptive — Collecter sans casser, ni la cible, ni le pipeline

Un collecteur meurt de deux façons : la cible le bloque (trop vite, mauvais User-Agent, robots
ignoré), ou la cible change (refonte HTML, sélecteur mort). Scrapling traite la seconde avec son
**parseur adaptatif** ; la première se traite par discipline. Ce skill impose les deux.

## 1. Avant d'écrire une ligne (R73)

Lire l'**inventaire des données locales** : ce qu'on veut collecter existe peut-être déjà (base
SQLite d'un pipeline, export précédent, flux RSS, API ouverte). Un collecteur qui refait ce qu'une
base contient déjà coûte des requêtes à la cible pour rien. Écrire en une ligne ce que le
collecteur apportera **en plus** ; si la ligne est vide, ne pas collecter.

## 2. Discipline de collecte

1. **`robots.txt` avec notre User-Agent** (R74) — le lire en envoyant le même `User-Agent` que le
   collecteur ; certains sites servent un `robots.txt` différent ou un 403 selon l'agent, et un
   403 sur `robots.txt` vaut refus total, pas feu vert.
2. **User-Agent nommé** : `NomDuProjetBot/0.1 (+url-de-contact)` — jamais un UA de navigateur
   déguisé sur une cible qui l'interdit. Le nom du projet est une donnée de configuration.
3. **Throttle** : `download_delay` ≥ 2 s, `concurrent_requests_per_domain` = 1, respect de
   `Crawl-delay` s'il existe, `autothrottle_enabled` pour s'adapter.
4. **Provenance** (R41) : chaque enregistrement porte `url`, `collecte_le` (ISO 8601), `collecteur`,
   `version_selecteur`, `hash_contenu`. Sans provenance, une donnée n'est pas réutilisable.
5. **Reprise** : les spiders Scrapling reprennent sur checkpoint ; un lot interrompu redémarre où il
   s'est arrêté, il ne recommence pas de zéro.
6. **Sortie** : JSON Lines, un objet par page, écrit en append ; le script rend 0 seulement s'il a
   écrit au moins un enregistrement (R71).

## 3. Trois niveaux de fetch, dans l'ordre

| Niveau | Outil Scrapling | Quand |
|---|---|---|
| 1 — HTTP | `Fetcher.get(url)` | page servie en HTML complet ; c'est le défaut |
| 2 — navigateur | `DynamicFetcher.fetch(url)` (Playwright) | contenu injecté en JS, scroll infini |
| 3 — furtif | `StealthyFetcher.fetch(url)` | **seulement** si la cible autorise la collecte et bloque les clients non-navigateurs |

Monter d'un niveau coûte 10× plus de ressources et de risque ; on ne monte que sur preuve (niveau 1
ne renvoie pas l'élément attendu). Le niveau 3 n'est pas un outil de contournement d'interdiction :
si `robots.txt` dit non, aucun niveau ne s'applique.

Repli Playwright « nu » (sans Scrapling) : uniquement si Scrapling n'est pas installable ; le
script `scripts/fetch_adaptive.py` gère le message d'installation dans les deux cas.

## 4. Parseur adaptatif — le point fort

Première passe, l'élément existe : `page.css('.titre', auto_save=True)` enregistre ses
caractéristiques (balise, texte, attributs, parents, voisins) dans un SQLite local par domaine.
Après refonte, `page.css('.titre', adaptive=True)` retrouve l'élément par similarité même si le
sélecteur ne matche plus. Conséquence pratique :

- Activer `auto_save` **dès la première collecte**, pas après la panne.
- Journaliser `version_selecteur` ; quand `adaptive` a dû relocaliser, le noter dans la provenance
  et ouvrir une tâche « mettre à jour le sélecteur ».
- Le fichier SQLite adaptatif fait partie de l'état du collecteur : sauvegardé avec lui.

Détails, MCP (`scrapling-mcp`, 13 tools), spiders, options : `references/scrapling.md`.

## 5. Avant la première collecte sur un site

Règle commune : lire les conditions d'utilisation du site en plus de `robots.txt`, et préférer un
flux RSS ou une API quand ils existent (→ `watch-changes` pour le suivi dans le temps).

## 6. Séquence type

1. Inventaire local (§1) → ce qui manque, en une ligne.
2. `python3 scripts/fetch_adaptive.py --dry-run URL` → affiche le plan : UA, robots, niveau, sortie.
3. Collecte d'**une** page, contrôle manuel des champs extraits.
4. Lot de 10 avec throttle ; contrôle des compteurs (pages, erreurs, relocalisations).
5. Lot complet en tâche planifiée, JSONL + journal ; jamais en parallèle d'une autre tâche lourde.

## Changelog

- **2026-09-07 — 0.1.0** : version initiale. Scrapling (adaptatif, spiders, MCP), trois niveaux de
  fetch, discipline R73/R74/R41.
