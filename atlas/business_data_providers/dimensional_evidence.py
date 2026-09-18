"""The provider-neutral contract for dimensional evidence.

Extracted unchanged from `esef/dimensions.py` (Dimensional Evidence
Ingestion v1) when SEC Inline XBRL arrived and needed the identical
semantics. Nothing here was renamed or redesigned: the ESEF module
imports these names back and re-exports them, so every existing import
keeps working and the ESEF reader's behaviour is byte-identical.

One contract rather than two, for the reasons Sprint 11 gave for its
own rules. A fact's identity includes the report that filed it,
because a later report restates an earlier one. An axis is classified
by exact QName, because a substring rule gets
`SegmentConsolidationItemsAxis` backwards. A member's spelling is the
issuer's. A value that will not parse is evidence, not a number. Each
of those is true of an SEC filing for the same reason it is true of an
ESEF one, and a second, subtly different implementation of them would
be a second set of bugs.

What is deliberately *not* here is any taxonomy. `AxisClass` says what
an axis partitions; which QName means which class is a question about
IFRS or US-GAAP specifically, and each provider module answers it for
its own taxonomy against its own evidence.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

__all__ = [
    "INTRINSIC_DIMENSIONS",
    "VALUE_INLINE_LIMIT",
    "elide_value",
    "AxisClass",
    "PeriodKind",
    "ValueStatus",
    "Dimension",
    "DimensionalFact",
    "classify_value",
]


INTRINSIC_DIMENSIONS = frozenset({"concept", "entity", "period", "unit", "language"})

#: Values longer than this are kept in the filing cache rather than
#: inline. Chosen well above any real number, date, ISO duration or
#: enumeration URI and far below any disclosure note: the largest
#: non-text-block value in the four SEC benchmark filings is under 1 KB,
#: the smallest `*TextBlock` over 9 KB.
VALUE_INLINE_LIMIT = 4096


def elide_value(value_text: str) -> tuple[str, int, str]:
    """`(stored_text, byte_length, sha256)` for one filed value.

    Short values are returned unchanged. A long one is replaced by a
    marker that names its size and digest, because the failure this
    prevents is a consumer reading a truncated note as the whole note.
    The marker is deliberately not parseable as a number, so
    `classify_value` already calls it UNPARSABLE -- the same answer it
    gives for the original HTML."""
    raw = value_text.encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    if len(raw) <= VALUE_INLINE_LIMIT:
        return value_text, len(raw), digest
    return f"(value elided: {len(raw)} bytes, sha256 {digest})", len(raw), digest


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

    GEOGRAPHY = "geography"
    """Where a figure was earned or held. Added for SEC Inline XBRL
    Evidence Ingestion v1, against measured evidence:
    `srt:StatementGeographicalAxis` carries 84 facts across all four
    benchmark filings. A geography is not a business -- a company can
    report one segment across ten countries -- so the two axes answer
    different questions and must never be summed together."""

    PRODUCT_OR_SERVICE = "product_or_service"
    """What was sold. `srt:ProductOrServiceAxis`, 298 facts across all
    four filings, and routinely *combined* with the segment axis: 15 of
    GOOGL's 81 segment facts and 180 of VST's 388 carry both. The two
    decompose the same total along different lines."""

    LEGAL_ENTITY = "legal_entity"
    """Which legal entity within the group. `srt:ConsolidatedEntitiesAxis`,
    115 facts across GOOGL and VST. Kept distinct from both
    consolidation scope and business segment: a subsidiary is neither
    an elimination nor a reportable segment, and reading it as one
    would attribute a figure to a business the filer never named."""

    UNKNOWN = "unknown"
    """Not recognised. Preserved in full, classified as nothing."""


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

        **Precision is part of the identity too.** A filer may report the
        same figure twice at different roundings -- AMAT's 2025 dividends
        appear as both 1,384m and 1,400m against one context, GOOGL's
        unrecognised tax benefits as both 9,438m and 9,400m. They are
        not two measurements, but they are two statements, and the
        exact one is only recoverable if the rounded one did not
        overwrite it. Which to prefer is again a consumer's decision.
        Verified to change nothing for ESEF: of 150 duplicate-key groups
        in that corpus, none differ in `decimals`.

        The caller is therefore required to pass a `source_locator`
        that identifies the source document -- correctness of the key
        rests on it. Facts carrying an empty locator fall back to
        collapsing across reports, which is why the repository refuses
        them."""
        parts = [self.source_locator, self.concept, self.entity,
                 self.period_raw, self.unit or "",
                 "" if self.decimals is None else str(self.decimals)]
        parts += sorted(f"{d.axis_qname}={d.member_qname}" for d in self.dimensions)
        return hashlib.sha256("|".join(parts).encode()).hexdigest()
