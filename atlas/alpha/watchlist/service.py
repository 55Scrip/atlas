"""Application service for Atlas Alpha's provisional Watchlist state
(Investment Case Engine v1 slice).

`store` and `case_generation_service` are required: every `add_ticker`
call needs both to do its one job (link a ticker to an Investment
Case). `portfolio_store` (cross-context Case reuse) and
`business_record_repository`/`business_data_providers` (automatic
enrichment) are optional, progressively-enhancing capabilities -- the
same `X | None = None` opt-in pattern `AlphaPortfolioService` already
established for `case_generation_service` itself. Omitting them still
produces a correct, if less complete, result: a ticker still gets its
own new Case (just never a cross-context-reused one), and is still
added to the Watchlist (just never auto-enriched) -- useful for tests
that want to isolate Case-linking behavior from enrichment, or vice
versa.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.service import ensure_company_enriched
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.exceptions import AlphaWatchlistValidationError
from atlas.alpha.watchlist.models import AlphaWatchlistEntry
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.analysis_engine.business_data.providers import BusinessDataProvider

__all__ = ["AlphaWatchlistService"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AlphaWatchlistService:
    def __init__(
        self,
        store: AlphaWatchlistStore,
        case_generation_service: CaseGenerationService,
        portfolio_store: AlphaPortfolioStore | None = None,
        business_record_repository: SqlAlchemyBusinessRecordRepository | None = None,
        business_data_providers: tuple[BusinessDataProvider, ...] | None = None,
    ) -> None:
        self._store = store
        self._case_generation_service = case_generation_service
        self._portfolio_store = portfolio_store
        self._business_record_repository = business_record_repository
        self._business_data_providers = business_data_providers

    def _known_case_ids_by_ticker(self) -> dict[str, str]:
        """Portfolio's own current holdings, ticker -> case_id --
        "Watchlist and Portfolio are membership contexts around the
        same company knowledge," so a ticker already linked to a Case
        via Portfolio must reuse that exact Case when it is separately
        added to Watchlist, never create a second one for the same
        company."""
        if self._portfolio_store is None:
            return {}
        state = self._portfolio_store.get()
        if state is None:
            return {}
        return {holding.ticker: holding.case_id for holding in state.holdings if holding.case_id is not None}

    def _trigger_enrichment(self, ticker: str) -> None:
        """Best-effort, never raises for the caller: `ensure_company_
        enriched` already isolates every provider failure into its own
        returned `RefreshSummary` (discarded here -- this slice does
        not yet surface a per-request enrichment outcome to the caller;
        see the design record's Known Limitations) and is itself a
        no-op if this ticker already has persisted `BusinessRecord`s.
        Genuinely does nothing, on purpose, if either dependency is
        absent -- the deliberate no-op this class's own docstring
        describes."""
        if self._business_record_repository is None or self._business_data_providers is None:
            return
        ensure_company_enriched(ticker, self._business_data_providers, self._business_record_repository)

    def add_ticker(self, ticker: str) -> AlphaWatchlistEntry:
        """Idempotent: adding an already-watchlisted ticker returns the
        existing entry completely unchanged -- no duplicate row, no
        second Case, no repeated provider call. A genuinely new ticker
        resolves its Case id via `CaseGenerationService.ensure_case_id`
        (reusing a Portfolio-linked Case for the same ticker if one
        already exists), persists the new entry, then triggers
        automatic enrichment for it.
        """
        if not ticker or not ticker.strip():
            raise AlphaWatchlistValidationError("ticker must not be blank")
        normalized = ticker.strip().upper()

        existing = self._store.get_by_ticker(normalized)
        if existing is not None:
            return existing

        case_id = self._case_generation_service.ensure_case_id(
            current_case_id=None,
            ticker=normalized,
            known_case_ids_by_ticker=self._known_case_ids_by_ticker(),
        )
        entry = AlphaWatchlistEntry(ticker=normalized, case_id=case_id, added_at=_utc_now())
        self._store.add(entry)
        self._trigger_enrichment(normalized)
        return entry

    def list_all(self) -> tuple[AlphaWatchlistEntry, ...]:
        return self._store.list_all()
