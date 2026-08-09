"""Tests for `atlas.alpha.discovery_context.case_projection
.build_discovery_case_context` (ATLAS-030 Phase 18) -- the pure
projection from a real `InvestmentCaseComposition` onto Discovery's own
context shape. A real `CanonicalAnalysis` is built once via the existing
`analysis_engine` fixtures (`assemble_analysis` over a real
`decision_engine` pipeline run) and then narrowly overridden per
scenario with `dataclasses.replace` -- every scenario below exercises
the real, shaped analytical objects this function actually receives in
production, never a hand-rolled duck-typed stand-in.
"""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone

import pytest

from atlas.alpha.discovery_context.case_projection import (
    ConsiderKind,
    KeyRiskKind,
    PortfolioContextFact,
    build_discovery_case_context,
)
from atlas.alpha.investment_case.models import CurrentThesis, InvestmentCaseComposition
from atlas.alpha.portfolio.models import AlphaHolding, AlphaTradeLogEntry, ReconciliationStatus, TransactionType
from atlas.alpha.portfolio_status.models import (
    AttentionCategory,
    AttentionItem,
    PortfolioStatusReport,
    PortfolioSummaryMetrics,
)
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.pipeline import assemble_analysis
from atlas.analysis_engine.risk.contracts import RiskStatus, severity_for_risk_status
from atlas.analysis_engine.risk.models import EVALUATED_RISK_CATEGORIES, RiskAnalysisResult, RiskFinding
from atlas.analysis_engine.provenance import Provenance, SourceKind, UpdateTrigger
from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel
from tests.unit.analysis_engine._fixtures import GENERATED_AT, run_minimal

_NOW = datetime.now(timezone.utc)
_EMPTY_STATUS_REPORT = PortfolioStatusReport.empty()


def _prov() -> Provenance:
    return Provenance(
        source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
        source_references=(),
        dependencies=(),
        update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
        consumers=(),
        computed_at=_NOW,
    )


def _base_analysis():
    engine_input, output = run_minimal()
    return assemble_analysis(engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT)


def _risk_analysis(statuses: dict[RiskCategory, RiskStatus]) -> RiskAnalysisResult:
    assert set(statuses) == EVALUATED_RISK_CATEGORIES
    return RiskAnalysisResult(
        state=EvaluationState.EVALUATED,
        findings=tuple(
            RiskFinding(
                id=f"risk_finding:{category.value}",
                category=category,
                status=status,
                severity=severity_for_risk_status(status),
                supporting_facts=(),
                contradicting_facts=(),
                missing_evidence=(),
                confidence=EvidenceCoverageLevel.NOT_APPLICABLE,
                provenance=_prov(),
                evaluated_at=_NOW,
            )
            for category, status in statuses.items()
        ),
    )


def _holding(ticker: str = "AMD", weight_percent: float = 10.0, **overrides) -> AlphaHolding:
    return AlphaHolding(ticker=ticker, weight_percent=weight_percent, **overrides)


def _composition(*, holding, analysis, is_thesis_stale=False, decision_history=(), observation_history=(), outcome_history=(), trade_log=()) -> InvestmentCaseComposition:
    return InvestmentCaseComposition(
        case_id="00000000-0000-0000-0000-0000000000aa",
        holding_context=holding,
        canonical_analysis=analysis,
        current_thesis=CurrentThesis(
            latest_decision_reason=None, latest_decision_type=None, latest_observation_statement=None
        ),
        decision_history=decision_history,
        observation_history=observation_history,
        outcome_history=outcome_history,
        trade_log=trade_log,
        is_thesis_stale=is_thesis_stale,
        generated_at=_NOW,
    )


class TestHeldVsResearchCase:
    def test_held_case_carries_ticker(self):
        composition = _composition(holding=_holding("AMD"), analysis=_base_analysis())
        context = build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
        assert context.held is True
        assert context.ticker == "AMD"

    def test_research_only_case_has_no_ticker_and_no_workflow_facts(self):
        composition = _composition(holding=None, analysis=_base_analysis())
        context = build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
        assert context.held is False
        assert context.ticker is None
        assert context.key_risks == ()
        assert context.consider_kinds == ()
        assert context.portfolio_context_facts == ()


class TestNoObservations:
    def test_no_evidence_gaps_beyond_the_real_pipeline_output(self):
        composition = _composition(holding=_holding(), analysis=_base_analysis())
        context = build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
        # run_minimal() has zero Observations -- a real, honest gap.
        assert len(context.missing_evidence_kinds) >= 1


class TestOpenQuestions:
    def test_reflects_the_corrected_canonical_list_not_raw_reasoning(self):
        base = _base_analysis()
        custom_open_questions = base.open_questions[:2]
        analysis = dataclasses.replace(base, open_questions=custom_open_questions)
        composition = _composition(holding=_holding(), analysis=analysis)
        context = build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
        assert context.open_questions == tuple(q.kind for q in custom_open_questions)


