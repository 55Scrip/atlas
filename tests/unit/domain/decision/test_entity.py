"""Tests for the Decision aggregate root (API-001 Decision Capture)."""
from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.exceptions import InvalidDecidedAtError
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionSource,
    DecisionType,
    InvestmentCase,
    Subject,
    UserId,
)

_USER = UserId(uuid.uuid4())
_SUBJECT = Subject("ASML")
_CASE = InvestmentCase("Durable moat, undervalued relative to peers")
_CONFIDENCE = Confidence(75)
_PAST = datetime(2026, 1, 1, tzinfo=timezone.utc)
# The Case that owns this file's Decision fixtures — one fixed, named
# identity, mirroring the established pattern in
# tests/unit/domain/observation/test_entity.py.
_CASE_ID = CaseId()


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestDecisionRegistration:
    def test_captures_the_given_fields(self):
        decision = Decision.register(
            case_id=_CASE_ID,
            user_id=_USER,
            decision_type=DecisionType.BUY,
            subject=_SUBJECT,
            investment_case=_CASE,
            confidence=_CONFIDENCE,
            decided_at=_PAST,
        )
        assert decision.user_id == _USER
        assert decision.decision_type is DecisionType.BUY
        assert decision.subject == _SUBJECT
        assert decision.investment_case == _CASE
        assert decision.confidence == _CONFIDENCE
        assert decision.decided_at == _PAST

    def test_assigns_a_fresh_id(self):
        first = Decision.register(
            case_id=_CASE_ID,
            user_id=_USER,
            decision_type=DecisionType.BUY,
            subject=_SUBJECT,
            investment_case=_CASE,
            confidence=_CONFIDENCE,
        )
        second = Decision.register(
            case_id=_CASE_ID,
            user_id=_USER,
            decision_type=DecisionType.BUY,
            subject=_SUBJECT,
            investment_case=_CASE,
            confidence=_CONFIDENCE,
        )
        assert first.id != second.id

    def test_accepts_a_decision_type_string(self):
        decision = Decision.register(
            case_id=_CASE_ID,
            user_id=_USER,
            decision_type="BUY",
            subject=_SUBJECT,
            investment_case=_CASE,
            confidence=_CONFIDENCE,
        )
        assert decision.decision_type is DecisionType.BUY

    def test_requires_a_subject(self):
        with pytest.raises(TypeError):
            Decision.register(
                case_id=_CASE_ID,
                user_id=_USER,
                decision_type=DecisionType.BUY,
                investment_case=_CASE,
                confidence=_CONFIDENCE,
            )

    def test_requires_a_case_id(self):
        with pytest.raises(TypeError):
            Decision.register(
                user_id=_USER,
                decision_type=DecisionType.BUY,
                subject=_SUBJECT,
                investment_case=_CASE,
                confidence=_CONFIDENCE,
            )

    def test_recorded_at_is_always_now_regardless_of_decided_at(self):
        now = datetime(2026, 7, 13, tzinfo=timezone.utc)
        decision = Decision.register(
            case_id=_CASE_ID,
            user_id=_USER,
            decision_type=DecisionType.BUY,
            subject=_SUBJECT,
            investment_case=_CASE,
            confidence=_CONFIDENCE,
            decided_at=_PAST,
            clock=_fixed_clock(now),
        )
        assert decision.recorded_at == now
        assert decision.decided_at == _PAST

    def test_decided_at_defaults_to_now_when_omitted(self):
        now = datetime(2026, 7, 13, tzinfo=timezone.utc)
        decision = Decision.register(
            case_id=_CASE_ID,
            user_id=_USER,
            decision_type=DecisionType.BUY,
            subject=_SUBJECT,
            investment_case=_CASE,
            confidence=_CONFIDENCE,
            clock=_fixed_clock(now),
        )
        assert decision.decided_at == now

    def test_source_defaults_to_manual(self):
        decision = Decision.register(
            case_id=_CASE_ID,
            user_id=_USER,
            decision_type=DecisionType.BUY,
            subject=_SUBJECT,
            investment_case=_CASE,
            confidence=_CONFIDENCE,
        )
        assert decision.source is DecisionSource.MANUAL

    def test_accepts_an_explicit_source(self):
        decision = Decision.register(
            case_id=_CASE_ID,
            user_id=_USER,
            decision_type=DecisionType.WATCH,
            subject=_SUBJECT,
            investment_case=_CASE,
            confidence=_CONFIDENCE,
            source=DecisionSource.BROKER_SYNC,
        )
        assert decision.source is DecisionSource.BROKER_SYNC

    def test_rejects_naive_decided_at(self):
        with pytest.raises(InvalidDecidedAtError):
            Decision.register(
                case_id=_CASE_ID,
                user_id=_USER,
                decision_type=DecisionType.BUY,
                subject=_SUBJECT,
                investment_case=_CASE,
                confidence=_CONFIDENCE,
                decided_at=datetime(2026, 1, 1),
            )

    def test_normalises_decided_at_to_utc(self):
        tokyo = timezone(timedelta(hours=9))
        decided_at = datetime(2026, 1, 1, 9, 0, tzinfo=tokyo)
        decision = Decision.register(
            case_id=_CASE_ID,
            user_id=_USER,
            decision_type=DecisionType.BUY,
            subject=_SUBJECT,
            investment_case=_CASE,
            confidence=_CONFIDENCE,
            decided_at=decided_at,
        )
        assert decision.decided_at == datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)


