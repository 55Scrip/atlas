"""`InvestmentCaseHistoryService` -- see this package's own `__init__.py`
for the full ownership/reuse/read-only rationale.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.case_membership import known_cases
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.analysis_engine.investment_case_history import (
    AnalyticalHistory,
    HistoricalAnalysisEntry,
    build_analytical_history,
)

__all__ = ["InvestmentCaseHistoryService"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InvestmentCaseHistoryService:
    def __init__(
        self,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
        snapshot_repository: SqlAlchemyInvestmentCaseSnapshotRepository,
    ) -> None:
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store
        self._snapshot_repository = snapshot_repository

    def build_analytical_history(self) -> AnalyticalHistory:
        """Read-only: calls `SqlAlchemyInvestmentCaseSnapshotRepository
        .get_history` only -- never `.add`, never
        `InvestmentCaseCompositionService.build`/`build_many`. Opening
        History can never create a snapshot, a change record, or
        rewrite a timestamp."""
        entries: list[HistoricalAnalysisEntry] = []
        for case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            for snapshot, change_intelligence in self._snapshot_repository.get_history(case_id):
                entries.append(
                    HistoricalAnalysisEntry(
                        case_id=case_id, ticker=ticker, snapshot=snapshot, change_intelligence=change_intelligence
                    )
                )
        return build_analytical_history(tuple(entries), generated_at=_utc_now())
