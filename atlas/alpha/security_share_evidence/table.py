"""SQL schema for security-level share-class evidence.

Own `MetaData`, no SQL foreign key (the Alpha persistence convention).
Two tables: one row per processed annual filing (the completion record a
re-run reads), one row per class member and annual period end that filing
reports. Created only by the operator's write path
(`create_security_share_evidence_tables`); the read path never creates
them -- a database the command has not run against simply has no
security-level evidence.
"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

__all__ = [
    "security_share_filings_table",
    "security_share_observations_table",
    "current_share_filings_table",
    "current_share_observations_table",
    "create_security_share_evidence_tables",
    "create_current_share_evidence_tables",
]

metadata = MetaData()

security_share_filings_table = Table(
    "security_share_filings",
    metadata,
    Column("accession", String, primary_key=True),
    Column("issuer_cik", String, nullable=False, index=True),
    Column("form", String, nullable=False),
    Column("filing_date", String, nullable=False),
    Column("fiscal_period", String, nullable=True),
    Column("document_period_end", String, nullable=True),
    Column("instance_url", String, nullable=False),
    Column("cover_rows", Integer, nullable=False),
    Column("dimensioned_cover_rows", Integer, nullable=False),
    Column("observations", Integer, nullable=False),
    Column("proven", Integer, nullable=False),
    Column("ambiguous", Integer, nullable=False),
    Column("no_link", Integer, nullable=False),
    Column("conflicts", Integer, nullable=False),
    Column("parser_version", String, nullable=False),
    Column("processed_at", String, nullable=False),
)

security_share_observations_table = Table(
    "security_share_observations",
    metadata,
    Column("accession", String, primary_key=True),
    Column("class_member", String, primary_key=True),
    Column("period_end", String, primary_key=True),
    Column("issuer_cik", String, nullable=False, index=True),
    Column("form", String, nullable=False),
    Column("filing_date", String, nullable=False),
    Column("fiscal_period", String, nullable=True),
    Column("document_period_end", String, nullable=True),
    Column("class_axis", String, nullable=False),
    Column("shares", Float, nullable=True),
    Column("conflict", Boolean, nullable=False),
    Column("source_concept", String, nullable=False),
    Column("context_id", String, nullable=False),
    Column("link_kind", String, nullable=False),
    Column("cover_title", String, nullable=True),
    Column("cover_symbol", String, nullable=True, index=True),
    Column("cover_exchange", String, nullable=True),
    Column("cover_mic", String, nullable=True),
    Column("parser_version", String, nullable=False),
    Column("recorded_at", String, nullable=False),
)


#: Current Share-Count Evidence v1: cover-page counts, a separate evidence
#: type in separate, append-only tables. A filing is recorded once per
#: parser version and never rewritten.
current_share_filings_table = Table(
    "current_share_filings",
    metadata,
    Column("accession", String, primary_key=True),
    Column("parser_version", String, primary_key=True),
    Column("issuer_cik", String, nullable=False, index=True),
    Column("form", String, nullable=False),
    Column("filing_date", String, nullable=False),
    Column("document_period_end", String, nullable=True),
    Column("fiscal_period", String, nullable=True),
    Column("instance_url", String, nullable=False),
    Column("cover_rows", Integer, nullable=False),
    Column("share_classes_reported", Boolean, nullable=False),
    Column("counts", Integer, nullable=False),
    Column("proven", Integer, nullable=False),
    Column("ambiguous", Integer, nullable=False),
    Column("no_link", Integer, nullable=False),
    Column("conflicts", Integer, nullable=False),
    Column("retrieved_at", String, nullable=False),
    Column("recorded_at", String, nullable=False),
)

current_share_observations_table = Table(
    "current_share_observations",
    metadata,
    Column("accession", String, primary_key=True),
    Column("context_id", String, primary_key=True),
    Column("parser_version", String, primary_key=True),
    Column("evidence_type", String, nullable=False),
    Column("issuer_cik", String, nullable=False, index=True),
    Column("form", String, nullable=False),
    Column("filing_date", String, nullable=False),
    Column("document_period_end", String, nullable=True),
    Column("as_of", String, nullable=False),
    Column("scope", String, nullable=False),
    Column("class_axis", String, nullable=True),
    Column("class_member", String, nullable=True),
    Column("shares", Float, nullable=True),
    Column("unit", String, nullable=False),
    Column("decimals", String, nullable=True),
    Column("conflict", Boolean, nullable=False),
    Column("concept", String, nullable=False),
    Column("link_kind", String, nullable=False),
    Column("cover_title", String, nullable=True),
    Column("cover_symbol", String, nullable=True, index=True),
    Column("cover_exchange", String, nullable=True),
    Column("cover_mic", String, nullable=True),
    Column("retrieved_at", String, nullable=False),
    Column("recorded_at", String, nullable=False),
)


def create_current_share_evidence_tables(engine: Engine) -> None:
    sync_table_schema(engine, current_share_filings_table)
    sync_table_schema(engine, current_share_observations_table)


def create_security_share_evidence_tables(engine: Engine) -> None:
    sync_table_schema(engine, security_share_filings_table)
    sync_table_schema(engine, security_share_observations_table)
