"""Financial Risk v2 -- scale-aware debt burden.

The company fixtures are real: each tuple is a fiscal period end with
reported total debt, free cash flow and capital expenditure (billions),
exactly as Atlas holds them for that ticker. Fixture data, not rules --
nothing in the evaluator knows a ticker; the industry passed is the
company-profile label.
"""
from __future__ import annotations

import inspect
from datetime import datetime, timezone
from itertools import count

import pytest

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind as K
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.risk import financial_risk
from atlas.analysis_engine.risk.applicability import debt_burden_measure_applies
from atlas.analysis_engine.risk.contracts import (
    FinancialRiskCondition as C,
    FinancialRiskExclusionReason,
    FinancialRiskMeasure,
    RiskDataGapKind as Gap,
    RiskStatus,
)
from atlas.analysis_engine.risk.financial_risk import (
    DEBT_BURDEN_BANDS,
    FINANCIAL_STATEMENT_MAX_AGE_DAYS,
    evaluate_financial_risk,
)
from atlas.decision_engine.contracts import EvidenceCoverageLevel

AS_OF = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)
_ids = count()

COMPANIES = {
    "VST": ("UTILITIES - INDEPENDENT POWER PRODUCERS", (
        ("2023-12-31", 14.402, 3.777, 1.676), ("2024-12-31", 16.298, 2.485, 2.078), ("2025-12-31", 17.043, 1.318, 2.752))),
    "META": ("INTERNET CONTENT & INFORMATION", (
        ("2023-12-31", 18.385, 44.068, 27.045), ("2024-12-31", 28.826, 54.072, 37.256), ("2025-12-31", 58.744, 46.109, 69.691))),
    "INTC": ("SEMICONDUCTORS", (
        ("2023-12-30", 49.266, -14.279, 25.750), ("2024-12-28", 50.011, -15.656, 23.944), ("2025-12-27", 46.585, -4.949, 14.646))),
    "CAT": ("FARM & HEAVY CONSTRUCTION MACHINERY", (
        ("2023-12-31", 29.115, 11.288, 1.597), ("2024-12-31", 31.744, 10.047, 1.988), ("2025-12-31", 36.210, 8.918, 2.821))),
    "UNP": ("RAILROADS", (
        ("2023-12-31", 32.579, 4.773, 3.606), ("2024-12-31", 31.192, 5.894, 3.452), ("2025-12-31", 31.814, 5.499, 3.791))),
    "V": ("CREDIT SERVICES", (
        ("2023-09-30", 20.463, 19.696, 1.059), ("2024-09-30", 20.836, 18.693, 1.257), ("2025-09-30", 25.171, 21.577, 1.482))),
    "MA": ("CREDIT SERVICES", (
        ("2023-12-31", 15.681, 11.609, 0.371), ("2024-12-31", 18.226, 14.306, 0.474), ("2025-12-31", 19.000, 17.159, 0.489))),
    "MCO": ("FINANCIAL DATA & STOCK EXCHANGES", (
        ("2023-12-31", 7.001, 1.880, 0.271), ("2024-12-31", 7.428, 2.521, 0.317), ("2025-12-31", 6.994, 2.575, 0.326))),
    "AMAT": ("SEMICONDUCTOR EQUIPMENT & MATERIALS", (
        ("2023-10-29", 5.461, 7.594, 1.106), ("2024-10-27", 6.160, 7.487, 1.190), ("2025-10-26", 6.455, 5.698, 2.260))),
    "AMZN": ("INTERNET RETAIL", (
        ("2023-12-31", 66.808, 32.217, 52.729), ("2024-12-31", 57.640, 32.878, 82.999), ("2025-12-31", 68.396, 7.695, 131.819))),
    "NVDA": ("SEMICONDUCTORS", (
        ("2024-01-28", 9.709, 27.021, 1.069), ("2025-01-26", 8.463, 60.853, 3.236), ("2026-01-25", 8.468, 96.676, 6.042))),
    "MU": ("SEMICONDUCTORS", (
        ("2023-08-31", 12.049, -6.117, 7.676), ("2024-08-29", 11.343, 0.121, 8.386), ("2025-08-28", 11.533, 1.668, 15.857))),
}


