"""Tests for arkhon.integrations.base."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from arkhon.integrations.base import (
    Integration,
    IntegrationInfo,
    IntegrationResponse,
)


def test_integration_info_is_frozen() -> None:
    info = IntegrationInfo(
        id="test",
        kind="model",
        provider="test-provider",
        version="1.0.0",
        capabilities=("code",),
    )

    with pytest.raises(FrozenInstanceError):
        info.id = "changed"  # type: ignore[misc]


def test_integration_info_defaults() -> None:
    info = IntegrationInfo(id="x", kind="y", provider="z", version="1")

    assert info.capabilities == ()


def test_integration_response_defaults() -> None:
    resp = IntegrationResponse(ok=True)

    assert resp.ok is True

    assert resp.payload == {}

    assert resp.artifacts == []

    assert resp.reason == ""


def test_integration_response_with_data(tmp_path: Path) -> None:
    art = tmp_path / "out.json"

    art.write_text("{}", encoding="utf-8")

    resp = IntegrationResponse(
        ok=True,
        payload={"key": "value"},
        artifacts=[art],
        reason="done",
    )

    assert resp.payload["key"] == "value"

    assert resp.artifacts == [art]


def test_integration_is_abstract() -> None:
    with pytest.raises(TypeError):
        Integration()  # type: ignore[abstract]


def test_integration_subclass_must_implement_methods() -> None:
    class Incomplete(Integration):
        pass

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


def test_integration_subclass_repr() -> None:
    class Dummy(Integration):
        @property
        def info(self) -> IntegrationInfo:
            return IntegrationInfo(
                id="dummy",
                kind="test",
                provider="test-provider",
                version="0.1",
            )

        def health_check(self) -> bool:
            return True

    d = Dummy()

    assert "Dummy" in repr(d)

    assert "id='dummy'" in repr(d)

    assert "kind='test'" in repr(d)
