from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from arkhon.config import find_repo_root
from arkhon.core.errors import ManifestError
from arkhon.core.logging import JsonFormatter, configure_logging, get_logger


def test_find_repo_root_handles_filesystem_root_without_manifest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class RootPath:
        def __init__(self, *_parts: object) -> None:
            pass

        def resolve(self) -> RootPath:
            return self

        @property
        def parent(self) -> RootPath:
            return self

        def __truediv__(self, _other: str) -> RootPath:
            return self

        def is_file(self) -> bool:
            return False

    monkeypatch.delenv("APXOH_ROOT", raising=False)
    monkeypatch.setattr("arkhon.config.Path", RootPath)
    with pytest.raises(ManifestError, match="Could not locate"):
        find_repo_root()


def test_json_formatter_includes_exception_and_extra() -> None:
    try:
        raise RuntimeError("diagnostic")
    except RuntimeError:
        import sys

        record = logging.LogRecord(
            "arkhon.test", logging.ERROR, __file__, 1, "failed", (), sys.exc_info()
        )
    record.arkhon_extra = {"component": "unit-test"}
    payload = json.loads(JsonFormatter().format(record))
    assert payload["message"] == "failed"
    assert "RuntimeError: diagnostic" in payload["exception"]
    assert payload["extra"] == {"component": "unit-test"}


def test_configure_logging_rejects_bad_values_and_installs_json_handler() -> None:
    with pytest.raises(ValueError, match="unknown logging level"):
        configure_logging("not-a-level")
    with pytest.raises(ValueError, match="unknown logging format"):
        configure_logging("info", "xml")
    configure_logging("debug", "json")
    logger = get_logger("coverage")
    assert logger.name == "arkhon.coverage"
    root = logging.getLogger()
    assert root.level == logging.DEBUG
    assert isinstance(root.handlers[-1].formatter, JsonFormatter)
