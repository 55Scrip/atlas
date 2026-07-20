"""End-to-end proof of the First Decision Conversation (ATLAS-002).

Scripts a full seven-step conversation (Question through Decision) purely
through ConversationOrchestrator.respond(), feeding answers
programmatically rather than via real input(). Asserts the final state is
traceable back through the chain, respecting each edge's actual
mechanism: direct FK field for Conclusion->Evidence and
Interpretation->Observation, the matching reasoning_link record for the
other three edges. Also asserts Outcome, Evaluation, and Learning are
never touched — their tables aren't even created by this conversation's
own composition root.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

from atlas.core.application.conversation.composition import (
    build_conversation_orchestrator,
    create_conversation_tables,
)
from atlas.core.application.conversation.session import ConversationStep
from atlas.core.domain.conclusion.value_objects import ConclusionId
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.evidence.value_objects import EvidenceId
from atlas.core.domain.hypothesis.value_objects import HypothesisId
from atlas.core.domain.interpretation.value_objects import InterpretationId
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.core.domain.question.value_objects import QuestionId
from atlas.core.infrastructure.persistence.conclusion.sqlalchemy_repository import (
    SqlAlchemyConclusionRepository,
)
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.evidence.sqlalchemy_repository import (
    SqlAlchemyEvidenceRepository,
)
from atlas.core.infrastructure.persistence.hypothesis.sqlalchemy_repository import (
    SqlAlchemyHypothesisRepository,
)
from atlas.core.infrastructure.persistence.interpretation.sqlalchemy_repository import (
    SqlAlchemyInterpretationRepository,
)
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.question.sqlalchemy_repository import (
    SqlAlchemyQuestionRepository,
)
from atlas.core.infrastructure.persistence.reasoning_link.sqlalchemy_repository import (
    SqlAlchemyConclusionDecisionLinkRepository,
    SqlAlchemyHypothesisEvidenceLinkRepository,
    SqlAlchemyInterpretationHypothesisLinkRepository,
    SqlAlchemyQuestionObservationLinkRepository,
)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_conversation_tables(eng)
    return eng


@pytest.fixture
def resolved_case_id():
    return uuid.uuid4()


@pytest.fixture
def orchestrator(engine, resolved_case_id):
    return build_conversation_orchestrator(engine, case_id=resolved_case_id)


SCRIPTED_ANSWERS = [
    "Is demand for AI infrastructure accelerating?",  # Question
    "Semiconductor sector",  # Observation subject
    "Several companies raised capex guidance.",  # Observation statement
    "This suggests demand may be accelerating.",  # Interpretation
    "Demand for AI infrastructure may be accelerating.",  # Hypothesis
    "Order intake increased by 24 percent.",  # Evidence statement
    "it supports it",  # Evidence direction
    "The weight of evidence supports accelerating demand.",  # Conclusion
    "buy",  # Decision type
    "80",  # Decision confidence
]


class TestCompleteConversation:
    def test_walks_all_seven_steps_question_to_decision(
        self, engine, orchestrator, resolved_case_id
    ):
        session = orchestrator.start()
        assert session.case_id == resolved_case_id
        turn = None
        for answer in SCRIPTED_ANSWERS:
            turn = orchestrator.respond(session, answer)

        assert session.is_complete()
        assert turn.is_complete
        assert session.current_step is ConversationStep.DECISION_RECORDED

        question_repo = SqlAlchemyQuestionRepository(engine)
        observation_repo = SqlAlchemyObservationRepository(engine)
        interpretation_repo = SqlAlchemyInterpretationRepository(engine)
        hypothesis_repo = SqlAlchemyHypothesisRepository(engine)
        evidence_repo = SqlAlchemyEvidenceRepository(engine)
        conclusion_repo = SqlAlchemyConclusionRepository(engine)
        decision_repo = SqlAlchemyDecisionRepository(engine)

        question_observation_links = SqlAlchemyQuestionObservationLinkRepository(engine)
        interpretation_hypothesis_links = SqlAlchemyInterpretationHypothesisLinkRepository(
            engine
        )
        hypothesis_evidence_links = SqlAlchemyHypothesisEvidenceLinkRepository(engine)
        conclusion_decision_links = SqlAlchemyConclusionDecisionLinkRepository(engine)

        # Every entity round-trips by id.
        question = question_repo.get(QuestionId(session.question_id))
        observation = observation_repo.get(ObservationId(session.observation_id))
        interpretation = interpretation_repo.get(InterpretationId(session.interpretation_id))
        hypothesis = hypothesis_repo.get(HypothesisId(session.hypothesis_id))
        evidence = evidence_repo.get(EvidenceId(session.evidence_id))
        conclusion = conclusion_repo.get(ConclusionId(session.conclusion_id))
        decision = decision_repo.get(DecisionId(session.decision_id))
        assert None not in (
            question,
            observation,
            interpretation,
            hypothesis,
            evidence,
            conclusion,
            decision,
        )

        # The persisted Observation carries exactly the session's own,
        # already-resolved CaseId — never a default, fabricated, or
        # session_id/investor_id-derived substitute.
        assert observation.case_id.value == resolved_case_id

        # Decision -> Conclusion via ConclusionDecisionLink.
        decision_links = conclusion_decision_links.list_by_decision_id(decision.id)
        assert [link.conclusion_id for link in decision_links] == [conclusion.id]

        # Conclusion -> Evidence via a direct FK field, not a link.
        assert conclusion.evidence_id == evidence.id

        # Evidence -> Hypothesis via HypothesisEvidenceLink.
        evidence_links = hypothesis_evidence_links.list_by_evidence_id(evidence.id)
        assert [link.hypothesis_id for link in evidence_links] == [hypothesis.id]

        # Hypothesis -> Interpretation via InterpretationHypothesisLink.
        hypothesis_links = interpretation_hypothesis_links.list_by_hypothesis_id(hypothesis.id)
        assert [link.interpretation_id for link in hypothesis_links] == [interpretation.id]

        # Interpretation -> Observation via a direct FK field, not a link.
        assert interpretation.observation_id == observation.id

        # Observation -> Question via QuestionObservationLink.
        observation_links = question_observation_links.list_by_observation_id(observation.id)
        assert [link.question_id for link in observation_links] == [question.id]

        # The Decision itself reflects the person's own words.
        assert decision.decision_type.value == "BUY"
        assert decision.confidence.value == 80
        assert decision.subject.value == "Semiconductor sector"
        assert decision.investment_case.reason == (
            "The weight of evidence supports accelerating demand."
        )

    def test_outcome_evaluation_learning_tables_are_never_created(self, engine, orchestrator):
        session = orchestrator.start()
        for answer in SCRIPTED_ANSWERS:
            orchestrator.respond(session, answer)

        table_names = set(inspect(engine).get_table_names())
        assert "outcomes" not in table_names
        assert "evaluations" not in table_names
        assert "learnings" not in table_names

    def test_closing_message_does_not_mention_outcome_evaluation_or_learning(
        self, orchestrator
    ):
        session = orchestrator.start()
        turn = None
        for answer in SCRIPTED_ANSWERS:
            turn = orchestrator.respond(session, answer)

        lowered = turn.prompt.lower()
        for forbidden in ("outcome", "evaluat", "learning", "what happened", "how did it go"):
            assert forbidden not in lowered
