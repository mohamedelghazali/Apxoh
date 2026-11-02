"""Static safety checks for repository integration adapters.

These checks are a conservative first layer, not a substitute for code review,
sandboxing, runtime policy enforcement, or integration-specific tests.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]

ADAPTER_GLOBS = (
    "src/arkhon/integrations/**/adapter.py",
    "src/arkhon/integrations/**/verifier.py",
    "integrations/**/adapter.py",
    "integrations/**/verifier.py",
)

FORBIDDEN_PATTERNS = {
    "hardcoded-secret": re.compile(
        r"""(?i)(api[_-]?key|secret|token|password)\s*=\s*['"][A-Za-z0-9_\-]{16,}['"]"""
    ),
    "eval-call": re.compile(r"\beval\s*\("),
    "exec-call": re.compile(r"\bexec\s*\("),
    "subprocess-shell-true": re.compile(r"subprocess\.\w+\([^)]*shell\s*=\s*True"),
}

APPROVED_NETWORK_DOMAINS = {
    "api.anthropic.com",
    "api.openai.com",
    "api.deepseek.com",
    "generativelanguage.googleapis.com",
    "api.moonshot.cn",
    "api.moonshot.ai",
    "dashscope.aliyuncs.com",
    "github.com",
    "objects.githubusercontent.com",
    "raw.githubusercontent.com",
    "localhost",
    "127.0.0.1",
    "example.com",
    "pypi.org",
    "files.pythonhosted.org",
    "apxoh.dev",
    "www.apache.org",
}


def discover_adapters() -> list[Path]:
    """Return unique adapter and verifier source files."""
    return sorted({path for pattern in ADAPTER_GLOBS for path in ROOT.glob(pattern)})


@pytest.fixture(params=discover_adapters(), ids=lambda path: str(path.relative_to(ROOT)))
def adapter_source(request: pytest.FixtureRequest) -> tuple[Path, str]:
    path = request.param
    return path, path.read_text(encoding="utf-8")


def test_adapter_inventory_is_not_empty() -> None:
    assert discover_adapters(), "No adapter/verifier files discovered; review the inventory."


def test_adapter_parses_as_python(adapter_source: tuple[Path, str]) -> None:
    path, source = adapter_source
    ast.parse(source, filename=str(path))


def test_adapter_has_no_forbidden_patterns(adapter_source: tuple[Path, str]) -> None:
    path, source = adapter_source
    for name, pattern in FORBIDDEN_PATTERNS.items():
        match = pattern.search(source)
        assert match is None, (
            f"{path.relative_to(ROOT)} contains forbidden pattern {name!r} "
            f"at offset {match.start() if match else '?'}"
        )


def test_adapter_network_domains_are_approved(adapter_source: tuple[Path, str]) -> None:
    url_pattern = re.compile(r"https?://([A-Za-z0-9.\-]+)")
    for match in url_pattern.finditer(source):
        domain = match.group(1).lower()
        if domain.startswith("www."):
            domain = domain[4:]
        assert any(
            domain == approved or domain.endswith("." + approved)
            for approved in APPROVED_NETWORK_DOMAINS
        ), f"{path.relative_to(ROOT)} references unapproved domain: {domain}"


def test_adapter_does_not_log_secrets(adapter_source: tuple[Path, str]) -> None:
    logging_pattern = re.compile(r"\b(print|logger\.\w+|logging\.\w+)\s*\(([^)]*)\)")
    for match in logging_pattern.finditer(source):
        args = match.group(2).lower()
        if any(word in args for word in ("api_key", "token", "secret", "password")):
            pytest.fail(
                f"{path.relative_to(ROOT)} logs a potential secret: {match.group(0)[:80]}"
            )


def test_tsar_adapter_present() -> None:
    tsar_adapter = ROOT / "src" / "arkhon" / "integrations" / "tsar" / "adapter.py"
    assert tsar_adapter.is_file(), "TSAR adapter missing"
