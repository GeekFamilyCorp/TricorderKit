---
name: watch-changes
description: >-
  Met en place et exploite une veille de changements de pages et de flux, en local : changedetection.io
  (Apache-2.0, sélecteurs CSS/XPath/jq, notifications Apprise) pour surveiller des pages, RSSHub
  (AGPL-3.0) pour transformer des sites sans flux en RSS, puis route chaque changement détecté vers un
  fichier de veille daté ou un message sur le bus des agents. À utiliser quand l'utilisateur veut
  « être prévenu quand cette page change », « surveiller les nouveautés d'un site », « générer un
  flux RSS pour un site qui n'en a pas », « brancher une veille sur le digest », « configurer
  changedetection », « quelle route RSSHub pour ce site », ou quand un changement a été détecté et
  qu'il faut le consigner. Ne pas utiliser pour extraire des données structurées d'une page →
  scrape-adaptive, ni pour surveiller l'état d'un service ou d'un timer (observabilité).
license: MIT
allowed-tools: Read, Write, Grep, Glob, Bash(python3:*), Bash(docker:*), WebFetch
metadata:
  version: "0.1.0"
  author: GeekFamilyCorp
  status: public
  plugin: tk-knowledge
compatibility: Docker local (conteneurs changedetection.io et RSSHub, en 127.0.0.1) ; Playwright/sockpuppetbrowser optionnel pour les pages JS ; dossier de veille versionné et bus des agents (fichiers) pour la sortie.
---

# watch-changes — Savoir qu'une page a changé, et en faire quelque chose

Une veille a deux moitiés : **détecter** (l'outil regarde à notre place) et **consigner** (le
changement devient une entrée datée que quelqu'un — humain ou agent — lira). Beaucoup de veilles
meurent parce que la seconde moitié manque : l'outil notifie dans le vide. Ce skill couvre les deux.

## 1. Choisir l'outil

| Besoin | Outil | Pourquoi |
|---|---|---|
| Une page précise change (prix, date, liste) | **changedetection.io** | diff ciblé par sélecteur, historique, notifications |
| Un site publie régulièrement sans flux RSS | **RSSHub** | route → flux RSS lisible par tout lecteur ou par changedetection |
| Un site a déjà un flux RSS/Atom | ni l'un ni l'autre : lire le flux directement | moins de pièces mobiles |
| Il faut des champs structurés (rang, ISBN…) | → `scrape-adaptive` | la veille dit « ça a bougé », pas « voici les données » |

Vérifier d'abord l'existence d'un flux natif (`<link rel="alternate" type="application/rss+xml">`,
`/feed`, `/rss`) : c'est le cas le plus fréquent et le plus stable.

## 2. Installer (une fois)

Les deux outils tournent en conteneurs locaux, ports liés à `127.0.0.1` uniquement — rien
n'est exposé au LAN. Compose générique, variables, sélecteurs, notifications :
`references/changedetection.md` ; routes utiles et déploiement : `references/rsshub.md`.

Toute installation ou modification de conteneur est **proposée** avant d'être exécutée (R53) :
un `docker compose up` ne casse rien en général, mais un port déjà pris ou un volume mal nommé se
règle avant, pas après.

## 3. Configurer une surveillance qui tient

1. **Sélecteur étroit** : surveiller le bloc utile (`.liste-nouveautes`), pas la page entière —
   sinon chaque bannière déclenche une fausse alerte.
2. **Filtres** : ignorer dates du jour, compteurs, publicités (texte à ignorer, regex).
3. **Fréquence** honnête : une page hebdomadaire se vérifie une fois par jour, pas toutes les 5 min.
   La veille est un client comme un autre : User-Agent nommé, `robots.txt` respecté (R74).
4. **Notification Apprise** vers un point que le pipeline sait lire : un webhook local, un
   fichier, un e-mail dédié — pas une messagerie personnelle qu'on ne relira pas.
5. **Étiquette** (tag) par thème pour retrouver les surveillances d'un même domaine.

## 4. Quand un changement est détecté → consigner

Un changement produit **une entrée**, jamais deux fois la même (dédoublonner par hash du diff) :

1. Créer `claude/veilles/<slug>/<AAAA-MM-JJ>_<slug>_<hash8>.md` avec : source (URL), détectée le
   (ISO 8601), sélecteur, **diff** (extrait borné, ~40 lignes), lien vers l'historique
   changedetection, statut `a_qualifier`.
2. Ajouter une ligne au `JOURNAL_<slug>.md` du même dossier (date · résumé en une ligne · lien).
3. Si le bus des agents est en place : déposer un message `canal_agents` du type
   `{"event":"veille_changement","slug":…,"fichier":…,"hash":…}` — un message par changement,
   posté après le fichier, jamais avant (R55 : garde séquentielle).
4. Qualifier ensuite, à la main ou par un agent : `pertinent` / `bruit` / `a_collecter`
   (→ `scrape-adaptive` si des données structurées sont à extraire).

Ce qui est consigné est ce qui existe (R79) ; une notification lue puis oubliée n'existe pas.

## 5. Entretien

- Chaque mois : lister les surveillances sans changement depuis 90 jours (la page est morte ou le
  sélecteur l'est) et celles qui déclenchent tous les jours (sélecteur trop large).
- Sauvegarder le volume `datastore` de changedetection avec les autres états (NO-DROP).
- Une route RSSHub qui casse est un signal, pas une panne à cacher : consigner, chercher le flux
  natif, sinon basculer vers une surveillance changedetection de la page.

## Changelog

- **2026-09-07 — 0.1.0** : version initiale. changedetection.io + RSSHub, choix d'outil, réglages
  anti-bruit, procédure de consignation fichier de veille + bus.
