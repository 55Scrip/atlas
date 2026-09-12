"""Financial Risk basis disclosure: the evaluator retains why it reached its
level -- which signals, which branch of each rule, which reported figures --
without the level itself changing.

The VST shapes below are its real facts (total debt 14.402/16.298/17.043
billion USD at the 2023-2025 year ends, latest free cash flow 1.318 billion,
Capital Allocation MODERATE). Fixture data, not rules: nothing in the
evaluator knows a ticker.
"""
from __future__ import annotations

import dataclasses
import inspect
import itertools

import pytest

from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.risk import contracts as risk_contracts
from atlas.analysis_engine.risk import financial_risk
from atlas.analysis_engine.risk.contracts import (
    FinancialRiskCondition,
    FinancialRiskMetric,
    FinancialRiskRule,
    FinancialRiskSignal,
    RiskDataGapKind,
    RiskStatus,
)
from atlas.analysis_engine.risk.financial_risk import evaluate_financial_risk
from atlas.analysis_engine.risk.models import FinancialRiskBasis, FinancialRiskSignalBasis
from tests.unit.analysis_engine.risk._fixtures import EVALUATED_AT, business_fact, capital_allocation_finding

CA, CASH, DEBT = FinancialRiskSignal.CAPITAL_ALLOCATION, FinancialRiskSignal.CASH_GENERATION, FinancialRiskSignal.DEBT_TREND
S = BusinessCategoryStatus


def debt(*values: float, start: int = 2023):
    return tuple(business_fact(BusinessFactKind.TOTAL_DEBT, v, f"{start + i}-12-31") for i, v in enumerate(values))


def fcf(*values: float, start: int = 2025):
    return tuple(business_fact(BusinessFactKind.FREE_CASH_FLOW, v, f"{start - len(values) + 1 + i}-12-31")
                 for i, v in enumerate(values))


def evaluate(ca_status: BusinessCategoryStatus, facts: tuple):
    return evaluate_financial_risk(capital_allocation_finding(ca_status), facts, evaluated_at=EVALUATED_AT)


def vst_facts():
    return debt(14.402e9, 16.298e9, 17.043e9) + fcf(-0.816e9, 3.777e9, 2.485e9, 1.318e9)


def vst():
    return evaluate(S.MODERATE, vst_facts())


class TestVst:
    def test_high_because_total_debt_increased_between_every_evaluated_period(self):
        finding = vst()
        basis = finding.financial_risk_basis
        assert finding.status is basis.level is RiskStatus.HIGH
        assert basis.rule is FinancialRiskRule.ANY_SIGNAL_HIGH
        assert basis.determining == (DEBT,)
        debt_basis = basis.signal(DEBT)
        assert debt_basis.condition is FinancialRiskCondition.TOTAL_DEBT_INCREASED_EVERY_PERIOD
        assert [(o.period, o.value) for o in debt_basis.observations] == [
            ("2023-12-31", 14.402e9), ("2024-12-31", 16.298e9), ("2025-12-31", 17.043e9)]

    def test_every_observation_names_metric_unit_fact_and_source_record(self):
        facts = vst_facts()
        by_id = {f.id: f for f in facts}
        for observation in evaluate(S.MODERATE, facts).financial_risk_basis.signal(DEBT).observations:
            fact = by_id[observation.fact_id]
            assert observation.metric is FinancialRiskMetric.TOTAL_DEBT
            assert (observation.value, observation.unit, observation.period) == (fact.value, fact.unit, fact.period)
            assert observation.source_record_id == fact.source_record_id

    def test_positive_free_cash_flow_and_moderate_capital_allocation_are_retained_but_are_not_causes(self):
        basis = vst().financial_risk_basis
        assert basis.signal(CASH).level is RiskStatus.LOW
        assert basis.signal(CASH).condition is FinancialRiskCondition.LATEST_FREE_CASH_FLOW_NOT_NEGATIVE
        assert [o.value for o in basis.signal(CASH).observations] == [1.318e9]
        assert basis.signal(CA).level is RiskStatus.MODERATE
        assert CASH not in basis.determining and CA not in basis.determining

    def test_supporting_facts_and_missing_evidence_are_exactly_as_before(self):
        facts = vst_facts()
        finding = evaluate(S.MODERATE, facts)
        debt_ids = {f.id for f in facts if f.kind is BusinessFactKind.TOTAL_DEBT}
        latest_fcf = max((f for f in facts if f.kind is BusinessFactKind.FREE_CASH_FLOW), key=lambda f: f.period)
        assert set(finding.supporting_facts) == {"business_finding:capital_allocation", latest_fcf.id, *debt_ids}
        assert finding.missing_evidence == ()


