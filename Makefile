# TricorderKit v0.9 — Makefile
# Usage: make <target>
# Requires: Python 3.11+, Docker, GNU make (Windows: use 'mingw32-make' or 'nmake')

PYTHON  := python
TK      := $(PYTHON) cli/tk.py
PYTEST  := $(PYTHON) -m pytest

.PHONY: help install boot doctor health test test-all lint \
        docker-up docker-down docker-logs clean validate security \
        gate docs-sync gates install-hooks

# ── Default ──────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "TricorderKit v0.9 — Available targets"
	@echo "────────────────────────────────────────"
	@echo "  make install      Guided install (prerequisites + .env + Docker)"
	@echo "  make boot         Boot the agent session (/tk:boot)"
	@echo "  make doctor       Full health check (14 checks)"
	@echo "  make health       Quick health alias"
	@echo "  make test         Run test suite (fast — no live tests)"
	@echo "  make test-all     Run all tests including live"
	@echo "  make lint         Run linters (ruff + mypy)"
	@echo "  make docker-up    Start infrastructure services"
	@echo "  make docker-down  Stop infrastructure services"
	@echo "  make docker-logs  Tail service logs"
	@echo "  make validate     Validate repo structure"
	@echo "  make security     Run security audit"
	@echo "  make gate         Run public-boundary leak gate (terms + personal paths)"
	@echo "  make docs-sync    Run docs-sync gate (README/STATUS <-> structure/version/tests)"
	@echo "  make gates        Run all release gates (boundary + docs-sync)"
	@echo "  make install-hooks Enable the pre-push gates (.githooks)"
	@echo "  make clean        Remove __pycache__ and .pytest_cache"
	@echo ""

# ── Install & Boot ────────────────────────────────────────────────────────────

install:
	$(PYTHON) scripts/install-menu.py

boot:
	@echo "→ Run /tk:boot inside your Claude Code session."
	@echo "  (Claude Code must be running — this cannot be invoked via make)"

# ── Health ────────────────────────────────────────────────────────────────────

doctor:
	$(TK) doctor

health:
	$(TK) health

# ── Tests ─────────────────────────────────────────────────────────────────────

test:
	$(PYTEST) tests/ -x -q --ignore=tests/live

test-all:
	$(PYTEST) tests/ -x -q

# ── Lint ──────────────────────────────────────────────────────────────────────

lint:
	$(PYTHON) -m ruff check . --select E,W,F --ignore E501 || true
	$(PYTHON) -m mypy cli/tk.py --ignore-missing-imports || true

# ── Docker ────────────────────────────────────────────────────────────────────

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f --tail=100

# ── Audit ─────────────────────────────────────────────────────────────────────

validate:
	$(PYTHON) scripts/validate_repo.py

security:
	$(TK) security scan

# ── Public boundary gate (DEC-026) ────────────────────────────────────────────

gate:
	$(PYTHON) scripts/check_public_boundary.py

docs-sync:
	$(PYTHON) scripts/check_docs_sync.py

# Aggregate: every gate that must be green before a public push (R37 + R39)
gates: gate docs-sync

install-hooks:
	git config core.hooksPath .githooks
	@echo "Pre-push gates active (.githooks/pre-push). Disable: git config --unset core.hooksPath"

# ── Clean ─────────────────────────────────────────────────────────────────────

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean done."
