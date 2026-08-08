"""Tests for `atlas.analysis_engine.valuation.cash_flow
.evaluate_fcf_yield_relative` (ATLAS-024 Phase 6/7) -- the documented
rule table, Scenarios A-D/F/G from Phase 19, and Phase 18's edge cases."""
from __future__ import annotations

from datetime import datetime

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.provenance import Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.valuation.cash_flow import evaluate_fcf_yield_relative
from atlas.analysis_engine.valuation.contracts import ValuationDataGapKind, ValuationMethodKind, ValuationStatus
from atlas.analysis_engine.valuation.facts import ValuationFact, ValuationFactKind
from atlas.decision_engine.contracts import EvidenceCoverageLevel
from tests.unit.analysis_engine.valuation._fixtures import EVALUATED_AT

_COUNTER = iter(range(1_000_000))


def _prov() -> Provenance:
    return Provenance(
        source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
        source_references=(),
        dependencies=(),
        update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
        consumers=(),
        computed_at=EVALUATED_AT,
    )


def fcf(value: float, period: str) -> BusinessFact:
    i = next(_COUNTER)
    return BusinessFact(
        id=f"fcf-{i}",
        company="ASML",
        kind=BusinessFactKind.FREE_CASH_FLOW,
        value=value,
        unit="usd",
        period=period,
        source_record_id=f"record-{i}",
        provenance=_prov(),
        extracted_at=EVALUATED_AT,
    )


def price(value: float, period: str) -> ValuationFact:
    i = next(_COUNTER)
    return ValuationFact(
        id=f"price-{i}",
        company="ASML",
        kind=ValuationFactKind.SHARE_PRICE,
        value=value,
        unit="usd",
        period=period,
        source_record_id=f"record-{i}",
        provenance=_prov(),
        extracted_at=EVALUATED_AT,
    )


def shares(value: float, period: str) -> ValuationFact:
    i = next(_COUNTER)
    return ValuationFact(
        id=f"shares-{i}",
        company="ASML",
        kind=ValuationFactKind.SHARES_OUTSTANDING,
        value=value,
        unit="count",
        period=period,
        source_record_id=f"record-{i}",
        provenance=_prov(),
        extracted_at=EVALUATED_AT,
    )


def _market(period: str, price_value: float, shares_value: float) -> tuple[ValuationFact, ValuationFact]:
    return (price(price_value, period), shares(shares_value, period))


class TestScenarioA_ClearlyUndervalued:
    def test_fcf_growing_price_flat_yields_undervalued(self):
        business_facts = (fcf(100.0, "2022"), fcf(110.0, "2023"), fcf(200.0, "2024"))
        valuation_facts = (*_market("2022", 50.0, 100.0), *_market("2023", 52.0, 100.0), *_market("2024", 53.0, 100.0))
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.UNDERVALUED
        assert result.kind is ValuationMethodKind.FCF_YIELD_RELATIVE
        assert result.confidence is EvidenceCoverageLevel.FULL
        assert result.missing_evidence == ()


class TestScenarioB_FairlyValued:
    def test_current_yield_within_historical_range_is_fairly_valued(self):
        business_facts = (fcf(100.0, "2022"), fcf(105.0, "2023"), fcf(102.0, "2024"))
        valuation_facts = (*_market("2022", 50.0, 100.0), *_market("2023", 50.0, 100.0), *_market("2024", 50.5, 100.0))
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.FAIRLY_VALUED


class TestScenarioC_ClearlyExpensive:
    def test_fcf_flat_price_rising_yields_expensive(self):
        business_facts = (fcf(100.0, "2022"), fcf(100.0, "2023"), fcf(100.0, "2024"))
        valuation_facts = (*_market("2022", 10.0, 100.0), *_market("2023", 10.0, 100.0), *_market("2024", 50.0, 100.0))
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.EXPENSIVE


