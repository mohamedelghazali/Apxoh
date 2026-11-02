"""Minimal greeting module.

This example contains one typed, deterministic public function.
"""

from __future__ import annotations


def greet(name: str) -> str:
    """Return a greeting for the given name.

    Args:
        name: The name to greet. Must be non-empty.

    Returns:
        A greeting string.

    Raises:
        ValueError: if name is empty.
    """
    if not name:
        raise ValueError("name must not be empty")
    return f"Hello, {name}!"
