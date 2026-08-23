"""`EvidenceTimelineService` -- read-only. Mirrors `atlas.alpha
.investment_case_history.service.InvestmentCaseHistoryService`'s own
"History does not reason, History does not recompute" discipline
exactly: calls `SqlAlchemyEvidenceSnapshotRepository.get_latest`/
`.get_history` only, never `.add()`. Capturing a new `EvidenceSnapshot`
is the responsibility of `investment_case/api/router.py`'s own
composition root (the same place that already builds Coverage/Stance/
Evidence Quality for the real `/cases/{case_id}/analysis` response) --
opening a Timeline view can never create a snapshot, a transition, or a
timestamp.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.alpha.case_membership import known_cases, resolve_case_id_for_ticker
from atlas.alpha.evidence_timeline.models import EvidenceHistory, EvidenceSnapshot
from atlas.alpha.evidence_timeline.repository import SqlAlchemyEvidenceSnapshotRepository
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["EvidenceTimelineEntry", "EvidenceTimelineFeed", "EvidenceTimelineService"]


@dataclass(frozen=True)
class EvidenceTimelineEntry:
    """One Case's own snapshot, at one point in time, plus the
    (persisted, never recomputed) `EvidenceHistory` describing how it
    differs from the entry immediately before it -- mirrors
    `investment_case_history.HistoricalAnalysisEntry`'s exact shape."""

    case_id: str
    ticker: str | None
    snapshot: EvidenceSnapshot
    history: EvidenceHistory


@dataclass(frozen=True)
class EvidenceTimelineFeed:
    generated_at: datetime
    entries: tuple[EvidenceTimelineEntry, ...]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceTimelineService:
    def __init__(
        self,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
        snapshot_repository: SqlAlchemyEvidenceSnapshotRepository,
    ) -> None:
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store
        self._snapshot_repository = snapshot_repository

    def history_for_case(self, case_id: str) -> tuple[tuple[EvidenceSnapshot, EvidenceHistory], ...]:
        """Deliverable 5 -- Investment Case Integration. Oldest first,
        exactly `SqlAlchemyEvidenceSnapshotRepository.get_history`'s own
        ordering."""
        return self._snapshot_repository.get_history(case_id)

    def history_for_ticker(self, ticker: str) -> tuple[tuple[EvidenceSnapshot, EvidenceHistory], ...] | None:
        case_id = resolve_case_id_for_ticker(ticker, self._portfolio_store, self._watchlist_store)
        if case_id is None:
            return None
        return self.history_for_case(case_id)

    def build_feed(self) -> EvidenceTimelineFeed:
        """Deliverables 6/7/9 -- the unified, cross-Case timeline
        Portfolio/Discovery/Daily Brief read from, mirroring
        `InvestmentCaseHistoryService.build_analytical_history`'s own
        "every Case Portfolio or Watchlist membership already covers,
        newest first" shape exactly."""
        entries: list[EvidenceTimelineEntry] = []
        for case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            for snapshot, history in self._snapshot_repository.get_history(case_id):
                entries.append(EvidenceTimelineEntry(case_id=case_id, ticker=ticker, snapshot=snapshot, history=history))
        ordered = tuple(
            sorted(entries, key=lambda entry: (-entry.snapshot.captured_at.timestamp(), entry.case_id, entry.snapshot.content_hash))
        )
        return EvidenceTimelineFeed(generated_at=_utc_now(), entries=ordered)
