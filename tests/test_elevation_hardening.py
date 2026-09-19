from datetime import date

import pytest

from generate_committee_report import build_screening_package
from src.atlasre import DealInputs
from src.governance import default_lineage, model_run_fingerprint, versioned_assumptions
from src.lease import Lease, LeaseUnderwritingInputs, lease_rollup, underwrite_with_lease_roll


def test_lease_rollover_vacancy_and_replacement_rent_are_separate():
    lease = Lease(
        "Tenant A",
        date(2025, 1, 1),
        date(2025, 1, 31),
        120_000,
        rollover_vacancy_months=2,
        rollover_rent_change=-0.10,
    )
    rollup = lease_rollup([lease], date(2025, 1, 1), 4)
    assert rollup.iloc[1]["rollover_vacancy"] == pytest.approx(10_000)
    assert rollup.iloc[2]["rollover_vacancy"] == pytest.approx(10_000)
    assert rollup.iloc[3]["rollover_rent"] == pytest.approx(9_000)
    assert rollup.iloc[3]["noi"] == pytest.approx(9_000)


def test_all_expired_leases_without_rollover_produce_zero_forward_noi():
    lease = Lease("Expired", date(2024, 1, 1), date(2024, 12, 31), 120_000)
    rollup = lease_rollup([lease], date(2025, 1, 1), 12)
    assert rollup["active_leases"].sum() == 0
    assert rollup["noi"].sum() == pytest.approx(0)


def test_negative_lease_growth_is_supported_without_negative_rent():
    lease = Lease("Deflating", date(2025, 1, 1), date(2026, 12, 31), 120_000, annual_escalation=-0.10)
    rollup = lease_rollup([lease], date(2025, 1, 1), 13)
    assert rollup.iloc[0]["contract_rent"] == pytest.approx(10_000)
    assert rollup.iloc[12]["contract_rent"] == pytest.approx(9_000)
    assert (rollup["noi"] >= 0).all()


def test_lease_derived_path_preserves_original_simplified_input():
    original = DealInputs(10_000_000, 650_000, leverage=.50)
    lease_inputs = LeaseUnderwritingInputs(
        (Lease("Tenant", date(2025, 1, 1), date(2026, 12, 31), 1_200_000),),
        date(2025, 1, 1),
        months=12,
        operating_expense_ratio=.20,
    )
    result = underwrite_with_lease_roll(original, lease_inputs)
    assert original.annual_noi == 650_000
    assert result["lease_derived_annual_noi"] == pytest.approx(960_000)
    assert result["underwriting"]["entry_cap_rate"] == pytest.approx(.096)


def test_model_fingerprint_is_invariant_to_row_column_and_lineage_order():
    assumptions = versioned_assumptions(
        {"purchase_price": (10_000_000, "USD"), "exit_cap_rate": (.06, "%")},
        deal_id="A",
        version=2,
        effective_at="2026-09-19",
    )
    reordered = assumptions.loc[::-1, list(reversed(assumptions.columns))].reset_index(drop=True)
    fingerprint = model_run_fingerprint("v0.10", assumptions, default_lineage())
    assert fingerprint == model_run_fingerprint("v0.10", reordered, list(reversed(default_lineage())))


def test_model_fingerprint_changes_for_material_assumption_change():
    base = versioned_assumptions({"purchase_price": (10_000_000, "USD")}, deal_id="A")
    changed = base.copy()
    changed.loc[0, "value"] = 10_250_000
    assert model_run_fingerprint("v0.10", base, default_lineage()) != model_run_fingerprint("v0.10", changed, default_lineage())


def test_unverified_package_cannot_display_an_initial_screen_pass():
    files = build_screening_package(DealInputs(10_000_000, 650_000, leverage=.25), source_status="REVIEW REQUIRED", simulations=25)
    report = files["investment_committee_report.md"].decode("utf-8")
    assert "Decision status | **PASSES INITIAL SCREEN** |" not in report
    assert "PASSES INITIAL SCREEN" not in report


def test_lease_path_package_has_traceable_lease_artifacts_and_lineage():
    lease_inputs = LeaseUnderwritingInputs(
        (Lease("Tenant", date(2025, 1, 1), date(2027, 12, 31), 600_000, vacancy_assumption=.05),),
        date(2025, 1, 1),
        months=12,
        operating_expense_ratio=.20,
    )
    files = build_screening_package(DealInputs(10_000_000, 650_000, leverage=.50), simulations=25, lease_inputs=lease_inputs)
    report = files["investment_committee_report.md"].decode("utf-8")
    lineage = files["lineage.json"].decode("utf-8")
    assert {"lease_summary.csv", "lease_monthly_rollup.csv", "lease_annual_summary.csv"}.issubset(files)
    assert "optional rent-roll bridge" in report
    assert "sum monthly lease NOI / supplied months x 12" in lineage
