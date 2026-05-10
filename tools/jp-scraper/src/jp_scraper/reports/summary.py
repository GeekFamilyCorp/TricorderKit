from pathlib import Path
import json
from jp_scraper.storage.jsonl import read_jsonl

def _latest_source_dir(source: str, runs: Path) -> Path:
    candidates = sorted([p for p in runs.glob(f"*/{source}") if p.is_dir()])
    if not candidates:
        raise FileNotFoundError(f"No runs found for source {source}")
    return candidates[-1]

def build_summary(source: str, runs: Path) -> Path:
    latest = _latest_source_dir(source, runs)
    records = read_jsonl(latest / "scan_delta.jsonl")
    errors = read_jsonl(latest / "errors.jsonl")
    lines = [
        f"# Scan summary — {source}",
        "",
        f"- Run directory: `{latest}`",
        f"- Delta records: {len(records)}",
        f"- Errors: {len(errors)}",
        "",
        "## Records",
        "",
    ]
    for rec in records[:50]:
        lines.append(f"- **{rec.get('title') or 'N/A'}** — {rec.get('url') or 'N/A'}")
        sig = rec.get("signals") or {}
        active = [k for k, v in sig.items() if v]
        if active:
            lines.append(f"  - Signals: {', '.join(active)}")
    if len(records) > 50:
        lines.append(f"- … {len(records)-50} additional records hidden from LLM summary.")
    if errors:
        lines += ["", "## Errors", ""]
        for err in errors[:20]:
            lines.append(f"- `{err.get('error')}` on `{err.get('url') or err.get('source') or ''}`")
    lines += [
        "",
        "## Token policy",
        "",
        "Claude should read this file first, then `scan_delta.jsonl` only if needed. Do not read raw HTML by default.",
    ]
    out = latest / "scan_summary.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