class TestTheRuleIsUnchanged:
    """The level is the documented table, first match wins -- restated here
    independently and checked over every signal combination."""

    @staticmethod
    def _documented(ca_status, fcf_values, debt_values):
        ca = {S.WEAK: "high", S.MODERATE: "moderate", S.STRONG: "low"}.get(ca_status, "insufficient")
        cash = "insufficient" if not fcf_values else ("high" if fcf_values[-1] < 0 else "low")
        pairs = list(zip(debt_values, debt_values[1:]))
        rising = bool(pairs) and all(b > a for a, b in pairs)
        if "high" in (ca, cash) or rising:
            return RiskStatus.HIGH
        if ca == cash == "insufficient":
            return RiskStatus.INSUFFICIENT_INPUT
        if ca == cash == "low":
            return RiskStatus.LOW
        return RiskStatus.MODERATE

    @pytest.mark.parametrize("ca_status,fcf_values,debt_values", list(itertools.product(
        [S.WEAK, S.MODERATE, S.STRONG, S.INSUFFICIENT_INPUT],
        [(), (-5.0,), (0.0,), (5.0,), (-5.0, 5.0), (5.0, -5.0)],
        [(), (10.0,), (10.0, 11.0), (10.0, 11.0, 12.0), (12.0, 11.0, 10.0), (10.0, 12.0, 11.0), (10.0, 10.0, 11.0)],
    )))
    def test_level_equals_the_documented_table_and_the_basis_agrees(self, ca_status, fcf_values, debt_values):
        finding = evaluate(ca_status, fcf(*fcf_values) + debt(*debt_values))
        assert finding.status is self._documented(ca_status, fcf_values, debt_values)
        assert finding.financial_risk_basis.level is finding.status

    def test_disclosure_is_deterministic(self):
        facts = vst_facts()
        results = {evaluate(S.MODERATE, facts).financial_risk_basis for _ in range(5)}
        assert len(results) == 1


class TestSignalsAreRetainedSeparately:
    def test_three_high_signals_are_all_named_in_rule_order_none_netted(self):
        basis = evaluate(S.WEAK, fcf(-1.0) + debt(1.0, 2.0)).financial_risk_basis
        assert basis.determining == (CA, CASH, DEBT)

    def test_two_high_signals_without_debt_name_exactly_those_two(self):
        basis = evaluate(S.WEAK, fcf(-4.949e9) + debt(38.1e9, 49.3e9, 46.6e9)).financial_risk_basis
        assert basis.determining == (CA, CASH)
        assert basis.signal(DEBT).condition is FinancialRiskCondition.TOTAL_DEBT_NO_CONSISTENT_DIRECTION

    def test_negative_latest_free_cash_flow_alone_names_its_period_and_value(self):
        basis = evaluate(S.MODERATE, fcf(4.96e9, -14.9e9, -15.3e9, -47.218e9)).financial_risk_basis
        assert basis.determining == (CASH,)
        assert [(o.period, o.value) for o in basis.signal(CASH).observations] == [("2025-12-31", -47.218e9)]


