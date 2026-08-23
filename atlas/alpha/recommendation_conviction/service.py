"""Orchestration for Recommendation Conviction & Strength. The only
part of this package that performs I/O.

**Reuses four already-computed engines, recomputes nothing.**
`InvestmentDecisionService.synthesize_for_case` (Sprint 1, unmodified --
the action this conviction is *about*), `DecisionReadinessService
.assess_for_case` (Sprint 11, unmodified -- status/blockers/supporting
reasons), `InvestmentCaseCompositionService.build` (unmodified --
`canonical_analysis.conviction`, the primary existing "how strong is
the analysis" signal, and `is_thesis_stale`), and `EvidenceGraphService
.build_for_case` (Sprint 10, unmodified -- `weak_dependencies`). See
this package's own `__init__.py` for the full audit this reuse is
based on.

**Always computed live**, the same choice every sibling Alpha service
in the Decision Layer already makes. The one persisted table exists
solely so the *previous* computation can be read back for change
detection; it is never consulted to decide the current conviction.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.case_membership import known_cases, resolve_case_id_for_ticker
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.evidence_graph.models import WeaknessKind
from atlas.alpha.evidence_graph.service import EvidenceGraphService
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from atlas.alpha.recommendation_conviction.engine import (
    ConvictionInputs,
    build_conviction,
    build_portfolio_conviction_breakdown,
    compare_convictions,
    detect_conviction_change,
    summarize_conviction,
)
from atlas.alpha.recommendation_conviction.models import (
    ConvictionChange,
    ConvictionComparison,
    ConvictionSummary,
    PortfolioConvictionBreakdown,
    RecommendationConviction,
)
from atlas.alpha.recommendation_conviction.repository import SqlAlchemyRecommendationConvictionResultRepository
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["RecommendationConvictionService"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RecommendationConvictionService:
    def __init__(
        self,
        composition_service: InvestmentCaseCompositionService,
        decision_readiness_service: DecisionReadinessService,
        investment_decision_service: InvestmentDecisionService,
        evidence_graph_service: EvidenceGraphService,
        result_repository: SqlAlchemyRecommendationConvictionResultRepository,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
    ) -> None:
        self._composition_service = composition_service
        self._decision_readiness_service = decision_readiness_service
        self._investment_decision_service = investment_decision_service
        self._evidence_graph_service = evidence_graph_service
        self._result_repository = result_repository
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store

    def _build_inputs(self, case_id: str, *, ticker: str | None) -> ConvictionInputs | None:
        composition = self._composition_service.build(case_id)
        if composition is None:
            return None

        decision = self._investment_decision_service.synthesize_for_case(case_id, ticker=ticker)
        if decision is None:
            return None

        readiness = self._decision_readiness_service.assess_for_case(case_id)
        if readiness is None:
            return None

        graph = self._evidence_graph_service.build_for_case(case_id)
        weak_kinds = {d.kind for d in graph.weak_dependencies} if graph is not None else set()
        weak_dependency_kinds = tuple(kind for kind in WeaknessKind if kind in weak_kinds)

        return ConvictionInputs(
            action=decision.action,
            readiness_status=readiness.status,
            readiness_blockers=readiness.blockers,
            readiness_supporting_reasons=readiness.supporting_reasons,
            analysis_conviction=composition.canonical_analysis.conviction,
            weak_dependency_kinds=weak_dependency_kinds,
            is_thesis_stale=composition.is_thesis_stale,
        )

    def assess_for_case(self, case_id: str, *, ticker: str | None = None) -> RecommendationConviction | None:
        """`None` only when `case_id` does not resolve to a real Case
        or a real Investment Decision -- the same honest-absence
        contract every sibling Decision Layer service already uses."""
        inputs = self._build_inputs(case_id, ticker=ticker)
        if inputs is None:
            return None

        conviction = build_conviction(case_id, inputs, generated_at=_utc_now())
        self._result_repository.upsert(conviction, ticker=ticker)
        return conviction

    def assess_for_ticker(self, ticker: str) -> RecommendationConviction | None:
        case_id = resolve_case_id_for_ticker(ticker, self._portfolio_store, self._watchlist_store)
        if case_id is None:
            return None
        return self.assess_for_case(case_id, ticker=ticker)

    def summary_for_case(self, case_id: str, *, ticker: str | None = None) -> ConvictionSummary | None:
        conviction = self.assess_for_case(case_id, ticker=ticker)
        return summarize_conviction(conviction) if conviction is not None else None

    def change_for_case(self, case_id: str, *, ticker: str | None = None) -> ConvictionChange | None:
        """Reads the cache *before* this call's own fresh computation
        overwrites it."""
        previous = self._result_repository.get(case_id)
        current = self.assess_for_case(case_id, ticker=ticker)
        if current is None:
            return None
        return detect_conviction_change(previous, current, detected_at=current.generated_at)

    def compare(self, ticker_a: str, ticker_b: str) -> ConvictionComparison | None:
        conviction_a = self.assess_for_ticker(ticker_a)
        conviction_b = self.assess_for_ticker(ticker_b)
        if conviction_a is None or conviction_b is None:
            return None
        return compare_convictions(conviction_a, conviction_b)

    def assess_for_known_cases(self) -> dict[str, RecommendationConviction]:
        """Every Portfolio/Watchlist Case's own conviction, the same
        "every known company" scope every sibling service already
        uses."""
        result: dict[str, RecommendationConviction] = {}
        for case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            conviction = self.assess_for_case(case_id, ticker=ticker)
            if conviction is not None:
                result[case_id] = conviction
        return result

    def portfolio_conviction_breakdown(self) -> PortfolioConvictionBreakdown:
        """Deliverable 7 -- holdings-only scope, the same scope Sprint
        1's own `portfolio_action_distribution` already uses. Never
        re-ranked, never turned into an allocation suggestion."""
        portfolio_state = self._portfolio_store.get()
        holdings = portfolio_state.holdings if portfolio_state is not None else ()
        items: list[tuple[str, RecommendationConviction]] = []
        for holding in holdings:
            if holding.case_id is None:
                continue
            conviction = self.assess_for_case(holding.case_id, ticker=holding.ticker)
            if conviction is not None:
                items.append((holding.ticker, conviction))
        return build_portfolio_conviction_breakdown(tuple(items))
