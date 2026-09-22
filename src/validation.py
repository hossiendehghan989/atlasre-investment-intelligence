"""Shared validation helpers for public financial-model inputs."""

from __future__ import annotations

import math
from numbers import Integral, Real


def finite(value: Real, name: str) -> float:
    """Return a finite numeric value or raise a descriptive error."""
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite")
    return float(value)


def positive(value: Real, name: str) -> float:
    number = finite(value, name)
    if number <= 0:
        raise ValueError(f"{name} must be positive")
    return number


def non_negative(value: Real, name: str) -> float:
    number = finite(value, name)
    if number < 0:
        raise ValueError(f"{name} must be non-negative")
    return number


def unit_interval(value: Real, name: str, *, inclusive_one: bool = True) -> float:
    number = finite(value, name)
    if not 0 <= number <= 1 or (not inclusive_one and number >= 1):
        bound = "[0, 1]" if inclusive_one else "[0, 1)"
        raise ValueError(f"{name} must be in {bound}")
    return number


def integer(value: int, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(value)


__all__ = ["finite", "integer", "non_negative", "positive", "unit_interval"]
