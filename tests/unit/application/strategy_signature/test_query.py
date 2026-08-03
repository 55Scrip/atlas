"""Tests for StrategySignatureRecognitionQuery / ConnectedPatternsStrategy (ATLAS-006).

Two test styles: algorithmic tests construct RecognizedPattern instances
directly to prove the connectivity rule precisely (partition property,
chains vs. isolated patterns, ordering, identity/metadata separation,
description playing no role in membership); an end-to-end test builds
real Decisions through CaptureDecisionService and the two real Pattern
Recognition strategies (ATLAS-005/005B) to prove a three-Pattern chain
is achievable in practice, not just with test doubles.
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
from atlas.core.application.pattern_recognition.query import PatternRecognitionQuery
from atlas.core.application.pattern_recognition.recognized_pattern import RecognizedPattern
from atlas.core.application.pattern_recognition.strategies import (
    SameConfidenceStrategy,
    SameSubjectAndTypeStrategy,
)
from atlas.core.application.strategy_signature.query import StrategySignatureRecognitionQuery
from atlas.core.application.strategy_signature.recognized_strategy_signature import (
    RecognizedStrategySignature,
)
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
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table
from atlas.core.infrastructure.persistence.outcome.sqlalchemy_repository import (
    SqlAlchemyOutcomeRepository,
)
from atlas.core.infrastructure.persistence.outcome.table import create_outcome_table

_T0 = datetime(2026, 7, 14, 12, 0, 0, tzinfo=timezone.utc)
_RECOGNIZED_AT = datetime(2026, 7, 14, 15, 0, 0, tzinfo=timezone.utc)


def _new_decision_id() -> DecisionId:
    return DecisionId()


def _fake_pattern(
    strategy_name: str, decision_ids: list, description: str = "fake"
) -> RecognizedPattern:
    return RecognizedPattern(
        strategy_name=strategy_name,
        member_decision_ids=tuple(decision_ids),
        description=description,
        recognized_at=_RECOGNIZED_AT,
    )


@pytest.fixture
def strategy():
    return ConnectedPatternsStrategy(clock=lambda: _RECOGNIZED_AT)


class TestIsolatedPatterns:
    def test_no_patterns_yields_no_signatures(self, strategy):
        assert strategy.recognize(()) == ()

    def test_a_single_pattern_yields_no_signature(self, strategy):
        pattern = _fake_pattern("same_subject_and_type", [_new_decision_id(), _new_decision_id()])
        assert strategy.recognize((pattern,)) == ()

    def test_two_patterns_sharing_no_decision_yield_no_signature(self, strategy):
        pattern_a = _fake_pattern("same_subject_and_type", [_new_decision_id(), _new_decision_id()])
        pattern_b = _fake_pattern("same_confidence", [_new_decision_id(), _new_decision_id()])
        assert strategy.recognize((pattern_a, pattern_b)) == ()


class TestConnectedComponent:
    def test_two_overlapping_patterns_yield_one_signature(self, strategy):
        shared = _new_decision_id()
        pattern_a = _fake_pattern("same_subject_and_type", [shared, _new_decision_id()])
        pattern_b = _fake_pattern("same_confidence", [shared, _new_decision_id()])

        results = strategy.recognize((pattern_a, pattern_b))

        assert len(results) == 1
        signature = results[0]
        assert isinstance(signature, RecognizedStrategySignature)
        assert signature.strategy_name == "connected_patterns"
        assert set(signature.member_patterns) == {pattern_a, pattern_b}

    def test_three_pattern_chain_is_recognized_as_one_signature(self, strategy):
        # A-B share d1; B-C share d2; A and C share nothing directly.
        d1, d2 = _new_decision_id(), _new_decision_id()
        pattern_a = _fake_pattern("s", [d1, _new_decision_id()], description="A")
        pattern_b = _fake_pattern("s", [d1, d2], description="B")
        pattern_c = _fake_pattern("s", [d2, _new_decision_id()], description="C")

        results = strategy.recognize((pattern_a, pattern_b, pattern_c))

        assert len(results) == 1
        assert set(results[0].member_patterns) == {pattern_a, pattern_b, pattern_c}

    def test_two_separate_components_yield_two_signatures(self, strategy):
        shared_1 = _new_decision_id()
        pattern_a = _fake_pattern("s", [shared_1, _new_decision_id()])
        pattern_b = _fake_pattern("s", [shared_1, _new_decision_id()])

        shared_2 = _new_decision_id()
        pattern_c = _fake_pattern("s", [shared_2, _new_decision_id()])
        pattern_d = _fake_pattern("s", [shared_2, _new_decision_id()])

        results = strategy.recognize((pattern_a, pattern_b, pattern_c, pattern_d))

        assert len(results) == 2
        member_sets = {frozenset(sig.member_patterns) for sig in results}
        assert member_sets == {
            frozenset({pattern_a, pattern_b}),
            frozenset({pattern_c, pattern_d}),
        }


class TestPartitionProperty:
    def test_no_pattern_appears_in_more_than_one_signature(self, strategy):
        shared_1 = _new_decision_id()
        pattern_a = _fake_pattern("s", [shared_1, _new_decision_id()])
        pattern_b = _fake_pattern("s", [shared_1, _new_decision_id()])

        shared_2 = _new_decision_id()
        pattern_c = _fake_pattern("s", [shared_2, _new_decision_id()])
        pattern_d = _fake_pattern("s", [shared_2, _new_decision_id()])

        results = strategy.recognize((pattern_a, pattern_b, pattern_c, pattern_d))

        seen = [pattern for signature in results for pattern in signature.member_patterns]
        assert len(seen) == len(set(seen))


class TestIdentityMetadataSeparation:
    def test_same_member_patterns_are_the_same_signature_regardless_of_metadata(self):
        shared = _new_decision_id()
        pattern_a = _fake_pattern("same_subject_and_type", [shared, _new_decision_id()])
        pattern_b = _fake_pattern("same_confidence", [shared, _new_decision_id()])

        first = RecognizedStrategySignature(
            strategy_name="connected_patterns",
            member_patterns=(pattern_a, pattern_b),
            description="first description",
            recognized_at=_T0,
        )
        second = RecognizedStrategySignature(
            strategy_name="a_different_hypothetical_strategy",
            member_patterns=(pattern_a, pattern_b),
            description="a completely different description",
            recognized_at=_T0 + timedelta(days=1),
        )

        # Structural identity (invariant 2) is member_patterns alone —
        # these represent the same underlying Strategy Signature even
        # though strategy_name/recognized_at/description (metadata,
        # not identity) differ.
        assert first.member_patterns == second.member_patterns
        assert first.strategy_name != second.strategy_name
        assert first != second  # full dataclass equality still differs on metadata


class TestDeterministicOrdering:
    def test_member_patterns_within_a_signature_are_sorted_by_pattern_key(self, strategy):
        shared = _new_decision_id()
        later_key_pattern = _fake_pattern("zzz_strategy", [shared, _new_decision_id()])
        earlier_key_pattern = _fake_pattern("aaa_strategy", [shared, _new_decision_id()])

        results = strategy.recognize((later_key_pattern, earlier_key_pattern))

        assert len(results) == 1
        assert results[0].member_patterns == (earlier_key_pattern, later_key_pattern)

    def test_repeated_recognition_of_the_same_input_yields_the_same_order(self, strategy):
        shared = _new_decision_id()
        pattern_a = _fake_pattern("same_subject_and_type", [shared, _new_decision_id()])
        pattern_b = _fake_pattern("same_confidence", [shared, _new_decision_id()])

        first = strategy.recognize((pattern_b, pattern_a))
        second = strategy.recognize((pattern_a, pattern_b))

        assert first == second


class TestDescriptionPlaysNoRoleInMembership:
    def test_overlapping_decision_ids_group_together_despite_unrelated_descriptions(self, strategy):
        shared = _new_decision_id()
        pattern_a = _fake_pattern(
            "s", [shared, _new_decision_id()], description="Totally unrelated text."
        )
        pattern_b = _fake_pattern(
            "s", [shared, _new_decision_id()], description="Completely different wording."
        )

        results = strategy.recognize((pattern_a, pattern_b))

        assert len(results) == 1
        assert set(results[0].member_patterns) == {pattern_a, pattern_b}

    def test_disjoint_decision_ids_do_not_group_despite_similar_descriptions(self, strategy):
        pattern_a = _fake_pattern(
            "s", [_new_decision_id(), _new_decision_id()], description="Same wording here."
        )
        pattern_b = _fake_pattern(
            "s", [_new_decision_id(), _new_decision_id()], description="Same wording here."
        )

        results = strategy.recognize((pattern_a, pattern_b))

        assert results == ()


class TestTraceability:
    def test_every_decision_id_is_reachable_by_walking_member_patterns(self, strategy):
        shared = _new_decision_id()
        d_a = _new_decision_id()
        d_b = _new_decision_id()
        pattern_a = _fake_pattern("same_subject_and_type", [shared, d_a])
        pattern_b = _fake_pattern("same_confidence", [shared, d_b])

        signature = strategy.recognize((pattern_a, pattern_b))[0]

        reachable_ids = {
            decision_id
            for pattern in signature.member_patterns
            for decision_id in pattern.member_decision_ids
        }
        assert reachable_ids == {shared, d_a, d_b}


# ── End-to-end tests with real Decisions and real Pattern strategies ────────


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
def strategy_signature_query(pattern_recognition_query):
    return StrategySignatureRecognitionQuery(
        pattern_recognition_query,
        strategies=(ConnectedPatternsStrategy(clock=lambda: _RECOGNIZED_AT),),
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


class TestEndToEndWithRealStrategies:
    def test_three_pattern_chain_from_real_decisions_and_real_strategies(
        self, decision_repository, strategy_signature_query
    ):
        # NVIDIA/BUY conf=90, NVIDIA/BUY conf=70 -> same_subject_and_type Pattern P1={d1,d2}
        d1 = _make_decision(decision_repository, _T0, "NVIDIA", "BUY", 90)
        d2 = _make_decision(decision_repository, _T0, "NVIDIA", "BUY", 70)
        # AMD/SELL conf=90 shares confidence 90 with d1 -> same_confidence Pattern P2={d1,d3}
        d3 = _make_decision(decision_repository, _T0, "AMD", "SELL", 90)
        # AMD/SELL conf=60 shares subject+type with d3 -> same_subject_and_type Pattern P3={d3,d4}
        d4 = _make_decision(decision_repository, _T0, "AMD", "SELL", 60)

        signatures = strategy_signature_query.build()

        assert len(signatures) == 1
        signature = signatures[0]
        assert len(signature.member_patterns) == 3
        all_decision_ids = {
            decision_id
            for pattern in signature.member_patterns
            for decision_id in pattern.member_decision_ids
        }
        assert all_decision_ids == {d1.id, d2.id, d3.id, d4.id}


class TestNeverWritesEndToEnd:
    def test_build_never_calls_add_on_any_repository(self, engine):
        class RaisingOnAdd:
            def __init__(self, wrapped):
                self._wrapped = wrapped

            def add(self, *args, **kwargs):
                raise AssertionError("StrategySignatureRecognitionQuery must never write")

            def __getattr__(self, name):
                return getattr(self._wrapped, name)

        real_decision_repository = SqlAlchemyDecisionRepository(engine)
        _make_decision(real_decision_repository, _T0, "NVIDIA", "BUY", 90)
        _make_decision(real_decision_repository, _T0, "NVIDIA", "BUY", 70)
        _make_decision(real_decision_repository, _T0, "AMD", "SELL", 90)

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

        results = spy_signature_query.build()  # must not raise

        assert len(results) == 1
