"""FCF-yield evaluator -- fiscal-epoch construction (Valuation Observation
Integrity).

What each class pins:

- **Fiscal pairing**: a price meets the free cash flow of the fiscal year that
  was the latest one public on its date -- never an older year republished as
  a comparative, never a year not yet filed.
- **Epochs**: one observation per fiscal year; repeated refreshes of one year
  never add history; the current year is never its own history.
- **Eligibility**: three prior fiscal epochs before the comparison may
  classify; thinner history is described, never classified.
- **Sources**: annual statements only, no future fiscal years, one fact per
  period, one currency.
- **Applicability**: banks, dealers and insurers are not valued by FCF yield.
- **Real companies**: the test matrix, on inputs exactly as Atlas holds them.
"""
from __future__ import annotations

import dataclasses
import inspect
import random
import re

import pytest

from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.valuation import cash_flow
from atlas.analysis_engine.valuation.cash_flow import MINIMUM_PRIOR_EPOCHS, SHARE_COUNT_METHOD
from atlas.analysis_engine.valuation.contracts import (
    HistoricalYieldPosition as Position,
    ShareCountMethod,
    ValuationDataGapKind as Gap,
    ValuationDecisionEligibility as Eligibility,
    ValuationFactExclusionReason as Excluded,
    ValuationMethodKind,
    ValuationStatus as Status,
)
from atlas.analysis_engine.valuation.models import FcfYieldEpochObservation
from atlas.decision_engine.contracts import EvidenceCoverageLevel
from tests.unit.analysis_engine.valuation._epochs import (
    annual_history,
    evaluate,
    filed_on,
    filing,
    first_quote_day,
    quote,
    real_case,
    report_fcf,
    statement_fcf,
)

#: Four fiscal years, a steady business: yields 10%, 11%, 12% before today.
YEARS = {2021: 100.0, 2022: 110.0, 2023: 120.0, 2024: 130.0}
PRICES = {2021: 10.0, 2022: 10.0, 2023: 10.0}


def history(today_price: float, *, fcf=YEARS, prices=PRICES):
    business, market = annual_history(fcf, prices)
    return business, [*market, *quote("2026-08-20", today_price)]


class TestTheComparisonIsUnchanged:
    """Above every prior yield, below every one, or inside -- the ATLAS-024
    rule, applied to fiscal epochs."""

    def test_above_every_prior_yield_is_undervalued(self):
        finding = evaluate(*history(today_price=5.0))  # 130 / 500 = 26%
        assert finding.status is Status.UNDERVALUED
        assert finding.fcf_yield_evidence.position is Position.ABOVE_ALL_PRIOR
        assert finding.confidence is EvidenceCoverageLevel.FULL
        assert finding.missing_evidence == ()

    def test_below_every_prior_yield_is_expensive(self):
        finding = evaluate(*history(today_price=20.0))  # 130 / 2000 = 6.5%
        assert finding.status is Status.EXPENSIVE

    def test_inside_the_prior_range_is_fairly_valued(self):
        finding = evaluate(*history(today_price=11.8))  # 130 / 1180 = 11.0%
        assert finding.status is Status.FAIRLY_VALUED

    def test_historical_yields_are_the_prior_epochs_sorted(self):
        finding = evaluate(*history(today_price=11.8))
        assert finding.historical_yields == pytest.approx((0.10, 0.11, 0.12))
        assert finding.current_yield == pytest.approx(130 / 1180)

    def test_no_universal_yield_threshold_in_the_source(self):
        source = inspect.getsource(cash_flow)
        code = "\n".join(line for line in source.splitlines() if not line.strip().startswith("#"))
        for pattern in (r"current_yield\s*[<>]=?\s*\d", r"\d\s*[<>]=?\s*current_yield", r"yield\s*[<>]=?\s*0\.\d"):
            assert not re.search(pattern, code)


