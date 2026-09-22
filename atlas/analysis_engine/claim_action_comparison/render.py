"""A plain-text view of one comparison. Diagnostic only.

It says how the two sit together and why, and never that the claim was
confirmed, validated, met or caused -- none of which this layer establishes.
"""
from __future__ import annotations

from atlas.analysis_engine.claim_action_comparison.contracts import (
    ClaimActionComparison, Compatibility, EntityBasis, Relation,
)

__all__ = ["render_comparison"]

_HEADLINE = {
    Relation.RELEVANT_EXECUTION: "Relevant execution evidence",
    Relation.RELEVANT_DEPENDENCY: "Relevant to a dependency the claim names",
    Relation.NOT_RELEVANT: "Not relevant",
    Relation.NOT_COMPARABLE: "Not comparable",
}
_BASIS = {
    EntityBasis.ASSERTED_ROLE: "named in the action's own object or counterparty",
    EntityBasis.SOURCE_SPAN: "present in the action's sentence but in no asserted role",
    EntityBasis.ISSUER_ONLY: "same issuer only",
    EntityBasis.NONE: "no named entity to compare",
}
_WHY = {
    "insufficient_claim_semantics": "the claim names nothing countable or datable",
    "no_shared_event_vocabulary": "the action reports a continuing state, not an act",
    "entity_issuer_only": "nothing but the issuer is shared",
    "entity_unresolved": "no entity evidence on either side",
    "event_mismatch": "the act observed is not the act claimed",
    "temporal_action_before_claim": "the action predates the claim, so it is background to it",
}


def render_comparison(c: ClaimActionComparison) -> str:
    lines = [_HEADLINE[c.relation], ""]
    named = ", ".join(c.entity_surfaces) if c.entity_surfaces else "-"
    lines.append(f"Entity: {c.entity.value} ({_BASIS[c.entity_basis]}){'' if named == '-' else f' -- {named}'}")
    lines.append(f"Event: {c.event.value}")
    lines.append(f"Measure: {c.measure.value}"
                 + (" (recorded, never decisive)" if c.measure is not Compatibility.NOT_APPLICABLE else ""))
    lines.append("Direction: not compared -- no source states a direction for an observed action")
    lines.append(f"Time: {c.temporal_relation.value}")
    lines.append(f"Dependency: {c.dependency.value}")
    if c.relation is Relation.RELEVANT_DEPENDENCY:
        lines.append("")
        lines.append("This action bears on something the claim depends on. It is not evidence "
                     "that the claimed act happened.")
    for r in c.refusal_reasons:
        lines.append(f"Refused: {r} -- {_WHY[r]}")
    lines += ["", f"Claim ({c.claim.issuer} {c.claim.source_period}): {c.claim.passage}",
              f"Action ({c.action.accession}): {c.action.sentence}"]
    return "\n".join(lines)
