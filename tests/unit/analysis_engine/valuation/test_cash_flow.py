"""Tests for `atlas.analysis_engine.valuation.cash_flow
.evaluate_fcf_yield_relative` (ATLAS-024 Phase 6/7; temporal alignment
rewritten ATLAS-032) -- the documented rule table, no-look-ahead
eligibility, and Phase 18/19's edge cases.

**Periods are real ISO dates throughout, not bare years.** The
evaluator parses a market observation's `period` as a date to compare
against a Free Cash Flow fact's `published_at` -- exercising that with
realistic values (a fiscal year end, a filing date weeks/months later,
a market snapshot date later still) is the whole point of this
rewrite; bare-year periods (the ATLAS-024 convention) would silently
never exercise the real eligibility path.
"""
from __future__ import annotations

from datetime import datetime, timezone

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


def fcf(value: float, period: str, published_at: datetime) -> BusinessFact:
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
        published_at=published_at,
    )


def price(value: float, period: str, published_at: datetime = EVALUATED_AT) -> ValuationFact:
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
        published_at=published_at,
    )


def shares(value: float, period: str, published_at: datetime = EVALUATED_AT) -> ValuationFact:
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
        published_at=published_at,
    )


def _market(period: str, price_value: float, shares_value: float) -> tuple[ValuationFact, ValuationFact]:
    return (price(price_value, period), shares(shares_value, period))


