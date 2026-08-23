"""Orchestration for Decision Explanation & Traceability. The only
part of this package that performs I/O.

**Reuses five already-computed services, recomputes nothing.**
`InvestmentDecisionService.synthesize_for_case` (Sprint 1),
`RecommendationConvictionService.assess_for_case` (Sprint 2),
`DecisionReadinessService` (Atlas Intelligence Sprint 11),
`DecisionPathService.build_for_case` (Sprint 3), `DecisionMemoryService
.assess_for_case` (Sprint 5), and `EvidenceGraphService.build_for_case`
(Atlas Intelligence Sprint 10) -- all unmodified. See this package's
own `__init__.py` for the full audit this reuse is based on.

**Always computed live**, the same choice every sibling Decision Layer
service already makes. The one persisted table exists solely so the
*previous* computation can be read back for change detection.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.case_membership import known_cases, resolve_case_id_for_ticker
from atlas.alpha.decision_explanation.engine import (
    build_decision_explanation,
    build_portfolio_decision_explanation_breakdown,
    compare_decision_explanations,
    detect_decision_explanation_change,
    summarize_decision_explanation,
)
from atlas.alpha.decision_explanation.models import (
    DecisionExplanation,
    DecisionExplanationChange,
    DecisionExplanationComparison,
    DecisionExplanationSummary,
    PortfolioDecisionExplanationBreakdown,
)
from atlas.alpha.decision_explanation.repository import SqlAlchemyDecisionExplanationResultRepository
from atlas.alpha.decision_memory.service import DecisionMemoryService
from atlas.alpha.decision_path.service import DecisionPathService
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.evidence_graph.models import GraphNodeKind
from atlas.alpha.evidence_graph.service import EvidenceGraphService
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.recommendation_conviction.service import RecommendationConvictionService
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["DecisionExplanationService"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DecisionExplanationService:
    def __init__(
        self,
        investment_decision_service: InvestmentDecisionService,
        recommendation_conviction_service: RecommendationConvictionService,
        decision_readiness_service: DecisionReadinessService,
        decision_path_service: DecisionPathService,
        decision_memory_service: DecisionMemoryService,
        evidence_graph_service: EvidenceGraphService,
        result_repository: SqlAlchemyDecisionExplanationResultRepository,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
    ) -> None:
        self._investment_decision_service = investment_decision_service
        self._recommendation_conviction_service = recommendation_conviction_service
        self._decision_readiness_service = decision_readiness_service
        self._decision_path_service = decision_path_service
        self._decision_memory_service = decision_memory_service
        self._evidence_graph_service = evidence_graph_service
        self._result_repository = result_repository
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store

    def _ticker_for_case(self, case_id: str) -> str | None:
        for known_case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            if known_case_id == case_id:
                return ticker
        return None

    def build_for_case(self, case_id: str, *, ticker: str | None = None) -> DecisionExplanation | None:
        """`None` only when `case_id` does not resolve to a real Case
        or a real Investment Decision -- the same honest-absence
        contract every sibling Decision Layer service already uses."""
        resolved_ticker = ticker if ticker is not None else self._ticker_for_case(case_id)

        decision = self._investment_decision_service.synthesize_for_case(case_id, ticker=resolved_ticker)
        if decision is None:
            return None
        conviction = self._recommendation_conviction_service.assess_for_case(case_id, ticker=resolved_ticker)
        if conviction is None:
            return None
        readiness = self._decision_readiness_service.assess_for_case(case_id, ticker=resolved_ticker)
        if readiness is None:
            return None
        path = self._decision_path_service.build_for_case(case_id, ticker=resolved_ticker)
        if path is None:
            return None
        memory = self._decision_memory_service.assess_for_case(case_id, ticker=resolved_ticker)
        latest_snapshot_hash = (
            memory.current_snapshot.content_hash if memory is not None and memory.latest_change is not None else None
        )
        case_evidence_graph = self._evidence_graph_service.build_for_case(case_id)
        weak_dependencies = case_evidence_graph.weak_dependencies if case_evidence_graph is not None else ()
        finding_nodes = (
            tuple(n for n in case_evidence_graph.graph.nodes if n.kind is GraphNodeKind.FINDING)
            if case_evidence_graph is not None
            else ()
        )

        result = build_decision_explanation(
            case_id,
            decision=decision,
            conviction=conviction,
            readiness=readiness,
            path=path,
            latest_snapshot_hash=latest_snapshot_hash,
            weak_dependencies=weak_dependencies,
            finding_nodes=finding_nodes,
            generated_at=_utc_now(),
        )
        self._result_repository.upsert(result, ticker=resolved_ticker)
        return result

    def build_for_ticker(self, ticker: str) -> DecisionExplanation | None:
        case_id = resolve_case_id_for_ticker(ticker, self._portfolio_store, self._watchlist_store)
        if case_id is None:
            return None
        return self.build_for_case(case_id, ticker=ticker)

    def summary_for_case(self, case_id: str, *, ticker: str | None = None) -> DecisionExplanationSummary | None:
        explanation = self.build_for_case(case_id, ticker=ticker)
        return summarize_decision_explanation(explanation) if explanation is not None else None

    def change_for_case(self, case_id: str, *, ticker: str | None = None) -> DecisionExplanationChange | None:
        """Reads the cache *before* this call's own fresh computation
        overwrites it."""
        previous = self._result_repository.get(case_id)
        current = self.build_for_case(case_id, ticker=ticker)
        if current is None:
            return None
        return detect_decision_explanation_change(previous, current, detected_at=current.generated_at)

    def compare(self, ticker_a: str, ticker_b: str) -> DecisionExplanationComparison | None:
        case_id_a = resolve_case_id_for_ticker(ticker_a, self._portfolio_store, self._watchlist_store)
        case_id_b = resolve_case_id_for_ticker(ticker_b, self._portfolio_store, self._watchlist_store)
        if case_id_a is None or case_id_b is None:
            return None
        explanation_a = self.build_for_case(case_id_a, ticker=ticker_a)
        explanation_b = self.build_for_case(case_id_b, ticker=ticker_b)
        if explanation_a is None or explanation_b is None:
            return None
        return compare_decision_explanations(explanation_a, explanation_b)

    def portfolio_decision_explanation_breakdown(self) -> PortfolioDecisionExplanationBreakdown:
        """Deliverable 7 -- holdings-only scope, the same scope every
        sibling Decision Layer service already uses. Never re-ranked."""
        portfolio_state = self._portfolio_store.get()
        holdings = portfolio_state.holdings if portfolio_state is not None else ()
        items: list[tuple[str, DecisionExplanationChange | None]] = []
        for holding in holdings:
            if holding.case_id is None:
                continue
            change = self.change_for_case(holding.case_id, ticker=holding.ticker)
            items.append((holding.ticker, change))
        return build_portfolio_decision_explanation_breakdown(tuple(items))
