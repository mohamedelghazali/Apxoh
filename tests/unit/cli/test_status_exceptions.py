"""Tests for project status and exception inspection CLI commands."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from arkhon.cli import main
from arkhon.evidence.store import EvidenceStore


def _exception(
    exception_id: str,
    expires_at: str,
    status: str = "active",
) -> dict[str, object]:
    return {
        "exception_id": exception_id,
        "rule_id": "SE-TST-001",
        "scope": {"project": "fixture"},
        "rationale": "Approved temporary exception for a controlled test fixture.",
        "owner": "owner@example.test",
        "approver": "approver@example.test",
        "approved_at": "2026-01-01T00:00:00Z",
        "expires_at": expires_at,
        "compensating_control": "Manual review on every change.",
        "status": status,
    }


def test_status_json_empty_project(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["status", str(tmp_path), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["evidence"]["total"] == 0
    assert data["evidence"]["counts"]["PASS"] == 0
    assert data["languages"]["detected"] == []


def test_status_text_summarizes_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    store = EvidenceStore(tmp_path)
    for evidence_id, status, domain in (
        ("EVID-ONE", "PASS", "testing"),
        ("EVID-TWO", "FAIL", "testing"),
        ("EVID-THREE", "BLOCKED", "security"),
        ("EVID-FOUR", "ACCEPTED_RISK", "security"),
    ):
        artifact = tmp_path / f"{evidence_id}.txt"
        artifact.write_text(f"evidence for {evidence_id}", encoding="utf-8")
        store.write(
            domain,
            {
                "evidence_id": evidence_id,
                "source": "arkhon",
                "source_version": "0.1.0",
                "commit_sha": "a" * 40,
                "executed_at": "2026-11-01T00:00:00Z",
                "status": status,
                "artifacts": [
                    {
                        "path": artifact.name,
                        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                    }
                ],
            },
        )
    assert main(["status", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "Evidence records: 4" in output
    assert "PASS: 1" in output
    assert "FAIL: 1" in output
    assert "BLOCKED: 1" in output
    assert "other: 1" in output


def test_status_rejects_missing_project(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["status", str(tmp_path / "missing")]) == 1
    assert "not a directory" in capsys.readouterr().err


def test_status_fails_closed_on_tampered_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    evidence = tmp_path / ".arkhon" / "evidence" / "testing"
    evidence.mkdir(parents=True)
    (evidence / "EVID-INVALID!.json").write_text("{}", encoding="utf-8")
    assert main(["status", str(tmp_path)]) == 1
    assert "integrity check failed" in capsys.readouterr().err


def test_status_reports_invalid_project_declaration(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    declaration = tmp_path / ".arkhon" / "project.yaml"
    declaration.parent.mkdir()
    declaration.write_text("[", encoding="utf-8")
    assert main(["status", str(tmp_path)]) == 1
    assert "could not be computed" in capsys.readouterr().err


def test_exceptions_list_empty_registry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    registry = tmp_path / "empty.yaml"
    assert main(["exceptions", "list", "--registry", str(registry)]) == 0
    assert "No exceptions registered" in capsys.readouterr().out


def test_exceptions_list_json_and_text(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    registry = tmp_path / "registry.yaml"
    registry.write_text(
        yaml.safe_dump(
            {
                "exceptions": [
                    _exception("EXC-ACTIVE", "2030-01-01T00:00:00Z"),
                    _exception("EXC-EXPIRED", "2020-01-01T00:00:00Z"),
                    _exception("EXC-REVOKED", "2030-01-01T00:00:00Z", "revoked"),
                ]
            }
        ),
        encoding="utf-8",
    )
    assert main(["exceptions", "list", "--registry", str(registry), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert [item["status"] for item in data["exceptions"]] == [
        "active", "expired", "revoked"
    ]
    assert data["exceptions"][0]["active"] is True
    assert data["exceptions"][1]["active"] is False
    assert main(["exceptions", "list", "--registry", str(registry)]) == 0
    output = capsys.readouterr().out
    assert "EXC-ACTIVE" in output
    assert "EXPIRED" in output
    assert "REVOKED" in output


def test_exceptions_list_uses_repository_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "system" / "policies" / "exceptions" / "registry.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("version: 1\nexceptions: []\n", encoding="utf-8")
    monkeypatch.setattr("arkhon.cli._repo_root", lambda: tmp_path)
    assert main(["exceptions", "list"]) == 0
    assert "No exceptions registered" in capsys.readouterr().out


def test_exceptions_list_rejects_invalid_yaml(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    registry = tmp_path / "invalid.yaml"
    registry.write_text("exceptions: [", encoding="utf-8")
    assert main(["exceptions", "list", "--registry", str(registry)]) == 1
    assert "cannot load exception registry" in capsys.readouterr().err



def test_exceptions_list_rejects_non_mapping_registry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    registry = tmp_path / "invalid-shape.yaml"
    registry.write_text("- not-a-mapping\n", encoding="utf-8")
    assert main(["exceptions", "list", "--registry", str(registry)]) == 1
    assert "cannot load exception registry" in capsys.readouterr().err


def test_exceptions_list_rejects_non_iterable_exceptions(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    registry = tmp_path / "invalid-exceptions.yaml"
    registry.write_text("exceptions: 42\n", encoding="utf-8")
    assert main(["exceptions", "list", "--registry", str(registry)]) == 1
    assert "cannot load exception registry" in capsys.readouterr().err


def test_status_text_reports_empty_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["status", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "Evidence records: 0" in output
    assert "[INFO] no evidence has been recorded yet" in output
