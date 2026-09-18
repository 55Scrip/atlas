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

import hashlib
from dataclasses import dataclass
from decimal import Decimal
from datetime import date, timedelta
from enum import Enum

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

#: What xbrl-json puts in `dimensions` that is not an axis. These
#: describe the fact itself; everything else is a real axis/member pair.
INTRINSIC_DIMENSIONS = frozenset({"concept", "entity", "period", "unit", "language"})


class AxisClass(str, Enum):
    """What an axis partitions.

    Six members, one per behaviour actually observed in the cached
    corpus plus UNKNOWN. Nothing here is aspirational: an axis class
    with no facts behind it would be a claim about data Atlas does not
    have."""

    BUSINESS_SEGMENT = "business_segment"
    """IFRS 8 operating segments -- the reportable parts of a business.
    Only `SegmentsAxis` qualifies, and only because that is the axis IFRS
    defines for it."""

    CONSOLIDATION_SCOPE = "consolidation_scope"
    """Which part of the consolidation a figure belongs to: eliminations,
    entity totals, continuing versus discontinued operations.

    `SegmentConsolidationItemsAxis` is classified here rather than as a
    segment axis, and the distinction matters. Its standard members are
    `EliminationOfIntersegmentAmountsMember`, `OperatingSegmentsMember`
    and `EntitysTotalForSegmentConsolidationItemsMember` -- a
    consolidation vocabulary, not a list of businesses. Volvo also hangs
    its own segment members from it, which is exactly why the axis
    cannot be read as segments: the same axis carries both a business
    unit and the elimination that cancels part of it, and summing them
    as peers would be wrong."""

    EQUITY_COMPONENT = "equity_component"
    """Issued capital, retained earnings, reserves, non-controlling
    interests. The biggest axis in the corpus and the clearest example
    of a dimension that is not a business."""

    RESTATEMENT_BASIS = "restatement_basis"
    """Previously stated versus corrected figures. Two values for one
    period that must never be compared with each other as a change."""

    OTHER_ACCOUNTING_AXIS = "other_accounting_axis"
    """Recognised, and none of the above."""

    UNKNOWN = "unknown"
    """Not recognised. Preserved in full, classified as nothing."""


#: Exact axis QName to class. A dict rather than a pattern, because
#: `SegmentConsolidationItemsAxis` contains the substring "Segment" and
#: is not a segment axis -- a substring rule would get the single most
#: important distinction in this module backwards.
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


class PeriodKind(str, Enum):
    INSTANT = "instant"
    DURATION = "duration"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Dimension:
    """One axis/member pair, with both identities kept raw.

    Nothing is rewritten. Volvo's 2022 taxonomy declares
    `abvolvo:FinancialServciesMember` and
    `abvolvo:FinancialServicesMember` as two separate elements, with the
    misspelling reproduced in the issuer's own label ("Financial Servcies
    (member)"). Correcting it here would overwrite what the filing
    actually says."""

    axis_qname: str
    member_qname: str
    axis_class: AxisClass

    @property
    def axis_namespace(self) -> str:
        return self.axis_qname.split(":", 1)[0] if ":" in self.axis_qname else ""

    @property
    def member_namespace(self) -> str:
        return self.member_qname.split(":", 1)[0] if ":" in self.member_qname else ""

    @property
    def member_is_issuer_extension(self) -> bool:
        """A member the issuer defined rather than took from IFRS. Where
        the identity problems live."""
        return self.member_namespace not in {"ifrs-full", ""}


class ValueStatus(Enum):
    """Whether a filed value is usable as a number.

    A report sometimes carries a transform-error sentinel where a
    figure should be -- `(ixTransformValueError)` appears 19 times in
    the present corpus, always because the issuer's own inline-XBRL
    transform failed. That is source evidence and is preserved
    verbatim, but it is not an observation of a quantity, and a
    consumer must not be able to mistake it for one by reading
    `value_text` alone."""

    NUMERIC = "numeric"
    UNPARSABLE = "unparsable"


def classify_value(value_text: str) -> ValueStatus:
    """Numeric or not, decided only by whether it parses.

    No allow-list of known sentinels: a sentinel this reader has never
    seen must land in UNPARSABLE rather than be taken for a number."""
    try:
        Decimal(value_text)
    except (ArithmeticError, TypeError, ValueError):
        return ValueStatus.UNPARSABLE
    return ValueStatus.NUMERIC


@dataclass(frozen=True)
class DimensionalFact:
    """One reported figure that is *not* the consolidated one."""

    fact_id: str
    """The report's own identifier for the fact (`fact-151`)."""
    entity: str
    """The filer, as the report states it -- an LEI scheme string."""
    concept: str
    value_text: str
    """Kept as text. `decimals` describes the precision the issuer
    claimed, and parsing to float here would discard it silently."""
    decimals: int | None
    unit: str | None
    period_raw: str
    period_kind: PeriodKind
    period_end: str | None
    """The date the figure belongs to, with XBRL's following-midnight
    convention already undone -- the same correction the consolidated
    reader makes, so the two agree about what year a fact is in."""
    dimensions: tuple[Dimension, ...]
    source_locator: str
    """Which cached report this came from."""

    @property
    def value_status(self) -> ValueStatus:
        """Whether `value_text` is a number. Derived, never stored on
        the instance, so it cannot drift from the value it describes."""
        return classify_value(self.value_text)

    @property
    def axis_classes(self) -> frozenset[AxisClass]:
        return frozenset(d.axis_class for d in self.dimensions)

    @property
    def is_business_segment(self) -> bool:
        return AxisClass.BUSINESS_SEGMENT in self.axis_classes

    @property
    def semantic_key(self) -> str:
        """What makes two facts the same fact.

        The source report, then concept, entity, period, unit and the
        full dimension set. Unit is in the key because the same concept
        for the same period in SEK and in EUR are two facts, and period
        is in it because an instant and a duration ending on one date
        are not the same measurement. The dimension set is sorted so
        that a report listing two axes in a different order does not
        produce a second row.

        **The report is part of the identity.** An annual report
        restates the prior year alongside the current one, so the same
        coordinates recur across consecutive filings -- and 25 times in
        the present corpus the two filings disagree: equity restated,
        a share-based-payment tax entry that changes sign, provisions
        restated by 12.7%. Keying without the report made whichever
        filing happened to be ingested last overwrite the other, so
        Atlas could not see that a figure had been restated at all.
        A restatement is evidence; which figure to prefer is a
        consumer's decision, and this layer must not make it silently
        by dropping one of them.

        The caller is therefore required to pass a `source_locator`
        that identifies the source document -- correctness of the key
        rests on it. Facts carrying an empty locator fall back to
        collapsing across reports, which is why the repository refuses
        them."""
        parts = [self.source_locator, self.concept, self.entity,
                 self.period_raw, self.unit or ""]
        parts += sorted(f"{d.axis_qname}={d.member_qname}" for d in self.dimensions)
        return hashlib.sha256("|".join(parts).encode()).hexdigest()


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
