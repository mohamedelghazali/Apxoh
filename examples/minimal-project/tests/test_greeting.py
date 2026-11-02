"""Tests for the greeting module."""

from __future__ import annotations

import pytest

from greeting import greet


def test_greet_with_name() -> None:
    assert greet("Alice") == "Hello, Alice!"


def test_greet_with_unicode() -> None:
    assert greet("محمد") == "Hello, محمد!"


def test_greet_with_empty_name_raises() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        greet("")
