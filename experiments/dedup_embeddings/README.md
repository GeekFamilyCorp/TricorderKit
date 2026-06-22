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

## Livré (PoC exécutable, hors-ligne)
`dedup_embeddings.py` — pipeline **hybride** : blocking par embeddings (top-k cosinus) PUIS étage fuzzy
(Levenshtein, substitut RapidFuzz). Mesure recall / precision / F1 + nombre de comparaisons pour
(a) fuzzy exhaustif O(n²) vs (b) blocking + fuzzy. Deux moteurs : `proxy` (n-grammes de caractères,
déterministe, hors-ligne) et `nomic` (vrais embeddings via `EMBED_URL`, repli auto).

```
python dedup_embeddings.py --selftest
python dedup_embeddings.py --dataset sample_titles.jsonl
```

**Résultats mesurés (2026-06-22)** : le blocking atteint **la même qualité que le fuzzy exhaustif**
(dataset générique : rappel 1.0, F1 0.909) pour **-91 % de comparaisons** (66 → 6) ; selftest
-82 % (28 → 5). Limite honnête : la variante romaji (« Tokyo » vs « Toukyou ») n'est **pas** captée
par le proxy lexical — c'est exactement le rappel sémantique que le moteur `nomic` doit apporter,
à mesurer ensuite.

## Prochaines étapes (vers la promotion)
1. Brancher le moteur `nomic` (Qdrant + `nomic-embed-text`) et re-mesurer le rappel cross-script.
2. Mesure sur le jeu de doublons réel (cf. radar) avant/après l'étage embeddings.
3. Si gain net → DEC + intégrer comme option dans la dédup du projet de domaine privé (poste lié).

## Garde-fous
Isolé, mesuré avant promotion. Réutilise l'infra existante (pas de nouvelle dépendance lourde).
Données d'exemple génériques (aucun contenu métier privé), zéro écriture vault.
Réf. : BlockingPy (arXiv 2504.04266), record linkage w/ embeddings (Cambridge) — cf. radar.
