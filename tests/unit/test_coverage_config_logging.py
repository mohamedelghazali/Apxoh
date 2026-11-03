from __future__ import annotations

import json
import logging
from types import SimpleNamespace

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


def test_configure_logging_rejects_bad_values_and_installs_json_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="unknown logging level"):
        configure_logging("not-a-level")
    with pytest.raises(ValueError, match="unknown logging format"):
        configure_logging("info", "xml")
    class FakeRoot:
        def __init__(self) -> None:
            self.handlers = []
            self.level = logging.INFO

        def setLevel(self, level: str) -> None:  # noqa: N802
            self.level = level

        def addHandler(self, handler: logging.Handler) -> None:  # noqa: N802
            self.handlers.append(handler)

    fake_root = FakeRoot()
    fake_logging = SimpleNamespace(
        getLogger=lambda name=None: fake_root if name is None else logging.getLogger(name),
        StreamHandler=logging.StreamHandler,
        INFO=logging.INFO,
        DEBUG=logging.DEBUG,
    )
    monkeypatch.setattr("arkhon.core.logging.logging", fake_logging)
    configure_logging("debug", "json")
    logger = get_logger("coverage")
    assert logger.name == "arkhon.coverage"
    assert fake_root.level == "DEBUG"
    assert isinstance(fake_root.handlers[-1].formatter, JsonFormatter)
