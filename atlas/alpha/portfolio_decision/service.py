"""Orchestration for Portfolio Decision Synthesis. The only part of
this package that performs I/O.

**Reuses five already-computed services, recomputes nothing.**
`InvestmentDecisionService.synthesize_for_case` (Sprint 1),
`DecisionReliabilityService.assess_for_case` (Sprint 7),
`OpportunityCostService.assess_for_case` (Sprint 4),
`PortfolioFitService.assess_for_case` (Atlas Alpha Portfolio Fit),
`PortfolioIntelligenceService.build_report` (Atlas Intelligence Sprint
16), and `atlas.alpha.portfolio.projection.derive_portfolio_view`
(pure function, Atlas Alpha Portfolio) -- all unmodified. See this
package's own `__init__.py` for the full audit this reuse is based on.

**Always computed live**, the same choice every sibling Decision Layer
service already makes. The one persisted table exists solely so the
*previous* computation can be read back for change detection.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.case_membership import known_cases, resolve_case_id_for_ticker
from atlas.alpha.decision_reliability.service import DecisionReliabilityService
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from atlas.alpha.opportunity_cost.service import OpportunityCostService
from atlas.alpha.portfolio.projection import derive_portfolio_view
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_decision.engine import (
    build_portfolio_decision,
    build_portfolio_synthesis_breakdown,
    compare_portfolio_decisions,
    detect_portfolio_decision_change,
    summarize_portfolio_decision,
)
from atlas.alpha.portfolio_decision.models import (
    PortfolioDecision,
    PortfolioDecisionChange,
    PortfolioDecisionComparison,
    PortfolioDecisionSummary,
    PortfolioSynthesisBreakdown,
)
from atlas.alpha.portfolio_decision.repository import SqlAlchemyPortfolioDecisionResultRepository
from atlas.alpha.portfolio_fit.models import FitDimensionKind
from atlas.alpha.portfolio_fit.service import PortfolioFitService
from atlas.alpha.portfolio_intelligence.models import KeyFindingKind
from atlas.alpha.portfolio_intelligence.service import PortfolioIntelligenceService
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.domains.portfolio.models import ConcentrationLevel

__all__ = ["PortfolioDecisionService"]

_CONCENTRATION_KEY_FINDINGS = frozenset({KeyFindingKind.HIGH_CONCENTRATION, KeyFindingKind.ELEVATED_CONCENTRATION})


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PortfolioDecisionService:
    def __init__(
        self,
        investment_decision_service: InvestmentDecisionService,
        decision_reliability_service: DecisionReliabilityService,
        opportunity_cost_service: OpportunityCostService,
        portfolio_fit_service: PortfolioFitService,
        portfolio_intelligence_service: PortfolioIntelligenceService,
        result_repository: SqlAlchemyPortfolioDecisionResultRepository,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
    ) -> None:
        self._investment_decision_service = investment_decision_service
        self._decision_reliability_service = decision_reliability_service
        self._opportunity_cost_service = opportunity_cost_service
        self._portfolio_fit_service = portfolio_fit_service
        self._portfolio_intelligence_service = portfolio_intelligence_service
        self._result_repository = result_repository
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store

    def _ticker_for_case(self, case_id: str) -> str | None:
        for known_case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            if known_case_id == case_id:
                return ticker
        return None

    def assess_for_case(self, case_id: str, *, ticker: str | None = None) -> PortfolioDecision | None:
        """`None` only when `case_id` does not resolve to a real Case
        or a real Investment Decision -- the same honest-absence
        contract every sibling Decision Layer service already uses."""
        resolved_ticker = ticker if ticker is not None else self._ticker_for_case(case_id)

        decision = self._investment_decision_service.synthesize_for_case(case_id, ticker=resolved_ticker)
        if decision is None:
            return None
        reliability = self._decision_reliability_service.assess_for_case(case_id, ticker=resolved_ticker)
        if reliability is None:
            return None
        opportunity_cost = self._opportunity_cost_service.assess_for_case(case_id, ticker=resolved_ticker)
        if opportunity_cost is None:
            return None

        portfolio_state = self._portfolio_store.get()
        is_existing_holding = False
        current_weight_percent: float | None = None
        is_largest_position = False
        portfolio_concentration_level = ConcentrationLevel.LOW
        if portfolio_state is not None and resolved_ticker is not None:
            summary = derive_portfolio_view(portfolio_state)
            portfolio_concentration_level = summary.concentration.level
            is_largest_position = summary.largest_holding is not None and summary.largest_holding.ticker == resolved_ticker
            for holding in portfolio_state.holdings:
                if holding.ticker == resolved_ticker:
                    is_existing_holding = True
                    current_weight_percent = holding.weight_percent
                    break

        fit_assessment = self._portfolio_fit_service.assess_for_case(case_id)
        allocation_rating = None
        if fit_assessment is not None:
            for dimension in fit_assessment.dimensions:
                if dimension.kind is FitDimensionKind.ALLOCATION:
                    allocation_rating = dimension.rating
                    break

        intelligence_report = self._portfolio_intelligence_service.build_report()
        concentration_findings_for_ticker = tuple(
            f.kind
            for f in intelligence_report.key_findings
            if f.kind in _CONCENTRATION_KEY_FINDINGS and resolved_ticker is not None and resolved_ticker in f.tickers
        )
        large_unallocated = any(f.kind is KeyFindingKind.LARGE_UNALLOCATED for f in intelligence_report.key_findings)

        result = build_portfolio_decision(
            case_id,
            action=decision.action,
            reliability_level=reliability.level,
            is_existing_holding=is_existing_holding,
            current_weight_percent=current_weight_percent,
            is_largest_position=is_largest_position,
            allocation_rating=allocation_rating,
            portfolio_concentration_level=portfolio_concentration_level,
            concentration_findings_for_ticker=concentration_findings_for_ticker,
            large_unallocated=large_unallocated,
            alternatives=tuple(t.alternative for t in opportunity_cost.tradeoffs),
            generated_at=_utc_now(),
        )
        self._result_repository.upsert(result, ticker=resolved_ticker)
        return result

    def assess_for_ticker(self, ticker: str) -> PortfolioDecision | None:
        case_id = resolve_case_id_for_ticker(ticker, self._portfolio_store, self._watchlist_store)
        if case_id is None:
            return None
        return self.assess_for_case(case_id, ticker=ticker)

    def summary_for_case(self, case_id: str, *, ticker: str | None = None) -> PortfolioDecisionSummary | None:
        decision = self.assess_for_case(case_id, ticker=ticker)
        return summarize_portfolio_decision(decision) if decision is not None else None

    def change_for_case(self, case_id: str, *, ticker: str | None = None) -> PortfolioDecisionChange | None:
        """Reads the cache *before* this call's own fresh computation
        overwrites it."""
        previous = self._result_repository.get(case_id)
        current = self.assess_for_case(case_id, ticker=ticker)
        if current is None:
            return None
        return detect_portfolio_decision_change(previous, current, detected_at=current.generated_at)

    def compare(self, ticker_a: str, ticker_b: str) -> PortfolioDecisionComparison | None:
        case_id_a = resolve_case_id_for_ticker(ticker_a, self._portfolio_store, self._watchlist_store)
        case_id_b = resolve_case_id_for_ticker(ticker_b, self._portfolio_store, self._watchlist_store)
        if case_id_a is None or case_id_b is None:
            return None
        decision_a = self.assess_for_case(case_id_a, ticker=ticker_a)
        decision_b = self.assess_for_case(case_id_b, ticker=ticker_b)
        if decision_a is None or decision_b is None:
            return None
        return compare_portfolio_decisions(decision_a, decision_b)

    def portfolio_synthesis_breakdown(self) -> PortfolioSynthesisBreakdown:
        """Deliverable 8 -- holdings-only scope, the same scope every
        sibling Decision Layer service already uses. Never re-ranked."""
        portfolio_state = self._portfolio_store.get()
        holdings = portfolio_state.holdings if portfolio_state is not None else ()
        items: list[tuple[str, PortfolioDecision]] = []
        for holding in holdings:
            if holding.case_id is None:
                continue
            decision = self.assess_for_case(holding.case_id, ticker=holding.ticker)
            if decision is None:
                continue
            items.append((holding.ticker, decision))
        return build_portfolio_synthesis_breakdown(tuple(items))
