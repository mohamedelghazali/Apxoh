"""Unit tests for deterministic security artifact validators and target-neutral reporting."""

from __future__ import annotations

import json
import os
from pathlib import Path

from arkhon.security_audit.coverage import (
    CoverageCheck,
    CoverageLedger,
    CoverageUnit,
    build_canonical_coverage_id,
)
from arkhon.security_audit.findings import (
    DiscoveryProvenance,
    FindingsCollection,
    LocationRef,
    RemediationGuidance,
    SecurityFinding,
    SeverityAssessment,
    TraceStep,
    VerificationProvenance,
    compute_finding_fingerprint,
    finding_id_from_fingerprint,
)
from arkhon.security_audit.reporting import (
    compute_governance_gate_status,
    write_audit_reports,
)
from arkhon.security_audit.sandbox import SandboxCapabilities
from arkhon.security_audit.validators import (
    is_safe_relative_path,
    validate_audit_directory,
    validate_audit_report_data,
    validate_audit_report_file,
    validate_coverage_ledger_data,
    validate_coverage_ledger_file,
    validate_findings_data,
    validate_findings_file,
)

SHA = "c" * 40


def _valid_bundle(audit_dir: Path) -> tuple[CoverageLedger, FindingsCollection]:
    fp = compute_finding_fingerprint(
        component="src/app",
        attack_class="injection-input-handling",
        primary_file="src/app/api.py",
        symbol="run_query",
        invariant_key="dynamic-sql",
    )
    fid = finding_id_from_fingerprint(fp)
    finding = SecurityFinding(
        finding_id=fid,
        fingerprint=fp,
        title="SQL interpolation",
        description="desc",
        attack_class="injection-input-handling",
        component="src/app",
        affected_locations=[LocationRef("src/app/api.py", 10, "run_query")],
        trace=[TraceStep("sink", "src/app/api.py", 10, "run_query", "execute")],
        trust_boundary="external-unauthenticated-to-http",
        entry_point="http-route",
        affected_principal_or_resource="db",
        preconditions=["http request"],
        scenario_summary="interpolated query",
        reproduction_steps=["inspect line 10"],
        security_impact="unauthorized query",
        evidence_refs=["src/app/api.py:10"],
        discovery_provenance=DiscoveryProvenance(
            "hunter-01", "security-hunter", "AUDIT-0010", "2026-11-26T00:00:00Z", "static_ast"
        ),
        verification_provenance=VerificationProvenance(
            "verifier-01",
            "independent-finding-verifier",
            "AUDIT-0010",
            "2026-11-26T00:01:00Z",
            "independent_source_review",
            ("src/app/api.py:10",),
            (),
            ("checked parameterization",),
        ),
        verification_status="confirmed",
        lifecycle_state="confirmed",
        confidence_score="high",
        confidence_reason="verified",
        uncertainty_notes=[],
        severity=SeverityAssessment("high", "r", "critical", "r", "critical"),
        root_cause="unparameterized SQL",
        claimed_root_cause=None,
        remediation=RemediationGuidance(
            "Use parameterized placeholders",
            "bind parameters",
            (("src/app/api.py", "bind query args"),),
        ),
        unresolved_blockers=[],
        validation_plan=None,
        rejection_reason=None,
        related_rules=["SE-SEC-003"],
        related_requirements=[],
        commit_sha=SHA,
        first_seen_run="AUDIT-0010",
        last_seen_run="AUDIT-0010",
        first_seen_commit=SHA,
        first_seen_commit=SHA,
        state_history=[
            {
                "state": "candidate",
                "run_id": "AUDIT-0010",
                "commit_sha": SHA,
                "actor": "hunter-01",
                "reason": "found",
            },
            {
                "state": "confirmed",
                "run_id": "AUDIT-0010",
                "commit_sha": SHA,
                "actor": "verifier-01",
                "reason": "verified",
            },
        ],
    )
    cid = build_canonical_coverage_id(
        entry_point="http-route",
        trust_boundary="external-unauthenticated-to-http",
        component="src/app",
        attack_class="injection-input-handling",
        interface="http-api",
    )
    unit = CoverageUnit(
        coverage_id=cid,
        component="src/app",
        attack_class="injection-input-handling",
        trust_boundary="external-unauthenticated-to-http",
        entry_point="http-route",
        interface="http-api",
        starting_paths=["src/app/api.py"],
        status="examined",
        prior_status="new",
        wave=1,
        investigator_id="hunter-01",
        reviewed_paths=["src/app/api.py"],
        checks=[
            CoverageCheck(
                investigator_id="hunter-01",
                method="source",
                reviewed_paths=("src/app/api.py",),
                invariant="parameterized SQL",
                result="found SQL sink",
                evidence_refs=("src/app/api.py",),
                artifact_path=None,
                timestamp="2026-11-26T00:00:00Z",
            )
        ],
        finding_ids=[fid],
        candidate_fingerprints=[fp],
    )
    ledger = CoverageLedger(
        ledger_id="LEDGER-0010",
        audit_run_id="AUDIT-0010",
        project="demo",
        commit_sha=SHA,
        profile="standard",
        audit_status="completed",
        execution_mode="single_process_deterministic",
        scope_paths=[],
        units=[unit],
    )
    findings = FindingsCollection("AUDIT-0010", SHA, [finding])
    ledger.save(audit_dir / "coverage-ledger.json")
    findings.save(audit_dir / "findings.json")
    return ledger, findings