def fact(kind: K, value: float, period: str, *, record: str | None = None, unit: str = "USD") -> BusinessFact:
    i = next(_ids)
    record = record or f"statement-{i}"
    return BusinessFact(
        id=f"{record}:{kind.value}:{period}", company="TEST", kind=kind, value=value, unit=unit, period=period,
        source_record_id=record,
        provenance=Provenance(source_kind=SourceKind.ANALYSIS_ENGINE_STAGE, source_references=(), dependencies=(),
                              update_trigger=UpdateTrigger.UPSTREAM_STAGE_CHANGED, consumers=(Consumer.HISTORY,),
                              computed_at=AS_OF),
        extracted_at=AS_OF, published_at=AS_OF,
    )


def period_facts(period, debt, fcf, capex, *, record=None, unit="USD"):
    record = record or f"statement-{period}-{next(_ids)}"
    return (fact(K.TOTAL_DEBT, debt * 1e9, period, record=record, unit=unit),
            fact(K.FREE_CASH_FLOW, fcf * 1e9, period, record=record, unit=unit),
            fact(K.CAPITAL_EXPENDITURE, capex * 1e9, period, record=record, unit=unit))


def statements(facts):
    return frozenset(f.source_record_id for f in facts)


def evaluate(facts, industry="SEMICONDUCTORS", *, statement_ids=None, as_of=AS_OF):
    return evaluate_financial_risk(
        tuple(facts), statement_record_ids=statements(facts) if statement_ids is None else statement_ids,
        industry=industry, evaluated_at=as_of)


def company(ticker):
    industry, rows = COMPANIES[ticker]
    facts = tuple(f for row in rows for f in period_facts(*row))
    return evaluate(facts, industry)


def ratio(finding):
    return round(finding.financial_risk_basis.latest.ratio, 2)


class TestRealCompanies:
    def test_vst_is_high_because_debt_is_large_relative_to_operating_cash_flow(self):
        finding = company("VST")
        assert finding.status is RiskStatus.HIGH
        assert finding.financial_risk_basis.condition is C.DEBT_BURDEN_HIGH
        assert ratio(finding) == 4.19
        latest = finding.financial_risk_basis.latest
        assert latest.period == "2025-12-31"
        assert latest.operating_cash_flow == pytest.approx(4.07e9)

    def test_meta_is_low_despite_debt_rising_every_period(self):
        finding = company("META")
        assert finding.status is RiskStatus.LOW
        assert ratio(finding) == 0.51
        assert [round(o.total_debt / 1e9, 1) for o in finding.financial_risk_basis.history] == [18.4, 28.8, 58.7]

    def test_intc_is_high_on_burden_not_on_its_negative_free_cash_flow(self):
        finding = company("INTC")
        assert finding.status is RiskStatus.HIGH
        assert finding.financial_risk_basis.condition is C.DEBT_BURDEN_HIGH  # not a cash-flow-sign condition
        assert ratio(finding) == 4.8
        assert finding.financial_risk_basis.latest.free_cash_flow < 0 < finding.financial_risk_basis.latest.operating_cash_flow

    @pytest.mark.parametrize("ticker,level,value", [
        ("CAT", RiskStatus.HIGH, 3.08), ("UNP", RiskStatus.HIGH, 3.42), ("MCO", RiskStatus.MODERATE, 2.41),
        ("V", RiskStatus.LOW, 1.09), ("MA", RiskStatus.LOW, 1.08), ("AMAT", RiskStatus.LOW, 0.81),
        ("AMZN", RiskStatus.LOW, 0.49), ("NVDA", RiskStatus.LOW, 0.08), ("MU", RiskStatus.LOW, 0.66),
    ])
    def test_every_control_is_classified_by_its_latest_burden(self, ticker, level, value):
        finding = company(ticker)
        assert (finding.status, ratio(finding)) == (level, value)

    def test_amzn_high_capex_does_not_read_as_burden(self):
        """Free cash flow is 7.7 bn after 131.8 bn of capex; operating cash
        flow is 139.5 bn. Debt over free cash flow would read 8.9x."""
        basis = company("AMZN").financial_risk_basis
        assert basis.latest.total_debt / basis.latest.free_cash_flow > 8
        assert basis.latest.ratio < DEBT_BURDEN_BANDS.low_below


