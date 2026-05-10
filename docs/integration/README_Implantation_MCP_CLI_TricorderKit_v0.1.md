# README — Implantation MCP + CLI MangaTracker dans TricorderKit

Version : v0.1  
Date : 2026-05-10  
Destinataire : Claude / Claude Code  
Projet : TricorderKit × Japan-Alliance × MangaTracker  
Objectif principal : réduire la consommation de tokens en déplaçant l'extraction, le scraping, la normalisation et l'export dans des CLI locaux, puis réserver les MCP aux accès structurés, aux actions contrôlées et à l'orchestration.

---

## 1. Résumé exécutif pour Claude

Tu dois intégrer le pack `mangatracker_cli_pack_v0.1` dans TricorderKit comme une couche d'outillage local.

Principe central :

```text
Ne pas utiliser un agent conversationnel pour scraper, lister, parser ou comparer de grands volumes.
Utiliser les CLI pour les tâches répétitives et volumineuses.
Utiliser les MCP uniquement pour accéder à des systèmes externes structurés ou déclencher des commandes contrôlées.
```

Le CLI doit produire des fichiers Markdown / JSON / logs exploitables. Claude doit ensuite lire uniquement les sorties finales, pas les pages sources complètes.

L'objectif est de transformer TricorderKit en système agentique sobre :

```text
source japonaise
→ CLI métier
→ fichier normalisé court
→ cache local
→ export Obsidian / JSON
→ lecture par Claude
→ synthèse / décision / correction
```

---

## 2. Principe CLI-first

| Cas | Outil à utiliser | Raison |
|---|---|---|
| Scraper une page web | CLI | Évite de copier de grandes pages dans le contexte |
| Scanner plusieurs sources japonaises | CLI batch | Réduit les appels agentiques |
| Normaliser des résultats | CLI | Traitement déterministe |
| Lire une synthèse courte | Claude | Valeur ajoutée du modèle |
| Mettre à jour une fiche validée | Claude ou MCP contrôlé | Action ciblée |
| Accéder à kintone | MCP kintone ou cli-kintone | Accès structuré |
| Exporter vers Obsidian | CLI | Fichiers stables |
| Décision éditoriale | Claude | Raisonnement humain/éditorial |

---

## 3. Modules CLI disponibles

```text
mangatracker manga scan-new --source shonenjumpplus --type chapter1
mangatracker ln scan-ranking --source syosetu
mangatracker anime scan-news --source comic-natalie
mangatracker seiyu scan-agency --agency aoni
mangatracker studio scan --studio mappa
mangatracker game scan-news --source famitsu
mangatracker goods scan-maker --maker goodsmile
mangatracker events scan --source animejapan
mangatracker sync obsidian --vault ./exports
mangatracker sync kintone --table sources
mangatracker audit sources
```

---

## 4. Configuration MCP projet

Fichier `.mcp.json` à la racine — kintone via variables d'environnement.
Secrets dans `.env` (jamais committés).
Variables : `KINTONE_BASE_URL`, `KINTONE_API_TOKEN`.

---

## 5. Sécurité

- Whitelist CLI stricte dans `mcp/README_MCP_POLICY.md`
- Dry-run obligatoire pour les modifications massives
- Hooks Claude Code : `validate_no_secret_commit.py`, `token_budget_guard.py`
- Aucun secret dans Git
