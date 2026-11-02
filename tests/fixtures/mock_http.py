"""Mock HTTP helpers for testing adapters.

Patches ``urllib.request.urlopen`` so adapters can be tested without

network access. Every test that exercises an adapter should use this.

"""

from __future__ import annotations

import io

import json

from contextlib import contextmanager

from dataclasses import dataclass

from typing import Any, Callable, Iterator

from unittest.mock import patch

@dataclass

class FakeResponse:

    """Minimal stand-in for ``urllib.request.urlopen`` return value."""

    body: bytes

    status: int = 200

    headers: dict[str, str] | None = None

    def read(self) -> bytes:

        return self.body

    def __enter__(self) -> "FakeResponse":

        return self

    def __exit__(self, *_args: Any) -> None:

        return None

def make_json_response(payload: dict[str, Any], status: int = 200) -> FakeResponse:

    return FakeResponse(body=json.dumps(payload).encode("utf-8"), status=status)

def make_raw_response(body: str | bytes, status: int = 200) -> FakeResponse:

    if isinstance(body, str):

        body = body.encode("utf-8")

    return FakeResponse(body=body, status=status)

def make_http_error(status: int, reason: str = "error", message: str = "") -> Any:

    """Build an ``HTTPError`` instance without needing a real response."""

    import urllib.error

    err = urllib.error.HTTPError(

        url="https\://example.com",

        code=status,

        msg=reason,

        hdrs=None,

        fp=io.BytesIO(message.encode("utf-8")),

    )

    return err

@contextmanager

def patch_urlopen(

    response: FakeResponse | Callable[..., FakeResponse] | Exception,

) -> Iterator[Any]:

    """Patch ``urllib.request.urlopen`` for the duration of a test.

    ``response`` may be:

      * a ``FakeResponse`` instance (returned as-is)

      * a callable that takes ``request, timeout`` and returns a ``FakeResponse``

      * an ``Exception`` instance (raised when called)

    """

    calls: list[dict[str, Any]] = []

    def _fake_urlopen(request: Any, timeout: int | float | None = None, **kwargs: Any) -> Any:

        calls.append({"request": request, "timeout": timeout, "kwargs": kwargs})

        if isinstance(response, Exception):

            raise response

        if callable(response) and not isinstance(response, FakeResponse):

            return response(request=request, timeout=timeout, **kwargs)

        return response

    with patch("urllib.request.urlopen", side_effect=_fake_urlopen):

        yield calls