class TestTrendIsContextOnly:
    def test_v_rising_burden_is_still_low(self):
        basis = company("V").financial_risk_basis
        assert [round(o.ratio, 2) for o in basis.history] == [0.99, 1.04, 1.09]
        assert basis.level is RiskStatus.LOW

    def test_amat_rising_burden_is_still_low(self):
        basis = company("AMAT").financial_risk_basis
        assert [round(o.ratio, 2) for o in basis.history] == [0.63, 0.71, 0.81]
        assert basis.level is RiskStatus.LOW

    def test_vst_trend_is_carried_but_the_latest_decides(self):
        basis = company("VST").financial_risk_basis
        assert [round(o.ratio, 2) for o in basis.history] == [2.64, 3.57, 4.19]
        assert basis.latest is basis.history[-1]

    def test_a_falling_burden_is_not_rewarded_below_its_latest_level(self):
        basis = company("MCO").financial_risk_basis
        assert [round(o.ratio, 2) for o in basis.history] == [3.25, 2.62, 2.41]
        assert basis.level is RiskStatus.MODERATE

    def test_history_keeps_at_most_three_periods(self):
        facts = [f for year in range(2018, 2026) for f in period_facts(f"{year}-12-31", 1.0, 1.0, 0.0)]
        assert len(evaluate(facts).financial_risk_basis.history) == 3


class TestNoDoubleCounting:
    def test_the_evaluator_takes_no_capital_allocation_input(self):
        params = inspect.signature(evaluate_financial_risk).parameters
        assert "capital_allocation_finding" not in params
        source = inspect.getsource(financial_risk)
        assert "BusinessCategoryStatus" not in source and "capital_allocation_finding" not in source

    def test_negative_free_cash_flow_alone_never_makes_high(self):
        finding = evaluate(period_facts("2025-12-31", 1.0, -3.0, 5.0))
        assert finding.status is RiskStatus.LOW  # operating cash flow 2.0, debt 1.0 -> 0.5x

    def test_rising_debt_alone_never_makes_high(self):
        facts = [f for y, d in ((2023, 1.0), (2024, 2.0), (2025, 3.0)) for f in period_facts(f"{y}-12-31", d, 8.0, 2.0)]
        assert evaluate(facts).status is RiskStatus.LOW


class TestOperatingCashFlowSign:
    def test_negative_operating_cash_flow_is_high_and_named_as_such(self):
        basis = evaluate(period_facts("2025-12-31", 5.0, -4.0, 1.0)).financial_risk_basis
        assert (basis.level, basis.condition) == (RiskStatus.HIGH, C.OPERATING_CASH_FLOW_NEGATIVE)
        assert basis.latest.ratio is None

    def test_zero_operating_cash_flow_is_high_and_never_divided(self):
        basis = evaluate(period_facts("2025-12-31", 5.0, -2.0, 2.0)).financial_risk_basis
        assert (basis.level, basis.condition) == (RiskStatus.HIGH, C.OPERATING_CASH_FLOW_ZERO)
        assert basis.latest.ratio is None

    def test_a_tiny_positive_operating_cash_flow_keeps_its_true_large_ratio(self):
        basis = evaluate(period_facts("2025-12-31", 5.0, 0.001, 0.0)).financial_risk_basis
        assert basis.condition is C.DEBT_BURDEN_HIGH
        assert basis.latest.ratio == pytest.approx(5000.0)  # never capped

    def test_no_debt_is_zero_burden_not_missing(self):
        assert evaluate(period_facts("2025-12-31", 0.0, 3.0, 1.0)).status is RiskStatus.LOW


class TestBands:
    def test_the_policy_bands(self):
        assert (DEBT_BURDEN_BANDS.low_below, DEBT_BURDEN_BANDS.high_from) == (1.25, 3.0)

    @pytest.mark.parametrize("debt,level", [(1.24, RiskStatus.LOW), (1.25, RiskStatus.MODERATE),
                                            (2.99, RiskStatus.MODERATE), (3.0, RiskStatus.HIGH)])
    def test_band_edges(self, debt, level):
        assert evaluate(period_facts("2025-12-31", debt, 1.0, 0.0)).status is level

    def test_bands_are_documented_as_policy_not_credit_thresholds(self):
        doc = inspect.getdoc(financial_risk)
        assert "not credit-rating thresholds" in doc
        from atlas.analysis_engine.risk.models import DebtBurdenBands
        assert "not credit-rating thresholds" in inspect.getdoc(DebtBurdenBands)


