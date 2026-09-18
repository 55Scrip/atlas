"""SQL schema for dimensional evidence.

**The names carry no provider.** These tables were born as
`esef_dimensional_fact` and `esef_dimensional_fact_axis`, when ESEF was
the only source that had them. SEC Inline XBRL now stores the same
shape through the same contract, so the source belongs in
`source_locator` and `reader_version` -- which record exactly which
report and which reader produced a row -- and not in the table name. A
name that says ESEF over rows that are half SEC is a lie the schema
tells every reader of it.

Plural, and a child table named for its parent -- the convention
`business_records` and
`canonical_securities`/`canonical_security_identifiers` already set
here. Hence `dimensional_facts` and `dimensional_fact_axes`.

Axes rather than dimensions, because the columns are `axis_qname` and
`member_qname` and the distinction Sprint 11 exists to protect is about
axes: `SegmentConsolidationItemsAxis` is an axis that is not a segment,
and naming the table for the generic word would blur the one thing it
is there to keep sharp.

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
precisely described. So the value lives once, in `dimensional_facts`,
and its axes hang off it in `dimensional_fact_axes`.

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
    "dimensional_facts",
    metadata,
    Column("fact_key", String, primary_key=True),
    Column("entity", String, nullable=False, index=True),
    Column("concept", String, nullable=False, index=True),
    Column("value_text", String, nullable=False),
    # Whether `value_text` is a number. Stored beside the value rather
    # than left to the reader, so a consumer reading only this table
    # cannot mistake a transform-error sentinel for an observation.
    Column("value_status", String, nullable=False),
    # Size and digest of the value AS FILED. A US-GAAP `*TextBlock` fact
    # carries an entire disclosure note as embedded HTML -- 190 of the
    # 7,915 facts in four SEC filings are 91.3% of all their value bytes,
    # the largest 291 KB. Storing those inline would grow this database
    # by 15.5 MB for four filings and roughly a gigabyte for the corpus,
    # to hold bytes nothing queries. Above `VALUE_INLINE_LIMIT` the body
    # stays in the content-addressed filing cache and `value_text` holds
    # an explicit elision marker instead -- never a silent truncation.
    # These two columns make the elision checkable: the digest is of the
    # full original, so a body recovered from the cache can be proved to
    # be the one that was filed.
    Column("value_bytes", Integer, nullable=True),
    Column("value_digest", String, nullable=True),
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
    "dimensional_fact_axes",
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
