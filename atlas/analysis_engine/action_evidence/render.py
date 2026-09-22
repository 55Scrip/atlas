"""A plain reading of one record, for audit. No score, no verdict."""
from __future__ import annotations

from atlas.analysis_engine.action_evidence.contracts import ActionEvidence

__all__ = ["render"]


def _date(r: ActionEvidence) -> str:
    if r.date is None:
        return "undated"
    d = r.date
    stamp = f"{d.year:04d}" + (f"-{d.month:02d}" if d.month else "") + (f"-{d.day:02d}" if d.day else "")
    return f"{stamp} ({d.kind.value})"


def render(r: ActionEvidence) -> str:
    lines = [
        f"{_date(r)} | {r.action_type.value.upper()} | {r.status.value}",
        f"Actor: {r.actor_text or '(not written)'} [{r.actor_kind.value}"
        + ("" if r.actor_is_filer is None else f", filer={r.actor_is_filer}") + "]",
        f"Predicate: {r.predicate}" + (f" (reported via: {r.reported_via})" if r.reported_via else ""),
        f"Object: {r.object_text}",
    ]
    if r.counterparty_text:
        lines.append(f"Counterparty: {r.counterparty_text}")
    for q in r.quantities:
        lines.append(f"Quantity: {q.value_text} {q.unit or '[no unit in source]'} [{q.kind.value}]"
                     + (f" -- {q.qualifier}" if q.qualifier else ""))
    loc = r.locator
    lines.append(f"Source: {loc.issuer} {loc.accession} / {loc.section} / "
                 f"paragraph {loc.paragraph_ordinal}, sentence {loc.sentence_ordinal}")
    lines.append(f'Evidence: "{r.sentence}"')
    return "\n".join(lines)
