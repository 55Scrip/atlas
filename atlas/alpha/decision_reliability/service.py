"""Orchestration for Decision Reliability. The only part of this
package that performs I/O.

**Reuses three already-computed engines, recomputes nothing.**
`atlas.alpha.coverage.assess_coverage` (Atlas Intelligence Sprint 1,
unmodified -- called the same way `explainability`/`stance` already
call it), `EvidenceQualityService.assess_for_case` (Atlas Intelligence
Sprint 4, unmodified), `DecisionReadinessService.assess_for_case`
(Atlas Intelligence Sprint 11, unmodified). See this package's own
`__init__.py` for the full audit this reuse is based on.

**Always computed live**, the same choice every sibling Decision Layer
service already makes. The one persisted table exists solely so the
*previous* computation can be read back for change detection.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.case_membership import known_cases, resolve_case_id_for_ticker
from atlas.alpha.coverage import assess_coverage
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.decision_reliability.engine import (
    build_decision_reliability,
    build_portfolio_reliability_breakdown,
    compare_decision_reliability,
    detect_reliability_change,
    summarize_decision_reliability,
)
from atlas.alpha.decision_reliability.models import (
    DecisionReliability,
    DecisionReliabilitySummary,
    PortfolioReliabilityBreakdown,
    ReliabilityChange,
    ReliabilityComparison,
)
from atlas.alpha.decision_reliability.repository import SqlAlchemyDecisionReliabilityResultRepository
from atlas.alpha.evidence_quality.service import EvidenceQualityService
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["DecisionReliabilityService"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DecisionReliabilityService:
    def __init__(
        self,
        composition_service: InvestmentCaseCompositionService,
        evidence_quality_service: EvidenceQualityService,
        decision_readiness_service: DecisionReadinessService,
        result_repository: SqlAlchemyDecisionReliabilityResultRepository,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
    ) -> None:
        self._composition_service = composition_service
        self._evidence_quality_service = evidence_quality_service
        self._decision_readiness_service = decision_readiness_service
        self._result_repository = result_repository
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store

    def _ticker_for_case(self, case_id: str) -> str | None:
        for known_case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            if known_case_id == case_id:
                return ticker
        return None

    def assess_for_case(self, case_id: str, *, ticker: str | None = None) -> DecisionReliability | None:
        """`None` only when `case_id` does not resolve to a real Case
        -- the same honest-absence contract every sibling Decision
        Layer service already uses."""
        resolved_ticker = ticker if ticker is not None else self._ticker_for_case(case_id)

        composition = self._composition_service.build(case_id)
        if composition is None:
            return None
        coverage = assess_coverage(composition.canonical_analysis, is_thesis_stale=composition.is_thesis_stale)
        evidence_quality = self._evidence_quality_service.assess_for_case(case_id)
        if evidence_quality is None:
            return None
        readiness = self._decision_readiness_service.assess_for_case(case_id, ticker=resolved_ticker)
        if readiness is None:
            return None

        result = build_decision_reliability(
            case_id, coverage=coverage, evidence_quality=evidence_quality, readiness=readiness, generated_at=_utc_now()
        )
        self._result_repository.upsert(result, ticker=resolved_ticker)
        return result

    def assess_for_ticker(self, ticker: str) -> DecisionReliability | None:
        case_id = resolve_case_id_for_ticker(ticker, self._portfolio_store, self._watchlist_store)
        if case_id is None:
            return None
        return self.assess_for_case(case_id, ticker=ticker)

    def summary_for_case(self, case_id: str, *, ticker: str | None = None) -> DecisionReliabilitySummary | None:
        reliability = self.assess_for_case(case_id, ticker=ticker)
        return summarize_decision_reliability(reliability) if reliability is not None else None

    def change_for_case(self, case_id: str, *, ticker: str | None = None) -> ReliabilityChange | None:
        """Reads the cache *before* this call's own fresh computation
        overwrites it."""
        previous = self._result_repository.get(case_id)
        current = self.assess_for_case(case_id, ticker=ticker)
        if current is None:
            return None
        return detect_reliability_change(previous, current, detected_at=current.generated_at)

    def compare(self, ticker_a: str, ticker_b: str) -> ReliabilityComparison | None:
        case_id_a = resolve_case_id_for_ticker(ticker_a, self._portfolio_store, self._watchlist_store)
        case_id_b = resolve_case_id_for_ticker(ticker_b, self._portfolio_store, self._watchlist_store)
        if case_id_a is None or case_id_b is None:
            return None
        reliability_a = self.assess_for_case(case_id_a, ticker=ticker_a)
        reliability_b = self.assess_for_case(case_id_b, ticker=ticker_b)
        if reliability_a is None or reliability_b is None:
            return None
        return compare_decision_reliability(reliability_a, reliability_b)

    def portfolio_reliability_breakdown(self) -> PortfolioReliabilityBreakdown:
        """Deliverable 8 -- holdings-only scope, the same scope every
        sibling Decision Layer service already uses. Never re-ranked."""
        portfolio_state = self._portfolio_store.get()
        holdings = portfolio_state.holdings if portfolio_state is not None else ()
        items: list[tuple[str, DecisionReliability]] = []
        changes: list[tuple[str, ReliabilityChange | None]] = []
        for holding in holdings:
            if holding.case_id is None:
                continue
            reliability = self.assess_for_case(holding.case_id, ticker=holding.ticker)
            if reliability is None:
                continue
            items.append((holding.ticker, reliability))
            changes.append((holding.ticker, self.change_for_case(holding.case_id, ticker=holding.ticker)))
        return build_portfolio_reliability_breakdown(tuple(items), tuple(changes))
