"""Decision Timeline data model (ATLAS-004).

None of these types is a domain aggregate: none carries its own identity,
none is ever persisted, and every instance is recomputed fresh on every
request by DecisionTimelineQuery.build() (query.py). They exist purely to
give a Decision's own already-recorded history a chronological shape —
nothing here adds a fact, forms a judgment, or invents cardinality the
domain doesn't have.

Naming note: atlas/memory/timeline.py already defines an unrelated
`Timeline`/`TimelineComparison` (a generic snapshot-diff view for a
different subsystem). Every type here uses the domain-specific
`Decision*` prefix so no bare `Timeline` concept is added alongside it —
see docs/DecisionTimelineATLAS004.md.
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.evaluation.entity import Evaluation
from atlas.core.domain.learning.entity import Learning
from atlas.core.domain.outcome.entity import Outcome


@dataclass(frozen=True)
class EvaluationWithLearnings:
    """One recorded Evaluation, and every Learning recorded against it.

    `learnings` may be empty — an Evaluation with no Learning yet is
    reflected exactly as that, not hidden or padded. Ordered by
    (learning.recorded_at, learning_id) — see query.py.
    """

    evaluation: Evaluation
    learnings: tuple[Learning, ...]


@dataclass(frozen=True)
class DecisionReviewChain:
    """One recorded Outcome, and every Evaluation recorded against it.

    `evaluations` may be empty — an Outcome with no Evaluation yet (an
    interrupted Decision Review, per ATLAS-003) is reflected exactly as
    that. More than one Evaluation per Outcome is legal and, when
    present, all of them are kept, never collapsed to one. Ordered by
    (evaluation.recorded_at, evaluation_id) — see query.py.
    """

    outcome: Outcome
    evaluations: tuple[EvaluationWithLearnings, ...]


@dataclass(frozen=True)
class DecisionTimelineEntry:
    """One Decision, and every review chain recorded against it.

    `review_chains` may be empty — a Decision never yet reviewed.
    Decision Review permits repeat reviews, so more than one chain (one
    per Outcome) is expected and all are kept. Ordered by
    (outcome.recorded_at, outcome_id) — see query.py.
    """

    decision: Decision
    review_chains: tuple[DecisionReviewChain, ...]


@dataclass(frozen=True)
class DecisionTimeline:
    """The full, ordered chronological arrangement of an investor's own
    Decisions. Ordered by (decision.decided_at, decision_id) — see
    query.py.
    """

    entries: tuple[DecisionTimelineEntry, ...]
