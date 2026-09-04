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
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel
from atlas.analysis_engine.recommendation import (
    RECOMMENDATION_GATE_MINIMUM_CONVICTION,
    ChangeTriggerKind,
    ComputedDirectionalRecommendation,
    RecommendationDirection,
    evaluate_recommendation_gate,
)
from atlas.analysis_engine.recommendation_conviction import RecommendationConvictionLevel
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from atlas.analysis_engine.valuation.facts import extract_valuation_facts_from_records
from atlas.analysis_engine.valuation.pipeline import evaluate_valuation
from atlas.analysis_engine.valuation.support import ValuationSupport, ValuationSupportGapKind, ValuationSupportStatus
from atlas.decision_engine.contracts import (
    EvaluationState,
    EvidenceCoverageLevel,
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


def _insufficient_valuation_support() -> ValuationSupport:
    """The permanent, universal state every real company was in before
    `DE-015` was implemented -- the correct default for every call in
    this file that is not specifically exercising the new `DE-016`
    wiring (`TestBuyAddNowWired` below)."""
    return ValuationSupport(
        status=ValuationSupportStatus.INSUFFICIENT_INPUT,
        reasoning="No real data supplied in this fixture.",
        gap=ValuationSupportGapKind.INSUFFICIENT_HISTORICAL_VALUATION_DATA,
    )


def _call_gate(engine_input, output, *, conviction, **overrides):
    fields = dict(
        business_evaluation=output.business_evaluation,
        valuation=output.valuation,
        portfolio_intelligence=output.portfolio_intelligence,
        reasoning=output.reasoning,
        conviction=conviction,
        business_analysis=_insufficient_business_analysis(output),
        valuation_engine=_insufficient_valuation_engine(),
        valuation_support=_insufficient_valuation_support(),
        has_high_financial_or_valuation_risk=False,
        has_open_questions=False,
        generated_at=GENERATED_AT,
    )
    fields.update(overrides)
    return evaluate_recommendation_gate(engine_input, **fields)


class TestRecommendationIsDelegatedNotReimplemented:
    def test_result_matches_determine_recommendation_called_directly(self):
        """Still delegates to `determine_recommendation` for every field
        except `reason` -- `evaluate_recommendation_gate` corrects that
        one field afterward (Recommendation Evidence Sufficiency
        Alignment: `determine_recommendation`'s own `ENGINE_NOT
        _IMPLEMENTED` is stale from this call site, since `select_direction`
        is real and ran; see `recommendation.py`'s own comment)."""
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
        assert result.recommendation.kind == expected.kind
        assert result.recommendation.missing_evaluations == expected.missing_evaluations
        assert result.recommendation.required_before_recommendation == expected.required_before_recommendation
        assert result.recommendation.reason is RecommendationWithheldReason.EVIDENCE_INSUFFICIENT

    def test_still_recommendation_withheld_when_business_is_inconclusive(self):
        engine_input, output = run_populated()
        result = _call_gate(engine_input, output, conviction=_assessment(ConvictionLevel.VERY_HIGH))
        assert result.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD
        # Every prerequisite stage was EVALUATED here (real ran, real
        # declined) -- honest reason is EVIDENCE_INSUFFICIENT, not the
        # stale "engine not implemented" (Recommendation Evidence
        # Sufficiency Alignment).
        assert result.recommendation.reason is RecommendationWithheldReason.EVIDENCE_INSUFFICIENT


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


def _strong_growth_business_analysis() -> "BusinessAnalysisResult":
    """The `POSITIVE`-business mirror of `_weak_growth_business_analysis`
    above -- both Growth and Capital Allocation `STRONG`, every other
    category `INSUFFICIENT_INPUT` (this codebase's own permanent state
    for the categories it does not yet evaluate substantively)."""
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
    strong_categories = (BusinessCategory.GROWTH, BusinessCategory.CAPITAL_ALLOCATION)
    findings = tuple(
        BusinessFinding(
            id=f"business_finding:{category.value}",
            kind=category,
            status=BusinessCategoryStatus.STRONG if category in strong_categories else BusinessCategoryStatus.INSUFFICIENT_INPUT,
            severity=FindingSeverity.INFO if category in strong_categories else FindingSeverity.ATTENTION,
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


def _supported_valuation_support() -> ValuationSupport:
    return ValuationSupport(
        status=ValuationSupportStatus.SUPPORTED,
        reasoning="Test fixture: the adverse end of the range considered still avoids a nominal loss.",
    )


def _undervalued_valuation_engine():
    """A real `ValuationEngineResult` whose `FCF_YIELD_RELATIVE` finding
    is `UNDERVALUED` -- the identical real-records-through-
    `evaluate_valuation` shape
    `tests/unit/analysis_engine/valuation/test_support.py::_undervalued_facts`
    already establishes, reused here (not hand-built), with every
    `published_at` explicit and comfortably before `GENERATED_AT` --
    `market_record`'s own default `published_at` is that module's own,
    different `EVALUATED_AT` constant, one day after this file's
    `GENERATED_AT`, which would otherwise exclude every market
    observation as future-dated."""
    from datetime import date, datetime, timezone

    from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
    from atlas.analysis_engine.valuation.facts import extract_valuation_facts_from_records
    from atlas.analysis_engine.valuation.pipeline import evaluate_valuation
    from tests.unit.analysis_engine.valuation._fixtures import fundamentals_record, market_record

    def _filed(year: int) -> "datetime":
        return datetime(year, 2, 15, tzinfo=timezone.utc)

    records = (
        fundamentals_record(period_end=date(2022, 12, 31), identifier="rec22", published_at=_filed(2023), free_cash_flow=100.0),
        fundamentals_record(period_end=date(2023, 12, 31), identifier="rec23", published_at=_filed(2024), free_cash_flow=110.0),
        fundamentals_record(period_end=date(2024, 12, 31), identifier="rec24", published_at=_filed(2025), free_cash_flow=200.0),
        market_record(period_end=date(2023, 3, 1), identifier="recm22", published_at=_filed(2023), share_price=50.0, shares_outstanding=100.0),
        market_record(period_end=date(2024, 3, 1), identifier="recm23", published_at=_filed(2024), share_price=52.0, shares_outstanding=100.0),
        market_record(period_end=date(2025, 3, 1), identifier="recm24", published_at=_filed(2025), share_price=53.0, shares_outstanding=100.0),
    )
    business_facts = extract_facts_from_records(records, evaluated_at=GENERATED_AT)
    market_facts = extract_valuation_facts_from_records(records, evaluated_at=GENERATED_AT)
    return evaluate_valuation(business_facts, market_facts, evaluated_at=GENERATED_AT)


class TestBuyAddNowWired:
    """DE-016: proves the real, end-to-end wire -- a genuinely `SUPPORTED`
    `ValuationSupport`, passed all the way through
    `evaluate_recommendation_gate`, actually produces BUY/ADD -- not just
    `select_direction` in isolation (already covered by
    `test_direction_selector.py`)."""

    def _not_held_result(self):
        from tests.unit.decision_engine._fixtures import build_populated_input
        from atlas.decision_engine.pipeline import run_pipeline

        engine_input = build_populated_input(case_id="buy-add-wiring-not-held")
        output = run_pipeline(engine_input, generated_at=GENERATED_AT)
        assert output.portfolio_intelligence.holding_context.linkage is HoldingLinkage.ABSENT
        return engine_input, output

    def _held_result(self):
        from tests.unit.decision_engine._fixtures import build_populated_input
        from atlas.decision_engine.pipeline import run_pipeline
        import dataclasses as dc

        base_input = build_populated_input(case_id="buy-add-wiring-held")
        engine_input = dc.replace(
            base_input, portfolio_holding=PortfolioHoldingContext(ticker="ACME", weight_percent=4.0)
        )
        output = run_pipeline(engine_input, generated_at=GENERATED_AT)
        assert output.portfolio_intelligence.holding_context.linkage is HoldingLinkage.PRESENT
        return engine_input, output

    def test_supported_valuation_support_produces_a_real_buy(self):
        engine_input, output = self._not_held_result()
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.HIGH),
            business_analysis=_strong_growth_business_analysis(),
            valuation_engine=_undervalued_valuation_engine(),
            valuation_support=_supported_valuation_support(),
            has_high_financial_or_valuation_risk=False,
            has_open_questions=False,
            generated_at=GENERATED_AT,
        )
        assert isinstance(result.recommendation, ComputedDirectionalRecommendation)
        assert result.recommendation.direction is RecommendationDirection.BUY
        assert result.recommendation.direction_statement.strip() != ""

    def test_supported_valuation_support_produces_a_real_add(self):
        engine_input, output = self._held_result()
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.HIGH),
            business_analysis=_strong_growth_business_analysis(),
            valuation_engine=_undervalued_valuation_engine(),
            valuation_support=_supported_valuation_support(),
            has_high_financial_or_valuation_risk=False,
            has_open_questions=False,
            generated_at=GENERATED_AT,
        )
        assert isinstance(result.recommendation, ComputedDirectionalRecommendation)
        assert result.recommendation.direction is RecommendationDirection.ADD
        assert result.recommendation.direction_statement.strip() != ""

    def test_not_supported_valuation_support_leaves_the_same_case_withheld(self):
        """DE-016 Phase 15 fixture C: same not-held fixture as the real
        BUY case above, only `valuation_support` changed to
        `NOT_SUPPORTED` -- proves the wiring, not a coincidence of the
        fixture."""
        engine_input, output = self._not_held_result()
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.HIGH),
            business_analysis=_strong_growth_business_analysis(),
            valuation_engine=_undervalued_valuation_engine(),
            valuation_support=ValuationSupport(
                status=ValuationSupportStatus.NOT_SUPPORTED, reasoning="Test fixture: opposite pole."
            ),
            has_high_financial_or_valuation_risk=False,
            has_open_questions=False,
            generated_at=GENERATED_AT,
        )
        assert result.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD

    def test_insufficient_input_valuation_support_leaves_the_same_buy_case_withheld(self):
        """DE-016 Phase 15 fixture D: the real BUY fixture, only
        `valuation_support` changed to `INSUFFICIENT_INPUT`."""
        engine_input, output = self._not_held_result()
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.HIGH),
            business_analysis=_strong_growth_business_analysis(),
            valuation_engine=_undervalued_valuation_engine(),
            valuation_support=_insufficient_valuation_support(),
            has_high_financial_or_valuation_risk=False,
            has_open_questions=False,
            generated_at=GENERATED_AT,
        )
        assert result.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD

    def test_not_supported_valuation_support_leaves_the_same_add_case_withheld(self):
        """DE-016 Phase 15 fixture E: the real ADD fixture, only
        `valuation_support` changed to `NOT_SUPPORTED`."""
        engine_input, output = self._held_result()
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.HIGH),
            business_analysis=_strong_growth_business_analysis(),
            valuation_engine=_undervalued_valuation_engine(),
            valuation_support=ValuationSupport(
                status=ValuationSupportStatus.NOT_SUPPORTED, reasoning="Test fixture: opposite pole."
            ),
            has_high_financial_or_valuation_risk=False,
            has_open_questions=False,
            generated_at=GENERATED_AT,
        )
        assert result.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD

    def test_insufficient_input_valuation_support_leaves_the_same_add_case_withheld(self):
        """DE-016 Phase 15 fixture F: the real ADD fixture, only
        `valuation_support` changed to `INSUFFICIENT_INPUT`."""
        engine_input, output = self._held_result()
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.HIGH),
            business_analysis=_strong_growth_business_analysis(),
            valuation_engine=_undervalued_valuation_engine(),
            valuation_support=_insufficient_valuation_support(),
            has_high_financial_or_valuation_risk=False,
            has_open_questions=False,
            generated_at=GENERATED_AT,
        )
        assert result.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD


