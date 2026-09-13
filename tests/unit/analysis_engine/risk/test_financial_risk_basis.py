"""Financial Risk v2 basis: the evaluator's retained evidence cannot describe
more than it shows. Each construction below is a way a basis could overclaim
or contradict its own level, and each is rejected at construction.
"""
from __future__ import annotations

import dataclasses

import pytest

from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.risk.contracts import (
    FinancialRiskCondition as C,
    FinancialRiskMeasure,
    RiskDataGapKind as Gap,
    RiskStatus,
    severity_for_risk_status,
)
from atlas.analysis_engine.risk.models import DebtBurdenBands, DebtBurdenObservation, FinancialRiskBasis
from atlas.analysis_engine.findings import FindingSeverity
from tests.unit.analysis_engine.risk.test_financial_risk import company, evaluate, period_facts

BANDS = DebtBurdenBands(low_below=1.25, high_from=3.0)


def obs(period, debt, fcf, capex):
    return DebtBurdenObservation(
        period=period, unit="USD", total_debt=debt, free_cash_flow=fcf, capital_expenditure=capex,
        total_debt_fact_id=f"d-{period}", free_cash_flow_fact_id=f"f-{period}", capital_expenditure_fact_id=f"c-{period}",
        source_record_ids=(f"r-{period}",))


def vst():
    return company("VST").financial_risk_basis


class TestTheBasisIsTheDecision:
    def test_the_finding_level_is_the_basis_level(self):
        for ticker in ("VST", "META", "MCO"):
            finding = company(ticker)
            assert finding.status is finding.financial_risk_basis.level

    def test_high_restated_as_moderate_is_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(vst(), level=RiskStatus.MODERATE, condition=C.DEBT_BURDEN_MODERATE)

    def test_a_high_finding_on_a_low_basis_is_rejected(self):
        finding = company("VST")
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(finding, financial_risk_basis=company("META").financial_risk_basis)

    def test_a_basis_on_another_category_is_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(company("VST"), category=RiskCategory.VALUATION_RISK)


class TestConditionsMustDescribeTheirFigures:
    def test_high_burden_over_a_ratio_below_the_band(self):
        latest = obs("2025-12-31", 2.0, 1.0, 0.0)
        with pytest.raises(AnalysisEngineContractError):
            FinancialRiskBasis(level=RiskStatus.HIGH, condition=C.DEBT_BURDEN_HIGH, bands=BANDS,
                               measure=FinancialRiskMeasure.GROSS_DEBT_TO_OPERATING_CASH_FLOW,
                               latest=latest, history=(latest,))

    def test_altering_one_figure_so_the_ratio_leaves_the_band(self):
        basis = vst()
        altered = dataclasses.replace(basis.latest, total_debt=basis.latest.total_debt / 2)
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(basis, latest=altered, history=basis.history[:-1] + (altered,))

    def test_negative_cash_flow_condition_over_positive_operating_cash_flow(self):
        latest = obs("2025-12-31", 2.0, 1.0, 0.0)
        with pytest.raises(AnalysisEngineContractError):
            FinancialRiskBasis(level=RiskStatus.HIGH, condition=C.OPERATING_CASH_FLOW_NEGATIVE, bands=BANDS,
                               measure=FinancialRiskMeasure.GROSS_DEBT_TO_OPERATING_CASH_FLOW,
                               latest=latest, history=(latest,))

    def test_a_burden_band_over_zero_operating_cash_flow(self):
        latest = obs("2025-12-31", 2.0, -1.0, 1.0)
        with pytest.raises(AnalysisEngineContractError):
            FinancialRiskBasis(level=RiskStatus.HIGH, condition=C.DEBT_BURDEN_HIGH, bands=BANDS,
                               measure=FinancialRiskMeasure.GROSS_DEBT_TO_OPERATING_CASH_FLOW,
                               latest=latest, history=(latest,))


