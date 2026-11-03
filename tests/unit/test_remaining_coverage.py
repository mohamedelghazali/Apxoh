from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from arkhon.core.constants import language_ids, model_ids, platform_ids, product_ids
from arkhon.core.errors import (
    ConfigError,
    EvidenceError,
    EvidenceStaleError,
    EvidenceTamperedError,
    GovernanceError,
    RuleError,
    RuleValidationError,
)
from arkhon.evidence.integrity import (
    sha256_of,
    verify_artifact,
    verify_bundle,
    verify_freshness,
)
from arkhon.governance.charter_loader import (
    Principle,
    _load_yaml as load_charter_yaml,
    _parse_principles,
    load_charter,
)
from arkhon.language_support.registry import _parse_language, load_registry
from arkhon.policies.exceptions import (
    Exception as PolicyException,
    ExceptionRegistry,
    add_exception,
    load_exceptions,
)
from arkhon.rules.loader import Rule, load_rule_file, load_rules_dir
from arkhon.rules.validator import validate_against_schema, validate_semantics


def test_manifest_derived_identifier_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = SimpleNamespace(
        integrations={
            "integrations": {
                "models": [{"id": "model-a"}],
                "platforms": [{"id": "platform-a"}],
            }
        },
        languages={"supported": [{"id": "python"}]},
        products={"products": [{"id": "cli"}]},
    )
    monkeypatch.setattr("arkhon.core.constants.get_manifest", lambda: fake)
    assert model_ids() == ["model-a"]
    assert platform_ids() == ["platform-a"]
    assert language_ids() == ["python"]
    assert product_ids() == ["cli"]


def test_integrity_rejects_invalid_hash_and_bundle_shapes(tmp_path: Path) -> None:
    artifact = tmp_path / "proof.txt"
    artifact.write_text("proof", encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="invalid SHA-256"):
        verify_artifact(artifact, "XYZ")
    bundle = tmp_path / "bundle.json"
    bundle.write_text("[]", encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="JSON object"):
        verify_bundle(bundle, evidence_root=tmp_path, expected_commit_sha="a" * 40)
    bundle.write_text("{", encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="valid JSON"):
        verify_bundle(bundle, evidence_root=tmp_path, expected_commit_sha="a" * 40)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"commit_sha": "a" * 40, "artifacts": []}, "no artifacts"),
        ({"commit_sha": "a" * 40, "artifacts": [None]}, "malformed artifact entry"),
        (
            {"commit_sha": "a" * 40, "artifacts": [{"path": "", "sha256": "a" * 64}]},
            "malformed artifact path",
        ),
        (
            {"commit_sha": "a" * 40, "artifacts": [{"path": "proof", "sha256": 12}]},
            "malformed artifact hash",
        ),
    ],
)
def test_integrity_rejects_malformed_bundle_artifacts(
    tmp_path: Path, payload: dict, message: str
) -> None:
    bundle = tmp_path / "bundle.json"
    bundle.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match=message):
        verify_bundle(bundle, evidence_root=tmp_path, expected_commit_sha="a" * 40)


def test_freshness_rejects_negative_age_and_accepts_naive_timestamps() -> None:
    with pytest.raises(EvidenceError, match="non-negative"):
        verify_freshness("2026-11-01T00:00:00Z", max_age_hours=-1)
    verify_freshness(
        "2026-11-01T00:00:00",
        max_age_hours=24,
        now_iso="2026-11-01T12:00:00",
    )


def test_charter_yaml_and_markdown_error_paths(tmp_path: Path) -> None:
    with pytest.raises(GovernanceError, match="missing"):
        load_charter_yaml(tmp_path / "missing.yaml")
    bad = tmp_path / "bad.yaml"
    bad.write_text("[", encoding="utf-8")
    with pytest.raises(GovernanceError, match="cannot load"):
        load_charter_yaml(bad)
    bad.write_text("- item", encoding="utf-8")
    with pytest.raises(GovernanceError, match="mapping"):
        load_charter_yaml(bad)
    with pytest.raises(GovernanceError, match="markdown"):
        load_charter(tmp_path)


