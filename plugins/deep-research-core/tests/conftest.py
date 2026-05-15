"""
conftest.py — deep-research-core tests
Gestion du marqueur pytest live (appels reseau reels).

Usage :
    pytest tests/                        # tests unitaires seulement
    pytest tests/ --live                 # inclut les tests live (reseau requis)
    pytest tests/ --live -v              # verbose
    pytest tests/ --live -k mangadex     # filtrer par source
"""
import sys
from pathlib import Path

# Injecter scripts/ dans sys.path pour les imports directs
_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def pytest_addoption(parser):
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Executer les tests live (appels reseau reels vers APIs externes)",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "live: test necessitant un acces reseau vers APIs externes",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--live"):
        skip_live = __import__("pytest").mark.skip(
            reason="Tests live desactives. Utilisez --live pour les executer."
        )
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip_live)
