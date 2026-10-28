#!/usr/bin/env python3
"""
mcp_desc_audit.py — Audit du « Tool Schema Bloat » (G4, fichier 06).

Mesure la taille des descriptions des serveurs MCP déclarés dans un fichier de
config (claude_desktop_config.json / .mcp.json) et signale ce qui dépasse le
plafond recommandé (2 Ko par serveur). Lecture seule, aucun effet de bord.

Usage :
    python3 mcp_desc_audit.py /chemin/vers/.mcp.json
    python3 mcp_desc_audit.py /chemin/vers/config.json --cap 2048 --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_CAP = 2048  # octets, plafond conseillé par serveur (fichier 06)


def server_blob(name: str, cfg: dict) -> str:
    """Reconstitue le texte injecté en contexte pour un serveur (nom + description
    + instructions éventuelles). Approximation utile pour estimer le poids tokens."""
    parts = [name]
    for key in ("description", "instructions", "_comment"):
        val = cfg.get(key)
        if isinstance(val, str):
            parts.append(val)
    return "\n".join(parts)


def audit(config_path: Path, cap: int) -> dict:
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"[mcp-audit] config introuvable : {config_path}")
    except json.JSONDecodeError as exc:
        sys.exit(f"[mcp-audit] JSON invalide : {exc}")

    servers = data.get("mcpServers") or data.get("mcp_servers") or {}
    rows = []
    for name, cfg in servers.items():
        cfg = cfg if isinstance(cfg, dict) else {}
        size = len(server_blob(name, cfg).encode("utf-8"))
        rows.append({"server": name, "bytes": size, "over_cap": size > cap})
    rows.sort(key=lambda r: r["bytes"], reverse=True)
    return {
        "config": str(config_path),
        "cap_bytes": cap,
        "server_count": len(rows),
        "total_bytes": sum(r["bytes"] for r in rows),
        "over_cap": [r["server"] for r in rows if r["over_cap"]],
        "rows": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit taille descriptions MCP (G4).")
    ap.add_argument("config", help="Chemin du fichier de config MCP")
    ap.add_argument("--cap", type=int, default=DEFAULT_CAP, help="Plafond octets/serveur (def: 2048)")
    ap.add_argument("--json", action="store_true", help="Sortie JSON")
    args = ap.parse_args()

    report = audit(Path(args.config), args.cap)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"[mcp-audit] {report['server_count']} serveurs · total ~{report['total_bytes']} o "
          f"· plafond {report['cap_bytes']} o/serveur")
    for r in report["rows"]:
        flag = "  ⚠️ > plafond" if r["over_cap"] else ""
        print(f"  {r['bytes']:>6} o  {r['server']}{flag}")
    if report["over_cap"]:
        print(f"\nÀ compresser ({len(report['over_cap'])}) : {', '.join(report['over_cap'])}")
    else:
        print("\nOK — aucun serveur au-dessus du plafond.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
