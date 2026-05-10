from pathlib import Path
import yaml

def load_sources(path: Path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data.get("sources", [])

def get_source(source_id: str, path: Path):
    for src in load_sources(path):
        if src.get("id") == source_id:
            return src
    raise KeyError(f"Unknown source: {source_id}")

def load_selectors(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
