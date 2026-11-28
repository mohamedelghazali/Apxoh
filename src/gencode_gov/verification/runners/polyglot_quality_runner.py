"""Polyglot static quality runner integrating language_profile_loader and tool_resolver."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from gencode_gov.core.errors import ConfigError
from gencode_gov.language_support.detector import detect_languages
from gencode_gov.language_support.language_profile_loader import load_language_profile
from gencode_gov.language_support.tool_resolver import ToolStatus, resolve_tools
from gencode_gov.verification.runners.base import Runner, RunnerOutcome, RunnerResult

_PRIMARY_LINTERS: dict[str, list[str]] = {
    "python": ["ruff"],
    "typescript": ["eslint"],
    "javascript": ["eslint"],
    "go": ["golangci-lint"],
    "rust": ["clippy-driver"],
    "ruby": ["rubocop"],
    "java": ["checkstyle"],
    "csharp": ["dotnet"],
    "cpp": ["clang-tidy"],
}


def _repo_for_profiles() -> Path | None:
    repo_candidate = Path(__file__).resolve().parents[4]
    if (repo_candidate / "languages" / "registry.yaml").is_file():
        return repo_candidate
    return None  # pragma: no cover


class PolyglotQualityRunner(Runner):
    """Verify configured static-analysis tool readiness per detected language."""

    name = "polyglot-quality"

    def run(self, project_root: Path, artifact_dir: Path | None = None) -> RunnerResult:
        root = project_root.resolve()
        if not root.is_dir():
            return RunnerResult(
                runner=self.name,
                outcome=RunnerOutcome.BLOCKED,
                reason=f"project root is not a directory: {root}",
            )
        detection = detect_languages(root)
        detected_ids = [item.definition.id for item in detection.detected]
        profiles_repo = _repo_for_profiles()
        language_records: list[dict[str, Any]] = []
        missing_primary: list[str] = []
        for lang in detected_ids:
            profile_loaded = False
            if profiles_repo is not None:
                try:
                    _ = load_language_profile(lang, profiles_repo)
                    profile_loaded = True
                except ConfigError:  # pragma: no cover
                    profile_loaded = False
            linters = list(_PRIMARY_LINTERS.get(lang, []))
            resolution = resolve_tools(lang, linters)
            resolved_tools: list[dict[str, Any]] = []
            any_available = not linters
            for check in resolution.tools:
                avail = check.status == ToolStatus.AVAILABLE
                if avail:
                    any_available = True
                resolved_tools.append(
                    {"tool": check.name, "available": avail, "path": check.path or None}
                )
            if not any_available and lang == "python":  # pragma: no cover
                missing_primary.append(f"{lang}:{linters}")
            language_records.append(
                {"language": lang, "profile_loaded": profile_loaded, "tools": resolved_tools}
            )
        out_dir = artifact_dir or (root / ".gencode-gov" / "evidence" / "code-quality")
        if out_dir.exists() and out_dir.is_symlink():  # pragma: no cover
            return RunnerResult(
                runner=self.name,
                outcome=RunnerOutcome.BLOCKED,
                reason="refusing symlinked code-quality evidence directory",
            )
        out_dir.mkdir(parents=True, exist_ok=True)
        report_path = out_dir / "polyglot-quality-report.json"
        if report_path.exists() and report_path.is_symlink():  # pragma: no cover
            return RunnerResult(
                runner=self.name,
                outcome=RunnerOutcome.BLOCKED,
                reason="refusing symlinked polyglot-quality-report.json",
            )
        payload = {
            "schema_version": 1,
            "detected_languages": detected_ids,
            "languages": language_records,
            "missing_primary_tools": missing_primary,
        }
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=out_dir,
            prefix=".polyglot-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            tmp_path = Path(handle.name)
        tmp_path.replace(report_path)
        if missing_primary:  # pragma: no cover
            return RunnerResult(
                runner=self.name,
                outcome=RunnerOutcome.BLOCKED,
                reason=f"missing primary static quality tool(s): {missing_primary}",
                artifacts=[report_path],
            )
        return RunnerResult(
            runner=self.name,
            outcome=RunnerOutcome.PASS,
            reason=f"resolved static quality profiles for {len(detected_ids)} language(s)",
            artifacts=[report_path],
        )
