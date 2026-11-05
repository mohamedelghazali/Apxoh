from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from arkhon.verification.runners.base import RunnerOutcome
from arkhon.verification.runners.mypy_runner import MypyRunner
from arkhon.verification.runners.pytest_runner import PytestRunner
from arkhon.verification.runners.ruff_runner import RuffRunner


def _completed(args, code: int = 0, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(args, code, stdout, stderr)


def _pytest_run(monkeypatch, tmp_path: Path, *, xml: str | None, code: int = 0):
    tests = tmp_path / "tests"
    tests.mkdir(exist_ok=True)

    def run(command, **kwargs):
        if xml is not None:
            target = Path(command[command.index("--junit-xml") + 1])
            target.write_text(xml, encoding="utf-8")
        return _completed(command, code, "", "")

    monkeypatch.setattr("arkhon.verification.runners.pytest_runner.subprocess.run", run)
    return PytestRunner().run(tmp_path)


def test_pytest_runner_timeout_start_and_missing_xml(tmp_path: Path, monkeypatch) -> None:
    with pytest.raises(ValueError):
        PytestRunner(0)
    assert PytestRunner().run(tmp_path).outcome == RunnerOutcome.BLOCKED
    (tmp_path / "tests").mkdir()
    monkeypatch.setattr(
        "arkhon.verification.runners.pytest_runner.subprocess.run",
        lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired("pytest", 1)),
    )
    assert "timed out" in PytestRunner().run(tmp_path).reason
    monkeypatch.setattr(
        "arkhon.verification.runners.pytest_runner.subprocess.run",
        lambda *a, **k: (_ for _ in ()).throw(OSError("missing interpreter")),
    )
    assert "failed to start" in PytestRunner().run(tmp_path).reason
    monkeypatch.setattr(
        "arkhon.verification.runners.pytest_runner.subprocess.run",
        lambda command, **kwargs: _completed(command, 2, stderr="no XML"),
    )
    assert "no JUnit XML" in PytestRunner().run(tmp_path).reason


def test_pytest_runner_xml_validation_persistence_and_outcomes(tmp_path: Path, monkeypatch) -> None:
    assert "invalid JUnit XML" in _pytest_run(monkeypatch, tmp_path, xml="<broken").reason
    assert (
        "collected no tests"
        in _pytest_run(monkeypatch, tmp_path, xml='<testsuite tests="0"/>').reason
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.pytest_runner.shutil.copy2",
        lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")),
    )
    result = _pytest_run(
        monkeypatch, tmp_path, xml='<testsuite tests="1" failures="0" errors="0"/>'
    )
    assert result.outcome == RunnerOutcome.BLOCKED
    assert "cannot persist" in result.reason
    monkeypatch.undo()
    failed = _pytest_run(
        monkeypatch,
        tmp_path,
        xml='<testsuite tests="1" failures="1" errors="0" skipped="0"/>',
        code=1,
    )
    assert failed.outcome == RunnerOutcome.FAIL
    passed = _pytest_run(
        monkeypatch, tmp_path, xml='<testsuite tests="1" failures="0" errors="0"/>'
    )
    assert passed.outcome == RunnerOutcome.PASS


def test_ruff_runner_all_execution_paths(tmp_path: Path, monkeypatch) -> None:
    with pytest.raises(ValueError):
        RuffRunner(0)
    monkeypatch.setattr("arkhon.verification.runners.ruff_runner.shutil.which", lambda _n: None)
    assert RuffRunner().run(tmp_path).outcome == RunnerOutcome.BLOCKED
    monkeypatch.setattr(
        "arkhon.verification.runners.ruff_runner.shutil.which", lambda _n: "/usr/bin/ruff"
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.ruff_runner.subprocess.run",
        lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired("ruff", 1)),
    )
    assert "timed out" in RuffRunner().run(tmp_path).reason
    monkeypatch.setattr(
        "arkhon.verification.runners.ruff_runner.subprocess.run",
        lambda *a, **k: (_ for _ in ()).throw(OSError("spawn failed")),
    )
    assert "failed to start" in RuffRunner().run(tmp_path).reason
    monkeypatch.setattr(
        "arkhon.verification.runners.ruff_runner.subprocess.run",
        lambda command, **kwargs: _completed(command, 2, "not-json"),
    )
    assert "invalid Ruff JSON" in RuffRunner().run(tmp_path).reason
    monkeypatch.setattr(
        "arkhon.verification.runners.ruff_runner.subprocess.run",
        lambda command, **kwargs: _completed(command, 2, "{}"),
    )
    assert "not an array" in RuffRunner().run(tmp_path).reason
    monkeypatch.setattr(
        "arkhon.verification.runners.ruff_runner.subprocess.run",
        lambda command, **kwargs: _completed(command, 0, "[]"),
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.ruff_runner.shutil.copy2",
        lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")),
    )
    assert "cannot persist" in RuffRunner().run(tmp_path).reason
    monkeypatch.undo()
    monkeypatch.setattr(
        "arkhon.verification.runners.ruff_runner.shutil.which", lambda _n: "/usr/bin/ruff"
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.ruff_runner.subprocess.run",
        lambda command, **kwargs: _completed(command, 0, "[]"),
    )
    assert RuffRunner().run(tmp_path).outcome == RunnerOutcome.PASS
    monkeypatch.setattr(
        "arkhon.verification.runners.ruff_runner.subprocess.run",
        lambda command, **kwargs: _completed(command, 1, '[{"code":"E501"}]'),
    )
    assert RuffRunner().run(tmp_path).outcome == RunnerOutcome.FAIL
    monkeypatch.setattr(
        "arkhon.verification.runners.ruff_runner.subprocess.run",
        lambda command, **kwargs: _completed(command, 3, "[]", "internal"),
    )
    assert RuffRunner().run(tmp_path).outcome == RunnerOutcome.BLOCKED


