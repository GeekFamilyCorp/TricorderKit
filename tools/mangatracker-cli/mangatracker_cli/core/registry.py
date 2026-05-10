from pathlib import Path
import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "sources.yaml"

def load_sources(config_path: str | None = None) -> dict:
    path = Path(config_path) if config_path else DEFAULT_CONFIG
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def get_source(category: str, key: str, config_path: str | None = None) -> dict:
    sources = load_sources(config_path)
    try:
        return sources[category][key]
    except KeyError as exc:
        available = sorted((sources.get(category) or {}).keys())
        raise SystemExit(f"Source inconnue: {category}/{key}. Disponibles: {available}") from exc
