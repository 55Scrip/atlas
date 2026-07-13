"""Conversation session state (ATLAS-002 First Decision Conversation).

ConversationSession is deliberately NOT a domain aggregate. It is never
persisted, never touches a repository, and is not subject to the
insert-only/immutability discipline that governs every atlas/core domain
aggregate — because it isn't domain data, it's orchestration state
answering "where are we in this conversation." It is a plain, mutable
object by design, exempt from the frozen-dataclass convention used
everywhere else in this codebase, because it belongs to a different layer
entirely: the application boundary, not the domain model.

This conversation covers exactly seven Core Loop steps — Question through
Decision. Outcome, Evaluation, and Learning have no values in
ConversationStep at all: their absence here is the scope boundary for
ATLAS-002, not an unused branch. A decision cannot honestly produce its
own outcome, evaluation, and learning in the same sitting it was made in
— those require real-world time to pass. See
docs/FirstDecisionConversationATLAS002.md.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum, auto


class ConversationStep(Enum):
    QUESTION = auto()
    OBSERVATION = auto()
    INTERPRETATION = auto()
    HYPOTHESIS = auto()
    EVIDENCE = auto()
    CONCLUSION = auto()
    DECISION = auto()
    DECISION_RECORDED = auto()  # terminal state — the conversation stops here


@dataclass
class ConversationSession:
    """Mutable, in-memory, per-conversation state.

    Not persisted: a First Decision Conversation is a single sitting, and
    is not designed to be resumed after a gap (see Alternatives Considered
    in docs/FirstDecisionConversationATLAS002.md).
    """

    session_id: uuid.UUID = field(default_factory=uuid.uuid4)
    current_step: ConversationStep = ConversationStep.QUESTION

    # One id per completed step, populated as each Core Loop service call
    # returns. None until that step is reached.
    question_id: uuid.UUID | None = None
    observation_id: uuid.UUID | None = None
    interpretation_id: uuid.UUID | None = None
    hypothesis_id: uuid.UUID | None = None
    evidence_id: uuid.UUID | None = None
    conclusion_id: uuid.UUID | None = None
    decision_id: uuid.UUID | None = None

    # Values already stated by the person, kept only so a later step can
    # default to them instead of asking again (Decision's subject/reason).
    observation_subject: str | None = None
    conclusion_statement: str | None = None

    # Partial answers collected so far for the *current* step, keyed by
    # field name (e.g. while eliciting Evidence's two fields in sequence).
    pending: dict[str, str] = field(default_factory=dict)

    def is_complete(self) -> bool:
        return self.current_step is ConversationStep.DECISION_RECORDED
