"""Heuristic secret-exposure checks for tracked Apxoh source and documentation."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"sk-ant-[A-Za-z0-9\-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
)


def _tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
    )
    return [
        REPO_ROOT / item.decode("utf-8")
        for item in result.stdout.split(b"\0")
        if item
    ]


def _scan_file(path: Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    findings = []
    for pattern in SECRET_PATTERNS:
        for match in pattern.finditer(content):
            findings.append(f"{path.relative_to(REPO_ROOT)}: {match.group(0)[:8]}...")
    return findings


def test_no_secret_patterns_in_tracked_python_and_markdown() -> None:
    candidates = [
        path for path in _tracked_files()
        if path.suffix.lower() in {".py", ".md"}
        and (
            "src" in path.relative_to(REPO_ROOT).parts
            or "integrations" in path.relative_to(REPO_ROOT).parts
            or "docs" in path.relative_to(REPO_ROOT).parts
        )
    ]
    findings = [finding for path in candidates for finding in _scan_file(path)]
    assert not findings, "\n".join(findings)


def test_no_root_environment_files_are_tracked() -> None:
    tracked = {path.relative_to(REPO_ROOT).as_posix() for path in _tracked_files()}
    forbidden = {".env", ".env.local", ".env.production"}
    assert not (tracked & forbidden)


def test_gitignore_covers_environment_files() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore
    assert ".env.*" in gitignore


def test_no_private_key_files_are_tracked() -> None:
    forbidden_extensions = {".pem", ".key", ".p12", ".pfx"}
    forbidden_names = {"id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}
    findings = []
    for path in _tracked_files():
        if path.suffix.lower() in forbidden_extensions or path.name in forbidden_names:
            findings.append(path.relative_to(REPO_ROOT).as_posix())
    assert not findings, f"private-key-like files are tracked: {findings}"