def test_charter_rejects_invalid_entries_order_and_version(tmp_path: Path) -> None:
    raw = {"principles": [None] * 12}
    with pytest.raises(GovernanceError, match="must be a mapping"):
        _parse_principles(raw)
    raw = {
        "principles": [
            {"number": n, "statement": f"P{n}"} for n in range(1, 13)
        ]
    }
    raw["principles"][0]["statement"] = 7
    with pytest.raises(GovernanceError, match="invalid fields"):
        _parse_principles(raw)
    raw["principles"][0]["statement"] = "P1"
    raw["principles"][0]["number"] = 2
    with pytest.raises(GovernanceError, match="unique and ordered"):
        _parse_principles(raw)
    base = tmp_path / "system" / "charter"
    base.mkdir(parents=True)
    (base / "ENGINEERING_CHARTER.md").write_text("# Charter", encoding="utf-8")
    (base / "PRINCIPLES.yaml").write_text(
        yaml.safe_dump({"version": "", "principles": [
            {"number": n, "statement": f"P{n}"} for n in range(1, 13)
        ]}),
        encoding="utf-8",
    )
    with pytest.raises(GovernanceError, match="version"):
        load_charter(tmp_path)


def test_exception_registry_skips_bad_entries_and_adds_to_empty_mapping(
    tmp_path: Path,
) -> None:
    path = tmp_path / "exceptions.yaml"
    path.write_text(
        yaml.safe_dump({
            "exceptions": [
                "not a mapping",
                {"exception_id": "missing-fields"},
                {
                    "exception_id": "EXC-1",
                    "rule_id": "R-1",
                    "scope": {},
                    "rationale": "reason",
                    "owner": "owner",
                    "approver": "approver",
                    "approved_at": "2026-01-01T00:00:00Z",
                    "expires_at": "2030-01-01T00:00:00Z",
                    "compensating_control": "control",
                },
            ]
        }),
        encoding="utf-8",
    )
    registry = load_exceptions(path)
    assert [item.exception_id for item in registry.exceptions] == ["EXC-1"]
    empty = tmp_path / "empty.yaml"
    empty.write_text("{}", encoding="utf-8")
    exception = PolicyException(
        "EXC-2", "R-2", {}, "reason", "owner", "approver",
        "2026-01-01T00:00:00Z", "2030-01-01T00:00:00Z", "control",
    )
    add_exception(empty, exception)
    assert len(yaml.safe_load(empty.read_text(encoding="utf-8"))["exceptions"]) == 1


def test_exception_naive_expiry_and_registry_filters() -> None:
    exception = PolicyException(
        "EXC-3", "R-3", {}, "reason", "owner", "approver",
        "2026-01-01", "2030-01-01", "control",
    )
    now = datetime(2026, 11, 3, tzinfo=UTC)
    assert exception.is_active(now=now)
    revoked = PolicyException(
        "EXC-4", "R-3", {}, "reason", "owner", "approver",
        "2026-01-01", "2030-01-01", "control", status="revoked",
    )
    registry = ExceptionRegistry([exception, revoked])
    assert registry.active_for_rule("R-3", now=now) == [exception]
    assert registry.all_active(now=now) == [exception]


def _language(language_id: str, extensions: list[str]) -> dict:
    return {
        "id": language_id,
        "detection": {"extensions": extensions, "build_files": [], "lock_files": []},
        "primary_use": ["general"],
        "planned_tools": {"formatters": ["fmt"]},
        "milestone": 1,
    }


def test_language_parser_rejects_invalid_fields() -> None:
    with pytest.raises(ConfigError, match="detection"):
        _parse_language({"id": "x", "detection": []})
    with pytest.raises(ConfigError, match="id"):
        _parse_language({"id": " "})
    with pytest.raises(ConfigError, match="primary_use"):
        _parse_language({"id": "x", "primary_use": "not-a-list"})
    with pytest.raises(ConfigError, match="planned_tools"):
        _parse_language({"id": "x", "planned_tools": []})
    with pytest.raises(ConfigError, match="milestone"):
        _parse_language({"id": "x", "milestone": True})


