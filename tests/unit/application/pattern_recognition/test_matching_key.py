"""Tests for RecognizedPattern.matching_key (ATLAS-007 Prerequisite A).

matching_key retains the canonical grouping key each strategy already
computes internally, so a later consumer (Decision Reflection) can
compare against a specific Pattern using exact structured equality —
never by parsing `description` or dereferencing `member_decision_ids`.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.decision.capture_decision import (
    CaptureDecisionRequest,
    CaptureDecisionService,
)
from atlas.core.application.decision_timeline.query import DecisionTimelineQuery
from atlas.core.application.pattern_recognition.recognized_pattern import RecognizedPattern
from atlas.core.application.pattern_recognition.strategies import (
    SameConfidenceStrategy,
    SameSubjectAndTypeStrategy,
)
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
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table
from atlas.core.infrastructure.persistence.outcome.sqlalchemy_repository import (
    SqlAlchemyOutcomeRepository,
)
from atlas.core.infrastructure.persistence.outcome.table import create_outcome_table

_T0 = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(eng)
    create_observation_table(eng)
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


def _make_decision(decision_repository, decided_at, subject, decision_type, confidence):
    service = CaptureDecisionService(
        decision_repository, SqlAlchemyObservationRepository(decision_repository._engine)
    )
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


class TestDefaultBackwardCompatibility:
    def test_matching_key_defaults_to_empty_tuple(self):
        pattern = RecognizedPattern(
            strategy_name="same_subject_and_type",
            member_decision_ids=(),
            description="fake",
            recognized_at=_T0,
        )
        assert pattern.matching_key == ()

    def test_two_patterns_without_matching_key_remain_equal(self):
        first = RecognizedPattern(
            strategy_name="s", member_decision_ids=(), description="d", recognized_at=_T0
        )
        second = RecognizedPattern(
            strategy_name="s", member_decision_ids=(), description="d", recognized_at=_T0
        )
        assert first == second
        assert hash(first) == hash(second)


class TestSameSubjectAndTypeMatchingKey:
    def test_matching_key_is_subject_and_decision_type(
        self, decision_repository, decision_timeline_query
    ):
        _make_decision(decision_repository, _T0, "NVIDIA", "BUY", 90)
        _make_decision(decision_repository, _T0 + timedelta(hours=1), "NVIDIA", "BUY", 60)

        results = SameSubjectAndTypeStrategy().recognize(decision_timeline_query.build())

        assert len(results) == 1
        assert results[0].matching_key == ("NVIDIA", "BUY")


class TestSameConfidenceMatchingKey:
    def test_matching_key_is_stringified_confidence(
        self, decision_repository, decision_timeline_query
    ):
        _make_decision(decision_repository, _T0, "NVIDIA", "BUY", 90)
        _make_decision(decision_repository, _T0 + timedelta(hours=1), "AMD", "SELL", 90)

        results = SameConfidenceStrategy().recognize(decision_timeline_query.build())

        assert len(results) == 1
        assert results[0].matching_key == ("90",)
