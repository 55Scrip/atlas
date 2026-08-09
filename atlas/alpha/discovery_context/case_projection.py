"""Discovery's own per-Case projection (ATLAS-030) -- the replacement
for `atlas.alpha.case_intelligence.CaseIntelligenceReport` as the shape
Discovery consumes. Built exclusively from `InvestmentCaseComposition`
(ATLAS-027, the same object Portfolio Cockpit and the canonical
Investment Case API already consume) plus `PortfolioStatusService`'s own
already-computed summary/attention items -- never a second
`decision_engine.run_pipeline` call, never a recomputed evaluator.

`KeyRiskKind`/`ConsiderKind`/`PortfolioContextFact` are re-declared here
rather than imported from `case_intelligence` or `portfolio_intelligence`:
this package owns Discovery's own vocabulary now, decoupled from the
legacy compatibility surface (Phase 17's own "no new canonical code
depends on case_intelligence" rule). The member names and semantics are
unchanged from `case_intelligence`'s own taxonomy (Phase 6: "preserve
Discovery behavior unless demonstrably based on stale/fabricated legacy
fields") -- only the underlying data source and, for `PENDING_WORKFLOW`,
the computation itself changes (see `_pending_workflow` below).

Every threshold and category check here is a plain boolean comparison
against already-real data (holding weight, canonical Conviction/
Confidence/Risk/open-questions, Core Decision/Observation/Outcome
counts) -- never a second evaluator, never a weighted score. This is the
same deterministic-projection discipline `atlas.alpha.portfolio_cockpit
.attention` already established.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.alpha.investment_case.models import InvestmentCaseComposition
from atlas.alpha.portfolio.models import ReconciliationStatus
from atlas.alpha.portfolio_intelligence.thresholds import (
    ELEVATED_CONCENTRATION_WEIGHT_PERCENT,
    HIGH_CONCENTRATION_WEIGHT_PERCENT,
)
from atlas.alpha.portfolio_status.models import AttentionCategory, PortfolioStatusReport
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.conviction import ConvictionLevel
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.decision_engine.contracts import EvidenceCoverageLevel, EvidenceGapKind, OpenQuestionKind

__all__ = [
    "KeyRiskKind",
    "ConsiderKind",
    "PortfolioContextFact",
    "DiscoveryCaseContext",
    "build_discovery_case_context",
]


class KeyRiskKind(str, Enum):
    """Same three members `case_intelligence.KeyRiskKind` already had."""

    CONTRADICTING_EVIDENCE = "contradicting_evidence"
    HIGH_CONCENTRATION = "high_concentration"
    AWAITING_RECONCILIATION = "awaiting_reconciliation"


class ConsiderKind(str, Enum):
    """Same four per-Case members `case_intelligence.ConsiderKind` (via
    `portfolio_intelligence.models`) already produced for a held Case."""

    GATHER_EVIDENCE = "gather_evidence"
    REVIEW_THESIS = "review_thesis"
    UPDATE_CASE = "update_case"
    REVIEW_CONCENTRATION = "review_concentration"


class PortfolioContextFact(str, Enum):
    """Same six members `case_intelligence.PortfolioContextFact` already
    had."""

    LARGEST_HOLDING = "largest_holding"
    RECENTLY_INCREASED = "recently_increased"
    RECENTLY_TRIMMED = "recently_trimmed"
    HIGH_CONCENTRATION = "high_concentration"
    PENDING_WORKFLOW = "pending_workflow"
    EVIDENCE_INCOMPLETE = "evidence_incomplete"


#: The three "unfinished chain" categories `case_intelligence`'s own
#: `_pending_workflow_count` re-implemented independently (its own
#: docstring already flagged this as a known duplication). Reusing
#: `PortfolioStatusService`'s own `attention_items` here retires that
#: second implementation rather than porting it forward.
_PENDING_WORKFLOW_CATEGORIES = frozenset(
    {
        AttentionCategory.DECISION_WITHOUT_OUTCOME,
        AttentionCategory.OUTCOME_WITHOUT_EXECUTION,
        AttentionCategory.OBSERVATION_WITHOUT_DECISION,
    }
)


@dataclass(frozen=True)
class DiscoveryCaseContext:
    """The one canonical per-Case shape Discovery consumes. Every field
    is either a direct value from `InvestmentCaseComposition`/
    `CanonicalAnalysis`, or a deterministic threshold/category check over
    that same data plus `PortfolioStatusService`'s own summary -- never a
    recomputed Business/Valuation/Risk/Confidence/Conviction/
    Recommendation conclusion."""

    ticker: str | None
    held: bool
    current_thesis_reason: str | None
    confidence: EvidenceCoverageLevel
    conviction_level: ConvictionLevel
    is_stale: bool
    missing_evidence_kinds: tuple[EvidenceGapKind, ...]
    open_questions: tuple[OpenQuestionKind, ...]
    key_risks: tuple[KeyRiskKind, ...]
    consider_kinds: tuple[ConsiderKind, ...]
    portfolio_context_facts: tuple[PortfolioContextFact, ...]


def _pending_workflow(ticker: str, status_report: PortfolioStatusReport) -> bool:
    return any(
        item.ticker == ticker and item.category in _PENDING_WORKFLOW_CATEGORIES
        for item in status_report.attention_items
    )


def build_discovery_case_context(
    composition: InvestmentCaseComposition,
    status_report: PortfolioStatusReport,
) -> DiscoveryCaseContext:
    analysis = composition.canonical_analysis
    holding = composition.holding_context
    evidence_quality = analysis.business.evidence_quality
    evidence_gaps: tuple[EvidenceGapKind, ...] = (
        tuple(gap.kind for gap in evidence_quality.evidence_gaps) if evidence_quality is not None else ()
    )

    key_risks: list[KeyRiskKind] = []
    thesis_risk = next((f for f in analysis.risk_analysis.findings if f.category is RiskCategory.THESIS_RISK), None)
    if thesis_risk is not None and thesis_risk.status is RiskStatus.HIGH:
        key_risks.append(KeyRiskKind.CONTRADICTING_EVIDENCE)
    if holding is not None and holding.weight_percent >= HIGH_CONCENTRATION_WEIGHT_PERCENT:
        key_risks.append(KeyRiskKind.HIGH_CONCENTRATION)
    if holding is not None and holding.reconciliation_status is ReconciliationStatus.AWAITING_RECONCILIATION:
        key_risks.append(KeyRiskKind.AWAITING_RECONCILIATION)

    pending_workflow = holding is not None and _pending_workflow(holding.ticker, status_report)

    consider_kinds: list[ConsiderKind] = []
    if holding is not None:
        if len(evidence_gaps) > 0:
            consider_kinds.append(ConsiderKind.GATHER_EVIDENCE)
        if composition.is_thesis_stale:
            consider_kinds.append(ConsiderKind.REVIEW_THESIS)
        if pending_workflow:
            consider_kinds.append(ConsiderKind.UPDATE_CASE)
        if holding.weight_percent >= ELEVATED_CONCENTRATION_WEIGHT_PERCENT:
            consider_kinds.append(ConsiderKind.REVIEW_CONCENTRATION)

    portfolio_context_facts: list[PortfolioContextFact] = []
    if holding is not None:
        summary = status_report.summary
        if summary is not None and summary.largest_position_ticker == holding.ticker:
            portfolio_context_facts.append(PortfolioContextFact.LARGEST_HOLDING)
        if holding.weight_percent >= HIGH_CONCENTRATION_WEIGHT_PERCENT:
            portfolio_context_facts.append(PortfolioContextFact.HIGH_CONCENTRATION)
        if pending_workflow:
            portfolio_context_facts.append(PortfolioContextFact.PENDING_WORKFLOW)
        if evidence_quality is not None and evidence_quality.coverage in (
            EvidenceCoverageLevel.NONE,
            EvidenceCoverageLevel.PARTIAL,
        ):
            portfolio_context_facts.append(PortfolioContextFact.EVIDENCE_INCOMPLETE)
        if composition.trade_log:
            # `composition.trade_log` is already scoped to this holding's
            # own ticker by `InvestmentCaseCompositionService` itself.
            latest_trade = max(composition.trade_log, key=lambda t: t.executed_at)
            if latest_trade.transaction_type.value in ("BUY", "ADD"):
                portfolio_context_facts.append(PortfolioContextFact.RECENTLY_INCREASED)
            elif latest_trade.transaction_type.value in ("SELL", "EXIT"):
                portfolio_context_facts.append(PortfolioContextFact.RECENTLY_TRIMMED)

    return DiscoveryCaseContext(
        ticker=holding.ticker if holding is not None else None,
        held=holding is not None,
        current_thesis_reason=composition.current_thesis.latest_decision_reason,
        confidence=analysis.confidence,
        conviction_level=analysis.conviction.level,
        is_stale=composition.is_thesis_stale,
        missing_evidence_kinds=evidence_gaps,
        open_questions=tuple(q.kind for q in analysis.open_questions),
        key_risks=tuple(key_risks),
        consider_kinds=tuple(consider_kinds),
        portfolio_context_facts=tuple(portfolio_context_facts),
    )
