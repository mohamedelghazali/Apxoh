"""Tests for arkhon.config."""
from __future__ import annotations

from pathlib import Path

import pytest

from arkhon.config import Manifest, find_repo_root, get_manifest, load_manifest
from arkhon.core.errors import ManifestError

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_find_repo_root_from_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APXOH_ROOT", str(tmp_path))
    (tmp_path / "manifest").mkdir()
    (tmp_path / "manifest" / "index.yaml").write_text("x: 1\\n", encoding="utf-8")
    assert find_repo_root() == tmp_path


def test_find_repo_root_from_file() -> None:
    root = find_repo_root()
    assert (root / "manifest" / "index.yaml").is_file()


def test_load_manifest_returns_all_sections() -> None:
    manifest = load_manifest()
    assert isinstance(manifest, Manifest)
    assert manifest.name == "Apxoh"
    assert manifest.identifier == "arkhon"
    assert manifest.version == "0.1.0-dev.1"


def test_manifest_has_three_products() -> None:
    products = load_manifest().products["products"]
    assert len(products) == 3
    assert {item["id"] for item in products} == {
        "arkhon-core", "arkhon-agent-governance", "arkhon-assurance"
    }


def test_manifest_has_eight_models() -> None:
    assert len(load_manifest().integrations["integrations"]["models"]) == 8


def test_manifest_has_nine_languages() -> None:
    assert len(load_manifest().languages["supported"]) == 9


def test_manifest_has_tsar_security_authority() -> None:
    security = load_manifest().integrations["integrations"]["security"]
    assert len(security) == 1
    assert security[0]["id"] == "tsar"


def test_manifest_founding_decisions() -> None:
    decisions = load_manifest().system["founding_decisions"]
    assert decisions["relation_to_tsar"] == "separate"
    assert decisions["scope"] == "universal"
    assert decisions["engine"] == "hybrid"
    assert decisions["repository_language"] == "english-only"
    assert decisions["ai_provider_required_for_core"] is False


def test_manifest_to_dict() -> None:
    assert set(load_manifest().to_dict()) == {
        "index", "system", "products", "integrations", "languages", "standards", "compatibility"
    }


def test_load_manifest_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(ManifestError, match="missing"):
        load_manifest(tmp_path / "nope")


def test_get_manifest_is_cached() -> None:
    assert get_manifest() is get_manifest()