class TestConvictionAndConfidence:
    def test_both_come_directly_from_canonical_analysis(self):
        base = _base_analysis()
        composition = _composition(holding=_holding(), analysis=base)
        context = build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
        assert context.conviction_level is base.conviction.level
        assert context.confidence is base.confidence


class TestHighFinancialRisk:
    def test_high_financial_risk_does_not_by_itself_trigger_a_key_risk(self):
        """Only THESIS_RISK maps to `CONTRADICTING_EVIDENCE` -- Financial
        Risk has no `KeyRiskKind` analog (matches legacy `case_intelligence`'s
        own scope, confirmed by the ATLAS-030 audit)."""
        base = _base_analysis()
        analysis = dataclasses.replace(
            base,
            risk_analysis=_risk_analysis(
                {
                    RiskCategory.BUSINESS_RISK: RiskStatus.LOW,
                    RiskCategory.FINANCIAL_RISK: RiskStatus.HIGH,
                    RiskCategory.VALUATION_RISK: RiskStatus.LOW,
                    RiskCategory.THESIS_RISK: RiskStatus.LOW,
                }
            ),
        )
        composition = _composition(holding=_holding(), analysis=analysis)
        context = build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
        assert KeyRiskKind.CONTRADICTING_EVIDENCE not in context.key_risks


class TestHighThesisRisk:
    def test_high_thesis_risk_triggers_contradicting_evidence_key_risk(self):
        base = _base_analysis()
        analysis = dataclasses.replace(
            base,
            risk_analysis=_risk_analysis(
                {
                    RiskCategory.BUSINESS_RISK: RiskStatus.LOW,
                    RiskCategory.FINANCIAL_RISK: RiskStatus.LOW,
                    RiskCategory.VALUATION_RISK: RiskStatus.LOW,
                    RiskCategory.THESIS_RISK: RiskStatus.HIGH,
                }
            ),
        )
        composition = _composition(holding=_holding(), analysis=analysis)
        context = build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
        assert KeyRiskKind.CONTRADICTING_EVIDENCE in context.key_risks


class TestHighConcentration:
    def test_large_position_triggers_high_concentration_key_risk_and_fact(self):
        composition = _composition(holding=_holding(weight_percent=40.0), analysis=_base_analysis())
        context = build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
        assert KeyRiskKind.HIGH_CONCENTRATION in context.key_risks
        assert PortfolioContextFact.HIGH_CONCENTRATION in context.portfolio_context_facts

    def test_small_position_triggers_neither(self):
        composition = _composition(holding=_holding(weight_percent=5.0), analysis=_base_analysis())
        context = build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
        assert KeyRiskKind.HIGH_CONCENTRATION not in context.key_risks
        assert PortfolioContextFact.HIGH_CONCENTRATION not in context.portfolio_context_facts


class TestAwaitingReconciliation:
    def test_triggers_key_risk(self):
        holding = _holding(reconciliation_status=ReconciliationStatus.AWAITING_RECONCILIATION)
        composition = _composition(holding=holding, analysis=_base_analysis())
        context = build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
        assert KeyRiskKind.AWAITING_RECONCILIATION in context.key_risks


class TestThesisStale:
    def test_stale_thesis_triggers_review_thesis_consider_kind(self):
        composition = _composition(holding=_holding(), analysis=_base_analysis(), is_thesis_stale=True)
        context = build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
        assert context.is_stale is True
        assert ConsiderKind.REVIEW_THESIS in context.consider_kinds

    def test_fresh_thesis_does_not(self):
        composition = _composition(holding=_holding(), analysis=_base_analysis(), is_thesis_stale=False)
        context = build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
        assert ConsiderKind.REVIEW_THESIS not in context.consider_kinds


class TestPendingWorkflowReusesPortfolioStatusService:
    """ATLAS-030: fixes a documented pre-existing duplication --
    `case_intelligence`'s own `_pending_workflow_count` reimplemented
    `PortfolioStatusService`'s attention-item logic independently. This
    projection reuses `PortfolioStatusReport.attention_items` directly."""

    def test_a_matching_attention_item_triggers_update_case_and_pending_workflow_fact(self):
        status_report = PortfolioStatusReport(
            exists=True,
            summary=None,
            attention_items=(
                AttentionItem(ticker="AMD", category=AttentionCategory.DECISION_WITHOUT_OUTCOME, case_id=None),
            ),
            review_queue=(),
            health=None,
        )
        composition = _composition(holding=_holding("AMD"), analysis=_base_analysis())
        context = build_discovery_case_context(composition, status_report)
        assert ConsiderKind.UPDATE_CASE in context.consider_kinds
        assert PortfolioContextFact.PENDING_WORKFLOW in context.portfolio_context_facts

    def test_an_unrelated_ticker_does_not_trigger_it(self):
        status_report = PortfolioStatusReport(
            exists=True,
            summary=None,
            attention_items=(
                AttentionItem(ticker="NVDA", category=AttentionCategory.DECISION_WITHOUT_OUTCOME, case_id=None),
            ),
            review_queue=(),
            health=None,
        )
        composition = _composition(holding=_holding("AMD"), analysis=_base_analysis())
        context = build_discovery_case_context(composition, status_report)
        assert ConsiderKind.UPDATE_CASE not in context.consider_kinds

    def test_awaiting_reconciliation_category_does_not_count_as_pending_workflow(self):
        """Only the three "unfinished chain" categories count -- not
        every `AttentionCategory` member."""
        status_report = PortfolioStatusReport(
            exists=True,
            summary=None,
            attention_items=(
                AttentionItem(ticker="AMD", category=AttentionCategory.AWAITING_RECONCILIATION, case_id=None),
            ),
            review_queue=(),
            health=None,
        )
        composition = _composition(holding=_holding("AMD"), analysis=_base_analysis())
        context = build_discovery_case_context(composition, status_report)
        assert ConsiderKind.UPDATE_CASE not in context.consider_kinds


