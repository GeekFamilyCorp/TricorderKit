"""Tests de l'adaptateur d'ingestion documentaire (MarkItDown).

pytest --basetemp hors repo (cf. feedback obsidian_goat_patterns).
Pas de reseau, conversions locales uniquement.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "tk_ingest_document.py"


def _run(args, env=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, env=env,
    )


def test_convert_csv_produces_markdown_with_frontmatter(tmp_path):
    src = tmp_path / "sample.csv"
    src.write_text("title,year\nNaruto,1999\nBleach,2001\n", encoding="utf-8")
    out = tmp_path / "out.md"
    res = _run([str(src), str(out)])
    assert res.returncode == 0, res.stderr
    text = out.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert 'conversion_tool: "markitdown"' in text
    assert "source_hash:" in text
    assert "Naruto" in text


def test_rejects_unknown_extension(tmp_path):
    src = tmp_path / "bad.exe"
    src.write_bytes(b"MZ\x00\x00")
    out = tmp_path / "out.md"
    res = _run([str(src), str(out)])
    assert res.returncode == 1
    assert "Extension non autorisee" in res.stderr


def test_no_overwrite_without_flag(tmp_path):
    src = tmp_path / "sample.csv"
    src.write_text("a,b\n1,2\n", encoding="utf-8")
    out = tmp_path / "out.md"
    out.write_text("PRESENT", encoding="utf-8")
    res = _run([str(src), str(out)])
    assert res.returncode == 1
    assert out.read_text(encoding="utf-8") == "PRESENT"


def test_rollback_env_disables(tmp_path):
    import os
    src = tmp_path / "sample.csv"
    src.write_text("a,b\n1,2\n", encoding="utf-8")
    out = tmp_path / "out.md"
    env = {**os.environ, "TK_MARKITDOWN_ENABLED": "false"}
    res = _run([str(src), str(out)], env=env)
    assert res.returncode == 0
    assert not out.exists()


def test_preserves_original_on_archive(tmp_path):
    src = tmp_path / "sample.csv"
    src.write_text("a,b\n1,2\n", encoding="utf-8")
    out = tmp_path / "out.md"
    archive = tmp_path / "archive"
    res = _run([str(src), str(out), "--archive-dir", str(archive)])
    assert res.returncode == 0
    assert src.exists()                       # original jamais supprime
    assert (archive / "sample.csv").exists()  # copie archivee
