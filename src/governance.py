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
    assumption_id: str
    name: str
    value: Any
    unit: str
    version: int = 1
    source: str = "Not supplied"
    status: str = "REVIEW REQUIRED"
    owner: str = "Investment team"
    verified_by: str = ""
    effective_at: str = ""
    supersedes: str = ""
    notes: str = ""


def versioned_assumptions(values: dict[str, tuple[Any, str]], deal_id: str = "UNASSIGNED", version: int = 1, source: str = "Illustrative input", verified_by: str = "") -> pd.DataFrame:
    """Create an auditable assumption snapshot with stable IDs and explicit verification."""
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for name, (value, unit) in values.items():
        rows.append(asdict(Assumption(f"{deal_id}:{name}:v{version}", name, value, unit, version, source, "VERIFIED" if verified_by else "REVIEW REQUIRED", "Investment team", verified_by, now)))
    return pd.DataFrame(rows)


def assumption_register(values: dict[str, tuple[Any, str]], source: str = "Illustrative input") -> pd.DataFrame:
    """Backward-compatible register wrapper used by the dashboard."""
    return versioned_assumptions(values, source=source).rename(columns={"assumption_id": "id"})


def lineage_record(output_name: str, output_value: Any, inputs: Iterable[str], method: str, source_refs: Iterable[str] = (), assumption_version: int = 1) -> dict[str, Any]:
    return {"output": output_name, "value": output_value, "inputs": list(inputs), "method": method, "source_refs": list(source_refs), "assumption_version": assumption_version}


def audit_event(action: str, actor: str, payload: dict[str, Any], previous_hash: str = "GENESIS") -> dict[str, str]:
    event = {"timestamp": datetime.now(timezone.utc).isoformat(), "action": action, "actor": actor, "payload": payload, "previous_hash": previous_hash}
    canonical = json.dumps(event, sort_keys=True, default=str).encode("utf-8")
    event["event_hash"] = hashlib.sha256(canonical).hexdigest()
    return event


def verify_audit_chain(events: list[dict[str, Any]]) -> bool:
    previous = "GENESIS"
    for event in events:
        canonical_event = {"timestamp": event["timestamp"], "action": event["action"], "actor": event["actor"], "payload": event["payload"], "previous_hash": event["previous_hash"]}
        expected_hash = hashlib.sha256(json.dumps(canonical_event, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        if event.get("previous_hash") != previous or event.get("event_hash") != expected_hash:
            return False
        previous = event["event_hash"]
    return True


def ic_workflow() -> pd.DataFrame:
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


__all__ = ["Assumption", "versioned_assumptions", "assumption_register", "lineage_record", "audit_event", "verify_audit_chain", "ic_workflow", "default_lineage", "lineage_json"]
