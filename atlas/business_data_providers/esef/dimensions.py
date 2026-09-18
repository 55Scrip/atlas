"""The facts ESEF normalization throws away.

`normalization._undimensioned` keeps the consolidated figure and drops
everything else, which is correct for the job it does -- taking the first
match returned 533,269 MSEK for Volvo's 2023 revenue when the
consolidated number is 552,764 MSEK. But the facts it drops are 35% of
the corpus: 6,177 of 17,281 facts across the 32 cached reports, including
segment-level research spending and segment-level purchases of tangible
and intangible assets. Atlas downloads them, parses them and discards
them.

This module reads the same document and keeps the other half. It changes
nothing about the consolidated path: `duration_facts` and `instant_facts`
are untouched, and a dimensioned fact has never reached them.

**A dimension is not a segment.** The largest axis in the corpus by far
is `ComponentsOfEquityAxis` -- 4,016 facts across 8 issuers -- which
partitions equity into issued capital, retained earnings and reserves.
Reading "has dimensions" as "has segments" would have turned a statement
of changes in equity into eight business units.

**Classification is by exact axis name, never by substring.** An axis
Atlas does not recognise is preserved as UNKNOWN rather than guessed at,
because a wrong class is worse than an unread one: it invites arithmetic
across things that do not belong together.
"""
from __future__ import annotations

from datetime import date, timedelta

from atlas.business_data_providers.dimensional_evidence import (
    INTRINSIC_DIMENSIONS,
    AxisClass,
    Dimension,
    DimensionalFact,
    PeriodKind,
    ValueStatus,
    classify_value,
)

__all__ = [
    "DIMENSION_READER_VERSION",
    "AxisClass",
    "PeriodKind",
    "Dimension",
    "DimensionalFact",
    "classify_axis",
    "ValueStatus",
    "classify_value",
    "dimensional_facts",
    "INTRINSIC_DIMENSIONS",
]

DIMENSION_READER_VERSION = "esef-dimensions-1"


_AXIS_CLASS: dict[str, AxisClass] = {
    "ifrs-full:SegmentsAxis": AxisClass.BUSINESS_SEGMENT,
    "ifrs-full:SegmentConsolidationItemsAxis": AxisClass.CONSOLIDATION_SCOPE,
    "ifrs-full:ContinuingAndDiscontinuedOperationsAxis": AxisClass.CONSOLIDATION_SCOPE,
    "ifrs-full:ComponentsOfEquityAxis": AxisClass.EQUITY_COMPONENT,
    "ifrs-full:RetrospectiveApplicationAndRetrospectiveRestatementAxis": (
        AxisClass.RESTATEMENT_BASIS
    ),
}


def classify_axis(axis_qname: str) -> AxisClass:
    """The class of an axis, by exact name.

    Unrecognised axes are UNKNOWN and keep every character of their
    identity. The corpus contains one such case already -- a bare
    `noteId` key that is a document artefact rather than an axis -- and
    an ingestion that guessed at it would be inventing a dimension."""
    return _AXIS_CLASS.get(axis_qname, AxisClass.UNKNOWN)

def _period(period_raw: str) -> tuple[PeriodKind, str | None]:
    """Instant or duration, and the date the figure belongs to.

    Reuses the consolidated reader's correction: XBRL writes a closing
    balance as the following midnight, so 2024-12-31 arrives as
    2025-01-01."""
    if not period_raw:
        return PeriodKind.UNKNOWN, None
    try:
        if "/" in period_raw:
            end = date.fromisoformat(period_raw.split("/")[1][:10]) - timedelta(days=1)
            return PeriodKind.DURATION, end.isoformat()
        instant = date.fromisoformat(period_raw[:10]) - timedelta(days=1)
        return PeriodKind.INSTANT, instant.isoformat()
    except (TypeError, ValueError):
        return PeriodKind.UNKNOWN, None


def dimensional_facts(document: dict, *, source_locator: str = "") -> tuple[DimensionalFact, ...]:
    """Every dimensioned fact in one xbrl-json report.

    The exact complement of what the consolidated reader keeps: a fact
    appears here if and only if `normalization._undimensioned` would have
    rejected it. Neither reader can see the other's facts, so no figure
    can be counted twice by running both."""
    out: list[DimensionalFact] = []
    for fact_id, fact in (document.get("facts") or {}).items():
        raw = fact.get("dimensions") or {}
        axes = {a: m for a, m in raw.items() if a not in INTRINSIC_DIMENSIONS}
        if not axes:
            continue  # the consolidated reader's fact, not this one's
        concept = raw.get("concept")
        if not isinstance(concept, str) or not concept:
            continue
        period_raw = raw.get("period") or ""
        kind, end = _period(period_raw)
        value = fact.get("value")
        decimals = fact.get("decimals")
        out.append(
            DimensionalFact(
                fact_id=str(fact_id),
                entity=str(raw.get("entity") or ""),
                concept=concept,
                value_text="" if value is None else str(value),
                decimals=decimals if isinstance(decimals, int) else None,
                unit=raw.get("unit"),
                period_raw=str(period_raw),
                period_kind=kind,
                period_end=end,
                dimensions=tuple(
                    Dimension(axis_qname=a, member_qname=str(m), axis_class=classify_axis(a))
                    for a, m in sorted(axes.items())
                ),
                source_locator=source_locator,
            )
        )
    return tuple(out)
