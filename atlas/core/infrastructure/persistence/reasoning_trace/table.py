"""SQL schema for the Reasoning Trace store.

Two tables (docs/atlas_domain_object_architecture/
Reasoning-Trace-Implementation-Design.md, Section 30) — the first
one-to-many typed-reference persistence pattern in this codebase, since
every other typed reference in this codebase is a single inline column
pair on its own one table:

- `reasoning_traces`: the parent record — `id`, `case_id`, `recorded_at`.
- `reasoning_trace_supports`: one row per supporting reference, with a
  synthetic per-row primary key (`reasoning_trace_support_id`), mirroring
  `reasoning_link`'s own established precedent of a synthetic per-row
  primary key rather than a composite one. The composite `UniqueConstraint`
  on (`reasoning_trace_id`, `target_type`, `target_id`) is the first use
  of `UniqueConstraint` anywhere in this codebase — it directly enforces
  the set-semantics conclusion of the design's Section 12/Section 17 at
  the schema level, a schema-level backstop, not the primary enforcement
  (which is INV-013's non-empty check at domain/application construction).

Own MetaData, no foreign key anywhere — the same reasoning as every
other module in this codebase: an ordinary SQL foreign key cannot span
a polymorphic reference, and permanence plus the atomic parent+child
insert (see `sqlalchemy_repository.py`) eliminate the dangling-reference
risk a foreign key would otherwise guard against. The `target_type`
CHECK constraint is generated directly from `DomainObjectType`'s own
values, exactly like Knowledge Reference's own table.
"""
from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, MetaData, String, Table, UniqueConstraint
from sqlalchemy.engine import Engine

from atlas.core.domain.shared.domain_object_type import DomainObjectType

metadata = MetaData()

_ADOPTED_TARGET_TYPES = tuple(member.value for member in DomainObjectType)

reasoning_traces_table = Table(
    "reasoning_traces",
    metadata,
    Column("reasoning_trace_id", String, primary_key=True),
    Column("case_id", String, nullable=False, index=True),
    Column("recorded_at", String, nullable=False),
)

reasoning_trace_supports_table = Table(
    "reasoning_trace_supports",
    metadata,
    Column("reasoning_trace_support_id", String, primary_key=True),
    Column("reasoning_trace_id", String, nullable=False, index=True),
    Column("target_type", String, nullable=False, index=True),
    Column("target_id", String, nullable=False, index=True),
    CheckConstraint(
        "target_type IN ({})".format(
            ", ".join(f"'{value}'" for value in _ADOPTED_TARGET_TYPES)
        ),
        name="ck_reasoning_trace_supports_target_type_adopted",
    ),
    UniqueConstraint(
        "reasoning_trace_id",
        "target_type",
        "target_id",
        name="uq_reasoning_trace_supports_trace_target",
    ),
)


def create_reasoning_trace_tables(engine: Engine) -> None:
    metadata.create_all(engine, tables=[reasoning_traces_table, reasoning_trace_supports_table])
