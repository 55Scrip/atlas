"""SQL schema for SEC filing provenance.

Own `MetaData`, no foreign keys -- including none into
`dimensional_facts`, although that is where this filing's facts are
stored. The join is by `source_locator`, which is the accession plus
the primary document, and it is deliberately a value rather than a
constraint: the dimensional store must stay usable by a provider that
has no SEC accession at all.

**Why a separate table rather than more columns on the fact.** A
filing's identity is one fact about a document, not 3,283 repetitions
of it. VST's 10-K alone would otherwise carry the same CIK, accession,
form type, filing date and two URLs on every row.

**The raw document is not in here.** The four benchmark filings are
13.5 MB of primary-document HTML between them; the extracted instances
another 13.1 MB. Putting that in an operational SQLite table would grow
it by half its current size to store bytes nothing queries. The bytes
live in a content-addressed cache on disk and this table records the
digest, so a filing can be proved unchanged without reading it.
"""
from __future__ import annotations

from sqlalchemy import Column, Index, Integer, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

sec_filing_table = Table(
    "sec_filings", metadata,
    # The accession plus the primary document -- the same string that
    # goes into each of this filing's facts as `source_locator`.
    Column("source_locator", String, primary_key=True),
    Column("cik", String, nullable=False, index=True),
    Column("accession", String, nullable=False),
    Column("form_type", String, nullable=True),
    Column("period_end", String, nullable=True),
    Column("filed_at", String, nullable=True),
    Column("primary_document", String, nullable=False),
    Column("primary_document_url", String, nullable=False),
    Column("primary_document_sha256", String, nullable=True),
    Column("primary_document_bytes", Integer, nullable=True),
    Column("instance_document", String, nullable=True),
    Column("instance_url", String, nullable=True),
    Column("instance_sha256", String, nullable=True),
    Column("instance_bytes", Integer, nullable=True),
    Column("fact_count", Integer, nullable=False),
    Column("dimensioned_fact_count", Integer, nullable=False),
    Column("reader_version", String, nullable=False),
    Column("observed_at", String, nullable=False),
    Index("ix_sec_filings_cik_period", "cik", "period_end"),
)


def create_sec_filing_tables(engine: Engine) -> None:
    """Additive and idempotent, via the established schema sync."""
    sync_table_schema(engine, sec_filing_table)
