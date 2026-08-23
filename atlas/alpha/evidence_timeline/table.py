"""SQL schema for the Evidence Timeline snapshot store. Mirrors
`atlas.alpha.investment_case_change.table.investment_case_snapshot_table`'s
own shape exactly -- structural columns for what a caller queries by
(`case_id`, ordering by `captured_at`), plus one JSON column for the
comparison-relevant structured content and one for the persisted,
never-recomputed `EvidenceHistory` transition this row itself produced
against its immediate predecessor (the same "persist the historical
interpretation at the time, not deterministically recomputed later"
discipline that table's own `change_intelligence_json` column
documents).

`id` is a synthetic, deterministic `f"{case_id}:{captured_at}"`, for
the identical reason that table's own docstring gives.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

evidence_snapshot_table = Table(
    "evidence_snapshots",
    metadata,
    Column("id", String, primary_key=True),
    Column("case_id", String, nullable=False, index=True),
    Column("captured_at", String, nullable=False),
    Column("content_hash", String, nullable=False),
    Column("snapshot_json", String, nullable=False),
    Column("evidence_history_json", String, nullable=True),
)


def create_evidence_snapshot_table(engine: Engine) -> None:
    sync_table_schema(engine, evidence_snapshot_table)