class TestScenarioD_InsufficientHistory:
    def test_a_single_matched_period_is_insufficient(self):
        business_facts = (fcf(100.0, "2024"),)
        valuation_facts = _market("2024", 50.0, 100.0)
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT
        assert ValuationDataGapKind.INSUFFICIENT_HISTORICAL_VALUATION_PERIODS in result.missing_evidence

    def test_zero_facts_is_insufficient_with_all_three_missing_reasons(self):
        result = evaluate_fcf_yield_relative((), (), evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT
        assert result.confidence is EvidenceCoverageLevel.NOT_APPLICABLE
        assert set(result.missing_evidence) == {
            ValuationDataGapKind.MISSING_FREE_CASH_FLOW_HISTORY,
            ValuationDataGapKind.MISSING_MARKET_PRICE,
            ValuationDataGapKind.MISSING_SHARE_COUNT,
        }


class TestScenarioG_MissingData:
    def test_missing_share_count_only(self):
        business_facts = (fcf(100.0, "2023"), fcf(110.0, "2024"))
        valuation_facts = (price(50.0, "2023"), price(52.0, "2024"))  # no shares outstanding
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT
        assert ValuationDataGapKind.MISSING_SHARE_COUNT in result.missing_evidence
        assert result.confidence is EvidenceCoverageLevel.PARTIAL


class TestNegativeAndZeroCashFlow:
    def test_negative_current_fcf_is_insufficient_not_forced(self):
        business_facts = (fcf(-50.0, "2023"), fcf(-20.0, "2024"))
        valuation_facts = (*_market("2023", 10.0, 100.0), *_market("2024", 10.0, 100.0))
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT
        assert ValuationDataGapKind.CASH_FLOW_NOT_POSITIVE in result.missing_evidence

    def test_zero_fcf_is_also_excluded(self):
        business_facts = (fcf(0.0, "2023"), fcf(0.0, "2024"))
        valuation_facts = (*_market("2023", 10.0, 100.0), *_market("2024", 10.0, 100.0))
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT
        assert ValuationDataGapKind.CASH_FLOW_NOT_POSITIVE in result.missing_evidence

    def test_one_negative_historical_period_is_excluded_but_others_still_usable(self):
        """A single bad historical period does not poison the whole
        method -- it is simply excluded from the comparison, and the
        remaining valid periods still produce a real conclusion."""
        business_facts = (fcf(-10.0, "2022"), fcf(100.0, "2023"), fcf(100.0, "2024"))
        valuation_facts = (
            *_market("2022", 10.0, 100.0),
            *_market("2023", 50.0, 100.0),
            *_market("2024", 50.0, 100.0),
        )
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        # 2022 excluded (negative FCF); 2023 and 2024 both valid with
        # identical FCF and identical price -> yields match -> fairly valued.
        assert result.status is ValuationStatus.FAIRLY_VALUED
        assert ValuationDataGapKind.CASH_FLOW_NOT_POSITIVE not in result.missing_evidence


class TestStaleMarketData:
    def test_fcf_newer_than_market_snapshot_is_stale(self):
        business_facts = (fcf(100.0, "2023"), fcf(110.0, "2024"))
        valuation_facts = _market("2023", 50.0, 100.0)  # no 2024 market data at all
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT
        assert ValuationDataGapKind.STALE_MARKET_DATA in result.missing_evidence

    def test_matching_periods_are_never_stale(self):
        business_facts = (fcf(100.0, "2023"), fcf(110.0, "2024"))
        valuation_facts = (*_market("2023", 50.0, 100.0), *_market("2024", 52.0, 100.0))
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert ValuationDataGapKind.STALE_MARKET_DATA not in result.missing_evidence


class TestNoUniversalConstants:
    def test_no_hardcoded_yield_or_multiple_threshold_in_source(self):
        import inspect

        from atlas.analysis_engine.valuation import cash_flow

        source = inspect.getsource(cash_flow)
        for forbidden in ("0.05", "0.15", "price_to_earnings", "cheap_threshold", "expensive_threshold"):
            assert forbidden not in source, f"found forbidden constant/pattern: {forbidden!r}"

    def test_no_numeric_score_field_on_result(self):
        result = evaluate_fcf_yield_relative((), (), evaluated_at=EVALUATED_AT)
        assert not hasattr(result, "score")
        assert isinstance(result.status.value, str)


class TestTraceability:
    def test_current_period_facts_are_named_in_dependencies(self):
        p22, s22 = _market("2022", 50.0, 100.0)
        p23, s23 = _market("2023", 52.0, 100.0)
        f22 = fcf(100.0, "2022")
        f23 = fcf(110.0, "2023")
        result = evaluate_fcf_yield_relative((f22, f23), (p22, s22, p23, s23), evaluated_at=EVALUATED_AT)
        assert set(result.provenance.dependencies) == {f23.id, p23.id, s23.id}

    def test_all_valid_period_facts_are_supporting(self):
        p22, s22 = _market("2022", 50.0, 100.0)
        p23, s23 = _market("2023", 52.0, 100.0)
        f22 = fcf(100.0, "2022")
        f23 = fcf(110.0, "2023")
        result = evaluate_fcf_yield_relative((f22, f23), (p22, s22, p23, s23), evaluated_at=EVALUATED_AT)
        assert set(result.supporting_facts) == {f22.id, f23.id, p22.id, s22.id, p23.id, s23.id}


class TestDeterminism:
    def test_identical_facts_produce_a_deeply_equal_finding(self):
        business_facts = (fcf(100.0, "2023"), fcf(110.0, "2024"))
        valuation_facts = (*_market("2023", 50.0, 100.0), *_market("2024", 52.0, 100.0))
        first = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        second = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert first == second
