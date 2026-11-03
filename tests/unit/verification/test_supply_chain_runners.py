"""Supply-chain runner tests: real command contracts, fail-closed behavior and path safety."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from arkhon.verification.runners.base import RunnerOutcome
from arkhon.verification.runners.supply_chain_runner import (
    SupplyChainAttestationRunner,
    SyftRunner,
    _commit_sha,
    _safe_directory,
    _safe_file,
)

SHA = "a" * 40


def _bom() -> dict:
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.7",
        "version": 1,
        "metadata": {"tools": {"components": [{"name": "syft", "version": "1.0.0"}]}},
        "components": [{"type": "library", "name": "demo", "version": "1.0"}],
    }


def _config(root: Path) -> None:
    for name in ("dist/app.whl", "dist/provenance.intoto.jsonl", "dist/app.sigstore.json"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture", encoding="utf-8")
    config = {
        "artifact": "dist/app.whl",
        "provenance": "dist/provenance.intoto.jsonl",
        "signature_bundle": "dist/app.sigstore.json",
        "source_tag": "v1.2.3",
    }
    config_path = root / ".arkhon" / "supply-chain.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config), encoding="utf-8")


def test_safe_file_rejects_absolute_escape_and_missing(tmp_path: Path) -> None:
    assert _safe_file(tmp_path, None) is None
    assert _safe_file(tmp_path, "/etc/passwd") is None
    assert _safe_file(tmp_path, "../outside") is None
    assert _safe_file(tmp_path, "missing") is None
    good = tmp_path / "good.txt"
    good.write_text("ok", encoding="utf-8")
    assert _safe_file(tmp_path, "good.txt") == good.resolve()


def test_safe_file_rejects_symlink(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.write_text("ok", encoding="utf-8")
    link = tmp_path / "link.txt"
    link.symlink_to(target)
    assert _safe_file(tmp_path, "link.txt") is None


def test_syft_runner_blocks_when_git_or_syft_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = SyftRunner()
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: None
    )
    assert runner.run(tmp_path).outcome == RunnerOutcome.BLOCKED
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: SHA
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which", lambda name: None
    )
    result = runner.run(tmp_path)
    assert result.outcome == RunnerOutcome.BLOCKED
    assert "Syft executable" in result.reason


def test_syft_runner_generates_commit_bound_cyclonedx(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: SHA
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which", lambda name: "/usr/bin/syft"
    )

    def fake_run(command, **kwargs):
        assert command[1] == f"dir:{tmp_path.resolve()}"
        assert command[-1] == "cyclonedx-json"
        return subprocess.CompletedProcess(command, 0, json.dumps(_bom()), "")

    monkeypatch.setattr("arkhon.verification.runners.supply_chain_runner.subprocess.run", fake_run)
    result = SyftRunner().run(tmp_path)
    assert result.outcome == RunnerOutcome.PASS
    assert result.artifacts[0].is_file()
    data = json.loads(result.artifacts[0].read_text(encoding="utf-8"))
    assert {"name": "arkhon:commit-sha", "value": SHA} in data["metadata"]["component"][
        "properties"
    ]


def test_syft_runner_blocks_on_command_failure_and_invalid_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: SHA
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which", lambda name: "/usr/bin/syft"
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 2, "", "syft failed"),
    )
    assert "exited with 2" in SyftRunner().run(tmp_path).reason
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, "not json", ""),
    )
    assert "invalid JSON" in SyftRunner().run(tmp_path).reason


@pytest.mark.parametrize(
    ("bom", "message"),
    [
        ([], "not CycloneDX"),
        ({"bomFormat": "SPDX"}, "not CycloneDX"),
        ({"bomFormat": "CycloneDX", "specVersion": "1.3"}, "unsupported"),
        (
            {"bomFormat": "CycloneDX", "specVersion": "1.6", "metadata": [], "components": []},
            "metadata/components",
        ),
        (
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.6",
                "metadata": {"tools": []},
                "components": [],
            },
            "does not identify Syft",
        ),
    ],
)
def test_syft_runner_rejects_untrusted_bom_shapes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bom: object, message: str
) -> None:
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: SHA
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which", lambda name: "/usr/bin/syft"
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, json.dumps(bom), ""),
    )
    assert message.lower() in SyftRunner().run(tmp_path).reason.lower()


def test_syft_runner_handles_process_and_filesystem_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: SHA
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which", lambda name: "/usr/bin/syft"
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.subprocess.run",
        lambda *a, **k: (_ for _ in ()).throw(OSError("process failed")),
    )
    assert "execution failed" in SyftRunner().run(tmp_path).reason
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, json.dumps(_bom()), ""),
    )
    original = Path.mkdir

    def fail(path: Path, *args, **kwargs):
        if path.name == "supply-chain":
            raise OSError("read-only")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", fail)
    assert "output directory escapes" in SyftRunner().run(tmp_path).reason


def test_attestation_runner_blocks_without_config_or_tools(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: SHA
    )
    runner = SupplyChainAttestationRunner()
    assert "config is missing" in runner.run(tmp_path).reason
    _config(tmp_path)
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._tag_commit_sha",
        lambda _root, _tag: SHA,
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which", lambda name: None
    )
    assert "verifier(s) not found" in runner.run(tmp_path).reason


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        "[]",
        json.dumps({"artifact": "../escape", "provenance": "x", "signature_bundle": "y"}),
    ],
)
def test_attestation_runner_rejects_invalid_config_and_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, raw: str
) -> None:
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: SHA
    )
    config = tmp_path / ".arkhon" / "supply-chain.json"
    config.parent.mkdir()
    config.write_text(raw, encoding="utf-8")
    result = SupplyChainAttestationRunner().run(tmp_path)
    assert result.outcome == RunnerOutcome.BLOCKED


def test_attestation_runner_executes_both_verifiers_and_writes_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config(tmp_path)
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: SHA
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which",
        lambda name: f"/usr/bin/{name}",
    )
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, "Verified", "")

    monkeypatch.setattr("arkhon.verification.runners.supply_chain_runner.subprocess.run", fake_run)
    result = SupplyChainAttestationRunner().run(tmp_path)
    assert result.outcome == RunnerOutcome.PASS
    assert len(commands) == 2
    assert commands[0][1] == "verify-artifact"
    assert commands[0][commands[0].index("--source-tag") + 1] == "v1.2.3"
    assert commands[1][1] == "verify-blob"
    assert "v1\\.2\\.3" in commands[1][commands[1].index("--certificate-identity-regexp") + 1]
    report = next(path for path in result.artifacts if path.name.endswith(".attestation.json"))
    assert (
        json.loads(report.read_text(encoding="utf-8"))["verification"]["sigstore"]["verified"]
        is True
    )


@pytest.mark.parametrize("failure", ["slsa", "cosign", "spawn"])
def test_attestation_runner_fails_or_blocks_on_verifier_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    _config(tmp_path)
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: SHA
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which",
        lambda name: f"/usr/bin/{name}",
    )
    calls = 0

    def fake_run(command, **kwargs):
        nonlocal calls
        calls += 1
        if failure == "spawn" and calls == 1:
            raise OSError("spawn failed")
        return subprocess.CompletedProcess(
            command,
            1 if failure == "slsa" and calls == 1 or failure == "cosign" and calls == 2 else 0,
            "",
            "invalid",
        )

    monkeypatch.setattr("arkhon.verification.runners.supply_chain_runner.subprocess.run", fake_run)
    result = SupplyChainAttestationRunner().run(tmp_path)
    assert result.outcome == (RunnerOutcome.BLOCKED if failure == "spawn" else RunnerOutcome.FAIL)


def test_attestation_runner_reports_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config(tmp_path)
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: SHA
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which",
        lambda name: f"/usr/bin/{name}",
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, "", ""),
    )
    original = Path.mkdir

    def fail(path: Path, *args, **kwargs):
        if path.name == "supply-chain":
            raise OSError("read-only")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", fail)
    assert "report directory escapes" in SupplyChainAttestationRunner().run(tmp_path).reason


def test_commit_sha_resolution_failures_and_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which", lambda _name: None
    )
    assert _commit_sha(tmp_path) is None
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which", lambda _name: "/usr/bin/git"
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.subprocess.run",
        lambda *a, **k: (_ for _ in ()).throw(OSError("git error")),
    )
    assert _commit_sha(tmp_path) is None
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, "not-a-sha", ""),
    )
    assert _commit_sha(tmp_path) is None
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, SHA, ""),
    )
    assert _commit_sha(tmp_path) == SHA


def test_safe_directory_rejects_project_escape(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "outside"
    assert _safe_directory(root, outside) is None


def test_syft_runner_rejects_symlinked_output_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: SHA
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which",
        lambda _name: "/usr/bin/syft",
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, json.dumps(_bom()), ""),
    )
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    target = tmp_path / ".arkhon" / "reports"
    target.mkdir(parents=True)
    (target / "supply-chain").symlink_to(outside, target_is_directory=True)
    result = SyftRunner().run(tmp_path)
    assert result.outcome == RunnerOutcome.BLOCKED
    assert "escapes project root" in result.reason


def test_syft_runner_rejects_symlinked_sbom_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: SHA
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which", lambda _name: "/usr/bin/syft"
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, json.dumps(_bom()), ""),
    )
    output_dir = tmp_path / ".arkhon" / "reports" / "supply-chain"
    output_dir.mkdir(parents=True)
    outside = tmp_path.parent / f"{tmp_path.name}-outside-sbom.json"
    outside.write_text("outside", encoding="utf-8")
    (output_dir / f"sbom-{SHA[:12]}.cdx.json").symlink_to(outside)
    result = SyftRunner().run(tmp_path)
    assert result.outcome == RunnerOutcome.BLOCKED
    assert "symlinked SBOM" in result.reason


def test_syft_runner_blocks_when_sbom_cannot_be_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: SHA
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which", lambda _name: "/usr/bin/syft"
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, json.dumps(_bom()), ""),
    )
    original = Path.write_text

    def fail(path: Path, *args, **kwargs):
        if path.name.endswith(".cdx.json"):
            raise OSError("read-only")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail)
    result = SyftRunner().run(tmp_path)
    assert result.outcome == RunnerOutcome.BLOCKED
    assert "cannot persist SBOM" in result.reason


def test_attestation_runner_blocks_without_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: None
    )
    result = SupplyChainAttestationRunner().run(tmp_path)
    assert result.outcome == RunnerOutcome.BLOCKED
    assert "full Git commit SHA" in result.reason


def test_attestation_runner_rejects_symlinked_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config(tmp_path)
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: SHA
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which",
        lambda name: f"/usr/bin/{name}",
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, "", ""),
    )
    report_dir = tmp_path / ".arkhon" / "reports" / "supply-chain"
    report_dir.mkdir(parents=True)
    outside = tmp_path.parent / f"{tmp_path.name}-outside-attestation.json"
    outside.write_text("outside", encoding="utf-8")
    (report_dir / f"attestation-{SHA[:12]}.attestation.json").symlink_to(outside)
    result = SupplyChainAttestationRunner().run(tmp_path)
    assert result.outcome == RunnerOutcome.BLOCKED
    assert "symlinked attestation report" in result.reason


def test_attestation_runner_blocks_when_report_cannot_be_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config(tmp_path)
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: SHA
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which",
        lambda name: f"/usr/bin/{name}",
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, "", ""),
    )
    original = Path.write_text

    def fail(path: Path, *args, **kwargs):
        if path.name.endswith(".attestation.json"):
            raise OSError("read-only")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail)
    result = SupplyChainAttestationRunner().run(tmp_path)
    assert result.outcome == RunnerOutcome.BLOCKED
    assert "cannot persist attestation report" in result.reason


def test_tag_commit_sha_rejects_invalid_tag_and_missing_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from arkhon.verification.runners.supply_chain_runner import _tag_commit_sha

    assert _tag_commit_sha(tmp_path, "not-a-tag") is None
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which", lambda _name: None
    )
    assert _tag_commit_sha(tmp_path, "v1.2.3") is None


@pytest.mark.parametrize(
    ("output", "raises", "expected"),
    [
        (SHA, False, SHA),
        ("invalid", False, None),
        ("", True, None),
    ],
)
def test_tag_commit_sha_resolves_and_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    output: str,
    raises: bool,
    expected: str | None,
) -> None:
    from arkhon.verification.runners.supply_chain_runner import _tag_commit_sha

    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner.shutil.which",
        lambda _name: "/usr/bin/git",
    )

    def run(*args, **kwargs):
        if raises:
            raise OSError("git unavailable")
        return subprocess.CompletedProcess(args[0], 0, output, "")

    monkeypatch.setattr("arkhon.verification.runners.supply_chain_runner.subprocess.run", run)
    assert _tag_commit_sha(tmp_path, "v1.2.3") == expected


def test_attestation_runner_blocks_when_tag_points_to_another_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config(tmp_path)
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._commit_sha", lambda _root: SHA
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.supply_chain_runner._tag_commit_sha",
        lambda _root, _tag: "b" * 40,
    )
    result = SupplyChainAttestationRunner().run(tmp_path)
    assert result.outcome == RunnerOutcome.BLOCKED
    assert "does not resolve to the checked-out commit" in result.reason