class TestFiscalPairing:
    def test_a_fiscal_year_is_available_from_the_first_statement_filed_after_it_ended(self):
        finding = evaluate(*history(today_price=11.8))
        for epoch in finding.fcf_yield_evidence.prior_epochs:
            assert epoch.available_from == filed_on(int(epoch.fiscal_period[:4]))

    def test_a_comparative_republished_later_still_pairs_with_its_own_year(self):
        # As SEC statements are held: each fiscal year's figure was last
        # carried by the report two years later, so its own `published_at`
        # is that later date. Every report's filing date is still known.
        years = range(2017, 2025)
        business = [
            statement_fcf(100.0 + year - 2017, f"{year}-12-31", filed_on(min(year + 2, 2024))) for year in years
        ]
        business += [filing(filed_on(year)) for year in years]
        market = [f for year in range(2017, 2024) for f in quote(first_quote_day(year), 10.0)]
        market += quote("2026-08-20", 10.0)
        evidence = evaluate(business, market).fcf_yield_evidence
        for epoch in evidence.prior_epochs:
            # The 2019 price meets fiscal 2018 -- never fiscal 2016.
            assert int(epoch.observed_on[:4]) == int(epoch.fiscal_period[:4]) + 1
        assert evidence.current.fiscal_period == "2024-12-31"

    def test_the_old_rule_would_have_paired_two_years_back(self):
        # The same corpus under "latest period published by the snapshot
        # date": the 2019 price would meet fiscal 2017's figure, carried by
        # the 2019 report. The epoch construction never does.
        business = [statement_fcf(100.0, "2017-12-31", filed_on(2019)), statement_fcf(200.0, "2018-12-31", filed_on(2020))]
        business += [filing(filed_on(2017)), filing(filed_on(2018))]
        market = [*quote(first_quote_day(2018), 10.0), *quote("2026-08-20", 10.0)]
        evidence = evaluate(business, market).fcf_yield_evidence
        # The 2019 price belongs to fiscal 2018 -- today's fiscal year -- so
        # it is set aside with it, never paired with fiscal 2017.
        assert evidence.current.fiscal_period == "2018-12-31"
        assert evidence.consolidated_observations == (first_quote_day(2018),)
        assert evidence.prior_epochs == ()

    def test_a_price_before_the_year_was_filed_meets_the_year_before(self):
        # Fiscal 2024 ended; its report is not filed yet on 2025-01-20.
        business, market = annual_history(YEARS, PRICES)
        market += quote("2025-01-20", 10.0)
        evidence = evaluate(business, market).fcf_yield_evidence
        assert evidence.current.fiscal_period == "2023-12-31"
        assert evidence.current.free_cash_flow == 120.0

    def test_no_price_ever_meets_a_year_before_it_was_public(self):
        finding = evaluate(*history(today_price=11.8))
        evidence = finding.fcf_yield_evidence
        for epoch in (*evidence.prior_epochs, evidence.current):
            assert epoch.observed_on >= epoch.available_from.isoformat()

    def test_an_epoch_cannot_be_constructed_with_look_ahead(self):
        epoch = evaluate(*history(today_price=11.8)).fcf_yield_evidence.prior_epochs[0]
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(epoch, observed_on="2021-12-31")

    def test_a_missing_report_makes_availability_later_never_earlier(self):
        # Fiscal 2022's own report is missing: its figure is only known from
        # the next filing Atlas holds.
        business = [
            statement_fcf(100.0, "2021-12-31", filed_on(2021)),
            statement_fcf(110.0, "2022-12-31", filed_on(2023)),
            statement_fcf(120.0, "2023-12-31", filed_on(2023)),
        ]
        market = [*quote("2022-06-30", 10.0), *quote(first_quote_day(2022), 10.0), *quote("2026-08-20", 10.0)]
        evidence = evaluate(business, market).fcf_yield_evidence
        assert evidence.current.fiscal_period == "2023-12-31"
        assert evidence.current.available_from == filed_on(2023)
        assert evidence.prior_epochs[0].available_from == filed_on(2021)
        # Fiscal 2022 was not public before 2024, so nothing earlier meets
        # it; and the 2023-02 price came after fiscal 2022 closed, so it is
        # not a fiscal 2021 observation either. Only the mid-2022 price is.
        assert [(e.fiscal_period, e.observed_on) for e in evidence.prior_epochs] == [("2021-12-31", "2022-06-30")]

    def test_a_prior_observation_is_taken_within_its_fiscal_years_following_year(self):
        # No reports between fiscal 2012 and 2021: the only prices after 2013
        # belong to years Atlas does not hold, never to fiscal 2012.
        business = [
            statement_fcf(10.0, "2012-12-31", filed_on(2012)),
            *(statement_fcf(100.0 + y, f"{y}-12-31", filed_on(y)) for y in (2021, 2022, 2023, 2024)),
        ]
        market = [f for day in ("2014-06-30", "2016-06-30", "2019-06-28") for f in quote(day, 10.0)]
        market += [f for y in (2021, 2022, 2023) for f in quote(first_quote_day(y), 10.0)]
        market += quote("2026-08-20", 10.0)
        evidence = evaluate(business, market).fcf_yield_evidence
        assert "2012-12-31" not in [e.fiscal_period for e in evidence.prior_epochs]
        assert [e.fiscal_period[:4] for e in evidence.prior_epochs] == ["2021", "2022", "2023"]


