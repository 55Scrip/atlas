"""A diagnostic rendering of salience evidence.

Debug surface, not product UI. Every line is a field; there is no
summary line, because a summary is the thing this sprint deliberately
did not build. The closing line says so in as many words, so nobody
reading the output can mistake the absence of a verdict for an
oversight.
"""
from __future__ import annotations

from atlas.analysis_engine.strategy_salience.models import SalienceEvidence

__all__ = ["render_salience"]


def render_salience(evidence: SalienceEvidence, *, refs: int = 1) -> tuple[str, ...]:
    lines = [f"{evidence.node_kind.upper()}: {evidence.subject_text[:90]}"]
    lines.append(f"  observed periods      {', '.join(evidence.periods) or 'none'}"
                 f"   ({evidence.period_count})")
    lines.append(f"  continuity            {evidence.continuity}")
    current = evidence.is_current
    lines.append(
        f"  latest mention        {evidence.latest_period or 'unknown'}"
        f"   (corpus latest {evidence.corpus_latest_period or 'unknown'};"
        f" {'is the latest call' if current else 'not the latest call' if current is False else 'unknown'})"
    )
    lines.append(f"  management speakers   {evidence.management_speaker_count}")
    for mention in evidence.speakers:
        lines.append(f"      {mention.role.value:18} {(mention.title or '?')[:40]}"
                     f"  [{', '.join(mention.periods)}]")
    lines.append(f"  prepared remarks      {len(evidence.prepared_remark_refs)} passage(s)")
    lines.append(f"  management in Q&A     {len(evidence.qa_refs)} passage(s)")
    lines.append(f"  explicit priority     {evidence.priority_language.count}")
    for ref in evidence.priority_language.refs[:refs]:
        lines.append(f'      {ref.period} {(ref.speaker_title or "?")[:28]}: "{ref.text[:100]}"')
    attention = evidence.analyst_attention
    lines.append(
        f"  analyst attention     {attention.analyst_count} analyst(s)"
        f" across {len(attention.periods)} period(s)   [market attention, not management priority]"
    )
    for ref in attention.refs[:refs]:
        lines.append(f'      {ref.period} {(ref.speaker or "?")[:22]}: "{ref.text[:95]}"')
    lines.append(f"  graph linkage         degree {evidence.graph_linkage.degree}"
                 f"  {evidence.graph_linkage.by_relation or '{}'}")
    lines.append(f"  resource commitments  {len(evidence.resource_commitment_links)}")
    lines.append(f"  forward-evidence links {len(evidence.forward_links)}")
    lines.append("  interpretation        no aggregate salience label is produced; "
                 "the signals above are the output")
    return tuple(lines)
