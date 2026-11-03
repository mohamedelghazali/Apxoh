"""Deterministic verification orchestration and evidence recording."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import json
from pathlib import Path
import uuid

from arkhon.core.constants import STATUS_BLOCKED, STATUS_FAIL, STATUS_PASS
from arkhon.core.errors import VerificationError
from arkhon.core.logging import get_logger
from arkhon.evidence.collector import EvidenceCollector, EvidenceDraft
from arkhon.evidence.integrity import sha256_of
from arkhon.evidence.supply_chain import (
    verify_cyclonedx_sbom,
    verify_supply_chain_attestation_report,
)
from arkhon.evidence.store import EvidenceStore
from arkhon.verification.runners.base import Runner, RunnerOutcome, RunnerResult

logger = get_logger("verification.engine")


@dataclass
class VerificationRun:
    run_id: str
    domain: str
    commit_sha: str
    results: list[RunnerResult] = field(default_factory=list)
    status: str = STATUS_PASS
    evidence_id: str = ""

    @property
    def has_failures(self) -> bool:
        return self.status != STATUS_PASS


class VerificationEngine:
    """Run registered runners, aggregate outcomes, and persist evidence."""

    # ruff: noqa: I001

    def __init__(self, store: EvidenceStore, collector: EvidenceCollector) -> None:
        self._store = store
        self._collector = collector

    def run(
        self,
        *,
        domain: str,
        commit_sha: str,
        runners: Sequence[Runner],
        project_root: Path,
    ) -> VerificationRun:
        if not runners:
            raise VerificationError("no runners provided")
        if len(commit_sha) != 40 or any(c not in "0123456789abcdef" for c in commit_sha):
            raise VerificationError(f"invalid commit SHA: {commit_sha!r}")
        run_id = f"RUN-{uuid.uuid4().hex[:10].upper()}"
        results: list[RunnerResult] = []
        for runner in runners:
            logger.info("running %s for domain %s", runner.name, domain)
            try:
                result = runner.run(project_root)
                if not isinstance(result, RunnerResult):
                    raise TypeError("runner returned an invalid result object")
                invalid_reason = ""
                if not isinstance(result.outcome, RunnerOutcome):
                    invalid_reason = "runner returned an invalid outcome"
                elif result.outcome == RunnerOutcome.PASS and not result.artifacts:
                    invalid_reason = "runner reported PASS without evidence artifacts"
                else:
                    for artifact in result.artifacts:
                        try:
                            resolved_artifact = Path(artifact).resolve()
                            resolved_artifact.relative_to(project_root.resolve())
                        except (OSError, TypeError, ValueError):
                            invalid_reason = f"runner artifact is outside project root: {artifact}"
                            break
                        if not resolved_artifact.is_file():
                            invalid_reason = f"runner artifact is missing or not a file: {artifact}"
                            break
                if invalid_reason:
                    result = RunnerResult(
                        runner=runner.name,
                        outcome=RunnerOutcome.BLOCKED,
                        reason=invalid_reason,
                        artifacts=[],
                    )
                results.append(result)
            except Exception as exc:
                logger.exception("runner %s crashed", runner.name)
                results.append(
                    RunnerResult(
                        runner=runner.name,
                        outcome=RunnerOutcome.BLOCKED,
                        reason=f"runner crashed: {type(exc).__name__}: {exc}",
                        artifacts=[],
                    )
                )
        if domain in {"supply-chain", "release-attestations"} and all(
            result.outcome == RunnerOutcome.PASS for result in results
        ):
            acceptance_failure = self._verify_supply_chain_acceptance(
                domain, results, project_root=project_root, commit_sha=commit_sha
            )
            if acceptance_failure is not None:
                results.append(acceptance_failure)
        status = self._aggregate_status(results)
        evidence_id = self._record_evidence(
            domain=domain,
            commit_sha=commit_sha,
            results=results,
            status=status,
            run_id=run_id,
            project_root=project_root,
        )
        return VerificationRun(
            run_id=run_id,
            domain=domain,
            commit_sha=commit_sha,
            results=results,
            status=status,
            evidence_id=evidence_id,
        )

    @staticmethod
    def _verify_supply_chain_acceptance(
        domain: str,
        results: list[RunnerResult],
        *,
        project_root: Path,
        commit_sha: str,
    ) -> RunnerResult | None:
        """Re-verify SBOM or release attestations before recording PASS."""
        root = project_root.resolve()
        artifacts = [Path(path).resolve() for result in results for path in result.artifacts]
        if domain == "supply-chain":
            sboms = [
                path
                for path in artifacts
                if path.name.startswith("sbom-") and path.name.endswith(".cdx.json")
            ]
            if len(sboms) != 1:
                reason = "PASS requires exactly one commit-bound CycloneDX SBOM"
            else:
                try:
                    verify_cyclonedx_sbom(sboms[0], expected_commit_sha=commit_sha)
                    return None
                except Exception as exc:
                    reason = f"SBOM acceptance failed: {type(exc).__name__}: {exc}"
        else:
            reports = [path for path in artifacts if path.name.endswith(".attestation.json")]
            if len(reports) != 1:
                reason = "PASS requires exactly one SLSA/Sigstore attestation report"
            else:
                try:
                    evidence_artifacts = [
                        {"path": path.relative_to(root).as_posix(), "sha256": sha256_of(path)}
                        for path in artifacts
                    ]
                    verify_supply_chain_attestation_report(
                        reports[0],
                        evidence_root=root,
                        expected_commit_sha=commit_sha,
                        evidence_artifacts=evidence_artifacts,
                    )
                    return None
                except Exception as exc:
                    reason = (
                        f"cryptographic evidence acceptance failed: " f"{type(exc).__name__}: {exc}"
                    )
        return RunnerResult(
            runner="supply-chain-evidence-acceptance",
            outcome=RunnerOutcome.BLOCKED,
            reason=reason,
        )

    @staticmethod
    def _aggregate_status(results: list[RunnerResult]) -> str:
        if any(result.outcome == RunnerOutcome.FAIL for result in results):
            return STATUS_FAIL
        if any(result.outcome == RunnerOutcome.BLOCKED for result in results):
            return STATUS_BLOCKED
        return STATUS_PASS

    def _record_evidence(
        self,
        *,
        domain: str,
        commit_sha: str,
        results: list[RunnerResult],
        status: str,
        run_id: str,
        project_root: Path,
    ) -> str:
        draft: EvidenceDraft = self._collector.new_evidence(
            source="arkhon",
            source_version="0.1.0.dev1",
            commit_sha=commit_sha,
            status=status,
        )
        for result in results:
            for artifact in result.artifacts:
                draft.add_artifact(artifact)

        if not draft.artifacts:
            # A blocked runner may have no tool output to attach. Preserve a
            # machine-readable execution record without treating it as a PASS
            # artifact or silently dropping the BLOCKED evidence.
            summary_dir = project_root.resolve() / ".arkhon" / "reports" / "verification"
            summary_dir.mkdir(parents=True, exist_ok=True)
            summary_path = summary_dir / f"{run_id}.json"
            summary = {
                "run_id": run_id,
                "domain": domain,
                "commit_sha": commit_sha,
                "status": status,
                "runners": [
                    {
                        "name": result.runner,
                        "outcome": result.outcome.value,
                        "reason": result.reason,
                        "artifacts": [str(path) for path in result.artifacts],
                    }
                    for result in results
                ],
                "note": (
                    "Execution diagnostic only; this record is not proof "
                    "of a passing verification."
                ),
            }
            summary_path.write_text(
                json.dumps(summary, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            draft.add_artifact(summary_path)

        draft.summary = {
            "pass": sum(r.outcome == RunnerOutcome.PASS for r in results),
            "fail": sum(r.outcome == RunnerOutcome.FAIL for r in results),
            "blocked": sum(r.outcome == RunnerOutcome.BLOCKED for r in results),
        }
        evidence = draft.to_evidence()
        self._store.write(domain, evidence)
        return str(evidence["evidence_id"])
