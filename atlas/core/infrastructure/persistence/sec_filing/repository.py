"""Reading and writing SEC filing provenance."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from sqlalchemy import delete, select
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.sec_filing.table import sec_filing_table

__all__ = ["StoredFiling", "SecFilingRepository"]


@dataclass(frozen=True)
class StoredFiling:
    source_locator: str
    cik: str
    accession: str
    form_type: str | None
    period_end: str | None
    filed_at: str | None
    primary_document: str
    primary_document_url: str
    primary_document_sha256: str | None
    primary_document_bytes: int | None
    instance_document: str | None
    instance_url: str | None
    instance_sha256: str | None
    instance_bytes: int | None
    fact_count: int
    dimensioned_fact_count: int
    reader_version: str
    observed_at: str


class SecFilingRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        from atlas.core.infrastructure.persistence.sec_filing.table import create_sec_filing_tables

        create_sec_filing_tables(engine)

    def store(self, filings: Iterable[StoredFiling], *, observed_at: datetime) -> int:
        """Delete-then-insert per `source_locator`, so re-ingesting one
        filing replaces its own row and touches no other."""
        rows = list(filings)
        if not rows:
            return 0
        stamp = observed_at.isoformat()
        seen: set[str] = set()
        payload = []
        for filing in rows:
            if filing.source_locator in seen:
                continue
            seen.add(filing.source_locator)
            record = {c.name: getattr(filing, c.name) for c in sec_filing_table.columns}
            record["observed_at"] = stamp
            payload.append(record)
        with self._engine.begin() as connection:
            connection.execute(
                delete(sec_filing_table).where(
                    sec_filing_table.c.source_locator.in_([r["source_locator"] for r in payload])
                )
            )
            connection.execute(sec_filing_table.insert(), payload)
        return len(payload)

    def query(self, *, cik: str | None = None, form_type: str | None = None,
              period_end: str | None = None) -> tuple[StoredFiling, ...]:
        """Filings matching every filter given. Generic on purpose: this
        answers "which filings does Atlas hold", never "which filings
        support a strategy"."""
        statement = select(sec_filing_table)
        if cik:
            statement = statement.where(sec_filing_table.c.cik == cik)
        if form_type:
            statement = statement.where(sec_filing_table.c.form_type == form_type)
        if period_end:
            statement = statement.where(sec_filing_table.c.period_end == period_end)
        with self._engine.begin() as connection:
            rows = connection.execute(statement.order_by(sec_filing_table.c.source_locator)).mappings().all()
        return tuple(StoredFiling(**{c.name: row[c.name] for c in sec_filing_table.columns}) for row in rows)
