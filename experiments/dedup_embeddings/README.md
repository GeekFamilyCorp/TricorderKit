# experiments/dedup_embeddings — PoC #2 (god-mode) : blocking par embeddings pour la dédup

> Radar god-mode 2026-06-22, candidat #2 (~78). **PoC isolé.** État de l'art entity-resolution 2025-26 =
> hybride : **embeddings (nearest-neighbour blocking) PUIS** appariement fuzzy/probabiliste. Les embeddings
> rattrapent ce que le lexical (RapidFuzz) rate : variantes romaji/JP, translittérations.

## Pourquoi TricorderKit
`tools/fuzzy_match.py` (RapidFuzz) est lexical → manque « Tokyo Revengers » vs « 東京卍リベンジャーズ ».
Qdrant + `nomic-embed-text` sont **déjà en place** → un étage de blocking par embeddings avant le fuzzy
améliorerait le rappel de la dédup manga (Oricon, doublons) et réduirait les paires à comparer.

## Plan
1. Indexer les titres candidats (embeddings nomic via Qdrant ou en mémoire).
2. Blocking : pour chaque titre, top-k voisins par cosinus → paires candidates.
3. Étage fuzzy existant (RapidFuzz/`fuzzy_match.py`) sur les seules paires candidates → décision.
4. **Mesure** : rappel/précision sur le jeu de doublons connu (T-2026-06-06-DEDUP-ORICON) avant/après l'étage embeddings.
5. Si gain net → DEC + intégrer comme option dans la dédup du projet de domaine privé (poste lié).

## Garde-fous
Isolé, mesuré avant promotion. Réutilise l'infra existante (pas de nouvelle dépendance lourde).
Réf. : BlockingPy (arXiv 2504.04266), record linkage w/ embeddings (Cambridge) — cf. radar.
