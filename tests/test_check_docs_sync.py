"""Tests du gate docs-sync (scripts/check_docs_sync.py, DEC-028 / R39)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_docs_sync.py"
_spec = importlib.util.spec_from_file_location("check_docs_sync", _SCRIPT)
ds = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ds)


def _make_repo(tmp: Path, *, version="0.9.5", readme_ver="0.9.5",
               status_ver="0.9.5", tests=503, status_tests=503,
               plugins=("alpha", "beta"), readme_count=2,
               status_rows=("alpha", "beta")) -> Path:
    (tmp / "plugins").mkdir()
    for p in plugins:
        (tmp / "plugins" / p).mkdir()
    (tmp / "CHANGELOG.md").write_text(
        f"# CHANGELOG\n\n## [{version}] - 2026-06-01 - x\n\n## [0.9.0] - old\n",
        encoding="utf-8",
    )
    (tmp / "README.md").write_text(
        f"[![Version](badge/version-v{readme_ver}-blue)](x)\n"
        f"[![Tests](badge/tests-{tests}%20PASS-green)](x)\n"
        f"  plugins/  <- {readme_count} plugins\n"
        f"- **{tests} tests passing**\n"
        f"*TricorderKit v{readme_ver} - 2026*\n",
        encoding="utf-8",
    )
    rows = "".join(f"| {r} | ok | ok |\n" for r in status_rows)
    (tmp / "STATUS.md").write_text(
        f"# STATUS.md - TricorderKit v{status_ver}\n\n"
        "## Tableau de bord plugins\n\n| Plugin | A | B |\n|---|---|---|\n"
        f"{rows}\n"
        f"*TricorderKit v{status_ver} - {status_tests} tests PASS, 0 FAIL*\n",
        encoding="utf-8",
    )
    return tmp


def test_synced_repo_passes(tmp_path):
    repo = _make_repo(tmp_path)
    assert ds.run_checks(repo, check_tests=False) == []


def test_version_drift_detected(tmp_path):
    repo = _make_repo(tmp_path, status_ver="0.9")
    errs = ds.run_checks(repo, check_tests=False)
    assert any(f["check"] == "version" for f in errs)


def test_test_count_mismatch_detected(tmp_path):
    repo = _make_repo(tmp_path, status_tests=499)
    errs = ds.run_checks(repo, check_tests=False)
    assert any(f["check"] == "tests" for f in errs)


def test_phantom_plugin_in_status_detected(tmp_path):
    repo = _make_repo(tmp_path, status_rows=("alpha", "beta", "ghost"))
    errs = ds.run_checks(repo, check_tests=False)
    assert any("ghost" in f["message"] for f in errs)


def test_missing_plugin_from_status_detected(tmp_path):
    repo = _make_repo(tmp_path, status_rows=("alpha",))
    errs = ds.run_checks(repo, check_tests=False)
    assert any("beta" in f["message"] for f in errs)


def test_readme_plugin_count_drift_detected(tmp_path):
    repo = _make_repo(tmp_path, readme_count=3)
    errs = ds.run_checks(repo, check_tests=False)
    assert any("README annonce 3 plugins" in f["message"] for f in errs)


def test_canonical_version_parsing():
    assert ds.canonical_version("## [1.2.3] - x\n## [1.0.0]") == "1.2.3"
    assert ds.canonical_version("no version here") is None
