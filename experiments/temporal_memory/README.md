# experiments/temporal_memory — PoC #3 (god-mode) : mémoire temporelle (Graphiti/Zep-inspirée)

> Radar god-mode 2026-06-22, candidat #3 (~85, plus haut potentiel). **PoC isolé.**
> Le marché mémoire-agent 2026 converge sur un **graphe de connaissances temporel** (validité datée des faits).
> Zep/Graphiti bat Mem0 de +15 pts en récupération temporelle (LongMemEval) ; Mem0 ~67 % LOCOMO, -90 % tokens vs full-context.

## Pourquoi TricorderKit
Neo4j + Qdrant (graphify) sont **déjà là mais sous-exploités** pour la mémoire. Une couche temporelle
armerait `reflection.py` + `learning-engine` d'une vraie mémoire long terme datée (faits valides à un instant T),
inter-sessions, économe en tokens. Recoupe le repo **memvid** (déjà dans la liste des 8) → à benchmarker ici.

## Plan
1. Modéliser un mini-schéma temporel sur Neo4j (entité, fait, `valid_from`/`valid_to`, source).
2. Adapter une approche Graphiti-inspirée (ou évaluer Graphiti directement, Apache-2.0) en lecture/écriture.
3. Benchmark : mini-LongMemEval maison vs (a) full-context, (b) `memvid`, (c) cette couche.
4. Mesurer : exactitude récupération temporelle + tokens consommés.
5. Si concluant → DEC + brancher sur `memory-boot`/`reflection.py`.

## Livré (PoC exécutable, hors-ligne)
`temporal_memory.py` — store **bi-temporel** pur-Python (faits `valid_from`/`valid_to`/`source`),
requête `as_of(entity, attribute, t)`, mini-benchmark + mesure exactitude temporelle et proxy tokens.
Deux moteurs : `memory` (défaut, déterministe) et `neo4j` (optionnel via `NEO4J_URL`, repli auto).

```
python temporal_memory.py --selftest                      # jeu embarqué + assertions
python temporal_memory.py --dataset sample_episodes.jsonl # benchmark générique
```
Entrée JSONL : lignes `{"type":"episode",...}` (fait daté) et `{"type":"query",...,"as_of","expected"}`.

**Résultats mesurés (2026-06-22)** : exactitude temporelle **100 %** (selftest 6/6, sample 7/7) ;
économie tokens **84–88 %** vs baseline full-context (slice temporel pertinent au lieu de tout le journal).
Valide le principe : récupérer « ce qui était vrai à l'instant T » est à la fois exact et économe.

## Promu (backend réel SQLite + mini-LongMemEval) — 2026-06-22
Backend **RÉEL** ajouté : `SqliteEngine` (stdlib `sqlite3`, persistant, **zéro dépendance**).
Choisi plutôt que Neo4j pour la **portabilité** : tourne à l'identique sur le poste ET sur le VPS
(Hermes/Paperclip) qui utilise déjà SQLite — sans nouvelle infra. Neo4j reste une option future.

```
python temporal_memory.py --selftest                                   # + parité sqlite + persistance
python temporal_memory.py --dataset mini_longmemeval.jsonl --engine sqlite
python temporal_memory.py --dataset mini_longmemeval.jsonl --engine sqlite --db memoire.db
```

**Résultats mini-LongMemEval (17 requêtes, faits évolutifs sources/budgets/tâches/versions)** :
exactitude temporelle **100 %** (17/17), économie tokens **95,4 %** vs full-context, moteurs
`memory` et `sqlite` en **parité parfaite**, **persistance disque** validée (ré-ouverture .db).

## Prochaines étapes
1. Brancher un LLM-juge (même convention que `reflection.py`) pour les réponses en langage naturel.
2. Dédicace VPS Hermes/Paperclip (SQLite) — cf. proposition `claude-vault/70_ROADMAP/`.
3. Si concluant → DEC + couche temporelle sur `memory-boot`/`reflection.py`.

## Garde-fous
Isolé, benchmarké avant toute intégration. Données d'exemple génériques (aucun contenu métier privé),
zéro écriture vault. Vérifier licences (Graphiti/Mem0 = Apache-2.0 à confirmer).
Réf. : Awesome-Agent-Memory (github TeleAI-UAGI), comparatifs Zep/Mem0/Letta 2026 — cf. radar.
