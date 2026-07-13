"""Standalone CLI entry point for Decision Review (ATLAS-003).

    python -m atlas.core.application.decision_review.cli

Deliberately separate from atlas/cli/main.py and from atlas/conversation/
— same independence discipline as the First Decision Conversation CLI.
Uses the same shared, neutral database configuration
(atlas/core/infrastructure/config/database.py) as that CLI, so a
Decision recorded by one process can be found and reviewed by a later,
separate run of this one.
"""
from __future__ import annotations

from atlas.core.application.decision_review import prompts
from atlas.core.application.decision_review.composition import (
    build_decision_review_orchestrator,
    create_decision_review_tables,
)
from atlas.core.application.decision_review.lookup import format_decision_for_selection
from atlas.core.infrastructure.config.database import create_database_engine


def run() -> None:
    engine = create_database_engine()
    create_decision_review_tables(engine)
    orchestrator = build_decision_review_orchestrator(engine)

    numbered_decisions = orchestrator.list_decisions()
    if not numbered_decisions:
        print(prompts.NO_DECISIONS_MESSAGE)
        return

    print(prompts.SELECTION_HEADER)
    for number, decision in numbered_decisions:
        print(format_decision_for_selection(number, decision))

    session = None
    while session is None:
        answer = input("> ")
        session = orchestrator.select(numbered_decisions, answer)
        if session is None:
            print(prompts.SELECTION_REASK_PROMPT)

    print(prompts.OUTCOME_PROMPT)
    while not session.is_complete():
        answer = input("> ")
        turn = orchestrator.respond(session, answer)
        print(turn.prompt)


if __name__ == "__main__":
    run()
