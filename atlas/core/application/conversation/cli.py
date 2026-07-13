"""Standalone CLI entry point for the First Decision Conversation (ATLAS-002).

    python -m atlas.core.application.conversation.cli

Deliberately separate from atlas/cli/main.py, which already imports the
unrelated, legacy atlas/conversation/ package (a stateless single-turn
question router — see docs/FirstDecisionConversationATLAS002.md for the
distinction). This script has zero imports to or from atlas/conversation/
and does not register anything inside atlas/cli/main.py.

No framework, no new dependency: a plain input()/print() loop, its own
throwaway SQLite database file for this one conversation.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from sqlalchemy import create_engine

from atlas.core.application.conversation import prompts
from atlas.core.application.conversation.composition import (
    build_conversation_orchestrator,
    create_conversation_tables,
)


def run() -> None:
    db_path = Path(tempfile.mkdtemp()) / "atlas_conversation.db"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
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
