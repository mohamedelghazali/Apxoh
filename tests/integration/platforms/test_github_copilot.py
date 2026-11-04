"""Tests for the GitHub Copilot platform adapter.

Copilot cannot be tested end-to-end (Apxoh cannot call it). Tests

verify:

  * The adapter installs the instructions file.

  * The adapter verifies the file matches expected content.

  * The adapter reports itself as "configured" only.

"""

from __future__ import annotations

from pathlib import Path

import pytest

import yaml

from arkhon.integrations.platforms.github_copilot.adapter import (
    INSTRUCTIONS_REL_PATH,
    GitHubCopilotAdapter,
    _INSTRUCTIONS_CONTENT,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

PLATFORM_DIR = REPO_ROOT / "integrations" / "platforms" / "github-copilot"


def test_info() -> None:
    info = GitHubCopilotAdapter().info

    assert info.id == "github-copilot"

    assert info.kind == "platform"


def test_health_check_with_prompt() -> None:
    assert GitHubCopilotAdapter().health_check() is True


def test_install_creates_file(copilot_project: Path) -> None:
    adapter = GitHubCopilotAdapter()

    result = adapter.install(copilot_project)

    assert result.ok

    target = copilot_project / INSTRUCTIONS_REL_PATH

    assert target.is_file()

    assert target.stat().st_size > 0



def test_install_is_idempotent(copilot_project: Path) -> None:
    adapter = GitHubCopilotAdapter()
    first = adapter.install(copilot_project)
    second = adapter.install(copilot_project)
    assert first.ok and second.ok
    assert first.payload["sha256"] == second.payload["sha256"]


def test_install_preserves_existing_user_content(copilot_project: Path) -> None:
    target = copilot_project / INSTRUCTIONS_REL_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    original = "# User instructions\\n"
    target.write_text(original, encoding="utf-8")
    result = GitHubCopilotAdapter().install(copilot_project)
    assert not result.ok
    assert "refusing to overwrite" in result.reason
    assert target.read_text(encoding="utf-8") == original

def test_verify_passes_after_install(copilot_project: Path) -> None:
    adapter = GitHubCopilotAdapter()

    adapter.install(copilot_project)

    result = adapter.verify(copilot_project)

    assert result.ok

    assert "sha256" in result.payload


def test_verify_fails_without_file(copilot_project: Path) -> None:
    result = GitHubCopilotAdapter().verify(copilot_project)

    assert not result.ok

    assert "missing" in result.reason


def test_verify_fails_on_tampered_file(copilot_project: Path) -> None:
    adapter = GitHubCopilotAdapter()

    adapter.install(copilot_project)

    target = copilot_project / INSTRUCTIONS_REL_PATH

    target.write_text("tampered", encoding="utf-8")

    result = adapter.verify(copilot_project)

    assert not result.ok

    assert "does not match" in result.reason


def test_underlying_models_declared() -> None:
    path = PLATFORM_DIR / "underlying-models.yaml"

    assert path.is_file()

    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert data["verification_level"]["max_reachable"] == "configured"

    assert len(data["underlying_models"]) >= 1


def test_max_verification_is_configured() -> None:
    """The adapter must not claim Verified — it cannot verify Copilot."""

    path = PLATFORM_DIR / "underlying-models.yaml"

    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert data["verification_level"]["max_reachable"] == "configured"


def test_install_rejects_symlinked_github_directory(copilot_project: Path, tmp_path: Path) -> None:
    adapter = GitHubCopilotAdapter()
    external = tmp_path / "external"
    external.mkdir()
    (copilot_project / ".github").symlink_to(external, target_is_directory=True)

    result = adapter.install(copilot_project)

    assert not result.ok
    assert "symlinked .github" in result.reason
    assert list(external.iterdir()) == []


def test_install_rejects_symlinked_instructions_file(copilot_project: Path, tmp_path: Path) -> None:
    adapter = GitHubCopilotAdapter()
    target = copilot_project / INSTRUCTIONS_REL_PATH
    target.parent.mkdir(parents=True)
    external = tmp_path / "user-instructions.md"
    external.write_text("user content", encoding="utf-8")
    target.symlink_to(external)

    result = adapter.install(copilot_project)

    assert not result.ok
    assert "symlinked instructions" in result.reason
    assert external.read_text(encoding="utf-8") == "user content"


def test_install_rejects_non_file_target(copilot_project: Path) -> None:
    target = copilot_project / INSTRUCTIONS_REL_PATH
    target.parent.mkdir(parents=True)
    target.mkdir()

    result = GitHubCopilotAdapter().install(copilot_project)

    assert not result.ok
    assert "not a regular file" in result.reason


def test_install_reports_filesystem_error(
    copilot_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_mkdir = Path.mkdir

    def fail_mkdir(self: Path, *args: object, **kwargs: object) -> None:
        if self.name == ".github":
            raise OSError("simulated mkdir failure")
        return original_mkdir(self, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", fail_mkdir)

    result = GitHubCopilotAdapter().install(copilot_project)

    assert not result.ok
    assert "simulated mkdir failure" in result.reason


def test_install_handles_concurrent_matching_file(
    copilot_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = copilot_project / INSTRUCTIONS_REL_PATH
    original_open = Path.open

    def create_then_raise(\n        self: Path, mode: str = "r", *args: object, **kwargs: object\n    ):
        if self == target and mode == "xb":
            with original_open(self, "wb") as stream:
                stream.write(_INSTRUCTIONS_CONTENT.encode("utf-8"))
            raise FileExistsError("simulated concurrent creation")
        return original_open(self, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", create_then_raise)

    result = GitHubCopilotAdapter().install(copilot_project)

    assert result.ok


def test_install_handles_concurrent_different_file(
    copilot_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = copilot_project / INSTRUCTIONS_REL_PATH
    original_open = Path.open

    def create_then_raise(self, mode="r", *args, **kwargs):
        if self == target and mode == "xb":
            with original_open(self, "wb") as stream:
                stream.write(b"user content")
            raise FileExistsError("simulated concurrent creation")
        return original_open(self, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", create_then_raise)

    result = GitHubCopilotAdapter().install(copilot_project)

    assert not result.ok
    assert "appeared concurrently" in result.reason
    assert target.read_bytes() == b"user content"


def test_install_handles_unreadable_concurrent_file(
    copilot_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = copilot_project / INSTRUCTIONS_REL_PATH
    original_open = Path.open
    original_read_bytes = Path.read_bytes

    def create_then_raise(self, mode="r", *args, **kwargs):
        if self == target and mode == "xb":
            with original_open(self, "wb") as stream:
                stream.write(b"user content")
            raise FileExistsError("simulated concurrent creation")
        return original_open(self, mode, *args, **kwargs)

    def fail_read(self: Path) -> bytes:
        if self == target:
            raise OSError("simulated read failure")
        return original_read_bytes(self)

    monkeypatch.setattr(Path, "open", create_then_raise)
    monkeypatch.setattr(Path, "read_bytes", fail_read)

    result = GitHubCopilotAdapter().install(copilot_project)

    assert not result.ok
    assert "cannot verify instructions file" in result.reason


def test_verify_rejects_symlinked_instructions_file(copilot_project: Path, tmp_path: Path) -> None:
    target = copilot_project / INSTRUCTIONS_REL_PATH
    target.parent.mkdir(parents=True)
    external = tmp_path / "instructions.md"
    external.write_text("user content", encoding="utf-8")
    target.symlink_to(external)

    result = GitHubCopilotAdapter().verify(copilot_project)

    assert not result.ok
    assert "symlinked instructions" in result.reason


def test_verify_reports_read_error(
    copilot_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = GitHubCopilotAdapter()
    adapter.install(copilot_project)
    target = copilot_project / INSTRUCTIONS_REL_PATH
    original_read_bytes = Path.read_bytes

    def fail_read(self):
        if self == target:
            raise OSError("simulated read failure")
        return original_read_bytes(self)

    monkeypatch.setattr(Path, "read_bytes", fail_read)

    result = adapter.verify(copilot_project)

    assert not result.ok
    assert "cannot read instructions file" in result.reason
