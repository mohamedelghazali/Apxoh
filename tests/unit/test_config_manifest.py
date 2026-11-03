from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from arkhon.config import Manifest, _load_yaml, find_repo_root, get_manifest, load_manifest
from arkhon.core.errors import ManifestError


def _manifest_tree(root: Path) -> None:
    base = root / "manifest"
    base.mkdir(parents=True)
    names = ("system", "products", "integrations", "languages", "standards", "compatibility")
    refs = {name: f"{name}.yaml" for name in names}
    (base / "index.yaml").write_text(yaml.safe_dump({"files": refs}), encoding="utf-8")
    for name in names:
        value = {"system": {"name": "Apxoh", "identifier": "arkhon", "version": "1.0.0"}}
        (base / f"{name}.yaml").write_text(yaml.safe_dump(value), encoding="utf-8")


def test_manifest_load_and_properties(tmp_path: Path) -> None:
    _manifest_tree(tmp_path)
    manifest = load_manifest(tmp_path)
    assert manifest.name == "Apxoh"
    assert manifest.identifier == "arkhon"
    assert manifest.version == "1.0.0"
    assert set(manifest.to_dict()) == {
        "index",
        "system",
        "products",
        "integrations",
        "languages",
        "standards",
        "compatibility",
    }


def test_manifest_missing_and_invalid_files(tmp_path: Path) -> None:
    with pytest.raises(ManifestError, match="missing"):
        _load_yaml(tmp_path / "missing.yaml")
    path = tmp_path / "empty.yaml"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ManifestError, match="empty"):
        _load_yaml(path)
    path.write_text("- one\n", encoding="utf-8")
    with pytest.raises(ManifestError, match="mapping"):
        _load_yaml(path)
    path.write_text("[", encoding="utf-8")
    with pytest.raises(ManifestError, match="valid YAML"):
        _load_yaml(path)


@pytest.mark.parametrize(
    ("index", "message"),
    [
        ({}, "files"),
        ({"files": {"system": "system.yaml"}}, "missing references"),
        (
            {
                "files": {
                    "system": "",
                    "products": "p.yaml",
                    "integrations": "i.yaml",
                    "languages": "l.yaml",
                    "standards": "s.yaml",
                    "compatibility": "c.yaml",
                }
            },
            "non-empty string",
        ),
        (
            {
                "files": {
                    "system": "../escape.yaml",
                    "products": "p.yaml",
                    "integrations": "i.yaml",
                    "languages": "l.yaml",
                    "standards": "s.yaml",
                    "compatibility": "c.yaml",
                }
            },
            "escapes manifest",
        ),
    ],
)
def test_manifest_rejects_bad_index(tmp_path: Path, index: dict, message: str) -> None:
    base = tmp_path / "manifest"
    base.mkdir()
    (base / "index.yaml").write_text(yaml.safe_dump(index), encoding="utf-8")
    with pytest.raises(ManifestError, match=message):
        load_manifest(tmp_path)


def test_manifest_rejects_non_string_reference(tmp_path: Path) -> None:
    _manifest_tree(tmp_path)
    path = tmp_path / "manifest" / "index.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["files"]["system"] = 12
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ManifestError, match="non-empty string"):
        load_manifest(tmp_path)


def test_manifest_properties_report_missing_values() -> None:
    empty = {}
    manifest = Manifest(empty, empty, empty, empty, empty, empty, empty)
    for property_name in ("name", "identifier", "version"):
        with pytest.raises(ManifestError):
            getattr(manifest, property_name)


def test_find_repo_root_environment_and_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _manifest_tree(tmp_path)
    monkeypatch.setenv("APXOH_ROOT", str(tmp_path))
    assert find_repo_root() == tmp_path.resolve()
    monkeypatch.setenv("APXOH_ROOT", str(tmp_path / "invalid"))
    with pytest.raises(ManifestError, match="APXOH_ROOT"):
        find_repo_root()
    monkeypatch.delenv("APXOH_ROOT")
    assert (find_repo_root() / "manifest" / "index.yaml").is_file()


def test_get_manifest_uses_process_cache() -> None:
    get_manifest.cache_clear()
    first = get_manifest()
    second = get_manifest()
    assert first is second
    get_manifest.cache_clear()
