"""Valuation Observation Integrity -- what may reach the recommendation.

Eligibility is applied once, upstream: the FCF-yield finding's `status` only
classifies decision-eligible history. Everything below reads that status as
it always did, so thin history cannot become a BUY, a TRIM, a HOLD, a
Valuation Risk level or a valuation driver -- and a method that does not
apply is neither an unknown to resolve nor an open question to ask.
"""
from __future__ import annotations

import dataclasses
import json

import pytest

from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.conviction import ConvictionLevel
from atlas.analysis_engine.findings import FindingSeverity
from atlas.analysis_engine.investment_case_change import compare_snapshots
from atlas.analysis_engine.investment_case_synthesis import OpenQuestionOrigin, derive_case_open_questions
from atlas.analysis_engine.reasoning import (
    CanonicalEngine,
    InvestmentReasonKind,
    SignalState,
    deserialize_reasoning,
    serialize_reasoning,
)
from atlas.analysis_engine.recommendation import (
    ComputedDirectionalRecommendation,
    RecommendationDirection,
    evaluate_recommendation_gate,
)
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.risk.valuation_risk import evaluate_valuation_risk
from atlas.analysis_engine.valuation.contracts import (
    ValuationDecisionEligibility as Eligibility,
    ValuationMethodKind,
    ValuationStatus,
)
from atlas.analysis_engine.valuation.models import ValuationEngineResult
from atlas.analysis_engine.valuation.scenarios import build_scenario_findings
from atlas.decision_engine.contracts import EvaluationState, RecommendationOutcomeKind
from tests.unit.analysis_engine._fixtures import GENERATED_AT
from tests.unit.analysis_engine.test_investment_case_change import _snapshot, _with_risk
from tests.unit.analysis_engine.test_recommendation import (
    TestBuyAddNowWired,
    _assessment,
    _strong_growth_business_analysis,
    _supported_valuation_support,
)
from tests.unit.analysis_engine.valuation._epochs import annual_history, evaluate, quote

TODAY = "2026-06-30"


def fcf_finding(prior_years: int, today_price: float, *, industry: str = "SOFTWARE - APPLICATION"):
    """Prior fiscal years at a 2% yield (FCF 100 at price 50, 100 shares),
    then fiscal 2024 (FCF 100) priced today."""
    years = {2024 - prior_years + i: 100.0 for i in range(prior_years + 1)}
    business, market = annual_history(years, {y: 50.0 for y in list(years)[:-1]})
    return evaluate(business, [*market, *quote(TODAY, today_price)], industry=industry, at=GENERATED_AT)


def engine(finding) -> ValuationEngineResult:
    return ValuationEngineResult(
        state=EvaluationState.EVALUATED, findings=(finding, *build_scenario_findings(evaluated_at=GENERATED_AT))
    )


CHEAP, DEAR, INSIDE = 25.0, 100.0, 50.0  # 4%, 1%, 2% against prior 2%s


def gate(finding, *, held: bool, support=None):
    engine_input, output = (TestBuyAddNowWired()._held_result() if held else TestBuyAddNowWired()._not_held_result())
    return evaluate_recommendation_gate(
        engine_input,
        business_evaluation=output.business_evaluation,
        valuation=output.valuation,
        portfolio_intelligence=output.portfolio_intelligence,
        reasoning=output.reasoning,
        conviction=_assessment(ConvictionLevel.HIGH),
        business_analysis=_strong_growth_business_analysis(),
        valuation_engine=engine(finding),
        valuation_support=support or _supported_valuation_support(),
        has_high_financial_or_valuation_risk=evaluate_valuation_risk(finding, evaluated_at=GENERATED_AT).status
        is RiskStatus.HIGH,
        has_open_questions=False,
        generated_at=GENERATED_AT,
    ).recommendation


class TestTheFixturesMeanWhatTheySay:
    @pytest.mark.parametrize("prior, eligibility", [(1, Eligibility.LIMITED), (2, Eligibility.LIMITED),
                                                    (3, Eligibility.ELIGIBLE), (0, Eligibility.INSUFFICIENT)])
    def test_eligibility(self, prior, eligibility):
        assert fcf_finding(prior, CHEAP).fcf_yield_evidence.eligibility is eligibility


