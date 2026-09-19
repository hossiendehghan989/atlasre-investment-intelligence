from io import BytesIO
from zipfile import ZipFile

from generate_committee_report import build_screening_package, screening_package_zip
from src.atlasre import DealInputs


def test_screening_package_contains_executive_sections_and_supporting_files():
    files = build_screening_package(DealInputs(10_000_000, 650_000, leverage=.5), simulations=100)
    report = files["investment_committee_report.md"].decode()
    memo = files["investment_committee_memo.md"].decode()
    package_readme = files["README_ILLUSTRATIVE.md"].decode()
    assert report.startswith("# ILLUSTRATIVE")
    assert memo.startswith("# ILLUSTRATIVE")
    assert package_readme.startswith("# ILLUSTRATIVE")
    assert "Downside and governance flags" in report
    assert "Expected shortfall" in report
    assert "Model-run fingerprint" in report
    assert "review_required" not in report.lower()
    assert {
        "stress_cases.csv",
        "annual_debt_schedule.csv",
        "monthly_development_model.csv",
        "assumptions.csv",
        "lineage.json",
        "risk_summary.json",
        "lease_summary.csv",
        "lease_monthly_rollup.csv",
        "excel_reconciliation.xlsx",
    }.issubset(files)


def test_screening_package_zip_is_readable():
    package = screening_package_zip(DealInputs(10_000_000, 650_000, leverage=.5), simulations=50)
    with ZipFile(BytesIO(package)) as archive:
        names = set(archive.namelist())
    assert "investment_committee_report.md" in names
    assert "investment_committee_memo.md" in names
    assert "README_ILLUSTRATIVE.md" in names
    assert "annual_debt_schedule.csv" in names
    assert "monthly_development_model.csv" in names
    assert "lease_summary.csv" in names
    assert "excel_reconciliation.xlsx" in names


def test_verified_without_evidence_is_review_required_throughout_package():
    files = build_screening_package(
        DealInputs(10_000_000, 650_000, leverage=.5),
        source_status="VERIFIED",
        simulations=25,
    )
    report = files["investment_committee_report.md"].decode()
    assumptions = files["assumptions.csv"].decode()
    assert "| Source status | **REVIEW REQUIRED** |" in report
    assert "Source-backed screening input" not in assumptions
    assert "REVIEW REQUIRED" in assumptions


def test_verified_with_evidence_is_verified_throughout_package():
    files = build_screening_package(
        DealInputs(10_000_000, 650_000, leverage=.5),
        source_status="VERIFIED",
        verified_by="Reviewer A",
        source_reference="data-room://deal-001/operating-statement.pdf",
        simulations=25,
    )
    report = files["investment_committee_report.md"].decode()
    assumptions = files["assumptions.csv"].decode()
    assert "| Source status | **VERIFIED** |" in report
    assert "Source-backed screening input" in assumptions
    assert "VERIFIED" in assumptions
