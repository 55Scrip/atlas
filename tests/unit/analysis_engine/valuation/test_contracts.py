"""Tests for `atlas.analysis_engine.valuation.contracts` (ATLAS-024
Phase 10/12) -- the closed taxonomies."""
from __future__ import annotations

from atlas.analysis_engine.findings import FindingSeverity
from atlas.analysis_engine.valuation.contracts import (
    ValuationAssumptionKind,
    ValuationDataGapKind,
    ValuationMethodKind,
    ValuationStatus,
    severity_for_valuation_status,
)


class TestValuationStatusIsClosed:
    def test_exactly_five_members(self):
        assert len(ValuationStatus) == 5

    def test_contains_the_three_real_outcomes(self):
        values = {member.value for member in ValuationStatus}
        assert {"undervalued", "fairly_valued", "expensive"}.issubset(values)

    def test_no_pseudo_precision_members(self):
        values = {member.value for member in ValuationStatus}
        forbidden = {"very_undervalued", "slightly_expensive"}
        assert forbidden.isdisjoint(values)


class TestValuationMethodKindIsClosed:
    def test_exactly_four_members(self):
        assert len(ValuationMethodKind) == 4

    def test_contains_fcf_yield_relative(self):
        assert ValuationMethodKind.FCF_YIELD_RELATIVE.value == "fcf_yield_relative"

    def test_contains_all_three_scenarios(self):
        values = {member.value for member in ValuationMethodKind}
        assert {"scenario_bear", "scenario_base", "scenario_bull"}.issubset(values)


class TestValuationDataGapKindNamesRealReasons:
    def test_stale_market_data_is_named(self):
        assert ValuationDataGapKind.STALE_MARKET_DATA.value == "stale_market_data"

    def test_cash_flow_not_positive_is_distinct_from_missing(self):
        """Not the same concept as 'missing' -- the data is present, just
        not usable for this method."""
        assert ValuationDataGapKind.CASH_FLOW_NOT_POSITIVE.value == "cash_flow_not_positive"


class TestValuationAssumptionKindIsReservedNotConstructed:
    def test_three_members_named(self):
        assert len(ValuationAssumptionKind) == 3


class TestSeverityMapping:
    def test_insufficient_input_is_attention(self):
        assert severity_for_valuation_status(ValuationStatus.INSUFFICIENT_INPUT) is FindingSeverity.ATTENTION

    def test_expensive_is_attention_not_material(self):
        """Expensive stays ATTENTION, never escalated above a WEAK
        Growth finding's own severity -- valuation and business quality
        are independent, never ranked against each other."""
        assert severity_for_valuation_status(ValuationStatus.EXPENSIVE) is FindingSeverity.ATTENTION

    def test_undervalued_and_fairly_valued_are_info(self):
        assert severity_for_valuation_status(ValuationStatus.UNDERVALUED) is FindingSeverity.INFO
        assert severity_for_valuation_status(ValuationStatus.FAIRLY_VALUED) is FindingSeverity.INFO
