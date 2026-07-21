"""Tests for PatternRecognitionQuery (ATLAS-005).

Constructs PatternRecognitionQuery directly from a DecisionTimelineQuery
built on real SQLite-backed repositories — proving Pattern Recognition
is independently testable and depends only on DecisionTimeline, never on
a repository or Engine directly.
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
from atlas.core.application.pattern_recognition.strategies import SameSubjectAndTypeStrategy
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
def query(decision_timeline_query):
    strategy = SameSubjectAndTypeStrategy(clock=lambda: _RECOGNIZED_AT)
    return PatternRecognitionQuery(decision_timeline_query, strategies=(strategy,))


def _make_decision(decision_repository, decided_at, subject="NVIDIA", decision_type="BUY"):
    service = CaptureDecisionService(decision_repository)
    return service.capture(
        CaptureDecisionRequest(
            case_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            decision_type=decision_type,
            subject=subject,
            reason="Demand is accelerating.",
            confidence=80,
            decided_at=decided_at,
        )
    )


class TestNoRecurrence:
    def test_no_decisions_yields_no_results(self, query):
        assert query.build() == ()

    def test_single_decision_yields_no_results(self, decision_repository, query):
        _make_decision(decision_repository, _T0)
        assert query.build() == ()

    def test_two_decisions_with_different_subjects_yield_no_results(
        self, decision_repository, query
    ):
        _make_decision(decision_repository, _T0, subject="NVIDIA")
        _make_decision(decision_repository, _T0, subject="AMD")
        assert query.build() == ()

    def test_two_decisions_with_same_subject_but_different_type_yield_no_results(
        self, decision_repository, query
    ):
        _make_decision(decision_repository, _T0, subject="NVIDIA", decision_type="BUY")
        _make_decision(decision_repository, _T0, subject="NVIDIA", decision_type="SELL")
        assert query.build() == ()


class TestSameSubjectAndTypeRecurrence:
    def test_two_matching_decisions_yield_one_recognized_pattern(
        self, decision_repository, query
    ):
        first = _make_decision(decision_repository, _T0, subject="NVIDIA", decision_type="BUY")
        second = _make_decision(decision_repository, _T0, subject="NVIDIA", decision_type="BUY")

        results = query.build()

        assert len(results) == 1
        recognized = results[0]
        assert isinstance(recognized, RecognizedPattern)
        assert recognized.strategy_name == "same_subject_and_type"
        assert set(recognized.member_decision_ids) == {first.id, second.id}
        assert recognized.description == "You have made 2 BUY decisions on NVIDIA."
        assert recognized.recognized_at == _RECOGNIZED_AT

    def test_traceability_matches_decision_timeline(
        self, decision_repository, decision_timeline_query, query
    ):
        first = _make_decision(decision_repository, _T0, subject="NVIDIA", decision_type="BUY")
        second = _make_decision(decision_repository, _T0, subject="NVIDIA", decision_type="BUY")
        _make_decision(decision_repository, _T0, subject="AMD", decision_type="BUY")

        recognized = query.build()[0]
        timeline = decision_timeline_query.build()

        expected_ids = {
            entry.decision.id
            for entry in timeline.entries
            if entry.decision.subject.value == "NVIDIA"
            and entry.decision.decision_type.value == "BUY"
        }
        assert expected_ids == {first.id, second.id}
        assert set(recognized.member_decision_ids) == expected_ids

    def test_three_matching_decisions_are_all_members_of_one_recognized_pattern(
        self, decision_repository, query
    ):
        first = _make_decision(decision_repository, _T0, subject="NVIDIA", decision_type="BUY")
        second = _make_decision(decision_repository, _T0, subject="NVIDIA", decision_type="BUY")
        third = _make_decision(decision_repository, _T0, subject="NVIDIA", decision_type="BUY")

        results = query.build()

        assert len(results) == 1
        assert set(results[0].member_decision_ids) == {first.id, second.id, third.id}


class TestStrategyExtensibility:
    def test_a_second_independent_strategy_runs_alongside_the_first_unmerged(
        self, decision_repository, decision_timeline_query
    ):
        class AlwaysRecognizesEverythingStrategy:
            name = "always_recognizes_everything"

            def recognize(self, timeline):
                if not timeline.entries:
                    return ()
                ids = tuple(entry.decision.id for entry in timeline.entries)
                return (
                    RecognizedPattern(
                        strategy_name=self.name,
                        member_decision_ids=ids,
                        description="Fake strategy result.",
                        recognized_at=_RECOGNIZED_AT,
                    ),
                )

        _make_decision(decision_repository, _T0, subject="NVIDIA", decision_type="BUY")
        _make_decision(decision_repository, _T0, subject="NVIDIA", decision_type="BUY")

        combined_query = PatternRecognitionQuery(
            decision_timeline_query,
            strategies=(
                SameSubjectAndTypeStrategy(clock=lambda: _RECOGNIZED_AT),
                AlwaysRecognizesEverythingStrategy(),
            ),
        )

        results = combined_query.build()

        strategy_names = {recognized.strategy_name for recognized in results}
        assert strategy_names == {"same_subject_and_type", "always_recognizes_everything"}
        assert len(results) == 2


class TestNeverWrites:
    def test_build_never_calls_add_on_any_repository(self, engine):
        class RaisingOnAdd:
            def __init__(self, wrapped):
                self._wrapped = wrapped

            def add(self, *args, **kwargs):
                raise AssertionError("PatternRecognitionQuery must never write")

            def __getattr__(self, name):
                return getattr(self._wrapped, name)

        real_decision_repository = SqlAlchemyDecisionRepository(engine)
        _make_decision(real_decision_repository, _T0, subject="NVIDIA", decision_type="BUY")
        _make_decision(real_decision_repository, _T0, subject="NVIDIA", decision_type="BUY")

        spy_timeline_query = DecisionTimelineQuery(
            decision_repository=RaisingOnAdd(real_decision_repository),
            outcome_repository=RaisingOnAdd(SqlAlchemyOutcomeRepository(engine)),
            evaluation_repository=RaisingOnAdd(SqlAlchemyEvaluationRepository(engine)),
            learning_repository=RaisingOnAdd(SqlAlchemyLearningRepository(engine)),
        )
        spy_query = PatternRecognitionQuery(
            spy_timeline_query, strategies=(SameSubjectAndTypeStrategy(),)
        )

        results = spy_query.build()  # must not raise

        assert len(results) == 1
