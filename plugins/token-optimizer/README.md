# token-optimizer

**Plugin Claude Cowork / Claude Code** — Routeur intelligent Haiku/Sonnet/Opus avec compression de sortie caveman, compression de contexte, docs fraiches et suivi de budget mensuel.

> Inspire de cinq projets remarquables :
> - [obra/superpowers](https://github.com/obra/superpowers) — framework de skills composables
> - [upstash/context7](https://github.com/upstash/context7) — injection de docs a jour via MCP
> - [muratcankoylan/Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) — context engineering
> - [rtk-ai/rtk](https://github.com/rtk-ai/rtk) — proxy CLI Rust qui compresse les sorties (-60 a -90% tokens)
> - [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) + [GabrielBarberini/laconic](https://github.com/GabrielBarberini/laconic) — compression de sortie prose -75 a -90%

## Pourquoi ce plugin

Par defaut, une seule taille de modele est utilisee pour toute tache et les reponses sont verbeuses. Resultat : on paie Opus pour des traductions, et Haiku redige des romans pour une question simple. **token-optimizer** classifie chaque requete, choisit le bon modele ET compresse automatiquement les sorties via le mode caveman — double economie sur input et output.

Gains typiques mesurables :

- **Routage modele** : -50 a -80% de cout input sans perte de qualite
- **Caveman (sortie)** : -65 a -90% tokens output sur T1/T2 (benchmarks reels JuliusBrussee/laconic)
- **Context7 (docs fraiches)** : -65% de tokens de contexte et zero hallucination d'API
- **rtk (compression CLI)** : -60 a -90% sur les sorties git/npm/docker/pytest/kubectl
- **Compression de contexte structuree** : -70% sur les sessions longues sans perte d'info critique

## Composants du plugin

| Composant | Role |
|-----------|------|
| **Skills** | |
| `model-router` | Skill central : classifie + active caveman + route vers Haiku/Sonnet/Opus |
| `caveman` | Compression sortie prose -75 a -90% (caveman full/lite/ultra) |
| `task-classifier` | Classification deterministe avec score 0-100 |
| `budget-tracker` | Suivi conso mensuelle, alertes 50/80/95% |
| `context-compress` | Compression structuree du contexte (techniques muratcankoylan) |
| `docs-fresh` | Wrapper Context7 pour docs a jour sans hallucination |
| `cli-compress` | Wrapper rtk pour compresser les sorties de commandes |
| **Agents** | |
| `haiku-executor` | Execute les taches T1 (simples, courtes) |
| `sonnet-executor` | Execute les taches T2 (standard, polyvalentes) |
| `opus-executor` | Execute les taches T3 (complexes, critiques) |
| **MCP** | |
| `context7` | Serveur MCP Upstash pour docs fraiches (npx auto) |
| **Hooks** | |
| `PreToolUse/Bash` | Reecrit les commandes shell via rtk pour compression |
| `PostToolUse/Task` | Log automatique de la conso de tokens dans le budget |
| **Scripts** | |
| `scripts/classify.py` | Classifieur Python autonome (CLI) |
| `scripts/budget.py` | Suivi de budget (status / log / log-from-task / reset / set-budget) |
| `scripts/rtk-rewrite.sh` | Hook de reecriture des commandes |
| `scripts/rtk-install.sh` | Installer one-shot pour rtk |

## Utilisation

### Cas typique : le routeur fait tout

Posez simplement votre question. Le plugin intercepte via le skill `model-router`, classifie, active caveman, route.

```
Vous : "Traduis cette phrase en anglais"
Plugin :
  Classification : T1 (traduction simple)
  Modele choisi : Haiku 4.5
  Mode caveman : full (~75% tokens sortie economises)
  -> delegation a haiku-executor
```

```
Vous : "Concois l'architecture d'un systeme de paiement multi-tenant PCI-DSS"
Plugin :
  Classification : T3 (architecture + domaine sensible)
  Modele choisi : Opus 4.6
  Mode caveman : desactive (document formel)
  Optimisations : docs-fresh (payment libs)
  -> delegation a opus-executor
```

### Forcer un mode caveman

```
"mode caveman lite"       -> reponses professionnelles serrees (-45% tokens)
"mode caveman full"       -> style caveman classique (-75% tokens)
"mode caveman ultra"      -> abreviations maximales (-90% tokens)
"stop caveman"            -> retour au mode normal
```

### Forcer un modele

```
"Utilise Opus : donne-moi 5 synonymes de rapide"    -> force Opus
"Mode economique : analyse ce code de 500 lignes"   -> force Haiku
"Critique : deploie cette migration"                 -> ignore la desescalade budget
```

## Architecture en flux

```
Prompt utilisateur
       |
       v
  [model-router]  <--- [budget-tracker] (consulte)
       |
       |--- [caveman] (T1: full, T2: lite, T3: off)  --> -75% tokens output
       |--- [context-compress] (si ctx > 60% fenetre) --> -70% tokens contexte
       |--- [docs-fresh] (si lib mentionnee) -------> MCP Context7
       |
       v
  Tier T1 / T2 / T3
       |
       v
  haiku-executor / sonnet-executor / opus-executor
       |
       |--- [cli-compress] via hook rtk (si cmd bash) --> -80% tokens CLI
       |
       v
  Reponse compressee
```

## Licence

MIT. Les cinq projets sources conservent leurs licences respectives.
