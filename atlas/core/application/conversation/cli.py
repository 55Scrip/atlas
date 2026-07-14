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

ATLAS-007's second disclosed touch to this file: an optional Decision
Reflection is checked for, and printed if found, immediately after the
decision type is captured and before confidence is asked. This is purely
additive — session.py, orchestrator.py, and prompts.py are all
unmodified, and the check reads only fields ConversationSession already
exposes publicly. Nothing about the Reflection's presence or absence
changes turn.prompt, session state, or what gets recorded.
"""
from __future__ import annotations

from atlas.core.application.conversation import prompts
from atlas.core.application.conversation.composition import (
    build_conversation_orchestrator,
    create_conversation_tables,
)
from atlas.core.application.conversation.session import ConversationSession, ConversationStep
from atlas.core.application.decision_reflection.composition import (
    build_decision_reflection_query,
    create_decision_reflection_tables,
)
from atlas.core.application.decision_reflection.query import DecisionReflectionQuery
from atlas.core.application.decision_reflection.reasoning_context import ReasoningContext
from atlas.core.infrastructure.config.database import create_database_engine


def _maybe_print_reflection(
    decision_reflection_query: DecisionReflectionQuery, session: ConversationSession
) -> None:
    if not (
        session.current_step is ConversationStep.DECISION
        and "decision_type" in session.pending
    ):
        return
    context = ReasoningContext(
        subject=session.observation_subject,
        decision_type=session.pending["decision_type"],
    )
    reflection = decision_reflection_query.reflect(context)
    if reflection is not None:
        print(f"(Reflection) {reflection.description}")


def run() -> None:
    engine = create_database_engine()
    create_conversation_tables(engine)
    create_decision_reflection_tables(engine)
    orchestrator = build_conversation_orchestrator(engine)
    decision_reflection_query = build_decision_reflection_query(engine)

    session = orchestrator.start()
    print(prompts.QUESTION_PROMPT)
    while not session.is_complete():
        answer = input("> ")
        turn = orchestrator.respond(session, answer)
        _maybe_print_reflection(decision_reflection_query, session)
        print(turn.prompt)


if __name__ == "__main__":
    run()
