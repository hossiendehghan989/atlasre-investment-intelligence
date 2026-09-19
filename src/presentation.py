"""Small presentation helpers shared by the dashboard and its tests."""


def fraction_from_percent(display_percent: float) -> float:
    """Convert a human-facing percentage value to the model's fraction form."""
    return float(display_percent) / 100.0
