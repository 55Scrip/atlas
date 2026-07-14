"""Standalone CLI entry point for Reflection History (ATLAS-010).

    python -m atlas.core.application.reflection_history.cli

Deliberately separate from atlas/cli/main.py and atlas/conversation/ —
same independence discipline as every other standalone CLI in this
lineage. Read-only throughout: nothing in this file, or anything it
calls, ever writes a Decision, Reflection Response, or Investor
Identity row — except the one explicit, disclosed Investor Identity
bootstrap step below, which is ATLAS-009B's own store-level capability,
not something this file performs itself.

Prints every persisted field of each Reflection Response completely and
verbatim, under fixed, neutral labels. Nothing is truncated, reworded,
or summarized; no new sentence is synthesized from these fields; no
Pattern/Strategy Signature recognition is ever re-run to enrich or
recompute what was captured at Reflection Response's own capture time
(ATLAS-009). No filtering, search, pagination, grouping, or Decision
Timeline integration.
"""
from __future__ import annotations

from atlas.core.application.investor_identity.composition import (
    resolve_investor_identity,
)
from atlas.core.application.reflection_history.composition import (
    build_reflection_history_query,
    create_reflection_history_tables,
)
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.infrastructure.config.database import create_database_engine


def _print_entry(number: int, entry: ReflectionResponse) -> None:
    provenance = entry.provenance
    print(f"\n{number}. Recorded: {entry.recorded_at.isoformat()}")
    print(f"   Response: {entry.response_text.value}")
    print(f"   Reflection: {provenance.reflection_description}")
    print(f"   Coaching Question: {provenance.coaching_question_text}")
    grounding_member_ids = ", ".join(
        str(decision_id) for decision_id in provenance.grounding_pattern.member_decision_ids
    )
    print(
        f"   Grounding Pattern: {provenance.grounding_pattern.strategy_name} "
        f"({grounding_member_ids})"
    )
    if provenance.strategy_signature_patterns:
        print("   Strategy Signature Patterns:")
        for pattern in provenance.strategy_signature_patterns:
            member_ids = ", ".join(str(decision_id) for decision_id in pattern.member_decision_ids)
            print(f"     - {pattern.strategy_name} ({member_ids})")
    else:
        print("   Strategy Signature Patterns: (none)")
    print(f"   Reasoning Context — Subject: {provenance.reasoning_context_subject}")
    print(f"   Reasoning Context — Decision Type: {provenance.reasoning_context_decision_type}")
    print(f"   Reasoning Context — Confidence: {provenance.reasoning_context_confidence}")


def run() -> None:
    engine = create_database_engine()
    create_reflection_history_tables(engine)
    owner_user_id = resolve_investor_identity(engine)
    history = build_reflection_history_query(engine, owner_user_id).build()

    if not history.entries:
        print("No Reflection Responses recorded yet.")
        return

    print("Your preserved Reflection Responses, in order:")
    for number, entry in enumerate(history.entries, start=1):
        _print_entry(number, entry)


if __name__ == "__main__":
    run()
