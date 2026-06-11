#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mcp_gateway.py — Gouvernance MCP machine-lisible (TricorderKit, DEC-046 / N3).

Rend executable la politique MCP : DENY-BY-DEFAULT. Confronte la configuration
reelle (.mcp.json) a l'allowlist declarative (mcp/registry_allowlist.yaml) et
journalise chaque decision (mcp/logs/mcp_calls.jsonl).

Sous-commandes :
  list             Serveurs/tools declares (allowlist) + configures (.mcp.json).
  audit            Verifie .mcp.json contre l'allowlist : serveurs non declares,
                   secrets en clair (DEC-039), tools bannis -> echec si fuite.
  allowlist-check  Decision autorise/refuse pour --server S --tool T.

Sortie conforme a core/contracts/skill_output.schema.json (--format json|md).
Codes retour : 0 = OK, 1 = violation/refus, 2 = erreur d'environnement.

Conventions repo : argparse (pas typer), UTF-8 force (PATTERN-WIN-ENCODING),
lecture JSON tolerante au BOM (utf-8-sig).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import fnmatch
import io
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# scripts/ -> mcp/ -> REPO_ROOT
MCP_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = MCP_DIR.parent
ALLOWLIST = MCP_DIR / "registry_allowlist.yaml"
MCP_CONFIG = REPO_ROOT / ".mcp.json"
CALL_LOG = MCP_DIR / "logs" / "mcp_calls.jsonl"

SKILL_NAME = "mcp-gateway"
SKILL_VERSION = "0.1.0"

# Reference ${VAR} ou ${VAR:-default} : seule forme toleree pour un secret.
_ENV_REF = re.compile(r"^\$\{[A-Za-z_][A-Za-z0-9_]*(?::-[^}]*)?\}$")
# Cle d'env a posture sensible (heuristique secret).
_SECRET_KEY = re.compile(r"(TOKEN|SECRET|PASSWORD|API_KEY|KEY|CREDENTIAL)", re.IGNORECASE)


# ── Encodage (PATTERN-WIN-ENCODING) ─────────────────────────────────────────────
def setup_utf8() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None:
            continue
        enc = (getattr(stream, "encoding", "") or "").lower()
        if enc.startswith("utf"):
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
                continue
            except Exception:
                pass
        buffer = getattr(stream, "buffer", None)
        if buffer is not None:
            try:
                setattr(sys, name, io.TextIOWrapper(buffer, encoding="utf-8", errors="replace"))
            except Exception:
                pass
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Chargement YAML ─────────────────────────────────────────────────────────────
class EnvError(RuntimeError):
    """Erreur d'environnement (dependance/fichier manquant) -> exit code 2."""


def load_allowlist(path: Path | None = None) -> dict:
    p = path or ALLOWLIST
    if not p.exists():
        raise EnvError(f"allowlist introuvable : {p}")
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - depend de l'env
        raise EnvError("PyYAML requis (pip install pyyaml)") from exc
    return yaml.safe_load(p.read_text(encoding="utf-8-sig")) or {}


def load_mcp_config(path: Path | None = None) -> dict:
    p = path or MCP_CONFIG
    if not p.exists():
        raise EnvError(f".mcp.json introuvable : {p}")
    return json.loads(p.read_text(encoding="utf-8-sig"))


# ── Contrat de sortie skill_output ──────────────────────────────────────────────
def skill_output(status: str, summary: str, *, data: Any | None = None,
                 next_steps: list[str] | None = None,
                 error: dict | None = None) -> dict:
    if status not in ("success", "partial", "error", "dry_run"):
        raise ValueError(f"status invalide: {status}")
    out: dict[str, Any] = {"summary": summary[:500]}
    if data is not None:
        out["data"] = data
    if next_steps:
        out["next_steps"] = next_steps[:5]
    env: dict[str, Any] = {
        "status": status,
        "skill_name": SKILL_NAME,
        "skill_version": SKILL_VERSION,
        "timestamp": now_iso(),
        "output": out,
    }
    if error is not None:
        env["error"] = error
    return env


