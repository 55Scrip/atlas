"""SQL schema for Security Identity Evidence (Sprint 23).

Own `MetaData`, no SQL ForeignKey -- `confirmation_id` is a plain
indexed string column referencing `security_confirmations.id`,
matching every other Alpha persistence table's convention for
referencing a sibling aggregate (see
`atlas.alpha.security_confirmation.table`'s own identical reasoning).

Append-only from the start (Sprint 22's own lesson applied up front
rather than retrofitted): no unique constraint on `confirmation_id` --
multiple evidence rows are the normal, expected shape (one row per
verification attempt), read back via `repository.get_latest`'s own
`ORDER BY ... DESC LIMIT 1`, the same idiom
`security_confirmation.repository.get_latest_event` already
established.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

security_identity_evidence_table = Table(
    "security_identity_evidence",
    metadata,
    Column("id", String, primary_key=True),
    Column("confirmation_id", String, nullable=False, index=True),
    Column("provider", String, nullable=False),
    Column("status", String, nullable=False),
    Column("provider_identifier", String, nullable=True),
    Column("verified_ticker", String, nullable=True),
    Column("verified_name", String, nullable=True),
    Column("exchange", String, nullable=True),
    Column("provider_response_json", String, nullable=False),
    Column("verified_at", String, nullable=False),
)


def create_security_identity_evidence_table(engine: Engine) -> None:
    sync_table_schema(engine, security_identity_evidence_table)
