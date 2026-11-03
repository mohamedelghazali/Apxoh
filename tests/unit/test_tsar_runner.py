# ruff: noqa: I001
from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from arkhon.evidence.integrity import sha256_of
from arkhon.integrations.tsar.adapter import TsarAdapter
from arkhon.integrations.tsar.verifier import REQUIRED_RULE_IDS
from arkhon.verification.runners.base import RunnerOutcome
from arkhon.verification.runners.tsar_runner import TsarRunner


SHA = "a" * 40


def _git(monkeypatch: pytest.MonkeyPatch, output: str = SHA) -> None:
    monkeypatch.setattr("arkhon.verification.runners.tsar_runner.shutil.which",
                        lambda _name: "/usr/bin/git")
    monkeypatch.setattr(
        "arkhon.verification.runners.tsar_runner.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, output, ""),
    )


def _payload(root: Path, status: str = "PASS") -> dict:
    artifact = root / "scan.json"
    artifact.write_text("{}", encoding="utf-8")
    return {
        "evidence_id": "EVID-TSAR-1",
        "tsar_version": "1.2.0",
        "commit_sha": SHA,
        "executed_at": "2026-11-03T00:00:00Z",
        "status": status,
        "rule_ids": list(REQUIRED_RULE_IDS),
        "summary": {"critical": 0, "high": 0},
        "artifacts": [{"path": "scan.json", "sha256": sha256_of(artifact)}],
    }


def test_tsar_runner_requires_positive_timeout_and_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ValueError):
        TsarRunner(0)
    monkeypatch.setattr("arkhon.verification.runners.tsar_runner.shutil.which",
                        lambda _name: None)
    result = TsarRunner().run(tmp_path)
    assert result.outcome == RunnerOutcome.BLOCKED
    assert "git executable" in result.reason


@pytest.mark.parametrize("error", [
    subprocess.CalledProcessError(1, "git"),
    subprocess.TimeoutExpired("git", 1),
    OSError("git unavailable"),
])
def test_tsar_runner_git_resolution_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    monkeypatch.setattr("arkhon.verification.runners.tsar_runner.shutil.which",
                        lambda _name: "/usr/bin/git")
    def fail(*args: object, **kwargs: object) -> None:
        raise error
    monkeypatch.setattr("arkhon.verification.runners.tsar_runner.subprocess.run", fail)
    assert "cannot resolve commit SHA" in TsarRunner().run(tmp_path).reason


def test_tsar_runner_rejects_invalid_sha_and_adapter_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _git(monkeypatch, "not-a-sha")
    assert "invalid commit SHA" in TsarRunner().run(tmp_path).reason
    _git(monkeypatch)
    monkeypatch.setattr(
        TsarAdapter,
        "audit",
        lambda _self, _root, _sha: SimpleNamespace(
            ok=False, reason="scanner unavailable", payload={}, artifacts=[]
        ),
    )
    result = TsarRunner().run(tmp_path)
    assert result.outcome == RunnerOutcome.BLOCKED
    assert result.reason == "scanner unavailable"


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("PASS", RunnerOutcome.PASS),
        ("FAIL", RunnerOutcome.FAIL),
        ("BLOCKED", RunnerOutcome.BLOCKED),
    ],
)
def test_tsar_runner_maps_verified_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status: str,
    expected: RunnerOutcome,
) -> None:
    _git(monkeypatch)
    payload = _payload(tmp_path, status)
    monkeypatch.setattr(
        TsarAdapter,
        "audit",
        lambda _self, _root, _sha: SimpleNamespace(
            ok=True, reason="", payload=payload, artifacts=[]
        ),
    )
    result = TsarRunner().run(tmp_path)
    assert result.outcome == expected


def test_tsar_runner_blocks_untrusted_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _git(monkeypatch)
    monkeypatch.setattr(
        TsarAdapter,
        "audit",
        lambda _self, _root, _sha: SimpleNamespace(
            ok=True, reason="", payload={"status": "PASS"}, artifacts=[]
        ),
    )
    result = TsarRunner().run(tmp_path)
    assert result.outcome == RunnerOutcome.BLOCKED
    assert "verification failed" in result.reason


def test_tsar_runner_maps_critical_findings_to_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _git(monkeypatch)
    payload = _payload(tmp_path)
    payload["summary"]["critical"] = 1
    monkeypatch.setattr(
        TsarAdapter,
        "audit",
        lambda _self, _root, _sha: SimpleNamespace(
            ok=True, reason="", payload=payload, artifacts=[]
        ),
    )
    result = TsarRunner().run(tmp_path)
    assert result.outcome == RunnerOutcome.FAIL
    assert "critical/high" in result.reason
