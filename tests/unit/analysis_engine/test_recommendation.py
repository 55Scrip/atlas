"""Tests for `atlas.analysis_engine.recommendation
.evaluate_recommendation_gate` (ATLAS-020 Phase 10; "Recommendation
Backend Step 3" wiring) -- confirms the RecommendationWithheld fallback
still delegates to `atlas.decision_engine.stages.recommendation
.determine_recommendation` (never reimplementing it), confirms the
Conviction gate (ATLAS-020's own addition), and confirms the gate now
also produces `ComputedDirectionalRecommendation` for real when
`direction_selector.select_direction` reaches a real direction.

Every call below that is not specifically exercising Direction Selection
passes `business_analysis`/`valuation_engine` built from empty facts
(`_insufficient_business_analysis`/`_insufficient_valuation_engine`) --
Growth and Capital Allocation both resolve to `INSUFFICIENT_INPUT` from
empty `business_records`, which `direction_selector.select_direction`
treats as "Business status unknown" and returns `None` for (see that
module's own docstring) -- so these calls exercise exactly the same
RecommendationWithheld-only behaviour this file tested before this
sprint, just reached via the new, real Direction Selector path rather
than a hardcoded gap. `TestDirectionSelectorNowWired` proves the other
branch is real."""
from __future__ import annotations

from atlas.analysis_engine.business import evaluate_business_analysis
from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel
from atlas.analysis_engine.recommendation import (
    RECOMMENDATION_GATE_MINIMUM_CONVICTION,
    ComputedDirectionalRecommendation,
    RecommendationDirection,
    evaluate_recommendation_gate,
)
from atlas.analysis_engine.recommendation_conviction import RecommendationConvictionLevel
from atlas.analysis_engine.valuation.facts import extract_valuation_facts_from_records
from atlas.analysis_engine.valuation.pipeline import evaluate_valuation
from atlas.decision_engine.contracts import (
    EvaluationState,
    HoldingLinkage,
    PortfolioHoldingContext,
    RecommendationOutcomeKind,
    RecommendationWithheldReason,
)
from atlas.decision_engine.stages.recommendation import determine_recommendation
from tests.unit.analysis_engine._fixtures import GENERATED_AT, run_minimal, run_populated


def _assessment(level: ConvictionLevel) -> ConvictionAssessment:
    return ConvictionAssessment(level=level, reasons=())


def _insufficient_business_analysis(output):
    """Growth/Capital Allocation both `INSUFFICIENT_INPUT` -- no
    `business_records` supplied, matching every real call site's default
    (see `pipeline.py`'s own module docstring)."""
    return evaluate_business_analysis(output.business_evaluation, business_records=(), evaluated_at=GENERATED_AT)


def _insufficient_valuation_engine():
    """`FCF_YIELD_RELATIVE` resolves `INSUFFICIENT_INPUT` -- no facts
    supplied, matching every real call site's default."""
    business_facts = extract_facts_from_records((), evaluated_at=GENERATED_AT)
    market_facts = extract_valuation_facts_from_records((), evaluated_at=GENERATED_AT)
    return evaluate_valuation(business_facts, market_facts, evaluated_at=GENERATED_AT)


def _call_gate(engine_input, output, *, conviction, **overrides):
    fields = dict(
        business_evaluation=output.business_evaluation,
        valuation=output.valuation,
        portfolio_intelligence=output.portfolio_intelligence,
        reasoning=output.reasoning,
        conviction=conviction,
        business_analysis=_insufficient_business_analysis(output),
        valuation_engine=_insufficient_valuation_engine(),
        has_high_financial_or_valuation_risk=False,
        has_open_questions=False,
        generated_at=GENERATED_AT,
    )
    fields.update(overrides)
    return evaluate_recommendation_gate(engine_input, **fields)


class TestRecommendationIsDelegatedNotReimplemented:
    def test_result_matches_determine_recommendation_called_directly(self):
        engine_input, output = run_minimal()
        result = _call_gate(engine_input, output, conviction=_assessment(ConvictionLevel.HIGH))
        expected = determine_recommendation(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            generated_at=GENERATED_AT,
        )
        assert result.recommendation == expected

    def test_still_recommendation_withheld_when_business_is_inconclusive(self):
        engine_input, output = run_populated()
        result = _call_gate(engine_input, output, conviction=_assessment(ConvictionLevel.VERY_HIGH))
        assert result.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD
        assert result.recommendation.reason is RecommendationWithheldReason.ENGINE_NOT_IMPLEMENTED


class TestConvictionGate:
    def test_insufficient_evidence_does_not_meet_the_gate(self):
        engine_input, output = run_minimal()
        result = _call_gate(engine_input, output, conviction=_assessment(ConvictionLevel.INSUFFICIENT_EVIDENCE))
        assert result.conviction_gate_met is False

    def test_low_does_not_meet_the_gate(self):
        engine_input, output = run_minimal()
        result = _call_gate(engine_input, output, conviction=_assessment(ConvictionLevel.LOW))
        assert result.conviction_gate_met is False

    def test_moderate_meets_the_gate(self):
        assert RECOMMENDATION_GATE_MINIMUM_CONVICTION is ConvictionLevel.MODERATE
        engine_input, output = run_minimal()
        result = _call_gate(engine_input, output, conviction=_assessment(ConvictionLevel.MODERATE))
        assert result.conviction_gate_met is True

    def test_very_high_meets_the_gate(self):
        engine_input, output = run_minimal()
        result = _call_gate(engine_input, output, conviction=_assessment(ConvictionLevel.VERY_HIGH))
        assert result.conviction_gate_met is True


