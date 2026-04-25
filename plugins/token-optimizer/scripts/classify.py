#!/usr/bin/env python3
"""
classify.py — Classifieur de complexite pour token-optimizer.

Analyse un prompt et retourne un tier (T1/T2/T3) + modele recommande.
Heuristique deterministe basee sur 5 dimensions (voir skills/task-classifier/SKILL.md).

Usage:
    python3 classify.py --prompt "votre prompt ici"
    python3 classify.py --prompt "..." --json
    echo "votre prompt" | python3 classify.py --stdin
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ------------------------------------------------------------------
# Detection des signaux
# ------------------------------------------------------------------

SENSITIVE_PATTERNS = [
    r"\blegal\b", r"\bjuridique\b", r"\bmedical\b", r"\bsante\b",
    r"\brgpd\b", r"\bgdpr\b", r"\bsecurite\b", r"\bsecurity\b",
    r"\bproduction\b", r"\bprod\b", r"\bincident\b", r"\bcritique\b",
    r"\bpayment\b", r"\bpaiement\b", r"\bcrypto\b", r"\bauth\b",
    r"\bpci-dss\b", r"\bhipaa\b", r"\bfinancier\b", r"\bbanque\b",
]

ARCHITECTURE_PATTERNS = [
    r"\barchitecture\b", r"\bdesign\b.{0,10}\bsystem\b",
    r"\btrade-?off\b", r"\badr\b", r"\bdistributed\b", r"\bscalab",
    r"\bmicroservice\b", r"\bevent-?driven\b",
]

DEBUG_PATTERNS = [
    r"\bdebug\b", r"\bmemory leak\b", r"\brace condition\b",
    r"\bstack ?trace\b", r"\bpanic\b", r"\bsegfault\b",
    r"\bdeadlock\b", r"\bperformance\b.{0,10}\bissue\b",
]

SIMPLE_PATTERNS = [
    r"\btraduis\b", r"\btranslate\b", r"\bresume\b", r"\bsummari[sz]e\b",
    r"\breformule\b", r"\breformula?tion\b", r"\bsynonyme\b",
    r"\btypo\b", r"\bcorrige\b", r"\bcapitale de\b",
    r"\bc'est quoi\b.{0,30}\?", r"\bwhat is\b.{0,30}\?",
]

DRAFT_PATTERNS = [
    r"\bbrouillon\b", r"\bquick draft\b", r"\bidee rapide\b",
    r"\bfirst draft\b", r"\bjuste pour voir\b",
]

FORCE_OPUS_PATTERNS = [
    r"\butilise opus\b", r"\buse opus\b", r"\bavec opus\b",
    r"\ble meilleur\b", r"\bmax quality\b",
]

FORCE_HAIKU_PATTERNS = [
    r"\butilise haiku\b", r"\buse haiku\b",
    r"\bmode economique\b", r"\bfast mode\b",
]

CODE_CREATION_PATTERNS = [
    r"\b(ecris|cree|code|implemente|implement|developpe|develop|build|write|make|construis)\b.{0,50}\b(composant|component|endpoint|api|route|script|fonction|function|classe|class|module|hook|service|controller|middleware|migration|test|query)\b",
    r"\b(react|vue|svelte|angular|next\.?js|express|fastapi|django|flask|spring|laravel|rails)\b",
    r"\b(typescript|javascript|python|rust|golang|java|ruby|php|swift|kotlin)\b.{0,30}\b(code|script|programme|app)\b",
]


def count_tokens_approx(text: str) -> int:
    words = len(text.split())
    return int(words / 0.75)


def has_any(text: str, patterns) -> bool:
    low = text.lower()
    return any(re.search(p, low) for p in patterns)


def count_code_blocks(text: str) -> int:
    return len(re.findall(r"```", text)) // 2


def expected_output_length(prompt: str) -> str:
    low = prompt.lower()
    if re.search(r"\b(\d+)\s*(mots|words)\b", low):
        m = re.search(r"\b(\d+)\s*(mots|words)\b", low)
        n = int(m.group(1))
        if n < 300:
            return "short"
        elif n < 1500:
            return "medium"
        return "long"
    if any(k in low for k in ["article", "blog post", "guide complet",
                               "documentation", "livre blanc", "whitepaper",
                               "analyse detaillee", "rapport complet"]):
        return "long"
    if any(k in low for k in ["une phrase", "un mot", "oui ou non",
                               "en bref", "en une ligne"]):
        return "short"
    return "medium"


def reasoning_depth(prompt: str) -> str:
    low = prompt.lower()
    if has_any(low, ARCHITECTURE_PATTERNS):
        return "architectural"
    if has_any(low, DEBUG_PATTERNS):
        return "multistep"
    if any(k in low for k in ["explique pourquoi", "analyse", "compare",
                               "planifie", "audit", "trade-off", "strategique",
                               "demontre", "prouve"]):
        return "multistep"
    if any(k in low for k in ["explique", "decris", "presente", "definis"]):
        return "simple"
    return "factual"


def score_input_length(tokens: int) -> int:
    if tokens < 500: return 0
    if tokens < 1500: return 5
    if tokens < 5000: return 10
    if tokens < 15000: return 20
    return 30


def score_output_length(expected: str) -> int:
    return {"short": 0, "medium": 10, "long": 20}[expected]


def score_reasoning(depth: str) -> int:
    return {"factual": 0, "simple": 10, "multistep": 20, "architectural": 25}[depth]


def score_sensitive(prompt: str) -> int:
    if has_any(prompt, SENSITIVE_PATTERNS):
        return 15
    if re.search(r"\b(code|api|bdd|database|sql)\b", prompt.lower()):
        return 5
    return 0


def score_multisource(prompt: str) -> int:
    code_blocks = count_code_blocks(prompt)
    file_mentions = len(re.findall(
        r"\b\w+\.(py|js|ts|tsx|jsx|md|json|yaml|yml|sql|rs|go|java|rb)\b",
        prompt.lower()
    ))
    total = code_blocks + file_mentions
    if total == 0: return 0
    if total <= 2: return 5
    return 10


MODELS = {
    "T1": "claude-haiku-4-5-20251001",
    "T2": "claude-sonnet-4-6",
    "T3": "claude-opus-4-6",
}


def classify(prompt: str, budget_saturated: bool = False) -> dict:
    tokens = count_tokens_approx(prompt)
    out_len = expected_output_length(prompt)
    depth = reasoning_depth(prompt)

    dims = {
        "input_length": score_input_length(tokens),
        "output_length": score_output_length(out_len),
        "reasoning_depth": score_reasoning(depth),
        "sensitive_domain": score_sensitive(prompt),
        "multi_source": score_multisource(prompt),
    }
    score = sum(dims.values())

    if score <= 25:
        tier = "T1"
    elif score <= 60:
        tier = "T2"
    else:
        tier = "T3"

    if depth == "architectural" and dims["sensitive_domain"] >= 15:
        tier = "T3"
    elif depth == "architectural" and tier == "T1":
        tier = "T2"
    elif depth == "multistep" and dims["sensitive_domain"] >= 15 and tier == "T2":
        tier = "T3"

    if has_any(prompt, CODE_CREATION_PATTERNS) and tier == "T1":
        tier = "T2"

    if has_any(prompt, FORCE_OPUS_PATTERNS):
        tier = "T3"
    elif has_any(prompt, FORCE_HAIKU_PATTERNS):
        tier = "T1"
    elif has_any(prompt, DRAFT_PATTERNS) and tier == "T3":
        tier = "T2"
    elif has_any(prompt, SIMPLE_PATTERNS) and tier == "T3":
        tier = "T2"

    if budget_saturated and tier != "T1" and not has_any(prompt, [r"\bcritique\b", r"\burgent\b"]):
        tier = {"T3": "T2", "T2": "T1"}[tier]

    model = MODELS[tier]

    explanation = (
        f"Score {score}/100 -> {tier} ({model}). "
        f"Input ~{tokens} tokens, output {out_len}, reasoning {depth}. "
        f"Sensitive: {dims['sensitive_domain']>0}, multi-source: {dims['multi_source']}."
    )

    return {
        "score": score,
        "tier": tier,
        "model": model,
        "approx_input_tokens": tokens,
        "expected_output_length": out_len,
        "reasoning_depth": depth,
        "dimensions": dims,
        "budget_downgrade_applied": budget_saturated,
        "explanation": explanation,
    }


def main():
    parser = argparse.ArgumentParser(description="Classify a prompt for token-optimizer.")
    parser.add_argument("--prompt", type=str, help="Prompt text")
    parser.add_argument("--stdin", action="store_true", help="Read prompt from stdin")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--budget-saturated", action="store_true", help="Signal budget > 80%")
    args = parser.parse_args()

    if args.stdin:
        prompt = sys.stdin.read()
    elif args.prompt:
        prompt = args.prompt
    else:
        parser.error("Fournir --prompt ou --stdin")

    result = classify(prompt, budget_saturated=args.budget_saturated)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Tier     : {result['tier']}")
        print(f"Modele   : {result['model']}")
        print(f"Score    : {result['score']}/100")
        print(f"Tokens   : ~{result['approx_input_tokens']}")
        print(f"Depth    : {result['reasoning_depth']}")
        print(f"Output   : {result['expected_output_length']}")
        print(f"Details  : {result['dimensions']}")
        print(f"Explain  : {result['explanation']}")


if __name__ == "__main__":
    main()
