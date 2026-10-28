# models/ — Registre de modèles (abstraction Ollama / LiteLLM)

> Composant net-new (DEC-051, roadmap A) — démarré le 2026-06-19. Couche générique, **sans GPU**, sans secret.

## Quoi
- `model_registry.yaml` — déclare la gateway (LiteLLM, via env), les **tiers logiques** (T1/T2/T3 → local/distant) et les modèles locaux Ollama.
- `registry.py` — CLI : `list` (modèles+tiers) · `resolve --tier T2 [--prefer local|remote]` (résout le modèle à utiliser). Sortie JSON, zéro réseau, zéro secret.

## Pourquoi
Centralise le mapping tier→modèle (cohérent avec `MODEL_ROUTING_POLICY` Haiku 55 / Sonnet 30 / Opus 15) et permet de privilégier le **local gratuit** (Ollama) sur T1/T2. Référencé par le routeur (`token-optimizer`) à terme.

## Usage
```
python models/registry.py list
python models/registry.py resolve --tier T2 --prefer local
```
Pré-requis : `pyyaml`. Secrets (URL/clé gateway) = variables d'env (`LLM_GATEWAY_URL`, `LLM_GATEWAY_KEY`), jamais dans le registre.

## Limites
vLLM = optionnel, **GPU requis** (absent) → non activé. Tenir `local_models` à jour avec `ollama list`.
