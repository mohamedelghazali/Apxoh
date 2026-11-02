# Apxoh — Makefile
# Unified commands for local development and CI.

.DEFAULT_GOAL := help
.PHONY: help install install-dev clean test test-unit test-integration test-security \
        test-rules test-fixtures lint format typecheck audit validate self-audit ci \
        release-check docs install-models verify-all verify-fixtures examples

PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
PYTEST := $(BIN)/pytest
RUFF := $(BIN)/ruff
MYPY := $(BIN)/mypy
PIP := $(BIN)/pip
BANDIT := $(BIN)/bandit
PIP_AUDIT := $(BIN)/pip-audit
ARKHON := $(BIN)/arkhon

help:
	@echo "Apxoh — available targets:"
	@echo ""
	@echo "  Setup: install, install-dev, install-models"
	@echo "  Development: test, test-unit, test-integration, test-security,"
	@echo "               test-rules, test-fixtures, lint, format, typecheck, audit"
	@echo "  Verification: validate, verify-all, verify-fixtures, self-audit"
	@echo "  Release: ci, release-check"
	@echo "  Utilities: clean, docs, examples"

$(VENV):
	$(PYTHON) -m venv $(VENV)

install: $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e .

install-dev: $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	@if [ -x "$(BIN)/pre-commit" ]; then $(BIN)/pre-commit install; fi

install-models:
	@$(PYTHON) -c "from pathlib import Path; p=Path('src/arkhon/integrations/models'); print('Model integration directories:'); [print('  -', x.name) for x in sorted(p.iterdir()) if x.is_dir()]"

clean:
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

test:
	$(PYTEST) -ra

test-unit:
	$(PYTEST) tests/unit -ra

test-integration:
	$(PYTEST) tests/integration -ra

test-security:
	$(PYTEST) tests/security -ra -v

test-rules:
	$(PYTEST) tests/rules tests/unit/rules -ra

test-fixtures:
	$(PYTEST) tests/languages -ra -v

lint:
	$(RUFF) check src tests scripts

format:
	$(RUFF) check --fix src tests scripts
	$(RUFF) format src tests scripts

typecheck:
	$(MYPY) --strict src

audit:
	$(BANDIT) -r src -c pyproject.toml
	$(PIP_AUDIT) --strict --desc

validate:
	$(PYTHON) scripts/validation/validate_all.py

verify-all:
	$(ARKHON) validate
	$(ARKHON) inspect . --json
	$(ARKHON) verify . --domain testing

verify-fixtures:
	@set -e; for fixture in tests/languages/fixtures/*-project; do \
		if [ -d "$$fixture" ]; then \
			echo "=== Inspecting $$fixture ==="; \
			$(ARKHON) inspect "$fixture" --json; \
			$(ARKHON) verify "$fixture" --domain testing; \
		fi; \
	done

self-audit: verify-all

ci: lint typecheck test validate

release-check:
	@echo "Checking release readiness..."
	@test -f VERSION || (echo "missing VERSION" && exit 1)
	@test -f CHANGELOG.md || (echo "missing CHANGELOG.md" && exit 1)
	@$(PYTHON) -c "import tomllib,pathlib; v=pathlib.Path('VERSION').read_text().strip(); p=tomllib.loads(pathlib.Path('pyproject.toml').read_text()); assert v == p['project']['version'], f'VERSION={v} vs pyproject={p[\"project\"][\"version\"]}'; print('versions match:', v)"
	@$(MAKE) ci

docs:
	@echo "Documentation rendering is not implemented yet."

examples:
	@echo "Available example projects:"
	@for d in examples/*/; do \
		if [ -d "$$d" ]; then echo " - $$d"; fi; \
	done
