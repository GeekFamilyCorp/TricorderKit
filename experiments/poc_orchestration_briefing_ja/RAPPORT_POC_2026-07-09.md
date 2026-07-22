# PoC — Orchestration multi-agent vs prompt unique (candidat #1, radar god-mode 2026-07-06)

Statut : **tranché — GO Sébastien 2026-07-09** ([[00_SYSTEM/DECISIONS/DEC-062_architecture-briefing-ja-agent-unique]], repo claude-vault). Décision appliquée à `PROJECT_APP_MULTI_AGENTS.md` (choix d'architecture uniquement — le prototypage code reste à faire). PoC isolé, aucune intégration cœur ; ne modifie ni `orchestrator.py` ni aucun skill existant.
Cas testé : démo prévue par `PROJECT_APP_MULTI_AGENTS.md` — **"Briefing matinal Japan Alliance"** (agent_mémoire lit HOT_CACHE → agent_japan_alliance cherche les sorties Shueisha de la semaine → agent_mémoire logue dans le Daily Log). Ce cas n'est pas encore construit en dur ; ce PoC informe le choix d'architecture avant de le coder.

## 0. Pivot par rapport à la demande initiale

Le radar god-mode #2 avait suggéré de tester le candidat #1 (arXiv 2604.27891, *"In-Context Prompting Obsoletes Agent Orchestration for Procedural Tasks"*) sur le sous-flux `ln-validator` (contrôle schéma LN). En lisant `SKILL.md` de `ln-validator`, il s'avère que ce flux est un **pipeline de scripts Python déterministes** (`ln_validate.py` → dispatch `ln_enrich_gaps.py`, appels API Narou/openBD/AniList/Wikidata/BookWalker), sans jugement LLM en boucle, déjà à 185/187 fiches correctement graduées (98,9 %). Il n'y a donc **aucune orchestration LLM à remettre en cause** sur ce flux — le tester aurait été un test vide. Pivot validé par Sébastien vers le cas "Briefing matinal Japan Alliance", qui est le seul flux de l'écosystème actuel à correspondre réellement au profil du papier (chaîne procédurale de plusieurs **agents LLM** séquentiels, pas encore figée en code).

## 1. Protocole

**Méthode A — multi-agent (architecture telle que documentée dans PROJECT_APP_MULTI_AGENTS.md)** : 3 appels d'agent isolés via le Task tool, chacun ne recevant QUE ce que l'agent précédent lui transmet (péримètre défini, pas de contexte partagé) :
1. `agent_mémoire` #1 — lit `HOT_CACHE.md` seul, produit un résumé de 5-8 lignes pour la suite.
2. `agent_japan_alliance` — reçoit uniquement ce résumé + sa consigne, fait la recherche web, produit un briefing texte.
3. `agent_mémoire` #2 — reçoit uniquement le briefing de l'étape 2, rédige l'entrée de Daily Log (dry-run, rien écrit sur disque).

**Méthode B — prompt unique (auto-orchestration)** : une seule passe continue (moi, dans le même contexte tout du long) : lecture de `HOT_CACHE.md` → recherche web → rédaction de l'entrée, sans hand-off ni reset de contexte, avec le contexte complet disponible à chaque étape.

Même tâche exacte, même fenêtre (semaine du 6-12 juillet 2026), même éditeur cible (Shueisha / Weekly Shōnen Jump).

## 2. Résultats — Méthode A (multi-agent)

| Étape | Coût mesuré |
|---|---|
| Agent 1 (mémoire→lecture) | 48 986 tokens, 1 tool use, 15,1 s |
| Agent 2 (recherche web) | 39 842 tokens, 4 tool use, 50,8 s |
| Agent 3 (rédaction log) | 38 191 tokens, 3 tool use, 34,5 s |
| **Total** | **~127 000 tokens, 8 tool uses, ~100 s, 3 contextes séparés** |

**Sortie finale (extrait)** : entrée Daily Log correcte sur la forme, mais :
- **Erreur factuelle non détectée** : tirage supplémentaire annoncé à **50 000** exemplaires (au lieu de 500 000 réels — vérifié ci-dessous, 2 sources indépendantes). Erreur d'un facteur 10, produite par l'agent 2 et **transmise sans vérification** par l'agent 3, qui n'avait aucun moyen de la recouper (il ne voit que le texte reçu, pas les sources brutes).
- **Lacune signalée mais non comblée** : l'agent 3 note lui-même, dans sa "Note de complétude", qu'il manque le contenu chapitre-par-chapitre du numéro du 6 juillet — parce que l'agent 2 ne l'avait pas cherché sous cet angle (recherche trop generale sur "sorties Shueisha", pas sur le sommaire précis du numéro).
- Isolation du contexte confirmée : agent 2 n'avait aucune idée du contenu du HOT_CACHE au-delà du résumé de 5 lignes reçu (conforme à l'architecture "périmètre défini" prévue).

## 3. Résultats — Méthode B (prompt unique)

Même recherche relancée dans le même contexte que la lecture du HOT_CACHE (2 requêtes WebSearch, contre 4 tool_uses côté agent 2 seul en méthode A — pas de perte de temps à reformuler une consigne "à l'aveugle").

