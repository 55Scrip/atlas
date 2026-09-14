"""SQL schema for class economic-rights evidence: one completion row per
filing and parser version, one row per observation. Append-only, created
only by the operator's write path; the read path never creates them."""
from __future__ import annotations

from sqlalchemy import Column, Float, Integer, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

__all__ = ["class_rights_filings_table", "class_rights_observations_table", "create_class_rights_evidence_tables"]

metadata = MetaData()

class_rights_filings_table = Table(
    "class_rights_filings",
    metadata,
    Column("accession", String, primary_key=True),
    Column("parser_version", String, primary_key=True),
    Column("issuer_cik", String, nullable=False, index=True),
    Column("form", String, nullable=False),
    Column("filing_date", String, nullable=False),
    Column("document_period_end", String, nullable=True),
    Column("presented_from", String, nullable=True),
    Column("instance_url", String, nullable=False),
    Column("observations", Integer, nullable=False),
    Column("retrieved_at", String, nullable=False),
    Column("recorded_at", String, nullable=False),
)

class_rights_observations_table = Table(
    "class_rights_observations",
    metadata,
    Column("accession", String, primary_key=True),
    Column("observation_key", String, primary_key=True),
    Column("parser_version", String, primary_key=True),
    Column("evidence_type", String, nullable=False),
    Column("issuer_cik", String, nullable=False, index=True),
    Column("form", String, nullable=False),
    Column("filing_date", String, nullable=False),
    Column("kind", String, nullable=False),
    Column("strength", String, nullable=False),
    Column("subject_member", String, nullable=True),
    Column("subject_label", String, nullable=True),
    Column("target_member", String, nullable=True),
    Column("target_label", String, nullable=True),
    Column("related_members", String, nullable=False),
    Column("related_labels", String, nullable=False),
    Column("value", Float, nullable=True),
    Column("value_low", Float, nullable=True),
    Column("value_high", Float, nullable=True),
    Column("unit", String, nullable=True),
    Column("decimals", String, nullable=True),
    Column("equity_kind", String, nullable=True),
    Column("effective_from", String, nullable=False),
    Column("effective_to", String, nullable=False),
    Column("concept", String, nullable=False),
    Column("context_id", String, nullable=False),
    Column("excerpt", String, nullable=True),
    Column("retrieved_at", String, nullable=False),
    Column("recorded_at", String, nullable=False),
)


def create_class_rights_evidence_tables(engine: Engine) -> None:
    sync_table_schema(engine, class_rights_filings_table)
    sync_table_schema(engine, class_rights_observations_table)
