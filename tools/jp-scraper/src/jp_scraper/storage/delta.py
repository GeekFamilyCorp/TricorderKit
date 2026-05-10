from pathlib import Path
from jp_scraper.storage.jsonl import read_jsonl, write_jsonl

def _latest_source_dir(source: str, runs: Path) -> Path:
    candidates = sorted([p for p in runs.glob(f"*/{source}") if p.is_dir()])
    if not candidates:
        raise FileNotFoundError(f"No runs found for source {source}")
    return candidates[-1]

def build_delta(source: str, runs: Path) -> Path:
    latest = _latest_source_dir(source, runs)
    records = read_jsonl(latest / "normalized_records.jsonl")
    write_jsonl(latest / "scan_delta.jsonl", records)
    return latest / "scan_delta.jsonl"
