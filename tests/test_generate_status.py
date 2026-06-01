"""
test_generate_status.py — Tests generate_status.py + tk report
TricorderKit v0.9

Valide sans services réels :
  - collect_services() renvoie une liste structurée
  - collect_repo_meta() renvoie version/commit/branch
  - collect_hook_stats() gère l'absence de fichiers log
  - collect_workflow_cycles() gère l'absence de fichiers log
  - collect_budget_alerts() gère l'absence de fichiers log
  - format_status_md() génère un Markdown structuré valide
  - generate_status --output json renvoie un dict complet
  - generate_status --no-status-md ne crée pas STATUS.md
  - tk report generate --no-status-md crée un rapport dans reports/
  - STATUS.md contient les sections attendues

Usage :
  pytest tests/test_generate_status.py -v
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

# ── Chemins ────────────────────────────────────────────────────────────────────
REPO_ROOT       = Path(__file__).resolve().parent.parent
GENERATE_SCRIPT = REPO_ROOT / "scripts" / "generate_status.py"
TK_CLI          = REPO_ROOT / "cli" / "tk.py"
STATUS_MD       = REPO_ROOT / "STATUS.md"


# ── Import du module pour tests unitaires ─────────────────────────────────────
import importlib.util
spec = importlib.util.spec_from_file_location("generate_status", GENERATE_SCRIPT)
gs   = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gs)


# ── Tests : fichiers requis ────────────────────────────────────────────────────

def test_generate_script_exists():
    assert GENERATE_SCRIPT.exists(), "scripts/generate_status.py introuvable"


def test_tk_cli_exists():
    assert TK_CLI.exists(), "cli/tk.py introuvable"


# ── Tests : collecteurs ────────────────────────────────────────────────────────

def test_collect_services_returns_list():
    services = gs.collect_services()
    assert isinstance(services, list)
    assert len(services) >= 4


def test_collect_services_structure():
    for svc in gs.collect_services():
        assert "name"   in svc
        assert "port"   in svc
        assert "up"     in svc
        assert "status" in svc
        assert svc["status"] in ("up", "down")


def test_collect_repo_meta_has_required_keys():
    meta = gs.collect_repo_meta()
    for key in ("version", "commit", "branch", "tests", "generated_at"):
        assert key in meta, f"collect_repo_meta: clé '{key}' manquante"


def test_collect_repo_meta_commit_not_empty():
    meta = gs.collect_repo_meta()
    assert meta["commit"] != "unknown", "commit ne devrait pas être 'unknown' dans un repo git"


def test_collect_hook_stats_no_files(tmp_path, monkeypatch):
    """Sans fichiers log, collect_hook_stats renvoie des valeurs vides."""
    monkeypatch.setattr(gs, "HOOKS_CACHE_DIR", tmp_path)
    result = gs.collect_hook_stats()
    assert result["post_records"] == 0
    assert result["pre_records"]  == 0
    assert result["skills"]       == []
    assert result["total_runs"]   == 0


def test_collect_hook_stats_with_records(tmp_path, monkeypatch):
    """Avec des records, collect_hook_stats agrège correctement."""
    monkeypatch.setattr(gs, "HOOKS_CACHE_DIR", tmp_path)
    post_log = tmp_path / "post_execution.log"
    records = [
        {"skill": "test-skill", "quality_score": 0.9, "tokens_used": 100},
        {"skill": "test-skill", "quality_score": 0.7, "tokens_used": 200},
        {"skill": "other-skill", "quality_score": 0.3, "tokens_used": 50},
    ]
    post_log.write_text(
        "\n".join(json.dumps(r) for r in records), encoding="utf-8"
    )
    result = gs.collect_hook_stats()
    assert result["post_records"] == 3
    assert result["total_runs"]   == 3
    skills_map = {s["skill"]: s for s in result["skills"]}
    assert "test-skill"  in skills_map
    assert "other-skill" in skills_map
    assert skills_map["test-skill"]["runs"]      == 2
    assert skills_map["test-skill"]["avg_score"] == 0.8


def test_collect_workflow_cycles_no_files(tmp_path, monkeypatch):
    monkeypatch.setattr(gs, "HOOKS_CACHE_DIR", tmp_path)
    result = gs.collect_workflow_cycles()
    assert result["total_records"] == 0
    assert result["workflows"]     == []


def test_collect_workflow_cycles_aggregates(tmp_path, monkeypatch):
    monkeypatch.setattr(gs, "HOOKS_CACHE_DIR", tmp_path)
    wf_log = tmp_path / "workflow_cycles.log"
    records = [
        {"workflow": "sourceWatch", "timestamp": "2026-05-22T10:00:00Z"},
        {"workflow": "sourceWatch", "timestamp": "2026-05-22T11:00:00Z"},
        {"workflow": "usageObserver", "timestamp": "2026-05-22T12:00:00Z"},
    ]
    wf_log.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    result = gs.collect_workflow_cycles()
    assert result["total_records"] == 3
    wf_map = {w["name"]: w for w in result["workflows"]}
    assert wf_map["sourceWatch"]["cycles"]   == 2
    assert wf_map["usageObserver"]["cycles"] == 1


def test_collect_budget_alerts_no_files(tmp_path, monkeypatch):
    monkeypatch.setattr(gs, "HOOKS_CACHE_DIR", tmp_path)
    result = gs.collect_budget_alerts()
    assert result["total_alerts"] == 0
    assert result["recent"]       == []


# ── Tests : formateurs ─────────────────────────────────────────────────────────

def test_format_status_md_has_required_sections():
    data = gs.collect_all()
    md   = gs.format_status_md(data)
    for section in [
        "# TricorderKit — STATUS",
        "## 🐳 Services Docker",
        "## 🪝 Hooks",
        "## ⏱️ Cycles workflow",
        "## 💰 Alertes budget",
        "## 🔌 Plugins actifs",
    ]:
        assert section in md, f"Section manquante dans STATUS.md : {section!r}"


def test_format_status_md_has_frontmatter():
    data = gs.collect_all()
    md   = gs.format_status_md(data)
    assert md.startswith("---"), "STATUS.md doit commencer par frontmatter YAML"
    assert "generated:" in md
    assert "version:" in md


def test_format_status_md_has_service_rows():
    data = gs.collect_all()
    md   = gs.format_status_md(data)
    for svc_name in ["Neo4j", "Qdrant", "Langfuse", "Temporal"]:
        assert svc_name in md, f"Service {svc_name} absent du tableau STATUS.md"


def test_format_status_md_no_alerts_message():
    data = {**gs.collect_all(), "budget": {"total_alerts": 0, "recent": []}}
    md   = gs.format_status_md(data)
    assert "Aucune alerte budget" in md


def test_format_status_md_with_alerts():
    data = {**gs.collect_all(), "budget": {
        "total_alerts": 3,
        "recent": [{"workflow": "sourceWatch", "tokens_used": 5000,
                    "timestamp": "2026-05-22T10:00:00Z"}],
    }}
    md = gs.format_status_md(data)
    assert "3 alerte(s)" in md
    assert "sourceWatch" in md


# ── Tests : génération fichiers ───────────────────────────────────────────────

def test_generate_json_output():
    r = subprocess.run(
        [sys.executable, str(GENERATE_SCRIPT), "--output", "json", "--no-status-md"],
        capture_output=True, text=True, cwd=REPO_ROOT, timeout=30,
        env={**__import__("os").environ, "PYTHONUTF8": "1"},
    )
    assert r.returncode == 0, f"generate_status --output json échoué : {r.stderr}"
    data = json.loads(r.stdout)
    for key in ("meta", "services", "hooks", "workflows", "budget", "plugins"):
        assert key in data, f"Clé '{key}' absente de la sortie JSON"


def test_generate_no_status_md_does_not_write(tmp_path):
    """--no-status-md ne doit pas écrire STATUS.md dans le cwd."""
    r = subprocess.run(
        [sys.executable, str(GENERATE_SCRIPT), "--no-status-md"],
        capture_output=True, text=True, cwd=str(tmp_path), timeout=30,
        env={**__import__("os").environ, "PYTHONUTF8": "1"},
    )
    # STATUS.md ne doit PAS exister dans tmp_path
    assert not (tmp_path / "STATUS.md").exists(), \
        "STATUS.md ne devrait pas être créé avec --no-status-md"


def test_status_md_written_by_default():
    """Le générateur produit un STATUS.md avec en-tête et section Services Docker.

    On valide le CONTRAT DE SORTIE du générateur (format_status_md), pas le
    STATUS.md vitrine curaté à la racine du dépôt : ce dernier est un document
    maintenu à la main et validé par le docs-sync gate, distinct de la sortie
    runtime de generate_status.py.
    """
    md = gs.format_status_md(gs.collect_all())
    assert "# TricorderKit — STATUS" in md
    assert "Services Docker" in md


def test_tk_report_generate_creates_report():
    """tk report generate --no-status-md crée un rapport dans reports/."""
    r = subprocess.run(
        [sys.executable, str(TK_CLI), "report", "generate", "--no-status-md"],
        capture_output=True, text=True, cwd=REPO_ROOT, timeout=30,
        env={**__import__("os").environ, "PYTHONUTF8": "1"},
    )
    assert r.returncode == 0, f"tk report generate échoué : {r.stderr}"
    reports_dir = REPO_ROOT / "reports"
    assert reports_dir.exists(), "reports/ doit exister"
    report_files = list(reports_dir.glob("status_*.md"))
    assert len(report_files) >= 1, "Au moins un rapport status_*.md doit exister"


def test_tk_report_show_outputs_content():
    """tk report show affiche le contenu de STATUS.md."""
    r = subprocess.run(
        [sys.executable, str(TK_CLI), "report", "show"],
        capture_output=True, text=True, cwd=REPO_ROOT, timeout=30,
        env={**__import__("os").environ, "PYTHONUTF8": "1"},
    )
    assert r.returncode == 0, f"tk report show échoué : {r.stderr}"
    assert "TricorderKit" in r.stdout
