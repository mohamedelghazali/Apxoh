"""Deterministic verification orchestration and evidence recording."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from arkhon.core.constants import STATUS_BLOCKED, STATUS_FAIL, STATUS_PASS
from arkhon.core.errors import VerificationError
from arkhon.core.logging import get_logger
from arkhon.evidence.collector import EvidenceCollector, EvidenceDraft
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
    def __init__(self, store: EvidenceStore, collector: EvidenceCollector) -> None:
        self._store = store
        self._collector = collector

    def run(
        self, *, domain: str, commit_sha: str, runners: Sequence[Runner],
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
                results.append(result)
            except Exception as exc:
                logger.exception("runner %s crashed", runner.name)
                results.append(RunnerResult(
                    runner=runner.name, outcome=RunnerOutcome.BLOCKED,
                    reason=f"runner crashed: {type(exc).__name__}: {exc}", artifacts=[],
                ))
        status = self._aggregate_status(results)
        evidence_id = self._record_evidence(
            domain=domain, commit_sha=commit_sha, results=results, status=status,
        )
        return VerificationRun(
            run_id=run_id, domain=domain, commit_sha=commit_sha,
            results=results, status=status, evidence_id=evidence_id,
        )

    @staticmethod
    def _aggregate_status(results: list[RunnerResult]) -> str:
        if any(result.outcome == RunnerOutcome.FAIL for result in results):
            return STATUS_FAIL
        if any(result.outcome == RunnerOutcome.BLOCKED for result in results):
            return STATUS_BLOCKED
        return STATUS_PASS

    def _record_evidence(
        self, *, domain: str, commit_sha: str, results: list[RunnerResult], status: str,
    ) -> str:
        draft: EvidenceDraft = self._collector.new_evidence(
            source="arkhon", source_version="0.1.0.dev1",
            commit_sha=commit_sha, status=status,
        )
        for result in results:
            for artifact in result.artifacts:
                draft.add_artifact(artifact)
        if not draft.artifacts:
            raise VerificationError(
                "verification produced no artifacts; evidence cannot be recorded as verified"
            )
        draft.summary = {
            "pass": sum(r.outcome == RunnerOutcome.PASS for r in results),
            "fail": sum(r.outcome == RunnerOutcome.FAIL for r in results),
            "blocked": sum(r.outcome == RunnerOutcome.BLOCKED for r in results),
        }
        evidence = draft.to_evidence()
        self._store.write(domain, evidence)
        return str(evidence["evidence_id"])
