"""Tests for the GitHub Copilot platform adapter.

Copilot cannot be tested end-to-end (Apxoh cannot call it). Tests

verify:

  * The adapter installs the instructions file.

  * The adapter verifies the file matches expected content.

  * The adapter reports itself as "configured" only.

"""

from __future__ import annotations

from pathlib import Path

import yaml

from arkhon.integrations.platforms.github_copilot.adapter import (
    INSTRUCTIONS_REL_PATH,
    GitHubCopilotAdapter,
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
