"""`PortfolioCockpitService` (ATLAS-028 Phase 22) -- the one canonical
Portfolio Cockpit composition owner. See this package's own
`__init__.py` for the full ownership/reuse rationale.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_cockpit.attention import determine_attention
from atlas.alpha.portfolio_cockpit.models import (
    ConvictionLevelCount,
    PortfolioCockpitReport,
    PortfolioHoldingAnalysis,
    UnresolvedHolding,
    ValuationStatusCount,
)
from atlas.alpha.portfolio_cockpit.projection import business_summary, risk_projection, valuation_finding
from atlas.alpha.portfolio_status.service import PortfolioStatusService
from atlas.alpha.portfolio_cockpit.contracts import ReviewPriority
from atlas.analysis_engine.conviction import ConvictionLevel
from atlas.analysis_engine.valuation.contracts import ValuationStatus

__all__ = ["PortfolioCockpitService"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PortfolioCockpitService:
    def __init__(
        self,
        portfolio_store: AlphaPortfolioStore,
        investment_case_composition_service: InvestmentCaseCompositionService,
        portfolio_status_service: PortfolioStatusService,
    ) -> None:
        self._portfolio_store = portfolio_store
        self._investment_case_composition_service = investment_case_composition_service
        self._portfolio_status_service = portfolio_status_service

    def build_report(self) -> PortfolioCockpitReport:
        state = self._portfolio_store.get()
        if state is None or not state.holdings:
            return PortfolioCockpitReport(
                exists=False,
                holdings=(),
                unresolved_holdings=(),
                summary=None,
                conviction_distribution=(),
                valuation_distribution=(),
                priority_review_count=0,
                generated_at=_utc_now(),
            )

        case_ids = tuple(h.case_id for h in state.holdings if h.case_id is not None)
        compositions = self._investment_case_composition_service.build_many(case_ids)

        holdings: list[PortfolioHoldingAnalysis] = []
        unresolved: list[UnresolvedHolding] = []
        for holding in state.holdings:
            composition = compositions.get(holding.case_id) if holding.case_id is not None else None
            if composition is None:
                unresolved.append(UnresolvedHolding(ticker=holding.ticker, case_id=holding.case_id))
                continue

            analysis = composition.canonical_analysis
            risk_findings = analysis.risk_analysis.findings
            attention = determine_attention(
                weight_percent=holding.weight_percent,
                conviction=analysis.conviction,
                confidence=analysis.confidence,
                risk_findings=risk_findings,
            )
            holdings.append(
                PortfolioHoldingAnalysis(
                    ticker=holding.ticker,
                    case_id=holding.case_id,
                    weight_percent=holding.weight_percent,
                    value_absolute=holding.value_absolute,
                    reconciliation_status=holding.reconciliation_status,
                    conviction=analysis.conviction,
                    valuation=valuation_finding(analysis.valuation_engine),
                    business=business_summary(analysis.business_analysis),
                    risk_projection=risk_projection(analysis.risk_analysis),
                    risk_findings=risk_findings,
                    confidence=analysis.confidence,
                    is_thesis_stale=composition.is_thesis_stale,
                    attention=attention,
                )
            )

        # Portfolio-wide facts are never recomputed here -- reused by
        # reference from PortfolioStatusService's own, already-real
        # concentration/unallocated/holdings-count computation.
        status_report = self._portfolio_status_service.build_report()

        conviction_counts = Counter(h.conviction.level for h in holdings)
        valuation_counts = Counter(h.valuation.status for h in holdings)

        return PortfolioCockpitReport(
            exists=True,
            holdings=tuple(holdings),
            unresolved_holdings=tuple(unresolved),
            summary=status_report.summary,
            conviction_distribution=tuple(
                ConvictionLevelCount(level=level, count=conviction_counts[level]) for level in ConvictionLevel
            ),
            valuation_distribution=tuple(
                ValuationStatusCount(status=status, count=valuation_counts[status]) for status in ValuationStatus
            ),
            priority_review_count=sum(
                1 for h in holdings if h.attention.priority is ReviewPriority.PRIORITY_REVIEW
            ),
            generated_at=_utc_now(),
        )