class TestApplicability:
    @pytest.mark.parametrize("industry", ["BANKS - DIVERSIFIED", "BANKS - REGIONAL", "CAPITAL MARKETS",
                                          "INSURANCE - DIVERSIFIED", "INSURANCE - LIFE", "MORTGAGE FINANCE",
                                          "  capital   markets "])
    def test_balance_sheet_financials_are_not_applicable(self, industry):
        finding = evaluate(period_facts("2025-12-31", 250.0, -47.0, 2.0), industry)
        assert finding.status is RiskStatus.NOT_APPLICABLE
        assert finding.financial_risk_basis.condition is C.MEASURE_NOT_APPLICABLE
        assert finding.supporting_facts == () and finding.missing_evidence == ()
        assert finding.confidence is EvidenceCoverageLevel.NOT_APPLICABLE

    @pytest.mark.parametrize("industry", ["CREDIT SERVICES", "FINANCIAL DATA & STOCK EXCHANGES", "INSURANCE BROKERS",
                                          "ASSET MANAGEMENT", "UTILITIES - REGULATED ELECTRIC", "SEMICONDUCTORS"])
    def test_operating_businesses_in_and_around_finance_are_applicable(self, industry):
        assert debt_burden_measure_applies(industry) is True

    def test_the_rule_reads_the_industry_never_the_sector(self):
        assert debt_burden_measure_applies("FINANCIAL SERVICES") is True
        source = inspect.getsource(inspect.getmodule(debt_burden_measure_applies))
        assert "GS" not in source.split('"""')[-1] and "JPM" not in source  # no issuer names in code

    @pytest.mark.parametrize("industry", [None, "", "   "])
    def test_unknown_industry_is_insufficient_never_assumed(self, industry):
        finding = evaluate(period_facts("2025-12-31", 5.0, 1.0, 0.0), industry)
        assert finding.status is RiskStatus.INSUFFICIENT_INPUT
        assert finding.missing_evidence == (Gap.INDUSTRY_UNKNOWN,)


class TestEligibility:
    def test_a_future_period_is_excluded_aapl(self):
        """AAPL's `live_verify_script` record: FY2027, free cash flow 300 bn,
        no currency. Excluded before anything is computed."""
        real = period_facts("2025-09-27", 90.678, 98.767, 12.715)
        future = fact(K.FREE_CASH_FLOW, 300e9, "2027-09-26", record="live-verify", unit="unspecified")
        finding = evaluate((*real, future), "CONSUMER ELECTRONICS", statement_ids=statements(real) | {"live-verify"})
        basis = finding.financial_risk_basis
        assert basis.latest.period == "2025-09-27"
        assert [(e.fact_id, e.reason) for e in basis.excluded] == [(future.id, FinancialRiskExclusionReason.FUTURE_PERIOD)]
        assert future.id not in finding.supporting_facts

    def test_a_non_statement_source_is_excluded(self):
        real = period_facts("2024-12-31", 2.0, 2.0, 0.0)
        other = period_facts("2025-12-31", 9.0, 1.0, 0.0, record="annual-report")
        finding = evaluate((*real, *other), statement_ids=statements(real))
        assert finding.financial_risk_basis.latest.period == "2024-12-31"
        assert {e.reason for e in finding.financial_risk_basis.excluded} == {
            FinancialRiskExclusionReason.NOT_A_FINANCIAL_STATEMENT}

    def test_stale_statements_are_insufficient_vz(self):
        facts = [f for y, d, fc, cx in ((2012, 51.99, 20.0, 16.0), (2013, 93.59, 22.0, 16.6))
                 for f in period_facts(f"{y}-12-31", d, fc, cx)]
        finding = evaluate(facts, "TELECOM SERVICES")
        assert finding.status is RiskStatus.INSUFFICIENT_INPUT
        assert finding.missing_evidence == (Gap.STALE_FINANCIAL_STATEMENTS,)
        assert finding.financial_risk_basis.history == ()

    def test_staleness_limit_is_two_years(self):
        assert FINANCIAL_STATEMENT_MAX_AGE_DAYS == 730
        fresh = evaluate(period_facts("2024-09-12", 1.0, 1.0, 0.0))
        stale = evaluate(period_facts("2024-09-10", 1.0, 1.0, 0.0))
        assert fresh.status is RiskStatus.LOW and stale.status is RiskStatus.INSUFFICIENT_INPUT

    def test_stale_debt_is_never_paired_with_current_cash_flow_gs_pattern(self):
        """Debt last reported 2015, cash flow through 2025, in an applicable industry."""
        facts = (fact(K.TOTAL_DEBT, 243e9, "2015-12-31"), *period_facts("2025-12-31", 0, 1.0, 1.0)[1:])
        finding = evaluate(facts, "RAILROADS")
        assert finding.status is RiskStatus.INSUFFICIENT_INPUT
        assert finding.missing_evidence == (Gap.NO_ALIGNED_PERIOD,)


