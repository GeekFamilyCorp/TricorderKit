# experiments/dedup_embeddings — PoC #2 (god-mode) : blocking par embeddings pour la dédup

> Radar god-mode 2026-06-22, candidat #2 (~78). **PoC isolé.** État de l'art entity-resolution 2025-26 =
> hybride : **embeddings (nearest-neighbour blocking) PUIS** appariement fuzzy/probabiliste. Les embeddings
> rattrapent ce que le lexical (RapidFuzz) rate : translittérations, alphabets différents.

## Pourquoi TricorderKit
`tools/fuzzy_match.py` (RapidFuzz) est lexical → il manque « Moscow » vs « Москва ».
Qdrant + `nomic-embed-text` sont **déjà en place** → un étage de blocking par embeddings avant le fuzzy
améliore le rappel de la dédup et réduit le nombre de paires à comparer.

## Plan
1. Indexer les titres candidats (embeddings nomic via Qdrant ou en mémoire).
2. Blocking : pour chaque titre, top-k voisins par cosinus → paires candidates.
3. Étage fuzzy existant (RapidFuzz/`fuzzy_match.py`) sur les seules paires candidates → décision.
4. **Mesure** : rappel/précision sur un jeu de doublons connu, avant/après l'étage embeddings.
5. Si gain net → décision + intégration comme option de la dédup d'un projet lié (`docs/linked_projects.md`).

## Livré (PoC exécutable, hors-ligne)
`dedup_embeddings.py` — pipeline **hybride** : blocking par embeddings (top-k cosinus) PUIS étage fuzzy
(Levenshtein, substitut RapidFuzz). Mesure recall / precision / F1 + nombre de comparaisons pour
(a) fuzzy exhaustif O(n²) vs (b) blocking + fuzzy. Deux moteurs : `proxy` (n-grammes de caractères,
déterministe, hors-ligne) et `nomic` (vrais embeddings via `EMBED_URL`, repli auto).

```
python dedup_embeddings.py --selftest
python dedup_embeddings.py --dataset sample_titles.jsonl
```

**Résultats mesurés** : le blocking atteint **la même qualité que le fuzzy exhaustif**
(dataset générique `sample_titles.jsonl` : rappel 1.0, F1 0.909) pour **-91 % de comparaisons** (66 → 6) ;
selftest (27/10/2026) : rappel 0.75, F1 0.857, **-82 %** de comparaisons (28 → 5). Limite honnête : la
variante translittérée (« Tchaikovsky » vs « Tschaikowski ») n'est **pas** captée par le proxy lexical —
c'est exactement le rappel sémantique que le moteur `nomic` doit apporter.

## Étape 2 — moteur nomic + décision sémantique

Le moteur `nomic` est branché (embeddings Ollama `nomic-embed-text` via `EMBED_URL`, défaut
`http://localhost:11434`), avec une **décision SÉMANTIQUE** (cosinus ≥ `--sem`) — car la décision
lexicale (Levenshtein) ne peut PAS trancher deux alphabets différents.

```
ollama serve            # nomic-embed-text doit être pull
python dedup_embeddings.py --dataset cross_script.jsonl --engine nomic --topk 6 --block 0.45 --sem 0.6
```

`cross_script.jsonl` mélange latin, cyrillique, grec et variantes (7 doublons). Mesure hors-ligne du
proxy lexical (27/10/2026) : rappel 0.14, F1 0.25 — il ne capte aucune paire inter-alphabets.
**La mesure avec le moteur `nomic` sur ce jeu reste à refaire** (le jeu a été remplacé le 27/10/2026 ;
l'ancienne mesure portait sur un autre corpus et n'est plus publiée). Piste connue : `nomic-embed-text`
est anglophone-centré ; un embedder multilingue (`bge-m3`, `multilingual-e5`) devrait mieux relier
les alphabets.

## Garde-fous
Isolé, mesuré avant promotion. Réutilise l'infra existante (pas de nouvelle dépendance lourde).
Données d'exemple génériques, zéro écriture vault.
Réf. : BlockingPy (arXiv 2504.04266), record linkage w/ embeddings (Cambridge) — cf. radar.