class TestNonFiringAndMissing:
    def test_a_mixed_debt_history_is_kept_as_evaluated_but_supports_nothing(self):
        facts = fcf(5.0) + debt(10.0, 12.0, 11.0)
        finding = evaluate(S.STRONG, facts)
        debt_basis = finding.financial_risk_basis.signal(DEBT)
        assert debt_basis.condition is FinancialRiskCondition.TOTAL_DEBT_NO_CONSISTENT_DIRECTION
        assert len(debt_basis.observations) == 3
        assert not {o.fact_id for o in debt_basis.observations} & set(finding.supporting_facts)
        assert RiskDataGapKind.MISSING_DEBT_HISTORY in finding.missing_evidence  # unchanged gap reporting

    def test_flat_debt_between_two_periods_is_not_an_increase(self):
        basis = evaluate(S.STRONG, fcf(5.0) + debt(10.0, 10.0, 11.0)).financial_risk_basis
        assert basis.signal(DEBT).condition is FinancialRiskCondition.TOTAL_DEBT_NO_CONSISTENT_DIRECTION
        assert basis.level is RiskStatus.LOW

    @pytest.mark.parametrize("values", [(), (10.0,)])
    def test_fewer_than_two_debt_periods_is_named_as_such(self, values):
        basis = evaluate(S.STRONG, fcf(5.0) + debt(*values)).financial_risk_basis
        assert basis.signal(DEBT).condition is FinancialRiskCondition.TOTAL_DEBT_FEWER_THAN_TWO_PERIODS
        assert len(basis.signal(DEBT).observations) == len(values)

    def test_falling_debt_is_low_and_never_a_cause_of_a_high_level(self):
        basis = evaluate(S.WEAK, fcf(5.0) + debt(12.0, 11.0, 10.0)).financial_risk_basis
        assert basis.signal(DEBT).condition is FinancialRiskCondition.TOTAL_DEBT_DECREASED_EVERY_PERIOD
        assert basis.determining == (CA,)

    def test_no_evidence_is_insufficient_with_nothing_fabricated(self):
        basis = evaluate(S.INSUFFICIENT_INPUT, ()).financial_risk_basis
        assert basis.level is RiskStatus.INSUFFICIENT_INPUT
        assert basis.rule is FinancialRiskRule.NO_CORE_SIGNAL_ASSESSED
        assert all(not s.observations for s in basis.signals)

    def test_low_rests_on_both_core_signals(self):
        basis = evaluate(S.STRONG, fcf(5.0)).financial_risk_basis
        assert (basis.level, basis.rule, basis.determining) == (
            RiskStatus.LOW, FinancialRiskRule.CORE_SIGNALS_BOTH_LOW, (CA, CASH))

    @pytest.mark.parametrize("ca_status,facts,determining", [
        (S.MODERATE, fcf(5.0), (CA,)),
        (S.STRONG, (), (CASH,)),
        (S.MODERATE, (), (CA, CASH)),
    ])
    def test_moderate_names_the_core_signals_that_kept_it_from_low(self, ca_status, facts, determining):
        basis = evaluate(ca_status, facts).financial_risk_basis
        assert (basis.level, basis.rule, basis.determining) == (
            RiskStatus.MODERATE, FinancialRiskRule.CORE_SIGNAL_NOT_LOW, determining)

    def test_the_basis_reports_the_observation_the_rule_read_whatever_its_period(self):
        """Disclosure, not correction: the cash signal reads the latest
        period Atlas holds, and the basis shows which one that was."""
        basis = evaluate(S.STRONG, fcf(-1.0, 3.0, 300.0, start=2027)).financial_risk_basis
        assert [o.period for o in basis.signal(CASH).observations] == ["2027-12-31"]


