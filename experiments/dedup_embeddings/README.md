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

## Étape 2 — moteur nomic RÉEL + décision sémantique (mesuré 2026-06-24)

Le moteur `nomic` est désormais **branché pour de vrai** (embeddings Ollama `nomic-embed-text` via
`EMBED_URL`, défaut `http://localhost:11434`), avec une **décision SÉMANTIQUE** (cosinus ≥ `--sem`) —
car la décision lexicale (Levenshtein) ne peut PAS trancher un cross-script (scripts différents).

```
ollama serve            # nomic-embed-text doit être pull
python dedup_embeddings.py --dataset cross_script.jsonl --engine nomic --topk 6 --block 0.45 --sem 0.6
```

**Mesure réelle** (jeu `cross_script.jsonl` : romaji / kana / kanji / anglais, 7 doublons) :

| Moteur | rappel | précision | F1 | cross-script récupérés |
|---|---|---|---|---|
| proxy **lexical** | 0.14 | 1.00 | 0.25 | 0 (n'en capte aucun) |
| **nomic** sémantique (sem 0.6) | 0.29 | 0.50 | **0.36** | « Naruto » ↔ 「ナルト」 |
| nomic sémantique (sem 0.5) | 0.43 | 0.17 | 0.24 | + « Shingeki no Kyojin » ↔ 「進撃の巨人」 |

**Verdict honnête** : nomic apporte un **vrai** signal cross-script que le lexical n'atteint jamais
(il rapproche romaji↔kana et romaji↔kanji de la même œuvre), MAIS le signal est **faible/bruité** —
la précision s'effondre dès qu'on baisse le seuil pour capter plus. `sem 0.6` = meilleur point
(F1 0.36, récupère une vraie paire sans tout casser).

**Prochaine étape** : `nomic-embed-text` est anglophone-centré → pour la prod, évaluer un embedder
**multilingue/CJK** (ex. `bge-m3`, `multilingual-e5`) qui devrait nettement mieux bridger JP↔romaji.
Puis mesure sur le jeu de doublons réel avant promotion (DEC) dans la dédup du projet de domaine privé.

## Garde-fous
Isolé, mesuré avant promotion. Réutilise l'infra existante (pas de nouvelle dépendance lourde).
Données d'exemple génériques (aucun contenu métier privé), zéro écriture vault.
Réf. : BlockingPy (arXiv 2504.04266), record linkage w/ embeddings (Cambridge) — cf. radar.
