"""Tests for arkhon.language_support.detector."""

from __future__ import annotations

from pathlib import Path

import pytest

from arkhon.language_support.detector import detect_languages


def _write(root: Path, rel: str, content: str = "x") -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def test_empty_directory(tmp_path: Path) -> None:
    result = detect_languages(tmp_path)
    assert result.total_files == 0
    assert result.detected == []


def test_single_language(tmp_path: Path) -> None:
    _write(tmp_path, "src/main.py")
    _write(tmp_path, "src/util.py")
    result = detect_languages(tmp_path)
    assert len(result.detected) == 1
    assert result.detected[0].definition.id == "python"
    assert result.detected[0].file_count == 2


def test_multiple_languages_ordered_by_count(tmp_path: Path) -> None:
    for i in range(5):
        _write(tmp_path, f"src/file{i}.py")
    for i in range(3):
        _write(tmp_path, f"web/file{i}.ts")
    _write(tmp_path, "web/one.js")
    result = detect_languages(tmp_path)
    ids = [d.definition.id for d in result.detected]
    assert ids[0] == "python"
    assert "typescript" in ids
    assert "javascript" in ids


def test_primary_language(tmp_path: Path) -> None:
    for i in range(3):
        _write(tmp_path, f"src/f{i}.py")
    _write(tmp_path, "web/x.ts")
    result = detect_languages(tmp_path)
    assert result.primary == "python"


def test_ignored_directories(tmp_path: Path) -> None:
    _write(tmp_path, "src/main.py")
    _write(tmp_path, "node_modules/x.js")
    _write(tmp_path, "__pycache__/y.py")
    _write(tmp_path, ".venv/lib/z.py")
    result = detect_languages(tmp_path)
    assert len(result.detected) == 1
    assert result.detected[0].definition.id == "python"
    assert result.detected[0].file_count == 1


def test_unknown_extensions(tmp_path: Path) -> None:
    _write(tmp_path, "src/main.py")
    _write(tmp_path, "src/weird.xyzzy")
    result = detect_languages(tmp_path)
    assert ".xyzzy" in result.unknown


def test_sample_files_limited(tmp_path: Path) -> None:
    for i in range(10):
        _write(tmp_path, f"src/f{i}.py")
    result = detect_languages(tmp_path, max_samples=3)
    assert len(result.detected[0].sample_files) == 3


def test_case_insensitive_extensions(tmp_path: Path) -> None:
    _write(tmp_path, "src/main.PY")
    result = detect_languages(tmp_path)
    assert len(result.detected) == 1
    assert result.detected[0].definition.id == "python"


def test_not_a_directory(tmp_path: Path) -> None:
    f = tmp_path / "not-a-dir"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(NotADirectoryError):
        detect_languages(f)
