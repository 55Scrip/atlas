"""Diagnostic rendering of attribution evidence.

Prints the status, every linking fact with its passage, and the channels
audited and found absent -- so a reader can tell "Atlas cannot narrow
this" from "Atlas did not look".
"""
from __future__ import annotations

from atlas.analysis_engine.strategy_attribution.models import ActionAttribution

__all__ = ["render_attribution"]


def render_attribution(result: ActionAttribution, *, channels: bool = False) -> tuple[str, ...]:
    lines = [f"{result.node_kind.upper()}: {result.subject_text[:74]}",
             f"  status                {result.status.value}",
             f"  resolutions           {', '.join(r.value for r in result.resolutions) or 'none'}"]
    for link in result.links:
        amount = f" amount={link.amount.value_text!r}" if link.amount else " (no amount stated)"
        lines.append(f"  link                  [{link.basis.value}] {link.resolution.value}"
                     f" -> {link.target_name or '(company)'}  tense={link.tense.value}{amount}")
        lines.append(f'      "{link.evidence.text[:150]}"')
        lines.append(f"      {link.evidence.period} {(link.evidence.speaker_title or '?')[:34]}"
                     f" | record {link.evidence.source_record_id[:28]}")
    if result.links:
        lines.append(f"  link authored by      "
                     f"{'management' if result.attribution_is_management_authored else 'mixed sources'}")
    lines.append(f"  independent action    {'yes' if result.has_independent_action_evidence else 'not established here'}")
    lines.append(f"  may conclude          {result.may_conclude}")
    for claim in result.may_not_conclude:
        lines.append(f"  may NOT conclude      {claim}")
    if channels:
        for channel in result.unavailable_channels:
            lines.append(f"  no channel            {channel}")
    return tuple(lines)
