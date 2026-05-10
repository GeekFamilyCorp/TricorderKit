from pathlib import Path
from jp_scraper.storage.config import load_sources

def audit_sources(config: Path) -> str:
    sources = load_sources(config)
    lines = ["# Sources audit", "", f"Sources configured: {len(sources)}", ""]
    for src in sources:
        issues = []
        if not src.get("id"): issues.append("missing id")
        if not src.get("base_url"): issues.append("missing base_url")
        if src.get("respect_robots") is not True: issues.append("respect_robots should be true")
        lines.append(f"- `{src.get('id')}` [{src.get('category')}] — {src.get('base_url')} — issues: {', '.join(issues) if issues else 'none'}")
    return "\n".join(lines)
