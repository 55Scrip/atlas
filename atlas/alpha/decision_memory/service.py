"""Orchestration for Decision Memory. The only part of this package
that performs I/O.

**Reuses four already-computed engines, recomputes nothing.**
`InvestmentDecisionService.synthesize_for_case` (Sprint 1),
`DecisionReadinessService.assess_for_case` (Sprint 11),
`RecommendationConvictionService.assess_for_case` (Sprint 2),
`DecisionPathService.build_for_case` (Sprint 3), and
`OpportunityCostService.assess_for_case` (Sprint 4) -- every one
unmodified. See this package's own `__init__.py` for the full audit
this reuse is based on.

**Every read appends, idempotently.** Unlike every prior Decision
Layer sprint's own "one row, always overwritten" cache table, this
service's own repository is append-only (mirrors `atlas.alpha
.investment_case_change`'s own established discipline): `assess_for_case`
always builds the current snapshot fresh, then calls `repository.add`
unconditionally -- a structurally-unchanged snapshot is silently a
no-op (idempotent by `content_hash`), a real change is a new,
permanent row. History is never rewritten, never pruned.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.case_membership import known_cases, resolve_case_id_for_ticker
from atlas.alpha.decision_memory.engine import (
    DecisionSnapshotInputs,
    build_decision_memory,
    build_portfolio_decision_memory_breakdown,
    build_snapshot,
    compare_decision_memories,
    detect_decision_change,
)
from atlas.alpha.decision_memory.models import (
    DecisionMemoryChange,
    DecisionMemory,
    DecisionMemoryComparison,
    DecisionTimeline,
    PortfolioDecisionMemoryBreakdown,
)
from atlas.alpha.decision_memory.repository import SqlAlchemyDecisionMemoryRepository
from atlas.alpha.decision_path.service import DecisionPathService
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from atlas.alpha.opportunity_cost.service import OpportunityCostService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.recommendation_conviction.service import RecommendationConvictionService
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["DecisionMemoryService"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DecisionMemoryService:
    def __init__(
        self,
        investment_decision_service: InvestmentDecisionService,
        decision_readiness_service: DecisionReadinessService,
        recommendation_conviction_service: RecommendationConvictionService,
        decision_path_service: DecisionPathService,
        opportunity_cost_service: OpportunityCostService,
        repository: SqlAlchemyDecisionMemoryRepository,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
    ) -> None:
        self._investment_decision_service = investment_decision_service
        self._decision_readiness_service = decision_readiness_service
        self._recommendation_conviction_service = recommendation_conviction_service
        self._decision_path_service = decision_path_service
        self._opportunity_cost_service = opportunity_cost_service
        self._repository = repository
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store

    def _ticker_for_case(self, case_id: str) -> str | None:
        for known_case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            if known_case_id == case_id:
                return ticker
        return None

    def _build_inputs(self, case_id: str, *, ticker: str | None) -> DecisionSnapshotInputs | None:
        decision = self._investment_decision_service.synthesize_for_case(case_id, ticker=ticker)
        if decision is None:
            return None
        readiness = self._decision_readiness_service.assess_for_case(case_id)
        if readiness is None:
            return None
        conviction = self._recommendation_conviction_service.assess_for_case(case_id, ticker=ticker)
        if conviction is None:
            return None
        path = self._decision_path_service.build_for_case(case_id, ticker=ticker)
        if path is None:
            return None
        opportunity_cost = self._opportunity_cost_service.assess_for_case(case_id, ticker=ticker)
        if opportunity_cost is None:
            return None

        primary_alternative = opportunity_cost.tradeoffs[0].alternative if opportunity_cost.tradeoffs else None

        return DecisionSnapshotInputs(
            action=decision.action,
            readiness_status=readiness.status,
            blocker_codes=tuple(b.kind.value for b in readiness.blockers),
            conviction_strength=conviction.strength,
            conviction_stability=conviction.stability,
            decision_path_step_count=len(path.steps),
            decision_path_final_state=path.final_reachable_state,
            primary_alternative_kind=primary_alternative.kind if primary_alternative is not None else None,
            alternative_count=len(opportunity_cost.tradeoffs),
        )

    def _record_current_snapshot(self, case_id: str, *, ticker: str | None) -> DecisionMemoryChange | None:
        """Builds the current snapshot fresh and appends it if -- and
        only if -- it is structurally different from the current head.
        Returns the `DecisionMemoryChange` that was just persisted only when
        a *new* row was actually written this call, `None` otherwise
        (including when `case_id` doesn't resolve, or nothing changed)
        -- the same "no event, no timestamp" contract every sibling
        Decision Layer service already uses."""
        inputs = self._build_inputs(case_id, ticker=ticker)
        if inputs is None:
            return None
        snapshot = build_snapshot(case_id, inputs, recorded_at=_utc_now())
        previous_head = self._repository.get_latest(case_id)
        change = detect_decision_change(previous_head, snapshot, detected_at=snapshot.recorded_at)
        written = self._repository.add(case_id, snapshot, change, ticker=ticker)
        return change if written else None

    def assess_for_case(self, case_id: str, *, ticker: str | None = None) -> DecisionMemory | None:
        """`None` only when `case_id` does not resolve to a real Case
        or a real Investment Decision -- the same honest-absence
        contract every sibling Decision Layer service already uses."""
        resolved_ticker = ticker if ticker is not None else self._ticker_for_case(case_id)
        self._record_current_snapshot(case_id, ticker=resolved_ticker)

        current_snapshot = self._repository.get_latest(case_id)
        if current_snapshot is None:
            return None
        previous_snapshot = self._repository.get_previous(case_id)
        history_entries = self._repository.get_history(case_id)
        history = DecisionTimeline(case_id=case_id, entries=history_entries)

        latest_change = history_entries[-1].change if history_entries else None
        if latest_change is not None and latest_change.is_baseline:
            latest_change = None

        return build_decision_memory(case_id, current_snapshot, previous_snapshot, latest_change, history)

    def assess_for_ticker(self, ticker: str) -> DecisionMemory | None:
        case_id = resolve_case_id_for_ticker(ticker, self._portfolio_store, self._watchlist_store)
        if case_id is None:
            return None
        return self.assess_for_case(case_id, ticker=ticker)

    def change_for_case(self, case_id: str, *, ticker: str | None = None) -> DecisionMemoryChange | None:
        """`None` unless a *new*, non-baseline snapshot was actually
        appended during this exact call."""
        resolved_ticker = ticker if ticker is not None else self._ticker_for_case(case_id)
        change = self._record_current_snapshot(case_id, ticker=resolved_ticker)
        if change is None or change.is_baseline:
            return None
        return change

    def compare(self, ticker_a: str, ticker_b: str) -> DecisionMemoryComparison | None:
        memory_a = self.assess_for_ticker(ticker_a)
        memory_b = self.assess_for_ticker(ticker_b)
        if memory_a is None or memory_b is None:
            return None
        return compare_decision_memories(memory_a, memory_b)

    def portfolio_decision_memory_breakdown(self) -> PortfolioDecisionMemoryBreakdown:
        """Deliverable 7 -- holdings-only scope, the same scope every
        sibling Decision Layer service already uses. Never re-ranked."""
        portfolio_state = self._portfolio_store.get()
        holdings = portfolio_state.holdings if portfolio_state is not None else ()
        items: list[tuple[str, DecisionMemory]] = []
        for holding in holdings:
            if holding.case_id is None:
                continue
            memory = self.assess_for_case(holding.case_id, ticker=holding.ticker)
            if memory is not None:
                items.append((holding.ticker, memory))
        return build_portfolio_decision_memory_breakdown(tuple(items))
