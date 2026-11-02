"""Unit tests for the verification engine and runner contracts."""
from __future__ import annotations

from pathlib import Path

import pytest

from arkhon.core.errors import VerificationError
from arkhon.evidence.collector import EvidenceCollector
from arkhon.evidence.store import EvidenceStore
from arkhon.verification.engine import VerificationEngine
from arkhon.verification.runners.base import Runner, RunnerOutcome, RunnerResult


class FakePassRunner(Runner):
    @property
    def name(self) -> str:
        return "fake-pass"

    def run(self, project_root: Path) -> RunnerResult:
        artifact = project_root / "fake-pass.txt"
        artifact.write_text("verified", encoding="utf-8")
        return RunnerResult(self.name, RunnerOutcome.PASS, artifacts=[artifact])


class FakeFailRunner(Runner):
    @property
    def name(self) -> str:
        return "fake-fail"

    def run(self, project_root: Path) -> RunnerResult:
        artifact = project_root / "fake-fail.txt"
        artifact.write_text("failed", encoding="utf-8")
        return RunnerResult(self.name, RunnerOutcome.FAIL, "forced failure", [artifact])


class FakeBlockedRunner(Runner):
    @property
    def name(self) -> str:
        return "fake-blocked"

    def run(self, project_root: Path) -> RunnerResult:
        return RunnerResult(self.name, RunnerOutcome.BLOCKED, "missing prerequisite")


class FakeCrashedRunner(Runner):
    @property
    def name(self) -> str:
        return "fake-crashed"

    def run(self, project_root: Path) -> RunnerResult:
        raise RuntimeError("simulated runner crash")


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / ".arkhon" / "evidence").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def engine(project: Path) -> VerificationEngine:
    return VerificationEngine(EvidenceStore(project), EvidenceCollector(root=project))


def test_engine_requires_runners(engine: VerificationEngine, project: Path) -> None:
    with pytest.raises(VerificationError, match="no runners"):
        engine.run(domain="testing", commit_sha="a" * 40, runners=[], project_root=project)


def test_engine_rejects_bad_sha(engine: VerificationEngine, project: Path) -> None:
    with pytest.raises(VerificationError, match="invalid commit SHA"):
        engine.run(domain="testing", commit_sha="not-a-sha", runners=[FakePassRunner()], project_root=project)


def test_engine_passes(engine: VerificationEngine, project: Path) -> None:
    run = engine.run(domain="testing", commit_sha="a" * 40, runners=[FakePassRunner()], project_root=project)
    assert run.status == "PASS"
    assert len(run.results) == 1


def test_engine_fails(engine: VerificationEngine, project: Path) -> None:
    run = engine.run(domain="testing", commit_sha="b" * 40, runners=[FakePassRunner(), FakeFailRunner()], project_root=project)
    assert run.status == "FAIL"


def test_engine_blocked(engine: VerificationEngine, project: Path) -> None:
    run = engine.run(domain="testing", commit_sha="c" * 40, runners=[FakePassRunner(), FakeBlockedRunner()], project_root=project)
    assert run.status == "BLOCKED"


def test_engine_handles_crashed_runner(engine: VerificationEngine, project: Path) -> None:
    run = engine.run(domain="testing", commit_sha="d" * 40, runners=[FakeCrashedRunner()], project_root=project)
    assert run.status == "BLOCKED"
    assert "crashed" in run.results[0].reason


def test_engine_writes_evidence(engine: VerificationEngine, project: Path) -> None:
    run = engine.run(domain="testing", commit_sha="e" * 40, runners=[FakePassRunner()], project_root=project)
    assert run.evidence_id.startswith("EVID-ARKHON-")
    assert list((project / ".arkhon" / "evidence" / "testing").glob("*.json"))
