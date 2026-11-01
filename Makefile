# Apxoh — Makefile
# Unified commands for local development and CI.

.DEFAULT_GOAL := help
.PHONY: help install install-dev clean test test-unit test-integration test-security test-rules lint format typecheck audit validate self-audit ci release-check docs

PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
PYTEST := $(BIN)/pytest
RUFF := $(BIN)/ruff
MYPY := $(BIN)/mypy
PIP := $(BIN)/pip
BANDIT := $(BIN)/bandit
PIP_AUDIT := $(BIN)/pip-audit
CHECK_JSONSCHEMA := $(BIN)/check-jsonschema

help:
	@echo "Apxoh — available targets:"
	@echo "  install          Install package (prod only)"
	@echo "  install-dev      Install package + dev dependencies"
	@echo "  clean            Remove build artifacts and caches"
	@echo "  test             Run full test suite"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-security    Run security tampering/bypass tests"
	@echo "  test-rules       Run rule validation tests"
	@echo "  lint             Run ruff (no fix)"
	@echo "  format           Run ruff --fix + format"
	@echo "  typecheck        Run mypy --strict"
	@echo "  audit            Run pip-audit + bandit"
	@echo "  validate         Validate schemas + rules + manifest"
	@echo "  self-audit       Apxoh governs itself"
	@echo "  ci               Full CI pipeline (lint+type+test+audit+validate)"
	@echo "  release-check    Verify release readiness"
	@echo "  docs             Render documentation (future)"

$(VENV):
	$(PYTHON) -m venv $(VENV)

install: $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e .

install-dev: $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	$(BIN)/pre-commit install || true

clean:
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

test:
	$(PYTEST) -ra

test-unit:
	$(PYTEST) tests/unit -ra

test-integration:
	$(PYTEST) tests/integration -ra

test-security:
	$(PYTEST) tests/security -ra -v

test-rules:
	$(PYTEST) tests/rules -ra

lint:
	$(RUFF) check src tests

format:
	$(RUFF) check --fix src tests
	$(RUFF) format src tests

typecheck:
	$(MYPY) src

audit:
	$(BANDIT) -r src -c pyproject.toml
	$(PIP_AUDIT) --strict --desc

validate:
	$(PYTHON) scripts/validation/validate_all.py

self-audit:
	$(BIN)/arkhon doctor
	$(BIN)/arkhon --version
	$(PYTEST) tests -ra

ci: lint typecheck test audit validate
	@echo "CI pipeline passed."

release-check:
	@echo "Checking release readiness..."
	@test -f VERSION || (echo "missing VERSION" && exit 1)
	@test -f CHANGELOG.md || (echo "missing CHANGELOG.md" && exit 1)
	@$(PYTHON) -c "import tomllib,pathlib; \
		v=pathlib.Path('VERSION').read_text().strip(); \
		p=tomllib.loads(pathlib.Path('pyproject.toml').read_text()); \
		assert v.replace('-','.') == p['project']['version'], f'VERSION={v} vs pyproject={p[\"project\"][\"version\"]}'; \
		print('versions match:', v)"
	@$(MAKE) ci
	@echo "Release readiness: OK"

docs:
	@echo "Documentation rendering is not yet implemented."
