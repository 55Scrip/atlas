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

ATLAS-008's third disclosed touch: when a Reflection fires, Decision
Coach asks at most one fixed question, followed by a single, ephemeral
input() call — read once and unconditionally discarded, never passed to
ConversationOrchestrator, never inspected. This gives the investor a
genuine, separate opportunity to respond to Coach without that response
being silently miscategorized as an answer to the next real Core Loop
prompt (confidence). ConversationSession/ConversationStep gain no new
state from this — it is a CLI-level pause between two Core Loop turns,
never a Core Loop step itself.

ATLAS-009's fourth disclosed touch: if the investor's ephemeral response
to Coach is non-empty, one more explicit, optional question asks whether
they would like to keep it. Only an explicit "yes" constructs a
ProvisionalReflectionResponse — held in a local variable here, never on
ConversationSession, exactly like the Reflection/Coach objects
themselves. It becomes a durable ReflectionResponse only at the exact
moment session.current_step transitions to DECISION_RECORDED — i.e.,
only once Decision capture has already, unambiguously, succeeded.
Decision capture and Reflection Response capture are two separate
writes, not one transaction: CommitDecisionFromConclusionService is
untouched, and if the second write fails, the already-recorded Decision
is unaffected — the CLI reports the failure honestly rather than
retrying, duplicating, or rolling anything back. session.py,
orchestrator.py, prompts.py, and decision_coach/coach.py remain
completely unmodified.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable

from sqlalchemy.engine import Engine

from atlas.core.application.conversation import prompts
from atlas.core.application.conversation.composition import (
    build_conversation_orchestrator,
    create_conversation_tables,
    resolve_existing_case,
    resolve_new_case,
)
from atlas.core.application.conversation.session import ConversationSession, ConversationStep
from atlas.core.application.decision_coach.coach import select_coaching_question
from atlas.core.application.decision_reflection.composition import (
    build_decision_reflection_query,
    create_decision_reflection_tables,
)
from atlas.core.application.decision_reflection.query import DecisionReflectionQuery
from atlas.core.application.decision_reflection.reasoning_context import ReasoningContext
from atlas.core.application.reflection_response.capture_reflection_response import (
    CaptureReflectionResponseService,
)
from atlas.core.application.reflection_response.composition import (
    build_capture_reflection_response_service,
    create_reflection_response_tables,
)
from atlas.core.application.reflection_response.preservation_choice import (
    parse_preservation_choice,
)
from atlas.core.application.reflection_response.provisional_response import (
    ProvisionalReflectionResponse,
    build_provenance_snapshot,
)
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.infrastructure.config.database import create_database_engine


def _maybe_reflect_and_coach(
    decision_reflection_query: DecisionReflectionQuery,
    session: ConversationSession,
    provisional_response: ProvisionalReflectionResponse | None,
    input_fn: Callable[[str], str] = input,
) -> ProvisionalReflectionResponse | None:
    if not (
        session.current_step is ConversationStep.DECISION
        and "decision_type" in session.pending
    ):
        return provisional_response
    context = ReasoningContext(
        subject=session.observation_subject,
        decision_type=session.pending["decision_type"],
    )
    reflection = decision_reflection_query.reflect(context)
    if reflection is None:
        return provisional_response
    print(f"(Reflection) {reflection.description}")

    coaching_question = select_coaching_question(reflection)
    print(f"(Coach) {coaching_question.text}")
    print("(You may respond, or press Enter to continue.)")
    response_text = input_fn("> ")  # raw, exactly as typed — never stripped or altered

    if not response_text.strip():
        return provisional_response  # nothing to preserve; unchanged from ATLAS-008

    print("(Would you like to keep this response for your own future reference? yes/no)")
    choice = input_fn("> ")
    if not parse_preservation_choice(choice):
        return provisional_response  # explicit decline; discarded, exactly as before

    provenance = build_provenance_snapshot(reflection, coaching_question, context)
    return ProvisionalReflectionResponse(response_text=response_text, provenance=provenance)


def _maybe_commit_reflection_response(
    capture_reflection_response_service: CaptureReflectionResponseService,
    session: ConversationSession,
    provisional_response: ProvisionalReflectionResponse | None,
) -> None:
    if provisional_response is None:
        return
    try:
        capture_reflection_response_service.capture(
            provisional_response, decision_id=DecisionId(session.decision_id)
        )
    except Exception:
        # Decision capture already succeeded, independently, before this
        # second write was attempted — its failure never calls that into
        # question. No retry, no duplicate-write attempt, no rollback of
        # the Decision; the failure is reported, not swallowed.
        print(
            "(Note) Your decision was recorded, but the response you chose "
            "to keep could not be saved."
        )


def _resolve_case_id(engine: Engine, input_fn: Callable[[str], str] = input) -> uuid.UUID:
    """Require one explicit choice — new investigation, or continue an
    existing one — before the Question prompt or any Core Loop step.

    There is no blank-input default: an unrecognized answer re-asks the
    same question, an unparseable or unknown existing CaseId re-asks for
    the id only, and no Case is ever created to paper over either case
    (Core-Loop-Observation-Case-Context-Implementation-Design.md, Section
    19/31).
    """
    while True:
        choice = input_fn(
            "Start a new investigation, or continue an existing one? (new/continue) > "
        ).strip().lower()
        if choice == "new":
            case_id = resolve_new_case(engine)
            print(
                f"(New investigation started. Your Case id is {case_id} — "
                "save this if you want to continue it later.)"
            )
            return case_id
        if choice == "continue":
            while True:
                raw = input_fn("Enter the Case id to continue > ").strip()
                try:
                    candidate = uuid.UUID(raw)
                except ValueError:
                    print("(That doesn't look like a valid Case id — please try again.)")
                    continue
                resolved = resolve_existing_case(engine, candidate)
                if resolved is None:
                    print("(No investigation found with that id — please try again.)")
                    continue
                return resolved
        print("Sorry, please answer 'new' or 'continue'.")


def run() -> None:
    engine = create_database_engine()
    create_conversation_tables(engine)
    create_decision_reflection_tables(engine)
    create_reflection_response_tables(engine)
    case_id = _resolve_case_id(engine)
    orchestrator = build_conversation_orchestrator(engine, case_id=case_id)
    decision_reflection_query = build_decision_reflection_query(engine)
    capture_reflection_response_service = build_capture_reflection_response_service(engine)

    session = orchestrator.start()
    provisional_response: ProvisionalReflectionResponse | None = None
    print(prompts.QUESTION_PROMPT)
    while not session.is_complete():
        answer = input("> ")
        turn = orchestrator.respond(session, answer)

        if session.current_step is ConversationStep.DECISION_RECORDED:
            _maybe_commit_reflection_response(
                capture_reflection_response_service, session, provisional_response
            )
        else:
            provisional_response = _maybe_reflect_and_coach(
                decision_reflection_query, session, provisional_response
            )

        print(turn.prompt)


if __name__ == "__main__":
    run()
