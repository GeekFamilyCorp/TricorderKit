# experiments/openevolve_poc — « autoresearch » pour TricorderKit (OpenEvolve, GPU-free)

> Issu de l'analyse de `karpathy/autoresearch` (2026-06-22). Verdict : autoresearch tel quel = banc
> d'entraînement LLM **mono-GPU** → inadapté (poste/VPS sans GPU, pas de modèle à entraîner). Mais son
> **pattern** (proposer → mesurer une métrique → garder/jeter → recommencer) est réalisé ici via
> **OpenEvolve** (implémentation open-source d'AlphaEvolve), sur **CPU**, avec un **LLM local Ollama**.

## Idée
Au lieu d'optimiser `val_bpb` d'un GPT, on fait **évoluer la décision de dédup** pour maximiser le **F1**.
L'évaluateur réutilise le PoC #2 (`dedup_embeddings`). C'est la brique qui débloque l'Étape 2 dédup.

## Fichiers
- `initial_program.py` — programme **évoluable** (bloc `EVOLVE-BLOCK` : seuils blocking/fuzzy/topk +
  logique `predict`). C'est l'équivalent du `train.py` d'autoresearch.
- `evaluator.py` — contrat OpenEvolve : `evaluate(program_path) -> {combined_score=F1, recall, precision}`.
- `search_baseline.py` — **optimiseur déterministe hors-ligne** (proxy sans dépendance ni LLM) qui prouve
  la boucle propose/mesure/garde. Remplacé par OpenEvolve pour une vraie évolution (qui réécrit aussi la logique).
- `config.yaml` — OpenEvolve pointant sur **Ollama local** (`http://localhost:11434/v1`), seed 42.

## Lancer (hors-ligne, tout de suite)
```
python search_baseline.py --selftest      # balaye les params, garde le meilleur F1
python evaluator.py                        # métriques du programme courant
```

## Lancer la vraie évolution (OpenEvolve)
```
pip install openevolve
python openevolve-run.py experiments/openevolve_poc/initial_program.py \
       experiments/openevolve_poc/evaluator.py \
       --config experiments/openevolve_poc/config.yaml --iterations 60
```
LLM = Ollama local (coût ~0, GPU-free). Ou pointer `api_base` sur la gateway Hermes du VPS.

## Résultat mesuré (2026-06-22, hors-ligne)
L'optimiseur déterministe a trouvé, en **288 évaluations**, des paramètres
(`BLOCK_THRESHOLD=0.2`, `FUZZY_THRESHOLD=0.85`, `TOPK=2`) qui font passer le **F1 de 0.909 → 1.0**
(élimine le faux positif, rappel conservé à 1.0) vs la baseline manuelle du PoC #2. **Preuve que la
boucle évaluateur-pilotée trouve déjà mieux que le réglage humain** — OpenEvolve (qui réécrit aussi la
logique, pas seulement les seuils, et explore via MAP-Elites) devrait aller plus loin.

## Place dans la boucle self-improving
god-mode **propose** la cible → OpenEvolve **optimise** le programme → RAGAS/F1 **valide** →
reflection **journalise**. C'est « autoresearch » réalisé pour TricorderKit, sans GPU.

## Garde-fous
Isolé, hors-ligne pour le selftest, jamais d'écriture vault, budget d'itérations plafonné,
données d'exemple génériques (R37). Promotion (intégration dédup réelle) = sur DEC, après mesure.

## Statut réel (2026-06-24)
- **openevolve 0.2.27 installé** ; harness prêt (`initial_program.py` + `evaluator.py` + `config.yaml`).
- **Optimiseur déterministe hors-ligne validé** : trouve déjà le réglage optimal (F1 0.909 → **1.0**) — cf. `search_baseline.py --selftest`.
- **Vraie évolution LLM = en attente d'un modèle de CODE capable.** Le seul modèle local (`qwen:1.8b`) est trop
  faible pour réécrire du code utilement (et l'endpoint Ollama `/v1` est lent à froid). Pour lancer pour de vrai :
  `ollama pull qwen2.5-coder:7b` puis la commande du `config.yaml`. Honnêteté : pas de faux résultat ici.
