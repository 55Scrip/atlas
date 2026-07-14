"""Standalone CLI entry point for Reflection Exploration (ATLAS-012).

    python -m atlas.core.application.reflection_exploration.cli

Deliberately separate from atlas/cli/main.py and atlas/conversation/ —
same independence discipline as every other standalone CLI in this
lineage. Read-only throughout, aside from the one explicit, disclosed
Investor Identity bootstrap step (ATLAS-009B's own store-level
capability, reused verbatim, never performed by this file itself).

Atlas never suggests, infers, defaults, ranks, or automatically chooses
any member of a scope — every selection must come from the investor's
own input. No filtering, search, pagination, grouping, analysis, or
Decision Timeline / Reflection Comparison / Understanding integration.
"""
from __future__ import annotations

from collections.abc import Callable

from atlas.core.application.investor_identity.composition import (
    resolve_investor_identity,
)
from atlas.core.application.reflection_exploration.exceptions import (
    ReflectionExplorationError,
)
from atlas.core.application.reflection_exploration.query import ReflectionExplorationQuery
from atlas.core.application.reflection_history.composition import (
    build_reflection_history_query,
    create_reflection_history_tables,
)
from atlas.core.application.reflection_history.history import ReflectionHistory
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.value_objects import ReflectionResponseId
from atlas.core.infrastructure.config.database import create_database_engine


def _sorted_entries(history: ReflectionHistory) -> tuple[ReflectionResponse, ...]:
    # Presentation-consistency decision only: displaying entries in the
    # same (recorded_at, id.value) order the resulting Exploration will
    # itself use, so the numbers the investor sees line up with the
    # order their selection is displayed back in. Sorted explicitly
    # here rather than relying on ReflectionHistoryQuery's own ordering
    # incidentally holding.
    return tuple(
        sorted(history.entries, key=lambda response: (response.recorded_at, response.id.value))
    )


def _print_pointer_line(number: int, entry: ReflectionResponse) -> None:
    print(f"{number}. Recorded: {entry.recorded_at.isoformat()} — {entry.response_text.value}")


def _print_full_entry(entry: ReflectionResponse) -> None:
    provenance = entry.provenance
    print(f"\nRecorded: {entry.recorded_at.isoformat()}")
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
    ordered_entries: tuple[ReflectionResponse, ...],
    input_fn: Callable[[str], str] = input,
) -> tuple[ReflectionResponseId, ...]:
    prompt = (
        "\nType the numbers of the Reflection Responses to explore, "
        "separated by spaces, or press enter for an empty scope > "
    )
    while True:
        answer = input_fn(prompt).strip()
        if not answer:
            return ()

        tokens = answer.split()
        choices: list[int] = []
        for token in tokens:
            try:
                choices.append(int(token))
            except ValueError:
                choices = None
                break
        if choices is None or any(
            not (1 <= choice <= len(ordered_entries)) for choice in choices
        ):
            print("Please type only the numbers shown above, separated by spaces.")
            continue

        return tuple(ordered_entries[choice - 1].id for choice in choices)


def run(input_fn: Callable[[str], str] = input) -> None:
    engine = create_database_engine()
    create_reflection_history_tables(engine)
    owner_user_id = resolve_investor_identity(engine)
    history = build_reflection_history_query(engine, owner_user_id).build()

    if not history.entries:
        print("No Reflection Responses recorded yet.")
        return

    ordered_entries = _sorted_entries(history)
    print("Your preserved Reflection Responses:")
    for number, entry in enumerate(ordered_entries, start=1):
        _print_pointer_line(number, entry)

    selected_ids = _prompt_for_selection(ordered_entries, input_fn)

    try:
        exploration = ReflectionExplorationQuery(history).build(selected_ids)
    except ReflectionExplorationError as error:
        print(f"\n{error}")
        return

    if not exploration.entries:
        print("\nYour exploration is empty.")
        return

    print(f"\nYour exploration ({len(exploration.entries)} Reflection Response(s)):")
    for entry in exploration.entries:
        _print_full_entry(entry)


if __name__ == "__main__":
    run()
