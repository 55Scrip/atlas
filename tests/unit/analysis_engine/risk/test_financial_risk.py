"""Tests for `atlas.analysis_engine.risk.financial_risk.evaluate_financial_risk`
(ATLAS-025 Phase 6) -- the documented two-signal rule table and
Scenarios A-D from Phase 21."""
from __future__ import annotations

from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.risk.contracts import RiskDataGapKind, RiskStatus
from atlas.analysis_engine.risk.financial_risk import evaluate_financial_risk
from atlas.decision_engine.contracts import EvidenceCoverageLevel
from tests.unit.analysis_engine.risk._fixtures import EVALUATED_AT, business_fact, capital_allocation_finding


class TestScenarioA_HealthyIsLow:
    def test_strong_capital_allocation_and_positive_fcf_is_low(self):
        finding = capital_allocation_finding(BusinessCategoryStatus.STRONG)
        facts = (business_fact(BusinessFactKind.FREE_CASH_FLOW, 200.0, "2024"),)
        result = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.LOW


class TestScenarioB_AdverseSignalIsHigh:
    def test_negative_fcf_alone_is_high_even_with_strong_capital_allocation(self):
        """Either adverse signal is disqualifying -- never offset by the
        other side being positive."""
        finding = capital_allocation_finding(BusinessCategoryStatus.STRONG)
        facts = (business_fact(BusinessFactKind.FREE_CASH_FLOW, -50.0, "2024"),)
        result = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.HIGH

    def test_weak_capital_allocation_alone_is_high_even_with_positive_fcf(self):
        finding = capital_allocation_finding(BusinessCategoryStatus.WEAK)
        facts = (business_fact(BusinessFactKind.FREE_CASH_FLOW, 200.0, "2024"),)
        result = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.HIGH

    def test_both_signals_adverse_is_still_just_high_never_a_worse_tier(self):
        finding = capital_allocation_finding(BusinessCategoryStatus.WEAK)
        facts = (business_fact(BusinessFactKind.FREE_CASH_FLOW, -50.0, "2024"),)
        result = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.HIGH


