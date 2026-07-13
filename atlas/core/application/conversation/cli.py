"""Standalone CLI entry point for the First Decision Conversation (ATLAS-002).

    python -m atlas.core.application.conversation.cli

Deliberately separate from atlas/cli/main.py, which already imports the
unrelated, legacy atlas/conversation/ package (a stateless single-turn
question router — see docs/FirstDecisionConversationATLAS002.md for the
distinction). This script has zero imports to or from atlas/conversation/
and does not register anything inside atlas/cli/main.py.

No framework, no new dependency: a plain input()/print() loop. The
database comes from the shared, neutral infrastructure configuration
boundary (atlas/core/infrastructure/config/database.py, ATLAS-003) so a
Decision recorded here can be found again later by a Decision Review —
not a throwaway per-run database as in this file's original version.
"""
from __future__ import annotations

from atlas.core.application.conversation import prompts
from atlas.core.application.conversation.composition import (
    build_conversation_orchestrator,
    create_conversation_tables,
)
from atlas.core.infrastructure.config.database import create_database_engine


def run() -> None:
    engine = create_database_engine()
    create_conversation_tables(engine)
    orchestrator = build_conversation_orchestrator(engine)

    session = orchestrator.start()
    print(prompts.QUESTION_PROMPT)
    while not session.is_complete():
        answer = input("> ")
        turn = orchestrator.respond(session, answer)
        print(turn.prompt)


if __name__ == "__main__":
    run()
