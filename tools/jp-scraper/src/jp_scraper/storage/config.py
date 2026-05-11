from pathlib import Path
from typing import Optional
import yaml

# Config files bundled inside the installed package
_PKG_CONFIG = Path(__file__).parent.parent / "config"


def load_sources(path: Optional[Path] = None) -> list:
    if path is None:
        path = _PKG_CONFIG / "sources.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data.get("sources", [])


def get_source(source_id: str, path: Optional[Path] = None):
    for src in load_sources(path):
        if src.get("id") == source_id:
            return src
    raise KeyError(f"Unknown source: {source_id}")


def load_selectors(path: Optional[Path] = None) -> dict:
    if path is None:
        path = _PKG_CONFIG / "selectors.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
