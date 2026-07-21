"""Tests for StrategySignatureRecognitionQuery.recognize() (ATLAS-007 Prerequisite B).

recognize(recognized_patterns) lets a caller that already holds one
authoritative tuple of RecognizedPattern run Strategy Signature
Recognition without triggering a second Pattern Recognition pass.
build() must delegate through it with unchanged observable behavior.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.decision.capture_decision import (
    CaptureDecisionRequest,
    CaptureDecisionService,
)
from atlas.core.application.decision_timeline.query import DecisionTimelineQuery
from atlas.core.application.pattern_recognition.query import PatternRecognitionQuery
from atlas.core.application.pattern_recognition.recognized_pattern import RecognizedPattern
from atlas.core.application.pattern_recognition.strategies import (
    SameConfidenceStrategy,
    SameSubjectAndTypeStrategy,
)
from atlas.core.application.strategy_signature.query import StrategySignatureRecognitionQuery
from atlas.core.application.strategy_signature.strategies import ConnectedPatternsStrategy
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from atlas.core.infrastructure.persistence.evaluation.sqlalchemy_repository import (
    SqlAlchemyEvaluationRepository,
)
from atlas.core.infrastructure.persistence.evaluation.table import create_evaluation_table
from atlas.core.infrastructure.persistence.learning.sqlalchemy_repository import (
    SqlAlchemyLearningRepository,
)
from atlas.core.infrastructure.persistence.learning.table import create_learning_table
from atlas.core.infrastructure.persistence.outcome.sqlalchemy_repository import (
    SqlAlchemyOutcomeRepository,
)
from atlas.core.infrastructure.persistence.outcome.table import create_outcome_table

_T0 = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
_RECOGNIZED_AT = datetime(2026, 7, 15, 15, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(eng)
    create_outcome_table(eng)
    create_evaluation_table(eng)
    create_learning_table(eng)
    return eng


@pytest.fixture
def decision_repository(engine):
    return SqlAlchemyDecisionRepository(engine)


@pytest.fixture
def decision_timeline_query(engine, decision_repository):
    return DecisionTimelineQuery(
        decision_repository=decision_repository,
        outcome_repository=SqlAlchemyOutcomeRepository(engine),
        evaluation_repository=SqlAlchemyEvaluationRepository(engine),
        learning_repository=SqlAlchemyLearningRepository(engine),
    )


@pytest.fixture
def pattern_recognition_query(decision_timeline_query):
    return PatternRecognitionQuery(
        decision_timeline_query,
        strategies=(
            SameSubjectAndTypeStrategy(clock=lambda: _RECOGNIZED_AT),
            SameConfidenceStrategy(clock=lambda: _RECOGNIZED_AT),
        ),
    )


def _make_decision(decision_repository, decided_at, subject, decision_type, confidence):
    service = CaptureDecisionService(decision_repository)
    return service.capture(
        CaptureDecisionRequest(
            case_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            decision_type=decision_type,
            subject=subject,
            reason="Demand is accelerating.",
            confidence=confidence,
            decided_at=decided_at,
        )
    )


class TestRecognizeMatchesBuild:
    def test_recognize_given_builds_own_snapshot_matches_build_output(
        self, decision_repository, pattern_recognition_query
    ):
        _make_decision(decision_repository, _T0, "NVIDIA", "BUY", 90)
        _make_decision(decision_repository, _T0, "NVIDIA", "BUY", 70)
        _make_decision(decision_repository, _T0, "AMD", "SELL", 90)

        strategy_signature_query = StrategySignatureRecognitionQuery(
            pattern_recognition_query,
            strategies=(ConnectedPatternsStrategy(clock=lambda: _RECOGNIZED_AT),),
        )

        recognized_patterns = pattern_recognition_query.build()
        via_recognize = strategy_signature_query.recognize(recognized_patterns)
        via_build = strategy_signature_query.build()

        assert via_recognize == via_build


class TestRecognizeNeverCallsPatternRecognitionBuild:
    def test_recognize_does_not_invoke_the_pattern_recognition_query(self):
        class RaisingPatternRecognitionQuery:
            def build(self):
                raise AssertionError(
                    "recognize() must not call PatternRecognitionQuery.build()"
                )

        strategy_signature_query = StrategySignatureRecognitionQuery(
            RaisingPatternRecognitionQuery(),
            strategies=(ConnectedPatternsStrategy(clock=lambda: _RECOGNIZED_AT),),
        )

        shared = DecisionId()
        pattern_a = RecognizedPattern(
            strategy_name="same_subject_and_type",
            member_decision_ids=(shared, DecisionId()),
            description="a",
            recognized_at=_RECOGNIZED_AT,
            matching_key=("NVIDIA", "BUY"),
        )
        pattern_b = RecognizedPattern(
            strategy_name="same_confidence",
            member_decision_ids=(shared, DecisionId()),
            description="b",
            recognized_at=_RECOGNIZED_AT,
            matching_key=("90",),
        )

        results = strategy_signature_query.recognize((pattern_a, pattern_b))  # must not raise

        assert len(results) == 1