class TestRecommendationEvidenceSufficiencyAlignmentIntegration:
    """End-to-end proof through the real `evaluate_recommendation_gate`
    (not just `select_direction`/`calculate_recommendation_conviction`
    in isolation -- those are `test_direction_selector.py`'s and
    `test_recommendation_conviction.py`'s own responsibility): a Case
    with zero recorded Observations (`run_minimal`, the same fixture
    `TestRecommendationIsDelegatedNotReimplemented` uses) but real,
    provenance-backed company-fundamentals evidence now reaches a real
    `ComputedDirectionalRecommendation`, exactly as it would for an
    Observation-backed Case."""

    def test_no_observations_but_real_growth_and_valuation_produces_a_real_buy(self):
        engine_input, output = run_minimal()
        assert output.portfolio_intelligence.holding_context.linkage is HoldingLinkage.ABSENT
        assert output.business_evaluation.evidence_quality.coverage is EvidenceCoverageLevel.NOT_APPLICABLE

        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.HIGH),
            business_analysis=_strong_growth_business_analysis(),
            valuation_engine=_undervalued_valuation_engine(),
            valuation_support=_supported_valuation_support(),
            has_high_financial_or_valuation_risk=False,
            has_open_questions=False,
            generated_at=GENERATED_AT,
        )
        assert isinstance(result.recommendation, ComputedDirectionalRecommendation)
        assert result.recommendation.direction is RecommendationDirection.BUY
        assert result.recommendation.conviction_level is RecommendationConvictionLevel.LOW

    def test_no_observations_and_no_real_company_evidence_stays_withheld(self):
        """The control: zero Observations AND business/valuation still
        inconclusive (this file's own default `_call_gate` fixtures) --
        unchanged, still withheld."""
        engine_input, output = run_minimal()
        result = _call_gate(engine_input, output, conviction=_assessment(ConvictionLevel.HIGH))
        assert result.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD


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
            valuation_support=_insufficient_valuation_support(),
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
            valuation_support=_insufficient_valuation_support(),
            has_high_financial_or_valuation_risk=False,
            has_open_questions=False,
            generated_at=GENERATED_AT,
        )
        assert not hasattr(result.recommendation, "reason")


