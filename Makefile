.PHONY: install test lint validate clean

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest

lint:
	ruff check src tests
	ruff format --check src tests

validate:
	python scripts/validation/validate_all.py
