"""Tests for DecisionReflectionQuery (ATLAS-007).

Covers: no correspondence, Pattern-grounded, Strategy-Signature-grounded
(with the single-pass identity proof and invariant-14 proof),
deterministic priority selection, ReasoningContext canonicalization, the
two/three-Decision scenario proving the in-progress Decision never
counts toward its own grounding Pattern, and a runtime "never writes"
proof across the full dependency chain.
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
from atlas.core.application.decision_reflection.query import DecisionReflectionQuery
from atlas.core.application.decision_reflection.reasoning_context import ReasoningContext
from atlas.core.application.decision_reflection.reflection import DecisionReflection
from atlas.core.application.decision_timeline.query import DecisionTimelineQuery
from atlas.core.application.pattern_recognition.query import PatternRecognitionQuery
from atlas.core.application.pattern_recognition.strategies import (
    SameConfidenceStrategy,
    SameSubjectAndTypeStrategy,
)
from atlas.core.application.strategy_signature.query import StrategySignatureRecognitionQuery
from atlas.core.application.strategy_signature.strategies import ConnectedPatternsStrategy
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
_REFLECTED_AT = datetime(2026, 7, 15, 15, 30, 0, tzinfo=timezone.utc)


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


@pytest.fixture
def strategy_signature_recognition_query(pattern_recognition_query):
    return StrategySignatureRecognitionQuery(
        pattern_recognition_query,
        strategies=(ConnectedPatternsStrategy(clock=lambda: _RECOGNIZED_AT),),
    )


@pytest.fixture
def decision_reflection_query(pattern_recognition_query, strategy_signature_recognition_query):
    return DecisionReflectionQuery(
        pattern_recognition_query,
        strategy_signature_recognition_query,
        clock=lambda: _REFLECTED_AT,
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


class TestNoCorrespondence:
    def test_empty_context_yields_no_reflection(self, decision_reflection_query):
        assert decision_reflection_query.reflect(ReasoningContext()) is None

    def test_no_decisions_recorded_yields_no_reflection(self, decision_reflection_query):
        context = ReasoningContext(subject="NVIDIA", decision_type="BUY")
        assert decision_reflection_query.reflect(context) is None

    def test_one_prior_matching_decision_is_not_enough_for_a_pattern(
        self, decision_repository, decision_reflection_query
    ):
        # SameSubjectAndTypeStrategy requires 2+ already-recorded Decisions.
        # A single recorded Decision plus the in-progress one is still
        # only one recorded Decision — the in-progress Decision never
        # counts, since it is not yet persisted.
        _make_decision(decision_repository, _T0, "NVIDIA", "BUY", 90)

        context = ReasoningContext(subject="NVIDIA", decision_type="BUY")

        assert decision_reflection_query.reflect(context) is None


class TestPatternGroundedReflection:
    def test_two_prior_matching_decisions_ground_a_reflection_for_a_third(
        self, decision_repository, decision_reflection_query
    ):
        first = _make_decision(decision_repository, _T0, "NVIDIA", "BUY", 90)
        second = _make_decision(decision_repository, _T0, "NVIDIA", "BUY", 70)

        context = ReasoningContext(subject="NVIDIA", decision_type="BUY")
        reflection = decision_reflection_query.reflect(context)

        assert isinstance(reflection, DecisionReflection)
        assert reflection.pattern.strategy_name == "same_subject_and_type"
        assert set(reflection.pattern.member_decision_ids) == {first.id, second.id}
        assert reflection.strategy_signature is None
        assert reflection.reflected_at == _REFLECTED_AT

    def test_canonicalization_strips_whitespace_before_matching(
        self, decision_repository, decision_reflection_query
    ):
        _make_decision(decision_repository, _T0, "NVIDIA", "BUY", 90)
        _make_decision(decision_repository, _T0, "NVIDIA", "BUY", 70)

        context = ReasoningContext(subject="  NVIDIA  ", decision_type="BUY")
        reflection = decision_reflection_query.reflect(context)

        assert reflection is not None
        assert reflection.pattern.matching_key == ("NVIDIA", "BUY")


class TestStrategySignatureGroundedReflection:
    def test_reflection_attaches_the_signature_containing_the_winning_pattern(
        self, decision_repository, decision_reflection_query
    ):
        # Same three-Pattern chain proven in ATLAS-006: P1(NVIDIA/BUY) --d1--
        # P2(confidence 90) --d3-- P3(AMD/SELL). P1 and P3 share nothing
        # directly, yet all three are one connected Signature.
        _make_decision(decision_repository, _T0, "NVIDIA", "BUY", 90)
        _make_decision(decision_repository, _T0, "NVIDIA", "BUY", 70)
        _make_decision(decision_repository, _T0, "AMD", "SELL", 90)
        _make_decision(decision_repository, _T0, "AMD", "SELL", 60)

        context = ReasoningContext(subject="NVIDIA", decision_type="BUY")
        reflection = decision_reflection_query.reflect(context)

        assert reflection is not None
        assert reflection.strategy_signature is not None
        assert len(reflection.strategy_signature.member_patterns) == 3

        # Invariant 14: the Signature is relevant only because the winning
        # Pattern is genuinely one of its constituents.
        assert reflection.pattern in reflection.strategy_signature.member_patterns

        # Single-pass guarantee: the exact same object, not merely an
        # equal one — proving no second Pattern Recognition pass occurred.
        assert any(
            reflection.pattern is member
            for member in reflection.strategy_signature.member_patterns
        )


class TestDeterministicPrioritySelection:
    def test_same_subject_and_type_wins_over_same_confidence_when_both_match(
        self, decision_repository, decision_reflection_query
    ):
        # Pattern A: same_subject_and_type on (NVIDIA, BUY).
        _make_decision(decision_repository, _T0, "NVIDIA", "BUY", 90)
        _make_decision(decision_repository, _T0, "NVIDIA", "BUY", 70)
        # Pattern B: same_confidence on 80, unrelated subjects/types.
        _make_decision(decision_repository, _T0, "AMD", "SELL", 80)
        _make_decision(decision_repository, _T0, "TSLA", "HOLD", 80)

        # This in-progress context matches BOTH Patterns simultaneously.
        context = ReasoningContext(subject="NVIDIA", decision_type="BUY", confidence=80)
        reflection = decision_reflection_query.reflect(context)

        assert reflection is not None
        assert reflection.pattern.strategy_name == "same_subject_and_type"


class TestNeverWrites:
    def test_reflect_never_calls_add_on_any_repository(self, engine):
        class RaisingOnAdd:
            def __init__(self, wrapped):
                self._wrapped = wrapped

            def add(self, *args, **kwargs):
                raise AssertionError("DecisionReflectionQuery must never write")

            def __getattr__(self, name):
                return getattr(self._wrapped, name)

        real_decision_repository = SqlAlchemyDecisionRepository(engine)
        _make_decision(real_decision_repository, _T0, "NVIDIA", "BUY", 90)
        _make_decision(real_decision_repository, _T0, "NVIDIA", "BUY", 70)

        spy_timeline_query = DecisionTimelineQuery(
            decision_repository=RaisingOnAdd(real_decision_repository),
            outcome_repository=RaisingOnAdd(SqlAlchemyOutcomeRepository(engine)),
            evaluation_repository=RaisingOnAdd(SqlAlchemyEvaluationRepository(engine)),
            learning_repository=RaisingOnAdd(SqlAlchemyLearningRepository(engine)),
        )
        spy_pattern_query = PatternRecognitionQuery(
            spy_timeline_query,
            strategies=(
                SameSubjectAndTypeStrategy(clock=lambda: _RECOGNIZED_AT),
                SameConfidenceStrategy(clock=lambda: _RECOGNIZED_AT),
            ),
        )
        spy_signature_query = StrategySignatureRecognitionQuery(
            spy_pattern_query,
            strategies=(ConnectedPatternsStrategy(clock=lambda: _RECOGNIZED_AT),),
        )
        spy_reflection_query = DecisionReflectionQuery(
            spy_pattern_query, spy_signature_query, clock=lambda: _REFLECTED_AT
        )

        context = ReasoningContext(subject="NVIDIA", decision_type="BUY")
        reflection = spy_reflection_query.reflect(context)  # must not raise

        assert reflection is not None
