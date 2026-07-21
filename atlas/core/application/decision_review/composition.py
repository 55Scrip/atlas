"""Composition root for Decision Review (ATLAS-003).

Wires exactly the four dependencies this review needs: a read-only
DecisionRepository, and the three existing, unmodified Outcome/
Evaluation/Learning services. Does not construct QuestionService or any
of the other First Decision Conversation services — this conversation
starts mid-cycle, not from Question. Does not create the questions/
observations/interpretations/hypotheses/evidence/conclusions tables
either — Decision Review only ever reads Decision, never anything
upstream of it.

Also wires `JudgmentService` (Evaluation-to-Judgment-Reduction-Design.md,
Package M2): after Learning succeeds, the orchestrator captures one
canonical Judgment characterizing the review's own Outcome, using the
Evaluation's own statement verbatim. `JudgmentService` requires one
repository per eligible subject-reference type by construction, so
`KnowledgeReferenceRepository`, `ObservationRepository`, and
`ReasoningTraceRepository` are constructed here too — each lazily wraps
the engine and touches no table until actually queried, and this
review's own subject is always exactly one Outcome reference, so those
three are never queried in practice. Their own tables are therefore
deliberately not created here (see `create_decision_review_tables`) —
only `judgments`, which every captured Judgment actually writes to.
`decision_repository`/`outcome_repository` are already constructed for
the existing services above and are reused directly, unmodified, for
`JudgmentService`.
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from atlas.core.application.decision_review.orchestrator import DecisionReviewOrchestrator
from atlas.core.application.evaluation.capture_evaluation import EvaluationService
from atlas.core.application.judgment.capture_judgment import JudgmentService
from atlas.core.application.learning.capture_learning import LearningService
from atlas.core.application.outcome.capture_outcome import OutcomeService
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from atlas.core.infrastructure.persistence.evaluation.sqlalchemy_repository import (
    SqlAlchemyEvaluationRepository,
)
from atlas.core.infrastructure.persistence.evaluation.table import create_evaluation_table
from atlas.core.infrastructure.persistence.judgment.sqlalchemy_repository import (
    SqlAlchemyJudgmentRepository,
)
from atlas.core.infrastructure.persistence.judgment.table import create_judgment_table
from atlas.core.infrastructure.persistence.knowledge_reference.sqlalchemy_repository import (
    SqlAlchemyKnowledgeReferenceRepository,
)
from atlas.core.infrastructure.persistence.learning.sqlalchemy_repository import (
    SqlAlchemyLearningRepository,
)
from atlas.core.infrastructure.persistence.learning.table import create_learning_table
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.outcome.sqlalchemy_repository import (
    SqlAlchemyOutcomeRepository,
)
from atlas.core.infrastructure.persistence.outcome.table import create_outcome_table
from atlas.core.infrastructure.persistence.reasoning_trace.sqlalchemy_repository import (
    SqlAlchemyReasoningTraceRepository,
)


def create_decision_review_tables(engine: Engine) -> None:
    """Create every table Decision Review needs, plus the Judgment table
    the post-Learning write (Package M2) uses.

    Deliberately does not create the knowledge_references/observations/
    reasoning_traces tables — this review never reads or writes any of
    them: the Judgment captured here always cites exactly one Outcome
    as its sole subject, never a Knowledge Reference, Observation, or
    Reasoning Trace. Also does not create the questions/.../conclusions
    tables, since Decision Review never reads or writes anything
    upstream of Decision itself.
    """
    create_decision_table(engine)
    create_outcome_table(engine)
    create_evaluation_table(engine)
    create_learning_table(engine)
    create_judgment_table(engine)


def build_decision_review_orchestrator(engine: Engine) -> DecisionReviewOrchestrator:
    decision_repository = SqlAlchemyDecisionRepository(engine)
    outcome_repository = SqlAlchemyOutcomeRepository(engine)
    evaluation_repository = SqlAlchemyEvaluationRepository(engine)
    learning_repository = SqlAlchemyLearningRepository(engine)
    judgment_repository = SqlAlchemyJudgmentRepository(engine)
    knowledge_reference_repository = SqlAlchemyKnowledgeReferenceRepository(engine)
    observation_repository = SqlAlchemyObservationRepository(engine)
    reasoning_trace_repository = SqlAlchemyReasoningTraceRepository(engine)

    return DecisionReviewOrchestrator(
        decision_repository=decision_repository,
        outcome_service=OutcomeService(decision_repository, outcome_repository),
        evaluation_service=EvaluationService(outcome_repository, evaluation_repository),
        learning_service=LearningService(evaluation_repository, learning_repository),
        judgment_service=JudgmentService(
            judgment_repository,
            knowledge_reference_repository,
            observation_repository,
            decision_repository,
            outcome_repository,
            reasoning_trace_repository,
        ),
    )
