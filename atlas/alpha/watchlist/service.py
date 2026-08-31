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
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.case_membership import resolve_case_id_for_ticker
from atlas.alpha.ingestion.engine import classify_refresh
from atlas.alpha.ingestion.repository import SqlAlchemyIngestionResultRepository
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.exceptions import (
    AlphaWatchlistEntryNotFoundError,
    AlphaWatchlistValidationError,
)
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
        identity_gate: CanonicalSecurityIdentityGate | None = None,
        ingestion_result_repository: SqlAlchemyIngestionResultRepository | None = None,
        quota_tracker: "object | None" = None,
    ) -> None:
        self._store = store
        self._case_generation_service = case_generation_service
        self._portfolio_store = portfolio_store
        self._business_record_repository = business_record_repository
        self._business_data_providers = business_data_providers
        self._identity_gate = identity_gate
        self._ingestion_result_repository = ingestion_result_repository
        # Calibration Phase 8B -- see `AlphaPortfolioService.__init__`'s
        # own note: optional, duck-typed (`has_budget() -> bool`), and
        # `None` for every pre-8B caller.
        self._quota_tracker = quota_tracker

    def _budget_available(self):
        return self._quota_tracker.has_budget if self._quota_tracker is not None else None

    def _trigger_enrichment(self, ticker: str, case_id: str | None = None) -> None:
        """Best-effort, never raises for the caller: `ensure_company_
        enriched` already isolates every provider failure into its own
        returned `RefreshSummary` (discarded here -- this slice does
        not yet surface a per-request enrichment outcome to the caller;
        see the design record's Known Limitations) and is itself a
        no-op if this ticker already has persisted `BusinessRecord`s.
        Genuinely does nothing, on purpose, if any dependency is absent
        -- the deliberate no-op this class's own docstring describes.
        Sprint O: `identity_gate` joins `business_record_repository`/
        `business_data_providers` as a third all-or-nothing dependency
        -- there is no path where enrichment runs without it (that
        would mean a `BusinessRecord` created without ever passing
        through the mandatory Identity Gate)."""
        if (
            self._business_record_repository is None
            or self._business_data_providers is None
            or self._identity_gate is None
        ):
            return
        # Automatic Enrichment Coverage, Implementation Phase 1: the
        # prior run's own classified failures (if any), so a provider
        # already known `FAILED_UNSUPPORTED` for this ticker (e.g. SEC
        # for a foreign-private-issuer 20-F filer) is never retried as
        # though it were transient (Requirement 8), while one classified
        # `FAILED_TRANSIENT`/`NOT_YET_ATTEMPTED` (e.g. Alpha Vantage
        # with a still-unconfigured API key) still is -- see
        # `business_data_refresh.completion`'s own module docstring.
        known_provider_failures: tuple = ()
        if self._ingestion_result_repository is not None:
            prior = self._ingestion_result_repository.get_by_ticker(ticker)
            if prior is not None:
                known_provider_failures = prior.provider_failures
        summary = ensure_company_enriched(
            ticker, self._business_data_providers, self._business_record_repository,
            identity_gate=self._identity_gate,
            known_provider_failures=known_provider_failures,
            budget_available=self._budget_available(),
        )
        # Atlas Intelligence Sprint 9 (Data Ingestion & Automatic
        # Refresh, Deliverable 4/11) -- records the real, already-
        # computed `RefreshSummary` as this Case's own `IngestionResult`
        # so Monitoring can later read (never re-detect) whether new
        # data arrived. `summary is None` means `ensure_company_enriched`
        # itself no-opped (already minimally complete) -- an honest
        # "no check happened," never recorded as a fabricated result.
        if summary is not None and self._ingestion_result_repository is not None:
            result = classify_refresh(summary, ticker=ticker, case_id=case_id, ran_at=summary.evaluated_at or _utc_now())
            self._ingestion_result_repository.upsert(result)

    def add_ticker(self, ticker: str) -> AlphaWatchlistEntry:
        """Idempotent: adding an already-watchlisted ticker returns the
        existing entry completely unchanged -- no duplicate row, no
        second Case, no repeated provider call.

        A ticker not currently on the Watchlist resolves its Case id
        via `case_membership.resolve_case_id_for_ticker` first --
        reusing a Case already linked to this exact ticker through a
        current Portfolio holding, or through this ticker's own prior
        (since-removed) Watchlist history, so remove-then-re-add
        restores continuity with the original Case rather than
        creating a new one (Ticker -> Existing Case Resolution Sprint).
        Only when no existing Case can be resolved does
        `CaseGenerationService.ensure_case_id` create a brand-new one.
        Persists the (re)activated entry, then triggers automatic
        enrichment for it.
        """
        if not ticker or not ticker.strip():
            raise AlphaWatchlistValidationError("ticker must not be blank")
        normalized = ticker.strip().upper()

        existing = self._store.get_by_ticker(normalized)
        if existing is not None:
            return existing

        resolved_case_id = resolve_case_id_for_ticker(normalized, self._portfolio_store, self._store)
        case_id = self._case_generation_service.ensure_case_id(
            current_case_id=resolved_case_id,
            ticker=normalized,
        )
        entry = AlphaWatchlistEntry(ticker=normalized, case_id=case_id, added_at=_utc_now())
        self._store.add(entry)
        self._trigger_enrichment(normalized, case_id)
        return entry

    def remove_ticker(self, ticker: str) -> None:
        """Removes a ticker from the Watchlist only -- a soft delete
        (see `store.py`): the row survives, so `case_membership.
        resolve_case_id_for_ticker` can still find its `case_id` if the
        ticker is later re-added. The Watchlist table has no
        relationship to Case/Decision/Evidence/Company data, so nothing
        else is touched either way. Raises
        `AlphaWatchlistEntryNotFoundError` if the ticker is not
        currently on the Watchlist, matching this codebase's
        established delete-of-missing convention rather than being
        silently idempotent (idempotence governs `add_ticker`, a
        different operation)."""
        normalized = ticker.strip().upper()
        existing = self._store.get_by_ticker(normalized)
        if existing is None:
            raise AlphaWatchlistEntryNotFoundError(
                f"No Watchlist entry found for ticker {normalized}"
            )
        self._store.remove(normalized, _utc_now())

    def list_all(self) -> tuple[AlphaWatchlistEntry, ...]:
        return self._store.list_all()
