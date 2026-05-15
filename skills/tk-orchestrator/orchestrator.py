#!/usr/bin/env python3
"""
orchestrator.py — CLI principale du tk-orchestrator
TricorderKit v0.8 — tk-orchestrator v0.2.0

Interface A : CLI Python (invoquée par Claude via Bash ou scripts)
Output : JSON contractualisé conforme skill_output.schema.json v1.0.0

Usage:
    python orchestrator.py route "liste les repos Claude"
    python orchestrator.py --dry-run route "surveille One Piece"
    python orchestrator.py chain --steps '[...]'
    python orchestrator.py budget-check --intent research
    python orchestrator.py status

Référence : DEC-008 — Orchestrator-First Pattern (15/05/2026)
"""

from __future__ import annotations
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# Résolution du path pour imports absolus ou relatifs
_HERE = Path(__file__).parent
_PROJECT_ROOT = _HERE.parent.parent  # TricorderKit_v0.7/
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Nom du package : skills/tk-orchestrator → skills.tk_orchestrator (tirets → underscores)
try:
    from skills.tk_orchestrator.router.intent_classifier import classify_intent, IntentResult
    from skills.tk_orchestrator.router.skill_registry import (
        load_cli_registry, load_skill_registry,
        find_cli_for_domain, CLIEntry,
    )
    from skills.tk_orchestrator.budget.token_tracker import (
        TokenBudget, budget_report, estimate_tokens,
    )
    from skills.tk_orchestrator.budget.session_cache import (
        get_boot_context, log_orchestration, store_session_value,
    )
    from skills.tk_orchestrator.context.context_manager import (
        run_cli_tool, load_skill_minimal, dry_run_preview,
    )
    from skills.tk_orchestrator.context.chain_executor import (
        ChainExecutor, ChainStep,
    )
except ModuleNotFoundError:
    # Fallback : imports relatifs si invoqué directement depuis le dossier du skill
    from router.intent_classifier import classify_intent, IntentResult  # type: ignore
    from router.skill_registry import (  # type: ignore
        load_cli_registry, load_skill_registry,
        find_cli_for_domain, CLIEntry,
    )
    from budget.token_tracker import TokenBudget, budget_report, estimate_tokens  # type: ignore
    from budget.session_cache import get_boot_context, log_orchestration, store_session_value  # type: ignore
    from context.context_manager import run_cli_tool, load_skill_minimal, dry_run_preview  # type: ignore
    from context.chain_executor import ChainExecutor, ChainStep  # type: ignore


# ── Constantes ────────────────────────────────────────────────────────────────

VERSION = "0.2.0"
SKILL_NAME = "tk-orchestrator"

# Risk levels par défaut selon le type d'action
RISK_MAP = {
    "query": "LOW",
    "audit": "LOW",
    "research": "LOW",
    "action": "MEDIUM",
    "workflow": "MEDIUM",
}


# ── Helpers output ────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _build_output(
    status: str,
    summary: str,
    data: Dict,
    budget: Optional[TokenBudget] = None,
    duration_ms: int = 0,
    dry_run_report: Optional[Dict] = None,
    error: Optional[Dict] = None,
    decisions_logged: Optional[List[str]] = None,
    next_steps: Optional[List[str]] = None,
) -> Dict:
    """Construit un output conforme skill_output.schema.json v1.0.0."""
    tokens = budget.to_schema_dict() if budget else {"input": 0, "output": 0, "total": 0}

    result = {
        "status": status,
        "skill_name": SKILL_NAME,
        "skill_version": VERSION,
        "timestamp": _now_iso(),
        "duration_ms": duration_ms,
        "tokens_used": tokens,
        "output": {
            "summary": summary[:500],  # max 500 chars selon schéma
            "data": data,
        },
    }

    if decisions_logged:
        result["output"]["decisions_logged"] = decisions_logged
    if next_steps:
        result["output"]["next_steps"] = next_steps[:5]
    if dry_run_report:
        result["dry_run_report"] = dry_run_report
    if error:
        result["error"] = error

    return result


def _find_project_root() -> Path:
    """Auto-détecte la racine TricorderKit."""
    import os
    env_root = os.environ.get("TRICORDERKIT_ROOT")
    if env_root:
        return Path(env_root)
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "CLAUDE.md").exists():
            return parent
        if (parent / "plugins" / "cli-forge" / "registry.yml").exists():
            return parent
    return current


def _assess_risk(cli_entry: Optional[CLIEntry], intent_type: str) -> str:
    """Évalue le niveau de risque d'une exécution."""
    if cli_entry is None:
        return "MEDIUM"
    if cli_entry.status == "prod_ready":
        return RISK_MAP.get(intent_type, "MEDIUM")
    elif cli_entry.status == "dry_run_validated":
        base = RISK_MAP.get(intent_type, "MEDIUM")
        # Escalader d'un niveau si seulement dry_run_validated
        return {"LOW": "LOW", "MEDIUM": "MEDIUM", "HIGH": "HIGH"}.get(base, "MEDIUM")
    else:
        return "CRITICAL"


