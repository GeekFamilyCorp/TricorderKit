# -*- coding: utf-8 -*-
"""Tests extract_lessons.py — nominal + seuil de confiance (écartement)."""
import json

import _common as C
import extract_lessons as EL


def test_lessons_are_schema_valid(make_card):
    cards = [make_card(strategy="official_sources_first", relevance=0.85, idx=str(i))
             for i in range(5)]
    lessons = EL.build_lessons("scraping_jp", cards)
    assert lessons, "au moins une leçon attendue"
    for ls in lessons:
        assert C.validate(ls, "lesson") == [], ls["lesson_id"]
        assert ls["status"] == "observed"
        assert ls["human_review_required"] is True


def test_comparative_lesson_when_two_strategies(make_card):
    cards = ([make_card(strategy="official_sources_first", relevance=0.85, idx=f"o{i}")
              for i in range(3)] +
             [make_card(strategy="mangaupdates_first", relevance=0.5, idx=f"m{i}")
              for i in range(3)])
    lessons = EL.build_lessons("scraping_jp", cards)
    assert any("compare" in ls["lesson_id"] for ls in lessons)


def test_threshold_drops_low_confidence(tmp_path, make_card, capsys):
    """Seuil élevé : une seule carte -> confiance faible -> leçon écartée, pas écrite."""
    cards_dir = tmp_path / "cards"
    cards_dir.mkdir(parents=True)
    c = make_card(strategy="solo", relevance=0.8, idx="a")
    (cards_dir / f"{c['experience_card_id']}.json").write_text(json.dumps(c), encoding="utf-8")
    out_dir = tmp_path / "lessons"
    rc = EL.main(["--task-type", "scraping_jp", "--cards-dir", str(cards_dir),
                  "--out-dir", str(out_dir), "--min-confidence", "0.95", "--format", "json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "partial"
    assert not out_dir.exists() or not list(out_dir.glob("*.json"))


def test_real_write_and_no_cards(tmp_path, make_card, capsys):
    cards_dir = tmp_path / "cards"
    cards_dir.mkdir(parents=True)
    for i in range(5):
        c = make_card(strategy="official_sources_first", relevance=0.85, idx=str(i))
        (cards_dir / f"{c['experience_card_id']}.json").write_text(json.dumps(c), encoding="utf-8")
    out_dir = tmp_path / "lessons"
    rc = EL.main(["--task-type", "scraping_jp", "--cards-dir", str(cards_dir),
                  "--out-dir", str(out_dir), "--min-confidence", "0.3", "--format", "json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "success"
    assert list(out_dir.glob("*.json"))
    # cas sans cartes
    rc2 = EL.main(["--task-type", "ghost", "--cards-dir", str(tmp_path / "void"),
                   "--format", "json"])
    assert rc2 == 1