class TestOneObservationPerEpoch:
    def test_refreshes_of_the_current_year_add_no_history(self):
        business, market = annual_history(YEARS, PRICES)
        once = evaluate(business, [*market, *quote("2026-08-20", 11.8)])
        often = evaluate(business, [*market, *(f for day in ("2026-02-27", "2026-08-07", "2026-08-17", "2026-08-20")
                                              for f in quote(day, 11.8))])
        assert often.fcf_yield_evidence.prior_epoch_count == once.fcf_yield_evidence.prior_epoch_count == 3
        assert often.historical_yields == once.historical_yields
        assert often.fcf_yield_evidence.consolidated_observations == ("2026-02-27", "2026-08-07", "2026-08-17")

    def test_the_current_year_never_appears_in_its_own_history(self):
        business, market = annual_history(YEARS, PRICES)
        # An earlier price in the current fiscal year, far cheaper than today.
        finding = evaluate(business, [*market, *quote("2025-03-01", 2.0), *quote("2026-08-20", 11.8)])
        evidence = finding.fcf_yield_evidence
        assert evidence.current.fiscal_period == "2024-12-31"
        assert all(e.fiscal_period < "2024-12-31" for e in evidence.prior_epochs)
        assert finding.status is Status.FAIRLY_VALUED

    def test_a_prior_epoch_is_its_first_observation_so_later_refreshes_change_nothing(self):
        business, market = annual_history(YEARS, PRICES)
        base = evaluate(business, [*market, *quote("2026-08-20", 11.8)])
        refreshed = evaluate(business, [*market, *quote("2022-11-30", 1.0), *quote("2026-08-20", 11.8)])
        assert refreshed.historical_yields == base.historical_yields
        assert refreshed.fcf_yield_evidence.consolidated_observations == ("2022-11-30",)

    def test_a_later_repetition_of_a_fiscal_year_is_not_a_new_epoch(self):
        business, market = annual_history(YEARS, PRICES)
        repeated = [*business, statement_fcf(110.0, "2022-12-31", filed_on(2024))]
        base = evaluate(business, [*market, *quote("2026-08-20", 11.8)])
        again = evaluate(repeated, [*market, *quote("2026-08-20", 11.8)])
        assert again.fcf_yield_evidence.prior_epoch_count == base.fcf_yield_evidence.prior_epoch_count

    def test_two_share_classes_with_different_refresh_counts_have_the_same_depth(self):
        business, market = annual_history(YEARS, PRICES)
        class_a = evaluate(business, [*market, *quote("2026-08-20", 11.8)])
        class_b = evaluate(business, [*market, *quote("2026-08-07", 11.5), *quote("2026-08-20", 11.8)])
        assert [e.fiscal_period for e in class_a.fcf_yield_evidence.prior_epochs] == [
            e.fiscal_period for e in class_b.fcf_yield_evidence.prior_epochs]
        assert class_a.status is class_b.status


