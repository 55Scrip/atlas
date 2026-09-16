"""`InvestmentCaseHistoryService` -- see this package's own `__init__.py`
for the full ownership/reuse/read-only rationale.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

from atlas.alpha.case_membership import known_cases
from atlas.alpha.investment_case.valuation_evidence_snapshot import ValuationEvidenceSnapshot
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.analysis_engine.investment_case_history import (
    AnalyticalHistory,
    HistoricalAnalysisEntry,
    build_analytical_history,
)

__all__ = ["AnalyticalHistoryWithEvidence", "InvestmentCaseHistoryService", "snapshot_identity"]


def snapshot_identity(case_id: str, captured_at: datetime) -> str:
    """The one key that joins a historical result to the evidence frozen with
    it. Identical to the `snapshotId` the API already publishes, so the join
    can never drift from what a client sees."""
    return f"{case_id}:{captured_at.isoformat()}"


@dataclass(frozen=True)
class AnalyticalHistoryWithEvidence:
    """The Core history exactly as Core built it, plus the frozen evidence
    belonging to each of its snapshots.

    This pairing lives in Alpha deliberately. `AnalyticalHistory` and
    `HistoricalAnalysisEntry` are Core contracts and know nothing about how
    Atlas persists evidence; hanging an Alpha persistence type on them would
    invert the dependency the architecture tests police. So Core still
    computes and orders the history, Alpha carries the frozen evidence
    alongside it, and the API schema joins the two by snapshot identity.
    """

    history: AnalyticalHistory
    evidence_by_snapshot_id: Mapping[str, ValuationEvidenceSnapshot | None]

    #: Additive by construction: every existing reader of the Core history
    #: keeps working unchanged, because this wrapper answers the same two
    #: questions the history itself does.
    @property
    def entries(self):
        return self.history.entries

    @property
    def generated_at(self) -> datetime:
        return self.history.generated_at


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

    def build_analytical_history(self) -> AnalyticalHistoryWithEvidence:
        """Read-only: calls `SqlAlchemyInvestmentCaseSnapshotRepository
        .get_history` only -- never `.add`, never
        `InvestmentCaseCompositionService.build`/`build_many`. Opening
        History can never create a snapshot, a change record, or
        rewrite a timestamp."""
        entries: list[HistoricalAnalysisEntry] = []
        evidence_by_snapshot: dict[str, ValuationEvidenceSnapshot | None] = {}
        for case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            for snapshot, change_intelligence, evidence in self._snapshot_repository.get_history_with_evidence(case_id):
                entries.append(
                    HistoricalAnalysisEntry(
                        case_id=case_id, ticker=ticker, snapshot=snapshot, change_intelligence=change_intelligence
                    )
                )
                # Keyed by the snapshot's own identity, never by ticker: one
                # Case has many snapshots, and two of them can hold different
                # evidence under an identical conclusion. The key is the same
                # `case_id:captured_at` the wire calls `snapshotId`.
                evidence_by_snapshot[snapshot_identity(case_id, snapshot.captured_at)] = evidence
        return AnalyticalHistoryWithEvidence(
            history=build_analytical_history(tuple(entries), generated_at=_utc_now()),
            evidence_by_snapshot_id=evidence_by_snapshot,
        )
