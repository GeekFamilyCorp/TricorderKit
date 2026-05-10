from pathlib import Path
from datetime import datetime
from jp_scraper.storage.config import get_source, load_selectors
from jp_scraper.storage.jsonl import write_jsonl
from jp_scraper.collectors.rss_collector import fetch_feed
from jp_scraper.collectors.http_collector import fetch_url
from jp_scraper.extractors.html_extractor import extract_listing
from jp_scraper.extractors.trafilatura_extractor import extract_url
from jp_scraper.normalizers.japanese_text import normalize_record
from jp_scraper.storage.hashing import stable_hash
import json

def _run_dir(out_root: Path, source_id: str) -> Path:
    day = datetime.now().strftime("%Y-%m-%d")
    run_dir = out_root / day / source_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir

def _write_run(run_dir: Path, records: list[dict], raw_urls: list[str] | None = None, errors: list[dict] | None = None):
    normalized = []
    for rec in records:
        n = normalize_record(rec)
        n["record_hash"] = stable_hash({k:v for k,v in n.items() if k not in ("fetched_at",)})
        normalized.append(n)
    write_jsonl(run_dir / "extracted_records.jsonl", records)
    write_jsonl(run_dir / "normalized_records.jsonl", normalized)
    write_jsonl(run_dir / "errors.jsonl", errors or [])
    (run_dir / "raw_urls.txt").write_text("\n".join(raw_urls or []), encoding="utf-8")
    write_jsonl(run_dir / "scan_delta.jsonl", normalized)
    token = {
        "records_extracted": len(records),
        "records_normalized": len(normalized),
        "estimated_raw_html_chars": sum(len(str(r)) for r in records),
        "summary_target_chars": 6000,
        "llm_should_read": ["scan_summary.md", "scan_delta.jsonl", "errors.jsonl"],
        "llm_should_not_read": ["raw html", "full DOM"],
    }
    (run_dir / "token_savings.json").write_text(json.dumps(token, ensure_ascii=False, indent=2), encoding="utf-8")
    return run_dir

def run_source(source_id: str, mode: str, config_path: Path, selectors_path: Path, out_root: Path) -> Path:
    source = get_source(source_id, config_path)
    selectors = load_selectors(selectors_path)
    profile = selectors.get(source.get("selectors_profile"), {})
    run_dir = _run_dir(out_root, source_id)
    errors = []
    records = []
    urls = []

    methods = source.get("method_priority", [])
    selected = mode if mode != "auto" else (methods[0] if methods else "http")

    if selected == "rss":
        if not source.get("rss_url"):
            errors.append({"error": "rss_url_missing", "source": source_id})
        else:
            records = fetch_feed(source["rss_url"])
            urls = [source["rss_url"]]
    elif selected == "trafilatura":
        records = extract_url(source["base_url"])
        urls = [source["base_url"]]
    elif selected in ("http", "sitemap", "playwright"):
        response = fetch_url(source["base_url"])
        urls = [source["base_url"]]
        if response.get("error"):
            errors.append(response)
        else:
            records = extract_listing(response["text"], source["base_url"], profile)
            write_jsonl(run_dir / "fetched_pages.jsonl", [{
                "url": response["url"],
                "status_code": response["status_code"],
                "headers": response.get("headers", {}),
                "html_chars": len(response.get("text") or ""),
            }])
    else:
        errors.append({"error": "unknown_mode", "mode": selected})

    _write_run(run_dir, records, urls, errors)
    return run_dir

def run_url(url: str, mode: str, out_root: Path) -> Path:
    source_id = "single-url"
    run_dir = _run_dir(out_root, source_id)
    if mode == "trafilatura":
        records = extract_url(url)
        errors = [r for r in records if r.get("record_type") == "error"]
    else:
        response = fetch_url(url)
        records = [{"record_type":"page", "title": url, "url": response["url"], "text": response.get("text", "")[:10000], "source_method":"http"}]
        errors = [response] if response.get("error") else []
    _write_run(run_dir, records, [url], errors)
    return run_dir
