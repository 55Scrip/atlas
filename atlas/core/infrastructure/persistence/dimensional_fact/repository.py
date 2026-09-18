"""Storing and querying dimensional evidence.

The query seam is deliberately generic -- by issuer, filing, concept,
axis, axis class, member, period. There is no `segment_capex_for_company`
here and there should not be: Sprint 12 will decide what questions to
ask, and a repository that has already decided is a repository that will
be worked around.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Sequence

from sqlalchemy import and_, delete, select
from sqlalchemy.engine import Engine

from atlas.business_data_providers.esef.dimensions import (
    DIMENSION_READER_VERSION,
    AxisClass,
    Dimension,
    DimensionalFact,
    PeriodKind,
)
from atlas.core.infrastructure.persistence.dimensional_fact.table import (
    create_dimensional_fact_tables,
    dimensional_fact_axis_table,
    dimensional_fact_table,
)

__all__ = ["StoredDimensionalFact", "DimensionalFactRepository"]


@dataclass(frozen=True)
class StoredDimensionalFact:
    fact_key: str
    entity: str
    concept: str
    value_text: str
    value_status: str
    """`ValueStatus.NUMERIC` or `.UNPARSABLE`. A fact whose value the
    issuer's own transform failed to produce is kept verbatim, not
    dropped and not coerced to zero -- but it is marked, so it can
    never be read as a quantity."""
    decimals: int | None
    unit: str | None
    period_raw: str
    period_kind: str
    period_end: str | None
    report_fact_id: str
    source_locator: str
    reader_version: str
    observed_at: str
    dimensions: tuple[Dimension, ...]

    @property
    def axis_classes(self) -> frozenset[AxisClass]:
        return frozenset(d.axis_class for d in self.dimensions)


class DimensionalFactRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        create_dimensional_fact_tables(engine)

    def store(self, facts: Iterable[DimensionalFact], *, observed_at: datetime) -> int:
        """Write facts, replacing any already held under the same
        semantic key.

        Delete-then-insert per key rather than an upsert: a fact's axis
        rows are part of its identity, and leaving a stale axis behind
        would silently change what a stored fact claims.

        Refuses a fact with no `source_locator`. The report is part of
        the semantic key (see `DimensionalFact.semantic_key`), so an
        empty locator would make facts from different filings collide
        and a restated figure would overwrite the original. That is a
        caller error, and it is the kind that produces a plausible
        wrong number rather than a crash, so it is rejected here rather
        than tolerated."""
        facts = list(facts)
        if not facts:
            return 0
        unlocated = [f for f in facts if not f.source_locator]
        if unlocated:
            raise ValueError(
                f"{len(unlocated)} fact(s) carry no source_locator; "
                f"the report is part of a fact's identity "
                f"(first: {unlocated[0].concept} {unlocated[0].period_raw})"
            )
        stamp = observed_at.isoformat()
        with self._engine.begin() as connection:
            keys = [f.semantic_key for f in facts]
            for chunk in (keys[i : i + 400] for i in range(0, len(keys), 400)):
                connection.execute(
                    delete(dimensional_fact_table).where(dimensional_fact_table.c.fact_key.in_(chunk))
                )
                connection.execute(
                    delete(dimensional_fact_axis_table).where(
                        dimensional_fact_axis_table.c.fact_key.in_(chunk)
                    )
                )
            seen: set[str] = set()
            rows = []
            axis_rows = []
            for fact in facts:
                key = fact.semantic_key
                if key in seen:
                    continue  # the same fact twice in one payload is one fact
                seen.add(key)
                rows.append(
                    {
                        "fact_key": key,
                        "entity": fact.entity,
                        "concept": fact.concept,
                        "value_text": fact.value_text,
                        "value_status": fact.value_status.value,
                        "decimals": fact.decimals,
                        "unit": fact.unit,
                        "period_raw": fact.period_raw,
                        "period_kind": fact.period_kind.value,
                        "period_end": fact.period_end,
                        "report_fact_id": fact.fact_id,
                        "source_locator": fact.source_locator,
                        "reader_version": DIMENSION_READER_VERSION,
                        "observed_at": stamp,
                    }
                )
                for dimension in fact.dimensions:
                    axis_rows.append(
                        {
                            "fact_key": key,
                            "axis_qname": dimension.axis_qname,
                            "member_qname": dimension.member_qname,
                            "axis_class": dimension.axis_class.value,
                            "axis_namespace": dimension.axis_namespace,
                            "member_namespace": dimension.member_namespace,
                        }
                    )
            if rows:
                connection.execute(dimensional_fact_table.insert(), rows)
            if axis_rows:
                connection.execute(dimensional_fact_axis_table.insert(), axis_rows)
        return len(seen)

    def query(
        self,
        *,
        entity: str | None = None,
        concept: str | None = None,
        axis_qname: str | None = None,
        axis_class: AxisClass | None = None,
        member_qname: str | None = None,
        period_end: str | None = None,
        source_locator: str | None = None,
    ) -> tuple[StoredDimensionalFact, ...]:
        """Facts matching every filter given, from storage alone.

        Deliberately generic: filters name axes, members, concepts and
        periods -- the vocabulary of the source -- and nothing here
        knows what a strategy is. A question about a strategy is a
        consumer's question, and giving this layer a
        `facts_supporting(strategy)` method would freeze one consumer's
        idea of relevance into the evidence store.

        **The same coordinates can come back more than once.** A fact's
        identity includes the report it was filed in, so a figure
        restated by a later annual report is returned alongside the
        original rather than replacing it -- 25 such disagreements
        exist in the present corpus. A caller that sums results without
        first choosing a filing per `source_locator` will double count.
        That choice is not made here on purpose: preferring the newest
        filing is usually right and sometimes exactly wrong, and this
        layer has no basis to decide which."""
        conditions = []
        if entity:
            conditions.append(dimensional_fact_table.c.entity == entity)
        if concept:
            conditions.append(dimensional_fact_table.c.concept == concept)
        if period_end:
            conditions.append(dimensional_fact_table.c.period_end == period_end)
        if source_locator:
            conditions.append(dimensional_fact_table.c.source_locator == source_locator)

        axis_conditions = []
        if axis_qname:
            axis_conditions.append(dimensional_fact_axis_table.c.axis_qname == axis_qname)
        if axis_class is not None:
            axis_conditions.append(dimensional_fact_axis_table.c.axis_class == axis_class.value)
        if member_qname:
            axis_conditions.append(dimensional_fact_axis_table.c.member_qname == member_qname)

        statement = select(dimensional_fact_table)
        if axis_conditions:
            matching = select(dimensional_fact_axis_table.c.fact_key).where(and_(*axis_conditions))
            conditions.append(dimensional_fact_table.c.fact_key.in_(matching))
        if conditions:
            statement = statement.where(and_(*conditions))
        statement = statement.order_by(
            dimensional_fact_table.c.entity,
            dimensional_fact_table.c.concept,
            dimensional_fact_table.c.period_end,
            dimensional_fact_table.c.fact_key,
        )

        with self._engine.begin() as connection:
            facts = list(connection.execute(statement).mappings())
            if not facts:
                return ()
            keys = [row["fact_key"] for row in facts]
            axes: dict[str, list[Dimension]] = {}
            for chunk in (keys[i : i + 400] for i in range(0, len(keys), 400)):
                for row in connection.execute(
                    select(dimensional_fact_axis_table)
                    .where(dimensional_fact_axis_table.c.fact_key.in_(chunk))
                    .order_by(dimensional_fact_axis_table.c.axis_qname)
                ).mappings():
                    axes.setdefault(row["fact_key"], []).append(
                        Dimension(
                            axis_qname=row["axis_qname"],
                            member_qname=row["member_qname"],
                            axis_class=AxisClass(row["axis_class"]),
                        )
                    )
        return tuple(
            StoredDimensionalFact(
                fact_key=row["fact_key"],
                entity=row["entity"],
                concept=row["concept"],
                value_text=row["value_text"],
                value_status=row["value_status"],
                decimals=row["decimals"],
                unit=row["unit"],
                period_raw=row["period_raw"],
                period_kind=row["period_kind"],
                period_end=row["period_end"],
                report_fact_id=row["report_fact_id"],
                source_locator=row["source_locator"],
                reader_version=row["reader_version"],
                observed_at=row["observed_at"],
                dimensions=tuple(axes.get(row["fact_key"], ())),
            )
            for row in facts
        )

    def axes(self) -> Sequence[tuple[str, str, int]]:
        """Every axis held, with its class and fact count -- the
        inventory a reader needs before trusting any query."""
        with self._engine.begin() as connection:
            rows = connection.execute(
                select(
                    dimensional_fact_axis_table.c.axis_qname,
                    dimensional_fact_axis_table.c.axis_class,
                ).order_by(dimensional_fact_axis_table.c.axis_qname)
            ).all()
        counts: dict[tuple[str, str], int] = {}
        for axis, klass in rows:
            counts[(axis, klass)] = counts.get((axis, klass), 0) + 1
        return tuple(sorted((a, k, n) for (a, k), n in counts.items()))
