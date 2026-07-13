"""End-to-end proof that one complete Atlas Core Loop reasoning cycle can
be executed through the existing architecture (ATLAS-001 Core Loop).

Question -> Observation -> Interpretation -> Hypothesis -> Evidence ->
Conclusion -> Decision -> Outcome -> Evaluation -> Learning

Wires all ten application services directly against a single in-memory
SQLite engine (no FastAPI, no REST layer this increment — see
docs/CoreLoopATLAS001.md) and walks every step, asserting round-trip
correctness of every entity and link by id, and that each composite
service's not-found case is exercised negatively with nothing written.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.conclusion.capture_conclusion import (
    CaptureConclusionRequest,
    ConclusionService,
)
from atlas.core.application.decision.capture_decision import CaptureDecisionService
from atlas.core.application.evaluation.capture_evaluation import (
    CaptureEvaluationRequest,
    EvaluationService,
)
from atlas.core.application.evidence.capture_evidence import EvidenceService
from atlas.core.application.hypothesis.capture_hypothesis import HypothesisService
from atlas.core.application.interpretation.capture_interpretation import (
    CaptureInterpretationRequest,
    InterpretationService,
)
from atlas.core.application.learning.capture_learning import (
    CaptureLearningRequest,
    LearningService,
)
from atlas.core.application.observation.capture_observation import CaptureObservationService
from atlas.core.application.outcome.capture_outcome import CaptureOutcomeRequest, OutcomeService
from atlas.core.application.question.capture_question import (
    CaptureQuestionRequest,
    QuestionService,
)
from atlas.core.application.reasoning_link.capture_evidence_from_hypothesis import (
    CaptureEvidenceFromHypothesisRequest,
    CaptureEvidenceFromHypothesisService,
)
from atlas.core.application.reasoning_link.commit_decision_from_conclusion import (
    CommitDecisionFromConclusionRequest,
    CommitDecisionFromConclusionService,
)
from atlas.core.application.reasoning_link.form_hypothesis_from_interpretation import (
    FormHypothesisFromInterpretationRequest,
    FormHypothesisFromInterpretationService,
)
from atlas.core.application.reasoning_link.observe_from_question import (
    ObserveFromQuestionRequest,
    ObserveFromQuestionService,
)
from atlas.core.domain.conclusion.exceptions import ConclusionNotFoundError
from atlas.core.domain.conclusion.value_objects import ConclusionId
from atlas.core.domain.evaluation.exceptions import EvaluationNotFoundError
from atlas.core.domain.hypothesis.exceptions import HypothesisNotFoundError
from atlas.core.domain.hypothesis.value_objects import HypothesisId
from atlas.core.domain.interpretation.exceptions import InterpretationNotFoundError
from atlas.core.domain.interpretation.value_objects import InterpretationId
from atlas.core.domain.outcome.exceptions import DecisionNotFoundError, OutcomeNotFoundError
from atlas.core.domain.outcome.value_objects import OutcomeId
from atlas.core.domain.question.exceptions import QuestionNotFoundError
from atlas.core.domain.question.value_objects import QuestionId
from atlas.core.infrastructure.persistence.conclusion.sqlalchemy_repository import (
    SqlAlchemyConclusionRepository,
)
from atlas.core.infrastructure.persistence.conclusion.table import create_conclusion_table
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from atlas.core.infrastructure.persistence.evaluation.sqlalchemy_repository import (
    SqlAlchemyEvaluationRepository,
)
from atlas.core.infrastructure.persistence.evaluation.table import create_evaluation_table
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
from atlas.core.infrastructure.persistence.learning.sqlalchemy_repository import (
    SqlAlchemyLearningRepository,
)
from atlas.core.infrastructure.persistence.learning.table import create_learning_table
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table
from atlas.core.infrastructure.persistence.outcome.sqlalchemy_repository import (
    SqlAlchemyOutcomeRepository,
)
from atlas.core.infrastructure.persistence.outcome.table import create_outcome_table
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

_T0 = datetime(2026, 7, 13, 8, 0, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_question_table(eng)
    create_observation_table(eng)
    create_interpretation_table(eng)
    create_hypothesis_table(eng)
    create_evidence_table(eng)
    create_conclusion_table(eng)
    create_decision_table(eng)
    create_outcome_table(eng)
    create_evaluation_table(eng)
    create_learning_table(eng)
    create_reasoning_link_tables(eng)
    return eng


@pytest.fixture
def services(engine):
    question_repository = SqlAlchemyQuestionRepository(engine)
    observation_repository = SqlAlchemyObservationRepository(engine)
    interpretation_repository = SqlAlchemyInterpretationRepository(engine)
    hypothesis_repository = SqlAlchemyHypothesisRepository(engine)
    evidence_repository = SqlAlchemyEvidenceRepository(engine)
    conclusion_repository = SqlAlchemyConclusionRepository(engine)
    decision_repository = SqlAlchemyDecisionRepository(engine)
    outcome_repository = SqlAlchemyOutcomeRepository(engine)
    evaluation_repository = SqlAlchemyEvaluationRepository(engine)
    learning_repository = SqlAlchemyLearningRepository(engine)

    question_observation_links = SqlAlchemyQuestionObservationLinkRepository(engine)
    interpretation_hypothesis_links = SqlAlchemyInterpretationHypothesisLinkRepository(engine)
    hypothesis_evidence_links = SqlAlchemyHypothesisEvidenceLinkRepository(engine)
    conclusion_decision_links = SqlAlchemyConclusionDecisionLinkRepository(engine)

    observation_service = CaptureObservationService(observation_repository)
    hypothesis_service = HypothesisService(hypothesis_repository)
    evidence_service = EvidenceService(evidence_repository)
    decision_service = CaptureDecisionService(decision_repository)

    return {
        "question": QuestionService(question_repository),
        "observe_from_question": ObserveFromQuestionService(
            question_repository, observation_service, question_observation_links
        ),
        "interpretation": InterpretationService(
            observation_repository, interpretation_repository
        ),
        "form_hypothesis": FormHypothesisFromInterpretationService(
            interpretation_repository, hypothesis_service, interpretation_hypothesis_links
        ),
        "capture_evidence": CaptureEvidenceFromHypothesisService(
            hypothesis_repository, evidence_service, hypothesis_evidence_links
        ),
        "conclusion": ConclusionService(evidence_repository, conclusion_repository),
        "commit_decision": CommitDecisionFromConclusionService(
            conclusion_repository, decision_service, conclusion_decision_links
        ),
        "outcome": OutcomeService(decision_repository, outcome_repository),
        "evaluation": EvaluationService(outcome_repository, evaluation_repository),
        "learning": LearningService(evaluation_repository, learning_repository),
        # repositories, exposed for round-trip assertions
        "question_repository": question_repository,
        "observation_repository": observation_repository,
        "interpretation_repository": interpretation_repository,
        "hypothesis_repository": hypothesis_repository,
        "evidence_repository": evidence_repository,
        "conclusion_repository": conclusion_repository,
        "decision_repository": decision_repository,
        "outcome_repository": outcome_repository,
        "evaluation_repository": evaluation_repository,
        "learning_repository": learning_repository,
    }


class TestCompleteReasoningCycle:
    def test_walks_all_ten_steps_question_to_learning(self, services):
        # 1. Question
        question = services["question"].capture(
            CaptureQuestionRequest(
                statement="Is demand for AI infrastructure accelerating?",
                raised_at=_T0,
            )
        )

        # 2. Observation (answering the Question)
        observe_result = services["observe_from_question"].observe(
            ObserveFromQuestionRequest(
                question_id=question.id.value,
                subject="Semiconductor sector",
                statement="Several companies raised capex guidance.",
                observed_at=_T0 + timedelta(hours=1),
            )
        )
        observation = observe_result.observation

        # 3. Interpretation (of the Observation)
        interpretation = services["interpretation"].capture(
            CaptureInterpretationRequest(
                observation_id=observation.id.value,
                statement="This suggests demand may be accelerating.",
                interpreted_at=_T0 + timedelta(hours=2),
            )
        )

        # 4. Hypothesis (formed from the Interpretation)
        form_result = services["form_hypothesis"].form(
            FormHypothesisFromInterpretationRequest(
                interpretation_id=interpretation.id.value,
                statement="Demand for AI infrastructure may be accelerating.",
                formulated_at=_T0 + timedelta(hours=3),
            )
        )
        hypothesis = form_result.hypothesis

        # 5. Evidence (captured against the Hypothesis)
        evidence_result = services["capture_evidence"].capture(
            CaptureEvidenceFromHypothesisRequest(
                hypothesis_id=hypothesis.id.value,
                statement="Order intake increased by 24 percent.",
                direction="SUPPORTS",
                observed_at=_T0 + timedelta(hours=4),
            )
        )
        evidence = evidence_result.evidence

        # 6. Conclusion (drawn from the Evidence)
        conclusion = services["conclusion"].capture(
            CaptureConclusionRequest(
                evidence_id=evidence.id.value,
                statement="The weight of evidence supports accelerating demand.",
                concluded_at=_T0 + timedelta(hours=5),
            )
        )

        # 7. Decision (committed from the Conclusion)
        commit_result = services["commit_decision"].commit(
            CommitDecisionFromConclusionRequest(
                conclusion_id=conclusion.id.value,
                user_id=uuid.uuid4(),
                decision_type="BUY",
                subject="NVIDIA",
                reason="Demand for AI infrastructure is accelerating.",
                confidence=80,
                decided_at=_T0 + timedelta(hours=6),
            )
        )
        decision = commit_result.decision

        # 8. Outcome (of the Decision)
        outcome = services["outcome"].capture(
            CaptureOutcomeRequest(
                decision_id=decision.id.value,
                statement="Revenue growth accelerated as expected.",
                occurred_at=_T0 + timedelta(days=90),
            )
        )

        # 9. Evaluation (of the Outcome)
        evaluation = services["evaluation"].capture(
            CaptureEvaluationRequest(
                outcome_id=outcome.id.value,
                statement="The decision proved correct; demand did accelerate.",
                evaluated_at=_T0 + timedelta(days=104),
            )
        )

        # 10. Learning (drawn from the Evaluation)
        learning = services["learning"].capture(
            CaptureLearningRequest(
                evaluation_id=evaluation.id.value,
                statement="Weigh capex guidance more heavily than headline revenue growth.",
                learned_at=_T0 + timedelta(days=105),
            )
        )

        # --- Round-trip every entity by id ---
        assert services["question_repository"].get(question.id) == question
        assert services["observation_repository"].get(observation.id) == observation
        assert services["interpretation_repository"].get(interpretation.id) == interpretation
        assert services["hypothesis_repository"].get(hypothesis.id) == hypothesis
        assert services["evidence_repository"].get(evidence.id) == evidence
        assert services["conclusion_repository"].get(conclusion.id) == conclusion
        assert services["decision_repository"].get(decision.id) == decision
        assert services["outcome_repository"].get(outcome.id) == outcome
        assert services["evaluation_repository"].get(evaluation.id) == evaluation
        assert services["learning_repository"].get(learning.id) == learning

        # --- Every FK field points correctly upstream ---
        assert interpretation.observation_id == observation.id
        assert conclusion.evidence_id == evidence.id
        assert outcome.decision_id == decision.id
        assert evaluation.outcome_id == outcome.id
        assert learning.evaluation_id == evaluation.id

        # --- The four bridge links connect the protected aggregates correctly ---
        assert observe_result.link.question_id == question.id
        assert observe_result.link.observation_id == observation.id
        assert form_result.link.interpretation_id == interpretation.id
        assert form_result.link.hypothesis_id == hypothesis.id
        assert evidence_result.link.hypothesis_id == hypothesis.id
        assert evidence_result.link.evidence_id == evidence.id
        assert commit_result.link.conclusion_id == conclusion.id
        assert commit_result.link.decision_id == decision.id


class TestNegativeCasesNothingIsWrittenOnFailure:
    def test_observe_from_unknown_question_writes_nothing(self, services):
        with pytest.raises(QuestionNotFoundError):
            services["observe_from_question"].observe(
                ObserveFromQuestionRequest(
                    question_id=QuestionId().value,
                    subject="Semiconductor sector",
                    statement="Several companies raised capex guidance.",
                    observed_at=_T0,
                )
            )
        assert services["observation_repository"].list_all() == []

    def test_interpret_unknown_observation_writes_nothing(self, services):
        from atlas.core.application.interpretation.capture_interpretation import (
            ObservationNotFoundError,
        )
        from atlas.core.domain.observation.value_objects import ObservationId

        with pytest.raises(ObservationNotFoundError):
            services["interpretation"].capture(
                CaptureInterpretationRequest(
                    observation_id=ObservationId().value,
                    statement="This suggests demand may be accelerating.",
                    interpreted_at=_T0,
                )
            )
        assert services["interpretation_repository"].list_all() == []

    def test_form_hypothesis_from_unknown_interpretation_writes_nothing(self, services):
        with pytest.raises(InterpretationNotFoundError):
            services["form_hypothesis"].form(
                FormHypothesisFromInterpretationRequest(
                    interpretation_id=InterpretationId().value,
                    statement="Demand for AI infrastructure may be accelerating.",
                    formulated_at=_T0,
                )
            )
        assert services["hypothesis_repository"].list_all() == []

    def test_capture_evidence_from_unknown_hypothesis_writes_nothing(self, services):
        with pytest.raises(HypothesisNotFoundError):
            services["capture_evidence"].capture(
                CaptureEvidenceFromHypothesisRequest(
                    hypothesis_id=HypothesisId().value,
                    statement="Order intake increased by 24 percent.",
                    direction="SUPPORTS",
                    observed_at=_T0,
                )
            )
        assert services["evidence_repository"].list_all() == []

    def test_conclude_from_unknown_evidence_writes_nothing(self, services):
        from atlas.core.domain.evidence.exceptions import EvidenceNotFoundError
        from atlas.core.domain.evidence.value_objects import EvidenceId

        with pytest.raises(EvidenceNotFoundError):
            services["conclusion"].capture(
                CaptureConclusionRequest(
                    evidence_id=EvidenceId().value,
                    statement="The weight of evidence supports accelerating demand.",
                    concluded_at=_T0,
                )
            )
        assert services["conclusion_repository"].list_all() == []

    def test_commit_decision_from_unknown_conclusion_writes_nothing(self, services):
        with pytest.raises(ConclusionNotFoundError):
            services["commit_decision"].commit(
                CommitDecisionFromConclusionRequest(
                    conclusion_id=ConclusionId().value,
                    user_id=uuid.uuid4(),
                    decision_type="BUY",
                    subject="NVIDIA",
                    reason="Demand for AI infrastructure is accelerating.",
                    confidence=80,
                    decided_at=_T0,
                )
            )
        assert services["decision_repository"].list_all() == []

    def test_capture_outcome_of_unknown_decision_writes_nothing(self, services):
        from atlas.core.domain.decision.value_objects import DecisionId

        with pytest.raises(DecisionNotFoundError):
            services["outcome"].capture(
                CaptureOutcomeRequest(
                    decision_id=DecisionId().value,
                    statement="Revenue growth accelerated as expected.",
                    occurred_at=_T0,
                )
            )
        assert services["outcome_repository"].list_all() == []

    def test_evaluate_unknown_outcome_writes_nothing(self, services):
        with pytest.raises(OutcomeNotFoundError):
            services["evaluation"].capture(
                CaptureEvaluationRequest(
                    outcome_id=OutcomeId().value,
                    statement="The decision proved correct; demand did accelerate.",
                    evaluated_at=_T0,
                )
            )
        assert services["evaluation_repository"].list_all() == []

    def test_learn_from_unknown_evaluation_writes_nothing(self, services):
        from atlas.core.domain.evaluation.value_objects import EvaluationId

        with pytest.raises(EvaluationNotFoundError):
            services["learning"].capture(
                CaptureLearningRequest(
                    evaluation_id=EvaluationId().value,
                    statement="Weigh capex guidance more heavily than headline revenue growth.",
                    learned_at=_T0,
                )
            )
        assert services["learning_repository"].list_all() == []