**Différences constatées, à consigne identique** :
- **Correction de l'erreur numérique** : une 2e recherche ciblée ("500000 OR 50000") a permis de trouver 2 sources indépendantes (jumpichiban.com, x.com/pokemon_viet) confirmant **500 000** exemplaires supplémentaires — pas 50 000. Rien dans la méthode A n'aurait déclenché cette re-vérification : chaque agent traitait l'info reçue comme acquise.
- **Comblement de la lacune identifiée par l'agent 3 en méthode A** : une recherche complémentaire ("Jump Database... issue 32 33 contents") a trouvé le **sommaire réel du n°32 du 6 juillet** (One Piece #1187, Blue Box #249, Hunter × Hunter #412, Sakamoto Days #266, Witch Watch #253, Akane-banashi #213 couleur, etc.) — l'exact manque que l'agent 3 de la méthode A avait signalé sans pouvoir le combler (il n'avait pas la main pour relancer une recherche).
- Aucun hand-off, aucune perte d'information entre "lecture mémoire" et "rédaction finale" : le lien avec le contexte HOT_CACHE (rien sur Shueisha spécifiquement, mentions adjacentes shogakukan-comic.jp/akitashoten.co.jp) reste disponible nativement pour la rédaction finale, sans dépendre de la fidélité d'un résumé intermédiaire.

## 4. Verdict

| Critère | Méthode A (multi-agent) | Méthode B (prompt unique) |
|---|---|---|
| Exactitude factuelle | ❌ erreur ×10 non détectée (propagée sans contrôle) | ✅ corrigée (re-vérification naturelle) |
| Complétude (sommaire réel du numéro) | ❌ lacune identifiée mais non comblée (pas de boucle de rattrapage) | ✅ comblée dans la même passe |
| Coût / latence | ~127k tokens, 8 tool uses, ~100 s, 3 contextes | moindre : 2 recherches web dans un seul contexte continu, pas de coût de hand-off (résumés intermédiaires, attente inter-agent) |
| Traçabilité | Chaque étape isolée = plus facile à auditer isolément (avantage réel de A) | Une seule trace, mais complète et cohérente de bout en bout |

**Conclusion pour ce cas précis** : sur une tâche procédurale bien définie et courte (3 étapes, peu de branchement), **le prompt unique auto-orchestré a été supérieur sur l'exactitude, la complétude et le coût**, confirmant directement le signal du candidat #1 pour ce type de flux. Le point faible réel de la méthode A n'est pas le multi-agent en soi, mais l'**absence de boucle de vérification croisée entre agents** : chaque agent fait confiance au texte reçu de l'agent précédent sans recouper les faits ni pouvoir relancer une recherche complémentaire hors de son périmètre étroit.

**Recommandation (proposition, pas d'application automatique)** : pour l'App Multi-Agents, ne pas construire "Briefing matinal Japan Alliance" comme 3 agents séparés avec hand-off texte. Deux options à arbitrer par Sébastien :
1. **Un seul agent** (scope large "recherche + mémoire" pour ce cas précis), qui lit HOT_CACHE, cherche, rédige — sans découpage agent_mémoire/agent_japan_alliance pour CE cas.
2. Si la séparation d'agents reste voulue pour d'autres raisons (auditabilité, permissions différenciées écriture/lecture), **ajouter une étape de vérification croisée** (l'agent de rédaction doit pouvoir relancer une recherche complémentaire, pas seulement accepter le texte reçu) — ce qui réduit une partie de l'avantage coût du multi-agent.
Le protocole d'actions critiques (validation écriture) de `PROJECT_APP_MULTI_AGENTS.md` reste valable dans les deux cas — ce PoC ne teste que l'orchestration lecture/recherche, pas l'écriture réelle (dry-run respecté, rien écrit dans le Daily Log réel).

**Limite du PoC** : un seul cas testé, un seul run par méthode (pas de moyenne sur plusieurs essais) — signal utile mais pas une preuve statistique. Le papier source lui-même portait sur des domaines conversationnels (support client), pas des pipelines outillés comme celui-ci ; ce PoC est la vérification-maison demandée précisément parce que la généralisation n'était pas garantie.

## Sources (vérification de l'erreur méthode A)
- [Weekly Shonen Jump Issue 32, 2026 — Jump Database (Fandom)](https://jump.fandom.com/wiki/Weekly_Shonen_Jump_Issue_32,_2026) — sommaire réel du n°32.
- [Weekly Shonen Jump 33 Issue 2026 — jumpichiban.com](https://jumpichiban.com/en-us/products/weekly-shonen-jump-33-issue-2026-include-special-limited-edition-one-piece-card-bonus-item) — 500 000 exemplaires supplémentaires.
- [x.com/pokemon_viet/status/2072518023974654069](https://x.com/pokemon_viet/status/2072518023974654069) — confirmation indépendante des 500 000 exemplaires.
- [ONE PIECE Card Game Featuring Monkey D. Luffy — ORICON NEWS](https://us.oricon-group.com/news/8984/).

*PoC exécuté par Claude (lane god-mode / App Multi-Agents), 2026-07-09. Rapport isolé dans `experiments/` — aucune modification du cœur TricorderKit ni de skills existants.*
