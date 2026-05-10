from pathlib import Path
import json
from .models import Record


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def export_json(records: list[Record], output_dir: str | Path, filename: str) -> Path:
    out = ensure_dir(output_dir) / filename
    payload = [r.to_dict() for r in records]
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def export_markdown(records: list[Record], output_dir: str | Path, filename: str, title: str) -> Path:
    out = ensure_dir(output_dir) / filename
    lines = [f"# {title}", "", "| Catégorie | Action | Titre JP | Source | Fiabilité | Notes |", "|---|---|---|---|---|---|"]    
    for r in records:
        d = r.to_dict()
        lines.append(f"| {d['category']} | {d['action']} | {d['title_jp']} | {d['source']} | {d['confidence_label']} | {d['notes']} |")
    lines += ["", "## Notes de fiabilité", "", "- Confirmé : source officielle directe.", "- Probable : source commerciale fiable ou média professionnel.", "- À vérifier : source secondaire ou donnée non confirmée.", "- Incomplet : parseur non implémenté ou donnée absente."]
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
