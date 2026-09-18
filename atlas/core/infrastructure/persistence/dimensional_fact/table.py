"""SQL schema for dimensional evidence.

Own `MetaData`, no foreign keys into any existing table -- the same
convention every other bounded context here follows, and for a stronger
reason than usual: nothing that already exists may acquire a
relationship to this data. Consolidated facts feed Financial Risk,
valuation and the Investment Case today; dimensional facts feed nothing
yet, and a foreign key would be the first thread of a connection this
sprint is not making.

**Two tables, not one.** A fact can carry several axes -- 430 of the
6,177 in the cached corpus do -- and the obvious shortcut of one row per
(fact, axis) pair would repeat the *value* once per axis. Anything that
later summed a column would double-count a figure for the crime of being
precisely described. So the value lives once, in `esef_dimensional_fact`,
and its axes hang off it in `esef_dimensional_fact_axis`.

`fact_key` is the semantic identity -- concept, entity, period, unit and
the sorted dimension set -- so re-ingesting a report replaces rather than
duplicates, and a report that lists two axes in a different order does
not produce a second row.
"""
from __future__ import annotations

from sqlalchemy import Column, Index, Integer, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

dimensional_fact_table = Table(
    "esef_dimensional_fact",
    metadata,
    Column("fact_key", String, primary_key=True),
    Column("entity", String, nullable=False, index=True),
    Column("concept", String, nullable=False, index=True),
    Column("value_text", String, nullable=False),
    # Whether `value_text` is a number. Stored beside the value rather
    # than left to the reader, so a consumer reading only this table
    # cannot mistake a transform-error sentinel for an observation.
    Column("value_status", String, nullable=False),
    Column("decimals", Integer, nullable=True),
    Column("unit", String, nullable=True),
    Column("period_raw", String, nullable=False),
    Column("period_kind", String, nullable=False),
    Column("period_end", String, nullable=True, index=True),
    Column("report_fact_id", String, nullable=False),
    Column("source_locator", String, nullable=False),
    Column("reader_version", String, nullable=False),
    Column("observed_at", String, nullable=False),
)

dimensional_fact_axis_table = Table(
    "esef_dimensional_fact_axis",
    metadata,
    Column("fact_key", String, primary_key=True),
    Column("axis_qname", String, primary_key=True),
    Column("member_qname", String, nullable=False),
    Column("axis_class", String, nullable=False, index=True),
    Column("axis_namespace", String, nullable=False),
    Column("member_namespace", String, nullable=False),
)

Index("ix_esef_dim_axis_member", dimensional_fact_axis_table.c.member_qname)


def create_dimensional_fact_tables(engine: Engine) -> None:
    sync_table_schema(engine, dimensional_fact_table)
    sync_table_schema(engine, dimensional_fact_axis_table)
