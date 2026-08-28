"""Persistence for enrichment progress -- a plain read/write store, no
job-queue semantics. `start_batch` seeds every ticker as `PENDING` in
the given (weight-prioritized) order; `mark_analyzing`/`mark_done`/
`mark_deferred` update one row in place.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine

from atlas.alpha.enrichment_tracking.models import (
    EnrichmentProgressBatch,
    EnrichmentProgressEntry,
    EnrichmentProgressStatus,
)
from atlas.alpha.enrichment_tracking.table import enrichment_progress_table


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EnrichmentProgressStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def start_batch(self, batch_id: str, tickers_with_names: tuple[tuple[str, str | None], ...]) -> None:
        """Seeds every ticker as `PENDING`, in the given order. Replaces
        any prior rows for this `batch_id` outright -- a batch id is
        never reused for a second, different ticker set."""
        with self._engine.begin() as connection:
            connection.execute(
                delete(enrichment_progress_table).where(
                    enrichment_progress_table.c.batch_id == batch_id
                )
            )
            if not tickers_with_names:
                return
            now = _utc_now_iso()
            connection.execute(
                enrichment_progress_table.insert(),
                [
                    {
                        "batch_id": batch_id,
                        "ticker": ticker,
                        "company_name": company_name,
                        "status": EnrichmentProgressStatus.PENDING.value,
                        "updated_at": now,
                        "sequence": sequence,
                    }
                    for sequence, (ticker, company_name) in enumerate(tickers_with_names)
                ],
            )

    def _set_status(self, batch_id: str, ticker: str, status: EnrichmentProgressStatus) -> None:
        statement = sqlite_insert(enrichment_progress_table).values(
            batch_id=batch_id,
            ticker=ticker,
            company_name=None,
            status=status.value,
            updated_at=_utc_now_iso(),
            sequence=0,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[enrichment_progress_table.c.batch_id, enrichment_progress_table.c.ticker],
            set_={"status": status.value, "updated_at": _utc_now_iso()},
        )
        with self._engine.begin() as connection:
            connection.execute(statement)

    def mark_analyzing(self, batch_id: str, ticker: str) -> None:
        self._set_status(batch_id, ticker, EnrichmentProgressStatus.ANALYZING)

    def mark_done(self, batch_id: str, ticker: str) -> None:
        self._set_status(batch_id, ticker, EnrichmentProgressStatus.DONE)

    def mark_deferred(self, batch_id: str, ticker: str) -> None:
        self._set_status(batch_id, ticker, EnrichmentProgressStatus.DEFERRED)

    def get_batch(self, batch_id: str) -> EnrichmentProgressBatch | None:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(enrichment_progress_table)
                    .where(enrichment_progress_table.c.batch_id == batch_id)
                    .order_by(enrichment_progress_table.c.sequence)
                )
                .mappings()
                .all()
            )
        if not rows:
            return None
        entries = tuple(
            EnrichmentProgressEntry(
                batch_id=row["batch_id"],
                ticker=row["ticker"],
                company_name=row["company_name"],
                status=EnrichmentProgressStatus(row["status"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        )
        return EnrichmentProgressBatch(batch_id=batch_id, entries=entries)