# ── Commande : route ──────────────────────────────────────────────────────────

def cmd_route(
    request: str,
    dry_run: bool = False,
    budget_override: Optional[int] = None,
    root: Optional[Path] = None,
) -> Dict:
    """
    Route une requête vers le bon tool (CLI-first) et l'exécute.
    """
    t_start = time.time()
    root = root or _find_project_root()

    # Phase 0 — Vérifier le cache tk-boot
    boot_ctx = get_boot_context(root)
    boot_cache_available = bool(boot_ctx)

    # Phase 1 — Intent & domaine
    intent: IntentResult = classify_intent(request)

    # Phase 2 — Budget
    budget = TokenBudget.from_intent(intent.type, request)
    if budget_override:
        budget.total = budget_override
        budget.effective = int(budget_override * 0.8)

    # Phase 3 — Sélection tool (CLI-first)
    clis = load_cli_registry(root)
    skills = load_skill_registry(root)

    selected_cli = find_cli_for_domain(intent.domain, intent.type, clis)
    selected_skill = None
    tool_type = "none"
    selected_tool_name = "none"

    if selected_cli:
        tool_type = "cli"
        selected_tool_name = selected_cli.name
    elif skills:
        # Trouver un skill pertinent par triggers
        for skill_name, skill in skills.items():
            if any(intent.domain in t or intent.type in t for t in skill.triggers):
                selected_skill = skill
                tool_type = "skill"
                selected_tool_name = skill_name
                break

    risk_level = _assess_risk(selected_cli, intent.type)

    # Phase 4 — Exécution isolée
    if dry_run or tool_type == "none":
        exec_result = dry_run_preview(
            tool_name=selected_tool_name,
            tool_type=tool_type if tool_type != "none" else "llm_fallback",
            command=_default_command(selected_cli, intent),
            args={"query": request},
            risk_level=risk_level,
        )
    elif tool_type == "cli" and selected_cli:
        command = _default_command(selected_cli, intent)
        budget.consume(estimate_tokens(request), purpose="input", step=0)
        exec_result = run_cli_tool(
            cli=selected_cli,
            command=command,
            args={"query": request},
            dry_run=dry_run,
        )
    elif tool_type == "skill" and selected_skill:
        exec_result = load_skill_minimal(
            skill=selected_skill,
            args={"request": request},
            dry_run=dry_run,
        )
    else:
        exec_result = {
            "status": "error",
            "output": None,
            "tokens": 0,
            "error": "Aucun tool adapté trouvé pour ce domaine",
        }

    # Consommer tokens de l'exécution
    exec_tokens = exec_result.get("tokens", 0)
    budget.consume(exec_tokens, purpose="execution", step=1)

    duration_ms = int((time.time() - t_start) * 1000)

    # Phase 6 — Log
    log_orchestration(
        root=root,
        intent_type=intent.type,
        domain=intent.domain,
        tool_used=selected_tool_name,
        status=exec_result.get("status", "unknown"),
        tokens_used=budget.used,
        duration_ms=duration_ms,
    )

    # Construction output
    final_status = exec_result.get("status", "error")
    if dry_run and final_status not in ("error",):
        final_status = "dry_run"

    tool_no_match = tool_type == "none"
    summary = (
        f"Routed '{request[:60]}' → {selected_tool_name} "
        f"[{intent.type}/{intent.domain}] — {budget.used} tokens"
        if not tool_no_match
        else f"No tool found for '{request[:60]}' [{intent.type}/{intent.domain}]"
    )

    data = {
        "intent": {
            "type": intent.type,
            "domain": intent.domain,
            "confidence": intent.confidence,
            "entities": intent.entities,
            "domain_scores": intent.domain_scores,
        },
        "routing": {
            "selected_tool": selected_tool_name,
            "tool_type": tool_type,
            "command": _default_command(selected_cli, intent) if selected_cli else None,
            "registry_status": selected_cli.status if selected_cli else None,
            "risk_level": risk_level,
        },
        "token_budget": budget.to_dict(),
        "boot_cache_used": boot_cache_available,
        "execution": exec_result.get("output"),
    }

    dry_run_report = exec_result.get("dry_run_report")

    error_dict = None
    if final_status == "error":
        error_dict = {
            "code": "ROUTING_FAILED" if tool_no_match else "EXECUTION_FAILED",
            "message": exec_result.get("error", "Erreur inconnue"),
            "recoverable": exec_result.get("recoverable", True),
            "rollback_available": False,
        }

    return _build_output(
        status=final_status,
        summary=summary,
        data=data,
        budget=budget,
        duration_ms=duration_ms,
        dry_run_report=dry_run_report,
        error=error_dict,
        next_steps=_suggest_next_steps(intent, selected_tool_name, final_status),
    )