class TestDecisionEligibility:
    @pytest.mark.parametrize("prior, eligibility", [
        (0, Eligibility.INSUFFICIENT), (1, Eligibility.LIMITED), (2, Eligibility.LIMITED),
        (3, Eligibility.ELIGIBLE), (4, Eligibility.ELIGIBLE), (6, Eligibility.ELIGIBLE),
    ])
    def test_eligibility_by_prior_epochs(self, prior, eligibility):
        years = {2024 - prior + i: 100.0 for i in range(prior + 1)}
        prices = {year: 10.0 for year in list(years)[:-1]}
        business, market = annual_history(years, prices)
        finding = evaluate(business, [*market, *quote("2026-08-20", 5.0)])
        assert finding.fcf_yield_evidence.prior_epoch_count == prior
        assert finding.fcf_yield_evidence.eligibility is eligibility

    def test_three_prior_epochs_is_the_policy(self):
        assert MINIMUM_PRIOR_EPOCHS == 3

    @pytest.mark.parametrize("today_price, position", [
        (5.0, Position.ABOVE_ALL_PRIOR), (20.0, Position.BELOW_ALL_PRIOR), (11.4, Position.WITHIN_PRIOR_RANGE),
    ])
    def test_limited_history_is_described_never_classified(self, today_price, position):
        business, market = annual_history({2022: 100.0, 2023: 110.0, 2024: 120.0}, {2022: 10.0, 2023: 10.0})
        finding = evaluate(business, [*market, *quote("2026-08-20", today_price)])
        evidence = finding.fcf_yield_evidence
        assert evidence.eligibility is Eligibility.LIMITED
        assert evidence.position is position
        assert finding.status is Status.INSUFFICIENT_INPUT
        assert finding.historical_yields == ()
        assert finding.current_yield is not None
        assert finding.missing_evidence == (Gap.INSUFFICIENT_HISTORICAL_VALUATION_PERIODS,)

    def test_no_prior_epoch_keeps_the_current_yield_and_says_why(self):
        business, market = annual_history({2024: 120.0}, {})
        finding = evaluate(business, [*market, *quote("2026-08-07", 10.0), *quote("2026-08-20", 10.5)])
        assert finding.fcf_yield_evidence.eligibility is Eligibility.INSUFFICIENT
        assert finding.current_yield == pytest.approx(120 / 1050)
        assert finding.status is Status.INSUFFICIENT_INPUT
        assert finding.missing_evidence == (Gap.INSUFFICIENT_HISTORICAL_VALUATION_PERIODS,)

    def test_a_classified_status_over_limited_evidence_is_rejected(self):
        business, market = annual_history({2022: 100.0, 2023: 110.0, 2024: 120.0}, {2022: 10.0, 2023: 10.0})
        finding = evaluate(business, [*market, *quote("2026-08-20", 20.0)])
        for status in (Status.EXPENSIVE, Status.FAIRLY_VALUED, Status.UNDERVALUED):
            with pytest.raises(AnalysisEngineContractError):
                dataclasses.replace(finding, status=status)

    def test_limited_history_never_reaches_historical_yields(self):
        business, market = annual_history({2022: 100.0, 2023: 110.0, 2024: 120.0}, {2022: 10.0, 2023: 10.0})
        finding = evaluate(business, [*market, *quote("2026-08-20", 20.0)])
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(finding, historical_yields=finding.fcf_yield_evidence.prior_yields)

    def test_eligibility_must_match_the_evidence(self):
        evidence = evaluate(*history(today_price=11.8)).fcf_yield_evidence
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(evidence, eligibility=Eligibility.LIMITED)
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(evidence, prior_epochs=evidence.prior_epochs[:2])

    def test_span_and_bounds_are_retained(self):
        evidence = evaluate(*history(today_price=11.8)).fcf_yield_evidence
        assert evidence.earliest_prior_epoch == "2021-12-31"
        assert evidence.latest_prior_epoch == "2023-12-31"
        assert evidence.span_years == pytest.approx(3.0, abs=0.01)


