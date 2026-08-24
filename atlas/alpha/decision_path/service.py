"""Orchestration for Decision Path & Required Progress. The only part
of this package that performs I/O.

**Reuses four already-computed engines, recomputes nothing.**
`InvestmentDecisionService.synthesize_for_case` (Sprint 1, unmodified --
the action this path is about), `RecommendationConvictionService
.assess_for_case` (Sprint 2, unmodified -- the strength this path is
about), `DecisionReadinessService.assess_for_case` (Sprint 11,
unmodified -- status/blockers/supporting reasons, this path's own
primary input), and `EvidenceGraphService.build_for_case` (Sprint 10,
unmodified -- weak dependencies and their underlying node details, for
the "permanent dependency gap" check). See this package's own
`__init__.py` for the full audit this reuse is based on.

**Always computed live**, the same choice every sibling Decision Layer
service already makes. The one persisted table exists solely so the
*previous* computation can be read back for change detection.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.case_membership import known_cases, resolve_case_id_for_ticker
from atlas.alpha.decision_path.engine import (
    DecisionPathInputs,
    build_decision_path,
    build_portfolio_decision_path_breakdown,
    compare_decision_paths,
    detect_decision_path_change,
    summarize_decision_path,
)
from atlas.alpha.decision_path.models import (
    DecisionPath,
    DecisionPathChange,
    DecisionPathComparison,
    DecisionPathSummary,
    PortfolioDecisionPathBreakdown,
)
from atlas.alpha.decision_path.repository import SqlAlchemyDecisionPathResultRepository
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.evidence_graph.service import EvidenceGraphService
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.recommendation_conviction.service import RecommendationConvictionService
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["DecisionPathService"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DecisionPathService:
    def __init__(
        self,
        investment_decision_service: InvestmentDecisionService,
        recommendation_conviction_service: RecommendationConvictionService,
        decision_readiness_service: DecisionReadinessService,
        evidence_graph_service: EvidenceGraphService,
        result_repository: SqlAlchemyDecisionPathResultRepository,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
    ) -> None:
        self._investment_decision_service = investment_decision_service
        self._recommendation_conviction_service = recommendation_conviction_service
        self._decision_readiness_service = decision_readiness_service
        self._evidence_graph_service = evidence_graph_service
        self._result_repository = result_repository
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store
        # Request-scoped memoization (Decision Layer Runtime
        # Verification sprint) -- same pattern and justification as
        # `InvestmentCaseCompositionService._build_cache`: this dict is
        # as request-scoped as the instance itself, so caching by
        # `case_id` changes no observable behavior, only how many times
        # an identical path -- and its own repository upsert, which a
        # cache hit now also skips -- is repeated within one request.
        # `ticker` is deliberately excluded from the key -- see
        # `recommendation_conviction.service`'s own identical comment
        # for why. Measured: `build_for_case` was called up to 3 times
        # for one Case within a single `/decision-explanation/{id}`
        # request.
        self._build_for_case_cache: dict[str, DecisionPath | None] = {}

    def _build_inputs(self, case_id: str, *, ticker: str | None) -> DecisionPathInputs | None:
        decision = self._investment_decision_service.synthesize_for_case(case_id, ticker=ticker)
        if decision is None:
            return None

        conviction = self._recommendation_conviction_service.assess_for_case(case_id, ticker=ticker)
        if conviction is None:
            return None

        readiness = self._decision_readiness_service.assess_for_case(case_id)
        if readiness is None:
            return None

        graph = self._evidence_graph_service.build_for_case(case_id)
        weak_dependencies = graph.weak_dependencies if graph is not None else ()
        graph_node_details_by_id = {node.id: node.details for node in graph.graph.nodes} if graph is not None else {}

        return DecisionPathInputs(
            action=decision.action,
            strength=conviction.strength,
            readiness_status=readiness.status,
            readiness_blockers=readiness.blockers,
            readiness_supporting_reasons=readiness.supporting_reasons,
            weak_dependencies=weak_dependencies,
            graph_node_details_by_id=graph_node_details_by_id,
        )

    def build_for_case(self, case_id: str, *, ticker: str | None = None) -> DecisionPath | None:
        """`None` only when `case_id` does not resolve to a real Case
        or a real Investment Decision -- the same honest-absence
        contract every sibling Decision Layer service already uses."""
        if case_id in self._build_for_case_cache:
            return self._build_for_case_cache[case_id]
        path = self._build_for_case_uncached(case_id, ticker=ticker)
        self._build_for_case_cache[case_id] = path
        if path is not None:
            self._result_repository.upsert(path, ticker=ticker)
        return path

    def _build_for_case_uncached(self, case_id: str, *, ticker: str | None) -> DecisionPath | None:
        inputs = self._build_inputs(case_id, ticker=ticker)
        if inputs is None:
            return None
        return build_decision_path(case_id, inputs, generated_at=_utc_now())

    def build_for_ticker(self, ticker: str) -> DecisionPath | None:
        case_id = resolve_case_id_for_ticker(ticker, self._portfolio_store, self._watchlist_store)
        if case_id is None:
            return None
        return self.build_for_case(case_id, ticker=ticker)

    def summary_for_case(self, case_id: str, *, ticker: str | None = None) -> DecisionPathSummary | None:
        path = self.build_for_case(case_id, ticker=ticker)
        return summarize_decision_path(path) if path is not None else None

    def change_for_case(self, case_id: str, *, ticker: str | None = None) -> DecisionPathChange | None:
        """Reads the cache *before* this call's own fresh computation
        overwrites it."""
        previous = self._result_repository.get(case_id)
        current = self.build_for_case(case_id, ticker=ticker)
        if current is None:
            return None
        return detect_decision_path_change(previous, current, detected_at=current.generated_at)

    def compare(self, ticker_a: str, ticker_b: str) -> DecisionPathComparison | None:
        path_a = self.build_for_ticker(ticker_a)
        path_b = self.build_for_ticker(ticker_b)
        if path_a is None or path_b is None:
            return None
        return compare_decision_paths(path_a, path_b)

    def build_for_known_cases(self) -> dict[str, DecisionPath]:
        """Every Portfolio/Watchlist Case's own path, the same "every
        known company" scope every sibling service already uses."""
        result: dict[str, DecisionPath] = {}
        for case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            path = self.build_for_case(case_id, ticker=ticker)
            if path is not None:
                result[case_id] = path
        return result

    def portfolio_decision_path_breakdown(self) -> PortfolioDecisionPathBreakdown:
        """Deliverable 7 -- holdings-only scope, the same scope every
        sibling Decision Layer service already uses. Never re-ranked,
        never turned into an allocation suggestion."""
        portfolio_state = self._portfolio_store.get()
        holdings = portfolio_state.holdings if portfolio_state is not None else ()
        items: list[tuple[str, DecisionPath]] = []
        for holding in holdings:
            if holding.case_id is None:
                continue
            path = self.build_for_case(holding.case_id, ticker=holding.ticker)
            if path is not None:
                items.append((holding.ticker, path))
        return build_portfolio_decision_path_breakdown(tuple(items))