def _default_command(cli: Optional[CLIEntry], intent: IntentResult) -> Optional[str]:
    """Choisit la commande par défaut selon l'intention."""
    if not cli or not cli.commands:
        return None
    if intent.type == "query":
        for cmd in cli.commands:
            if "list" in cmd or "search" in cmd or "get" in cmd:
                return cmd
    return cli.commands[0]


def _suggest_next_steps(intent: IntentResult, tool: str, status: str) -> List[str]:
    """Génère des suggestions de prochaines étapes contextuelles."""
    steps = []
    if status == "success":
        steps.append(f"Vérifier les résultats de {tool} dans le vault Obsidian")
    if intent.domain == "manga":
        steps.append("Indexer les resultats dans la collection Qdrant du domaine")
    if tool == "none" or status == "error":
        steps.append("Vérifier registry.yml — aucune CLI disponible pour ce domaine")
        steps.append("Exécuter /tk:boot pour recharger le contexte de session")
    return steps[:5]


# ── Commande : chain ──────────────────────────────────────────────────────────

def cmd_chain(
    steps_json: str,
    dry_run: bool = False,
    root: Optional[Path] = None,
) -> Dict:
    """
    Exécute une chaîne d'étapes ordonnées avec abort-on-failure.

    steps_json: JSON array de steps, ex:
    '[{"tool":"github-goat","cmd":"list-repos","args":{"query":"claude"}}]'
    """
    t_start = time.time()
    root = root or _find_project_root()

    try:
        steps_data = json.loads(steps_json)
    except json.JSONDecodeError as e:
        return _build_output(
            status="error",
            summary="JSON invalide pour --steps",
            data={},
            error={"code": "INVALID_JSON", "message": str(e), "recoverable": True, "rollback_available": False},
        )

    if not isinstance(steps_data, list) or not steps_data:
        return _build_output(
            status="error",
            summary="--steps doit être un tableau JSON non vide",
            data={},
            error={"code": "INVALID_STEPS", "message": "Tableau vide ou non-tableau", "recoverable": True, "rollback_available": False},
        )

    clis = load_cli_registry(root)
    budget = TokenBudget.from_intent("workflow", steps_json)

    chain_steps = []
    for raw_step in steps_data:
        chain_steps.append(ChainStep(
            tool=raw_step.get("tool", "unknown"),
            command=raw_step.get("cmd", ""),
            args=raw_step.get("args", {}),
            risk_level=raw_step.get("risk", "MEDIUM"),
        ))

    def step_runner(step: ChainStep, previous_output: Optional[Dict], is_dry_run: bool) -> Dict:
        """Runner qui exécute chaque step de la chaîne."""
        cli_entry = clis.get(step.tool)
        if not cli_entry:
            return {
                "status": "error",
                "error": f"CLI '{step.tool}' introuvable ou non validée dans registry.yml",
                "tokens": 0,
                "output": None,
            }
        # Injecter l'output précédent dans les args si disponible
        merged_args = dict(step.args)
        if previous_output and isinstance(previous_output, dict):
            merged_args["_previous"] = previous_output

        return run_cli_tool(cli_entry, step.command, merged_args, dry_run=is_dry_run)

    executor = ChainExecutor(budget=budget, dry_run=dry_run)
    chain_result = executor.execute(chain_steps, step_runner)
    duration_ms = int((time.time() - t_start) * 1000)

    final_status = chain_result.overall_status
    summary = (
        f"Chain {final_status}: {chain_result.success_count}/{len(chain_steps)} "
        f"steps OK — {budget.used} tokens"
    )

    error_dict = None
    if final_status in ("partial", "error") and chain_result.abort_reason:
        error_dict = {
            "code": f"CHAIN_ABORTED_STEP_{chain_result.aborted_at_step}",
            "message": chain_result.abort_reason,
            "recoverable": True,
            "rollback_available": False,
        }

    return _build_output(
        status=final_status,
        summary=summary,
        data={
            "chain": chain_result.to_dict(),
            "token_budget": budget.to_dict(),
            "chain_policy": "abort_on_failure",
            "chain_limit": 5,
        },
        budget=budget,
        duration_ms=duration_ms,
        error=error_dict,
    )


# ── Commande : budget-check ───────────────────────────────────────────────────

