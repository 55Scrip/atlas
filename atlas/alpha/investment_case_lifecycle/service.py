"""Orchestration for the Investment Case Lifecycle. The only part of
this package that performs I/O.

**Reuses two already-computed services, recomputes nothing new.**
`InvestmentCaseCompositionService.build` (unmodified, read-only) supplies
every real signal `engine.py` reads; `MonitoringService.freshness_for_case`
(unmodified, read-only) supplies `last_monitored_at`/`has_ever_monitored`.
See this package's own `__init__.py` for the full audit this reuse is
based on.

**Always computed live**, the same choice every sibling Decision Layer
service already makes -- Atlas Status is never read from a cache to
decide the current lifecycle state. The one persisted table
(`investment_case_lifecycle_history_table`) exists solely so the
*previous* evaluation's own Mandatory Core and `published_since` can be
read back for regression detection; it is never consulted to decide
the current state itself.

**Isolation**: this module only ever reads `InvestmentCaseComposition`
and `CaseOperationalFreshness` -- it never calls anything that writes
to the Decision Layer, recommendation, valuation, portfolio-fit, or any
stored investment conclusion. Its own repository writes are scoped to
its own `investment_case_lifecycle_history` table only.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.case_membership import known_cases
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_case_lifecycle.engine import build_atlas_status
from atlas.alpha.investment_case_lifecycle.models import (
    AtlasStatus,
    EvidenceTier,
    LifecycleSnapshot,
    LifecycleState,
    MandatoryCoreAssessment,
    MandatoryItemAssessment,
    MandatoryItemId,
    MissingReasonCode,
)
from atlas.alpha.investment_case_lifecycle.repository import SqlAlchemyLifecycleSnapshotRepository
from atlas.alpha.monitoring.service import MonitoringService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["InvestmentCaseLifecycleService"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _error_mandatory_core() -> MandatoryCoreAssessment:
    items = tuple(
        MandatoryItemAssessment(item=item_id, satisfied=False, satisfied_via=None, reason=MissingReasonCode.INTERNAL_EVALUATION_ERROR)
        for item_id in MandatoryItemId
    )
    return MandatoryCoreAssessment(items=items, all_satisfied=False)


class InvestmentCaseLifecycleService:
    def __init__(
        self,
        composition_service: InvestmentCaseCompositionService,
        monitoring_service: MonitoringService,
        snapshot_repository: SqlAlchemyLifecycleSnapshotRepository,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
    ) -> None:
        self._composition_service = composition_service
        self._monitoring_service = monitoring_service
        self._snapshot_repository = snapshot_repository
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store
        # Request-scoped memoization, the same pattern and justification
        # every sibling Decision Layer service already uses (see
        # `DecisionReadinessService.__init__`'s own comment) -- `ticker`
        # is excluded from the key for the same reason given there.
        self._status_for_case_cache: dict[str, AtlasStatus | None] = {}

    def _ticker_for_case(self, case_id: str) -> str | None:
        for known_case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            if known_case_id == case_id:
                return ticker
        return None

    def status_for_case(self, case_id: str, *, ticker: str | None = None) -> AtlasStatus | None:
        """`None` only when `case_id` does not resolve to a real Case
        -- the same honest-absence contract every sibling Alpha service
        already uses."""
        resolved_ticker = ticker if ticker is not None else self._ticker_for_case(case_id)
        if case_id in self._status_for_case_cache:
            return self._status_for_case_cache[case_id]
        status = self._status_for_case_uncached(case_id, ticker=resolved_ticker)
        self._status_for_case_cache[case_id] = status
        return status

    def _status_for_case_uncached(self, case_id: str, *, ticker: str | None) -> AtlasStatus | None:
        generated_at = _utc_now()
        previous_snapshot = self._snapshot_repository.get(case_id)
        try:
            composition = self._composition_service.build(case_id)
            if composition is None:
                return None
            freshness = self._monitoring_service.freshness_for_case(case_id)
        except Exception:
            # A genuine evaluator/service exception -- categorically
            # distinct from a normal "evidence not present yet" outcome
            # (Lifecycle Specification's own distinction between
            # `INTERNAL_EVALUATION_ERROR` and every other
            # `MissingReasonCode`). Deliberately not persisted: an
            # exception is transient by nature, and upserting it would
            # corrupt the regression-history table's own comparison
            # baseline for the next successful evaluation.
            previous_state = previous_snapshot.lifecycle_state if previous_snapshot is not None else None
            fallback_state = previous_state if previous_state in (
                LifecycleState.PUBLISHED,
                LifecycleState.CONTINUOUS_MONITORING,
            ) else LifecycleState.ANALYSIS_RUNNING
            return AtlasStatus(
                case_id=case_id,
                lifecycle_state=fallback_state,
                mandatory_core=_error_mandatory_core(),
                evidence_tier=EvidenceTier.MANDATORY_ONLY,
                important_missing_items=(),
                optional_missing_items=(),
                next_expected_action="resolving an internal evaluation error",
                last_updated=None,
                next_refresh_description="next automatic check, triggered by new evidence (price refresh, filing, portfolio event)",
                published_since=previous_snapshot.published_since if previous_snapshot is not None else None,
                last_regression=None,
                generated_at=generated_at,
            )

        previous_state = previous_snapshot.lifecycle_state if previous_snapshot is not None else None
        previous_core = previous_snapshot.mandatory_core if previous_snapshot is not None else None
        published_since_input = (
            previous_snapshot.published_since
            if previous_snapshot is not None and previous_snapshot.published_since is not None
            else generated_at
        )

        status = build_atlas_status(
            case_id=case_id,
            composition=composition,
            ticker=ticker,
            has_ever_monitored=freshness.last_monitored_at is not None,
            last_monitored_at=freshness.last_monitored_at,
            previous_state=previous_state,
            previous_core=previous_core,
            published_since=published_since_input,
            generated_at=generated_at,
        )

        self._snapshot_repository.upsert(
            LifecycleSnapshot(
                case_id=case_id,
                lifecycle_state=status.lifecycle_state,
                mandatory_core=status.mandatory_core,
                published_since=status.published_since,
                generated_at=generated_at,
            ),
            ticker=ticker,
        )
        return status

    def status_for_known_cases(self) -> dict[str, AtlasStatus]:
        """Every Portfolio/Watchlist Case's own Atlas Status -- same
        scope every sibling service already uses for "every known
        company.\""""
        result: dict[str, AtlasStatus] = {}
        for case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            status = self.status_for_case(case_id, ticker=ticker)
            if status is not None:
                result[case_id] = status
        return result