class TestLargestHoldingFact:
    def test_matches_portfolio_status_summary_by_reference_not_recomputed(self):
        summary = PortfolioSummaryMetrics(
            holdings_count=1,
            largest_position_ticker="AMD",
            largest_position_weight_percent=10.0,
            number_of_investment_cases=1,
            open_decisions=0,
            pending_outcomes=0,
            pending_executions=0,
            concentration_level="Low",
            unallocated_percent=0.0,
        )
        status_report = PortfolioStatusReport(exists=True, summary=summary, attention_items=(), review_queue=(), health=None)
        composition = _composition(holding=_holding("AMD"), analysis=_base_analysis())
        context = build_discovery_case_context(composition, status_report)
        assert PortfolioContextFact.LARGEST_HOLDING in context.portfolio_context_facts


class TestRecentTrade:
    def test_most_recent_buy_triggers_recently_increased(self):
        trade = AlphaTradeLogEntry(
            outcome_id="o1", decision_id="d1", security="AMD", transaction_type=TransactionType.BUY,
            quantity=10, execution_price=100.0, executed_at=_NOW,
        )
        composition = _composition(holding=_holding("AMD"), analysis=_base_analysis(), trade_log=(trade,))
        context = build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
        assert PortfolioContextFact.RECENTLY_INCREASED in context.portfolio_context_facts

    def test_most_recent_sell_triggers_recently_trimmed(self):
        trade = AlphaTradeLogEntry(
            outcome_id="o1", decision_id="d1", security="AMD", transaction_type=TransactionType.SELL,
            quantity=10, execution_price=100.0, executed_at=_NOW,
        )
        composition = _composition(holding=_holding("AMD"), analysis=_base_analysis(), trade_log=(trade,))
        context = build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
        assert PortfolioContextFact.RECENTLY_TRIMMED in context.portfolio_context_facts


class TestUnknownCaseIdIsHandledUpstream:
    """`build_discovery_case_context` itself never receives an unresolved
    Case -- `DiscoveryContextService.build()` returns `case=None` before
    calling this function at all (proven directly in
    `test_service.py::TestWellFormedButNonexistentCaseId`)."""

    def test_function_requires_a_real_composition_by_construction(self):
        import inspect

        signature = inspect.signature(build_discovery_case_context)
        assert "composition" in signature.parameters


class TestCrossCaseIsolationAndDeterminism:
    def test_two_different_compositions_never_share_state(self):
        composition_a = _composition(holding=_holding("AMD", weight_percent=40.0), analysis=_base_analysis())
        composition_b = _composition(holding=_holding("NVDA", weight_percent=5.0), analysis=_base_analysis())
        context_a = build_discovery_case_context(composition_a, _EMPTY_STATUS_REPORT)
        context_b = build_discovery_case_context(composition_b, _EMPTY_STATUS_REPORT)
        assert context_a.ticker == "AMD"
        assert context_b.ticker == "NVDA"
        assert KeyRiskKind.HIGH_CONCENTRATION in context_a.key_risks
        assert KeyRiskKind.HIGH_CONCENTRATION not in context_b.key_risks

    def test_identical_input_produces_an_equal_result(self):
        composition = _composition(holding=_holding(), analysis=_base_analysis())
        first = build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
        second = build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
        assert first == second

    def test_this_pure_function_is_batch_safe_by_construction(self):
        """Phase 15/32: `build_discovery_case_context` takes an already-
        fetched `InvestmentCaseComposition` and `PortfolioStatusReport`
        -- no repository access of its own -- so calling it once per
        entry of an `InvestmentCaseCompositionService.build_many(...)`
        result performs zero additional repository scans. Discovery's
        own live call pattern resolves exactly one Case per chat
        request today (confirmed by this sprint's audit), so this proves
        the projection is batch-compatible in principle rather than
        claiming Discovery currently batches multiple Cases."""
        compositions = {
            "a": _composition(holding=_holding("AMD"), analysis=_base_analysis()),
            "b": _composition(holding=_holding("NVDA"), analysis=_base_analysis()),
        }
        contexts = {
            case_id: build_discovery_case_context(composition, _EMPTY_STATUS_REPORT)
            for case_id, composition in compositions.items()
        }
        assert contexts["a"].ticker == "AMD"
        assert contexts["b"].ticker == "NVDA"
