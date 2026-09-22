"""Generate committed ILLUSTRATIVE review files from the default deterministic case."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generate_committee_report import MODEL_VERSION, build_screening_package  # noqa: E402
from src.atlasre import DealInputs  # noqa: E402

OUTPUT = ROOT / "docs" / "sample_output"


def _metadata_line(fingerprint: str) -> str:
    return f"# ILLUSTRATIVE | model_version={MODEL_VERSION} | run_fingerprint={fingerprint}\n"


def generate() -> None:
    """Write review artifacts and explicit metadata without hidden filesystem state."""
    OUTPUT.mkdir(parents=True, exist_ok=True)
    files = build_screening_package(DealInputs(10_000_000, 650_000, hold_years=5, leverage=0.5))
    report = files["investment_committee_report.md"]
    fingerprint = next(
        line.split("`")[1] for line in report.decode().splitlines() if line.startswith("| Model-run fingerprint |")
    )
    metadata = _metadata_line(fingerprint)

    (OUTPUT / "README_ILLUSTRATIVE.md").write_bytes(files["README_ILLUSTRATIVE.md"])
    (OUTPUT / "investment_committee_memo.md").write_bytes(files["investment_committee_memo.md"])
    (OUTPUT / "investment_committee_report.md").write_bytes(report)
    for filename in ["assumptions.csv", "annual_debt_schedule.csv"]:
        (OUTPUT / filename).write_text(metadata + files[filename].decode(), encoding="utf-8")
    risk = json.loads(files["risk_summary.json"])
    (OUTPUT / "risk_summary.json").write_text(
        json.dumps(
            {
                "package_label": "ILLUSTRATIVE",
                "model_version": MODEL_VERSION,
                "run_fingerprint": fingerprint,
                "metrics": risk,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OUTPUT / "excel_reconciliation.xlsx").write_bytes(files["excel_reconciliation.xlsx"])
    print(OUTPUT)


if __name__ == "__main__":
    generate()