class TestScenarioC_MixedIsModerate:
    def test_moderate_capital_allocation_with_positive_fcf_is_moderate(self):
        finding = capital_allocation_finding(BusinessCategoryStatus.MODERATE)
        facts = (business_fact(BusinessFactKind.FREE_CASH_FLOW, 200.0, "2024"),)
        result = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.MODERATE

    def test_strong_capital_allocation_with_no_fcf_fact_is_moderate_not_low(self):
        """One signal computable and LOW, the other insufficient -> MODERATE,
        never a silent promotion to LOW."""
        finding = capital_allocation_finding(BusinessCategoryStatus.STRONG)
        result = evaluate_financial_risk(finding, (), evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.MODERATE
        assert RiskDataGapKind.MISSING_CASH_FLOW_LEVEL in result.missing_evidence


class TestScenarioD_MissingHistoryIsInsufficientInput:
    def test_both_signals_insufficient_is_insufficient_input(self):
        finding = capital_allocation_finding(
            BusinessCategoryStatus.INSUFFICIENT_INPUT, confidence=EvidenceCoverageLevel.NOT_APPLICABLE
        )
        result = evaluate_financial_risk(finding, (), evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.INSUFFICIENT_INPUT
        assert RiskDataGapKind.CAPITAL_ALLOCATION_ASSESSMENT_UNAVAILABLE in result.missing_evidence
        assert RiskDataGapKind.MISSING_CASH_FLOW_LEVEL in result.missing_evidence

    def test_never_silently_treats_missing_fcf_as_zero(self):
        """Absence of a FREE_CASH_FLOW fact must never be interpreted as
        a zero (non-negative, LOW-risk) value."""
        finding = capital_allocation_finding(BusinessCategoryStatus.INSUFFICIENT_INPUT)
        result = evaluate_financial_risk(finding, (), evaluated_at=EVALUATED_AT)
        assert result.status is not RiskStatus.LOW


class TestEdgeCases:
    def test_zero_fcf_is_treated_as_non_negative_low(self):
        finding = capital_allocation_finding(BusinessCategoryStatus.STRONG)
        facts = (business_fact(BusinessFactKind.FREE_CASH_FLOW, 0.0, "2024"),)
        result = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.LOW

    def test_most_recent_period_wins_when_multiple_fcf_facts_exist(self):
        finding = capital_allocation_finding(BusinessCategoryStatus.STRONG)
        facts = (
            business_fact(BusinessFactKind.FREE_CASH_FLOW, -100.0, "2022"),
            business_fact(BusinessFactKind.FREE_CASH_FLOW, 200.0, "2024"),
            business_fact(BusinessFactKind.FREE_CASH_FLOW, 150.0, "2023"),
        )
        result = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.LOW

    def test_never_invents_a_leverage_ratio(self):
        """Company Data Foundation v1: `TOTAL_DEBT` is now a real,
        legitimate signal input (`debt_trend_signal`, a pure
        sign-of-consecutive-deltas comparison -- see module docstring)
        -- so referencing the fact kind itself is no longer forbidden.
        What remains forbidden is any actual *ratio* -- debt divided by
        equity, EBITDA, or any other invented denominator."""
        import inspect

        from atlas.analysis_engine.risk import financial_risk

        source = inspect.getsource(financial_risk)
        for forbidden in ("debt_to_equity", "debt_to_ebitda", "leverage_ratio"):
            assert forbidden not in source


class TestTraceability:
    def test_category_and_id_are_correct(self):
        finding = capital_allocation_finding(BusinessCategoryStatus.STRONG)
        facts = (business_fact(BusinessFactKind.FREE_CASH_FLOW, 200.0, "2024"),)
        result = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        assert result.category is RiskCategory.FINANCIAL_RISK
        assert result.id == "risk_finding:financial_risk"

    def test_capital_allocation_finding_id_is_always_a_dependency(self):
        finding = capital_allocation_finding(BusinessCategoryStatus.STRONG)
        facts = (business_fact(BusinessFactKind.FREE_CASH_FLOW, 200.0, "2024"),)
        result = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        assert finding.id in result.provenance.dependencies


class TestDeterminism:
    def test_identical_input_produces_a_deeply_equal_finding(self):
        finding = capital_allocation_finding(BusinessCategoryStatus.MODERATE)
        facts = (business_fact(BusinessFactKind.FREE_CASH_FLOW, 200.0, "2024"),)
        first = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        second = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        assert first == second


class TestDebtTrendSignal:
    """Company Data Foundation v1: an escalation-only third signal --
    can turn a result `HIGH`, and its own fact ids are always included
    when it fires, but it never changes `confidence` (still computed
    from exactly the original two signals) and never blocks a `LOW`
    result from the other two."""

    def test_consistently_rising_debt_escalates_to_high_even_with_no_other_signal(self):
        finding = capital_allocation_finding(BusinessCategoryStatus.INSUFFICIENT_INPUT, confidence=EvidenceCoverageLevel.NOT_APPLICABLE)
        facts = (
            business_fact(BusinessFactKind.TOTAL_DEBT, 100.0, "2022"),
            business_fact(BusinessFactKind.TOTAL_DEBT, 200.0, "2023"),
            business_fact(BusinessFactKind.TOTAL_DEBT, 300.0, "2024"),
        )
        result = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.HIGH
        # Escalation only -- confidence stays exactly what the original
        # two (both-insufficient) signals alone would produce.
        assert result.confidence is EvidenceCoverageLevel.NOT_APPLICABLE

    def test_consistently_falling_debt_alone_does_not_unlock_low(self):
        """A falling debt trend is real, positive information, but it
        is not one of the two signals `confidence`/the `LOW` branch
        reads -- with both original signals insufficient, the result
        stays `INSUFFICIENT_INPUT`, never a fabricated `LOW`."""
        finding = capital_allocation_finding(BusinessCategoryStatus.INSUFFICIENT_INPUT, confidence=EvidenceCoverageLevel.NOT_APPLICABLE)
        facts = (
            business_fact(BusinessFactKind.TOTAL_DEBT, 300.0, "2022"),
            business_fact(BusinessFactKind.TOTAL_DEBT, 200.0, "2023"),
            business_fact(BusinessFactKind.TOTAL_DEBT, 100.0, "2024"),
        )
        result = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.INSUFFICIENT_INPUT

    def test_a_single_debt_period_is_insufficient_never_a_trend(self):
        finding = capital_allocation_finding(BusinessCategoryStatus.STRONG)
        facts = (
            business_fact(BusinessFactKind.FREE_CASH_FLOW, 200.0, "2024"),
            business_fact(BusinessFactKind.TOTAL_DEBT, 100.0, "2024"),
        )
        result = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.LOW  # unaffected -- debt trend stays insufficient
        assert RiskDataGapKind.MISSING_DEBT_HISTORY in result.missing_evidence

    def test_mixed_debt_trend_is_insufficient_not_moderate(self):
        finding = capital_allocation_finding(BusinessCategoryStatus.STRONG)
        facts = (
            business_fact(BusinessFactKind.FREE_CASH_FLOW, 200.0, "2024"),
            business_fact(BusinessFactKind.TOTAL_DEBT, 100.0, "2022"),
            business_fact(BusinessFactKind.TOTAL_DEBT, 200.0, "2023"),
            business_fact(BusinessFactKind.TOTAL_DEBT, 150.0, "2024"),
        )
        result = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.LOW  # the two real signals still win; debt trend contributes nothing
        assert RiskDataGapKind.MISSING_DEBT_HISTORY in result.missing_evidence

    def test_healthy_result_is_unaffected_when_debt_data_is_entirely_absent(self):
        """Backward-compatible: a company with no TOTAL_DEBT facts at
        all behaves identically to before this sprint."""
        finding = capital_allocation_finding(BusinessCategoryStatus.STRONG)
        facts = (business_fact(BusinessFactKind.FREE_CASH_FLOW, 200.0, "2024"),)
        result = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.LOW
        assert result.confidence is EvidenceCoverageLevel.FULL
        assert RiskDataGapKind.MISSING_DEBT_HISTORY in result.missing_evidence

    def test_rising_debt_fact_ids_are_included_in_supporting_facts_when_it_fires(self):
        finding = capital_allocation_finding(BusinessCategoryStatus.STRONG)
        facts = (
            business_fact(BusinessFactKind.FREE_CASH_FLOW, 200.0, "2024"),
            business_fact(BusinessFactKind.TOTAL_DEBT, 100.0, "2022"),
            business_fact(BusinessFactKind.TOTAL_DEBT, 200.0, "2023"),
            business_fact(BusinessFactKind.TOTAL_DEBT, 300.0, "2024"),
        )
        result = evaluate_financial_risk(finding, facts, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.HIGH
        debt_ids = {f.id for f in facts if f.kind is BusinessFactKind.TOTAL_DEBT}
        assert debt_ids.issubset(set(result.supporting_facts))
        assert debt_ids.issubset(set(result.provenance.dependencies))
