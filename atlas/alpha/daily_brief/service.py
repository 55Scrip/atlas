"""`DailyBriefService` -- see this package's own `__init__.py` for the
full ownership/reuse rationale.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.case_membership import known_cases
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.analysis_engine.daily_brief import DailyBrief, build_daily_brief, build_daily_brief_entry

__all__ = ["DailyBriefService"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DailyBriefService:
    def __init__(
        self,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
        investment_case_composition_service: InvestmentCaseCompositionService,
    ) -> None:
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store
        self._investment_case_composition_service = investment_case_composition_service

    def build_daily_brief(self) -> DailyBrief:
        entries = []
        for case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            composition = self._investment_case_composition_service.build(case_id)
            if composition is None or composition.change_intelligence is None:
                # Honest absence: an unresolved case_id (should not
                # happen for a real Portfolio/Watchlist entry, but never
                # assumed), or Change Intelligence itself unavailable
                # (no snapshot repository wired) -- either way, silently
                # excluded rather than fabricated into an entry.
                continue
            entry = build_daily_brief_entry(case_id, ticker, composition.change_intelligence)
            if entry is not None:
                entries.append(entry)
        return build_daily_brief(tuple(entries), generated_at=_utc_now())