def emit(env: dict, fmt: str) -> None:
    if fmt == "md":
        o = env.get("output", {})
        print(f"# {env['skill_name']} — {env['status']}")
        print(f"\n{o.get('summary', '')}\n")
        data = o.get("data")
        if isinstance(data, dict):
            for k, v in data.items():
                print(f"- **{k}** : {json.dumps(v, ensure_ascii=False)}")
        if o.get("next_steps"):
            print("\n## Prochaines etapes")
            for s in o["next_steps"]:
                print(f"- {s}")
    else:
        print(json.dumps(env, ensure_ascii=False, indent=2))


# ── Journal par appel (mcp/logs/mcp_calls.jsonl) ────────────────────────────────
def log_call(action: str, payload: dict) -> None:
    try:
        CALL_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {"ts": now_iso(), "action": action, **payload}
        with CALL_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # le journal ne doit jamais bloquer une decision


# ── Indexation de l'allowlist ───────────────────────────────────────────────────
def _server_tools(server: dict) -> dict[str, dict]:
    return {t["name"]: t for t in server.get("allowed_tools", []) if isinstance(t, dict) and t.get("name")}


def _is_forbidden(tool_name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(tool_name, pat) for pat in patterns)


# ── allowlist-check : decision deny-by-default ──────────────────────────────────
def decide(allow: dict, server: str, tool: str) -> dict:
    """Retourne {allowed, reason, permission?} selon l'allowlist (deny par defaut)."""
    patterns = allow.get("forbidden_tool_patterns", []) or []
    if _is_forbidden(tool, patterns):
        return {"allowed": False, "reason": f"tool '{tool}' banni (forbidden_tool_patterns)"}
    servers = allow.get("servers", {}) or {}
    srv = servers.get(server)
    if srv is None:
        return {"allowed": False, "reason": f"serveur '{server}' non declare (deny-by-default)"}
    tools = _server_tools(srv)
    spec = tools.get(tool)
    if spec is None:
        return {"allowed": False, "reason": f"tool '{tool}' non declare pour '{server}' (deny-by-default)"}
    return {
        "allowed": True,
        "reason": "declare dans l'allowlist",
        "permission": spec.get("permission", "read"),
        "rate_limit_per_min": spec.get("rate_limit_per_min"),
        "dry_run_default": spec.get("dry_run_default", False),
    }


def cmd_allowlist_check(args) -> int:
    allow = load_allowlist()
    d = decide(allow, args.server, args.tool)
    log_call("allowlist-check", {"server": args.server, "tool": args.tool,
                                 "allowed": d["allowed"], "reason": d["reason"]})
    status = "success" if d["allowed"] else "error"
    summary = ("AUTORISE" if d["allowed"] else "REFUSE") + f" : {args.server}/{args.tool} — {d['reason']}"
    err = None if d["allowed"] else {"code": "MCP_DENIED", "message": d["reason"],
                                     "recoverable": True, "rollback_available": False}
    emit(skill_output(status, summary, data=d, error=err), args.format)
    return 0 if d["allowed"] else 1


# ── list : declare (allowlist) + configure (.mcp.json) ──────────────────────────
def cmd_list(args) -> int:
    allow = load_allowlist()
    cfg = load_mcp_config()
    declared = allow.get("servers", {}) or {}
    configured = (cfg.get("mcpServers") or {})
    rows = []
    for name in sorted(set(declared) | set(configured)):
        srv = declared.get(name, {})
        rows.append({
            "server": name,
            "declared": name in declared,
            "configured": name in configured,
            "permissions": srv.get("permissions", []),
            "tools": sorted(_server_tools(srv)) if srv else [],
        })
    data = {"policy_default": allow.get("policy", {}).get("default", "deny"),
            "servers": rows, "count": len(rows)}
    summary = (f"{len(rows)} serveur(s) — politique '{data['policy_default']}'. "
               f"declares={sum(r['declared'] for r in rows)}, "
               f"configures={sum(r['configured'] for r in rows)}.")
    log_call("list", {"count": len(rows)})
    emit(skill_output("success", summary, data=data), args.format)
    return 0