class TestSourceEligibility:
    def test_a_future_fiscal_year_is_excluded_and_named(self):
        business, market = history(today_price=11.8)
        future = statement_fcf(300.0, "2027-09-26", "2026-08-10")
        finding = evaluate([*business, future], market)
        assert finding.fcf_yield_evidence.excluded[0].reason is Excluded.FUTURE_PERIOD
        assert finding.fcf_yield_evidence.current.fiscal_period == "2024-12-31"
        assert finding.current_yield == pytest.approx(130 / 1180)

    def test_a_figure_outside_the_annual_statements_is_excluded_and_named(self):
        business, market = history(today_price=11.8)
        estimate = report_fcf(900.0, "2025-12-31", "2026-03-01")
        finding = evaluate([*business, estimate], market)
        assert [x.reason for x in finding.fcf_yield_evidence.excluded] == [Excluded.NOT_A_FINANCIAL_STATEMENT]
        assert finding.current_yield == pytest.approx(130 / 1180)

    def test_two_different_figures_for_one_year_are_ambiguous_and_dropped(self):
        business, market = history(today_price=11.8)
        conflicting = statement_fcf(999.0, "2022-12-31", filed_on(2022))
        finding = evaluate([*business, conflicting], market)
        assert "2022-12-31" not in [e.fiscal_period for e in finding.fcf_yield_evidence.prior_epochs]

    def test_a_currency_mismatch_forms_no_observation(self):
        business = [statement_fcf(100.0 + y, f"{y}-12-31", filed_on(y), unit="EUR") for y in (2021, 2022, 2023, 2024)]
        market = [f for y in (2021, 2022, 2023) for f in quote(first_quote_day(y), 10.0)] + list(quote("2026-08-20", 10.0))
        finding = evaluate(business, market)
        assert finding.current_yield is None
        assert Gap.CURRENCY_MISMATCH in finding.missing_evidence

    def test_input_order_never_matters(self):
        business, market = history(today_price=11.8)
        business = [*business, report_fcf(900.0, "2025-12-31", "2026-03-01"), statement_fcf(300.0, "2027-09-26", "2026-08-10")]
        expected = evaluate(business, market)
        rng = random.Random(7)
        for _ in range(5):
            b, m = list(business), list(market)
            rng.shuffle(b)
            rng.shuffle(m)
            assert evaluate(b, m) == expected


class TestNonPositiveCashFlow:
    def test_negative_current_cash_flow_forms_no_current_observation(self):
        business, market = annual_history({**YEARS, 2024: -50.0}, PRICES)
        finding = evaluate(business, [*market, *quote("2026-08-20", 10.0)])
        assert finding.current_yield is None
        assert finding.status is Status.INSUFFICIENT_INPUT
        assert Gap.CASH_FLOW_NOT_POSITIVE in finding.missing_evidence

    def test_zero_current_cash_flow_forms_no_current_observation(self):
        business, market = annual_history({**YEARS, 2024: 0.0}, PRICES)
        finding = evaluate(business, [*market, *quote("2026-08-20", 10.0)])
        assert finding.current_yield is None

    def test_a_negative_prior_year_is_skipped_not_counted(self):
        business, market = annual_history({2020: 90.0, **YEARS, 2022: -10.0}, {2020: 10.0, **PRICES})
        evidence = evaluate(business, [*market, *quote("2026-08-20", 11.8)]).fcf_yield_evidence
        assert [e.fiscal_period[:4] for e in evidence.prior_epochs] == ["2020", "2021", "2023"]


class TestApplicability:
    @pytest.mark.parametrize("industry", ["BANKS - DIVERSIFIED", "CAPITAL MARKETS", "INSURANCE - DIVERSIFIED"])
    def test_balance_sheet_financials_are_not_applicable(self, industry):
        finding = evaluate(*history(today_price=11.8), industry=industry)
        assert finding.fcf_yield_evidence.eligibility is Eligibility.NOT_APPLICABLE
        assert finding.status is Status.INSUFFICIENT_INPUT
        assert finding.current_yield is None and finding.historical_yields == ()
        assert finding.missing_evidence == (Gap.VALUATION_METHOD_NOT_APPLICABLE,)
        assert finding.confidence is EvidenceCoverageLevel.NOT_APPLICABLE

    @pytest.mark.parametrize("industry", ["CREDIT SERVICES", "FINANCIAL DATA & STOCK EXCHANGES", "INSURANCE BROKERS"])
    def test_operating_financial_services_stay_applicable(self, industry):
        assert evaluate(*history(today_price=11.8), industry=industry).status is Status.FAIRLY_VALUED

    def test_an_unknown_industry_is_named_not_assumed(self):
        finding = evaluate(*history(today_price=11.8), industry=None)
        assert finding.status is Status.INSUFFICIENT_INPUT
        assert finding.missing_evidence == (Gap.VALUATION_APPLICABILITY_UNKNOWN,)

    def test_not_applicable_carries_no_observation(self):
        evidence = evaluate(*history(today_price=11.8), industry="CAPITAL MARKETS").fcf_yield_evidence
        current = evaluate(*history(today_price=11.8)).fcf_yield_evidence.current
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(evidence, current=current)


