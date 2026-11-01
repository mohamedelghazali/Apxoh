"""Structural tests for every JSON Schema in schemas/."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMAS_DIR = REPO_ROOT / "schemas"
EXPECTED_SCHEMAS = {
    "rule.schema.json", "evidence.schema.json", "finding.schema.json",
    "assessment.schema.json", "exception.schema.json", "report.schema.json",
    "project.schema.json", "state.schema.json", "integration-contract.schema.json",
}


def _all_schema_files() -> list[Path]:
    return sorted(SCHEMAS_DIR.glob("*.json")) if SCHEMAS_DIR.is_dir() else []


@pytest.mark.parametrize("path", _all_schema_files(), ids=lambda p: p.name)
def test_schema_is_valid_json(path: Path) -> None:
    with path.open(encoding="utf-8") as fh:
        json.load(fh)


@pytest.mark.parametrize("path", _all_schema_files(), ids=lambda p: p.name)
def test_schema_is_valid_jsonschema(path: Path) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    with path.open(encoding="utf-8") as fh:
        jsonschema.Draft202012Validator.check_schema(json.load(fh))


@pytest.mark.parametrize("path", _all_schema_files(), ids=lambda p: p.name)
def test_schema_has_id(path: Path) -> None:
    with path.open(encoding="utf-8") as fh:
        schema = json.load(fh)
    assert schema.get("$id"), f"{path.name} missing $id"
    assert schema.get("$schema"), f"{path.name} missing $schema"


def test_all_expected_schemas_present() -> None:
    actual = {p.name for p in _all_schema_files()}
    assert not (EXPECTED_SCHEMAS - actual), f"missing schemas: {EXPECTED_SCHEMAS - actual}"


def test_schema_ids_are_unique() -> None:
    ids: dict[str, str] = {}
    for path in _all_schema_files():
        schema = json.loads(path.read_text(encoding="utf-8"))
        sid = schema["$id"]
        assert sid not in ids, f"duplicate $id '{sid}' in {path.name} and {ids[sid]}"
        ids[sid] = path.name


def test_manifest_compatibility_lists_all_schemas() -> None:
    compat = REPO_ROOT / "manifest" / "compatibility.yaml"
    if not compat.is_file():
        pytest.skip("compatibility.yaml missing")
    data = yaml.safe_load(compat.read_text(encoding="utf-8"))
    declared = {item["path"] for item in data.get("schemas", [])}
    actual = {str(path.relative_to(REPO_ROOT)) for path in _all_schema_files()}
    assert actual == declared, f"manifest/compatibility.yaml out of sync: declared={declared} actual={actual}"
