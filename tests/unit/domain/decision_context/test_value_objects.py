"""Tests for DecisionContext value objects (API-002 Decision Context)."""
from __future__ import annotations

import uuid

import pytest

from atlas.core.domain.decision_context.exceptions import (
    InvalidAlternativeError,
    InvalidUncertaintyError,
    MissingSituationError,
)
from atlas.core.domain.decision_context.value_objects import (
    AlternativesConsidered,
    ContextId,
    Situation,
    Uncertainties,
)


class TestContextId:
    def test_generates_a_uuid_by_default(self):
        assert isinstance(ContextId().value, uuid.UUID)

    def test_two_default_ids_are_different(self):
        assert ContextId() != ContextId()

    def test_equal_by_value(self):
        value = uuid.uuid4()
        assert ContextId(value) == ContextId(value)


class TestSituation:
    def test_holds_the_value(self):
        assert Situation("Portfolio already had large semiconductor exposure").value == (
            "Portfolio already had large semiconductor exposure"
        )

    def test_strips_surrounding_whitespace(self):
        assert Situation("  reasoning  ").value == "reasoning"

    def test_rejects_empty_situation(self):
        with pytest.raises(MissingSituationError):
            Situation("")

    def test_rejects_whitespace_only_situation(self):
        with pytest.raises(MissingSituationError):
            Situation("   ")

    def test_rejects_missing_situation(self):
        with pytest.raises(MissingSituationError):
            Situation(None)

    def test_is_frozen(self):
        situation = Situation("reasoning")
        with pytest.raises(AttributeError):
            situation.value = "changed"


class TestAlternativesConsidered:
    def test_may_be_empty(self):
        assert len(AlternativesConsidered()) == 0
        assert list(AlternativesConsidered()) == []

    def test_holds_items_in_order(self):
        alternatives = AlternativesConsidered(("Buy Applied Materials", "Buy Arm"))
        assert list(alternatives) == ["Buy Applied Materials", "Buy Arm"]

    def test_strips_each_item(self):
        alternatives = AlternativesConsidered(("  Buy Arm  ",))
        assert list(alternatives) == ["Buy Arm"]

    def test_rejects_an_empty_item(self):
        with pytest.raises(InvalidAlternativeError):
            AlternativesConsidered(("Buy Applied Materials", ""))

    def test_rejects_a_whitespace_only_item(self):
        with pytest.raises(InvalidAlternativeError):
            AlternativesConsidered(("   ",))

    def test_is_frozen(self):
        alternatives = AlternativesConsidered(("Buy Arm",))
        with pytest.raises(AttributeError):
            alternatives.items = ("Buy Applied Materials",)

    def test_underlying_collection_is_a_tuple(self):
        assert isinstance(AlternativesConsidered(("Buy Arm",)).items, tuple)


class TestUncertainties:
    def test_may_be_empty(self):
        assert len(Uncertainties()) == 0
        assert list(Uncertainties()) == []

    def test_holds_items_in_order(self):
        uncertainties = Uncertainties(("Market reaction", "Valuation already priced in growth"))
        assert list(uncertainties) == ["Market reaction", "Valuation already priced in growth"]

    def test_rejects_an_empty_item(self):
        with pytest.raises(InvalidUncertaintyError):
            Uncertainties(("Market reaction", ""))

    def test_is_frozen(self):
        uncertainties = Uncertainties(("Market reaction",))
        with pytest.raises(AttributeError):
            uncertainties.items = ("Something else",)