class TestWhatWouldChange:
    """Calibration Phase 2 (Investment Case Coherence Implementation),
    Phase 6: `RecommendationReasoning.what_would_change` must be
    genuinely populated -- not an empty tuple -- for every real
    `ComputedDirectionalRecommendation`, and must name the specific
    condition that actually gated this case, not a generic fallback."""

    def test_pure_priority_order_risk_outranks_everything(self):
        from atlas.analysis_engine.recommendation import _derive_what_would_change

        result = _derive_what_would_change(
            has_high_financial_or_valuation_risk=True,
            valuation_support_status=ValuationSupportStatus.NOT_SUPPORTED,
            growth_status=BusinessCategoryStatus.WEAK,
            capital_allocation_status=BusinessCategoryStatus.WEAK,
            valuation_status=ValuationStatus.EXPENSIVE,
        )
        # Precedence still puts risk first, but every applicable
        # condition is now emitted rather than only the winner. The
        # original first-match-wins behaviour silently discarded the
        # rest: AZN carries elevated risk AND an expensive valuation,
        # and a monitor cannot watch a condition it was never told
        # about. Ordering is what precedence governs now, not survival.
        assert result[0] is ChangeTriggerKind.REDUCED_RISK
        assert set(result) == {
            ChangeTriggerKind.REDUCED_RISK,
            ChangeTriggerKind.LOWER_VALUATION,
            ChangeTriggerKind.MORE_ATTRACTIVE_VALUATION,
            ChangeTriggerKind.IMPROVED_GROWTH_EVIDENCE,
            ChangeTriggerKind.IMPROVED_CAPITAL_ALLOCATION_EVIDENCE,
        }

    def test_pure_priority_order_valuation_support_outranks_business(self):
        from atlas.analysis_engine.recommendation import _derive_what_would_change

        result = _derive_what_would_change(
            has_high_financial_or_valuation_risk=False,
            valuation_support_status=ValuationSupportStatus.NOT_SUPPORTED,
            growth_status=BusinessCategoryStatus.WEAK,
            capital_allocation_status=BusinessCategoryStatus.WEAK,
            valuation_status=ValuationStatus.EXPENSIVE,
        )
        # Valuation still precedes business quality in the ordering;
        # the business-quality conditions are no longer dropped.
        assert result.index(ChangeTriggerKind.MORE_ATTRACTIVE_VALUATION) < result.index(
            ChangeTriggerKind.IMPROVED_GROWTH_EVIDENCE)
        assert ChangeTriggerKind.IMPROVED_CAPITAL_ALLOCATION_EVIDENCE in result

    def test_pure_no_credible_trigger_is_a_real_disclosed_answer_not_silence(self):
        from atlas.analysis_engine.recommendation import _derive_what_would_change

        result = _derive_what_would_change(
            has_high_financial_or_valuation_risk=False,
            valuation_support_status=ValuationSupportStatus.SUPPORTED,
            growth_status=BusinessCategoryStatus.STRONG,
            capital_allocation_status=BusinessCategoryStatus.STRONG,
            valuation_status=ValuationStatus.UNDERVALUED,
            has_real_risk_evidence=True,
        )
        # A case with no weakness at all used to be the ONLY thing this
        # vocabulary could describe, via the fallback -- which is why 7
        # of 9 real cases produced nothing else and the field was
        # useless for monitoring. For a healthy holding the credible
        # change is that a strength breaks, and that is now expressible.
        assert ChangeTriggerKind.NO_CREDIBLE_TRIGGER_IDENTIFIED not in result
        assert set(result) == {
            ChangeTriggerKind.FINANCIAL_RISK_BECOMES_ELEVATED,
            ChangeTriggerKind.VALUATION_BECOMES_EXPENSIVE,
            ChangeTriggerKind.VALUATION_SUPPORT_LOST,
            ChangeTriggerKind.GROWTH_DETERIORATES,
            ChangeTriggerKind.CAPITAL_ALLOCATION_DETERIORATES,
        }

    def test_the_fallback_survives_only_when_no_dimension_speaks(self):
        """It is still a real, disclosed answer -- just no longer the
        default one. Reached when every dimension is inconclusive."""
        from atlas.analysis_engine.recommendation import _derive_what_would_change

        assert _derive_what_would_change(
            has_high_financial_or_valuation_risk=False,
            has_real_risk_evidence=False,
            valuation_support_status=ValuationSupportStatus.INSUFFICIENT_INPUT,
            growth_status=BusinessCategoryStatus.MODERATE,
            capital_allocation_status=BusinessCategoryStatus.MODERATE,
            valuation_status=ValuationStatus.NOT_EVALUATED,
        ) == (ChangeTriggerKind.NO_CREDIBLE_TRIGGER_IDENTIFIED,)

    def test_a_data_gap_emits_no_condition(self):
        """`INSUFFICIENT_INPUT` valuation support is a missing input,
        not an investment condition. `key_unknowns` already reports it
        as ANALYSIS_INPUT_MISSING; emitting it here too would give one
        fact two owners."""
        from atlas.analysis_engine.recommendation import _derive_what_would_change

        result = _derive_what_would_change(
            has_high_financial_or_valuation_risk=False,
            has_real_risk_evidence=True,
            valuation_support_status=ValuationSupportStatus.INSUFFICIENT_INPUT,
            growth_status=BusinessCategoryStatus.MODERATE,
            capital_allocation_status=BusinessCategoryStatus.MODERATE,
            valuation_status=ValuationStatus.FAIRLY_VALUED,
        )
        assert ChangeTriggerKind.MORE_ATTRACTIVE_VALUATION not in result
        assert ChangeTriggerKind.VALUATION_SUPPORT_LOST not in result

    def test_absent_risk_evidence_never_claims_risk_is_fine(self):
        """Without real risk evidence, `FINANCIAL_RISK_BECOMES_ELEVATED`
        must not be emitted -- absence of assessment is not a
        reassuring finding."""
        from atlas.analysis_engine.recommendation import _derive_what_would_change

        assert ChangeTriggerKind.FINANCIAL_RISK_BECOMES_ELEVATED not in _derive_what_would_change(
            has_high_financial_or_valuation_risk=False,
            has_real_risk_evidence=False,
            valuation_support_status=ValuationSupportStatus.SUPPORTED,
            growth_status=BusinessCategoryStatus.STRONG,
            capital_allocation_status=BusinessCategoryStatus.STRONG,
            valuation_status=ValuationStatus.FAIRLY_VALUED,
        )

    def test_a_real_trim_from_weak_growth_names_improved_growth_evidence(self):
        """End-to-end: the exact fixture `TestDirectionSelectorNowWired`
        already uses for a real TRIM (WEAK Growth, everything else
        insufficient/unsupported) must report the Growth trigger, not a
        fallback -- the whole point of Phase 6 is that this answer is
        specific to the case that actually produced it."""
        engine_input, output, business_analysis = TestDirectionSelectorNowWired()._held_weak_business_result()
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.HIGH),
            business_analysis=business_analysis,
            valuation_engine=_insufficient_valuation_engine(),
            valuation_support=_insufficient_valuation_support(),
            has_high_financial_or_valuation_risk=False,
            has_open_questions=False,
            generated_at=GENERATED_AT,
        )
        assert isinstance(result.recommendation, ComputedDirectionalRecommendation)
        assert result.recommendation.reasoning.what_would_change == (ChangeTriggerKind.IMPROVED_GROWTH_EVIDENCE,)

    def test_a_real_buy_from_a_strong_undervalued_case_names_no_credible_trigger(self):
        """End-to-end: the exact fixture `TestBuyAddNowWired` already
        uses for a real BUY (everything strong/supported/undervalued)
        has nothing weak to name -- must honestly say so, never invent
        a trigger that isn't real."""
        from tests.unit.decision_engine._fixtures import build_populated_input
        from atlas.decision_engine.pipeline import run_pipeline

        engine_input = build_populated_input(case_id="what-would-change-buy-wiring")
        output = run_pipeline(engine_input, generated_at=GENERATED_AT)
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.HIGH),
            business_analysis=_strong_growth_business_analysis(),
            valuation_engine=_undervalued_valuation_engine(),
            valuation_support=_supported_valuation_support(),
            has_high_financial_or_valuation_risk=False,
            has_open_questions=False,
            generated_at=GENERATED_AT,
        )
        assert isinstance(result.recommendation, ComputedDirectionalRecommendation)
        # A strong, undervalued, well-supported case has no weakness to
        # heal -- which used to leave the fallback as the only sayable
        # answer. It now names what would BREAK the case instead, which
        # is the genuinely monitorable condition for a healthy holding.
        triggers = result.recommendation.reasoning.what_would_change
        assert ChangeTriggerKind.NO_CREDIBLE_TRIGGER_IDENTIFIED not in triggers
        assert ChangeTriggerKind.VALUATION_BECOMES_EXPENSIVE in triggers
        assert ChangeTriggerKind.VALUATION_SUPPORT_LOST in triggers
        assert ChangeTriggerKind.GROWTH_DETERIORATES in triggers
