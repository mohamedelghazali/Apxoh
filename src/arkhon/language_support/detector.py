"""Detect project languages from registered file extensions."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from arkhon.core.logging import get_logger
from arkhon.language_support.registry import LanguageDefinition, LanguageRegistry

logger = get_logger("language_support.detector")

IGNORED_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        "vendor",
        "target",
        "dist",
        "build",
        "out",
        ".venv",
        "venv",
        "env",
        ".env",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".nox",
        ".idea",
        ".vscode",
        ".arkhon",
        "coverage",
        "htmlcov",
    }
)
MAX_FILE_SIZE = 5 * 1024 * 1024


@dataclass
class DetectedLanguage:
    definition: LanguageDefinition
    file_count: int
    sample_files: list[Path] = field(default_factory=list)


@dataclass
class DetectionResult:
    root: Path
    detected: list[DetectedLanguage] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    total_files: int = 0

    @property
    def primary(self) -> str | None:
        if not self.detected:
            return None
        return max(self.detected, key=lambda item: item.file_count).definition.id


def _should_skip(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in relative.parts[:-1]):
            return True
        if path.is_symlink() or path.stat().st_size > MAX_FILE_SIZE:
            return True
    except (OSError, ValueError):
        return True
    return False


def detect_languages(
    root: Path,
    *,
    registry: LanguageRegistry | None = None,
    max_samples: int = 5,
) -> DetectionResult:
    root = root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"not a directory: {root}")
    if isinstance(max_samples, bool) or max_samples < 0:
        raise ValueError("max_samples must be a non-negative integer")

    reg = registry or _get_default_registry()
    counts: Counter[str] = Counter()
    samples: dict[str, list[Path]] = {}
    unknown_exts: Counter[str] = Counter()
    total = 0

    for path in root.rglob("*"):
        if not path.is_file() or _should_skip(path, root):
            continue
        total += 1
        ext = path.suffix.lower()
        if not ext:
            continue
        lang_id = reg.language_for_extension(ext)
        if lang_id is None:
            unknown_exts[ext] += 1
            continue
        counts[lang_id] += 1
        bucket = samples.setdefault(lang_id, [])
        if len(bucket) < max_samples:
            bucket.append(path)

    detected = [
        DetectedLanguage(reg.get(lang_id), count, samples.get(lang_id, []))
        for lang_id, count in counts.most_common()
    ]
    logger.debug("detected %d languages across %d files", len(detected), total)
    return DetectionResult(root, detected, sorted(unknown_exts), total)


_default_registry: LanguageRegistry | None = None


def _get_default_registry() -> LanguageRegistry:
    global _default_registry
    if _default_registry is None:
        from arkhon.language_support.registry import load_registry

        _default_registry = load_registry()
    return _default_registry
