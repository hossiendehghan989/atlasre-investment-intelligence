"""Governance primitives for transparent, reviewable investment decisions."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable

import pandas as pd


@dataclass(frozen=True)
class Assumption:
    name: str
    value: Any
    unit: str
    source: str = "Not supplied"
    status: str = "REVIEW REQUIRED"
    owner: str = "Investment team"
    notes: str = ""


def assumption_register(values: dict[str, tuple[Any, str]], source: str = "Illustrative input") -> pd.DataFrame:
    """Return a normalized register; every assumption has an explicit review state."""
    rows = [asdict(Assumption(name, value, unit, source=source)) for name, (value, unit) in values.items()]
    return pd.DataFrame(rows, columns=["name", "value", "unit", "source", "status", "owner", "notes"])


def lineage_record(output_name: str, output_value: Any, inputs: Iterable[str], method: str, source_refs: Iterable[str] = ()) -> dict[str, Any]:
    """Create a machine-readable link between an output, assumptions, method, and sources."""
    return {
        "output": output_name,
        "value": output_value,
        "inputs": list(inputs),
        "method": method,
        "source_refs": list(source_refs),
    }


def audit_event(action: str, actor: str, payload: dict[str, Any], previous_hash: str = "GENESIS") -> dict[str, str]:
    """Create an append-only event with a deterministic hash chain."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "actor": actor,
        "payload": payload,
        "previous_hash": previous_hash,
    }
    canonical = json.dumps(event, sort_keys=True, default=str).encode("utf-8")
    event["event_hash"] = hashlib.sha256(canonical).hexdigest()
    return event


def verify_audit_chain(events: list[dict[str, Any]]) -> bool:
    """Verify ordering and hashes for an audit chain."""
    previous = "GENESIS"
    for event in events:
        canonical_event = {
            "timestamp": event["timestamp"],
            "action": event["action"],
            "actor": event["actor"],
            "payload": event["payload"],
            "previous_hash": event["previous_hash"],
        }
        canonical = json.dumps(canonical_event, sort_keys=True, default=str).encode("utf-8")
        expected_hash = hashlib.sha256(canonical).hexdigest()
        if event.get("previous_hash") != previous or event.get("event_hash") != expected_hash:
            return False
        previous = event["event_hash"]
    return True


def ic_workflow() -> pd.DataFrame:
    """Canonical investment committee state machine for the prototype."""
    return pd.DataFrame([
        {"stage": "Screening", "status": "Complete", "owner": "Acquisitions", "gate": "Core returns + downside visible"},
        {"stage": "Deep Dive", "status": "In progress", "owner": "Underwriting", "gate": "Sources attached + assumptions reviewed"},
        {"stage": "Recommendation", "status": "Pending", "owner": "IC sponsor", "gate": "Risk memo and portfolio impact"},
        {"stage": "Approval", "status": "Pending", "owner": "Investment committee", "gate": "Recorded decision + conditions"},
    ])


def default_lineage() -> list[dict[str, Any]]:
    return [
        lineage_record("levered_irr", "derived", ["purchase_price", "annual_noi", "annual_noi_growth", "exit_cap_rate", "leverage"], "monthly debt schedule + equity cash-flow IRR", ["deal_inputs.csv"]),
        lineage_record("minimum_dscr", "derived", ["annual_noi", "debt_rate", "debt_amortization_years", "leverage"], "annual NOI / annual debt service", ["loan_terms.xlsx"]),
        lineage_record("exit_value", "derived", ["annual_noi", "annual_noi_growth", "exit_cap_rate"], "forward NOI / exit cap rate", ["market_comps.pdf"]),
    ]


def lineage_json(records: list[dict[str, Any]]) -> str:
    return json.dumps(records, indent=2, default=str)


__all__ = ["Assumption", "assumption_register", "lineage_record", "audit_event", "verify_audit_chain", "ic_workflow", "default_lineage", "lineage_json"]


if __name__ == "__main__":
    first = audit_event("screening_created", "system", {"deal_id": "ATLAS-001"})
    second = audit_event("assumptions_reviewed", "analyst", {"deal_id": "ATLAS-001", "count": 9}, first["event_hash"])
    print(verify_audit_chain([first, second]))
    print(lineage_json(default_lineage()))