class TestDecisionImmutability:
    def test_is_frozen(self):
        decision = Decision.register(
            case_id=_CASE_ID,
            user_id=_USER,
            decision_type=DecisionType.BUY,
            subject=_SUBJECT,
            investment_case=_CASE,
            confidence=_CONFIDENCE,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            decision.confidence = Confidence(10)

    def test_a_changed_opinion_is_a_new_decision_not_a_mutation(self):
        original = Decision.register(
            case_id=_CASE_ID,
            user_id=_USER,
            decision_type=DecisionType.BUY,
            subject=_SUBJECT,
            investment_case=_CASE,
            confidence=_CONFIDENCE,
        )
        revised = Decision.register(
            case_id=_CASE_ID,
            user_id=_USER,
            decision_type=DecisionType.SELL,
            subject=_SUBJECT,
            investment_case=InvestmentCase("Thesis broke: moat eroded"),
            confidence=Confidence(80),
        )
        assert original.id != revised.id
        assert original.decision_type is DecisionType.BUY


class TestCaseOwnership:
    def test_two_decisions_in_the_same_case_remain_distinct(self):
        first = Decision.register(
            case_id=_CASE_ID,
            user_id=_USER,
            decision_type=DecisionType.BUY,
            subject=_SUBJECT,
            investment_case=_CASE,
            confidence=_CONFIDENCE,
        )
        second = Decision.register(
            case_id=_CASE_ID,
            user_id=_USER,
            decision_type=DecisionType.BUY,
            subject=_SUBJECT,
            investment_case=_CASE,
            confidence=_CONFIDENCE,
        )
        assert first.id != second.id
        assert first.case_id == second.case_id == _CASE_ID

    def test_decisions_in_different_cases_are_independent(self):
        other_case_id = CaseId()
        first = Decision.register(
            case_id=_CASE_ID,
            user_id=_USER,
            decision_type=DecisionType.BUY,
            subject=_SUBJECT,
            investment_case=_CASE,
            confidence=_CONFIDENCE,
        )
        second = Decision.register(
            case_id=other_case_id,
            user_id=_USER,
            decision_type=DecisionType.BUY,
            subject=_SUBJECT,
            investment_case=_CASE,
            confidence=_CONFIDENCE,
        )
        assert first.case_id != second.case_id
