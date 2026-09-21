"""Run a local screening package from an owner-supplied JSON deal file."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate_committee_report import build_screening_package
from src.atlasre import DealInputs

REQUIRED_FIELDS = {"purchase_price", "annual_noi"}
DEAL_FIELDS = {
    "purchase_price", "annual_noi", "hold_years", "annual_noi_growth", "exit_cap_rate",
    "discount_rate", "acquisition_cost_pct", "selling_cost_pct", "leverage", "debt_rate",
    "debt_amortization_years",
}
PERCENT_FIELDS = {
    "annual_noi_growth", "exit_cap_rate", "discount_rate", "acquisition_cost_pct",
    "selling_cost_pct", "leverage", "debt_rate",
}
INTEGER_FIELDS = {"hold_years", "debt_amortization_years"}


def load_deal(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("deal JSON must contain an object")
    allowed = DEAL_FIELDS | {"deal_id", "verified_by", "source_reference", "source_status", "simulations", "hurdle_rate"}
    unknown = {field for field in payload if not field.startswith("_")} - allowed
    if unknown:
        raise ValueError(f"unknown fields: {', '.join(sorted(unknown))}")
    missing = REQUIRED_FIELDS - set(payload)
    if missing:
        raise ValueError(f"missing required fields: {', '.join(sorted(missing))}")
    for field in DEAL_FIELDS & set(payload):
        value = payload[field]
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError(f"{field} must be a number")
        if not math.isfinite(float(value)):
            raise ValueError(f"{field} must be finite (not NaN or infinity)")
        if field in INTEGER_FIELDS and (not isinstance(value, int) or isinstance(value, bool)):
            raise ValueError(f"{field} must be an integer")
        if field in PERCENT_FIELDS and value < 0:
            raise ValueError(f"{field} cannot be negative")
    simulations = payload.get("simulations", 5000)
    if isinstance(simulations, bool) or not isinstance(simulations, int) or simulations <= 0:
        raise ValueError("simulations must be a positive integer")
    hurdle_rate = payload.get("hurdle_rate", 0.12)
    if isinstance(hurdle_rate, bool) or not isinstance(hurdle_rate, int | float) or not math.isfinite(float(hurdle_rate)):
        raise ValueError("hurdle_rate must be a finite number")
    if hurdle_rate < 0:
        raise ValueError("hurdle_rate cannot be negative")
    return payload


def run(path: Path, output: Path) -> Path:
    payload = load_deal(path)
    deal_kwargs = {field: payload[field] for field in DEAL_FIELDS if field in payload}
    deal = DealInputs(**deal_kwargs)
    files = build_screening_package(
        deal,
        deal_id=str(payload.get("deal_id", "OWNER-SUPPLIED")),
        source_status=str(payload.get("source_status", "REVIEW REQUIRED")),
        verified_by=payload.get("verified_by"),
        source_reference=payload.get("source_reference"),
        simulations=payload.get("simulations", 5000),
        hurdle_rate=float(payload.get("hurdle_rate", 0.12)),
    )
    output.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (output / name).write_bytes(content)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local AtlasRE screening package from deal.json")
    parser.add_argument("deal", type=Path, help="owner-supplied JSON input")
    parser.add_argument("--output", type=Path, default=Path("deal-review"), help="output directory")
    args = parser.parse_args()
    try:
        output = run(args.deal, args.output)
    except (ValueError, TypeError) as exc:
        parser.error(str(exc))
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
