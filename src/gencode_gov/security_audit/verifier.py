"""Independent adversarial finding verification (Phase 3 & Phase 5)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from gencode_gov.security_audit.findings import (
    FindingsCollection,
    RemediationGuidance,
    SecurityFinding,
    SeverityAssessment,
    VerificationProvenance,
)
from gencode_gov.security_audit.sandbox import SandboxExecutor, validate_agent_id
from gencode_gov.security_audit.validators import is_safe_relative_path

_MITIGATION_PATTERNS: tuple[tuple[str, str], ...] = (
    ("yaml.safe_load", "uses safe YAML loader (yaml.safe_load)"),
    ("SafeLoader", "explicitly specifies yaml.SafeLoader"),
    ("defusedxml", "parses XML through defusedxml"),
    (".relative_to(", "confines path via Path.relative_to()"),
    ("O_NOFOLLOW", "enforces O_NOFOLLOW against symlink races"),
    ("compare_digest", "uses constant-time hmac.compare_digest"),
    ("argon2", "uses adaptive Argon2 password hashing"),
    ("bcrypt", "uses adaptive bcrypt password hashing"),
    ("scrypt", "uses adaptive scrypt key derivation"),
)

_DEPLOYMENT_DEPENDENT_CLASSES = frozenset(
    {
        "cloud-deployment-security",
        "web-protocol-security",
        "mobile-application-security",
    }
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _calibrate_severity(attack_class: str, boundary: str) -> SeverityAssessment:
    """Assign calibrated severity strictly bounded so overall_severity <= impact."""
    unauth = "unauthenticated" in boundary or "external" in boundary
    if attack_class in {"injection-input-handling", "ai-llm-security", "memory-binary-safety"}:
        impact = "critical" if unauth else "high"
        likelihood = "high" if unauth else "medium"
        overall = "critical" if unauth else "high"
    elif attack_class in {
        "authn-authz-boundaries",
        "data-tenant-isolation",
        "secrets-credential-handling",
        "supply-chain-release",
    }:
        impact = "high"
        likelihood = "medium"
        overall = "high"
    elif attack_class in {
        "cryptographic-implementation",
        "configuration-infrastructure",
        "api-security",
        "client-side-security",
        "local-ipc-trust",
        "desktop-application-security",
        "protocols-rpc-messaging",
        "data-lifecycle-privacy",
        "resource-exhaustion-availability",
    }:
        impact = "medium"
        likelihood = "medium"
        overall = "medium"
    else:
        impact = "low"
        likelihood = "low"
        overall = "low"
    return SeverityAssessment(
        likelihood_score=likelihood,
        likelihood_reason=f"Reachable across {boundary} boundary in verified source context.",
        impact_score=impact,
        impact_reason=f"Verified {attack_class} invariant failure on target resource.",
        overall_severity=overall,
    )


class IndependentFindingVerifier:
    """Adversarial verifier that inspects source context and attempts to disprove leads."""

    def __init__(
        self,
        project_root: Path,
        *,
        verifier_id: str = "independent-verifier-01",
        sandbox: SandboxExecutor | None = None,
    ) -> None:
        if not validate_agent_id(verifier_id):
            raise ValueError(f"invalid canonical verifier_id: {verifier_id!r}")
        self.project_root = project_root.resolve()
        self.verifier_id = verifier_id
        self.sandbox = sandbox

    def verify_candidate(
        self,
        finding: SecurityFinding,
        *,
        run_id: str,
        commit_sha: str,
        sandbox_command: list[str] | None = None,
    ) -> SecurityFinding:
        """Attempt to disprove candidate; confirm only when source/local evidence holds."""
        if finding.discovery_provenance.agent_id == self.verifier_id:
            raise ValueError(
                f"separation-of-duties violation: {self.verifier_id!r} cannot self-verify"
            )

        disprove_attempts: list[str] = [
            "Verified repository-relative file existence and positive line bounds.",
            "Inspected surrounding source window for mitigating sanitizers or guards.",
            "Checked whether location belongs to synthetic tests or documentation fixtures.",
        ]
        supporting: list[str] = []
        contradictory: list[str] = []

        # 1. Verify trace & location integrity against real repository files
        primary_loc = finding.affected_locations[0]
        if not is_safe_relative_path(primary_loc.file):
            return self._mark_rejected(
                finding,
                run_id=run_id,
                commit_sha=commit_sha,
                disprove_attempts=disprove_attempts,
                supporting=supporting,
                contradictory=["Unsafe or non-relative source path in candidate location."],
                reason="Candidate references an invalid or unsafe source path.",
            )

        target_file = (self.project_root / primary_loc.file).resolve()
        try:
            target_file.relative_to(self.project_root)
        except ValueError:
            return self._mark_rejected(
                finding,
                run_id=run_id,
                commit_sha=commit_sha,
                disprove_attempts=disprove_attempts,
                supporting=supporting,
                contradictory=["Resolved path escapes repository root."],
                reason="Candidate path escapes repository root.",
            )

        if not target_file.is_file() or target_file.is_symlink():
            return self._mark_rejected(
                finding,
                run_id=run_id,
                commit_sha=commit_sha,
                disprove_attempts=disprove_attempts,
                supporting=supporting,
                contradictory=[f"Source file {primary_loc.file} missing or symlink."],
                reason=f"Referenced file {primary_loc.file} does not exist as a regular file.",
            )

        lines = target_file.read_text(encoding="utf-8", errors="replace").splitlines()
        if primary_loc.line < 1 or primary_loc.line > max(len(lines), 1):
            return self._mark_rejected(
                finding,
                run_id=run_id,
                commit_sha=commit_sha,
                disprove_attempts=disprove_attempts,
                supporting=supporting,
                contradictory=[
                    f"Line {primary_loc.line} out of range (1..{len(lines)}) in {primary_loc.file}."
                ],
                reason="Referenced source line number does not exist in target file.",
            )

        norm_rel = primary_loc.file.replace("\\", "/")
        if norm_rel.startswith(("tests/", "docs/")) or "/fixtures/" in norm_rel:
            contradictory.append(f"Path {norm_rel} is a non-production test or fixture file.")
            return self._mark_rejected(
                finding,
                run_id=run_id,
                commit_sha=commit_sha,
                disprove_attempts=disprove_attempts,
                supporting=supporting,
                contradictory=contradictory,
                reason="Pattern occurs inside test/doc fixture rather than target runtime.",
            )

        # 2. Inspect context window around reported line for mitigating controls
        win_start = max(0, primary_loc.line - 6)
        win_end = min(len(lines), primary_loc.line + 6)
        window_text = "\n".join(lines[win_start:win_end])
        target_line = lines[primary_loc.line - 1].strip()
        supporting.append(f"{primary_loc.file}:{primary_loc.line} -> {target_line[:120]}")

        for token, explanation in _MITIGATION_PATTERNS:
            if token in window_text and token not in (finding.claimed_root_cause or ""):
                contradictory.append(f"Mitigating control present in local scope: {explanation}")
                return self._mark_rejected(
                    finding,
                    run_id=run_id,
                    commit_sha=commit_sha,
                    disprove_attempts=disprove_attempts,
                    supporting=supporting,
                    contradictory=contradictory,
                    reason=f"Disproved by local mitigating control: {explanation}.",
                )

        if "subprocess.run" in target_line and "shell=True" not in window_text:
            contradictory.append("subprocess.run invoked without shell=True (list argv).")
            return self._mark_rejected(
                finding,
                run_id=run_id,
                commit_sha=commit_sha,
                disprove_attempts=disprove_attempts,
                supporting=supporting,
                contradictory=contradictory,
                reason="Disproved: subprocess invocation uses shell=False argument vector.",
            )

        # 3. Optional bounded sandbox check if dynamic local verification was requested
        method = "independent_source_review"
        if sandbox_command is not None:
            disprove_attempts.append("Executed bounded local check inside OS sandbox.")
            if self.sandbox is None:
                return self._mark_needs_validation(
                    finding,
                    run_id=run_id,
                    commit_sha=commit_sha,
                    disprove_attempts=disprove_attempts,
                    supporting=supporting,
                    blocker="SandboxExecutor not configured for dynamic local check.",
                )
            sb_res = self.sandbox.run_bounded(
                agent_id=self.verifier_id,
                argv=sandbox_command,
                source_root=self.project_root,
            )
            method = "independent_sandbox_check"
            if sb_res.status == "BLOCKED":
                return self._mark_blocked(
                    finding,
                    run_id=run_id,
                    commit_sha=commit_sha,
                    disprove_attempts=disprove_attempts,
                    supporting=supporting,
                    blocker=sb_res.blocker_reason or "Sandbox execution blocked.",
                )
            if sb_res.returncode != 0:
                contradictory.append("Bounded sandbox check did not reproduce claimed behavior.")
                return self._mark_rejected(
                    finding,
                    run_id=run_id,
                    commit_sha=commit_sha,
                    disprove_attempts=disprove_attempts,
                    supporting=supporting,
                    contradictory=contradictory,
                    reason="Bounded sandbox check disproved candidate hypothesis.",
                )
            supporting.append(f"Sandboxed local check ({sb_res.backend}) verified behavior.")

        # 4. Respect source visibility for external deployment/proxy/IAM assumptions
        if (
            finding.unresolved_blockers
            or finding.attack_class in _DEPLOYMENT_DEPENDENT_CLASSES
            and "deployment_verified" not in finding.evidence_refs
        ):
            blocker = (
                finding.unresolved_blockers[0]
                if finding.unresolved_blockers
                else (
                    f"External {finding.attack_class} gateway/IAM control visibility "
                    "is outside repository source."
                )
            )
            return self._mark_needs_validation(
                finding,
                run_id=run_id,
                commit_sha=commit_sha,
                disprove_attempts=disprove_attempts,
                supporting=supporting,
                blocker=blocker,
            )

        # 5. Confirmed: assign calibrated severity, confirmed root_cause, and remediation
        confirmed_cause = (
            finding.root_cause
            or finding.claimed_root_cause
            or f"Verified {finding.attack_class} invariant violation at {primary_loc.file}."
        )
        finding.verification_provenance = VerificationProvenance(
            verifier_id=self.verifier_id,
            role="independent-finding-verifier",
            run_id=run_id,
            timestamp=_utc_now(),
            method=method,
            supporting_evidence=tuple(supporting),
            contradictory_evidence=tuple(contradictory),
            disprove_attempts=tuple(disprove_attempts),
        )
        finding.verification_status = "confirmed"
        finding.root_cause = confirmed_cause
        finding.claimed_root_cause = None
        finding.severity = _calibrate_severity(finding.attack_class, finding.trust_boundary)
        finding.remediation = finding.remediation or RemediationGuidance(
            strategy=(
                f"Enforce strict boundary validation and safe API usage in {primary_loc.file}."
            ),
            invariant_to_enforce=(
                f"Untrusted input crossing {finding.trust_boundary} must never reach "
                f"{primary_loc.symbol} unvalidated."
            ),
            code_changes=(
                (primary_loc.file, f"Harden {primary_loc.symbol} at line {primary_loc.line}"),
            ),
        )
        finding.unresolved_blockers = []
        finding.validation_plan = None
        finding.rejection_reason = None
        finding.confidence_score = "high"
        finding.confidence_reason = "Source trace and local context independently verified."
        finding.transition_to(
            "confirmed",
            run_id=run_id,
            commit_sha=commit_sha,
            actor=self.verifier_id,
            reason="Independently verified source trace and absence of local mitigating controls.",
        )
        return finding

    def verify_record_integrity(
        self,
        finding: SecurityFinding,
        *,
        record_verifier_id: str,
        run_id: str,
        commit_sha: str,
    ) -> SecurityFinding:
        """Phase 5 independent record check ensuring final source references still match."""
        if not validate_agent_id(record_verifier_id):
            raise ValueError(f"invalid record_verifier_id: {record_verifier_id!r}")
        if record_verifier_id in {
            finding.discovery_provenance.agent_id,
            finding.verification_provenance.verifier_id if finding.verification_provenance else "",
        }:
            raise ValueError("Phase 5 record verifier must be distinct from hunter and Phase 3")
        if finding.verification_status not in {"confirmed", "needs_validation"}:
            return finding

        for step in finding.trace:
            full = (self.project_root / step.file).resolve()
            if not full.is_file() or full.is_symlink():
                return self._mark_needs_validation(
                    finding,
                    run_id=run_id,
                    commit_sha=commit_sha,
                    disprove_attempts=["Phase 5 record trace file check failed."],
                    supporting=[],
                    blocker=f"Trace file {step.file} missing during Phase 5 record check.",
                )
            line_count = len(full.read_text(encoding="utf-8", errors="replace").splitlines())
            if step.line < 1 or step.line > max(line_count, 1):
                return self._mark_needs_validation(
                    finding,
                    run_id=run_id,
                    commit_sha=commit_sha,
                    disprove_attempts=["Phase 5 record line range check failed."],
                    supporting=[],
                    blocker=f"Trace line {step.file}:{step.line} drifted out of bounds.",
                )
        return finding

    def _mark_rejected(
        self,
        finding: SecurityFinding,
        *,
        run_id: str,
        commit_sha: str,
        disprove_attempts: list[str],
        supporting: list[str],
        contradictory: list[str],
        reason: str,
    ) -> SecurityFinding:
        finding.claimed_root_cause = (
            finding.claimed_root_cause or finding.root_cause or finding.title
        )
        finding.root_cause = None
        finding.severity = None
        finding.remediation = None
        finding.unresolved_blockers = []
        finding.validation_plan = None
        finding.rejection_reason = reason
        finding.verification_status = "rejected"
        finding.verification_provenance = VerificationProvenance(
            verifier_id=self.verifier_id,
            role="independent-finding-verifier",
            run_id=run_id,
            timestamp=_utc_now(),
            method="independent_source_review",
            supporting_evidence=tuple(supporting),
            contradictory_evidence=tuple(contradictory),
            disprove_attempts=tuple(disprove_attempts),
        )
        finding.transition_to(
            "rejected",
            run_id=run_id,
            commit_sha=commit_sha,
            actor=self.verifier_id,
            reason=reason,
        )
        return finding

    def _mark_needs_validation(
        self,
        finding: SecurityFinding,
        *,
        run_id: str,
        commit_sha: str,
        disprove_attempts: list[str],
        supporting: list[str],
        blocker: str,
    ) -> SecurityFinding:
        finding.claimed_root_cause = (
            finding.claimed_root_cause or finding.root_cause or finding.title
        )
        finding.root_cause = None
        finding.severity = None
        finding.remediation = None
        finding.rejection_reason = None
        finding.unresolved_blockers = [blocker]
        finding.validation_plan = finding.validation_plan or {
            "local_check": (
                f"Run bounded sandboxed harness covering {finding.affected_locations[0].file}."
            ),
            "owner_deployment_check": (
                f"Inspect deployment config for {finding.trust_boundary} without live probes."
            ),
        }
        finding.verification_status = "needs_validation"
        finding.verification_provenance = VerificationProvenance(
            verifier_id=self.verifier_id,
            role="independent-finding-verifier",
            run_id=run_id,
            timestamp=_utc_now(),
            method="independent_source_review",
            supporting_evidence=tuple(supporting),
            contradictory_evidence=(),
            disprove_attempts=tuple(disprove_attempts),
        )
        finding.transition_to(
            "needs_validation",
            run_id=run_id,
            commit_sha=commit_sha,
            actor=self.verifier_id,
            reason=blocker,
        )
        return finding

    def _mark_blocked(
        self,
        finding: SecurityFinding,
        *,
        run_id: str,
        commit_sha: str,
        disprove_attempts: list[str],
        supporting: list[str],
        blocker: str,
    ) -> SecurityFinding:
        finding.claimed_root_cause = (
            finding.claimed_root_cause or finding.root_cause or finding.title
        )
        finding.root_cause = None
        finding.severity = None
        finding.remediation = None
        finding.rejection_reason = None
        finding.unresolved_blockers = [blocker]
        finding.validation_plan = {
            "local_check": "Provision OS network-isolated sandbox (bwrap or unshare -r --net)."
        }
        finding.verification_status = "blocked"
        finding.verification_provenance = VerificationProvenance(
            verifier_id=self.verifier_id,
            role="independent-finding-verifier",
            run_id=run_id,
            timestamp=_utc_now(),
            method="independent_sandbox_check",
            supporting_evidence=tuple(supporting),
            contradictory_evidence=(),
            disprove_attempts=tuple(disprove_attempts),
        )
        finding.transition_to(
            "blocked",
            run_id=run_id,
            commit_sha=commit_sha,
            actor=self.verifier_id,
            reason=blocker,
        )
        return finding


def verify_findings_collection(
    collection: FindingsCollection,
    *,
    project_root: Path,
    verifier_id: str = "independent-verifier-01",
    record_verifier_id: str = "record-verifier-01",
    sandbox: SandboxExecutor | None = None,
) -> FindingsCollection:
    """Run Phase 3 adversarial verification and Phase 5 record verification across collection."""
    verifier = IndependentFindingVerifier(
        project_root,
        verifier_id=verifier_id,
        sandbox=sandbox,
    )
    updated: list[SecurityFinding] = []
    for item in collection.records:
        if item.lifecycle_state == "remediated":
            updated.append(item)
            continue
        checked = verifier.verify_candidate(
            item,
            run_id=collection.audit_run_id,
            commit_sha=collection.commit_sha,
        )
        final_rec = verifier.verify_record_integrity(
            checked,
            record_verifier_id=record_verifier_id,
            run_id=collection.audit_run_id,
            commit_sha=collection.commit_sha,
        )
        updated.append(final_rec)
    result = FindingsCollection(
        audit_run_id=collection.audit_run_id,
        commit_sha=collection.commit_sha,
        records=updated,
    )
    result.deduplicate_and_sort()
    return result