# ── audit : .mcp.json confronte a l'allowlist ───────────────────────────────────
def audit(allow: dict, cfg: dict) -> dict:
    declared = allow.get("servers", {}) or {}
    configured = (cfg.get("mcpServers") or {})
    patterns = allow.get("forbidden_tool_patterns", []) or []
    violations: list[dict] = []
    warnings: list[dict] = []

    # 1. Serveurs configures mais non declares (deny-by-default).
    for name in sorted(configured):
        if name not in declared:
            violations.append({"kind": "undeclared_server", "server": name,
                               "detail": "present dans .mcp.json, absent de l'allowlist"})

    # 2. Secrets en clair dans .mcp.json (DEC-039 : references ${VAR} seulement).
    for name, spec in sorted(configured.items()):
        for key, val in (spec.get("env") or {}).items():
            if not isinstance(val, str) or not val:
                continue
            if _ENV_REF.match(val):
                continue  # reference d'environnement : conforme
            if _SECRET_KEY.search(key):
                violations.append({"kind": "inline_secret", "server": name, "env": key,
                                   "detail": "valeur litterale au lieu d'une reference ${VAR}"})

    # 3. Tools bannis declares par erreur dans l'allowlist (auto-coherence).
    for name, srv in sorted(declared.items()):
        for tname in _server_tools(srv):
            if _is_forbidden(tname, patterns):
                violations.append({"kind": "forbidden_tool_declared", "server": name, "tool": tname,
                                   "detail": "match un forbidden_tool_pattern"})

    # 4. Serveurs declares mais non configures (informatif, non bloquant).
    for name in sorted(declared):
        if name not in configured:
            warnings.append({"kind": "declared_not_configured", "server": name})

    return {"violations": violations, "warnings": warnings,
            "servers_configured": len(configured), "servers_declared": len(declared)}


def cmd_audit(args) -> int:
    allow = load_allowlist()
    cfg = load_mcp_config()
    res = audit(allow, cfg)
    n = len(res["violations"])
    log_call("audit", {"violations": n, "warnings": len(res["warnings"])})
    if n == 0:
        summary = (f"OK — {res['servers_configured']} serveur(s) configures, tous declares ; "
                   f"aucun secret en clair ; {len(res['warnings'])} avertissement(s).")
        emit(skill_output("success", summary, data=res), args.format)
        return 0
    kinds = ", ".join(sorted({v["kind"] for v in res["violations"]}))
    summary = f"ECHEC — {n} violation(s) : {kinds}."
    err = {"code": "MCP_AUDIT_FAIL", "message": summary, "recoverable": True,
           "rollback_available": False}
    emit(skill_output("error", summary, data=res,
                      next_steps=["Declarer le serveur dans mcp/registry_allowlist.yaml",
                                  "Remplacer toute valeur secrete par une reference ${VAR} (DEC-039)"],
                      error=err), args.format)
    return 1


# ── CLI ─────────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="mcp_gateway",
                                 description="Gouvernance MCP machine-lisible (deny-by-default)")
    sub = ap.add_subparsers(dest="cmd", metavar="<sous-commande>")
    # --format se place APRES la sous-commande (ergonomie + cablage tk).
    fmt_kw = dict(choices=["json", "md"], default="json")
    sub.add_parser("list", help="Serveurs/tools declares + configures").add_argument("--format", **fmt_kw)
    sub.add_parser("audit", help="Auditer .mcp.json vs allowlist").add_argument("--format", **fmt_kw)
    pc = sub.add_parser("allowlist-check", help="Decision autorise/refuse")
    pc.add_argument("--server", required=True)
    pc.add_argument("--tool", required=True)
    pc.add_argument("--format", **fmt_kw)
    return ap


_DISPATCH = {"list": cmd_list, "audit": cmd_audit, "allowlist-check": cmd_allowlist_check}


def main(argv: list[str] | None = None) -> int:
    setup_utf8()
    args = build_parser().parse_args(argv)
    if not args.cmd:
        build_parser().print_help()
        return 0
    try:
        return _DISPATCH[args.cmd](args)
    except EnvError as exc:
        emit(skill_output("error", str(exc),
                          error={"code": "ENV_ERROR", "message": str(exc),
                                 "recoverable": False, "rollback_available": False}),
             getattr(args, "format", "json"))
        return 2


if __name__ == "__main__":
    sys.exit(main())
