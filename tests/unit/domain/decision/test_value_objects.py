"""Tests for Decision value objects (API-001 Decision Capture)."""
from __future__ import annotations

import uuid

import pytest

from atlas.core.domain.decision.exceptions import (
    InvalidConfidenceError,
    InvalidDecisionTypeError,
    MissingDecisionTypeError,
    MissingReasonError,
    MissingSubjectError,
)
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionId,
    DecisionSource,
    DecisionType,
    InvestmentCase,
    Subject,
    UserId,
)


class TestDecisionId:
    def test_generates_a_uuid_by_default(self):
        assert isinstance(DecisionId().value, uuid.UUID)

    def test_two_default_ids_are_different(self):
        assert DecisionId() != DecisionId()

    def test_equal_by_value(self):
        value = uuid.uuid4()
        assert DecisionId(value) == DecisionId(value)


class TestUserId:
    def test_holds_the_given_uuid(self):
        value = uuid.uuid4()
        assert UserId(value).value == value

    def test_equal_by_value(self):
        value = uuid.uuid4()
        assert UserId(value) == UserId(value)


class TestDecisionType:
    @pytest.mark.parametrize("value", ["BUY", "SELL", "HOLD", "WATCH", "PASS"])
    def test_allowed_values_coerce(self, value):
        assert DecisionType.coerce(value) is DecisionType(value)

    def test_passthrough_of_existing_enum_member(self):
        assert DecisionType.coerce(DecisionType.BUY) is DecisionType.BUY

    def test_rejects_unknown_value(self):
        with pytest.raises(InvalidDecisionTypeError):
            DecisionType.coerce("STRONG_BUY")

    def test_rejects_missing_value(self):
        with pytest.raises(MissingDecisionTypeError):
            DecisionType.coerce(None)

    def test_missing_is_a_kind_of_invalid(self):
        with pytest.raises(InvalidDecisionTypeError):
            DecisionType.coerce(None)


class TestDecisionSource:
    def test_known_examples(self):
        assert DecisionSource.MANUAL == "Manual"
        assert DecisionSource.IMPORT == "Import"
        assert DecisionSource.BROKER_SYNC == "BrokerSync"
        assert DecisionSource.API == "API"


class TestSubject:
    def test_holds_the_value(self):
        assert Subject("ASML").value == "ASML"

    def test_strips_surrounding_whitespace(self):
        assert Subject("  ASML  ").value == "ASML"

    def test_rejects_empty_subject(self):
        with pytest.raises(MissingSubjectError):
            Subject("")

    def test_rejects_whitespace_only_subject(self):
        with pytest.raises(MissingSubjectError):
            Subject("   ")

    def test_rejects_missing_subject(self):
        with pytest.raises(MissingSubjectError):
            Subject(None)

    def test_is_frozen(self):
        subject = Subject("ASML")
        with pytest.raises(AttributeError):
            subject.value = "MSFT"


class TestInvestmentCase:
    def test_holds_the_reason(self):
        assert InvestmentCase("Strong moat, reasonable valuation").reason == (
            "Strong moat, reasonable valuation"
        )

    def test_strips_surrounding_whitespace(self):
        assert InvestmentCase("  reasoning  ").reason == "reasoning"

    def test_rejects_empty_reason(self):
        with pytest.raises(MissingReasonError):
            InvestmentCase("")

    def test_rejects_whitespace_only_reason(self):
        with pytest.raises(MissingReasonError):
            InvestmentCase("   ")

    def test_rejects_missing_reason(self):
        with pytest.raises(MissingReasonError):
            InvestmentCase(None)

    def test_is_frozen(self):
        case = InvestmentCase("reasoning")
        with pytest.raises(AttributeError):
            case.reason = "changed"


class TestConfidence:
    @pytest.mark.parametrize("value", [0, 1, 50, 99, 100])
    def test_accepts_values_within_range(self, value):
        assert Confidence(value).value == value

    @pytest.mark.parametrize("value", [-1, 101, 1000])
    def test_rejects_values_outside_range(self, value):
        with pytest.raises(InvalidConfidenceError):
            Confidence(value)

    def test_rejects_missing_confidence(self):
        with pytest.raises(InvalidConfidenceError):
            Confidence(None)

    def test_rejects_non_integer_confidence(self):
        with pytest.raises(InvalidConfidenceError):
            Confidence(50.5)

    def test_is_frozen(self):
        confidence = Confidence(50)
        with pytest.raises(AttributeError):
            confidence.value = 60
