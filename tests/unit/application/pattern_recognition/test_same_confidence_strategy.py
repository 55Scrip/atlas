"""Tests for SameConfidenceStrategy (ATLAS-005B).

Constructed directly from a DecisionTimelineQuery built on real
SQLite-backed repositories, mirroring test_query.py's own fixture
pattern. Includes the concrete cross-strategy overlap proof required by
ATLAS-005B-P: a single Decision belonging to both a same_subject_and_type
Pattern and a same_confidence Pattern simultaneously.
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

_T0 = datetime(2026, 7, 14, 12, 0, 0, tzinfo=timezone.utc)
_RECOGNIZED_AT = datetime(2026, 7, 14, 15, 0, 0, tzinfo=timezone.utc)


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
def confidence_only_query(decision_timeline_query):
    strategy = SameConfidenceStrategy(clock=lambda: _RECOGNIZED_AT)
    return PatternRecognitionQuery(decision_timeline_query, strategies=(strategy,))


@pytest.fixture
def combined_query(decision_timeline_query):
    strategies = (
        SameSubjectAndTypeStrategy(clock=lambda: _RECOGNIZED_AT),
        SameConfidenceStrategy(clock=lambda: _RECOGNIZED_AT),
    )
    return PatternRecognitionQuery(decision_timeline_query, strategies=strategies)


def _make_decision(
    decision_repository, decided_at, subject="NVIDIA", decision_type="BUY", confidence=80
):
    service = CaptureDecisionService(decision_repository)
    return service.capture(
        CaptureDecisionRequest(
            user_id=uuid.uuid4(),
            decision_type=decision_type,
            subject=subject,
            reason="Demand is accelerating.",
            confidence=confidence,
            decided_at=decided_at,
        )
    )


class TestNoRecurrence:
    def test_no_decisions_yields_no_results(self, confidence_only_query):
        assert confidence_only_query.build() == ()

    def test_single_decision_yields_no_results(self, decision_repository, confidence_only_query):
        _make_decision(decision_repository, _T0, confidence=80)
        assert confidence_only_query.build() == ()

    def test_two_decisions_with_different_confidence_yield_no_results(
        self, decision_repository, confidence_only_query
    ):
        _make_decision(decision_repository, _T0, confidence=80)
        _make_decision(decision_repository, _T0, confidence=81)
        assert confidence_only_query.build() == ()


class TestSameConfidenceRecurrence:
    def test_two_matching_decisions_yield_one_recognized_pattern(
        self, decision_repository, confidence_only_query
    ):
        first = _make_decision(decision_repository, _T0, subject="NVIDIA", confidence=80)
        second = _make_decision(decision_repository, _T0, subject="AMD", confidence=80)

        results = confidence_only_query.build()

        assert len(results) == 1
        recognized = results[0]
        assert isinstance(recognized, RecognizedPattern)
        assert recognized.strategy_name == "same_confidence"
        assert set(recognized.member_decision_ids) == {first.id, second.id}
        assert recognized.description == "You recorded confidence 80 on 2 separate Decisions."
        assert recognized.recognized_at == _RECOGNIZED_AT

    def test_three_matching_decisions_are_all_members_of_one_recognized_pattern(
        self, decision_repository, confidence_only_query
    ):
        first = _make_decision(decision_repository, _T0, subject="NVIDIA", confidence=75)
        second = _make_decision(decision_repository, _T0, subject="AMD", confidence=75)
        third = _make_decision(decision_repository, _T0, subject="INTC", confidence=75)

        results = confidence_only_query.build()

        assert len(results) == 1
        assert set(results[0].member_decision_ids) == {first.id, second.id, third.id}


class TestCrossStrategyOverlap:
    def test_a_decision_can_belong_to_both_a_subject_type_pattern_and_a_confidence_pattern(
        self, decision_repository, combined_query
    ):
        # Two NVIDIA/BUY decisions (same_subject_and_type recurrence).
        shared = _make_decision(
            decision_repository, _T0, subject="NVIDIA", decision_type="BUY", confidence=90
        )
        _make_decision(
            decision_repository, _T0, subject="NVIDIA", decision_type="BUY", confidence=60
        )
        # A third, unrelated-subject decision sharing the shared Decision's
        # confidence value (same_confidence recurrence).
        _make_decision(
            decision_repository, _T0, subject="AMD", decision_type="SELL", confidence=90
        )

        results = combined_query.build()

        by_strategy = {recognized.strategy_name: recognized for recognized in results}
        assert set(by_strategy) == {"same_subject_and_type", "same_confidence"}

        subject_type_pattern = by_strategy["same_subject_and_type"]
        confidence_pattern = by_strategy["same_confidence"]

        assert shared.id in subject_type_pattern.member_decision_ids
        assert shared.id in confidence_pattern.member_decision_ids
