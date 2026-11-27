"""Unit tests for SecurityFinding lifecycle, severity policy, and adversarial verifier."""

from __future__ import annotations

from pathlib import Path

import pytest

from gencode_gov.security_audit.findings import (
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
from gencode_gov.security_audit.sandbox import (
    SandboxCapabilities,
    SandboxExecutor,
)
from gencode_gov.security_audit.verifier import (
    IndependentFindingVerifier,
    verify_findings_collection,
)

SHA = "b" * 40


def _make_candidate(
    rel_file: str,
    line: int,
    *,
    attack_class: str = "injection-input-handling",
    boundary: str = "external-unauthenticated-to-http",
    agent_id: str = "hunter-01",
    claimed: str = "eval called on request input",
) -> SecurityFinding:
    fp = compute_finding_fingerprint(
        component="src/app",
        attack_class=attack_class,
        primary_file=rel_file,
        symbol="handle",
        invariant_key="unsafe-eval",
    )
    return SecurityFinding(
        finding_id=finding_id_from_fingerprint(fp),
        fingerprint=fp,
        title="Candidate issue",
        description="Candidate description",
        attack_class=attack_class,
        component="src/app",
        affected_locations=[LocationRef(file=rel_file, line=line, symbol="handle", end_line=line)],
        trace=[
            TraceStep(
                kind="entrypoint",
                file=rel_file,
                line=1,
                scope="handle",
                description="entry",
            ),
            TraceStep(
                kind="sink",
                file=rel_file,
                line=line,
                scope="handle",
                description="sink",
            ),
        ],
        trust_boundary=boundary,
        entry_point="http-route",
        affected_principal_or_resource="app runtime",
        preconditions=["caller reaches endpoint"],
        scenario_summary=claimed,
        reproduction_steps=["inspect source"],
        security_impact="code execution",
        evidence_refs=[f"{rel_file}:{line}"],
        discovery_provenance=DiscoveryProvenance(
            agent_id=agent_id,
            role="security-hunter",
            run_id="AUDIT-0001",
            timestamp="2026-11-26T00:00:00+00:00",
            method="static_ast",
        ),
        verification_provenance=None,
        verification_status="not_verified",
        lifecycle_state="candidate",
        confidence_score="medium",
        confidence_reason="initial",
        uncertainty_notes=[],
        severity=None,
        root_cause=None,
        claimed_root_cause=claimed,
        remediation=None,
        unresolved_blockers=[],
        validation_plan=None,
        rejection_reason=None,
        related_rules=["SE-SEC-003"],
        related_requirements=["REQ-001"],
        commit_sha=SHA,
        first_seen_run="AUDIT-0001",
        last_seen_run="AUDIT-0001",
        first_seen_commit=SHA,
        last_seen_commit=SHA,
        state_history=[
            {
                "state": "candidate",
                "run_id": "AUDIT-0001",
                "commit_sha": SHA,
                "actor": agent_id,
                "reason": "discovered",
            }
        ],
    )


def test_finding_policy_invariants_severity_bounds_and_deduplication(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="invalid severity level"):
        SeverityAssessment("bogus", "r", "high", "r", "high")
    with pytest.raises(ValueError, match="must not exceed demonstrated impact_score"):
        SeverityAssessment("high", "r", "medium", "r", "critical")

    cand = _make_candidate("src/app/mod.py", 2)
    cand.severity = SeverityAssessment("low", "r", "medium", "r", "medium")
    with pytest.raises(ValueError, match="severity is forbidden"):
        cand.to_dict()

    cand.severity = None
    cand.verification_status = "confirmed"
    with pytest.raises(ValueError, match="require severity, root_cause, and remediation"):
        cand.to_dict()

    cand.severity = SeverityAssessment("medium", "r", "high", "r", "high")
    cand.root_cause = "confirmed cause"
    cand.remediation = RemediationGuidance("fix", "inv", (("src/app/mod.py", "patch"),))
    with pytest.raises(ValueError, match="require independent verification_provenance"):
        cand.to_dict()

    cand.verification_provenance = VerificationProvenance(
        verifier_id="hunter-01",
        role="independent-finding-verifier",
        run_id="AUDIT-0001",
        timestamp="2026-11-26T00:00:00+00:00",
        method="independent_source_review",
        supporting_evidence=("ok",),
        contradictory_evidence=(),
        disprove_attempts=("checked",),
    )
    with pytest.raises(ValueError, match="never self-confirm"):
        cand.to_dict()

    cand.verification_provenance = VerificationProvenance(
        verifier_id="verifier-01",
        role="independent-finding-verifier",
        run_id="AUDIT-0001",
        timestamp="2026-11-26T00:00:00+00:00",
        method="independent_source_review",
        supporting_evidence=("ok",),
        contradictory_evidence=(),
        disprove_attempts=("checked",),
    )
    cand.transition_to("confirmed", run_id="AUDIT-0001", commit_sha=SHA, actor="v1", reason="ok")
    with pytest.raises(ValueError, match="invalid finding state transition"):
        cand.transition_to("reopened", run_id="AUDIT-0001", commit_sha=SHA, actor="v1", reason="no")

    dup = SecurityFinding.from_dict(cand.to_dict())
    dup.trace = dup.trace[:1]
    coll = FindingsCollection(audit_run_id="AUDIT-0001", commit_sha=SHA, records=[dup, cand])
    saved = coll.save(tmp_path / "findings.json")
    loaded = FindingsCollection.load(saved)
    assert len(loaded.records) == 1
    assert len(loaded.records[0].trace) == 2


def test_independent_verifier_confirms_rejects_needs_validation_and_blocks(
    tmp_path: Path,
) -> None:
    proj = tmp_path / "proj"
    (proj / "src" / "app").mkdir(parents=True)
    (proj / "tests").mkdir(parents=True)
    (proj / "src" / "app" / "vuln.py").write_text(
        "def handle(x):\n    return eval(x)\n", encoding="utf-8"
    )
    (proj / "src" / "app" / "safe_yaml.py").write_text(
        "import yaml\ndef parse(s):\n    return yaml.safe_load(s)\n", encoding="utf-8"
    )
    (proj / "src" / "app" / "safe_sub.py").write_text(
        "import subprocess\ndef run():\n    subprocess.run(['true'])\n", encoding="utf-8"
    )
    (proj / "tests" / "test_sample.py").write_text("eval('1')\n", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid canonical verifier_id"):
        IndependentFindingVerifier(proj, verifier_id="BAD_ID")

    verifier = IndependentFindingVerifier(proj, verifier_id="verifier-01")

    # Self-verification rejected immediately
    self_cand = _make_candidate("src/app/vuln.py", 2, agent_id="verifier-01")
    with pytest.raises(ValueError, match="separation-of-duties"):
        verifier.verify_candidate(self_cand, run_id="AUDIT-0001", commit_sha=SHA)

    # Unsafe path, traversal outside root, missing file, out-of-range line, test fixture -> rejected
    bad_path = _make_candidate("../escape.py", 1)
    res_bad_path = verifier.verify_candidate(bad_path, run_id="AUDIT-0001", commit_sha=SHA)
    assert res_bad_path.verification_status == "rejected"

    ext_link = proj / "src" / "app" / "link.py"
    ext_link.symlink_to("/etc/hosts")
    sym_cand = _make_candidate("src/app/link.py", 1)
    res_sym_cand = verifier.verify_candidate(sym_cand, run_id="AUDIT-0001", commit_sha=SHA)
    assert res_sym_cand.verification_status == "rejected"

    missing = _make_candidate("src/app/missing.py", 1)
    res_missing = verifier.verify_candidate(missing, run_id="AUDIT-0001", commit_sha=SHA)
    assert res_missing.verification_status == "rejected"

    bad_line = _make_candidate("src/app/vuln.py", 99)
    res_bad_line = verifier.verify_candidate(bad_line, run_id="AUDIT-0001", commit_sha=SHA)
    assert res_bad_line.verification_status == "rejected"

    test_cand = _make_candidate("tests/test_sample.py", 1)
    res_test_cand = verifier.verify_candidate(test_cand, run_id="AUDIT-0001", commit_sha=SHA)
    assert res_test_cand.verification_status == "rejected"

    # Mitigated YAML & shell=False subprocess -> disproved / rejected
    yaml_cand = _make_candidate("src/app/safe_yaml.py", 3, claimed="yaml load")
    res_yaml_cand = verifier.verify_candidate(yaml_cand, run_id="AUDIT-0001", commit_sha=SHA)
    assert res_yaml_cand.verification_status == "rejected"

    sub_cand = _make_candidate("src/app/safe_sub.py", 3, claimed="subprocess")
    res_sub_cand = verifier.verify_candidate(sub_cand, run_id="AUDIT-0001", commit_sha=SHA)
    assert res_sub_cand.verification_status == "rejected"

    # Deployment-dependent attack class -> needs_validation without severity
    cloud_cand = _make_candidate(
        "src/app/vuln.py",
        2,
        attack_class="cloud-deployment-security",
        boundary="internal",
    )
    nv_res = verifier.verify_candidate(cloud_cand, run_id="AUDIT-0001", commit_sha=SHA)
    assert nv_res.verification_status == "needs_validation"
    assert nv_res.severity is None

    # Severity calibration across high/medium/low tiers + Phase 5 record verification
    for cls_id in (
        "authn-authz-boundaries",
        "cryptographic-implementation",
        "mobile-application-security",
    ):
        c_item = _make_candidate("src/app/vuln.py", 2, attack_class=cls_id)
        if cls_id == "mobile-application-security":
            c_item.evidence_refs.append("deployment_verified")
        res_item = verifier.verify_candidate(c_item, run_id="AUDIT-0001", commit_sha=SHA)
        assert res_item.verification_status == "confirmed"
        assert res_item.severity is not None

    # Sandbox command branch: without sandbox -> needs_validation; blocked sandbox -> blocked;
    # non-zero exit -> rejected; zero exit -> confirmed
    sb_no_exec = _make_candidate("src/app/vuln.py", 2)
    assert (
        verifier.verify_candidate(
            sb_no_exec,
            run_id="AUDIT-0001",
            commit_sha=SHA,
            sandbox_command=["/bin/true"],
        ).verification_status
        == "needs_validation"
    )

    blocked_caps = SandboxCapabilities(True, True, True, True, None, False)
    blocked_sb = SandboxExecutor(tmp_path / "aud_blk", capabilities=blocked_caps)
    v_blk = IndependentFindingVerifier(proj, verifier_id="verifier-02", sandbox=blocked_sb)
    assert (
        v_blk.verify_candidate(
            _make_candidate("src/app/vuln.py", 2),
            run_id="AUDIT-0001",
            commit_sha=SHA,
            sandbox_command=["/bin/true"],
        ).verification_status
        == "blocked"
    )

    mock_ok_sb = SandboxExecutor(
        tmp_path / "aud_mock_ok",
        capabilities=SandboxCapabilities(True, True, True, True, "/bin/echo", False),
    )
    v_mock_ok = IndependentFindingVerifier(proj, verifier_id="verifier-04", sandbox=mock_ok_sb)
    assert (
        v_mock_ok.verify_candidate(
            _make_candidate("src/app/vuln.py", 2),
            run_id="AUDIT-0001",
            commit_sha=SHA,
            sandbox_command=["ok"],
        ).verification_status
        == "confirmed"
    )
    mock_fail_sb = SandboxExecutor(
        tmp_path / "aud_mock_fail",
        capabilities=SandboxCapabilities(True, True, True, True, "/bin/false", False),
    )
    v_mock_fail = IndependentFindingVerifier(proj, verifier_id="verifier-05", sandbox=mock_fail_sb)
    assert (
        v_mock_fail.verify_candidate(
            _make_candidate("src/app/vuln.py", 2),
            run_id="AUDIT-0001",
            commit_sha=SHA,
            sandbox_command=["fail"],
        ).verification_status
        == "rejected"
    )

    live_sb = SandboxExecutor(tmp_path / "aud_live")
    if (
        live_sb.capabilities.can_enforce_full_sandbox
        and live_sb.run_bounded(agent_id="probe-live", argv=["/bin/true"], source_root=proj).status
        == "PASS"
    ):
        v_live = IndependentFindingVerifier(proj, verifier_id="verifier-03", sandbox=live_sb)
        assert (
            v_live.verify_candidate(
                _make_candidate("src/app/vuln.py", 2),
                run_id="AUDIT-0001",
                commit_sha=SHA,
                sandbox_command=["/bin/false"],
            ).verification_status
            == "rejected"
        )
        assert (
            v_live.verify_candidate(
                _make_candidate("src/app/vuln.py", 2),
                run_id="AUDIT-0001",
                commit_sha=SHA,
                sandbox_command=["/bin/true"],
            ).verification_status
            == "confirmed"
        )

    # Collection verification + Phase 5 record drift checks
    coll = FindingsCollection(
        audit_run_id="AUDIT-0001",
        commit_sha=SHA,
        records=[_make_candidate("src/app/vuln.py", 2)],
    )
    verified_coll = verify_findings_collection(coll, project_root=proj)
    rec = verified_coll.records[0]
    assert rec.verification_status == "confirmed"

    with pytest.raises(ValueError, match="invalid record_verifier_id"):
        verifier.verify_record_integrity(
            rec, record_verifier_id="BAD", run_id="AUDIT-0001", commit_sha=SHA
        )
    with pytest.raises(ValueError, match="must be distinct"):
        verifier.verify_record_integrity(
            rec,
            record_verifier_id="independent-verifier-01",
            run_id="AUDIT-0001",
            commit_sha=SHA,
        )

    # Drift line out of bounds -> downgraded to needs_validation
    rec.trace[1] = TraceStep("sink", "src/app/vuln.py", 500, "handle", "drifted")
    drifted = verifier.verify_record_integrity(
        rec, record_verifier_id="record-v2", run_id="AUDIT-0001", commit_sha=SHA
    )
    assert drifted.verification_status == "needs_validation"

    # Missing trace file -> downgraded to needs_validation
    drifted.trace[0] = TraceStep("entrypoint", "src/app/gone.py", 1, "handle", "gone")
    drifted2 = verifier.verify_record_integrity(
        drifted, record_verifier_id="record-v3", run_id="AUDIT-0001", commit_sha=SHA
    )
    assert drifted2.verification_status == "needs_validation"
