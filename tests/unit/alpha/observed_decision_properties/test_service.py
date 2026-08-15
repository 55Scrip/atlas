"""Tests for `atlas.alpha.observed_decision_properties.service
.build_observed_decision_properties`. Real in-memory SQLite Decision
persistence throughout, via the real `SqlAlchemyDecisionRepository` and
`Decision.register` -- never a fake/mock repository, matching this
codebase's own established convention (e.g. `test_portfolio_status_v1
_scenarios.py`).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.observed_decision_properties.models import ObservedPropertyScope
from atlas.alpha.observed_decision_properties.service import build_observed_decision_properties
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionSource,
    InvestmentCase,
    Subject,
)
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import UserId
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import SqlAlchemyDecisionRepository
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_USER_ID = UserId(value=__import__("uuid").UUID("00000000-0000-0000-0000-000000000001"))


@pytest.fixture
def engine() -> Engine:
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_decision_table(engine)
    return engine


@pytest.fixture
def repository(engine: Engine) -> SqlAlchemyDecisionRepository:
    return SqlAlchemyDecisionRepository(engine)


def _register(
    repository: SqlAlchemyDecisionRepository,
    *,
    subject: str,
    decision_type: str,
    confidence: int,
    decided_at: datetime,
) -> Decision:
    decision = Decision.register(
        case_id=CaseId(),
        user_id=_USER_ID,
        decision_type=decision_type,
        subject=Subject(value=subject),
        investment_case=InvestmentCase(reason="Test reason."),
        confidence=Confidence(value=confidence),
        decided_at=decided_at,
        source=DecisionSource.MANUAL,
    )
    repository.add(decision)
    return decision


class TestEmptyAndSparseHistory:
    def test_zero_decisions_returns_empty_tuple(self, repository: SqlAlchemyDecisionRepository) -> None:
        assert build_observed_decision_properties(repository) == ()

    def test_one_decision_returns_empty_tuple(self, repository: SqlAlchemyDecisionRepository) -> None:
        _register(repository, subject="AMD", decision_type="BUY", confidence=70, decided_at=_t(0))
        assert build_observed_decision_properties(repository) == ()

    def test_two_unrelated_decisions_returns_empty_tuple(self, repository: SqlAlchemyDecisionRepository) -> None:
        _register(repository, subject="AMD", decision_type="BUY", confidence=70, decided_at=_t(0))
        _register(repository, subject="MSFT", decision_type="SELL", confidence=40, decided_at=_t(1))
        assert build_observed_decision_properties(repository) == ()

    def test_two_matching_decisions_produce_exactly_one_property_per_strategy(
        self, repository: SqlAlchemyDecisionRepository
    ) -> None:
        _register(repository, subject="AMD", decision_type="BUY", confidence=70, decided_at=_t(0))
        _register(repository, subject="AMD", decision_type="BUY", confidence=70, decided_at=_t(1))
        properties = build_observed_decision_properties(repository)
        # Same subject+type AND same confidence -- both strategies fire once each.
        assert {p.property_type for p in properties} == {"same_subject_and_type", "same_confidence"}
        for p in properties:
            assert p.observed_count == 2
            assert p.sample_size_warning is True


class TestEvidenceContract:
    def test_scope_is_single_company_for_subject_and_type(self, repository: SqlAlchemyDecisionRepository) -> None:
        _register(repository, subject="AMD", decision_type="BUY", confidence=70, decided_at=_t(0))
        _register(repository, subject="AMD", decision_type="BUY", confidence=80, decided_at=_t(1))
        properties = build_observed_decision_properties(repository)
        (prop,) = [p for p in properties if p.property_type == "same_subject_and_type"]
        assert prop.scope is ObservedPropertyScope.SINGLE_COMPANY

    def test_scope_is_portfolio_wide_for_confidence(self, repository: SqlAlchemyDecisionRepository) -> None:
        _register(repository, subject="AMD", decision_type="BUY", confidence=70, decided_at=_t(0))
        _register(repository, subject="MSFT", decision_type="SELL", confidence=70, decided_at=_t(1))
        properties = build_observed_decision_properties(repository)
        (prop,) = [p for p in properties if p.property_type == "same_confidence"]
        assert prop.scope is ObservedPropertyScope.PORTFOLIO_WIDE

    def test_denominator_for_subject_and_type_counts_all_decisions_for_that_subject(
        self, repository: SqlAlchemyDecisionRepository
    ) -> None:
        _register(repository, subject="AMD", decision_type="BUY", confidence=70, decided_at=_t(0))
        _register(repository, subject="AMD", decision_type="BUY", confidence=71, decided_at=_t(1))
        _register(repository, subject="AMD", decision_type="SELL", confidence=72, decided_at=_t(2))
        properties = build_observed_decision_properties(repository)
        (prop,) = [p for p in properties if p.property_type == "same_subject_and_type"]
        assert prop.observed_count == 2
        assert prop.total_eligible_decisions == 3  # 2 BUY + 1 SELL, all on AMD
        assert prop.proportion == pytest.approx(2 / 3)

    def test_denominator_for_confidence_counts_all_decisions(self, repository: SqlAlchemyDecisionRepository) -> None:
        _register(repository, subject="AMD", decision_type="BUY", confidence=70, decided_at=_t(0))
        _register(repository, subject="MSFT", decision_type="SELL", confidence=70, decided_at=_t(1))
        _register(repository, subject="TSLA", decision_type="HOLD", confidence=99, decided_at=_t(2))
        properties = build_observed_decision_properties(repository)
        (prop,) = [p for p in properties if p.property_type == "same_confidence"]
        assert prop.observed_count == 2
        assert prop.total_eligible_decisions == 3
        assert prop.proportion == pytest.approx(2 / 3)

    def test_supporting_decision_ids_are_real_and_traceable(self, repository: SqlAlchemyDecisionRepository) -> None:
        d1 = _register(repository, subject="AMD", decision_type="BUY", confidence=70, decided_at=_t(0))
        d2 = _register(repository, subject="AMD", decision_type="BUY", confidence=71, decided_at=_t(1))
        properties = build_observed_decision_properties(repository)
        (prop,) = [p for p in properties if p.property_type == "same_subject_and_type"]
        assert set(prop.supporting_decision_ids) == {str(d1.id), str(d2.id)}
        assert len(prop.supporting_decision_ids) == len(set(prop.supporting_decision_ids))  # no duplicates

    def test_time_context_derived_from_member_decided_at(self, repository: SqlAlchemyDecisionRepository) -> None:
        _register(repository, subject="AMD", decision_type="BUY", confidence=70, decided_at=_t(0))
        _register(repository, subject="AMD", decision_type="BUY", confidence=71, decided_at=_t(5))
        properties = build_observed_decision_properties(repository)
        (prop,) = [p for p in properties if p.property_type == "same_subject_and_type"]
        assert prop.first_observed_at == _t(0)
        assert prop.last_observed_at == _t(5)

    def test_outcome_aware_is_always_false(self, repository: SqlAlchemyDecisionRepository) -> None:
        _register(repository, subject="AMD", decision_type="BUY", confidence=70, decided_at=_t(0))
        _register(repository, subject="AMD", decision_type="BUY", confidence=71, decided_at=_t(1))
        properties = build_observed_decision_properties(repository)
        assert all(p.outcome_aware is False for p in properties)


class TestUnsafeVocabularyGuardrails:
    """Sprint 13 Phase 20: semantic-safety guardrails, not brittle
    string matching against every field -- these assert against the
    exact factual-description template this module generates."""

    _PROHIBITED_TERMS = (
        "strategy",
        "style",
        "habit",
        "discipline",
        "bias",
        "edge",
        "mistake",
        "better",
        "worse",
        "successful",
        "unsuccessful",
        "caused",
        "because",
    )

    def test_descriptions_never_contain_unsafe_vocabulary(self, repository: SqlAlchemyDecisionRepository) -> None:
        _register(repository, subject="AMD", decision_type="BUY", confidence=70, decided_at=_t(0))
        _register(repository, subject="AMD", decision_type="BUY", confidence=71, decided_at=_t(1))
        _register(repository, subject="AMD", decision_type="BUY", confidence=72, decided_at=_t(2))
        properties = build_observed_decision_properties(repository)
        assert properties  # sanity: this test only proves something if there is output to check
        for prop in properties:
            lowered = prop.factual_description.lower()
            for term in self._PROHIBITED_TERMS:
                assert term not in lowered, f"{term!r} found in {prop.factual_description!r}"

    def test_same_subject_and_type_description_is_exact_template(
        self, repository: SqlAlchemyDecisionRepository
    ) -> None:
        _register(repository, subject="AMD", decision_type="BUY", confidence=70, decided_at=_t(0))
        _register(repository, subject="AMD", decision_type="BUY", confidence=71, decided_at=_t(1))
        properties = build_observed_decision_properties(repository)
        (prop,) = [p for p in properties if p.property_type == "same_subject_and_type"]
        assert prop.factual_description == "You recorded 2 BUY Decisions for AMD."

    def test_same_confidence_description_is_exact_template(self, repository: SqlAlchemyDecisionRepository) -> None:
        _register(repository, subject="AMD", decision_type="BUY", confidence=70, decided_at=_t(0))
        _register(repository, subject="MSFT", decision_type="SELL", confidence=70, decided_at=_t(1))
        properties = build_observed_decision_properties(repository)
        (prop,) = [p for p in properties if p.property_type == "same_confidence"]
        assert prop.factual_description == "Confidence 70 appears in 2 recorded Decisions."


class TestSignatureExclusion:
    def test_no_signature_or_cross_property_object_is_ever_produced(
        self, repository: SqlAlchemyDecisionRepository
    ) -> None:
        # A history rich enough to form a real, giant connected component
        # under ConnectedPatternsStrategy (Sprint 11/12's own finding) --
        # verifying that even here, this module's output stays a flat
        # tuple of independent properties, never a merged object.
        for i in range(3):
            _register(repository, subject="AMD", decision_type="BUY", confidence=50, decided_at=_t(i))
        for i in range(2):
            _register(repository, subject="META", decision_type="BUY", confidence=50, decided_at=_t(10 + i))
        properties = build_observed_decision_properties(repository)
        property_types = {p.property_type for p in properties}
        assert property_types == {"same_subject_and_type", "same_confidence"}
        assert "connected_patterns" not in property_types
        assert not any(hasattr(p, "member_patterns") for p in properties)


class TestDeterminism:
    def test_repeated_calls_against_unchanged_history_are_identical(
        self, repository: SqlAlchemyDecisionRepository
    ) -> None:
        _register(repository, subject="AMD", decision_type="BUY", confidence=70, decided_at=_t(0))
        _register(repository, subject="AMD", decision_type="BUY", confidence=71, decided_at=_t(1))
        first = build_observed_decision_properties(repository)
        second = build_observed_decision_properties(repository)
        assert first == second


class TestHistoricalPrefixGrowth:
    def test_third_matching_decision_increments_observed_count(
        self, repository: SqlAlchemyDecisionRepository
    ) -> None:
        _register(repository, subject="AMD", decision_type="BUY", confidence=50, decided_at=_t(0))
        _register(repository, subject="AMD", decision_type="BUY", confidence=50, decided_at=_t(1))
        before = build_observed_decision_properties(repository)
        (before_prop,) = [p for p in before if p.property_type == "same_subject_and_type"]
        assert before_prop.observed_count == 2

        _register(repository, subject="AMD", decision_type="BUY", confidence=50, decided_at=_t(2))
        after = build_observed_decision_properties(repository)
        (after_prop,) = [p for p in after if p.property_type == "same_subject_and_type"]
        assert after_prop.observed_count == 3


def _t(offset_seconds: int) -> datetime:
    return datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=offset_seconds)