def test_language_registry_rejects_yaml_duplicates_and_extensions(tmp_path: Path) -> None:
    folder = tmp_path / "languages"
    folder.mkdir()
    path = folder / "registry.yaml"
    path.write_text("[", encoding="utf-8")
    with pytest.raises(ConfigError, match="cannot read"):
        load_registry(tmp_path)
    path.write_text(yaml.safe_dump({"languages": []}), encoding="utf-8")
    with pytest.raises(ConfigError, match="non-empty"):
        load_registry(tmp_path)
    path.write_text(yaml.safe_dump({"languages": [_language("x", [".x"]), _language("x", [".y"])]}),
                    encoding="utf-8")
    with pytest.raises(ConfigError, match="duplicate language"):
        load_registry(tmp_path)
    path.write_text(yaml.safe_dump({"languages": [_language("x", ["x"])]}), encoding="utf-8")
    with pytest.raises(ConfigError, match="invalid extension"):
        load_registry(tmp_path)
    path.write_text(yaml.safe_dump({
        "languages": [_language("x", [".x"]), _language("y", [".x"])]
    }), encoding="utf-8")
    with pytest.raises(ConfigError, match="multiple languages"):
        load_registry(tmp_path)


def test_detector_skips_symlinks_large_files_and_unclassified_files(tmp_path: Path) -> None:
    from arkhon.language_support.detector import detect_languages

    source = tmp_path / "main.py"
    source.write_text("x = 1", encoding="utf-8")
    link = tmp_path / "linked.py"
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip("symlinks are not available on this platform")
    (tmp_path / "README").write_text("no extension", encoding="utf-8")
    huge = tmp_path / "large.py"
    with huge.open("wb") as stream:
        stream.truncate(5 * 1024 * 1024 + 1)
    result = detect_languages(tmp_path)
    assert result.total_files == 2
    assert result.primary == "python"
    with pytest.raises(ValueError):
        detect_languages(tmp_path, max_samples=True)
    with pytest.raises(ValueError):
        detect_languages(tmp_path, max_samples=-1)


def test_rule_loader_handles_non_directory_yaml_errors_and_nonrecursive(
    tmp_path: Path,
) -> None:
    from arkhon.rules.loader import load_rules_dir

    file_path = tmp_path / "file"
    file_path.write_text("x", encoding="utf-8")
    result = load_rules_dir(file_path)
    assert not result.ok
    folder = tmp_path / "rules"
    folder.mkdir()
    (folder / "broken.yaml").write_text("[", encoding="utf-8")
    result = load_rules_dir(folder)
    assert not result.ok
    nested = folder / "nested"
    nested.mkdir()
    nested_rule = nested / "nested.yaml"
    nested_rule.write_text(yaml.safe_dump({
        "id": "SE-REQ-777", "metadata": {"title": "nested"}
    }), encoding="utf-8")
    assert load_rules_dir(folder, recursive=False).rules == []


def test_rule_validator_handles_invalid_schema_and_raw_shapes(tmp_path: Path) -> None:
    rule = Rule(
        "SE-REQ-001",
        Path("rule.yaml"),
        {
            "id": "OTHER-001",
            "metadata": {"domain": "requirements", "enforcement": "blocking",
                         "severity": "high", "status": "active"},
            "verification": [],
            "acceptance": [],
        },
    )
    assert len(validate_semantics(rule)) >= 3
    schema = tmp_path / "schema.json"
    schema.write_text('{"type": "not-a-json-schema-type"}', encoding="utf-8")
    assert validate_against_schema(rule, schema)
    schema.write_text("{", encoding="utf-8")
    assert validate_against_schema(rule, schema)
