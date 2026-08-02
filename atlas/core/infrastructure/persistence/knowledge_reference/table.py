"""SQL schema for the Knowledge Reference store.

Own MetaData, no foreign key on `target_id` — the target may belong to
any of the six adopted Domain Object types, each in its own table, and
an ordinary SQL foreign key cannot span a polymorphic reference (see
docs/atlas_domain_object_architecture/
Domain-Object-Implementation-Reconciliation-Plan.md, Section 13). The
`target_type` CHECK constraint is generated directly from
`DomainObjectType`'s own values — the single source of truth — rather
than a hand-duplicated literal list, so the two can never drift apart.
"""
from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

_ADOPTED_TARGET_TYPES = tuple(member.value for member in DomainObjectType)

knowledge_references_table = Table(
    "knowledge_references",
    metadata,
    Column("knowledge_reference_id", String, primary_key=True),
    Column("case_id", String, nullable=False, index=True),
    Column("target_type", String, nullable=False, index=True),
    Column("target_id", String, nullable=False, index=True),
    Column("recorded_at", String, nullable=False),
    CheckConstraint(
        "target_type IN ({})".format(
            ", ".join(f"'{value}'" for value in _ADOPTED_TARGET_TYPES)
        ),
        name="ck_knowledge_references_target_type_adopted",
    ),
)


def create_knowledge_reference_table(engine: Engine) -> None:
    sync_table_schema(engine, knowledge_references_table)
