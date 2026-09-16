"""`InvestmentCaseHistoryService` -- see this package's own `__init__.py`
for the full ownership/reuse/read-only rationale.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

from atlas.alpha.case_membership import known_cases
from atlas.alpha.investment_case.valuation_evidence_snapshot import ValuationEvidenceSnapshot
from atlas.alpha.investment_case_history.cursor import HistoryCursor, decode_cursor, encode_cursor
from atlas.alpha.investment_case_history.evidence_coverage import (
    HistoricalEvidenceCoverage,
    SnapshotRecord,
    build_coverage,
)
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.analysis_engine.investment_case_history import (
    AnalyticalHistory,
    HistoricalAnalysisEntry,
    build_analytical_history,
)

__all__ = [
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "AnalyticalHistoryWithEvidence",
    "InvestmentCaseHistoryService",
    "snapshot_identity",
]

#: Measured, not guessed: an evidence-bearing entry serialises to ~3.4 KB, so
#: 25 is roughly an 85 KB page -- a page a reader can actually use, and small
#: enough that the first one is cheap however long the history grows.
DEFAULT_PAGE_SIZE = 25
#: The ceiling exists so no caller can ask for the unbounded response this
#: sprint removed. 100 entries is ~340 KB, already more than any view needs.
MAX_PAGE_SIZE = 100


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
    #: The opaque boundary a client sends back to continue; `None` at the end
    #: of the history. `has_more` is answered by a single lookahead row, not
    #: by counting the corpus.
    next_cursor: str | None = None
    has_more: bool = False

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

    def build_analytical_history(
        self, *, limit: int = DEFAULT_PAGE_SIZE, cursor: str | None = None
    ) -> AnalyticalHistoryWithEvidence:
        """One bounded page of the combined history, newest first.

        Read-only: `get_visible_history_page` only, never `.add`, never
        `InvestmentCaseCompositionService.build`/`build_many`. Opening
        History still cannot create analytical state.

        **Scope is re-derived here, on every request**, from live Portfolio
        and Watchlist membership -- the pre-existing meaning of "whose
        history is this", unchanged. It is applied *before* the page is cut,
        so a Case outside scope never consumes a slot. The cursor is only an
        ordering boundary: it can narrow a page, never widen the scope, so a
        cursor cannot be used to reach a Case the request could not see.

        A traversal is therefore not a transactional snapshot of membership:
        a Case added or removed between two page requests is reflected in the
        later page. That is the honest consequence of scope meaning "now",
        and it is deliberate -- freezing membership for the length of a
        traversal would require session state this surface does not have.
        """
        page_size = max(1, min(int(limit), MAX_PAGE_SIZE))
        position = decode_cursor(cursor)
        membership = tuple(known_cases(self._portfolio_store, self._watchlist_store))
        ticker_by_case = {case_id: ticker for case_id, ticker in membership}
        rows, has_more = self._snapshot_repository.get_visible_history_page(
            [case_id for case_id, _ in membership],
            limit=page_size,
            after=None if position is None
            else (position.captured_at, position.case_id, position.content_hash),
        )
        entries: list[HistoricalAnalysisEntry] = []
        evidence_by_snapshot: dict[str, ValuationEvidenceSnapshot | None] = {}
        for case_id, snapshot, change_intelligence, evidence in rows:
            entries.append(
                HistoricalAnalysisEntry(
                    case_id=case_id, ticker=ticker_by_case.get(case_id),
                    snapshot=snapshot, change_intelligence=change_intelligence
                )
            )
            evidence_by_snapshot[snapshot_identity(case_id, snapshot.captured_at)] = evidence
        next_cursor = None
        if has_more and entries:
            last = entries[-1]
            next_cursor = encode_cursor(HistoryCursor(
                captured_at=last.snapshot.captured_at.isoformat(),
                case_id=last.case_id,
                content_hash=last.snapshot.content_hash,
            ))
        return AnalyticalHistoryWithEvidence(
            # Core still owns the ordering. The page already arrives in that
            # order, so this is a no-op re-sort -- which is exactly the point:
            # the endpoint cannot drift from the order Core defines.
            history=build_analytical_history(tuple(entries), generated_at=_utc_now()),
            evidence_by_snapshot_id=evidence_by_snapshot,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    def build_evidence_coverage(self) -> HistoricalEvidenceCoverage:
        """How much evidence-bearing history exists, for the Cases this
        request may see.

        Read-only and aggregate: one snapshot query, no page walking, and
        nothing from the live Case -- every value is read from the snapshots'
        own frozen payloads. Scope is the same live membership History uses,
        so coverage can never reveal a Case the caller could not already
        open.
        """
        membership = tuple(known_cases(self._portfolio_store, self._watchlist_store))
        ticker_by_case = {case_id: ticker for case_id, ticker in membership}
        rows = self._snapshot_repository.get_visible_snapshot_records([case_id for case_id, _ in membership])
        records = tuple(
            SnapshotRecord(
                case_id=row["case_id"],
                ticker=ticker_by_case.get(row["case_id"]),
                captured_at=datetime.fromisoformat(row["captured_at"]),
                valuation_status=row["valuation_status"],
                recommendation_state=row["recommendation_state"],
                valuation_methodology=row["valuation_methodology"],
                evidence=row["evidence"],
            )
            for row in rows
        )
        return build_coverage(records, visible_case_count=len(membership), generated_at=_utc_now())
