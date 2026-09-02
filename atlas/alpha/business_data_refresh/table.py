"""SQL schema for the BusinessRecord store (ATLAS-031, Phase 16).

The one persistence gap the ATLAS-022 audit named and deliberately did
not build: `business_data.pipeline.ingest` is a pure function with no
store of its own, and `existing_records` -- "which BusinessRecords
already exist for company X" -- has to survive across process runs for
versioning/duplicate-detection to mean anything in a real refresh, not
just inside one Python process's test.

`id` alone is primary key (already globally unique and stable per
version -- `{lineage_id}:v{n}`), matching `BusinessRecord`'s own
immutability contract: a record is never updated in place, only ever
inserted once. `company` is indexed since every real read pattern
(single-Case lookup, batched multi-Case lookup) filters by it.
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

business_record_table = Table(
    "business_records",
    metadata,
    Column("id", String, primary_key=True),
    Column("lineage_id", String, nullable=False, index=True),
    Column("identifier", String, nullable=False),
    Column("company", String, nullable=False, index=True),
    Column("document_type", String, nullable=False),
    Column("published_at", String, nullable=False),
    Column("provider_id", String, nullable=False),
    Column("source_reference", String, nullable=False),
    Column("content_hash", String, nullable=False),
    Column("version_number", Integer, nullable=False),
    Column("version_created_at", String, nullable=False),
    Column("version_supersedes", String, nullable=True),
    Column("version_provider_revision", String, nullable=True),
    Column("validation_status", String, nullable=False),
    Column("period_start", String, nullable=True),
    Column("period_end", String, nullable=True),
    Column("language", String, nullable=False),
    Column("metadata_json", String, nullable=False),
    Column("provenance_json", String, nullable=False),
    # Sprint O Phase 8 -- identity provenance, added via `sync_table_schema`
    # as nullable columns so every `BusinessRecord` persisted before this
    # sprint (all four values `None`) needs no migration/backfill.
    Column("canonical_security_id", String, nullable=True),
    Column("resolution_version", String, nullable=True),
    Column("identity_resolved_at", String, nullable=True),
    Column("provider_evidence_reference", String, nullable=True),
    # Legacy Identity Provenance Backfill. Nullable so `sync_table_schema`
    # adds it to the existing development database automatically.
    Column("canonical_issuer_id", String, nullable=True, index=True),
)


def create_business_record_table(engine: Engine) -> None:
    sync_table_schema(engine, business_record_table)