class TestAlignment:
    def test_debt_and_cash_flow_from_different_years_are_never_combined(self):
        facts = (fact(K.TOTAL_DEBT, 5e9, "2024-12-31"), fact(K.FREE_CASH_FLOW, 1e9, "2025-12-31"),
                 fact(K.CAPITAL_EXPENDITURE, 1e9, "2025-12-31"))
        assert evaluate(facts).missing_evidence == (Gap.NO_ALIGNED_PERIOD,)

    def test_free_cash_flow_and_capex_from_different_years_are_never_combined(self):
        facts = (fact(K.TOTAL_DEBT, 5e9, "2025-12-31"), fact(K.FREE_CASH_FLOW, 1e9, "2025-12-31"),
                 fact(K.CAPITAL_EXPENDITURE, 1e9, "2024-12-31"))
        assert evaluate(facts).status is RiskStatus.INSUFFICIENT_INPUT

    def test_mismatched_units_are_never_combined(self):
        debt, fcf, capex = period_facts("2025-12-31", 5.0, 1.0, 1.0)
        facts = (debt, fact(K.FREE_CASH_FLOW, 1e9, "2025-12-31", unit="EUR"), capex)
        assert evaluate(facts).missing_evidence == (Gap.NO_ALIGNED_PERIOD,)

    def test_an_ambiguous_period_is_dropped_not_guessed(self):
        facts = (*period_facts("2025-12-31", 5.0, 1.0, 1.0), fact(K.TOTAL_DEBT, 9e9, "2025-12-31"))
        assert evaluate(facts).status is RiskStatus.INSUFFICIENT_INPUT

    def test_the_latest_aligned_period_is_used_when_the_newest_year_is_incomplete(self):
        facts = (*period_facts("2024-12-31", 2.0, 1.0, 1.0), fact(K.FREE_CASH_FLOW, 1e9, "2025-12-31"))
        assert evaluate(facts).financial_risk_basis.latest.period == "2024-12-31"


class TestInsufficient:
    def test_missing_debt_avgo_pattern(self):
        facts = (fact(K.FREE_CASH_FLOW, 20e9, "2025-11-02"), fact(K.CAPITAL_EXPENDITURE, 1e9, "2025-11-02"))
        finding = evaluate(facts)
        assert (finding.status, finding.missing_evidence) == (RiskStatus.INSUFFICIENT_INPUT, (Gap.MISSING_DEBT,))
        assert finding.confidence is EvidenceCoverageLevel.NONE

    def test_missing_cash_flow_nee_pattern(self):
        finding = evaluate((fact(K.TOTAL_DEBT, 93e9, "2025-12-31"),), "UTILITIES - REGULATED ELECTRIC")
        assert finding.missing_evidence == (Gap.MISSING_OPERATING_CASH_FLOW,)

    def test_no_facts_at_all(self):
        finding = evaluate(())
        assert finding.missing_evidence == (Gap.MISSING_DEBT, Gap.MISSING_OPERATING_CASH_FLOW)
        assert finding.confidence is EvidenceCoverageLevel.NOT_APPLICABLE

    def test_insufficient_is_never_moderate(self):
        assert evaluate(()).status is not RiskStatus.MODERATE


class TestTraceability:
    def test_supporting_facts_are_the_three_facts_the_latest_ratio_used(self):
        facts = period_facts("2025-12-31", 17.043, 1.318, 2.752)
        finding = evaluate(facts)
        assert set(finding.supporting_facts) == {f.id for f in facts}
        latest = finding.financial_risk_basis.latest
        assert set(latest.fact_ids) == {f.id for f in facts}
        assert latest.source_record_ids == tuple(sorted({f.source_record_id for f in facts}))

    def test_measure_is_named(self):
        assert company("VST").financial_risk_basis.measure is FinancialRiskMeasure.GROSS_DEBT_TO_OPERATING_CASH_FLOW

    def test_category_and_id(self):
        finding = company("VST")
        assert (finding.category, finding.id) == (RiskCategory.FINANCIAL_RISK, "risk_finding:financial_risk")

    def test_deterministic_regardless_of_fact_order(self):
        industry, rows = COMPANIES["VST"]
        facts = tuple(f for row in rows for f in period_facts(*row))
        a = evaluate(facts, industry)
        b = evaluate(tuple(reversed(facts)), industry)
        assert a == b

    def test_never_invents_a_leverage_ratio(self):
        source = inspect.getsource(financial_risk)
        for forbidden in ("debt_to_equity", "debt_to_ebitda", "leverage_ratio", "net_debt", "interest_coverage"):
            assert forbidden not in source

    def test_no_clock_is_read(self):
        source = inspect.getsource(financial_risk)
        assert "datetime.now" not in source and "utcnow" not in source and "date.today" not in source
