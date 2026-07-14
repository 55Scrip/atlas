"""Composition root for the First Decision Conversation (ATLAS-002).

Wires exactly the seven services this conversation uses, plus the four
reasoning_link repositories its four composite steps depend on. Mirrors
the construction order already proven correct by
tests/unit/application/reasoning_link/test_core_loop_end_to_end.py.
Does not construct OutcomeService, EvaluationService, or LearningService
— those belong to a future review phase, not this conversation.
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from atlas.core.application.conclusion.capture_conclusion import ConclusionService
from atlas.core.application.conversation.orchestrator import ConversationOrchestrator
from atlas.core.application.decision.capture_decision import CaptureDecisionService
from atlas.core.application.evidence.capture_evidence import EvidenceService
from atlas.core.application.hypothesis.capture_hypothesis import HypothesisService
from atlas.core.application.interpretation.capture_interpretation import InterpretationService
from atlas.core.application.investor_identity.composition import (
    resolve_investor_identity,
)
from atlas.core.application.observation.capture_observation import CaptureObservationService
from atlas.core.application.question.capture_question import QuestionService
from atlas.core.application.reasoning_link.capture_evidence_from_hypothesis import (
    CaptureEvidenceFromHypothesisService,
)
from atlas.core.application.reasoning_link.commit_decision_from_conclusion import (
    CommitDecisionFromConclusionService,
)
from atlas.core.application.reasoning_link.form_hypothesis_from_interpretation import (
    FormHypothesisFromInterpretationService,
)
from atlas.core.application.reasoning_link.observe_from_question import (
    ObserveFromQuestionService,
)
from atlas.core.infrastructure.persistence.conclusion.sqlalchemy_repository import (
    SqlAlchemyConclusionRepository,
)
from atlas.core.infrastructure.persistence.conclusion.table import create_conclusion_table
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from atlas.core.infrastructure.persistence.evidence.sqlalchemy_repository import (
    SqlAlchemyEvidenceRepository,
)
from atlas.core.infrastructure.persistence.evidence.table import create_evidence_table
from atlas.core.infrastructure.persistence.hypothesis.sqlalchemy_repository import (
    SqlAlchemyHypothesisRepository,
)
from atlas.core.infrastructure.persistence.hypothesis.table import create_hypothesis_table
from atlas.core.infrastructure.persistence.interpretation.sqlalchemy_repository import (
    SqlAlchemyInterpretationRepository,
)
from atlas.core.infrastructure.persistence.interpretation.table import (
    create_interpretation_table,
)
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table
from atlas.core.infrastructure.persistence.question.sqlalchemy_repository import (
    SqlAlchemyQuestionRepository,
)
from atlas.core.infrastructure.persistence.question.table import create_question_table
from atlas.core.infrastructure.persistence.reasoning_link.sqlalchemy_repository import (
    SqlAlchemyConclusionDecisionLinkRepository,
    SqlAlchemyHypothesisEvidenceLinkRepository,
    SqlAlchemyInterpretationHypothesisLinkRepository,
    SqlAlchemyQuestionObservationLinkRepository,
)
from atlas.core.infrastructure.persistence.reasoning_link.table import (
    create_reasoning_link_tables,
)


def create_conversation_tables(engine: Engine) -> None:
    """Create every table this conversation's seven steps need.

    Deliberately does not create the outcomes/evaluations/learnings
    tables — this conversation never touches them.
    """
    create_question_table(engine)
    create_observation_table(engine)
    create_interpretation_table(engine)
    create_hypothesis_table(engine)
    create_evidence_table(engine)
    create_conclusion_table(engine)
    create_decision_table(engine)
    create_reasoning_link_tables(engine)


def build_conversation_orchestrator(engine: Engine) -> ConversationOrchestrator:
    investor_id = resolve_investor_identity(engine)

    question_repository = SqlAlchemyQuestionRepository(engine)
    observation_repository = SqlAlchemyObservationRepository(engine)
    interpretation_repository = SqlAlchemyInterpretationRepository(engine)
    hypothesis_repository = SqlAlchemyHypothesisRepository(engine)
    evidence_repository = SqlAlchemyEvidenceRepository(engine)
    conclusion_repository = SqlAlchemyConclusionRepository(engine)
    decision_repository = SqlAlchemyDecisionRepository(engine)

    question_observation_links = SqlAlchemyQuestionObservationLinkRepository(engine)
    interpretation_hypothesis_links = SqlAlchemyInterpretationHypothesisLinkRepository(engine)
    hypothesis_evidence_links = SqlAlchemyHypothesisEvidenceLinkRepository(engine)
    conclusion_decision_links = SqlAlchemyConclusionDecisionLinkRepository(engine)

    observation_service = CaptureObservationService(observation_repository)
    hypothesis_service = HypothesisService(hypothesis_repository)
    evidence_service = EvidenceService(evidence_repository)
    decision_service = CaptureDecisionService(decision_repository)

    return ConversationOrchestrator(
        question_service=QuestionService(question_repository),
        observe_from_question_service=ObserveFromQuestionService(
            question_repository, observation_service, question_observation_links
        ),
        interpretation_service=InterpretationService(
            observation_repository, interpretation_repository
        ),
        form_hypothesis_service=FormHypothesisFromInterpretationService(
            interpretation_repository, hypothesis_service, interpretation_hypothesis_links
        ),
        capture_evidence_service=CaptureEvidenceFromHypothesisService(
            hypothesis_repository, evidence_service, hypothesis_evidence_links
        ),
        conclusion_service=ConclusionService(evidence_repository, conclusion_repository),
        commit_decision_service=CommitDecisionFromConclusionService(
            conclusion_repository, decision_service, conclusion_decision_links
        ),
        investor_id=investor_id,
    )
