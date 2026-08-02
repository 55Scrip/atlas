"""SQL schema for the Judgment store.

Own MetaData, no foreign key on `subject_target_id` — the subject may
belong to any of the six adopted Domain Object types, each in its own
table, and an ordinary SQL foreign key cannot span a polymorphic
reference (see docs/atlas_domain_object_architecture/
Domain-Object-Implementation-Reconciliation-Plan.md, Section 13). The
`subject_target_type` CHECK constraint is generated directly from
`DomainObjectType`'s own values — the single source of truth — rather
than a hand-duplicated literal list, so the two can never drift apart.
NULL is permitted for `subject_target_type` (the internal-content
form carries no subject at all) and passes the CHECK unconditionally,
per ordinary SQL NULL-comparison semantics.

A second CHECK constraint enforces the paired-nullability rule from
Judgment-Implementation-Design.md Section 31: `subject_target_type` and
`subject_target_id` are both null or both non-null — never one without
the other.
"""
from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

_ADOPTED_TARGET_TYPES = tuple(member.value for member in DomainObjectType)

judgments_table = Table(
    "judgments",
    metadata,
    Column("judgment_id", String, primary_key=True),
    Column("case_id", String, nullable=False, index=True),
    Column("characterization", String, nullable=False),
    Column("subject_target_type", String, nullable=True, index=True),
    Column("subject_target_id", String, nullable=True, index=True),
    Column("recorded_at", String, nullable=False),
    CheckConstraint(
        "subject_target_type IN ({})".format(
            ", ".join(f"'{value}'" for value in _ADOPTED_TARGET_TYPES)
        ),
        name="ck_judgments_subject_target_type_adopted",
    ),
    CheckConstraint(
        "(subject_target_type IS NULL AND subject_target_id IS NULL) OR "
        "(subject_target_type IS NOT NULL AND subject_target_id IS NOT NULL)",
        name="ck_judgments_subject_reference_paired",
    ),
)


def create_judgment_table(engine: Engine) -> None:
    sync_table_schema(engine, judgments_table)
