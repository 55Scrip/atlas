"""Tests for `atlas.analysis_engine.business_facts.contracts`
(ATLAS-023 Phase 3) -- the eight-member fact taxonomy."""
from __future__ import annotations

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind


class TestBusinessFactKindIsClosed:
    def test_exactly_eight_members(self):
        assert len(BusinessFactKind) == 8

    def test_is_a_closed_string_enum(self):
        assert issubclass(BusinessFactKind, str)
        for member in BusinessFactKind:
            assert isinstance(member.value, str)

    def test_contains_growth_kinds(self):
        assert BusinessFactKind.REVENUE.value == "revenue"
        assert BusinessFactKind.FREE_CASH_FLOW.value == "free_cash_flow"

    def test_contains_capital_allocation_kinds(self):
        expected = {
            "capital_expenditure",
            "share_buybacks",
            "share_issuance",
            "dividends",
            "debt_issuance",
            "debt_repayment",
        }
        assert expected.issubset({member.value for member in BusinessFactKind})

    def test_no_growth_rate_kinds_exist(self):
        """Growth rates are computed by the evaluator, never persisted
        as a second fact kind -- see contracts.py's own docstring."""
        values = {member.value for member in BusinessFactKind}
        assert "revenue_growth" not in values
        assert "free_cash_flow_growth" not in values

    def test_unrecognized_kind_is_not_constructible(self):
        try:
            BusinessFactKind("operating_income")
            assert False, "expected ValueError"
        except ValueError:
            pass
