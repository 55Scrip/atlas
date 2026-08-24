"""Orchestration for Investment Decision Synthesis (Deliverable 3/6/7/
9/10/11). The only part of this package that performs I/O.

**Reuses three already-computed engines, recomputes nothing.**
`atlas.alpha.decision_support.describe_recommendation` (Decision
Support -> `DecisionAction`'s own anchor), `DecisionReadinessService
.assess_for_case` (Sprint 11, unmodified -- blockers/supporting
reasons/status), `StanceService.assess_for_case` (unmodified -- the
one supporting reason this engine borrows from Stance). See this
package's own `__init__.py` for the full audit this reuse is based on.

**Always computed live**, the same choice `atlas.alpha.decision_readiness`/
`evidence_graph` already make. The one persisted table exists solely so
the *previous* computation can be read back for change detection
(Deliverable 10/11); it is never consulted to decide the current
decision.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.case_membership import known_cases, resolve_case_id_for_ticker
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.decision_support import describe_recommendation
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_decision.engine import (
    SynthesisInputs,
    compare_decisions,
    detect_decision_change,
    summarize_decision,
    synthesize_decision,
)
from atlas.alpha.investment_decision.models import (
    DecisionAction,
    DecisionChange,
    DecisionComparison,
    DecisionSummary,
    InvestmentDecision,
)
from atlas.alpha.investment_decision.repository import SqlAlchemyInvestmentDecisionResultRepository
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.stance.service import StanceService
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["InvestmentDecisionService"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InvestmentDecisionService:
    def __init__(
        self,
        composition_service: InvestmentCaseCompositionService,
        decision_readiness_service: DecisionReadinessService,
        stance_service: StanceService,
        result_repository: SqlAlchemyInvestmentDecisionResultRepository,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
    ) -> None:
        self._composition_service = composition_service
        self._decision_readiness_service = decision_readiness_service
        self._stance_service = stance_service
        self._result_repository = result_repository
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store
        # Request-scoped memoization (Decision Layer Runtime
        # Verification sprint) -- same pattern and justification as
        # `InvestmentCaseCompositionService._build_cache`: this dict is
        # as request-scoped as the instance itself, so caching by
        # `case_id` changes no observable behavior, only how many times
        # an identical synthesis -- and its own repository upsert,
        # profiling-confirmed the dominant real cost, since every
        # upsert is its own committed transaction under this database's
        # `synchronous=FULL` config -- is repeated within one request.
        # `ticker` is deliberately excluded from the key: it is never
        # read while computing `InvestmentDecision` itself, only passed
        # to the one upsert a cache miss still performs; the repository
        # row it writes is byte-identical on every call within a
        # request regardless of which call triggers it, and no reader
        # anywhere in this codebase looks up a row by its `ticker`
        # column (confirmed by grep), so upserting once per `case_id`
        # instead of once per call changes no observable state.
        # Measured: `synthesize_for_case` was called up to 50 times for
        # one Case within a single `/decision-explanation/{id}` request.
        self._synthesize_for_case_cache: dict[str, InvestmentDecision | None] = {}

    def _build_inputs(self, case_id: str) -> SynthesisInputs | None:
        composition = self._composition_service.build(case_id)
        if composition is None:
            return None

        readiness = self._decision_readiness_service.assess_for_case(case_id)
        if readiness is None:
            return None

        stance = self._stance_service.assess_for_case(case_id)
        decision_support = describe_recommendation(composition.canonical_analysis.recommendation)

        return SynthesisInputs(
            decision_support_level=decision_support.level,
            readiness_status=readiness.status,
            readiness_blockers=readiness.blockers,
            readiness_supporting_reasons=readiness.supporting_reasons,
            stance_level=stance.level if stance is not None else None,
            stance_top_reason_code=stance.reasoning[0].code if stance is not None and stance.reasoning else None,
            is_thesis_stale=composition.is_thesis_stale,
        )

    def synthesize_for_case(self, case_id: str, *, ticker: str | None = None) -> InvestmentDecision | None:
        """`None` only when `case_id` does not resolve to a real Case
        -- the same honest-absence contract every sibling Alpha
        service already uses."""
        if case_id in self._synthesize_for_case_cache:
            return self._synthesize_for_case_cache[case_id]
        decision = self._synthesize_for_case_uncached(case_id)
        self._synthesize_for_case_cache[case_id] = decision
        if decision is not None:
            self._result_repository.upsert(decision, ticker=ticker)
        return decision

    def _synthesize_for_case_uncached(self, case_id: str) -> InvestmentDecision | None:
        inputs = self._build_inputs(case_id)
        if inputs is None:
            return None
        return synthesize_decision(case_id, inputs, generated_at=_utc_now())

    def synthesize_for_ticker(self, ticker: str) -> InvestmentDecision | None:
        case_id = resolve_case_id_for_ticker(ticker, self._portfolio_store, self._watchlist_store)
        if case_id is None:
            return None
        return self.synthesize_for_case(case_id, ticker=ticker)

    def summary_for_case(self, case_id: str, *, ticker: str | None = None) -> DecisionSummary | None:
        decision = self.synthesize_for_case(case_id, ticker=ticker)
        return summarize_decision(decision) if decision is not None else None

    def change_for_case(self, case_id: str, *, ticker: str | None = None) -> DecisionChange | None:
        """Deliverable 10/11 -- reads the cache *before* this call's
        own fresh computation overwrites it."""
        previous = self._result_repository.get(case_id)
        current = self.synthesize_for_case(case_id, ticker=ticker)
        if current is None:
            return None
        return detect_decision_change(previous, current, detected_at=current.generated_at)

    def compare(self, ticker_a: str, ticker_b: str) -> DecisionComparison | None:
        decision_a = self.synthesize_for_ticker(ticker_a)
        decision_b = self.synthesize_for_ticker(ticker_b)
        if decision_a is None or decision_b is None:
            return None
        return compare_decisions(decision_a, decision_b)

    def synthesize_for_known_cases(self) -> dict[str, InvestmentDecision]:
        """Deliverable 7/8 (Portfolio/Discovery) -- every Portfolio/
        Watchlist Case's own decision, same scope every sibling
        service already uses for "every known company.\""""
        result: dict[str, InvestmentDecision] = {}
        for case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            decision = self.synthesize_for_case(case_id, ticker=ticker)
            if decision is not None:
                result[case_id] = decision
        return result

    def portfolio_action_distribution(self) -> dict[str, tuple[str, ...]]:
        """Deliverable 7 -- "reuse Portfolio, never introduce another
        prioritization system": tickers grouped by action only, in
        Portfolio's own existing holdings order, never re-sorted."""
        portfolio_state = self._portfolio_store.get()
        holdings = portfolio_state.holdings if portfolio_state is not None else ()
        buckets: dict[DecisionAction, list[str]] = {action: [] for action in DecisionAction}
        for holding in holdings:
            if holding.case_id is None:
                continue
            decision = self.synthesize_for_case(holding.case_id, ticker=holding.ticker)
            if decision is not None:
                buckets[decision.action].append(holding.ticker)
        return {action.value: tuple(tickers) for action, tickers in buckets.items()}