class TestShareCountProxy:
    def test_every_evidence_names_the_proxy(self):
        assert SHARE_COUNT_METHOD is ShareCountMethod.CURRENT_SHARE_COUNT_PROXY
        assert evaluate(*history(today_price=11.8)).fcf_yield_evidence.share_count_method is SHARE_COUNT_METHOD
        assert list(ShareCountMethod) == [ShareCountMethod.CURRENT_SHARE_COUNT_PROXY]

    def test_no_historical_market_cap_is_called_exact(self):
        names = {f.name for f in dataclasses.fields(FcfYieldEpochObservation)} | {
            n for n, v in vars(FcfYieldEpochObservation).items() if isinstance(v, property)}
        assert "market_cap_proxy" in names
        assert not any(n in names for n in ("market_cap", "market_capitalisation", "historical_market_cap"))
        assert "proxy" in (FcfYieldEpochObservation.__doc__ or "")


class TestMissingInputs:
    def test_nothing_at_all_names_all_three_inputs(self):
        finding = evaluate((), ())
        assert finding.status is Status.INSUFFICIENT_INPUT
        assert set(finding.missing_evidence) >= {
            Gap.MISSING_FREE_CASH_FLOW_HISTORY, Gap.MISSING_MARKET_PRICE, Gap.MISSING_SHARE_COUNT}
        assert finding.confidence is EvidenceCoverageLevel.NOT_APPLICABLE

    def test_prices_before_any_filing_have_no_eligible_fundamentals(self):
        business, _ = annual_history({2024: 120.0}, {})
        finding = evaluate(business, quote("2024-06-28", 10.0))
        assert Gap.NO_ELIGIBLE_FUNDAMENTALS_AS_OF_OBSERVATION in finding.missing_evidence

    def test_the_finding_is_the_fcf_yield_method(self):
        finding = evaluate(*history(today_price=11.8))
        assert finding.kind is ValuationMethodKind.FCF_YIELD_RELATIVE
        assert set(finding.provenance.dependencies) == set(finding.fcf_yield_evidence.current.fact_ids)
        epochs = (finding.fcf_yield_evidence.current, *finding.fcf_yield_evidence.prior_epochs)
        assert set(finding.supporting_facts) == {i for e in epochs for i in e.fact_ids}


# Real companies, as Atlas holds them on 2026-09-11. Expectations were
# measured, not chosen: see the sprint's before/after census.
REAL = {
    #  ticker: (eligibility, status, prior epochs, current fiscal year)
    "GOOGL": (Eligibility.ELIGIBLE, Status.EXPENSIVE, 10, "2025-12-31"),
    "GOOG": (Eligibility.ELIGIBLE, Status.EXPENSIVE, 10, "2025-12-31"),
    "AAPL": (Eligibility.ELIGIBLE, Status.EXPENSIVE, 16, "2025-09-27"),
    "VST": (Eligibility.ELIGIBLE, Status.EXPENSIVE, 4, "2025-12-31"),
    "AMZN": (Eligibility.ELIGIBLE, Status.EXPENSIVE, 14, "2025-12-31"),
    "META": (Eligibility.ELIGIBLE, Status.FAIRLY_VALUED, 13, "2025-12-31"),
    "MU": (Eligibility.ELIGIBLE, Status.FAIRLY_VALUED, 11, "2025-08-28"),
    "CRWD": (Eligibility.ELIGIBLE, Status.FAIRLY_VALUED, 6, "2026-01-31"),
    "SHOP": (Eligibility.LIMITED, Status.INSUFFICIENT_INPUT, 1, "2025-12-31"),
    "AZN": (Eligibility.INSUFFICIENT, Status.INSUFFICIENT_INPUT, 0, "2025-12-31"),
    "AVGO": (Eligibility.INSUFFICIENT, Status.INSUFFICIENT_INPUT, 0, "2025-11-02"),
    "TSM": (Eligibility.INSUFFICIENT, Status.INSUFFICIENT_INPUT, 0, "2024-12-31"),
    "ASML": (Eligibility.INSUFFICIENT, Status.INSUFFICIENT_INPUT, 0, None),
    "INTC": (Eligibility.INSUFFICIENT, Status.INSUFFICIENT_INPUT, 0, None),
    "GS": (Eligibility.NOT_APPLICABLE, Status.INSUFFICIENT_INPUT, 0, None),
    "JPM": (Eligibility.NOT_APPLICABLE, Status.INSUFFICIENT_INPUT, 0, None),
    "BRK.B": (Eligibility.NOT_APPLICABLE, Status.INSUFFICIENT_INPUT, 0, None),
}


