"""Standalone CLI entry point for Decision Timeline (ATLAS-004).

    python -m atlas.core.application.decision_timeline.cli

Deliberately separate from atlas/cli/main.py and atlas/conversation/ —
same independence discipline as the First Decision Conversation and
Decision Review CLIs. Uses the same shared, neutral database
configuration (ATLAS-003) so it reads whatever those CLIs have already
recorded. Read-only throughout: nothing in this file, or anything it
calls, ever writes to any repository.
"""
from __future__ import annotations

from atlas.core.application.decision_timeline.composition import (
    build_decision_timeline_query,
    create_decision_timeline_tables,
)
from atlas.core.application.decision_timeline.timeline import DecisionTimelineEntry
from atlas.core.infrastructure.config.database import create_database_engine


def _describe_entry(number: int, entry: DecisionTimelineEntry) -> str:
    decision = entry.decision
    review_count = len(entry.review_chains)
    reviewed = f"reviewed {review_count}x" if review_count else "not yet reviewed"
    return (
        f"{number}. [{decision.decision_type.value}] {decision.subject.value} "
        f"(confidence {decision.confidence.value}, "
        f"decided {decision.decided_at.date()}, {reviewed})"
    )


def _print_detail(entry: DecisionTimelineEntry) -> None:
    decision = entry.decision
    print(f"\nDecision: {decision.decision_type.value} {decision.subject.value}")
    print(f"Confidence: {decision.confidence.value}")
    print(f"Decided: {decision.decided_at.isoformat()}")
    print(f"Reason: {decision.investment_case.reason}")

    if not entry.review_chains:
        print("\nNot yet reviewed.")
        return

    for chain_number, chain in enumerate(entry.review_chains, start=1):
        recorded_at = chain.outcome.recorded_at.isoformat()
        print(f"\nReview {chain_number} (outcome recorded {recorded_at}):")
        print(f"  Outcome: {chain.outcome.statement.value}")
        if not chain.evaluations:
            print("  (no evaluation recorded yet)")
            continue
        for evaluation_with_learnings in chain.evaluations:
            evaluation = evaluation_with_learnings.evaluation
            print(f"  Evaluation: {evaluation.statement.value}")
            if not evaluation_with_learnings.learnings:
                print("    (no learning recorded yet)")
                continue
            for learning in evaluation_with_learnings.learnings:
                print(f"    Learning: {learning.statement.value}")


def run() -> None:
    engine = create_database_engine()
    create_decision_timeline_tables(engine)
    query = build_decision_timeline_query(engine)
    timeline = query.build()

    if not timeline.entries:
        print("No decisions recorded yet. Have a First Decision Conversation first.")
        return

    print("Your decisions, in order:")
    for number, entry in enumerate(timeline.entries, start=1):
        print(_describe_entry(number, entry))

    print("\nType a number to see more detail, or press enter to quit.")
    while True:
        answer = input("> ").strip()
        if not answer:
            return
        try:
            choice = int(answer)
        except ValueError:
            print("Please type a number, or press enter to quit.")
            continue
        if not (1 <= choice <= len(timeline.entries)):
            print("Please type a number from the list above.")
            continue
        _print_detail(timeline.entries[choice - 1])


if __name__ == "__main__":
    run()
