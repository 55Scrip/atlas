"""Decision Review session state (ATLAS-003).

DecisionReviewSession is, like ConversationSession before it, deliberately
NOT a domain aggregate: never persisted, never touches a repository, not
subject to this codebase's insert-only/immutability discipline, because
it is orchestration state — "which Decision, which step" — not domain
data.

A Decision Review always covers exactly three steps: Outcome, Evaluation,
Learning, in that order, for exactly one previously recorded Decision.
Each review produces one full, fresh Outcome -> Evaluation -> Learning
triple; it never attempts to detect or resume a partially-completed prior
review. If a person quits partway through — e.g. after Outcome but before
Evaluation — that Outcome simply exists with no Evaluation or Learning
attached. ATLAS-003 does not detect, resume, or repair that. Running a
review again against the same Decision produces a second, independent
Outcome, unrelated to the incomplete first one. See
docs/DecisionReviewATLAS003.md.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum, auto


class DecisionReviewStep(Enum):
    OUTCOME = auto()
    EVALUATION = auto()
    LEARNING = auto()
    REVIEW_RECORDED = auto()  # terminal state — the review stops here


@dataclass
class DecisionReviewSession:
    """Mutable, in-memory, per-review state, anchored to one Decision."""

    decision_id: uuid.UUID
    session_id: uuid.UUID = field(default_factory=uuid.uuid4)
    current_step: DecisionReviewStep = DecisionReviewStep.OUTCOME

    outcome_id: uuid.UUID | None = None
    evaluation_id: uuid.UUID | None = None
    learning_id: uuid.UUID | None = None

    # Partial answers collected so far for the *current* step.
    pending: dict[str, str] = field(default_factory=dict)

    def is_complete(self) -> bool:
        return self.current_step is DecisionReviewStep.REVIEW_RECORDED
