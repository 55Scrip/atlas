"""Standalone CLI entry point for Reflection Comparison (ATLAS-011).

    python -m atlas.core.application.reflection_comparison.cli

Deliberately separate from atlas/cli/main.py and atlas/conversation/ —
same independence discipline as every other standalone CLI in this
lineage. Read-only throughout, aside from the one explicit, disclosed
Investor Identity bootstrap step (ATLAS-009B's own store-level
capability, reused verbatim, never performed by this file itself).

Atlas never suggests, infers, defaults, ranks, or automatically chooses
either half of a comparison — both selections must come from the
investor's own input, with no pre-selected default. No filtering,
search, pagination, grouping, or Decision Timeline integration.
"""
from __future__ import annotations

from collections.abc import Callable

from atlas.core.application.investor_identity.composition import (
    resolve_investor_identity,
)
from atlas.core.application.reflection_comparison.exceptions import (
    ReflectionComparisonError,
)
from atlas.core.application.reflection_comparison.query import ReflectionComparisonQuery
from atlas.core.application.reflection_history.composition import (
    build_reflection_history_query,
    create_reflection_history_tables,
)
from atlas.core.application.reflection_history.history import ReflectionHistory
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.infrastructure.config.database import create_database_engine


def _print_pointer_line(number: int, entry: ReflectionResponse) -> None:
    print(f"{number}. Recorded: {entry.recorded_at.isoformat()} — {entry.response_text.value}")


def _print_full_entry(label: str, entry: ReflectionResponse) -> None:
    provenance = entry.provenance
    print(f"\n{label}")
    print(f"Recorded: {entry.recorded_at.isoformat()}")
    print(f"Response: {entry.response_text.value}")
    print(f"Reflection: {provenance.reflection_description}")
    print(f"Coaching Question: {provenance.coaching_question_text}")
    grounding_member_ids = ", ".join(
        str(decision_id) for decision_id in provenance.grounding_pattern.member_decision_ids
    )
    print(
        f"Grounding Pattern: {provenance.grounding_pattern.strategy_name} "
        f"({grounding_member_ids})"
    )
    if provenance.strategy_signature_patterns:
        print("Strategy Signature Patterns:")
        for pattern in provenance.strategy_signature_patterns:
            member_ids = ", ".join(str(decision_id) for decision_id in pattern.member_decision_ids)
            print(f"  - {pattern.strategy_name} ({member_ids})")
    else:
        print("Strategy Signature Patterns: (none)")
    print(f"Reasoning Context — Subject: {provenance.reasoning_context_subject}")
    print(f"Reasoning Context — Decision Type: {provenance.reasoning_context_decision_type}")
    print(f"Reasoning Context — Confidence: {provenance.reasoning_context_confidence}")


def _prompt_for_selection(
    history: ReflectionHistory, prompt: str, input_fn: Callable[[str], str] = input
):
    while True:
        answer = input_fn(prompt).strip()
        try:
            choice = int(answer)
        except ValueError:
            print("Please type a number from the list above.")
            continue
        if not (1 <= choice <= len(history.entries)):
            print("Please type a number from the list above.")
            continue
        return history.entries[choice - 1].id


def run(input_fn: Callable[[str], str] = input) -> None:
    engine = create_database_engine()
    create_reflection_history_tables(engine)
    owner_user_id = resolve_investor_identity(engine)
    history = build_reflection_history_query(engine, owner_user_id).build()

    if len(history.entries) < 2:
        print("You need at least two preserved Reflection Responses to compare.")
        return

    print("Your preserved Reflection Responses:")
    for number, entry in enumerate(history.entries, start=1):
        _print_pointer_line(number, entry)

    first_id = _prompt_for_selection(history, "\nFirst selection > ", input_fn)
    second_id = _prompt_for_selection(history, "Second selection > ", input_fn)

    try:
        comparison = ReflectionComparisonQuery(history).build(first_id, second_id)
    except ReflectionComparisonError as error:
        print(f"\n{error}")
        return

    _print_full_entry("First:", comparison.first)
    _print_full_entry("Second:", comparison.second)


if __name__ == "__main__":
    run()