def real(ticker: str):
    business, market, industry = real_case(ticker)
    return evaluate(business, market, industry=industry)


class TestRealCompanies:
    @pytest.mark.parametrize("ticker", sorted(REAL))
    def test_measured_outcome(self, ticker):
        eligibility, status, prior, current = REAL[ticker]
        finding = real(ticker)
        evidence = finding.fcf_yield_evidence
        assert evidence.eligibility is eligibility
        assert finding.status is status
        assert evidence.prior_epoch_count == prior
        assert (evidence.current.fiscal_period if evidence.current else None) == current

    def test_googl_rests_on_a_decade_of_fiscal_years_and_goog_on_the_same_ones(self):
        googl, goog = real("GOOGL").fcf_yield_evidence, real("GOOG").fcf_yield_evidence
        assert googl.earliest_prior_epoch == "2015-12-31" and googl.span_years >= 10
        assert [e.fiscal_period for e in googl.prior_epochs] == [e.fiscal_period for e in goog.prior_epochs]
        # GOOG's extra refresh in the current year is set aside, not counted.
        assert len(goog.consolidated_observations) > len(googl.consolidated_observations)

    def test_aapl_never_prices_the_fiscal_2027_verification_figure(self):
        finding = real("AAPL")
        evidence = finding.fcf_yield_evidence
        assert [(x.fact_id.split(":")[-1], x.reason) for x in evidence.excluded] == [("2027-09-26", Excluded.FUTURE_PERIOD)]
        assert evidence.current.free_cash_flow == 98_767_000_000.0
        assert finding.current_yield == pytest.approx(0.0214, abs=0.0001)

    def test_thin_cheapness_and_thin_expense_do_not_classify(self):
        # TSM looked cheaper than one earlier price, AZN dearer than two:
        # both of those "histories" were refreshes of the same fiscal year.
        for ticker in ("TSM", "AZN", "AVGO"):
            finding = real(ticker)
            assert finding.current_yield is not None
            assert finding.historical_yields == ()
            assert finding.status is Status.INSUFFICIENT_INPUT

    def test_shop_is_described_below_its_one_prior_year_but_not_expensive(self):
        finding = real("SHOP")
        assert finding.fcf_yield_evidence.position is Position.BELOW_ALL_PRIOR
        assert finding.status is Status.INSUFFICIENT_INPUT

    def test_asml_reports_statements_and_quote_in_different_currencies(self):
        assert Gap.CURRENCY_MISMATCH in real("ASML").missing_evidence

    def test_banks_dealers_and_insurers_get_no_yield(self):
        for ticker in ("GS", "JPM", "BRK.B"):
            finding = real(ticker)
            assert finding.current_yield is None
            assert finding.missing_evidence == (Gap.VALUATION_METHOD_NOT_APPLICABLE,)

    def test_amzn_skips_its_negative_cash_flow_years(self):
        periods = [e.fiscal_period for e in real("AMZN").fcf_yield_evidence.prior_epochs]
        assert "2021-12-31" not in periods and "2022-12-31" not in periods
