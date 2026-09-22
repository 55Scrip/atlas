"""A plain-text view of one claim. Diagnostic only: it states what the claim
says and what *kind* of evidence would bear on it, and never whether the claim
is supported -- that comparison is not this layer's to make."""
from __future__ import annotations

from atlas.analysis_engine.strategy_claim.contracts import EventKind, MeasureKind, StrategyClaim

__all__ = ["render_claim"]

#: What an observer would have to see for the claim's own event to have happened.
_EVIDENCE = {
    EventKind.CONTRACT_ENTERED: "a contract entered",
    EventKind.CONSTRUCTION_STARTED: "construction started at the named site",
    EventKind.FACILITY_ESTABLISHED: "a facility established",
    EventKind.CAPITAL_DEPLOYED: "capital reported as spent",
    EventKind.SHARE_REPURCHASE: "shares reported as repurchased",
    EventKind.COMPLETION: "the named thing reported complete",
}
_UNITS = {
    MeasureKind.CAPITAL_DEPLOYMENT: "currency committed or spent",
    MeasureKind.CAPITAL_RETURNED: "currency returned to holders",
    MeasureKind.CAPACITY: "capacity, in the unit the source uses",
}


def render_claim(claim: StrategyClaim) -> str:
    lines = [f"CLAIM ({claim.status.value})",
             f"  {claim.predicate} {claim.object_text}".rstrip(),
             f"Observable: {claim.observability.value}"]
    lines.append("Evidence that would bear on it:")
    for e in claim.event_kinds:
        lines.append(f"  - {_EVIDENCE.get(e, e.value)}")
    for m in claim.measure_kinds:
        lines.append(f"  - {_UNITS[m]}")
    if not claim.event_kinds and not claim.measure_kinds:
        lines.append("  - none stated; the claim names nothing countable or datable")
    lines.append(f"Magnitude: {claim.magnitude.value_text} {claim.magnitude.unit}".rstrip()
                 if claim.magnitude else "Magnitude: not stated")
    lines.append(f"Horizon: {claim.horizon.raw_text}" if claim.horizon else "Horizon: not stated")
    for d in claim.dependencies:
        lines.append(f"Depends on ({d.marker}): {d.raw_text}")
    lines.append(f"Source: {claim.provenance.issuer} {claim.provenance.source_period} "
                 f"{claim.provenance.speaker_title}".rstrip())
    return "\n".join(lines)