class TestRecommendationWithheldWhenBusinessInconclusive:
    """Renamed from `TestNoDirectionalRecommendationTypeExists` --
    `ComputedDirectionalRecommendation` is no longer structurally
    unreachable (see `TestDirectionSelectorNowWired` below). What is
    still true, and still worth asserting, is that these specific,
    business-inconclusive fixtures never produce one, and that the
    Conviction gate remains a fact independent of `recommendation.kind`.
    """

    def test_result_has_no_direction_field_when_withheld(self):
        engine_input, output = run_minimal()
        result = _call_gate(engine_input, output, conviction=_assessment(ConvictionLevel.VERY_HIGH))
        assert result.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD
        assert not hasattr(result.recommendation, "direction")

    def test_conviction_gate_met_does_not_flip_the_recommendation_kind(self):
        """The five-level Conviction gate is an additional fact, not a
        switch that produces a directional outcome -- clearing it must
        never change `recommendation.kind` by itself; only
        `direction_selector.select_direction` does that."""
        engine_input, output = run_minimal()
        met = _call_gate(engine_input, output, conviction=_assessment(ConvictionLevel.VERY_HIGH))
        not_met = _call_gate(engine_input, output, conviction=_assessment(ConvictionLevel.LOW))
        assert met.recommendation.kind is not_met.recommendation.kind
        assert met.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD


def _weak_growth_business_analysis() -> "BusinessAnalysisResult":
    """A directly-constructed, valid `BusinessAnalysisResult` with a real
    `WEAK` Growth conclusion and every other category
    `INSUFFICIENT_INPUT` -- `growth.py`'s own rule table (declining
    Revenue and/or Free Cash Flow across every period) already has
    dedicated coverage in `test_growth.py`; this helper exercises the
    *wiring* from a real `BusinessCategoryStatus.WEAK` finding through to
    `evaluate_recommendation_gate`, not the evaluator itself, so it
    constructs the already-validated shape directly rather than
    re-running the full ingestion pipeline."""
    from atlas.analysis_engine.business_contracts import (
        BusinessAnalysisResult,
        BusinessCategory,
        BusinessCategoryStatus,
        BusinessFinding,
    )
    from atlas.analysis_engine.findings import FindingSeverity
    from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
    from atlas.decision_engine.contracts import EvidenceCoverageLevel

    provenance = Provenance(
        source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
        source_references=(),
        dependencies=(),
        update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
        consumers=(Consumer.PORTFOLIO_PAGE,),
        computed_at=GENERATED_AT,
    )
    findings = tuple(
        BusinessFinding(
            id=f"business_finding:{category.value}",
            kind=category,
            status=BusinessCategoryStatus.WEAK if category is BusinessCategory.GROWTH else BusinessCategoryStatus.INSUFFICIENT_INPUT,
            severity=FindingSeverity.MATERIAL if category is BusinessCategory.GROWTH else FindingSeverity.ATTENTION,
            supporting_evidence=(),
            contradicting_evidence=(),
            missing_evidence=(),
            confidence=EvidenceCoverageLevel.FULL,
            provenance=provenance,
            updated_at=GENERATED_AT,
        )
        for category in BusinessCategory
    )
    return BusinessAnalysisResult(state=EvaluationState.EVALUATED, findings=findings)


class TestDirectionSelectorNowWired:
    """"Recommendation Backend Step 3": proves `evaluate_recommendation_gate`
    genuinely constructs a `ComputedDirectionalRecommendation` when
    `direction_selector.select_direction` reaches a real direction --
    engineered here via a held position with a real `WEAK` Growth
    conclusion, which is real, case-specific negative evidence sufficient
    for TRIM regardless of Valuation (see `direction_selector.py`'s own
    docstring)."""

    def _held_weak_business_result(self):
        from tests.unit.decision_engine._fixtures import build_populated_input
        from atlas.decision_engine.pipeline import run_pipeline

        base_input = build_populated_input(case_id="direction-selector-wiring-case")
        import dataclasses as dc

        engine_input = dc.replace(
            base_input, portfolio_holding=PortfolioHoldingContext(ticker="ACME", weight_percent=4.0)
        )
        output = run_pipeline(engine_input, generated_at=GENERATED_AT)
        assert output.portfolio_intelligence.holding_context.linkage is HoldingLinkage.PRESENT
        business_analysis = _weak_growth_business_analysis()
        return engine_input, output, business_analysis

    def test_weak_growth_on_a_held_position_produces_a_real_trim(self):
        engine_input, output, business_analysis = self._held_weak_business_result()
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.HIGH),
            business_analysis=business_analysis,
            valuation_engine=_insufficient_valuation_engine(),
            has_high_financial_or_valuation_risk=False,
            has_open_questions=False,
            generated_at=GENERATED_AT,
        )
        assert isinstance(result.recommendation, ComputedDirectionalRecommendation)
        assert result.recommendation.direction is RecommendationDirection.TRIM
        assert isinstance(result.recommendation.conviction_level, RecommendationConvictionLevel)
        assert result.recommendation.direction_statement.strip() != ""
        assert result.recommendation.conviction_reason.strip() != ""

    def test_computed_directional_recommendation_never_carries_a_reason_field(self):
        """`RecommendationWithheld.reason` must never be read from a
        `ComputedDirectionalRecommendation` -- it has no such field."""
        engine_input, output, business_analysis = self._held_weak_business_result()
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.HIGH),
            business_analysis=business_analysis,
            valuation_engine=_insufficient_valuation_engine(),
            has_high_financial_or_valuation_risk=False,
            has_open_questions=False,
            generated_at=GENERATED_AT,
        )
        assert not hasattr(result.recommendation, "reason")
