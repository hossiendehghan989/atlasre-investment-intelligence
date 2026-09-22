"""Small presentation helpers shared by the dashboard and its tests."""

import math


def fraction_from_percent(display_percent: float) -> float:
    """Convert a human-facing percentage value to the model's fraction form."""
    return float(display_percent) / 100.0


def percent_or_na(value: float | None, decimals: int = 2) -> str:
    """Format a fractional percentage, using ``N/A`` when no finite result exists."""
    if value is None or not math.isfinite(float(value)):
        return "N/A"
    return f"{value:.{decimals}%}"


def metric_help(value: float | None, reason: str) -> str | None:
    """Return an explanatory tooltip only when a metric has no finite result."""
    if value is None or not math.isfinite(float(value)):
        return reason
    return None


def percent_or_na_report(value: float | None, decimals: int = 2, reason: str = "Result is not finite") -> str:
    """Format a report percentage with an explicit reason for an unavailable result."""
    if value is None or not math.isfinite(float(value)):
        return f"N/A — {reason}"
    return f"{value:.{decimals}%}"


def number_or_na_report(value: float | None, decimals: int = 0, prefix: str = "", suffix: str = "", reason: str = "Result is not finite") -> str:
    """Format a report number with an explicit reason for an unavailable result."""
    if value is None or not math.isfinite(float(value)):
        return f"N/A — {reason}"
    return f"{prefix}{value:,.{decimals}f}{suffix}"


def number_or_na(value: float | None, decimals: int = 0, prefix: str = "", suffix: str = "") -> str:
    """Format a finite number or return ``N/A`` without exposing NaN or infinity."""
    if value is None or not math.isfinite(float(value)):
        return "N/A"
    return f"{prefix}{value:,.{decimals}f}{suffix}"