class TestThinHistoryNeverDecides:
    """Phases S, T, U: thin cheapness is no BUY, thin expense no TRIM, thin
    neutrality no HOLD -- even with Valuation Support handed in as
    SUPPORTED, which only a classified valuation can act on."""

    @pytest.mark.parametrize("prior", [0, 1, 2])
    def test_thin_cheapness_is_not_a_buy(self, prior):
        recommendation = gate(fcf_finding(prior, CHEAP), held=False)
        assert recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD

    @pytest.mark.parametrize("prior", [1, 2])
    def test_thin_expense_is_not_a_trim(self, prior):
        recommendation = gate(fcf_finding(prior, DEAR), held=True)
        assert recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD

    @pytest.mark.parametrize("prior", [1, 2])
    def test_thin_neutrality_is_not_a_hold(self, prior):
        recommendation = gate(fcf_finding(prior, INSIDE), held=True)
        assert recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD

    def test_the_same_cheapness_on_eligible_history_is_a_buy(self):
        recommendation = gate(fcf_finding(3, CHEAP), held=False)
        assert isinstance(recommendation, ComputedDirectionalRecommendation)
        assert recommendation.direction is RecommendationDirection.BUY

    def test_the_same_expense_on_eligible_history_is_a_trim(self):
        recommendation = gate(fcf_finding(3, DEAR), held=True)
        assert recommendation.direction is RecommendationDirection.TRIM


class TestValuationRisk:
    def test_high_requires_eligible_expense(self):
        assert evaluate_valuation_risk(fcf_finding(3, DEAR), evaluated_at=GENERATED_AT).status is RiskStatus.HIGH
        for prior in (0, 1, 2):
            risk = evaluate_valuation_risk(fcf_finding(prior, DEAR), evaluated_at=GENERATED_AT)
            assert risk.status is RiskStatus.INSUFFICIENT_INPUT

    def test_limited_history_is_never_moderate(self):
        risk = evaluate_valuation_risk(fcf_finding(2, INSIDE), evaluated_at=GENERATED_AT)
        assert risk.status is RiskStatus.INSUFFICIENT_INPUT

    def test_not_applicable_is_its_own_status(self):
        risk = evaluate_valuation_risk(fcf_finding(3, DEAR, industry="CAPITAL MARKETS"), evaluated_at=GENERATED_AT)
        assert risk.status is RiskStatus.NOT_APPLICABLE
        assert risk.severity is FindingSeverity.INFO
        assert risk.missing_evidence == ()


def reasoning_of(finding, *, held=False):
    return gate(finding, held=held).reasoning


def kinds(reasons):
    return [r.kind for r in reasons]


def valuation_signal(reasoning):
    return next(c for c in reasoning.signal_summary if c.engine is CanonicalEngine.VALUATION)


class TestDrivers:
    """Phase AD: a valuation driver only from decision-eligible evidence."""

    def test_thin_expense_raises_no_valuation_expensive(self):
        reasoning = reasoning_of(fcf_finding(1, DEAR), held=True)
        assert InvestmentReasonKind.VALUATION_EXPENSIVE not in kinds(reasoning.counter_drivers)
        assert InvestmentReasonKind.FINANCIAL_RISK_ELEVATED not in kinds(reasoning.counter_drivers)

    def test_thin_cheapness_raises_no_supportive_valuation(self):
        reasoning = reasoning_of(fcf_finding(2, CHEAP))
        assert InvestmentReasonKind.VALUATION_UNDERVALUED not in kinds(reasoning.primary_drivers)
        assert InvestmentReasonKind.VALUATION_FAIRLY_VALUED not in kinds(reasoning.primary_drivers)

    def test_eligible_expense_is_named_as_valuation(self):
        reasoning = reasoning_of(fcf_finding(3, DEAR), held=True)
        assert InvestmentReasonKind.VALUATION_EXPENSIVE in kinds(reasoning.counter_drivers)
        assert InvestmentReasonKind.FINANCIAL_RISK_ELEVATED not in kinds(reasoning.counter_drivers)


class TestSignalSummary:
    def test_limited_history_is_described_with_its_depth(self):
        signal = valuation_signal(reasoning_of(fcf_finding(1, DEAR), held=True))
        assert signal.source_status == "insufficient_input"
        assert signal.state is SignalState.INCONCLUSIVE
        assert signal.evidence_eligibility == "limited"
        assert signal.historical_observation_count == 1
        assert signal.current_yield == pytest.approx(0.01)

    def test_eligible_history_counts_fiscal_years(self):
        signal = valuation_signal(reasoning_of(fcf_finding(3, DEAR), held=True))
        assert signal.evidence_eligibility == "eligible"
        assert signal.historical_observation_count == 3
        assert signal.historical_percentile == 0.0

    def test_not_applicable_is_not_an_unknown(self):
        reasoning = reasoning_of(fcf_finding(3, DEAR, industry="BANKS - DIVERSIFIED"))
        signal = valuation_signal(reasoning)
        assert signal.source_status == "not_applicable"
        assert signal.state is SignalState.NOT_EVALUATED
        assert signal.current_yield is None
        assert CanonicalEngine.VALUATION not in [u.engine for u in reasoning.key_unknowns]

    def test_thin_history_is_an_unknown_to_resolve(self):
        reasoning = reasoning_of(fcf_finding(1, DEAR), held=True)
        assert CanonicalEngine.VALUATION in [u.engine for u in reasoning.key_unknowns]

    def test_the_eligibility_survives_storage(self):
        reasoning = reasoning_of(fcf_finding(1, DEAR), held=True)
        stored = deserialize_reasoning(json.loads(json.dumps(serialize_reasoning(reasoning))))
        assert valuation_signal(stored).evidence_eligibility == "limited"

    def test_a_row_stored_before_eligibility_existed_reads_back_as_absent(self):
        payload = serialize_reasoning(reasoning_of(fcf_finding(1, DEAR), held=True))
        for contribution in payload["signalSummary"]:
            contribution.pop("evidenceEligibility")
        assert valuation_signal(deserialize_reasoning(payload)).evidence_eligibility is None


