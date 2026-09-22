from datetime import date

import pytest

from src.lease import Lease, lease_rollup, lease_summary


def test_lease_rollup_applies_escalation_vacancy_and_expiry():
    leases = [
        Lease(
            "Tenant A",
            date(2025, 1, 1),
            date(2025, 12, 31),
            120_000,
            annual_escalation=0.10,
            vacancy_assumption=0.05,
            credit_quality="STRONG",
        )
    ]
    rollup = lease_rollup(leases, date(2025, 1, 1), 13, operating_expense_ratio=0.20)
    assert rollup.iloc[0]["contract_rent"] == pytest.approx(10_000)
    assert rollup.iloc[0]["vacancy"] == pytest.approx(500)
    assert rollup.iloc[0]["noi"] == pytest.approx(7_600)
    assert rollup.iloc[11]["expiring_leases"] == 1
    assert rollup.iloc[12]["active_leases"] == 0


def test_lease_validation_rejects_invalid_dates_and_vacancy():
    with pytest.raises(ValueError):
        Lease("", date(2025, 1, 1), date(2025, 1, 1), 100).validate()
    with pytest.raises(ValueError):
        Lease("Tenant", date(2025, 2, 1), date(2025, 1, 1), 100).validate()
    with pytest.raises(ValueError):
        Lease("Tenant", date(2025, 1, 1), date(2025, 1, 1), 100, vacancy_assumption=1.1).validate()


def test_lease_summary_preserves_source_inputs():
    lease = Lease("Tenant", date(2025, 1, 1), date(2027, 12, 31), 250_000, credit_quality="AVERAGE")
    summary = lease_summary([lease])
    assert summary.iloc[0]["tenant"] == "Tenant"
    assert summary.iloc[0]["credit_quality"] == "AVERAGE"
