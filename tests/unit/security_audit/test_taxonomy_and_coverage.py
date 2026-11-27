"""Unit tests for the 19-class taxonomy and persistent Security Coverage Ledger."""

from __future__ import annotations

from pathlib import Path

import pytest

from gencode_gov.security_audit.coverage import (
    CoverageCheck,
    CoverageLedger,
    CoverageUnit,
    build_canonical_coverage_id,
    compare_coverage_ledgers,
)
from gencode_gov.security_audit.taxonomy import (
    DEFAULT_TAXONOMY,
    AttackClassDefinition,
    AttackClassRegistry,
)


def test_taxonomy_covers_all_19_classes_and_supports_custom_registration() -> None:
    assert len(DEFAULT_TAXONOMY) == 19
    all_defs = DEFAULT_TAXONOMY.all()
    assert len(all_defs) == 19
    assert DEFAULT_TAXONOMY.get("ai-llm-security") is not None
    assert DEFAULT_TAXONOMY.require("injection-input-handling").related_rules
    assert "web-protocol-security" in DEFAULT_TAXONOMY.as_mapping()

    with pytest.raises(KeyError):
        DEFAULT_TAXONOMY.require("nonexistent-class")

    custom_reg = AttackClassRegistry(all_defs)
    extra = AttackClassDefinition(
        id="custom-hardware-boundary",
        name="Custom Hardware Boundary",
        domain_group="hardware",
        summary="Custom domain test class.",
        related_rules=("SE-SEC-003",),
        entry_indicators=("ioctl",),
        sink_indicators=("dma",),
        defensive_invariants=("Validate DMA bounds.",),
        investigation_steps=("Inspect ioctl handlers.",),
        verification_hooks=("dma-check",),
    )
    custom_reg.register(extra)
    assert len(custom_reg) == 20
    with pytest.raises(ValueError, match="duplicate"):
        custom_reg.register(extra)
    with pytest.raises(ValueError, match="invalid or duplicate"):
        AttackClassRegistry((extra, extra))


def test_coverage_ledger_canonical_ids_reassignment_completeness_and_comparison(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        build_canonical_coverage_id(
            entry_point="   ",
            trust_boundary="b",
            component="c",
            attack_class="ai-llm-security",
        )

    cid1 = build_canonical_coverage_id(
        entry_point="http route",
        trust_boundary="ext->app",
        component="src/app",
        attack_class="injection-input-handling",
        interface="http-api",
        lifecycle="runtime",
    )
    assert "http%20route" in cid1
    assert cid1.endswith("::runtime")

    u1 = CoverageUnit(
        coverage_id=cid1,
        component="src/app",
        attack_class="injection-input-handling",
        trust_boundary="ext->app",
        entry_point="http route",
        interface="http-api",
        starting_paths=["src/app/api.py"],
        lifecycle="runtime",
    )
    # Planned units cannot be archived for reassignment and NEVER count as complete
    with pytest.raises(ValueError, match="only owned terminal"):
        u1.reassign("cannot reassign unowned planned unit")

    sha = "a" * 40
    ledger = CoverageLedger(
        ledger_id="LEDGER-0001",
        audit_run_id="AUDIT-0001",
        project="demo",
        commit_sha=sha,
        profile="deep",
        audit_status="initiated",
        execution_mode="single_process_deterministic",
        scope_paths=[],
        units=[u1],
    )
    comp_planned = ledger.compute_completeness()
    assert comp_planned["planned"] == 1
    assert comp_planned["examined"] == 0
    assert comp_planned["is_complete"] is False
    assert len(ledger.detect_gaps()) == 1

    # Examine u1, then archive wave 1 and reassign to wave 2
    u1.status = "partially_examined"
    u1.investigator_id = "hunter-01"
    u1.reviewed_paths = ["src/app/api.py"]
    u1.limitations = ["Dynamic macro unresolved"]
    u1.checks = [
        CoverageCheck(
            investigator_id="hunter-01",
            method="source",
            reviewed_paths=("src/app/api.py",),
            invariant="parameterize SQL",
            result="partial review",
            evidence_refs=("src/app/api.py",),
            artifact_path=None,
            timestamp="2026-11-26T00:00:00+00:00",
        )
    ]
    assert ledger.detect_gaps()[0]["reason"] == "Dynamic macro unresolved"
    u1.reassign("Wave 2 deep follow-up")
    assert u1.wave == 2
    assert u1.status == "planned"
    assert u1.investigator_id is None
    assert len(u1.attempts) == 1

    # Complete wave 2 with fresh investigator
    u1.status = "examined"
    u1.investigator_id = "hunter-02"
    u1.reviewed_paths = ["src/app/api.py"]
    u1.checks = [
        CoverageCheck(
            investigator_id="hunter-02",
            method="source",
            reviewed_paths=("src/app/api.py",),
            invariant="parameterize SQL",
            result="verified clean",
            evidence_refs=("src/app/api.py",),
            artifact_path=None,
            timestamp="2026-11-26T00:05:00+00:00",
        )
    ]
    ledger.audit_status = "completed"
    out_file = ledger.save(tmp_path / "coverage-ledger.json")
    reloaded = CoverageLedger.load(out_file)
    assert reloaded.compute_completeness()["is_complete"] is True
    assert reloaded.detect_gaps() == []

    # Invalid status raises ValueError
    bad_unit = CoverageUnit(
        coverage_id="a::b::c::d::e",
        component="c",
        attack_class="d",
        trust_boundary="b",
        entry_point="a",
        interface="e",
        starting_paths=["x.py"],
        status="bogus",
    )
    bad_ledger = CoverageLedger(
        ledger_id="LEDGER-BAD",
        audit_run_id="AUDIT-BAD",
        project="demo",
        commit_sha=sha,
        profile="standard",
        audit_status="initiated",
        execution_mode="single_process_deterministic",
        scope_paths=[],
        units=[bad_unit],
    )
    with pytest.raises(ValueError, match="invalid unit status"):
        bad_ledger.compute_completeness()

    # Cross-run ledger comparison
    prior_ledger = CoverageLedger.from_dict(reloaded.to_dict())
    prior_ledger.units[0].status = "planned"
    delta = compare_coverage_ledgers(prior_ledger, reloaded)
    assert len(delta["status_transitions"]) == 1
    assert delta["status_transitions"][0]["from_status"] == "planned"
    assert delta["status_transitions"][0]["to_status"] == "examined"
