"""Unit tests for SecurityAuditTaskDispatcher role isolation and separation of duties."""

from __future__ import annotations

from pathlib import Path

import pytest

from gencode_gov.security_audit.dispatcher import (
    AuditRole,
    SecurityAuditTaskDispatcher,
)


def test_task_dispatcher_assigns_roles_and_enforces_separation_of_duties(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="unsupported execution_mode"):
        SecurityAuditTaskDispatcher(audit_dir=tmp_path, execution_mode="invalid")

    dispatcher = SecurityAuditTaskDispatcher(audit_dir=tmp_path)
    with pytest.raises(ValueError, match="invalid canonical agent_id"):
        dispatcher.assign(
            agent_id="CON",
            role=AuditRole.HUNTER,
            wave=1,
            targets=("unit-1",),
        )
    with pytest.raises(ValueError, match="wave must be >= 1"):
        dispatcher.assign(
            agent_id="hunter-01",
            role=AuditRole.HUNTER,
            wave=0,
            targets=("unit-1",),
        )

    rec = dispatcher.assign(
        agent_id="hunter-01",
        role=AuditRole.HUNTER,
        wave=1,
        targets=("unit-1",),
    )
    assert rec.scratch_dir.is_dir()
    assert rec.artifacts_dir.is_dir()

    dispatcher.assign(
        agent_id="hunter-01",
        role=AuditRole.HUNTER,
        wave=1,
        targets=("unit-1",),
    )
    with pytest.raises(ValueError, match="already owned"):
        dispatcher.assign(
            agent_id="hunter-02",
            role=AuditRole.ATTACK_CLASS_SPECIALIST,
            wave=1,
            targets=("unit-1",),
        )

    with pytest.raises(ValueError, match="invalid canonical agent_id"):
        dispatcher.register_discovery("fp:1", "BAD_UPPER")

    dispatcher.register_discovery("fp:1", "hunter-01")
    with pytest.raises(ValueError, match="separation-of-duties violation"):
        dispatcher.assign(
            agent_id="hunter-01",
            role=AuditRole.INDEPENDENT_VERIFIER,
            wave=1,
            targets=("fp:1",),
        )
    with pytest.raises(ValueError, match="invalid canonical verifier_id"):
        dispatcher.assert_independent_verifier("fp:1", "NUL")
    with pytest.raises(ValueError, match="cannot independently verify"):
        dispatcher.assert_independent_verifier("fp:1", "hunter-01")

    dispatcher.assert_independent_verifier("fp:1", "verifier-01")
    dispatcher.assign(
        agent_id="verifier-01",
        role=AuditRole.INDEPENDENT_VERIFIER,
        wave=1,
        targets=("fp:1",),
    )
    summary = dispatcher.provenance_summary()
    assert summary["execution_mode"] == "single_process_deterministic"
    assert summary["multi_agent_independent_sessions"] is False
    assert summary["assignment_count"] == 3
