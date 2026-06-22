---
name: god-mode
description: Radar d'innovation et moteur d'auto-amélioration de TricorderKit. À utiliser quand l'utilisateur veut surveiller l'état de l'art, trouver des innovations récentes, "que sort-il de neuf en IA", chercher comment améliorer TricorderKit/un de ses modules, faire une veille techno priorisée, ou alimenter le self-improving en candidats. Scanne une base de sources de référence (arXiv, Papers with Code, IEEE, awesome-*, ResearchRabbit…), classe par pertinence pour TricorderKit, et PROPOSE des améliorations (validation humaine, jamais d'adoption automatique). NE PAS utiliser pour une simple recherche factuelle ponctuelle (déléguer à deep-research) ni pour un lookup de domaine manga/anime.
---

# god-mode — Radar d'innovation & auto-amélioration de TricorderKit

> Transforme une veille dispersée en **flux priorisé de candidats d'amélioration**. On part des
> meilleures sources, on filtre par pertinence pour TricorderKit, on classe, et on **propose** —
> l'adoption reste un acte humain (DEC + gates). Complète, sans dupliquer : `deep-research-core`
> (exécution de recherche), `learning-engine` (propose/promote), lane `tool_scout` (self-improving),
> `reflection.py` (capture passive). god-mode = la **couche de cadrage + sources + ranking** au-dessus.

## 1. Quand se déclencher
« veille techno », « état de l'art / SOTA sur X », « quoi de neuf en IA », « comment améliorer
TricorderKit / le RAG / la dédup / l'orchestration », « trouve des innovations », « alimente le tool_scout ».

## 2. Base de sources (God Mode List) — `sources.yaml`
Sources tierées (détail + politique dans `skills/god-mode/sources.yaml`) :
- **Primaire (papers + SOTA+code)** : arXiv, Papers with Code. → autorité, reproductibilité.
- **Adoption / curation** : awesome-machine-learning, awesome-public-datasets (GitHub). → maturité, étoiles.
- **Découverte / graphe de citations** : ResearchRabbit, Litmaps. → voisinage d'un papier clé.
- **Analytique / portée** : Google Scholar, IEEE Xplore, Dimensions. → citations, validation académique.

Priorité par défaut : **Papers with Code** (SOTA + code = adoptable) > **arXiv** (fraîcheur) >
**awesome-* / GitHub** (maturité) > découverte/analytique (approfondissement).

## 3. Protocole de scan (déterministe)
1. **Cadrer la cible** : un thème TricorderKit (cf. §4) ou une question utilisateur.
2. **Router vers les bonnes sources** (§2) — au moins 2 sources, primaire d'abord.
3. **Collecter** via `deep-research-core` / WebSearch / web_fetch (ne pas réimplémenter le fetch).
4. **Dédupliquer** (titre + auteurs ; pas le nom seul).
5. **Classer** par score (§5).
6. **Mapper** chaque candidat à un module TricorderKit (§4) + effort estimé.
7. **Proposer** : écrire un rapport de candidats dans `canal_agents/commands/claude_inbox/` ou
   `learning-engine` (propose), statut `à_valider`. **Aucune adoption sans DEC + GO.**

## 4. Carte cible — thème → module TricorderKit
| Thème | Module / plugin TK concerné |
|---|---|
| RAG, recherche hybride, reranking, GraphRAG | `graphify` (Qdrant+Neo4j+RRF+reranker) |
| Entity resolution / dédup / fuzzy matching | `tools/fuzzy_match.py` (RapidFuzz) + dédup vault |
| Scraping, anti-bot, extraction markdown | `scraper-runtime` |
| Orchestration agents / workflows durables | `workflow-engine` (Temporal/LangGraph) |
| Mémoire (court/long terme, consolidation) | `memory-boot` + vault + `reflection.py` |
| Éval qualité / benchmarks | `eval-lab` |
| Routage modèle / coût / compression | `token-optimizer` |
| Ingestion documents (PDF/DOCX/…) | `document-ingestion` |

## 5. Heuristique de classement (score 0-100)
`score = 40·pertinence_TK + 30·adoption + 20·récence + 10·faisabilité`
- **pertinence_TK** : recoupe un module §4 et un manque réel (gap).
- **adoption** : SOTA sur Papers with Code, étoiles GitHub, code dispo, maturité (≠ papier seul).
- **récence** : ≤ 12 mois favorisé ; mais une référence stable très adoptée garde de la valeur.
- **faisabilité** : intégrable sans GPU si possible, licence compatible (cf. garde-fous).
Ne **proposer** que les candidats ≥ seuil (défaut 60) ; lister les autres en « à surveiller ».

## 6. Métacognition & évaluation (issu de la méthode expert-IA)
Pour chaque candidat retenu, renseigner : problème TK qu'il résout, métrique d'amélioration attendue,
risque/coût, **explicabilité** (le gain est-il mesurable/justifiable ?), et une **hypothèse testable**
(idéalement un cas pour `eval-lab` ou un PoC isolé `experiments/`). Boucle : proposer → PoC → mesurer → DEC.

## 7. Garde-fous (non négociables)
- **100 % proposition** : god-mode ne modifie jamais le cœur ; il alimente `learning-engine`/`tool_scout`/`claude_inbox`.
- **≥ 2 sources** indépendantes ; source primaire/officielle d'abord ; citer URL + date.
- **Licence** : pour le dépôt public, bannir AGPL/copyleft viral (ex. piège Firecrawl déjà noté) ; vérifier avant toute reco d'intégration.
- **YAGNI** : ne pas anticiper ce qui duplique l'existant (LiteLLM, Temporal, Qdrant…) ; arbitrer comme la roadmap net-new.
- **Anti-hallucination** : pas de « SOTA » affirmé sans la source ; un benchmark = un lien Papers with Code/arXiv daté.

## 8. Cadence
- **À la demande** (ce skill) sur un thème.
- **Planifiable** : passe hebdo par thème, déposée sur le bus (lane `tool_scout`) → revue humaine.
- S'emboîte dans `caps` (capability `local-llm`/`graph` si enrichissement) et le bus canal_agents.

## 9. Sortie attendue (gabarit)
Rapport `GODMODE_RADAR_<thème>_<date>.md` :
- Top candidats (score, source+date, module TK cible, gain attendu, effort, licence).
- « À surveiller » (sous le seuil).
- Pour chaque top : hypothèse testable + prochaine étape (PoC `experiments/` ou DEC).
- Jamais d'application directe — proposition seule.
