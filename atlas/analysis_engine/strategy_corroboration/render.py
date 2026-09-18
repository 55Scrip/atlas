"""Diagnostic rendering of corroboration evidence.

Debug surface. Every result prints its coverage state and the list of
things it does not license anyone to conclude, because "supported" is a
word readers finish into sentences Atlas has not earned.
"""
from __future__ import annotations

from atlas.analysis_engine.strategy_corroboration.models import NodeCorroboration

__all__ = ["render_corroboration"]


def render_corroboration(result: NodeCorroboration) -> tuple[str, ...]:
    lines = [f"{result.node_kind.upper()}: {result.subject_text[:80]}",
             f"  coverage              {result.coverage.value}",
             f"  independent events    {result.independent_event_count}"]
    for label, items in (("supporting", result.supporting),
                         ("weakening", result.weakening),
                         ("context", result.context)):
        for item in items:
            evidence = item.evidence
            lines.append(
                f"  {label:20} [{evidence.evidence_class.value}] {evidence.measure} {evidence.period}"
                f"  {item.relation.value}  ({item.temporal.value})"
            )
            lines.append(f"      {item.explanation}")
            lines.append(f"      rule: {item.derivation_rule}; owner: {evidence.semantic_owner}"
                         f"; source: {evidence.source_record_id or evidence.evidence_id}")
    lines.append(f"  measures searched     {', '.join(result.searched_measures) or 'none'}")
    lines.append(f"  no channel exists for {', '.join(result.unavailable_measures) or 'none'}")
    for claim in result.may_not_conclude:
        lines.append(f"  may NOT conclude      {claim}")
    return tuple(lines)
