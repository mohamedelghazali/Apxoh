"""End-to-end CLI integration tests for GENCODE-GOV governance upgrades."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from gencode_gov.cli import main

_GIT = shutil.which("git") or "/usr/bin/git"


def _init_governed_python_project(root: Path) -> str:
    subprocess.run([_GIT, "init", "-q"], cwd=root, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.email", "lead@example.invalid"], cwd=root, check=True, timeout=10
    )
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.name", "eng_reviewer_role"], cwd=root, check=True, timeout=10
    )
    (root / "pyproject.toml").write_text(
        '[project]\nname = "tiny-svc"\nversion = "0.1.0"\n'
        "[tool.coverage.report]\nfail_under = 90\n",
        encoding="utf-8",
    )
    (root / "requirements.lock").write_text(
        f"pyyaml==6.0.2 --hash=sha256:{'a' * 64}\n",
        encoding="utf-8",
    )
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [0.1.0] - 2026-11-27\n- Initial governed release.\n",
        encoding="utf-8",
    )
    (root / "src" / "tiny_svc").mkdir(parents=True)
    (root / "src" / "tiny_svc" / "__init__.py").write_text(
        '__version__ = "0.1.0"\n\ndef greet(name: str) -> str:\n    return f"hi {name}"\n',
        encoding="utf-8",
    )
    (root / "tests").mkdir()
    (root / "tests" / "test_greet.py").write_text(
        "from tiny_svc import greet\n\n"
        "def test_greet() -> None:\n    assert greet('a') == 'hi a'\n",
        encoding="utf-8",
    )
    gov = root / ".gencode-gov"
    gov.mkdir()
    (gov / "config.yaml").write_text(
        "formats:\n  report:\n    - json\n    - markdown\n    - html\n",
        encoding="utf-8",
    )
    subprocess.run([_GIT, "add", "-A"], cwd=root, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-q", "-m", "feat: initial governed project"],
        cwd=root,
        check=True,
        timeout=10,
    )
    res = subprocess.run(  # noqa: S603
        [_GIT, "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    return res.stdout.strip()


def test_cli_validate_inspect_tools_attest_diff_drift_and_reports(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
    monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)

    sha = _init_governed_python_project(tmp_path)

    # 1. inspect --tools --json
    rc_ins = main(["inspect", str(tmp_path), "--tools", "--json"])
    assert rc_ins == 0
    ins_data = json.loads(capsys.readouterr().out)
    assert "tools" in ins_data

    # 2. attest via main CLI
    rc_att = main(
        [
            "attest",
            str(tmp_path),
            "--rule",
            "SE-ARC-001",
            "--reviewer",
            "reviewer_role_one",
            "--role",
            "Architecture Lead",
            "--rationale",
            "Reviewed library boundaries and approved for release.",
            "--commit",
            sha,
            "--json",
        ]
    )
    assert rc_att == 0
    att_out = json.loads(capsys.readouterr().out)
    assert att_out["commit_sha"] == sha

    # 3. diff-check via main CLI
    rc_diff = main(["diff-check", str(tmp_path), "--json"])
    assert rc_diff == 0
    diff_out = json.loads(capsys.readouterr().out)
    assert diff_out["status"] == "PASS"

    # 4. drift via main CLI (Notice: .gencode-gov/evidence & state exist untracked, testing GAP-03!)
    rc_drift = main(["drift", str(tmp_path), "--json"])
    assert rc_drift == 0
    drift_out = json.loads(capsys.readouterr().out)
    assert drift_out["current"]["python_files"] >= 1

    # 5. assess --json ignores untracked .gencode-gov/ runtime outputs (GAP-03)
    rc_assess = main(["assess", str(tmp_path), "--json"])
    assert rc_assess in {0, 1}
    assess_raw = capsys.readouterr().out
    assess_json = json.loads(assess_raw)
    assert "decision" in assess_json or "verdict" in assess_json or "score" in assess_json

    # 6. report --format html and --format sarif
    html_file = tmp_path / ".gencode-gov" / "reports" / "latest.html"
    sarif_file = tmp_path / ".gencode-gov" / "reports" / "latest.sarif"
    assert main(["report", str(tmp_path), "--format", "html", "--output", str(html_file)]) == 0
    capsys.readouterr()
    assert html_file.is_file()
    assert "GENCODE-GOV Governance Assessment" in html_file.read_text(encoding="utf-8")

    assert main(["report", str(tmp_path), "--format", "sarif", "--output", str(sarif_file)]) == 0
    capsys.readouterr()
    sarif_doc = json.loads(sarif_file.read_text(encoding="utf-8"))
    assert sarif_doc["version"] == "2.1.0"
