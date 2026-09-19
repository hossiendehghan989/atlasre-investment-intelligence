from pathlib import Path
from zipfile import ZipFile
from io import BytesIO

from src.atlasre import DealInputs
from generate_committee_report import build_screening_package, screening_package_zip


def test_screening_package_contains_executive_sections_and_supporting_files():
    files = build_screening_package(DealInputs(10_000_000, 650_000, leverage=.5), simulations=100)
    report = files["investment_committee_report.md"].decode()
    assert "Downside and governance flags" in report
    assert "Expected shortfall" in report
    assert "Model-run fingerprint" in report
    assert "review_required" not in report.lower()
    assert {"stress_cases.csv", "assumptions.csv", "lineage.json", "risk_summary.json", "lease_summary.csv", "lease_monthly_rollup.csv"}.issubset(files)


def test_screening_package_zip_is_readable():
    package = screening_package_zip(DealInputs(10_000_000, 650_000, leverage=.5), simulations=50)
    with ZipFile(BytesIO(package)) as archive:
        names = set(archive.namelist())
    assert "investment_committee_report.md" in names
    assert "lease_summary.csv" in names