class TestOpenQuestions:
    def _questions(self, finding):
        from atlas.analysis_engine.business_contracts import BusinessAnalysisResult
        business = _strong_growth_business_analysis()
        assert isinstance(business, BusinessAnalysisResult)
        return {q.origin for q in derive_case_open_questions(business, engine(finding))}

    def test_thin_history_is_an_open_valuation_question(self):
        assert OpenQuestionOrigin.VALUATION_INCONCLUSIVE in self._questions(fcf_finding(1, DEAR))

    def test_a_method_that_does_not_apply_asks_no_valuation_question(self):
        origins = self._questions(fcf_finding(3, DEAR, industry="INSURANCE - DIVERSIFIED"))
        assert not origins & {OpenQuestionOrigin.VALUATION_INCONCLUSIVE, OpenQuestionOrigin.VALUATION_EXPENSIVE_VERSUS_GROWTH,
                              OpenQuestionOrigin.SCENARIO_VALUATION_UNAVAILABLE}


class TestChangeIntelligence:
    """Phase AG: a corrected valuation history is a new ruler, not a
    re-rating -- across methods, nothing valuation-derived is reported;
    under one method, everything still is."""

    def _pair(self, previous_method, current_method):
        previous = dataclasses.replace(
            _with_risk(_snapshot(valuation_status="fairly_valued", risk_highlights=("valuation_risk",)),
                       "valuation_risk", "moderate"),
            valuation_methodology=previous_method)
        current = dataclasses.replace(
            _with_risk(_snapshot(valuation_status="expensive", open_questions=("valuation_expensive_versus_growth",)),
                       "valuation_risk", "high"),
            valuation_methodology=current_method)
        current = dataclasses.replace(current, business_category_states=tuple(
            (c, "strong" if c == "growth" else s, f) for c, s, f in current.business_category_states))
        return compare_snapshots(previous, current)

    def test_a_method_change_reports_only_what_the_company_did(self):
        result = self._pair(None, "fiscal_epoch_v2")
        dims = [(c.category.value, c.details.get("dimension") or c.details.get("highlight_kind")
                 or c.details.get("open_question_origin")) for c in result.changes]
        assert dims == [("analytical_coverage_changed", "growth")]

    def test_under_one_method_valuation_changes_are_still_reported(self):
        result = self._pair("fiscal_epoch_v2", "fiscal_epoch_v2")
        categories = {c.category.value for c in result.changes}
        assert {"valuation_changed", "valuation_risk_changed", "risk_removed", "open_question_added"} <= categories

    def test_a_captured_snapshot_records_the_construction(self):
        from atlas.analysis_engine.investment_case_change import capture_snapshot
        from atlas.analysis_engine.pipeline import assemble_analysis
        from atlas.analysis_engine.valuation.cash_flow import FCF_YIELD_METHODOLOGY
        from tests.unit.analysis_engine._fixtures import run_minimal

        engine_input, output = run_minimal()
        analysis = assemble_analysis(engine_input, output, is_thesis_stale=False, business_records=(), generated_at=GENERATED_AT)
        assert capture_snapshot(analysis).valuation_methodology == FCF_YIELD_METHODOLOGY == "fiscal_epoch_v2"


class TestTheFindingKindIsUnchanged:
    def test_eligibility_never_adds_a_valuation_status(self):
        assert {s.value for s in ValuationStatus} == {
            "not_evaluated", "insufficient_input", "undervalued", "fairly_valued", "expensive"}

    def test_the_fcf_finding_is_first_and_only_it_carries_evidence(self):
        result = engine(fcf_finding(3, DEAR))
        assert result.findings[0].kind is ValuationMethodKind.FCF_YIELD_RELATIVE
        assert all(f.fcf_yield_evidence is None for f in result.findings[1:])
        assert RiskCategory.VALUATION_RISK.value == "valuation_risk"