def test_validators_enforce_file_safety_schema_semantic_and_bundle_rules(
    tmp_path: Path,
) -> None:
    assert is_safe_relative_path("src/arkhon/cli.py") is True
    assert is_safe_relative_path("/etc/passwd") is False
    assert is_safe_relative_path("../up.py") is False
    assert is_safe_relative_path("bad\x07ctrl.py") is False
    assert is_safe_relative_path("con/file.py") is False

    # Missing, malformed, symlink, FIFO, and deep-nested JSON return controlled errors
    assert not validate_coverage_ledger_file(tmp_path / "missing.json").ok

    malformed = tmp_path / "bad.json"
    malformed.write_text("{not-json", encoding="utf-8")
    assert not validate_findings_file(malformed).ok

    sym = tmp_path / "sym.json"
    sym.symlink_to(malformed)
    assert not validate_audit_report_file(sym).ok

    fifo = tmp_path / "fifo.json"
    os.mkfifo(fifo)
    assert not validate_coverage_ledger_file(fifo).ok

    deep = tmp_path / "deep.json"
    nested: object = 1
    for _ in range(70):
        nested = [nested]
    deep.write_text(json.dumps(nested), encoding="utf-8")
    assert not validate_findings_file(deep).ok

    # Valid bundle + reports pass 100%
    aud = tmp_path / "valid_audit"
    aud.mkdir()
    ledger, findings = _valid_bundle(aud)
    caps = SandboxCapabilities(True, True, True, True, None, True)
    written = write_audit_reports(
        audit_dir=aud, ledger=ledger, findings=findings, sandbox_caps=caps, fmt="all"
    )
    assert set(written) == {"json", "markdown", "findings_detail", "needs_validation"}
    assert validate_audit_directory(aud).ok is True
    assert compute_governance_gate_status(ledger, findings) == "FAIL"

    # Semantic error mutations in ledger
    bad_ledger = ledger.to_dict()
    bad_ledger["units"][0]["coverage_id"] = "wrong-id"
    bad_ledger["units"][0]["reviewed_paths"] = ["other.py"]
    bad_ledger["audit_status"] = "completed"
    bad_ledger["completeness"]["examined"] = 99
    assert not validate_coverage_ledger_data(bad_ledger).ok

    # Semantic error mutations in findings (unsorted, self-confirmed, severity on needs_validation)
    bad_findings = findings.to_dict()
    rec0 = bad_findings["records"][0]
    rec0["verification_status"] = "needs_validation"
    assert not validate_findings_data(bad_findings).ok

    # Semantic error in report claiming PASS despite critical confirmed finding
    rep_data = json.loads((aud / "security-audit-report.json").read_text(encoding="utf-8"))
    rep_data["governance_gate_status"] = "PASS"
    assert not validate_audit_report_data(rep_data).ok

    # Cross-artifact mismatch detection
    (aud / "security-audit-report.json").write_text(json.dumps(rep_data), encoding="utf-8")
    assert not validate_audit_directory(aud).ok
