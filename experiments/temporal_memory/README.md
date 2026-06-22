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

## Garde-fous
Isolé, benchmarké avant toute intégration. Vérifier licences (Graphiti/Mem0 = Apache-2.0 à confirmer).
Réf. : Awesome-Agent-Memory (github TeleAI-UAGI), comparatifs Zep/Mem0/Letta 2026 — cf. radar.