def _dt(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


# A realistic three-year timeline: each fiscal year ends 12-31, is
# actually filed ~45 days later, and the market observation used to
# pair against it sits after that filing date (so the filing was
# genuinely public/eligible by the time of the observation) but before
# the *next* year's filing.
FY2022_PERIOD, FY2022_FILED = "2022-12-31", _dt(2023, 2, 15)
FY2023_PERIOD, FY2023_FILED = "2023-12-31", _dt(2024, 2, 15)
FY2024_PERIOD, FY2024_FILED = "2024-12-31", _dt(2025, 2, 15)
OBS_2023, OBS_2024, OBS_2025 = "2023-03-01", "2024-03-01", "2025-03-01"


class TestScenarioA_ClearlyUndervalued:
    def test_fcf_growing_price_flat_yields_undervalued(self):
        business_facts = (
            fcf(100.0, FY2022_PERIOD, FY2022_FILED),
            fcf(110.0, FY2023_PERIOD, FY2023_FILED),
            fcf(200.0, FY2024_PERIOD, FY2024_FILED),
        )
        valuation_facts = (*_market(OBS_2023, 50.0, 100.0), *_market(OBS_2024, 52.0, 100.0), *_market(OBS_2025, 53.0, 100.0))
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.UNDERVALUED
        assert result.kind is ValuationMethodKind.FCF_YIELD_RELATIVE
        assert result.confidence is EvidenceCoverageLevel.FULL
        assert result.missing_evidence == ()
        assert result.current_yield == 200.0 / (53.0 * 100.0)


class TestScenarioB_FairlyValued:
    def test_current_yield_within_historical_range_is_fairly_valued(self):
        business_facts = (
            fcf(100.0, FY2022_PERIOD, FY2022_FILED),
            fcf(105.0, FY2023_PERIOD, FY2023_FILED),
            fcf(102.0, FY2024_PERIOD, FY2024_FILED),
        )
        valuation_facts = (
            *_market(OBS_2023, 50.0, 100.0),
            *_market(OBS_2024, 50.0, 100.0),
            *_market(OBS_2025, 50.5, 100.0),
        )
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.FAIRLY_VALUED


class TestScenarioC_ClearlyExpensive:
    def test_fcf_flat_price_rising_yields_expensive(self):
        business_facts = (
            fcf(100.0, FY2022_PERIOD, FY2022_FILED),
            fcf(100.0, FY2023_PERIOD, FY2023_FILED),
            fcf(100.0, FY2024_PERIOD, FY2024_FILED),
        )
        valuation_facts = (*_market(OBS_2023, 10.0, 100.0), *_market(OBS_2024, 10.0, 100.0), *_market(OBS_2025, 50.0, 100.0))
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.EXPENSIVE


class TestScenarioD_InsufficientHistory:
    def test_a_single_observation_is_insufficient_but_current_yield_is_still_real(self):
        business_facts = (fcf(100.0, FY2024_PERIOD, FY2024_FILED),)
        valuation_facts = _market(OBS_2025, 50.0, 100.0)
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT
        assert ValuationDataGapKind.INSUFFICIENT_HISTORICAL_VALUATION_PERIODS in result.missing_evidence
        # ATLAS-032, Phase 5: Current FCF Yield does not require history.
        assert result.current_yield == 100.0 / (50.0 * 100.0)
        assert len(result.supporting_facts) == 3

    def test_zero_facts_is_insufficient_with_all_three_missing_reasons(self):
        result = evaluate_fcf_yield_relative((), (), evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT
        assert result.confidence is EvidenceCoverageLevel.NOT_APPLICABLE
        assert result.current_yield is None
        assert set(result.missing_evidence) == {
            ValuationDataGapKind.MISSING_FREE_CASH_FLOW_HISTORY,
            ValuationDataGapKind.MISSING_MARKET_PRICE,
            ValuationDataGapKind.MISSING_SHARE_COUNT,
        }


class TestScenarioG_MissingData:
    def test_missing_share_count_only(self):
        business_facts = (fcf(100.0, FY2023_PERIOD, FY2023_FILED), fcf(110.0, FY2024_PERIOD, FY2024_FILED))
        valuation_facts = (price(50.0, OBS_2024), price(52.0, OBS_2025))  # no shares outstanding
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT
        assert ValuationDataGapKind.MISSING_SHARE_COUNT in result.missing_evidence
        assert result.confidence is EvidenceCoverageLevel.PARTIAL
        assert result.current_yield is None

    def test_missing_market_price_only(self):
        business_facts = (fcf(100.0, FY2023_PERIOD, FY2023_FILED), fcf(110.0, FY2024_PERIOD, FY2024_FILED))
        valuation_facts = (shares(100.0, OBS_2024), shares(100.0, OBS_2025))  # no share price
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT
        assert ValuationDataGapKind.MISSING_MARKET_PRICE in result.missing_evidence
        assert result.current_yield is None

    def test_missing_free_cash_flow_entirely(self):
        valuation_facts = (*_market(OBS_2024, 50.0, 100.0), *_market(OBS_2025, 52.0, 100.0))
        result = evaluate_fcf_yield_relative((), valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT
        assert ValuationDataGapKind.MISSING_FREE_CASH_FLOW_HISTORY in result.missing_evidence
        assert result.current_yield is None

    def test_zero_share_price_excludes_that_observation(self):
        business_facts = (fcf(100.0, FY2023_PERIOD, FY2023_FILED),)
        valuation_facts = _market(OBS_2024, 0.0, 100.0)
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT
        assert result.current_yield is None

    def test_zero_shares_outstanding_excludes_that_observation(self):
        business_facts = (fcf(100.0, FY2023_PERIOD, FY2023_FILED),)
        valuation_facts = _market(OBS_2024, 50.0, 0.0)
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT
        assert result.current_yield is None

    def test_more_fcf_periods_than_market_observations_still_uses_the_eligible_one(self):
        """Three real FCF periods but only one market observation --
        the single observation still produces a real current yield,
        never crashing or being confused by the mismatched lengths."""
        business_facts = (
            fcf(100.0, FY2022_PERIOD, FY2022_FILED),
            fcf(110.0, FY2023_PERIOD, FY2023_FILED),
            fcf(200.0, FY2024_PERIOD, FY2024_FILED),
        )
        valuation_facts = _market(OBS_2025, 53.0, 100.0)
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT  # one observation -> no history
        assert result.current_yield == 200.0 / (53.0 * 100.0)  # paired with the latest eligible FCF (FY2024)

    def test_more_market_observations_than_fcf_periods_reuses_the_one_eligible_fcf(self):
        """One real FCF period but three market observations after its
        filing -- every observation pairs with that same FCF fact
        (never fabricating additional history)."""
        business_facts = (fcf(100.0, FY2022_PERIOD, FY2022_FILED),)
        valuation_facts = (*_market(OBS_2023, 50.0, 100.0), *_market(OBS_2024, 52.0, 100.0), *_market(OBS_2025, 53.0, 100.0))
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        # All three observations are valid (same eligible FCF, different
        # prices) -- current is OBS_2025 vs. historical OBS_2023/OBS_2024.
        assert result.status in (ValuationStatus.UNDERVALUED, ValuationStatus.FAIRLY_VALUED, ValuationStatus.EXPENSIVE)
        assert result.current_yield == 100.0 / (53.0 * 100.0)


class TestNegativeAndZeroCashFlow:
    def test_negative_current_fcf_is_insufficient_not_forced(self):
        business_facts = (fcf(-50.0, FY2023_PERIOD, FY2023_FILED), fcf(-20.0, FY2024_PERIOD, FY2024_FILED))
        valuation_facts = (*_market(OBS_2024, 10.0, 100.0), *_market(OBS_2025, 10.0, 100.0))
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT
        assert ValuationDataGapKind.CASH_FLOW_NOT_POSITIVE in result.missing_evidence

    def test_zero_fcf_is_also_excluded(self):
        business_facts = (fcf(0.0, FY2023_PERIOD, FY2023_FILED), fcf(0.0, FY2024_PERIOD, FY2024_FILED))
        valuation_facts = (*_market(OBS_2024, 10.0, 100.0), *_market(OBS_2025, 10.0, 100.0))
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT
        assert ValuationDataGapKind.CASH_FLOW_NOT_POSITIVE in result.missing_evidence

    def test_one_negative_historical_period_is_excluded_but_others_still_usable(self):
        """A single bad historical period does not poison the whole
        method -- it is simply excluded from the comparison, and the
        remaining valid periods still produce a real conclusion."""
        business_facts = (
            fcf(-10.0, FY2022_PERIOD, FY2022_FILED),
            fcf(100.0, FY2023_PERIOD, FY2023_FILED),
            fcf(100.0, FY2024_PERIOD, FY2024_FILED),
        )
        valuation_facts = (
            *_market(OBS_2023, 10.0, 100.0),
            *_market(OBS_2024, 50.0, 100.0),
            *_market(OBS_2025, 50.0, 100.0),
        )
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        # OBS_2023 excluded (negative FCF); OBS_2024 and OBS_2025 both
        # valid with identical FCF and identical price -> yields match
        # -> fairly valued.
        assert result.status is ValuationStatus.FAIRLY_VALUED
        assert ValuationDataGapKind.CASH_FLOW_NOT_POSITIVE not in result.missing_evidence


class TestNoLookAheadBias:
    """ATLAS-032's central guarantee: a market observation may only be
    paired with a Free Cash Flow fact that was genuinely public
    (`published_at <=` the observation's own date) by that point."""

    def test_market_observation_before_any_filing_has_no_eligible_fcf(self):
        # The only FCF fact is filed *after* the only market observation
        # -- Atlas could not have known this fundamental at that point.
        business_facts = (fcf(100.0, FY2024_PERIOD, FY2024_FILED),)
        valuation_facts = _market("2024-06-01", 50.0, 100.0)  # before FY2024_FILED (2025-02-15)
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT
        assert result.current_yield is None
        assert result.supporting_facts == ()
        assert ValuationDataGapKind.NO_ELIGIBLE_FUNDAMENTALS_AS_OF_OBSERVATION in result.missing_evidence

    def test_earlier_observation_never_paired_with_a_later_filed_fact(self):
        # Two FCF facts, two observations: an early observation must
        # pair with the earlier (already-filed) fact, never the later
        # one, even though the later one has a "more recent" period.
        early_fcf = fcf(100.0, FY2022_PERIOD, FY2022_FILED)
        late_fcf = fcf(999.0, FY2024_PERIOD, FY2024_FILED)  # published far later
        # Observation sits after FY2022's filing but well before FY2024's.
        p, s = _market(OBS_2023, 50.0, 100.0)
        result = evaluate_fcf_yield_relative((early_fcf, late_fcf), (p, s), evaluated_at=EVALUATED_AT)
        assert result.status is ValuationStatus.INSUFFICIENT_INPUT  # only one valid observation -> no history
        assert result.current_yield == 100.0 / (50.0 * 100.0)  # paired with the early (eligible) fact
        assert early_fcf.id in result.supporting_facts
        assert late_fcf.id not in result.supporting_facts

    def test_two_observations_each_pair_with_the_fact_eligible_at_that_time(self):
        f2022 = fcf(100.0, FY2022_PERIOD, FY2022_FILED)
        f2023 = fcf(110.0, FY2023_PERIOD, FY2023_FILED)
        p23, s23 = _market(OBS_2023, 50.0, 100.0)  # after FY2022 filed, before FY2023 filed
        p24, s24 = _market(OBS_2024, 52.0, 100.0)  # after FY2023 filed
        result = evaluate_fcf_yield_relative((f2022, f2023), (p23, s23, p24, s24), evaluated_at=EVALUATED_AT)
        assert result.status in (ValuationStatus.UNDERVALUED, ValuationStatus.FAIRLY_VALUED, ValuationStatus.EXPENSIVE)
        assert f2023.id in result.supporting_facts  # current observation paired with FY2023
        assert f2022.id in result.supporting_facts  # historical observation paired with FY2022


class TestStaleMarketDataRetired:
    """ATLAS-032 retired the old period-vs-period STALE_MARKET_DATA
    check (see cash_flow.py's module docstring for why); it is never
    constructed by this evaluator any more."""

    def test_fcf_filed_after_the_only_market_observation_is_not_labeled_stale(self):
        business_facts = (fcf(100.0, FY2023_PERIOD, FY2023_FILED), fcf(110.0, FY2024_PERIOD, FY2024_FILED))
        valuation_facts = _market(OBS_2024, 50.0, 100.0)  # before FY2024 was filed
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert ValuationDataGapKind.STALE_MARKET_DATA not in result.missing_evidence

    def test_matching_periods_are_never_stale(self):
        business_facts = (fcf(100.0, FY2023_PERIOD, FY2023_FILED), fcf(110.0, FY2024_PERIOD, FY2024_FILED))
        valuation_facts = (*_market(OBS_2024, 50.0, 100.0), *_market(OBS_2025, 52.0, 100.0))
        result = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert ValuationDataGapKind.STALE_MARKET_DATA not in result.missing_evidence


class TestNoUniversalConstants:
    def test_no_hardcoded_yield_or_multiple_threshold_in_source(self):
        import inspect

        from atlas.analysis_engine.valuation import cash_flow

        source = inspect.getsource(cash_flow)
        for forbidden in ("0.05", "0.15", "price_to_earnings", "cheap_threshold", "expensive_threshold"):
            assert forbidden not in source, f"found forbidden constant/pattern: {forbidden!r}"

    def test_no_generic_score_field_on_result(self):
        result = evaluate_fcf_yield_relative((), (), evaluated_at=EVALUATED_AT)
        assert not hasattr(result, "score")
        assert isinstance(result.status.value, str)


class TestTraceability:
    def test_current_period_facts_are_named_in_dependencies(self):
        p22, s22 = _market(OBS_2023, 50.0, 100.0)
        p23, s23 = _market(OBS_2024, 52.0, 100.0)
        f22 = fcf(100.0, FY2022_PERIOD, FY2022_FILED)
        f23 = fcf(110.0, FY2023_PERIOD, FY2023_FILED)
        result = evaluate_fcf_yield_relative((f22, f23), (p22, s22, p23, s23), evaluated_at=EVALUATED_AT)
        assert set(result.provenance.dependencies) == {f23.id, p23.id, s23.id}

    def test_all_valid_period_facts_are_supporting(self):
        p22, s22 = _market(OBS_2023, 50.0, 100.0)
        p23, s23 = _market(OBS_2024, 52.0, 100.0)
        f22 = fcf(100.0, FY2022_PERIOD, FY2022_FILED)
        f23 = fcf(110.0, FY2023_PERIOD, FY2023_FILED)
        result = evaluate_fcf_yield_relative((f22, f23), (p22, s22, p23, s23), evaluated_at=EVALUATED_AT)
        assert set(result.supporting_facts) == {f22.id, f23.id, p22.id, s22.id, p23.id, s23.id}


class TestDeterminism:
    def test_identical_facts_produce_a_deeply_equal_finding(self):
        business_facts = (fcf(100.0, FY2023_PERIOD, FY2023_FILED), fcf(110.0, FY2024_PERIOD, FY2024_FILED))
        valuation_facts = (*_market(OBS_2024, 50.0, 100.0), *_market(OBS_2025, 52.0, 100.0))
        first = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        second = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert first == second