class TestABasisCannotDescribeMoreThanItsEvidence:
    """Adversarial constructions: each is a way a basis could overclaim or
    contradict its own level, and each is rejected."""

    def _debt_basis(self, values, condition, level):
        observations = vst().financial_risk_basis.signal(DEBT).observations
        observations = tuple(dataclasses.replace(o, value=v) for o, v in zip(observations, values))
        return FinancialRiskSignalBasis(signal=DEBT, level=level, condition=condition, observations=observations)

    def test_increased_every_period_over_a_figure_that_fell(self):
        with pytest.raises(AnalysisEngineContractError):
            self._debt_basis((14.4e9, 16.3e9, 16.0e9), FinancialRiskCondition.TOTAL_DEBT_INCREASED_EVERY_PERIOD,
                             RiskStatus.HIGH)

    def test_increased_every_period_over_a_single_figure(self):
        with pytest.raises(AnalysisEngineContractError):
            self._debt_basis((14.4e9,), FinancialRiskCondition.TOTAL_DEBT_INCREASED_EVERY_PERIOD, RiskStatus.HIGH)

    def test_observations_out_of_period_order(self):
        observations = tuple(reversed(vst().financial_risk_basis.signal(DEBT).observations))
        with pytest.raises(AnalysisEngineContractError):
            FinancialRiskSignalBasis(signal=DEBT, level=RiskStatus.LOW,
                                     condition=FinancialRiskCondition.TOTAL_DEBT_DECREASED_EVERY_PERIOD,
                                     observations=observations)

    def test_a_condition_paired_with_the_wrong_level(self):
        with pytest.raises(AnalysisEngineContractError):
            self._debt_basis((1.0, 2.0, 3.0), FinancialRiskCondition.TOTAL_DEBT_INCREASED_EVERY_PERIOD,
                             RiskStatus.MODERATE)

    def test_positive_free_cash_flow_described_as_negative(self):
        observation = vst().financial_risk_basis.signal(CASH).observations
        with pytest.raises(AnalysisEngineContractError):
            FinancialRiskSignalBasis(signal=CASH, level=RiskStatus.HIGH,
                                     condition=FinancialRiskCondition.LATEST_FREE_CASH_FLOW_NEGATIVE,
                                     observations=observation)

    def test_a_debt_figure_carried_by_the_cash_signal(self):
        observations = vst().financial_risk_basis.signal(DEBT).observations[-1:]
        with pytest.raises(AnalysisEngineContractError):
            FinancialRiskSignalBasis(signal=CASH, level=RiskStatus.LOW,
                                     condition=FinancialRiskCondition.LATEST_FREE_CASH_FLOW_NOT_NEGATIVE,
                                     observations=observations)

    def test_a_non_firing_signal_named_as_a_cause_of_high(self):
        basis = vst().financial_risk_basis
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(basis, determining=(CASH, DEBT))

    def test_a_firing_signal_left_out_of_high(self):
        basis = evaluate(S.WEAK, fcf(-1.0) + debt(1.0, 2.0)).financial_risk_basis
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(basis, determining=(DEBT,))

    def test_high_restated_as_moderate(self):
        basis = vst().financial_risk_basis
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(basis, level=RiskStatus.MODERATE, rule=FinancialRiskRule.CORE_SIGNAL_NOT_LOW,
                                determining=(CA,))

    def test_a_high_finding_resting_on_a_moderate_basis(self):
        finding = vst()
        low_basis = evaluate(S.MODERATE, fcf(5.0)).financial_risk_basis
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(finding, financial_risk_basis=low_basis)

    def test_a_basis_on_a_category_that_is_not_financial_risk(self):
        with pytest.raises(AnalysisEngineContractError):
            dataclasses.replace(vst(), category=RiskCategory.VALUATION_RISK)

    def test_a_signal_missing_from_the_basis(self):
        basis = vst().financial_risk_basis
        with pytest.raises(AnalysisEngineContractError):
            FinancialRiskBasis(level=basis.level, rule=basis.rule, signals=basis.signals[:2], determining=())


class TestNothingBeyondTheRule:
    def test_the_vocabulary_names_no_ratio_rating_coverage_liquidity_or_forecast(self):
        words = {
            word
            for enum in (FinancialRiskSignal, FinancialRiskMetric, FinancialRiskCondition, FinancialRiskRule)
            for member in enum
            for word in member.value.split("_")
        }
        for forbidden in ("ratio", "leverage", "rating", "coverage", "liquidity", "ebitda", "net",
                          "forecast", "expected", "default", "credit"):
            assert forbidden not in words

    def test_the_evaluator_still_never_computes_a_ratio(self):
        source = inspect.getsource(financial_risk) + inspect.getsource(risk_contracts)
        for forbidden in ("debt_to_equity", "debt_to_ebitda", "leverage_ratio", "net_debt", "interest_coverage"):
            assert forbidden not in source

    def test_the_basis_carries_no_prose(self):
        """Closed tokens and the facts' own identifiers and figures only --
        wording is the frontend's, so it can change without rewriting
        what was decided."""
        basis = vst().financial_risk_basis
        for signal in basis.signals:
            assert isinstance(signal.condition, FinancialRiskCondition)
            for field in dataclasses.fields(signal):
                value = getattr(signal, field.name)
                assert not (isinstance(value, str) and " " in value)
