# -*- coding: utf-8 -*-
"""Tests compare_strategies.py — nominal (2 stratégies) + cas dégradé (1 seule)."""
import json

import _common as C
import compare_strategies as CS


def _seed(cards_dir, cards):
    cards_dir.mkdir(parents=True, exist_ok=True)
    for c in cards:
        (cards_dir / f"{c['experience_card_id']}.json").write_text(
            json.dumps(c), encoding="utf-8")


def test_two_strategies_produce_valid_variant(make_card):
    cards = [
        make_card(strategy="official_sources_first", relevance=0.85, idx="a"),
        make_card(strategy="official_sources_first", relevance=0.80, idx="b"),
        make_card(strategy="mangaupdates_first", relevance=0.55, idx="c"),
        make_card(strategy="mangaupdates_first", relevance=0.50, idx="d"),
    ]
    variant, stats = CS.build_variant("scraping_jp", cards, "japan-alliance")
    assert C.validate(variant, "strategy_variant") == []
    # official doit gagner (meilleur score)
    assert variant["decision"]["winning_variant"] == "official_sources_first"
    assert variant["variants"][0]["score_average"] >= variant["variants"][1]["score_average"]


def test_card_score_penalizes_duplicates(make_card):
    low_dupe = make_card(relevance=0.8)
    high_dupe = make_card(relevance=0.8)
    high_dupe["quality"]["duplicate_rate"] = 0.5
    assert CS.card_score(high_dupe) < CS.card_score(low_dupe)


def test_single_strategy_is_partial(tmp_path, make_card, capsys):
    """Échec attendu de comparaison : une seule stratégie -> status partial, pas d'objet JSON."""
    cards_dir = tmp_path / "cards"
    _seed(cards_dir, [make_card(strategy="only_one", idx="a"),
                      make_card(strategy="only_one", idx="b")])
    reports = tmp_path / "reports"
    rc = CS.main(["--task-type", "scraping_jp", "--cards-dir", str(cards_dir),
                  "--reports-dir", str(reports), "--format", "json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "partial"
    # MD écrit mais pas le JSON strategy_variant (schéma exige >=2 variantes)
    assert (reports / "strategy_scraping_jp.md").exists()
    assert not (reports / "strategy_scraping_jp.json").exists()


def test_no_cards_errors(tmp_path, capsys):
    rc = CS.main(["--task-type", "ghost", "--cards-dir", str(tmp_path / "empty"),
                  "--reports-dir", str(tmp_path / "r"), "--format", "json"])
    assert rc == 1
    out = json.loads(capsys.readouterr().out)
    assert out["error"]["code"] == "ERR_NO_CARDS"
