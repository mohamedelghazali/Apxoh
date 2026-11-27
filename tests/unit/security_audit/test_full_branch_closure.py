"""Final branch-closure tests ensuring 100.00% statement coverage across security_audit."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from gencode_gov.security_audit import cli_dispatch as cd_mod
from gencode_gov.security_audit import governance_bridge as gb_mod
from gencode_gov.security_audit import sandbox as sandbox_mod
from gencode_gov.security_audit import validators as validators_mod
from gencode_gov.security_audit.cli_dispatch import dispatch_security_audit
from gencode_gov.security_audit.coverage import (
    CoverageCheck,
    CoverageLedger,
    CoverageUnit,
    build_canonical_coverage_id,
)
from gencode_gov.security_audit.findings import (
    DiscoveryProvenance,
    FindingsCollection,
    LocationRef,
    SecurityFinding,
    TraceStep,
    compute_finding_fingerprint,
    finding_id_from_fingerprint,
)
from gencode_gov.security_audit.governance_bridge import (
    SecurityAuditRunner,
    derive_rule_outcomes_from_audit,
    summarize_audit_status,
)
from gencode_gov.security_audit.reassessment import reassess_repository
from gencode_gov.security_audit.reporting import build_security_audit_report
from gencode_gov.security_audit.sandbox import (
    SandboxCapabilities,
    SandboxExecutor,
    probe_sandbox_capabilities,
    promote_agent_artifacts,
)
from gencode_gov.security_audit.validators import (
    ArtifactValidationResult,
    is_safe_relative_path,
    validate_audit_directory,
    validate_audit_report_data,
    validate_coverage_ledger_data,
    validate_findings_file,
)
from gencode_gov.verification.runners.base import RunnerOutcome

_GIT = shutil.which("git") or "/usr/bin/git"
SHA = "d" * 40


def _make_lead(status: str, state: str) -> SecurityFinding:
    fp = compute_finding_fingerprint(
        component="src",
        attack_class="secrets-credential-handling",
        primary_file="src/pkg_keep/keep.py",
        symbol="cfg",
        invariant_key=f"inv-{status}-{state}",
    )
    return SecurityFinding(
        finding_id=finding_id_from_fingerprint(fp),
        fingerprint=fp,
        title="Lead",
        description="Desc",
        attack_class="secrets-credential-handling",
        component="src",
        affected_locations=[LocationRef("src/pkg_keep/keep.py", 1, "cfg")],
        trace=[TraceStep("sink", "src/pkg_keep/keep.py", 1, "cfg", "sink")],
        trust_boundary="internal",
        entry_point="mod",
        affected_principal_or_resource="res",
        preconditions=[],
        scenario_summary="sum",
        reproduction_steps=[],
        security_impact="imp",
        evidence_refs=["src/pkg_keep/keep.py:1"],
        discovery_provenance=DiscoveryProvenance(
            "hunter-01", "security-hunter", "AUDIT-00X1", "2026-11-26T00:00:00Z", "static_ast"
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
        rejection_reason="rej" if status == "rejected" else None,
        related_rules=["SE-SEC-005"],
        related_requirements=[],
        commit_sha=SHA,
        first_seen_run="AUDIT-00X1",
        last_seen_run="AUDIT-00X1",
        first_seen_commit=SHA,
        last_seen_commit=SHA,
        state_history=[
            {
                "state": state,
                "run_id": "AUDIT-00X1",
                "commit_sha": SHA,
                "actor": "hunter-01",
                "reason": "init",
            }
        ],
    )


def test_final_branches_for_100pct_coverage(tmp_path: Path) -> None:
    assert is_safe_relative_path("a\\b") is False
    nested_two = tmp_path / "nested_two.json"
    nested_two.write_text("[[1], [2]]", encoding="utf-8")
    with (
        patch.object(validators_mod, "MAX_NESTING_DEPTH", 0),
        patch.object(validators_mod, "MAX_REPORTED_ERRORS", 1),
    ):
        assert not validate_findings_file(nested_two).ok
    assert not validate_coverage_ledger_data({}).ok

    cid = build_canonical_coverage_id(
        entry_point="e", trust_boundary="b", component="c", attack_class="api-security"
    )
    led = CoverageLedger(
        "LEDGER-00X1",
        "AUDIT-00X1",
        "p",
        SHA,
        "standard",
        "initiated",
        "single_process_deterministic",
        [],
        [
            CoverageUnit(
                coverage_id=cid,
                component="c",
                attack_class="api-security",
                trust_boundary="b",
                entry_point="e",
                interface="internal",
                starting_paths=["a.py"],
            )
        ],
    )
    rep_inc = build_security_audit_report(
        ledger=led,
        findings=FindingsCollection("AUDIT-00X1", SHA, []),
        sandbox_caps=SandboxCapabilities(True, True, True, True, None, True),
    )
    rep_inc["audit_status"] = "completed"
    assert not validate_audit_report_data(rep_inc).ok

    ca_dir = tmp_path / "ca_dir"
    ca_dir.mkdir()
    led.units[0].status = "examined"
    led.units[0].investigator_id = "hunter-01"
    led.units[0].reviewed_paths = ["a.py"]
    led.units[0].checks = [CoverageCheck("hunter-01", "source", ("a.py",), "i", "r", (), None, "t")]
    led.units[0].finding_ids = ["SEC-FIND-AAAAAAAA"]
    led.units[0].candidate_fingerprints = ["missing:fp:1"]
    led.audit_status = "completed"
    led.save(ca_dir / "coverage-ledger.json")
    FindingsCollection("AUDIT-00X1", SHA, []).save(ca_dir / "findings.json")

    rep_ok = build_security_audit_report(
        ledger=led,
        findings=FindingsCollection("AUDIT-00X1", SHA, []),
        sandbox_caps=SandboxCapabilities(True, True, True, True, None, True),
    )
    rep_ok["governance_gate_status"] = "FAIL"
    rep_ok["confirmed_findings"] = [
        {
            "finding_id": "SEC-FIND-BBBBBBBB",
            "fingerprint": "fp",
            "title": "t",
            "severity": "high",
            "component": "c",
            "attack_class": "api-security",
            "trust_boundary": "b",
            "primary_location": "a.py:1",
            "remediation_strategy": "fix",
            "related_rules": ["SE-SEC-003"],
        }
    ]
    (ca_dir / "security-audit-report.json").write_text(json.dumps(rep_ok), encoding="utf-8")
    ca_val = validate_audit_directory(ca_dir)
    assert not ca_val.ok
    assert any("references missing finding" in e for e in ca_val.errors)
    assert any("references missing fingerprint" in e for e in ca_val.errors)
    assert any("confirmed_findings disagrees" in e for e in ca_val.errors)

    f_rem = _make_lead("rejected", "remediated")
    assert derive_rule_outcomes_from_audit(led, FindingsCollection("AUDIT-00X1", SHA, [f_rem]))

    f_blk = _make_lead("blocked", "blocked")
    blk_dir = tmp_path / "blk_sum"
    blk_dir.mkdir()
    led.units[0].finding_ids = [f_blk.finding_id]
    led.units[0].candidate_fingerprints = [f_blk.fingerprint]
    led.save(blk_dir / "coverage-ledger.json")
    FindingsCollection("AUDIT-00X1", SHA, [f_blk]).save(blk_dir / "findings.json")
    assert summarize_audit_status(blk_dir)["finding_counts"]["blocked"] == 1

    gp = tmp_path / "gp"
    (gp / "src" / "pkg_keep").mkdir(parents=True)
    (gp / "src" / "pkg_touch").mkdir(parents=True)
    (gp / "docs").mkdir()
    (gp / "docs" / "note.py").write_text("eval('ignored')\n", encoding="utf-8")
    (gp / "src" / "pkg_keep" / "keep.py").write_text("x = 1\n", encoding="utf-8")
    (gp / "src" / "pkg_touch" / "touch.py").write_text(
        "def f(z):\n    return eval(z)\n", encoding="utf-8"
    )
    subprocess.run([_GIT, "init"], cwd=gp, check=True, capture_output=True)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.email", "t@example.com"], cwd=gp, check=True
    )
    subprocess.run([_GIT, "config", "user.name", "T"], cwd=gp, check=True)  # noqa: S603
    subprocess.run([_GIT, "add", "."], cwd=gp, check=True)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-m", "c1"], cwd=gp, check=True, capture_output=True
    )
    sha_c1 = subprocess.run(  # noqa: S603
        [_GIT, "rev-parse", "HEAD"], cwd=gp, check=True, capture_output=True, text=True
    ).stdout.strip()

    p_dir = tmp_path / "p_dir"
    with patch.object(Path, "home", return_value=tmp_path / "fake_home"):
        dispatch_security_audit(
            "plan",
            argparse.Namespace(
                audit_target=str(gp), output_dir=None, profile="standard", scope=None, json=True
            ),
            commit_resolver=lambda _: sha_c1,
        )
    dispatch_security_audit(
        "run",
        argparse.Namespace(
            audit_target=str(gp),
            output_dir=str(p_dir),
            profile="standard",
            scope=["src/pkg_touch/touch.py"],
            sandbox_mode="auto",
            max_units=None,
            verifier_id="independent-verifier-01",
            report_format="all",
            record_evidence=False,
            json=True,
        ),
        commit_resolver=lambda _: sha_c1,
    )
    pl = CoverageLedger.load(p_dir / "coverage-ledger.json")
    pf = FindingsCollection.load(p_dir / "findings.json")
    nv_lead = _make_lead("needs_validation", "needs_validation")
    pf.records.append(nv_lead)
    for u in pl.units:
        if (
            "src/pkg_touch/touch.py" in u.starting_paths
            and u.attack_class == "secrets-credential-handling"
        ):
            u.status = "partially_examined"
            u.limitations = ["partial"]
        elif (
            "src/pkg_keep/keep.py" in u.starting_paths
            and u.attack_class == "injection-input-handling"
        ):
            u.status = "examined"
            u.investigator_id = "hunter-01"
            u.reviewed_paths = list(u.starting_paths)
            u.checks = [
                CoverageCheck(
                    "hunter-01", "source", tuple(u.starting_paths), "i", "r", (), None, "t"
                )
            ]
            u.finding_ids = [nv_lead.finding_id]
            u.candidate_fingerprints = [nv_lead.fingerprint]
            u.limitations = []
    pl.save(p_dir / "coverage-ledger.json")
    pf.save(p_dir / "findings.json")

    (gp / "src" / "pkg_touch" / "touch.py").write_text(
        "import pickle\ndef f(z):\n    pickle.loads(z)\n    return eval(z)\n",
        encoding="utf-8",
    )
    subprocess.run([_GIT, "add", "."], cwd=gp, check=True)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-m", "c2"], cwd=gp, check=True, capture_output=True
    )
    sha_c2 = subprocess.run(  # noqa: S603
        [_GIT, "rev-parse", "HEAD"], cwd=gp, check=True, capture_output=True, text=True
    ).stdout.strip()

    re_out = tmp_path / "re_out"
    delta2 = reassess_repository(
        project_root=gp,
        prior_dir=p_dir,
        output_dir=re_out,
        audit_run_id="AUDIT-00C2",
        head_commit=sha_c2,
    )
    assert len(delta2.new_finding_ids) >= 1
    assert len(delta2.persisting_finding_ids) >= 1

    with patch.object(
        cd_mod,
        "validate_audit_directory",
        return_value=ArtifactValidationResult(False, ("forced-err",)),
    ):
        assert (
            dispatch_security_audit(
                "run",
                argparse.Namespace(
                    audit_target=str(gp),
                    output_dir=str(tmp_path / "f_run"),
                    profile="quick",
                    scope=None,
                    sandbox_mode="auto",
                    max_units=None,
                    verifier_id="independent-verifier-01",
                    report_format="json",
                    record_evidence=False,
                    json=False,
                ),
                commit_resolver=lambda _: sha_c2,
            )
            == 1
        )
        assert (
            dispatch_security_audit(
                "verify-findings",
                argparse.Namespace(
                    audit_target=str(gp),
                    audit_dir=str(re_out),
                    verifier_id="verifier-99",
                    json=False,
                ),
                commit_resolver=lambda _: sha_c2,
            )
            == 1
        )

    fake_cli = MagicMock()
    fake_cli._commit_sha = lambda _: sha_c2
    with patch.dict("sys.modules", {"gencode_gov.cli": fake_cli}):
        runner = SecurityAuditRunner()
        r_def = runner.run(gp, artifact_dir=None)
        assert r_def.outcome == RunnerOutcome.FAIL
        with patch.object(
            gb_mod,
            "validate_audit_directory",
            return_value=ArtifactValidationResult(False, ("bad",)),
        ):
            r_inv = runner.run(gp, artifact_dir=tmp_path / "r_inv")
            assert r_inv.outcome == RunnerOutcome.BLOCKED

    sb = SandboxExecutor(
        tmp_path / "sb_cov",
        capabilities=SandboxCapabilities(True, True, True, True, None, True),
    )
    if probe_sandbox_capabilities().unshare_net_available:
        real_which = sandbox_mod.shutil.which
        with patch(
            "shutil.which",
            side_effect=lambda cmd: "/bin/true" if cmd == "ip" else real_which(cmd),
        ):
            lb_res = sb.run_bounded(
                agent_id="hunter-lb",
                argv=["/bin/true"],
                source_root=gp,
                allow_loopback=True,
            )
            assert lb_res.status == "PASS"

    sc_dir, ar_dir = sb.prepare_agent_dirs("hunter-race")
    race_file = sc_dir / "mut.txt"
    race_file.write_bytes(b"abcd")
    real_fstat = sandbox_mod.os.fstat

    with patch("os.read", side_effect=[b"abcdef", b""]):
        pr_grow = promote_agent_artifacts(
            scratch_dir=sc_dir,
            artifacts_dir=ar_dir,
            allowlisted_files=("mut.txt",),
            max_file_bytes=4,
        )
        assert pr_grow.rejected[0][1] == "scratch file mutated during promotion"

    call_idx = {"n": 0}

    def _fstat_dest_bad(fd: int) -> object:
        st = real_fstat(fd)
        if not sandbox_mod.stat.S_ISDIR(st.st_mode):
            call_idx["n"] += 1
            if call_idx["n"] == 3:
                m = MagicMock()
                m.st_mode = st.st_mode
                m.st_nlink = 2
                return m
        return st

    with patch("os.fstat", side_effect=_fstat_dest_bad):
        pr_dst = promote_agent_artifacts(
            scratch_dir=sc_dir,
            artifacts_dir=ar_dir,
            allowlisted_files=("mut.txt",),
        )
        assert pr_dst.rejected[0][1] == "destination verification failed"

    (sc_dir / "sub").mkdir()
    (sc_dir / "sub" / "ok.txt").write_bytes(b"1")
    dir_check_idx = {"n": 0}

    def _fstat_non_dir(fd: int) -> object:
        st = real_fstat(fd)
        dir_check_idx["n"] += 1
        if dir_check_idx["n"] == 1:
            m = MagicMock()
            m.st_mode = 0o100644
            return m
        return st

    with patch("os.fstat", side_effect=_fstat_non_dir):
        pr_nondir = promote_agent_artifacts(
            scratch_dir=sc_dir,
            artifacts_dir=ar_dir,
            allowlisted_files=("sub/ok.txt",),
        )
        assert "not a directory" in pr_nondir.rejected[0][1]
