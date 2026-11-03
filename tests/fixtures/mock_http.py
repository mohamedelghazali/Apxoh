"""Mock HTTP helpers for testing adapters without network access."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch


@dataclass
class FakeResponse:
    """Minimal stand-in for an http.client.HTTPResponse."""

    body: bytes
    status: int = 200
    reason: str = "OK"
    headers: dict[str, str] | None = None

    def read(self) -> bytes:
        return self.body


class FakeConnection:
    """Minimal HTTP(S) connection that returns a configured fake response."""

    def __init__(
        self,
        response: FakeResponse | Callable[..., FakeResponse] | Exception,
        calls: list[dict[str, Any]],
        timeout: int | float | None = None,
    ) -> None:
        self._response = response
        self._calls = calls
        self._timeout = timeout
        self._request: Any = None

    def request(
        self,
        method: str,
        url: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._calls.append(
            {"method": method, "url": url, "body": body, "headers": headers}
        )
        self._request = SimpleNamespace(
            data=body,
            headers=headers or {},
            method=method,
            full_url=url,
        )

    def getresponse(self) -> FakeResponse:
        if isinstance(self._response, Exception):
            raise self._response
        if callable(self._response):
            return self._response(request=self._request, timeout=self._timeout)
        return self._response

    def close(self) -> None:
        return None


def make_json_response(payload: dict[str, Any], status: int = 200) -> FakeResponse:
    return FakeResponse(
        body=json.dumps(payload).encode("utf-8"),
        status=status,
        reason="OK" if status < 400 else "HTTP error",
    )


def make_raw_response(body: str | bytes, status: int = 200) -> FakeResponse:
    if isinstance(body, str):
        body = body.encode("utf-8")
    return FakeResponse(body=body, status=status)


def make_http_error(
    status: int,
    reason: str = "error",
    message: str = "",
) -> FakeResponse:
    """Build an HTTP response with an error status."""
    return FakeResponse(body=message.encode("utf-8"), status=status, reason=reason)


@contextmanager
def patch_urlopen(
    response: FakeResponse | Callable[..., FakeResponse] | Exception,
) -> Iterator[list[dict[str, Any]]]:
    """Patch HTTP and HTTPS connection constructors for adapter tests."""
    calls: list[dict[str, Any]] = []

    def _connection(*_args: Any, **kwargs: Any) -> FakeConnection:
        return FakeConnection(response, calls, timeout=kwargs.get("timeout"))

    with (
        patch("http.client.HTTPSConnection", side_effect=_connection),
        patch("http.client.HTTPConnection", side_effect=_connection),
    ):
        yield calls
