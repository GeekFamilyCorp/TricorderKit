#!/usr/bin/env python3
"""TricorderKit - adaptateur d'ingestion documentaire (MarkItDown).

Convertit un document vers du Markdown normalise avec frontmatter TricorderKit.

Garde-fous (non negociables) :
  - l'original n'est jamais supprime (copie en archive si --archive-dir fourni) ;
  - pas d'ecrasement silencieux d'un .md existant (sauf --overwrite) ;
  - extension verifiee contre une liste blanche ;
  - rollback : TK_MARKITDOWN_ENABLED=false -> sortie immediate (no-op) ;
  - echec -> code retour non nul + (optionnel) copie en quarantaine.

Usage :
  python tk_ingest_document.py INPUT OUTPUT.md
         [--archive-dir DIR] [--quarantine-dir DIR]
         [--report PATH.jsonl] [--overwrite]

Sortie : Markdown exploitable par le vault Obsidian / RAG local.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".xlsx", ".xls", ".pptx",
    ".html", ".htm", ".csv", ".json", ".xml",
    ".zip", ".epub", ".txt",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _build_frontmatter(src: Path, src_hash: str) -> str:
    lines = [
        "---",
        f'source_file: "{src.name}"',
        f'source_path: "{src.as_posix()}"',
        f'source_hash: "{src_hash}"',
        f'source_extension: "{src.suffix.lower()}"',
        'conversion_tool: "markitdown"',
        f'conversion_date: "{_now()}"',
        'ingestion_status: "converted"',
        "---",
        "",
    ]
    return "\n".join(lines)


def _report(report_path: Path | None, record: dict) -> None:
    if report_path is None:
        return
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _quarantine(src: Path, quarantine_dir: Path | None) -> None:
    if quarantine_dir is None:
        return
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, quarantine_dir / src.name)


def main() -> int:
    # --- Rollback global ---
    if os.getenv("TK_MARKITDOWN_ENABLED", "true").lower() == "false":
        print("TK_MARKITDOWN_ENABLED=false : ingestion desactivee (no-op).",
              file=sys.stderr)
        return 0

    parser = argparse.ArgumentParser(description="Ingestion documentaire MarkItDown.")
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--archive-dir")
    parser.add_argument("--quarantine-dir")
    parser.add_argument("--report")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    archive_dir = Path(args.archive_dir).resolve() if args.archive_dir else None
    quarantine_dir = Path(args.quarantine_dir).resolve() if args.quarantine_dir else None
    report_path = Path(args.report).resolve() if args.report else None

    # --- Validations ---
    if not input_path.exists():
        print(f"Input introuvable : {input_path}", file=sys.stderr)
        return 1

    ext = input_path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        print(f"Extension non autorisee : {ext}", file=sys.stderr)
        return 1

    if output_path.exists() and not args.overwrite:
        print(f"Sortie deja presente (pas d'ecrasement) : {output_path}",
              file=sys.stderr)
        return 1

    # --- Conversion ---
    try:
        from markitdown import MarkItDown
    except ImportError:
        print("markitdown non installe : pip install \"markitdown[pdf,docx,xlsx,pptx]\"",
              file=sys.stderr)
        return 1

    src_hash = _file_hash(input_path)
    try:
        md = MarkItDown(enable_plugins=False)
        result = md.convert(str(input_path))
        body = result.text_content or ""
        if not body.strip():
            raise ValueError("conversion vide (PDF scanne sans OCR ?)")
    except Exception as exc:  # noqa: BLE001 - on veut tracer tout echec
        _quarantine(input_path, quarantine_dir)
        _report(report_path, {
            "ts": _now(), "status": "failed", "error": str(exc),
            "source_file": input_path.name, "source_hash": src_hash,
        })
        print(f"Echec de conversion : {exc}", file=sys.stderr)
        return 1

    # --- Ecriture Markdown + frontmatter ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_build_frontmatter(input_path, src_hash) + body,
                           encoding="utf-8")

    # --- Archivage de l'original (jamais de suppression) ---
    if archive_dir is not None:
        archive_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(input_path, archive_dir / input_path.name)

    _report(report_path, {
        "ts": _now(), "status": "converted",
        "source_file": input_path.name, "source_hash": src_hash,
        "output": output_path.as_posix(), "chars": len(body),
    })
    print(f"Converti : {input_path.name} -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