class TestShape:
    def test_a_level_needs_its_observation_and_the_history_ends_with_it(self):
        basis = vst()
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(basis, latest=None)
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(basis, history=basis.history[:-1])

    def test_history_is_ordered_and_bounded(self):
        basis = vst()
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(basis, history=tuple(reversed(basis.history)))
        four = (obs("2022-12-31", 1.0, 1.0, 0.0), *basis.history)
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(basis, history=four)

    def test_not_applicable_carries_no_figures_and_no_gaps(self):
        with pytest.raises(AnalysisEngineContractError):
            FinancialRiskBasis(level=RiskStatus.NOT_APPLICABLE, condition=C.MEASURE_NOT_APPLICABLE, bands=BANDS,
                               latest=vst().latest, history=(vst().latest,),
                               measure=FinancialRiskMeasure.GROSS_DEBT_TO_OPERATING_CASH_FLOW)
        with pytest.raises(AnalysisEngineContractError):
            FinancialRiskBasis(level=RiskStatus.NOT_APPLICABLE, condition=C.MEASURE_NOT_APPLICABLE, bands=BANDS,
                               gaps=(Gap.MISSING_DEBT,))

    def test_insufficient_must_say_why_and_shows_no_stale_figures(self):
        with pytest.raises(AnalysisEngineContractError):
            FinancialRiskBasis(level=RiskStatus.INSUFFICIENT_INPUT, condition=C.NO_ELIGIBLE_EVIDENCE, bands=BANDS)
        stale = obs("2013-12-31", 93.6, 22.0, 16.6)
        with pytest.raises(AnalysisEngineContractError):
            FinancialRiskBasis(level=RiskStatus.INSUFFICIENT_INPUT, condition=C.NO_ELIGIBLE_EVIDENCE, bands=BANDS,
                               gaps=(Gap.STALE_FINANCIAL_STATEMENTS,), history=(stale,))

    def test_an_observation_names_three_distinct_facts_and_a_source(self):
        latest = vst().latest
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(latest, source_record_ids=())
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(latest, capital_expenditure_fact_id=latest.total_debt_fact_id)

    def test_bands_must_be_ordered(self):
        with pytest.raises(AnalysisEngineContractError):
            DebtBurdenBands(low_below=3.0, high_from=1.25)


class TestDerivedOperatingCashFlow:
    def test_is_free_cash_flow_plus_capex_with_both_facts_retained(self):
        latest = vst().latest
        assert latest.operating_cash_flow == latest.free_cash_flow + latest.capital_expenditure
        assert latest.free_cash_flow_fact_id.endswith("free_cash_flow:2025-12-31")
        assert latest.capital_expenditure_fact_id.endswith("capital_expenditure:2025-12-31")

    def test_ratio_is_none_when_operating_cash_flow_is_not_positive(self):
        assert obs("2025-12-31", 1.0, -1.0, 1.0).ratio is None
        assert obs("2025-12-31", 1.0, -2.0, 1.0).ratio is None


class TestStatusVocabulary:
    def test_not_applicable_is_its_own_status(self):
        assert RiskStatus.NOT_APPLICABLE.value == "not_applicable"
        assert RiskStatus.NOT_APPLICABLE not in (RiskStatus.LOW, RiskStatus.INSUFFICIENT_INPUT)

    def test_not_applicable_is_informational_not_a_gap(self):
        assert severity_for_risk_status(RiskStatus.NOT_APPLICABLE) is FindingSeverity.INFO

    def test_the_condition_vocabulary_names_no_rating_coverage_liquidity_or_forecast(self):
        words = {w for member in C for w in member.value.split("_")}
        for forbidden in ("rating", "coverage", "liquidity", "interest", "maturity", "default", "credit",
                          "forecast", "ebitda", "leverage"):
            assert forbidden not in words

    def test_the_same_facts_give_the_same_basis(self):
        facts = period_facts("2025-12-31", 3.0, 1.0, 0.5)
        assert evaluate(facts).financial_risk_basis == evaluate(facts).financial_risk_basis