def test_mypy_runner_all_execution_paths(tmp_path: Path, monkeypatch) -> None:
    with pytest.raises(ValueError):
        MypyRunner(0)
    monkeypatch.setattr("arkhon.verification.runners.mypy_runner.shutil.which", lambda _n: None)
    assert MypyRunner().run(tmp_path).outcome == RunnerOutcome.BLOCKED
    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.shutil.which", lambda _n: "/usr/bin/mypy"
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.subprocess.run",
        lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired("mypy", 1)),
    )
    assert "timed out" in MypyRunner().run(tmp_path).reason
    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.subprocess.run",
        lambda *a, **k: (_ for _ in ()).throw(OSError("spawn failed")),
    )
    assert "failed to start" in MypyRunner().run(tmp_path).reason
    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.subprocess.run",
        lambda command, **kwargs: _completed(command, 0, "Success"),
    )
    original_open = Path.open

    def fail_content_addressed_write(path: Path, mode: str = "r", *args, **kwargs):
        if mode == "xb":
            raise OSError("read only")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_content_addressed_write)
    assert "cannot persist" in MypyRunner().run(tmp_path).reason
    monkeypatch.undo()
    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.shutil.which", lambda _n: "/usr/bin/mypy"
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.subprocess.run",
        lambda command, **kwargs: _completed(command, 0, "Success"),
    )
    assert MypyRunner().run(tmp_path).outcome == RunnerOutcome.PASS
    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.subprocess.run",
        lambda command, **kwargs: _completed(command, 1, "type error"),
    )
    assert MypyRunner().run(tmp_path).outcome == RunnerOutcome.FAIL
    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.subprocess.run",
        lambda command, **kwargs: _completed(command, 2, "internal error"),
    )
    assert MypyRunner().run(tmp_path).outcome == RunnerOutcome.BLOCKED

def test_mypy_runner_reuses_immutable_content_addressed_artifacts(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.shutil.which", lambda _name: "/usr/bin/mypy"
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.subprocess.run",
        lambda command, **kwargs: _completed(command, 0, "same mypy output"),
    )

    first = MypyRunner().run(tmp_path)
    second = MypyRunner().run(tmp_path)
    assert first.outcome == RunnerOutcome.PASS
    assert second.outcome == RunnerOutcome.PASS
    assert first.artifacts == second.artifacts
    artifact = first.artifacts[0]
    assert artifact.name.startswith("mypy-")
    assert artifact.read_text(encoding="utf-8") == "same mypy output"

    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.subprocess.run",
        lambda command, **kwargs: _completed(command, 0, "new mypy output"),
    )
    third = MypyRunner().run(tmp_path)
    assert third.outcome == RunnerOutcome.PASS
    assert third.artifacts[0] != artifact
    assert artifact.read_text(encoding="utf-8") == "same mypy output"

def test_mypy_runner_blocks_tampered_content_addressed_artifact(
    tmp_path: Path, monkeypatch
) -> None:
    import hashlib

    payload = b"expected output"
    digest = hashlib.sha256(payload).hexdigest()
    target = tmp_path / ".arkhon" / "evidence" / "code-quality" / f"mypy-{digest}.txt"
    target.parent.mkdir(parents=True)
    target.write_text("tampered", encoding="utf-8")
    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.shutil.which", lambda _name: "/usr/bin/mypy"
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.subprocess.run",
        lambda command, **kwargs: _completed(command, 0, payload.decode("utf-8")),
    )

    result = MypyRunner().run(tmp_path)
    assert result.outcome == RunnerOutcome.BLOCKED
    assert "does not match its digest" in result.reason

def test_mypy_runner_refuses_symlinked_content_addressed_artifact(
    tmp_path: Path, monkeypatch
) -> None:
    import hashlib

    payload = b"symlinked output"
    digest = hashlib.sha256(payload).hexdigest()
    target_dir = tmp_path / ".arkhon" / "evidence" / "code-quality"
    target_dir.mkdir(parents=True)
    victim = tmp_path / "victim.txt"
    victim.write_bytes(payload)
    target = target_dir / f"mypy-{digest}.txt"
    target.symlink_to(victim)
    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.shutil.which", lambda _name: "/usr/bin/mypy"
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.subprocess.run",
        lambda command, **kwargs: _completed(command, 0, payload.decode("utf-8")),
    )

    result = MypyRunner().run(tmp_path)
    assert result.outcome == RunnerOutcome.BLOCKED
    assert "refusing symlinked" in result.reason

