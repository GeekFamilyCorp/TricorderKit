# Grille des types de taches

Classification semantique des taches pour determiner le tier de modele.

## T1 - Haiku 4.5 (tache simple, rapide, peu couteuse)

| Categorie | Exemples de prompts |
|-----------|---------------------|
| FAQ / Q&A courte | "quelle est la capitale de X", "c'est quoi Y en une phrase" |
| Resume court | "resume-moi ce paragraphe en 3 lignes" |
| Reformulation | "reformule ceci plus formellement" |
| Traduction simple | "traduis en anglais ce message de 200 mots" |
| Classification | "est-ce un email de spam ?", "categorise ces 10 items" |
| Extraction basique | "extrais les dates de ce texte" |
| Conversation creative courte | dialogue, brainstorming leger, suggestions rapides |
| Corrections typo/orthographe | relecture simple |
| Conversion format simple | JSON -> YAML, CSV -> markdown |

Critere token : input < 1500 tokens ET output attendu < 800 tokens.

## T2 - Sonnet 4.6 (tache standard, polyvalente)

| Categorie | Exemples de prompts |
|-----------|---------------------|
| Redaction article/doc | blog post, doc technique moyenne, email commercial |
| Analyse documentaire | synthese de 2-5 sources, compte-rendu de reunion |
| Code non critique | composant React, script Python d'automatisation, endpoint REST simple |
| Refactor limite | renommage variables, extraction de fonction, cleanup |
| Recherche multi-sources | veille technologique, benchmark produits |
| Orchestration legere | plan de travail a 5-10 etapes, decomposition de projet |
| Analyse de donnees moyenne | pandas / requetes SQL simples / graphiques |
| Redaction commerciale | proposal, one-pager, email sequence |
| Traduction longue ou technique | doc technique, article long |

Critere token : input 1500-15000 tokens, output 800-5000 tokens.

## T3 - Opus 4.6 (tache complexe, critique, multi-etapes)

| Categorie | Exemples de prompts |
|-----------|---------------------|
| Architecture systeme | conception distribuee, ADR, trade-offs techniques |
| Code critique/securite | authentification, crypto, endpoints financiers, migration DB |
| Raisonnement complexe | preuves mathematiques, optimisation combinatoire, decisions strategiques multi-variables |
| Debug complexe | analyse stack trace distribuee, race conditions, memory leaks |
| Planification strategique | roadmap long terme, analyse concurrentielle approfondie |
| Analyse legale/medicale | due diligence, diagnostic differentiel |
| Code multi-fichiers | refactor architectural, migration framework entier |
| Analyse de donnees avancee | stat inferentielle, ML, etudes causales |
| Revue de PR critique | code review securite, perf, architecture |

Critere token : input > 15000 tokens OU complexite cognitive elevee independante de la longueur.

## Signaux de forcage (override la grille)

**Monter d'un tier** si le prompt contient :

- Mentions domaines sensibles : "legal", "medical", "RGPD", "securite", "production", "incident", "critique"
- Exigences qualite : "tres soigne", "pour mon CEO", "pour un client", "deployment"
- Multi-fichier : "dans tous les fichiers", "partout dans le projet"

**Descendre d'un tier** si le prompt contient :

- Brouillon / essai : "premier jet", "quick draft", "idee rapide"
- Exploration : "juste pour voir", "cote creatif"
- Budget sature (cf. budget-tracker)
