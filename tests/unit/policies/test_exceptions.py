"""Tests for arkhon.policies.exceptions."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from arkhon.core.errors import GovernanceError
from arkhon.policies.exceptions import (
    Exception,
    ExceptionRegistry,
    add_exception,
    load_exceptions,
    revoke_exception,
)


def _exc(
    exc_id: str = "EXC-0001",
    rule_id: str = "SE-TST-001",
    expires_at: str = "2030-01-01T00:00:00Z",
    status: str = "active",
) -> Exception:
    return Exception(
        exception_id=exc_id,
        rule_id=rule_id,
        scope={"project": "test", "files": ["src/x.py"]},
        rationale="test rationale for exception",
        owner="owner@example.com",
        approver="approver@example.com",
        approved_at="2026-01-01T00:00:00Z",
        expires_at=expires_at,
        compensating_control="manual test weekly",
        status=status,
    )


def test_is_expired_future() -> None:
    e = _exc(expires_at="2030-01-01T00:00:00Z")
    assert not e.is_expired()


def test_is_expired_past() -> None:
    e = _exc(expires_at="2020-01-01T00:00:00Z")
    assert e.is_expired()


def test_is_expired_at_exact_expiry_instant() -> None:
    expiry = datetime(2030, 1, 1, tzinfo=UTC)
    e = _exc(expires_at="2030-01-01T00:00:00Z")
    assert e.is_expired(now=expiry)
    assert not e.is_active(now=expiry)


def test_is_active() -> None:
    e = _exc(expires_at="2030-01-01T00:00:00Z")
    assert e.is_active()


def test_is_not_active_if_expired() -> None:
    e = _exc(expires_at="2020-01-01T00:00:00Z")
    assert not e.is_active()


def test_is_not_active_if_revoked() -> None:
    e = _exc(status="revoked")
    assert not e.is_active()


def test_registry_active_for_rule() -> None:
    reg = ExceptionRegistry(
        exceptions=[
            _exc("EXC-1", "SE-TST-001"),
            _exc("EXC-2", "SE-SEC-001"),
        ]
    )
    active = reg.active_for_rule("SE-TST-001")
    assert len(active) == 1
    assert active[0].exception_id == "EXC-1"


def test_registry_expired_not_returned() -> None:
    reg = ExceptionRegistry(
        exceptions=[
            _exc("EXC-1", expires_at="2020-01-01T00:00:00Z"),
        ]
    )
    assert reg.active_for_rule("SE-TST-001") == []


def test_registry_all_active() -> None:
    reg = ExceptionRegistry(
        exceptions=[
            _exc("EXC-1"),
            _exc("EXC-2"),
        ]
    )
    assert len(reg.all_active()) == 2


def test_load_exceptions_missing_file() -> None:
    reg = load_exceptions(Path("/nonexistent.yaml"))
    assert reg.exceptions == []


def test_load_exceptions_from_yaml(tmp_path: Path) -> None:
    p = tmp_path / "registry.yaml"
    p.write_text(
        yaml.safe_dump(
            {
                "exceptions": [
                    {
                        "exception_id": "EXC-0001",
                        "rule_id": "SE-TST-001",
                        "scope": {"project": "x"},
                        "rationale": "r" * 50,
                        "owner": "a@b.c",
                        "approver": "d@e.f",
                        "approved_at": "2026-01-01T00:00:00Z",
                        "expires_at": "2030-01-01T00:00:00Z",
                        "compensating_control": "c" * 20,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    reg = load_exceptions(p)
    assert len(reg.exceptions) == 1


def test_add_exception_writes(tmp_path: Path) -> None:
    p = tmp_path / "registry.yaml"
    add_exception(p, _exc())
    assert p.is_file()
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert len(data["exceptions"]) == 1


def test_add_duplicate_raises(tmp_path: Path) -> None:
    p = tmp_path / "registry.yaml"
    add_exception(p, _exc("EXC-1"))
    with pytest.raises(GovernanceError, match="already exists"):
        add_exception(p, _exc("EXC-1"))


def test_load_exceptions_skips_malformed_records_and_handles_empty_registry(
    tmp_path: Path,
) -> None:
    path = tmp_path / "registry.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "exceptions": [
                    "not-a-mapping",
                    {"exception_id": "missing-required-fields"},
                    {
                        "exception_id": "EXC-BAD-DATE",
                        "rule_id": "SE-TST-001",
                        "scope": {},
                        "rationale": "rationale",
                        "owner": "owner",
                        "approver": "approver",
                        "approved_at": "not-a-date",
                        "expires_at": "not-a-date",
                        "compensating_control": "control",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    assert load_exceptions(path).exceptions == []
    empty = tmp_path / "empty.yaml"
    empty.write_text("null", encoding="utf-8")
    assert load_exceptions(empty).exceptions == []


def test_add_exception_repairs_missing_exceptions_key(tmp_path: Path) -> None:
    path = tmp_path / "registry.yaml"
    path.write_text("metadata: {}\n", encoding="utf-8")
    add_exception(path, _exc("EXC-REPAIRED"))
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert [item["exception_id"] for item in data["exceptions"]] == ["EXC-REPAIRED"]


def test_revoke_exception_persists_audit_record(tmp_path: Path) -> None:
    path = tmp_path / "registry.yaml"
    add_exception(path, _exc("EXC-REVOKE"))
    revoke_exception(
        path,
        "EXC-REVOKE",
        revoked_by="security@example.com",
        reason="risk no longer accepted",
        revoked_at="2026-11-05T18:30:00Z",
    )

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    item = data["exceptions"][0]
    assert item["status"] == "revoked"
    assert item["revocation"] == {
        "revoked_by": "security@example.com",
        "revoked_at": "2026-11-05T18:30:00Z",
        "reason": "risk no longer accepted",
    }
    assert load_exceptions(path).all_active() == []


def test_revoke_exception_rejects_unknown_or_already_revoked_ids(tmp_path: Path) -> None:
    path = tmp_path / "registry.yaml"
    add_exception(path, _exc("EXC-REVOKE"))

    with pytest.raises(GovernanceError, match="not found"):
        revoke_exception(path, "EXC-MISSING", revoked_by="admin", reason="closed")

    revoke_exception(path, "EXC-REVOKE", revoked_by="admin", reason="closed")
    with pytest.raises(GovernanceError, match="not active"):
        revoke_exception(path, "EXC-REVOKE", revoked_by="admin", reason="again")


@pytest.mark.parametrize(
    ("revoked_by", "reason", "revoked_at", "message"),
    [
        ("", "reason", None, "revoked_by"),
        ("admin", " ", None, "reason"),
        ("admin", "reason", "not-a-date", "timestamp"),
    ],
)
def test_revoke_exception_rejects_invalid_audit_metadata(
    tmp_path: Path,
    revoked_by: str,
    reason: str,
    revoked_at: str | None,
    message: str,
) -> None:
    path = tmp_path / "registry.yaml"
    add_exception(path, _exc("EXC-REVOKE"))
    with pytest.raises(GovernanceError, match=message):
        revoke_exception(
            path,
            "EXC-REVOKE",
            revoked_by=revoked_by,
            reason=reason,
            revoked_at=revoked_at,
        )



def test_revoke_exception_rejects_empty_id(tmp_path: Path) -> None:
    with pytest.raises(GovernanceError, match="exception_id"):
        revoke_exception(tmp_path / "registry.yaml", " ", revoked_by="admin", reason="closed")


def test_revoke_exception_rejects_symlinked_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "registry.yaml"
    path.write_text("exceptions: []\n", encoding="utf-8")
    original = Path.is_symlink

    def is_symlink(candidate: Path) -> bool:
        return True if candidate == path else original(candidate)

    monkeypatch.setattr(Path, "is_symlink", is_symlink)
    with pytest.raises(GovernanceError, match="symlinked"):
        revoke_exception(path, "EXC-1", revoked_by="admin", reason="closed")


def test_revoke_exception_rejects_missing_registry(tmp_path: Path) -> None:
    with pytest.raises(GovernanceError, match="not found"):
        revoke_exception(
            tmp_path / "missing.yaml", "EXC-1", revoked_by="admin", reason="closed"
        )


@pytest.mark.parametrize("contents", ["exceptions: {}\n", "- invalid-root\n", "exceptions: [\n"])
def test_revoke_exception_rejects_invalid_registry_yaml(
    tmp_path: Path, contents: str
) -> None:
    path = tmp_path / "registry.yaml"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(GovernanceError):
        revoke_exception(path, "EXC-1", revoked_by="admin", reason="closed")


def test_revoke_exception_rejects_duplicate_ids(tmp_path: Path) -> None:
    path = tmp_path / "registry.yaml"
    record = {
        "exception_id": "EXC-DUP",
        "rule_id": "SE-TST-001",
        "scope": {},
        "rationale": "test rationale",
        "owner": "owner",
        "approver": "approver",
        "approved_at": "2026-01-01T00:00:00Z",
        "expires_at": "2030-01-01T00:00:00Z",
        "compensating_control": "manual review",
        "status": "active",
    }
    path.write_text(yaml.safe_dump({"exceptions": [record, record]}), encoding="utf-8")
    with pytest.raises(GovernanceError, match="duplicate"):
        revoke_exception(path, "EXC-DUP", revoked_by="admin", reason="closed")


def test_revoke_exception_wraps_read_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "registry.yaml"
    path.write_text("exceptions: []\n", encoding="utf-8")
    original = Path.read_text

    def read_text(candidate: Path, *args: object, **kwargs: object) -> str:
        if candidate == path:
            raise OSError("simulated read failure")
        return original(candidate, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    with pytest.raises(GovernanceError, match="cannot read"):
        revoke_exception(path, "EXC-1", revoked_by="admin", reason="closed")


def test_revoke_exception_cleans_temporary_file_after_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "registry.yaml"
    add_exception(path, _exc("EXC-ATOMIC"))
    original = Path.replace

    def fail_replace(candidate: Path, target: Path) -> Path:
        if candidate.parent == tmp_path and candidate.name.startswith(".registry.yaml."):
            raise OSError("simulated atomic replace failure")
        return original(candidate, target)

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(GovernanceError, match="cannot persist"):
        revoke_exception(path, "EXC-ATOMIC", revoked_by="admin", reason="closed")
    assert not list(tmp_path.glob(".registry.yaml.*.tmp"))
    assert load_exceptions(path).all_active()
