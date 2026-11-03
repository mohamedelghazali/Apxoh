"""Tests for arkhon.policies.exceptions."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from arkhon.core.errors import GovernanceError
from arkhon.policies.exceptions import (
    Exception,
    ExceptionRegistry,
    add_exception,
    load_exceptions,
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
    reg = ExceptionRegistry(exceptions=[
        _exc("EXC-1", "SE-TST-001"),
        _exc("EXC-2", "SE-SEC-001"),
    ])
    active = reg.active_for_rule("SE-TST-001")
    assert len(active) == 1
    assert active[0].exception_id == "EXC-1"


def test_registry_expired_not_returned() -> None:
    reg = ExceptionRegistry(exceptions=[
        _exc("EXC-1", expires_at="2020-01-01T00:00:00Z"),
    ])
    assert reg.active_for_rule("SE-TST-001") == []


def test_registry_all_active() -> None:
    reg = ExceptionRegistry(exceptions=[
        _exc("EXC-1"),
        _exc("EXC-2"),
    ])
    assert len(reg.all_active()) == 2


def test_load_exceptions_missing_file() -> None:
    reg = load_exceptions(Path("/nonexistent.yaml"))
    assert reg.exceptions == []


def test_load_exceptions_from_yaml(tmp_path: Path) -> None:
    p = tmp_path / "registry.yaml"
    p.write_text(yaml.safe_dump({
        "exceptions": [{
            "exception_id": "EXC-0001",
            "rule_id": "SE-TST-001",
            "scope": {"project": "x"},
            "rationale": "r" * 50,
            "owner": "a@b.c",
            "approver": "d@e.f",
            "approved_at": "2026-01-01T00:00:00Z",
            "expires_at": "2030-01-01T00:00:00Z",
            "compensating_control": "c" * 20,
        }],
    }), encoding="utf-8")
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
