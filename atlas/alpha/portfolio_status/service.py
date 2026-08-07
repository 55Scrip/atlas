"""Builds the Portfolio Status report (ATLAS-015).

Reads Alpha's own portfolio state and trade log, plus Core's Decision,
Outcome, and Observation repositories -- all read-only, exactly the
authorized direction `atlas/alpha/portfolio/service.py::apply_confirmed_trade`
already established for Outcome, extended here to Decision and
Observation the same way. No Core object is ever constructed or
modified. Reuses `atlas.domains.portfolio.calculations` (via
`atlas.alpha.portfolio.projection.derive_portfolio_view`) for
concentration/largest-position math rather than re-deriving it.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.alpha.portfolio.models import AlphaPortfolioState, ReconciliationStatus
from atlas.alpha.portfolio.projection import derive_portfolio_view
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio_status.models import (
    AttentionCategory,
    AttentionItem,
    PortfolioHealthMetrics,
    PortfolioStatusReport,
    PortfolioSummaryMetrics,
    ReviewQueueItem,
)
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.outcome.repository import OutcomeRepository

# A fixed, documented threshold -- not a scoring model. An Investment
# Case is flagged "very old" once 90 days have passed since the
# earliest Decision or Observation recorded against it (Case itself has
# no timestamp query surface; see the module docstring in
# `atlas/core/domain/case/repository.py`, which deliberately has no
# `list_all` -- this reuses data already read for the other checks
# rather than expanding that boundary).
_VERY_OLD_CASE_THRESHOLD_DAYS = 90

# A ticker that already passed Portfolio Import's client-side resolution
# is always uppercase letters/digits, optionally with a "." or "-"
# share-class suffix (see `resolveInstrument()` in
# `frontend/src/portfolio-import/resolution.ts` and the Nasdaq Stockholm
# entries in `instrumentRegistry.ts`, e.g. "VOLV-B", "BRK.B"). This is a
# structural well-formedness check only -- it cannot confirm a ticker is
# real, only flag one that looks broken.
_TICKER_SHAPE_RE = re.compile(r"^[A-Z0-9]{1,10}([.\-][A-Z0-9]{1,3})?$")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class _CaseActivity:
    """Everything this module needs about one Case, gathered once from
    the Decisions/Observations/Outcomes already fetched -- never a
    direct Case read (no `list_all` exists for Case; see above)."""

    decisions: tuple[Decision, ...]
    observations: tuple[Observation, ...]


class PortfolioStatusService:
    def __init__(
        self,
        portfolio_store: AlphaPortfolioStore,
        trade_log_store: AlphaTradeLogStore,
        decision_repository: DecisionRepository,
        outcome_repository: OutcomeRepository,
        observation_repository: ObservationRepository,
    ) -> None:
        self._portfolio_store = portfolio_store
        self._trade_log_store = trade_log_store
        self._decision_repository = decision_repository
        self._outcome_repository = outcome_repository
        self._observation_repository = observation_repository

    def build_report(self) -> PortfolioStatusReport:
        state = self._portfolio_store.get()
        if state is None or not state.holdings:
            return PortfolioStatusReport.empty()

        all_decisions = self._decision_repository.list_all()
        all_outcomes = self._outcome_repository.list_all()
        all_observations = self._observation_repository.list_all()
        all_trades = self._trade_log_store.list_all()

        decisions_by_case: dict[str, list[Decision]] = defaultdict(list)
        for decision in all_decisions:
            decisions_by_case[str(decision.case_id)].append(decision)

        observations_by_case: dict[str, list[Observation]] = defaultdict(list)
        for observation in all_observations:
            observations_by_case[str(observation.case_id)].append(observation)

        outcomes_by_decision_id: dict[str, int] = defaultdict(int)
        for outcome in all_outcomes:
            outcomes_by_decision_id[str(outcome.decision_id)] += 1

        outcome_ids_with_trade = {trade.outcome_id for trade in all_trades}

        observation_ids_referenced_by_a_decision = {
            str(decision.observation_id)
            for decision in all_decisions
            if decision.observation_id is not None
        }

        now = _utc_now()
        attention_items: list[AttentionItem] = []

        for holding in state.holdings:
            if holding.case_id is None:
                attention_items.append(
                    AttentionItem(ticker=holding.ticker, category=AttentionCategory.MISSING_CASE, case_id=None)
                )
                continue

            case_id = holding.case_id
            case_decisions = decisions_by_case.get(case_id, [])
            case_observations = observations_by_case.get(case_id, [])

            for decision in case_decisions:
                decision_id = str(decision.id)
                if outcomes_by_decision_id.get(decision_id, 0) == 0:
                    attention_items.append(
                        AttentionItem(
                            ticker=holding.ticker,
                            category=AttentionCategory.DECISION_WITHOUT_OUTCOME,
                            case_id=case_id,
                        )
                    )

            for outcome in all_outcomes:
                if str(outcome.case_id) != case_id:
                    continue
                if str(outcome.id) not in outcome_ids_with_trade:
                    attention_items.append(
                        AttentionItem(
                            ticker=holding.ticker,
                            category=AttentionCategory.OUTCOME_WITHOUT_EXECUTION,
                            case_id=case_id,
                        )
                    )

            for observation in case_observations:
                if str(observation.id) not in observation_ids_referenced_by_a_decision:
                    attention_items.append(
                        AttentionItem(
                            ticker=holding.ticker,
                            category=AttentionCategory.OBSERVATION_WITHOUT_DECISION,
                            case_id=case_id,
                        )
                    )

            # `decided_at`/`observed_at`, not `recorded_at`: both are
            # client-settable (an imported or backdated Decision/
            # Observation carries its own real date), so this reflects
            # when the thinking actually happened rather than when
            # Atlas happened to capture it.
            activity_timestamps = [decision.decided_at for decision in case_decisions] + [
                observation.observed_at for observation in case_observations
            ]
            if activity_timestamps:
                earliest = min(activity_timestamps)
                age_days = (now - earliest).days
                if age_days >= _VERY_OLD_CASE_THRESHOLD_DAYS:
                    attention_items.append(
                        AttentionItem(
                            ticker=holding.ticker,
                            category=AttentionCategory.VERY_OLD_CASE,
                            case_id=case_id,
                            age_days=age_days,
                        )
                    )

            if holding.reconciliation_status == ReconciliationStatus.AWAITING_RECONCILIATION:
                attention_items.append(
                    AttentionItem(
                        ticker=holding.ticker,
                        category=AttentionCategory.AWAITING_RECONCILIATION,
                        case_id=case_id,
                    )
                )

        summary = self._build_summary(state, attention_items)
        review_queue = self._build_review_queue(attention_items)
        health = self._build_health(state, all_decisions, attention_items)

        return PortfolioStatusReport(
            exists=True,
            summary=summary,
            attention_items=tuple(attention_items),
            review_queue=review_queue,
            health=health,
        )

    def _build_summary(
        self, state: AlphaPortfolioState, attention_items: list[AttentionItem]
    ) -> PortfolioSummaryMetrics:
        portfolio_summary = derive_portfolio_view(state)
        held_case_ids = {holding.case_id for holding in state.holdings if holding.case_id is not None}

        unallocated_percent = 100.0 - sum(h.weight_percent for h in state.holdings) - (
            state.cash_weight_percent or 0.0
        )

        # Deliberately NOT `portfolio_summary.largest_weight`: that
        # figure is the largest holding's share of the *known* holdings
        # total, which silently diverges from the plain
        # `holding.weight_percent` already shown per-row on the
        # Holdings list whenever any weight is unallocated (e.g. a
        # 60/20 split reads as "75%" there, not 60%) -- confusing next
        # to a Holdings section showing 60%. This reads the same
        # `weight_percent` the Holdings list already displays, so the
        # two never disagree.
        largest_holding = max(state.holdings, key=lambda h: h.weight_percent, default=None)
        return PortfolioSummaryMetrics(
            holdings_count=len(state.holdings),
            largest_position_ticker=largest_holding.ticker if largest_holding is not None else None,
            largest_position_weight_percent=(
                largest_holding.weight_percent if largest_holding is not None else None
            ),
            number_of_investment_cases=len(held_case_ids),
            open_decisions=_count(attention_items, AttentionCategory.DECISION_WITHOUT_OUTCOME),
            pending_outcomes=_count(attention_items, AttentionCategory.OUTCOME_WITHOUT_EXECUTION),
            pending_executions=_count(attention_items, AttentionCategory.AWAITING_RECONCILIATION),
            concentration_level=portfolio_summary.concentration.level.value,
            unallocated_percent=round(unallocated_percent, 2),
        )

    def _build_review_queue(self, attention_items: list[AttentionItem]) -> tuple[ReviewQueueItem, ...]:
        by_ticker: dict[str, list[AttentionItem]] = defaultdict(list)
        for item in attention_items:
            by_ticker[item.ticker].append(item)

        queue = [
            ReviewQueueItem(
                ticker=ticker,
                case_id=items[0].case_id,
                reason_count=len(items),
                top_category=items[0].category,
            )
            for ticker, items in by_ticker.items()
        ]
        # Deterministic order: most reasons first, then alphabetical --
        # not a learned or AI ranking.
        queue.sort(key=lambda item: (-item.reason_count, item.ticker))
        return tuple(queue)

    def _build_health(
        self,
        state: AlphaPortfolioState,
        all_decisions: list[Decision],
        attention_items: list[AttentionItem],
    ) -> PortfolioHealthMetrics:
        held_case_ids = {holding.case_id for holding in state.holdings if holding.case_id is not None}
        holdings_with_case = sum(1 for holding in state.holdings if holding.case_id is not None)

        held_case_decisions = [
            decision for decision in all_decisions if str(decision.case_id) in held_case_ids
        ]
        most_recent_decision_at = (
            max(decision.decided_at for decision in held_case_decisions) if held_case_decisions else None
        )

        unallocated_percent = 100.0 - sum(h.weight_percent for h in state.holdings) - (
            state.cash_weight_percent or 0.0
        )
        allocated_percent = round(100.0 - unallocated_percent, 2)

        unknown_tickers = tuple(
            holding.ticker for holding in state.holdings if not _TICKER_SHAPE_RE.match(holding.ticker)
        )

        return PortfolioHealthMetrics(
            holdings_with_case_count=holdings_with_case,
            holdings_count=len(state.holdings),
            most_recent_decision_at=most_recent_decision_at,
            outstanding_workflow_items=len(attention_items),
            allocated_percent=allocated_percent,
            unknown_instrument_tickers=unknown_tickers,
        )


def _count(items: list[AttentionItem], category: AttentionCategory) -> int:
    return sum(1 for item in items if item.category == category)
