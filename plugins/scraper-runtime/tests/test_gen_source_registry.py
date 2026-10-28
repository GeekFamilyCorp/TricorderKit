# -*- coding: utf-8 -*-
"""Tests gen_source_registry.py — parsing nominal + dédup + cas d'erreur."""
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import gen_source_registry as G

SAMPLE = """\
# Registre normalisé

| name | url | type | official | profile |
|---|---|---|---|---|
| Source A | https://a.example.com/ | api | oui | markdown_rag |
| Source B | https://b.example.com/ | html | non | static_html |
| Dup | https://a.example.com/ | api | oui | markdown_rag |
| Bad profile | https://c.example.com/ | html | non | wat |
"""


def test_parse_and_normalize_dedups_and_flags():
    rows = G.parse_markdown_table(SAMPLE)
    entries = G.normalize(rows)
    # 3 URLs distinctes (le doublon A est écarté)
    assert len(entries) == 3
    a = next(e for e in entries if e["name"] == "Source A")
    assert a["official"] is True and a["profile"] == "markdown_rag"
    b = next(e for e in entries if e["name"] == "Source B")
    assert b["official"] is False
    # profil invalide → champ profile absent (pas d'erreur)
    bad = next(e for e in entries if e["name"] == "Bad profile")
    assert "profile" not in bad


def test_yaml_output_is_wellformed_and_quotes_specials():
    entries = G.normalize(G.parse_markdown_table(SAMPLE))
    y = G.to_yaml(entries, scope="project-a")
    assert "project_scope: project-a" in y
    assert "count: 3" in y
    # une URL avec ':' doit être quotée
    assert '"https://a.example.com/"' in y


def test_main_dry_run_and_missing_file(tmp_path, capsys):
    # dry-run : pas de --out -> aperçu stdout, exit 0
    p = tmp_path / "reg.md"
    p.write_text(SAMPLE, encoding="utf-8")
    rc = G.main(["--in", str(p), "--project-scope", "demo"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "sources:" in out and "Source A" in out
    # fichier manquant -> exit 2
    rc2 = G.main(["--in", str(tmp_path / "nope.md")])
    assert rc2 == 2


def test_main_writes_file(tmp_path):
    p = tmp_path / "reg.md"
    p.write_text(SAMPLE, encoding="utf-8")
    out = tmp_path / "source_registry.yaml"
    rc = G.main(["--in", str(p), "--out", str(out)])
    assert rc == 0
    content = out.read_text(encoding="utf-8")
    assert content.startswith("# source_registry.yaml")
    assert "count: 3" in content
