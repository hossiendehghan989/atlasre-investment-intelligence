"""Governance primitives for transparent, reviewable investment decisions."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, TypedDict

import pandas as pd

from .validation import integer


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


def _stable_assumption_id(deal_id: str, name: str, version: int) -> str:
    if not deal_id.strip() or not name.strip() or version < 1:
        raise ValueError("deal_id, assumption name, and version are required")
    return f"{deal_id.strip()}:{name.strip()}:v{version}"


def versioned_assumptions(
    values: dict[str, tuple[Any, str]],
    deal_id: str = "UNASSIGNED",
    version: int = 1,
    source: str = "Illustrative input",
    verified_by: str = "",
    supersedes: dict[str, str] | None = None,
    effective_at: str = "",
    owner: str = "Investment team",
) -> pd.DataFrame:
    """Create stable assumption IDs with version, source, and supersession fields.

    ``effective_at`` is caller-supplied rather than generated at runtime. This
    avoids inserting a volatile timestamp into a logically identical model run;
    callers that have a real effective date should provide it explicitly.
    """
    integer(version, "version", minimum=1)
    if not values or not source or not owner:
        raise ValueError("assumption values, source, and owner are required")
    supersedes = supersedes or {}
    rows: list[dict[str, Any]] = []
    for name, value_and_unit in values.items():
        if not isinstance(value_and_unit, tuple) or len(value_and_unit) != 2:
            raise ValueError("assumption values must be (value, unit) tuples")
        value, unit = value_and_unit
        assumption_id = _stable_assumption_id(deal_id, name, version)
        rows.append(asdict(Assumption(
            assumption_id=assumption_id,
            name=name.strip(),
            value=value,
            unit=str(unit),
            version=version,
            source=source,
            status="VERIFIED" if verified_by else "REVIEW REQUIRED",
            owner=owner,
            verified_by=verified_by,
            effective_at=effective_at,
            supersedes=supersedes.get(name, ""),
        )))
    return pd.DataFrame(rows)


def assumption_register(values: dict[str, tuple[Any, str]], source: str = "Illustrative input") -> pd.DataFrame:
    """Backward-compatible assumption register with a stable public ``id`` field."""
    return versioned_assumptions(values, source=source).rename(columns={"assumption_id": "id"})


def lineage_record(output_name: str, output_value: Any, inputs: Iterable[str], method: str, source_refs: Iterable[str] = (), assumption_version: int = 1) -> LineageRecord:
    inputs_list, sources_list = list(inputs), list(source_refs)
    integer(assumption_version, "assumption_version", minimum=1)
    if not output_name or not inputs_list or not method:
        raise ValueError("lineage requires an output, input assumptions, method, and positive version")
    return {
        "output": output_name,
        "value": output_value,
        "inputs": inputs_list,
        "method": method,
        "source_refs": sources_list,
        "assumption_version": assumption_version,
    }


def _canonical_event(event: dict[str, Any]) -> bytes:
    return json.dumps({key: event[key] for key in ("timestamp", "action", "actor", "payload", "previous_hash")}, sort_keys=True, default=str).encode("utf-8")


def audit_event(action: str, actor: str, payload: dict[str, Any], previous_hash: str = "GENESIS") -> AuditEvent:
    if not action or not actor or not isinstance(payload, dict) or not previous_hash:
        raise ValueError("audit action, actor, payload, and previous hash are required")
    event: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "action": action,
        "actor": actor,
        "payload": payload,
        "previous_hash": previous_hash,
    }
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
        lineage_record("levered_irr", "derived", ["purchase_price", "annual_noi", "annual_noi_growth", "exit_cap_rate", "leverage"], "annual debt schedule + equity cash-flow IRR", ["deal_inputs.csv"], 1),
        lineage_record("minimum_dscr", "derived", ["annual_noi", "debt_rate", "debt_amortization_years", "leverage"], "annual NOI / annual debt service", ["loan_terms.xlsx"], 1),
        lineage_record("exit_value", "derived", ["annual_noi", "annual_noi_growth", "exit_cap_rate"], "forward NOI / exit cap rate", ["market_comps.pdf"], 1),
    ]


def lineage_json(records: list[LineageRecord]) -> str:
    return json.dumps(records, indent=2, default=str)


def _canonicalize(value: Any) -> Any:
    """Normalize common container types without losing material values."""
    if isinstance(value, dict):
        return {str(key): _canonicalize(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    if hasattr(value, "item"):
        try:
            return _canonicalize(value.item())
        except (AttributeError, ValueError):
            pass
    return value


def _canonical_lineage(record: LineageRecord) -> dict[str, Any]:
    return {
        "output": record["output"],
        "value": _canonicalize(record["value"]),
        "inputs": sorted(map(str, record["inputs"])),
        "method": record["method"],
        "source_refs": sorted(map(str, record["source_refs"])),
        "assumption_version": record["assumption_version"],
    }


def model_run_fingerprint(model_version: str, assumptions: pd.DataFrame, lineage: list[LineageRecord]) -> str:
    """Hash a canonical model version, assumption snapshot, and lineage set.

    The fingerprint is invariant to DataFrame row/column order and lineage-order
    presentation. It changes when any material assumption value, metadata, model
    version, or lineage element changes.
    """
    id_column = "id" if "id" in assumptions.columns else "assumption_id" if "assumption_id" in assumptions.columns else ""
    if not model_version or not id_column:
        raise ValueError("model_version and assumption IDs are required")
    if assumptions[id_column].isna().any() or assumptions[id_column].duplicated().any():
        raise ValueError("assumption IDs must be present and unique")
    records = [_canonicalize(record) for record in assumptions.to_dict(orient="records")]
    canonical_assumptions = sorted(records, key=lambda record: str(record[id_column]))
    canonical_lineage = sorted((_canonical_lineage(record) for record in lineage), key=lambda record: json.dumps(record, sort_keys=True, default=str))
    payload = {
        "model_version": model_version,
        "assumptions": canonical_assumptions,
        "lineage": canonical_lineage,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


__all__ = [
    "Assumption",
    "AuditEvent",
    "LineageRecord",
    "assumption_register",
    "audit_event",
    "default_lineage",
    "ic_workflow",
    "lineage_json",
    "lineage_record",
    "model_run_fingerprint",
    "verify_audit_chain",
    "versioned_assumptions",
]
