"""Orchestration for Decision Readiness (Deliverable 3/6/7/9/10/11).
The only part of this package that performs I/O.

**Reuses five already-computed engines, recomputes nothing.** Coverage
level and Confidence come straight off `CanonicalAnalysis
.analysis_coverage.level` and `Stance.confidence` (Stance's own
`confidence` field is already a verbatim copy of `CoverageAssessment
.overall_confidence` -- see `atlas.alpha.stance.models.Stance`'s own
docstring); Decision Support comes from `atlas.alpha.decision_support
.describe_recommendation`; Monitoring's operational state comes from
`MonitoringService.freshness_for_case` (Sprint 7/8/9, unmodified);
"conflicting evidence"/"critical dependency"/"missing thesis evidence"
come from `EvidenceGraphService.build_for_case` (Sprint 10, unmodified)
-- a `contradicting_evidence`-kind `FINDING` node, a `CRITICAL
_DEPENDENCY` weak dependency, and `NO_SUPPORT` weak dependencies,
respectively. See this package's own `__init__.py` for the full audit
this reuse is based on.

**Always computed live**, the same choice `atlas.alpha.evidence_graph`/
`coverage`/`stance`/`portfolio_fit` already make -- one Case's own
already-small signal set is cheap enough to recompute on every read.
The one persisted table (`decision_readiness_result_table`) exists
solely so the *previous* computation can be read back for change
detection (Deliverable 10/11); it is never consulted to decide the
current status.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.case_membership import known_cases, resolve_case_id_for_ticker
from atlas.alpha.decision_readiness.engine import (
    ReadinessInputs,
    compare_readiness,
    derive_decision_readiness,
    detect_blockers,
    detect_readiness_change,
    detect_supporting_reasons,
    summarize_readiness,
)
from atlas.alpha.decision_readiness.models import (
    DecisionReadiness,
    DecisionReadinessChange,
    DecisionReadinessComparison,
    DecisionReadinessStatus,
    DecisionReadinessSummary,
)
from atlas.alpha.decision_readiness.repository import SqlAlchemyDecisionReadinessResultRepository
from atlas.alpha.decision_support import describe_recommendation
from atlas.alpha.evidence_graph.models import GraphNodeKind, WeaknessKind
from atlas.alpha.evidence_graph.service import EvidenceGraphService
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.monitoring.service import MonitoringService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.stance.service import StanceService
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.analysis_engine.findings import FindingKind

__all__ = ["DecisionReadinessService"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DecisionReadinessService:
    def __init__(
        self,
        composition_service: InvestmentCaseCompositionService,
        stance_service: StanceService,
        monitoring_service: MonitoringService,
        evidence_graph_service: EvidenceGraphService,
        result_repository: SqlAlchemyDecisionReadinessResultRepository,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
    ) -> None:
        self._composition_service = composition_service
        self._stance_service = stance_service
        self._monitoring_service = monitoring_service
        self._evidence_graph_service = evidence_graph_service
        self._result_repository = result_repository
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store

    def _build_inputs(self, case_id: str) -> ReadinessInputs | None:
        composition = self._composition_service.build(case_id)
        if composition is None:
            return None

        stance = self._stance_service.assess_for_case(case_id)
        freshness = self._monitoring_service.freshness_for_case(case_id)
        built_graph = self._evidence_graph_service.build_for_case(case_id)

        has_conflicting_evidence_finding = False
        no_support_finding_count = 0
        has_critical_dependency = False
        if built_graph is not None:
            has_conflicting_evidence_finding = any(
                node.kind is GraphNodeKind.FINDING and node.details.get("kind") == FindingKind.CONTRADICTING_EVIDENCE.value
                for node in built_graph.graph.nodes
            )
            no_support_finding_count = sum(
                1 for w in built_graph.weak_dependencies if w.kind is WeaknessKind.NO_SUPPORT
            )
            has_critical_dependency = any(
                w.kind is WeaknessKind.CRITICAL_DEPENDENCY for w in built_graph.weak_dependencies
            )

        return ReadinessInputs(
            coverage_level=composition.canonical_analysis.analysis_coverage.level,
            confidence_level=stance.confidence if stance is not None else None,
            decision_support_level=describe_recommendation(composition.canonical_analysis.recommendation).level,
            valuation_support_status=composition.canonical_analysis.valuation_support.status,
            valuation_support_gap=composition.canonical_analysis.valuation_support.gap,
            stance_level=stance.level if stance is not None else None,
            observation_count=len(composition.observation_history),
            has_conflicting_evidence_finding=has_conflicting_evidence_finding,
            no_support_finding_count=no_support_finding_count,
            has_critical_dependency=has_critical_dependency,
            is_monitoring_pending=freshness.is_pending,
            last_monitored_at=freshness.last_monitored_at,
            last_run_failed_for_case=freshness.last_run_failed_for_case,
            data_freshness_status=freshness.data_freshness_status,
        )

    def assess_for_case(self, case_id: str, *, ticker: str | None = None) -> DecisionReadiness | None:
        """`None` only when `case_id` does not resolve to a real Case
        -- the same honest-absence contract every sibling Alpha
        service already uses."""
        inputs = self._build_inputs(case_id)
        if inputs is None:
            return None

        status = derive_decision_readiness(inputs)
        readiness = DecisionReadiness(
            case_id=case_id,
            status=status,
            blockers=detect_blockers(inputs),
            supporting_reasons=detect_supporting_reasons(inputs),
            generated_at=_utc_now(),
        )
        self._result_repository.upsert(readiness, ticker=ticker)
        return readiness

    def assess_for_ticker(self, ticker: str) -> DecisionReadiness | None:
        case_id = resolve_case_id_for_ticker(ticker, self._portfolio_store, self._watchlist_store)
        if case_id is None:
            return None
        return self.assess_for_case(case_id, ticker=ticker)

    def summary_for_case(self, case_id: str, *, ticker: str | None = None) -> DecisionReadinessSummary | None:
        readiness = self.assess_for_case(case_id, ticker=ticker)
        return summarize_readiness(readiness) if readiness is not None else None

    def change_for_case(self, case_id: str, *, ticker: str | None = None) -> DecisionReadinessChange | None:
        """Deliverable 10/11 -- reads the cache *before* this call's
        own fresh computation overwrites it, exactly the same before/
        after ordering `InvestmentCaseCompositionService._assemble`
        already uses for `ChangeIntelligence`."""
        previous = self._result_repository.get(case_id)
        current = self.assess_for_case(case_id, ticker=ticker)
        if current is None:
            return None
        return detect_readiness_change(previous, current, detected_at=current.generated_at)

    def compare(self, ticker_a: str, ticker_b: str) -> DecisionReadinessComparison | None:
        readiness_a = self.assess_for_ticker(ticker_a)
        readiness_b = self.assess_for_ticker(ticker_b)
        if readiness_a is None or readiness_b is None:
            return None
        return compare_readiness(readiness_a, readiness_b)

    def assess_for_known_cases(self) -> dict[str, DecisionReadiness]:
        """Deliverable 7/8 (Portfolio/Discovery) -- every Portfolio/
        Watchlist Case's own readiness, same scope every sibling
        service already uses for "every known company.\""""
        result: dict[str, DecisionReadiness] = {}
        for case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            readiness = self.assess_for_case(case_id, ticker=ticker)
            if readiness is not None:
                result[case_id] = readiness
        return result

    def portfolio_breakdown(self) -> dict[DecisionReadinessStatus, tuple[str, ...]]:
        """Deliverable 7 -- "reuse existing Portfolio UI, never create a
        second prioritization system": tickers grouped by status only,
        in Portfolio's own existing holdings order, never re-sorted or
        re-ranked by this package."""
        portfolio_state = self._portfolio_store.get()
        holdings = portfolio_state.holdings if portfolio_state is not None else ()
        buckets: dict[DecisionReadinessStatus, list[str]] = {status: [] for status in DecisionReadinessStatus}
        for holding in holdings:
            if holding.case_id is None:
                continue
            readiness = self.assess_for_case(holding.case_id, ticker=holding.ticker)
            if readiness is not None:
                buckets[readiness.status].append(holding.ticker)
        return {status: tuple(tickers) for status, tickers in buckets.items()}
