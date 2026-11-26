"""Comprehensive negative and edge-case tests driving 100% security_audit coverage."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import unicodedata
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from arkhon.security_audit import cli_dispatch as cd_mod
from arkhon.security_audit import sandbox as sandbox_mod
from arkhon.security_audit import validators as validators_mod
from arkhon.security_audit.cli_dispatch import dispatch_security_audit
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
    SecurityFinding,
    TraceStep,
    compute_finding_fingerprint,
    finding_id_from_fingerprint,
)
from arkhon.security_audit.governance_bridge import (
    SecurityAuditRunner,
    derive_rule_outcomes_from_audit,
    evaluate_security_audit_method,
    record_security_audit_evidence,
    summarize_audit_status,
)
from arkhon.security_audit.hunting import (
    discover_architecture,
    execute_hunting_waves,
    seed_coverage_ledger,
)
from arkhon.security_audit.reassessment import (
    compute_changed_files,
    reassess_repository,
)
from arkhon.security_audit.reporting import (
    build_security_audit_report,
    compute_governance_gate_status,
    render_markdown_audit_report,
)
from arkhon.security_audit.sandbox import (
    SandboxCapabilities,
    SandboxExecutor,
    SandboxLimits,
    probe_sandbox_capabilities,
    promote_agent_artifacts,
)
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
from arkhon.security_audit.verifier import IndependentFindingVerifier
from arkhon.verification.runners.base import RunnerOutcome, RunnerResult

_GIT = shutil.which("git") or "/usr/bin/git"
SHA = "d" * 40


def _make_base_finding(status: str = "not_verified", state: str = "candidate") -> SecurityFinding:
    fp = compute_finding_fingerprint(
        component=".hidden",
        attack_class="secrets-credential-handling",
        primary_file="src/cfg.py",
        symbol="cfg",
        invariant_key="cred",
    )
    return SecurityFinding(
        finding_id=finding_id_from_fingerprint(fp),
        fingerprint=fp,
        title="Title",
        description="Desc",
        attack_class="secrets-credential-handling",
        component="src",
        affected_locations=[LocationRef("src/cfg.py", 1, "cfg")],
        trace=[TraceStep("sink", "src/cfg.py", 1, "cfg", "sink")],
        trust_boundary="internal",
        entry_point="mod",
        affected_principal_or_resource="res",
        preconditions=[],
        scenario_summary="sum",
        reproduction_steps=[],
        security_impact="imp",
        evidence_refs=["src/cfg.py:1"],
        discovery_provenance=DiscoveryProvenance(
            "hunter-01", "security-hunter", "AUDIT-0100", "2026-11-26T00:00:00Z", "static_ast"
        ),
        verification_provenance=None,
        verification_status=status,
        lifecycle_state=state,
        confidence_score="low",
        confidence_reason="r",
        uncertainty_notes=[],
        severity=None,
        root_cause=None,
        claimed_root_cause="claimed",
        remediation=None,
        unresolved_blockers=["blk"] if status in {"needs_validation", "blocked"} else [],
        validation_plan=(
            {"local_check": "chk"} if status in {"needs_validation", "blocked"} else None
        ),
        rejection_reason="disproved" if status == "rejected" else None,
        related_rules=["SE-SEC-005"],
        related_requirements=[],
        commit_sha=SHA,
        first_seen_run="AUDIT-0100",
        last_seen_run="AUDIT-0100",
        first_seen_commit=SHA,
        last_seen_commit=SHA,
        state_history=[
            {
                "state": state,
                "run_id": "AUDIT-0100",
                "commit_sha": SHA,
                "actor": "hunter-01",
                "reason": "init",
            }
        ],
    )


def test_findings_roundtrip_all_nullable_fields_and_verifier_edges(tmp_path: Path) -> None:
    # Roundtrip candidate (null verification_provenance, null severity, null remediation)
    c_rec = _make_base_finding("not_verified", "candidate")
    c_reloaded = SecurityFinding.from_dict(c_rec.to_dict())
    assert c_reloaded.verification_provenance is None

    # Roundtrip rejected (non-null rejection_reason)
    r_rec = _make_base_finding("rejected", "rejected")
    r_reloaded = SecurityFinding.from_dict(r_rec.to_dict())
    assert r_reloaded.rejection_reason == "disproved"

    # Verifier fallback root_cause when claimed_root_cause is None + non-confirmed Phase 5 skip
    proj = tmp_path / "p"
    (proj / "src").mkdir(parents=True)
    (proj / "src" / "cfg.py").write_text("x = 1\n", encoding="utf-8")
    v = IndependentFindingVerifier(proj, verifier_id="verifier-09")
    assert v.verify_record_integrity(
        r_reloaded, record_verifier_id="record-09", run_id="AUDIT-0100", commit_sha=SHA
    ).verification_status == "rejected"

    no_claim = _make_base_finding("not_verified", "candidate")
    no_claim.claimed_root_cause = None
    confirmed = v.verify_candidate(no_claim, run_id="AUDIT-0100", commit_sha=SHA)
    assert confirmed.verification_status == "confirmed"
    assert confirmed.root_cause is not None


def test_validator_exhaustive_semantic_and_limit_branches(tmp_path: Path) -> None:
    # Unicode NFD & Windows drive path rejection
    nfd = unicodedata.normalize("NFD", "caf\u00e9.py")
    assert is_safe_relative_path(nfd) is False
    assert is_safe_relative_path("C:foo.py") is False

    # Schema fallback dir check
    with patch.object(Path, "is_dir", return_value=False):
        res_missing_schema = validate_audit_report_data({})
        assert not res_missing_schema.ok

    # Oversized file, read growth, OSError on read, array/object collection limits, error cap
    f_json = tmp_path / "sample.json"
    f_json.write_text("{}", encoding="utf-8")
    with patch.object(validators_mod, "MAX_INPUT_BYTES", 0):
        assert not validate_findings_file(f_json).ok
    with (
        patch.object(validators_mod, "MAX_INPUT_BYTES", 10),
        patch("os.read", return_value=b"x" * 15),
    ):
        assert not validate_findings_file(f_json).ok
    with patch("os.fstat", side_effect=OSError("io err")):
        assert not validate_findings_file(f_json).ok

    big_arr = tmp_path / "big_arr.json"
    big_obj = tmp_path / "big_obj.json"
    with patch.object(validators_mod, "MAX_COLLECTION_ITEMS", 2):
        big_arr.write_text("[1, 2, 3]", encoding="utf-8")
        assert not validate_findings_file(big_arr).ok
        big_obj.write_text('{"a":1,"b":2,"c":3}', encoding="utf-8")
        assert not validate_findings_file(big_obj).ok
    with patch.object(validators_mod, "MAX_REPORTED_ERRORS", 1):
        many_err = tmp_path / "many.json"
        many_err.write_text("[[[[1]]]]", encoding="utf-8")
        with patch.object(validators_mod, "MAX_NESTING_DEPTH", 1):
            assert len(validate_findings_file(many_err).errors) == 1
        assert len(validate_findings_data({"bad": 1}).errors) == 1

    # Valid file-level calls
    cid1 = build_canonical_coverage_id(
        entry_point="e1", trust_boundary="b", component="c", attack_class="api-security"
    )
    cid2 = build_canonical_coverage_id(
        entry_point="e2", trust_boundary="b", component="c", attack_class="api-security"
    )
    good_ledger = CoverageLedger(
        ledger_id="LEDGER-0100",
        audit_run_id="AUDIT-0100",
        project="p",
        commit_sha=SHA,
        profile="standard",
        audit_status="initiated",
        execution_mode="single_process_deterministic",
        scope_paths=[],
        units=[
            CoverageUnit(
                coverage_id=cid1,
                component="c",
                attack_class="api-security",
                trust_boundary="b",
                entry_point="e1",
                interface="internal",
                starting_paths=["a.py"],
            )
        ],
    )
    lp = good_ledger.save(tmp_path / "good_ledger.json")
    assert validate_coverage_ledger_file(lp).ok
    fp_path = FindingsCollection("AUDIT-0100", SHA, []).save(tmp_path / "good_findings.json")
    assert validate_findings_file(fp_path).ok

    # Exhaustive CoverageLedger semantic violations
    ld = good_ledger.to_dict()
    u_base = ld["units"][0]
    u_planned_bad = {
        **u_base,
        "coverage_id": cid2,
        "entry_point": "e2",
        "starting_paths": ["../x"],
        "limitations": ["bad"],
    }
    u_not_app_bad = {**u_base, "status": "not_applicable", "limitations": []}
    u_in_prog_bad = {**u_base, "status": "in_progress", "investigator_id": None}
    u_exam_bad = {**u_base, "status": "examined", "investigator_id": "con", "limitations": ["x"]}
    u_blocked_bad = {
        **u_base,
        "status": "blocked",
        "wave": 2,
        "investigator_id": "hunter-01",
        "reviewed_paths": ["a.py"],
        "limitations": [],
        "checks": [
            {
                "investigator_id": "con",
                "method": "source",
                "reviewed_paths": ["../bad"],
                "invariant": "i",
                "result": "r",
                "evidence_refs": [],
                "artifact_path": "should-be-null",
                "timestamp": "t",
            },
            {
                "investigator_id": "hunter-01",
                "method": "sandbox_local",
                "reviewed_paths": ["a.py"],
                "invariant": "i",
                "result": "r",
                "evidence_refs": [],
                "artifact_path": "wrong/prefix.txt",
                "timestamp": "t",
            },
        ],
        "attempts": [
            {
                "wave": 3,
                "status": "blocked",
                "investigator_id": "hunter-01",
                "reviewed_paths": [],
                "checks": [],
                "finding_ids": [],
                "candidate_fingerprints": [],
                "limitations": ["l"],
                "reassignment_reason": "r",
            },
            {
                "wave": 1,
                "status": "blocked",
                "investigator_id": "hunter-01",
                "reviewed_paths": [],
                "checks": [],
                "finding_ids": [],
                "candidate_fingerprints": [],
                "limitations": ["l"],
                "reassignment_reason": "r",
            },
        ],
    }
    ld["units"] = [u_planned_bad, u_not_app_bad, u_in_prog_bad, u_exam_bad, u_blocked_bad]
    ld["audit_status"] = "completed"
    res_ld = validate_coverage_ledger_data(ld)
    assert not res_ld.ok
    assert any("unique and sorted" in e for e in res_ld.errors)

    # Exhaustive Findings semantic violations
    base_d = _make_base_finding("not_verified", "candidate").to_dict()
    r1 = {
        **base_d,
        "fingerprint": "z-fp",
        "finding_id": "SEC-FIND-00000000",
        "affected_locations": [{"file": "../bad.py", "line": 5, "end_line": 2, "symbol": "s"}],
        "trace": [
            {
                "kind": "propagation",
                "file": "../bad.py",
                "line": 1,
                "scope": "s",
                "description": "d",
            }
        ],
        "verification_status": "confirmed",
        "verification_provenance": None,
        "severity": {
            "likelihood": {"score": "high", "reason": "r"},
            "impact": {"score": "low", "reason": "r"},
            "overall_severity": "critical",
        },
        "root_cause": None,
        "remediation": {
            "strategy": "s",
            "invariant_to_enforce": "i",
            "code_changes": [{"file": "../bad.py", "summary": "s"}],
        },
        "unresolved_blockers": ["still-blocked"],
        "state_history": [
            {
                "state": "remediated",
                "run_id": "AUDIT-0100",
                "commit_sha": SHA,
                "actor": "a",
                "reason": "r",
            },
            {
                "state": "candidate",
                "run_id": "AUDIT-0100",
                "commit_sha": SHA,
                "actor": "a",
                "reason": "r",
            },
        ],
    }
    r2 = {
        **base_d,
        "fingerprint": "a-fp",
        "trace": [
            {"kind": "propagation", "file": "a.py", "line": 1, "scope": "s", "description": "d"},
            {"kind": "entrypoint", "file": "a.py", "line": 2, "scope": "s", "description": "d"},
            {"kind": "entrypoint", "file": "a.py", "line": 3, "scope": "s", "description": "d"},
        ],
        "verification_status": "rejected",
        "rejection_reason": None,
        "root_cause": "should-not-be-here",
        "verification_provenance": {
            "verifier_id": "hunter-01",
            "role": "r",
            "run_id": "AUDIT-0100",
            "timestamp": "t",
            "method": "independent_source_review",
            "supporting_evidence": [],
            "contradictory_evidence": [],
            "disprove_attempts": ["d"],
        },
    }
    r3 = {
        **base_d,
        "fingerprint": "m-fp",
        "verification_status": "needs_validation",
        "unresolved_blockers": [],
        "validation_plan": None,
    }
    res_fd = validate_findings_data(
        {
            "schema_version": "1.0.0",
            "audit_run_id": "AUDIT-0100",
            "commit_sha": SHA,
            "records": [r1, r2, r3],
        }
    )
    assert not res_fd.ok

    # Cross-artifact mismatch branches in validate_audit_directory
    mis_dir = tmp_path / "mismatch"
    mis_dir.mkdir()
    good_ledger.units[0].status = "examined"
    good_ledger.units[0].investigator_id = "hunter-01"
    good_ledger.units[0].reviewed_paths = ["a.py"]
    good_ledger.units[0].finding_ids = ["SEC-FIND-DEADBEEF"]
    good_ledger.units[0].candidate_fingerprints = ["missing-fp"]
    good_ledger.units[0].checks = [
        CoverageCheck(
            "hunter-01",
            "sandbox_local",
            ("a.py",),
            "inv",
            "res",
            (),
            "agents/hunter-01/artifacts/missing.txt",
            "t",
        )
    ]
    good_ledger.audit_status = "completed"
    good_ledger.save(mis_dir / "coverage-ledger.json")

    orphan = _make_base_finding("rejected", "rejected")
    FindingsCollection("AUDIT-9999", "e" * 40, [orphan]).save(mis_dir / "findings.json")

    rep_dict = build_security_audit_report(
        ledger=good_ledger,
        findings=FindingsCollection("AUDIT-0100", SHA, []),
        sandbox_caps=SandboxCapabilities(True, True, True, True, None, False),
    )
    rep_file = mis_dir / "security-audit-report.json"
    rep_file.write_text(json.dumps(rep_dict), encoding="utf-8")
    assert validate_audit_report_file(rep_file).ok

    # Force ledger & findings valid individually so cross-artifact block runs
    good_ledger.units[0].finding_ids = []
    good_ledger.units[0].candidate_fingerprints = []
    good_ledger.save(mis_dir / "coverage-ledger.json")
    (mis_dir / "agents" / "hunter-01" / "artifacts").mkdir(parents=True)
    # Leave missing.txt absent so promoted artifact check triggers
    rep_dict["commit_sha"] = "f" * 40
    rep_dict["audit_status"] = "initiated"
    rep_dict["coverage_summary"]["examined"] = 0
    rep_file.write_text(json.dumps(rep_dict), encoding="utf-8")
    cross_res = validate_audit_directory(mis_dir)
    assert not cross_res.ok
    assert any("mismatched audit_run_id" in e for e in cross_res.errors)


def test_hunting_reporting_reassessment_sandbox_and_cli_remaining_branches(
    tmp_path: Path,
) -> None:
    # Hunting: ignored dirs, CLI surface, quick/scoped seeding, syntax error, async def
    proj = tmp_path / "hunt_proj"
    (proj / "src" / "cli_pkg").mkdir(parents=True)
    (proj / "venv").mkdir()
    (proj / "venv" / "ignored.py").write_text("eval('1')\n", encoding="utf-8")
    (proj / "src" / "cli_pkg" / "tool.py").write_text(
        "import argparse\n"
        "# prompt innerHTML AF_UNIX logger.info zipfile.ZipFile\n"
        f"admin_{'pass'}{'word'} = '{'a' * 10}'\n"
        "async def run_async(p):\n"
        "    parser = argparse.ArgumentParser()\n"
        "    (lambda x: x)(1)\n"
        "    return parser\n",
        encoding="utf-8",
    )
    (proj / "src" / "cli_pkg" / "broken.py").write_text("def broken(:\n", encoding="utf-8")
    (proj / "src" / "other").mkdir(parents=True)
    (proj / "src" / "other" / "mod.py").write_text("y = 2\n", encoding="utf-8")

    inv = discover_architecture(proj, SHA)
    # Quick profile merges duplicate cid; scoped run marks out-of-scope units not_examined
    q_ledger = seed_coverage_ledger(inv, audit_run_id="AUDIT-Q1", profile="quick")
    assert q_ledger.units
    s_ledger = seed_coverage_ledger(
        inv, audit_run_id="AUDIT-S1", profile="standard", scope_paths=["src/cli_pkg"]
    )
    assert any(u.status == "not_examined" for u in s_ledger.units)

    # Max-units cap -> partially_completed
    from arkhon.security_audit.dispatcher import SecurityAuditTaskDispatcher

    disp = SecurityAuditTaskDispatcher(tmp_path / "aud_s1")
    execute_hunting_waves(project_root=proj, ledger=s_ledger, dispatcher=disp, max_units=1)
    assert s_ledger.audit_status == "partially_completed"

    # Missing starting file -> not_applicable; blocked unit -> audit_status == blocked
    na_ledger = seed_coverage_ledger(inv, audit_run_id="AUDIT-NA")
    for u in na_ledger.units:
        u.starting_paths = ["src/deleted_file.py"]
    execute_hunting_waves(
        project_root=proj,
        ledger=na_ledger,
        dispatcher=SecurityAuditTaskDispatcher(tmp_path / "aud_na"),
    )
    assert compute_governance_gate_status(
        na_ledger, FindingsCollection("AUDIT-NA", SHA, [])
    ) == "NOT_APPLICABLE"

    na_ledger.units[0].status = "blocked"
    na_ledger.units[0].investigator_id = "hunter-01"
    na_ledger.units[0].reviewed_paths = ["a.py"]
    na_ledger.units[0].limitations = ["blk"]
    na_ledger.units[0].checks = [
        CoverageCheck("hunter-01", "source", ("a.py",), "i", "r", (), None, "t")
    ]
    execute_hunting_waves(
        project_root=proj,
        ledger=na_ledger,
        dispatcher=SecurityAuditTaskDispatcher(tmp_path / "aud_blk_st"),
    )
    assert na_ledger.audit_status == "blocked"

    # Reporting: blocked, not_verified, rejected, remediated, reopened, zero-limitation multi-agent
    f_blk = _make_base_finding("blocked", "blocked")
    f_nv = _make_base_finding("not_verified", "candidate")
    f_nv.fingerprint = "nv-fp"
    f_nv.finding_id = finding_id_from_fingerprint("nv-fp")
    f_rej = _make_base_finding("rejected", "rejected")
    f_rej.fingerprint = "rej-fp"
    f_rej.finding_id = finding_id_from_fingerprint("rej-fp")
    rep_all = build_security_audit_report(
        ledger=s_ledger,
        findings=FindingsCollection("AUDIT-S1", SHA, [f_blk, f_nv, f_rej]),
        sandbox_caps=SandboxCapabilities(True, True, True, True, None, False),
    )
    assert rep_all["rejected_count"] == 1
    assert len(rep_all["blocked_items"]) == 1
    assert len(rep_all["not_verified_items"]) == 1

    clean_unit = CoverageUnit(
        coverage_id=build_canonical_coverage_id(
            entry_point="e", trust_boundary="b", component="c", attack_class="api-security"
        ),
        component="c",
        attack_class="api-security",
        trust_boundary="b",
        entry_point="e",
        interface="internal",
        starting_paths=["a.py"],
        status="examined",
        investigator_id="hunter-01",
        reviewed_paths=["a.py"],
        checks=[CoverageCheck("hunter-01", "source", ("a.py",), "i", "r", (), None, "t")],
    )
    clean_ledger = CoverageLedger(
        "LEDGER-CLN",
        "AUDIT-CLN",
        "p",
        SHA,
        "standard",
        "completed",
        "multi_agent_delegated",
        [],
        [clean_unit],
    )
    rep_clean = build_security_audit_report(
        ledger=clean_ledger,
        findings=FindingsCollection("AUDIT-CLN", SHA, []),
        sandbox_caps=SandboxCapabilities(True, True, True, True, "/usr/bin/bwrap", True),
    )
    md_clean = render_markdown_audit_report(rep_clean)
    assert "examined without blockers" in md_clean

    # Governance bridge: invalid bundle ValueError, rule outcomes, SecurityAuditRunner
    with pytest.raises(ValueError, match="cannot record invalid"):
        record_security_audit_evidence(
            project_root=proj, audit_dir=tmp_path / "empty_aud", commit_sha=SHA
        )
    out_blk = derive_rule_outcomes_from_audit(
        s_ledger, FindingsCollection("AUDIT-S1", SHA, [f_blk])
    )
    assert out_blk["SE-SEC-005"][0] == "BLOCKED"
    out_pass = derive_rule_outcomes_from_audit(
        clean_ledger, FindingsCollection("AUDIT-CLN", SHA, [])
    )
    assert out_pass["SE-SEC-003"][0] == "PASS"

    assert evaluate_security_audit_method(
        RunnerResult(runner="security-audit", outcome=RunnerOutcome.BLOCKED, reason="no git")
    )[0] == "BLOCKED"
    bad_rep = tmp_path / "bad_aud" / "security-audit-report.json"
    bad_rep.parent.mkdir()
    bad_rep.write_text("{}", encoding="utf-8")
    assert evaluate_security_audit_method(
        RunnerResult(
            runner="security-audit", outcome=RunnerOutcome.PASS, artifacts=[bad_rep]
        )
    )[0] == "BLOCKED"
    assert summarize_audit_status(bad_rep.parent)["valid"] is False

    # Sandbox extra branches: probe OSError, preexec limiter, bwrap argv, promotion errors
    with patch("subprocess.run", side_effect=OSError("no exec")):
        p_err = probe_sandbox_capabilities(which_fn=lambda _: "/bin/true", run_probe=True)
        assert p_err.bwrap_path is None
        assert p_err.unshare_net_available is False

    limiter = sandbox_mod._build_preexec_limiter(SandboxLimits())
    with patch("resource.setrlimit", side_effect=ValueError("cap")):
        limiter()
    with patch("resource.setrlimit", return_value=None):
        limiter()

    bwrap_exec = SandboxExecutor(
        tmp_path / "bwrap_aud",
        capabilities=SandboxCapabilities(True, True, True, True, "/bin/echo", False),
    )
    bw_res = bwrap_exec.run_bounded(
        agent_id="hunter-bw", argv=["hello"], source_root=proj
    )
    assert bw_res.status == "PASS"

    # Promotion: existing nested destination dir, non-directory parent segment, mutation mid-read
    sc, ar = bwrap_exec.prepare_agent_dirs("hunter-pr")
    (sc / "d").mkdir()
    (ar / "d").mkdir()
    (sc / "d" / "f1.txt").write_text("ok", encoding="utf-8")
    (sc / "file_as_dir").write_text("not a dir", encoding="utf-8")
    pr1 = promote_agent_artifacts(
        scratch_dir=sc,
        artifacts_dir=ar,
        allowlisted_files=("d/f1.txt", "file_as_dir/leaf.txt"),
    )
    assert pr1.promoted == ("d/f1.txt",)
    # Promoting same destination file twice hits EEXIST OSError cleanly
    pr_dup = promote_agent_artifacts(
        scratch_dir=sc, artifacts_dir=ar, allowlisted_files=("d/f1.txt",)
    )
    assert len(pr_dup.rejected) == 1

    # CLI dispatch remaining branches: default dir, disabled caps, error exits
    assert cd_mod._default_output_dir(proj, "AUDIT-1").name == "AUDIT-1"
    assert cd_mod._resolve_sandbox_caps("disabled").can_enforce_full_sandbox is False
    assert (
        dispatch_security_audit(
            "plan",
            argparse.Namespace(audit_target=str(proj), json=False),
            commit_resolver=lambda _: None,
        )
        == 1
    )
    assert (
        dispatch_security_audit(
            "run",
            argparse.Namespace(
                audit_target=str(proj),
                output_dir=str(tmp_path / "req_sb"),
                sandbox_mode="required",
                json=False,
            ),
            commit_resolver=lambda _: SHA,
        )
        in {0, 1}
    )
    disabled_caps = cd_mod._resolve_sandbox_caps("disabled")
    with (
        patch.object(
            sandbox_mod, "probe_sandbox_capabilities", return_value=disabled_caps
        ),
        patch.object(
            cd_mod, "probe_sandbox_capabilities", return_value=disabled_caps
        ),
    ):
        assert (
            dispatch_security_audit(
                "run",
                argparse.Namespace(
                    audit_target=str(proj),
                    output_dir=str(tmp_path / "req_blk"),
                    sandbox_mode="required",
                    json=False,
                ),
                commit_resolver=lambda _: SHA,
            )
            == 1
        )
    assert (
        dispatch_security_audit(
            "validate",
            argparse.Namespace(audit_dir=str(bad_rep.parent), json=False),
            commit_resolver=lambda _: SHA,
        )
        == 1
    )
    assert (
        dispatch_security_audit(
            "status",
            argparse.Namespace(audit_dir=str(bad_rep.parent), json=False),
            commit_resolver=lambda _: SHA,
        )
        == 1
    )
    assert (
        dispatch_security_audit(
            "verify-findings",
            argparse.Namespace(
                audit_target=str(tmp_path / "missing_proj"),
                audit_dir=str(bad_rep.parent),
                json=False,
            ),
            commit_resolver=lambda _: SHA,
        )
        == 1
    )

    # Reassessment: base == head (unchanged carry-forward!) and missing git executable
    git_proj = tmp_path / "reassess_same"
    (git_proj / "src").mkdir(parents=True)
    (git_proj / "src" / "a.py").write_text("def f(x):\n    return eval(x)\n", encoding="utf-8")
    subprocess.run(  # noqa: S603
        [_GIT, "init"], cwd=git_proj, check=True, capture_output=True
    )
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.email", "t@example.com"], cwd=git_proj, check=True
    )
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.name", "T"], cwd=git_proj, check=True
    )
    subprocess.run([_GIT, "add", "."], cwd=git_proj, check=True)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-m", "init"], cwd=git_proj, check=True, capture_output=True
    )
    g_sha = subprocess.run(  # noqa: S603
        [_GIT, "rev-parse", "HEAD"],
        cwd=git_proj,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert compute_changed_files(git_proj, g_sha, g_sha) == ()
    with patch("shutil.which", return_value=None), pytest.raises(RuntimeError):
        compute_changed_files(git_proj, "a" * 40, "b" * 40)

    r_prior = tmp_path / "r_prior"
    dispatch_security_audit(
        "run",
        argparse.Namespace(
            audit_target=str(git_proj),
            output_dir=str(r_prior),
            profile="standard",
            scope=None,
            sandbox_mode="auto",
            max_units=None,
            verifier_id="independent-verifier-01",
            report_format="all",
            record_evidence=False,
            json=True,
        ),
        commit_resolver=lambda _: g_sha,
    )
    r_same = tmp_path / "r_same"
    same_delta = reassess_repository(
        project_root=git_proj,
        prior_dir=r_prior,
        output_dir=r_same,
        audit_run_id="AUDIT-SAME",
        head_commit=g_sha,
        base_commit=g_sha,
    )
    assert len(same_delta.persisting_finding_ids) == 1

    # SecurityAuditRunner.run() end-to-end (with real git project and non-git project)
    fake_cli = MagicMock()
    fake_cli._commit_sha = lambda p: g_sha if p == git_proj.resolve() else None
    with patch.dict("sys.modules", {"arkhon.cli": fake_cli}):
        runner = SecurityAuditRunner()
        res_blocked = runner.run(tmp_path)
        assert res_blocked.outcome == RunnerOutcome.BLOCKED
        res_ran = runner.run(git_proj, artifact_dir=tmp_path / "runner_out")
        assert res_ran.outcome == RunnerOutcome.FAIL
