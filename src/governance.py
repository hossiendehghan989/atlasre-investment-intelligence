"""Governance primitives for transparent, reviewable investment decisions."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable, TypedDict

import pandas as pd


class LineageRecord(TypedDict):
    output: str
    value: Any
    inputs: list[str]
    method: str
    source_refs: list[str]
    assumption_version: int


class AuditEvent(TypedDict):
    timestamp: str
    action: str
    actor: str
    payload: dict[str, Any]
    previous_hash: str
    event_hash: str


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


def versioned_assumptions(values: dict[str, tuple[Any, str]], deal_id: str = "UNASSIGNED", version: int = 1, source: str = "Illustrative input", verified_by: str = "", supersedes: dict[str, str] | None = None) -> pd.DataFrame:
    """Create stable assumption IDs and an explicit verification state."""
    if not deal_id or version < 1 or not source:
        raise ValueError("deal_id, version, and source are required")
    now = datetime.now(timezone.utc).isoformat()
    supersedes = supersedes or {}
    rows = [asdict(Assumption(f"{deal_id}:{name}:v{version}", name, value, unit, version, source, "VERIFIED" if verified_by else "REVIEW REQUIRED", "Investment team", verified_by, now, supersedes.get(name, ""))) for name, (value, unit) in values.items()]
    return pd.DataFrame(rows)


def assumption_register(values: dict[str, tuple[Any, str]], source: str = "Illustrative input") -> pd.DataFrame:
    return versioned_assumptions(values, source=source).rename(columns={"assumption_id": "id"})


def lineage_record(output_name: str, output_value: Any, inputs: Iterable[str], method: str, source_refs: Iterable[str] = (), assumption_version: int = 1) -> LineageRecord:
    inputs_list, sources_list = list(inputs), list(source_refs)
    if not output_name or not inputs_list or not method or assumption_version < 1:
        raise ValueError("lineage requires an output, input assumptions, method, and positive version")
    return {"output": output_name, "value": output_value, "inputs": inputs_list, "method": method, "source_refs": sources_list, "assumption_version": assumption_version}


def _canonical_event(event: dict[str, Any]) -> bytes:
    return json.dumps({key: event[key] for key in ("timestamp", "action", "actor", "payload", "previous_hash")}, sort_keys=True, default=str).encode("utf-8")


def audit_event(action: str, actor: str, payload: dict[str, Any], previous_hash: str = "GENESIS") -> AuditEvent:
    if not action or not actor or not isinstance(payload, dict) or not previous_hash:
        raise ValueError("audit action, actor, payload, and previous hash are required")
    event: dict[str, Any] = {"timestamp": datetime.now(timezone.utc).isoformat(), "action": action, "actor": actor, "payload": payload, "previous_hash": previous_hash}
    event["event_hash"] = hashlib.sha256(_canonical_event(event)).hexdigest()
    return event  # type: ignore[return-value]


def verify_audit_chain(events: list[dict[str, Any]]) -> bool:
    previous = "GENESIS"
    for event in events:
        try:
            expected_hash = hashlib.sha256(_canonical_event(event)).hexdigest()
        except (KeyError, TypeError, ValueError):
            return False
        if event.get("previous_hash") != previous or event.get("event_hash") != expected_hash:
            return False
        previous = str(event["event_hash"])
    return True


def ic_workflow() -> pd.DataFrame:
    return pd.DataFrame([
        {"stage": "Screening", "status": "Complete", "owner": "Acquisitions", "gate": "Core returns + downside visible"},
        {"stage": "Deep Dive", "status": "In progress", "owner": "Underwriting", "gate": "Sources attached + assumptions reviewed"},
        {"stage": "Recommendation", "status": "Pending", "owner": "IC sponsor", "gate": "Risk memo and portfolio impact"},
        {"stage": "Approval", "status": "Pending", "owner": "Investment committee", "gate": "Recorded decision + conditions"},
    ])


def default_lineage() -> list[LineageRecord]:
    return [
        lineage_record("levered_irr", "derived", ["purchase_price", "annual_noi", "annual_noi_growth", "exit_cap_rate", "leverage"], "monthly debt schedule + equity cash-flow IRR", ["deal_inputs.csv"]),
        lineage_record("minimum_dscr", "derived", ["annual_noi", "debt_rate", "debt_amortization_years", "leverage"], "annual NOI / annual debt service", ["loan_terms.xlsx"]),
        lineage_record("exit_value", "derived", ["annual_noi", "annual_noi_growth", "exit_cap_rate"], "forward NOI / exit cap rate", ["market_comps.pdf"]),
    ]


def lineage_json(records: list[LineageRecord]) -> str:
    return json.dumps(records, indent=2, default=str)


def model_run_fingerprint(model_version: str, assumptions: pd.DataFrame, lineage: list[LineageRecord]) -> str:
    """Hash model version, assumption snapshot, and lineage into a reproducibility ID."""
    if not model_version or "id" not in assumptions.columns and "assumption_id" not in assumptions.columns:
        raise ValueError("model_version and assumption IDs are required")
    records = assumptions.sort_values(by=["id"] if "id" in assumptions.columns else ["assumption_id"]).to_dict(orient="records")
    payload = {"model_version": model_version, "assumptions": records, "lineage": lineage}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


__all__ = ["Assumption", "AuditEvent", "LineageRecord", "versioned_assumptions", "assumption_register", "lineage_record", "audit_event", "verify_audit_chain", "ic_workflow", "default_lineage", "lineage_json", "model_run_fingerprint"]
