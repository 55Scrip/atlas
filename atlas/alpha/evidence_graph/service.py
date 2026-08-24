"""Orchestration for the Evidence Graph (Deliverable 3/6/7/8/9). The
only part of this package that performs I/O.

Always computed live, never cached -- the same choice `atlas.alpha
.coverage`/`atlas.alpha.stance`/`atlas.alpha.portfolio_fit` already
make for a per-Case assessment this cheap (one Case's own already-small
Decision/Observation/Evidence/CaseCondition/Assumption/Finding set).
No new read-model table, no Recompute-vs-Ingestion question to answer
this sprint -- unlike Monitoring, nothing here is expensive enough to
need incremental recomputation."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from atlas.alpha.case_membership import known_cases, resolve_case_id_for_ticker
from atlas.alpha.evidence_graph.engine import build_evidence_graph, compute_impact_summary, detect_weak_dependencies
from atlas.alpha.evidence_graph.models import (
    EvidenceGraph,
    EvidenceGraphComparison,
    EvidenceGraphComparisonSide,
    GraphNodeKind,
    ImpactedChange,
    WeakDependency,
    WeaknessKind,
)
from atlas.alpha.evidence_graph.portfolio import PortfolioSharedWeakPoints, find_shared_weak_points
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.core.application.assumption.assumption_service import AssumptionService
from atlas.core.application.case_condition.case_condition_service import CaseConditionService
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.evidence.repository import EvidenceRepository

__all__ = ["EvidenceGraphService", "CaseEvidenceGraph"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _comparison_side(ticker: str, built: CaseEvidenceGraph) -> EvidenceGraphComparisonSide:
    isolated_observation_ids = {
        w.node_id for w in built.weak_dependencies if w.kind is WeaknessKind.ISOLATED_CHAIN
    }
    observation_count = sum(1 for n in built.graph.nodes if n.kind is GraphNodeKind.OBSERVATION)
    critical_count = sum(1 for w in built.weak_dependencies if w.kind is WeaknessKind.CRITICAL_DEPENDENCY)
    return EvidenceGraphComparisonSide(
        ticker=ticker,
        case_id=built.graph.case_id,
        independent_observation_chains=observation_count - len(isolated_observation_ids),
        critical_dependency_count=critical_count,
        weak_link_count=len(built.weak_dependencies),
    )


class CaseEvidenceGraph:
    """A small, named group -- the graph, its own weak-dependency
    findings, and its own impacted-change summary (Deliverable 10),
    computed together so a caller never has to remember to call all
    three."""

    __slots__ = ("graph", "weak_dependencies", "impacted_changes")

    def __init__(
        self,
        graph: EvidenceGraph,
        weak_dependencies: tuple[WeakDependency, ...],
        impacted_changes: tuple[ImpactedChange, ...] = (),
    ) -> None:
        self.graph = graph
        self.impacted_changes = impacted_changes
        self.weak_dependencies = weak_dependencies


class EvidenceGraphService:
    def __init__(
        self,
        composition_service: InvestmentCaseCompositionService,
        evidence_repository: EvidenceRepository,
        case_condition_service: CaseConditionService,
        assumption_service: AssumptionService,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
    ) -> None:
        self._composition_service = composition_service
        self._evidence_repository = evidence_repository
        self._case_condition_service = case_condition_service
        self._assumption_service = assumption_service
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store
        # Request-scoped memoization (Decision Layer Runtime
        # Verification sprint) -- same pattern and justification as
        # `InvestmentCaseCompositionService._build_cache`: this dict is
        # as request-scoped as the instance itself, so caching by
        # `case_id` changes no observable behavior, only how many times
        # an identical graph is rebuilt within one request. Measured:
        # `build_for_case` was called up to 71 times for one Case within
        # a single `/decision-explanation/{id}` request.
        self._build_for_case_cache: dict[str, CaseEvidenceGraph | None] = {}

    def build_for_case(self, case_id: str) -> CaseEvidenceGraph | None:
        """`None` only when `case_id` does not resolve to a real Case --
        the same honest-absence contract `InvestmentCaseCompositionService
        .build` already uses."""
        if case_id in self._build_for_case_cache:
            return self._build_for_case_cache[case_id]
        result = self._build_for_case_uncached(case_id)
        self._build_for_case_cache[case_id] = result
        return result

    def _build_for_case_uncached(self, case_id: str) -> CaseEvidenceGraph | None:
        composition = self._composition_service.build(case_id)
        if composition is None:
            return None

        observation_ids = {o.id for o in composition.observation_history}
        case_evidence = tuple(e for e in self._evidence_repository.list_all() if e.observation_id in observation_ids)

        typed_case_id = CaseId(value=uuid.UUID(case_id))
        case_conditions = tuple(self._case_condition_service.list_for_case(typed_case_id))
        assumptions = tuple(self._assumption_service.list_for_case(typed_case_id))

        generated_at = _utc_now()
        graph = build_evidence_graph(
            case_id,
            observations=composition.observation_history,
            evidence=case_evidence,
            decisions=composition.decision_history,
            outcomes=composition.outcome_history,
            case_conditions=case_conditions,
            assumptions=assumptions,
            findings=composition.canonical_analysis.findings,
            generated_at=generated_at,
        )
        weak_dependencies = detect_weak_dependencies(graph)
        changes = composition.change_intelligence.changes if composition.change_intelligence is not None else ()
        impacted_changes = compute_impact_summary(graph, changes)
        return CaseEvidenceGraph(graph=graph, weak_dependencies=weak_dependencies, impacted_changes=impacted_changes)

    def build_for_known_cases(self) -> dict[str, CaseEvidenceGraph]:
        """Deliverable 7/9 (Portfolio/Compare) -- every Portfolio/
        Watchlist Case's own graph, same scope `MonitoringService`/
        `PortfolioFitService` already use for "every known company.\""""
        result: dict[str, CaseEvidenceGraph] = {}
        for case_id, _ticker in known_cases(self._portfolio_store, self._watchlist_store):
            built = self.build_for_case(case_id)
            if built is not None:
                result[case_id] = built
        return result

    def build_for_ticker(self, ticker: str) -> CaseEvidenceGraph | None:
        case_id = resolve_case_id_for_ticker(ticker, self._portfolio_store, self._watchlist_store)
        if case_id is None:
            return None
        return self.build_for_case(case_id)

    def compare(self, ticker_a: str, ticker_b: str) -> EvidenceGraphComparison | None:
        """Deliverable 9 -- Compare Integration. `None` only when either
        ticker does not resolve to a real, known Case, the same
        contract `StanceService.compare`/`PortfolioFitService`'s own
        compare already use."""
        built_a = self.build_for_ticker(ticker_a)
        built_b = self.build_for_ticker(ticker_b)
        if built_a is None or built_b is None:
            return None
        return EvidenceGraphComparison(a=_comparison_side(ticker_a, built_a), b=_comparison_side(ticker_b, built_b))

    def portfolio_shared_weak_points(self) -> PortfolioSharedWeakPoints:
        """Deliverable 7 -- Portfolio holdings only (never Watchlist),
        "flera innehav" is holdings language specifically."""
        portfolio_state = self._portfolio_store.get()
        holdings = portfolio_state.holdings if portfolio_state is not None else ()
        graphs_by_case: dict[str, CaseEvidenceGraph] = {}
        ticker_by_case: dict[str, str | None] = {}
        for holding in holdings:
            if holding.case_id is None:
                continue
            built = self.build_for_case(holding.case_id)
            if built is not None:
                graphs_by_case[holding.case_id] = built
                ticker_by_case[holding.case_id] = holding.ticker
        return find_shared_weak_points(graphs_by_case, ticker_by_case)
