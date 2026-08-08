"""Tests for `atlas.analysis_engine.growth.evaluate_growth` (ATLAS-023
Phase 5) -- the documented rule table, and Scenarios A-D from Phase 14."""
from __future__ import annotations

from atlas.analysis_engine.business_contracts import BusinessCategory, BusinessCategoryStatus, BusinessDataGapKind
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.growth import evaluate_growth
from atlas.analysis_engine.provenance import Provenance, SourceKind, UpdateTrigger
from atlas.decision_engine.contracts import EvidenceCoverageLevel
from tests.unit.analysis_engine.business_facts._fixtures import EVALUATED_AT

_COUNTER = iter(range(100000))


def fact(kind: BusinessFactKind, value: float, period: str) -> BusinessFact:
    i = next(_COUNTER)
    return BusinessFact(
        id=f"fact-{i}",
        company="ASML",
        kind=kind,
        value=value,
        unit="usd",
        period=period,
        source_record_id=f"record-{i}",
        provenance=Provenance(
            source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
            source_references=(),
            dependencies=(),
            update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
            consumers=(),
            computed_at=EVALUATED_AT,
        ),
        extracted_at=EVALUATED_AT,
    )


class TestScenarioA_StrongGrowth:
    def test_consistent_positive_growth_across_both_metrics_is_strong(self):
        facts = (
            fact(BusinessFactKind.REVENUE, 1000, "2022"),
            fact(BusinessFactKind.REVENUE, 1100, "2023"),
            fact(BusinessFactKind.REVENUE, 1250, "2024"),
            fact(BusinessFactKind.FREE_CASH_FLOW, 200, "2022"),
            fact(BusinessFactKind.FREE_CASH_FLOW, 240, "2023"),
            fact(BusinessFactKind.FREE_CASH_FLOW, 300, "2024"),
        )
        result = evaluate_growth(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.STRONG
        assert result.kind is BusinessCategory.GROWTH
        assert result.confidence is EvidenceCoverageLevel.FULL
        assert result.missing_evidence == ()


class TestScenarioB_MixedGrowth:
    def test_metrics_disagreeing_is_moderate(self):
        facts = (
            fact(BusinessFactKind.REVENUE, 1000, "2023"),
            fact(BusinessFactKind.REVENUE, 1100, "2024"),
            fact(BusinessFactKind.FREE_CASH_FLOW, 300, "2023"),
            fact(BusinessFactKind.FREE_CASH_FLOW, 250, "2024"),
        )
        result = evaluate_growth(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.MODERATE

    def test_single_metric_consistently_positive_caps_at_moderate(self):
        """Confirmed design decision: STRONG requires both metrics."""
        facts = (
            fact(BusinessFactKind.REVENUE, 1000, "2022"),
            fact(BusinessFactKind.REVENUE, 1100, "2023"),
            fact(BusinessFactKind.REVENUE, 1250, "2024"),
        )
        result = evaluate_growth(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.MODERATE
        assert result.confidence is EvidenceCoverageLevel.PARTIAL


class TestScenarioC_Contraction:
    def test_all_supported_metrics_deteriorating_is_weak(self):
        facts = (
            fact(BusinessFactKind.REVENUE, 1000, "2022"),
            fact(BusinessFactKind.REVENUE, 900, "2023"),
            fact(BusinessFactKind.REVENUE, 800, "2024"),
            fact(BusinessFactKind.FREE_CASH_FLOW, 200, "2022"),
            fact(BusinessFactKind.FREE_CASH_FLOW, 150, "2023"),
            fact(BusinessFactKind.FREE_CASH_FLOW, 100, "2024"),
        )
        result = evaluate_growth(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.WEAK

    def test_single_supported_metric_deteriorating_is_also_weak(self):
        facts = (
            fact(BusinessFactKind.REVENUE, 1000, "2023"),
            fact(BusinessFactKind.REVENUE, 900, "2024"),
        )
        result = evaluate_growth(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.WEAK


class TestScenarioD_InsufficientHistory:
    def test_a_single_period_is_insufficient(self):
        facts = (fact(BusinessFactKind.REVENUE, 1000, "2024"),)
        result = evaluate_growth(facts, evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.INSUFFICIENT_INPUT
        assert BusinessDataGapKind.INSUFFICIENT_HISTORICAL_PERIODS in result.missing_evidence
        assert BusinessDataGapKind.MISSING_REVENUE_HISTORY in result.missing_evidence
        assert BusinessDataGapKind.MISSING_CASH_FLOW_HISTORY in result.missing_evidence

    def test_zero_facts_is_insufficient(self):
        result = evaluate_growth((), evaluated_at=EVALUATED_AT)
        assert result.status is BusinessCategoryStatus.INSUFFICIENT_INPUT
        assert result.confidence is EvidenceCoverageLevel.NOT_APPLICABLE

    def test_one_period_with_some_facts_is_not_applicable_vs_none(self):
        """Confidence distinguishes 'nothing at all' from 'something,
        but not enough' -- both extraction-level realities, not the
        same fact."""
        zero = evaluate_growth((), evaluated_at=EVALUATED_AT)
        one_period = evaluate_growth((fact(BusinessFactKind.REVENUE, 1000, "2024"),), evaluated_at=EVALUATED_AT)
        assert zero.confidence is EvidenceCoverageLevel.NOT_APPLICABLE
        assert one_period.confidence is EvidenceCoverageLevel.NONE


class TestNoFabrication:
    def test_flat_deltas_never_produce_strong(self):
        facts = (
            fact(BusinessFactKind.REVENUE, 1000, "2023"),
            fact(BusinessFactKind.REVENUE, 1000, "2024"),
            fact(BusinessFactKind.FREE_CASH_FLOW, 500, "2023"),
            fact(BusinessFactKind.FREE_CASH_FLOW, 500, "2024"),
        )
        result = evaluate_growth(facts, evaluated_at=EVALUATED_AT)
        assert result.status is not BusinessCategoryStatus.STRONG

    def test_no_numeric_score_anywhere(self):
        result = evaluate_growth((), evaluated_at=EVALUATED_AT)
        assert not hasattr(result, "score")
        assert isinstance(result.status.value, str)


class TestEvidenceTraceability:
    def test_supporting_evidence_names_the_facts_that_drove_a_positive_delta(self):
        r1 = fact(BusinessFactKind.REVENUE, 1000, "2023")
        r2 = fact(BusinessFactKind.REVENUE, 1100, "2024")
        result = evaluate_growth((r1, r2), evaluated_at=EVALUATED_AT)
        assert set(result.supporting_evidence) == {r1.id, r2.id}

    def test_contradicting_evidence_names_the_facts_that_drove_a_negative_delta(self):
        r1 = fact(BusinessFactKind.REVENUE, 1000, "2023")
        r2 = fact(BusinessFactKind.REVENUE, 900, "2024")
        result = evaluate_growth((r1, r2), evaluated_at=EVALUATED_AT)
        assert set(result.contradicting_evidence) == {r1.id, r2.id}


class TestDeterminism:
    def test_identical_facts_produce_a_deeply_equal_finding(self):
        facts = (
            fact(BusinessFactKind.REVENUE, 1000, "2023"),
            fact(BusinessFactKind.REVENUE, 1100, "2024"),
        )
        first = evaluate_growth(facts, evaluated_at=EVALUATED_AT)
        second = evaluate_growth(facts, evaluated_at=EVALUATED_AT)
        assert first == second

    def test_fact_order_does_not_affect_the_result(self):
        f1 = fact(BusinessFactKind.REVENUE, 1000, "2022")
        f2 = fact(BusinessFactKind.REVENUE, 1100, "2023")
        f3 = fact(BusinessFactKind.REVENUE, 1250, "2024")
        forward = evaluate_growth((f1, f2, f3), evaluated_at=EVALUATED_AT)
        shuffled = evaluate_growth((f3, f1, f2), evaluated_at=EVALUATED_AT)
        assert forward.status == shuffled.status
