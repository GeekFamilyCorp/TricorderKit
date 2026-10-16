"""Tests de scripts/check_preflight_contract.py (contrat d'entrée des plugins)."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_preflight_contract.py"
SCHEMA = ROOT / "core" / "contracts" / "skill_preflight.schema.json"

spec = importlib.util.spec_from_file_location("check_preflight_contract", SCRIPT)
cpc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cpc)

VALID = """
name: demo
preflight:
  dependencies:
    - {name: temporal, kind: tcp, target: "localhost:7233", required: true}
  env:
    - {name: DEMO_TOKEN, required: true, secret: true}
  stop_conditions: ["service injoignable"]
  retry: {max_attempts: 3}
  rollback: {strategy: git_revert, procedure: "git revert du commit puis redémarrage"}
  escalation: {risk_level: LOW, ask_before: []}
"""


def _run(tmp_path: Path, manifests: dict, *extra) -> tuple[int, None]:
    plugins = tmp_path / "plugins"
    for name, content in manifests.items():
        d = plugins / name
        d.mkdir(parents=True)
        if content is not None:
            (d / "manifest.yml").write_text(content, encoding="utf-8")
    return cpc.main(["--plugins-dir", str(plugins), "--schema", str(SCHEMA), *extra]), None


def _report(capsys) -> dict:
    return json.loads(capsys.readouterr().out)


def test_valid_contract_passes(tmp_path, capsys):
    code, _ = _run(tmp_path, {"demo": VALID})
    rep = _report(capsys)
    assert code == 0 and rep["summary"]["ok"] == 1


def test_missing_is_warning_only(tmp_path, capsys):
    code, _ = _run(tmp_path, {"a": None, "b": "name: b\n"})
    rep = _report(capsys)
    assert code == 0
    assert rep["summary"]["missing_manifest"] == 1 and rep["summary"]["missing_preflight"] == 1


def test_missing_fails_in_strict(tmp_path, capsys):
    code, _ = _run(tmp_path, {"b": "name: b\n"}, "--strict")
    assert code == 1 and _report(capsys)["status"] == "fail"


@pytest.mark.parametrize("bad", [
    VALID.replace("max_attempts: 3", "max_attempts: 0"),                        # réessai non borné
    VALID.replace("secret: true}", "secret: true, default: abc}"),              # défaut sur un secret
    VALID.replace('stop_conditions: ["service injoignable"]', "stop_conditions: []"),  # pas de stop
    VALID.replace("strategy: git_revert", "strategy: yolo"),                    # stratégie inconnue
    VALID.replace("localhost:7233", "C:\\\\Users\\\\someone\\\\x"),              # chemin personnel
])
def test_invalid_contracts_fail(tmp_path, capsys, bad):
    code, _ = _run(tmp_path, {"demo": bad})
    rep = _report(capsys)
    assert code == 1 and rep["summary"]["invalid"] == 1


def test_real_workflow_engine_manifest_is_valid(capsys):
    code = cpc.main(["--plugins-dir", str(ROOT / "plugins"), "--schema", str(SCHEMA)])
    rep = _report(capsys)
    we = next(r for r in rep["results"] if r["plugin"] == "workflow-engine")
    assert we["status"] == "ok", we["errors"]
    assert code == 0
