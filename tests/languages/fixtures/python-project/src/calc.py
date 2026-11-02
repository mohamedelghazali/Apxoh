"""Minimal calculator module for Apxoh fixture testing."""

from __future__ import annotations


def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b


def subtract(a: int, b: int) -> int:
    """Return the difference of two integers."""
    return a - b


def multiply(a: int, b: int) -> int:
    """Return the product of two integers."""
    return a * b


def divide(a: int, b: int) -> float:
    """Return the quotient of two integers.

    Raises:
        ZeroDivisionError: if b is zero.
    """
    if b == 0:
        raise ZeroDivisionError("cannot divide by zero")
    return a / b