def cmd_budget_check(intent_type: str, input_text: str = "") -> Dict:
    """Rapport de budget token pour un type d'intention."""
    report = budget_report(intent_type, input_text)
    return _build_output(
        status="success",
        summary=f"Budget check pour intent={intent_type}: {report['effective_budget']} tokens effectifs",
        data={"budget_report": report},
    )


# ── Commande : status ─────────────────────────────────────────────────────────

def cmd_status(root: Optional[Path] = None) -> Dict:
    """Rapport de statut du système d'orchestration."""
    root = root or _find_project_root()

    clis = load_cli_registry(root)
    skills = load_skill_registry(root)
    boot_ctx = get_boot_context(root)

    return _build_output(
        status="success",
        summary=f"Orchestrator OK — {len(clis)} CLI(s) validée(s), {len(skills)} skill(s) disponible(s)",
        data={
            "clis_available": [
                {"name": c.name, "status": c.status, "commands": c.commands}
                for c in clis.values()
            ],
            "skills_available": [
                {"name": s.name, "triggers": s.triggers[:3]}
                for s in skills.values()
            ],
            "boot_cache": "available" if boot_ctx else "not_loaded",
            "registry_path": str(root / "plugins/cli-forge/registry.yml"),
        },
        next_steps=["Exécuter /tk:boot si boot_cache=not_loaded"],
    )


# ── CLI Interface (argparse) ──────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tk-orchestrator",
        description="TricorderKit — Meta-skill orchestrateur v0.2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python orchestrator.py route "liste les repos Claude"
  python orchestrator.py --dry-run route "surveille One Piece"
  python orchestrator.py chain --steps '[{"tool":"github-goat","cmd":"list-repos","args":{}}]'
  python orchestrator.py budget-check --intent research
  python orchestrator.py status
        """,
    )

    parser.add_argument(
        "--dry-run", action="store_true",
        help="Mode simulation — aucun effet de bord",
    )
    parser.add_argument(
        "--output", choices=["json", "table"], default="json",
        help="Format de sortie (défaut: json)",
    )
    parser.add_argument(
        "--root", type=Path, default=None,
        help="Racine du projet TricorderKit (auto-détectée si absent)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # route
    route_p = subparsers.add_parser("route", help="Router une requête vers le bon tool")
    route_p.add_argument("request", nargs="+", help="Requête en langage naturel")
    route_p.add_argument("--budget", type=int, default=None, help="Budget token personnalisé")

    # chain
    chain_p = subparsers.add_parser("chain", help="Exécuter une chaîne de steps")
    chain_p.add_argument(
        "--steps", required=True,
        help='JSON array de steps: \'[{"tool":"...","cmd":"...","args":{}}]\'',
    )

    # budget-check
    budget_p = subparsers.add_parser("budget-check", help="Vérifier le budget token")
    budget_p.add_argument(
        "--intent", choices=["query", "action", "workflow", "research", "audit", "unknown"],
        default="query", help="Type d'intention",
    )
    budget_p.add_argument("--input", dest="input_text", default="", help="Texte d'entrée à estimer")

    # status
    subparsers.add_parser("status", help="Statut du système d'orchestration")

    return parser


def _format_table(result: Dict) -> str:
    """Format texte lisible pour --output table."""
    lines = [
        f"Status  : {result.get('status', '?')}",
        f"Skill   : {result.get('skill_name', '?')} v{result.get('skill_version', '?')}",
        f"Time    : {result.get('duration_ms', 0)}ms",
    ]
    tokens = result.get("tokens_used", {})
    lines.append(f"Tokens  : {tokens.get('total', 0)} (in:{tokens.get('input', 0)} / out:{tokens.get('output', 0)})")
    output = result.get("output", {})
    lines.append(f"Summary : {output.get('summary', '-')}")
    if result.get("error"):
        lines.append(f"Error   : {result['error'].get('message', '-')}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Dispatch
    result: Dict
    if args.command == "route":
        request_str = " ".join(args.request)
        result = cmd_route(
            request=request_str,
            dry_run=args.dry_run,
            budget_override=getattr(args, "budget", None),
            root=args.root,
        )
    elif args.command == "chain":
        result = cmd_chain(
            steps_json=args.steps,
            dry_run=args.dry_run,
            root=args.root,
        )
    elif args.command == "budget-check":
        result = cmd_budget_check(
            intent_type=args.intent,
            input_text=args.input_text,
        )
    elif args.command == "status":
        result = cmd_status(root=args.root)
    else:
        result = _build_output(
            status="error",
            summary=f"Commande inconnue : {args.command}",
            data={},
            error={"code": "UNKNOWN_COMMAND", "message": f"{args.command}", "recoverable": True, "rollback_available": False},
        )

    # Output
    if args.output == "table":
        print(_format_table(result))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    return 0 if result.get("status") in ("success", "dry_run") else 1


if __name__ == "__main__":
    sys.exit(main())
