"""One SEC filing's XBRL instance, read as dimensional evidence.

The SEC counterpart to `esef.dimensions.dimensional_facts`, producing
the identical `DimensionalFact` from a different source format. What is
*not* different: axis and member QNames are preserved exactly as filed,
the report is part of a fact's identity, a value that will not parse
stays evidence rather than becoming a number, and an unrecognised axis
is UNKNOWN rather than guessed.

**It reuses the one XBRL instance parser this repository already has**
(`xbrl_instance.read_instance`, live since the share-class work and
moved out of that adapter when this module needed it). Two parsers
over one grammar would be two sets of bugs. That parser has two limits
this module works around rather than changes, because production code
depends on its current behaviour: it counts a context's *typed*
dimensions without keeping their values, and it resolves a unit built
from a `<divide>` to `None`. Both losses are real -- VST files its
revenue backlog by year as typed members, and every benchmark filing
has one per-share unit -- so `typed_members` and `filing_units` below
read those two things directly and the rest still comes from the one
reader.

**Why the extracted instance and not the inline document.** SEC
publishes, in the same accession folder as the primary Inline XBRL
document, its own extracted `*_htm.xml` instance -- the same facts the
primary document carries inline, in the format the parser above
already reads. The primary document is still fetched and kept: it is
the text, and `filing_content_intelligence` reads its sections and
tables. Splitting the job this way avoids a second, unproven iXBRL
HTML parser whose failures would be silent. `FilingIdentity` records
both URLs so every fact can be traced to the inline document it came
from.

**Entity identity is the CIK, never the ticker.** The context carries
no entity, so the filer is taken from the filing's own
`dei:EntityCentralIndexKey`, falling back to the accession's CIK. A
ticker is display metadata and changes; a CIK does not.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from atlas.business_data_providers.dimensional_evidence import (
    AxisClass,
    Dimension,
    DimensionalFact,
    PeriodKind,
)
from atlas.business_data_providers.sec_filing.axes import classify_sec_axis
from atlas.business_data_providers.xbrl_instance import read_instance

__all__ = ["SEC_FILING_READER_VERSION", "FilingIdentity", "filing_facts", "filing_units",
           "typed_members", "unit_refs"]

SEC_FILING_READER_VERSION = "sec-inline-xbrl-1"


#: A fact element: a prefixed tag carrying `contextRef`. Nil facts are
#: excluded, matching what the shared reader does with them.
_FACT_RE = re.compile(r'<([\w.-]+:[\w.-]+)\b([^>]*\bcontextRef="[^"]*"[^>]*?)/?>')
_CTXREF_RE = re.compile(r'contextRef="([^"]*)"')
_UNITREF_RE = re.compile(r'unitRef="([^"]*)"')
_NIL_RE = re.compile(r'nil="(?:true|1)"')


def unit_refs(instance_xml: str) -> dict[tuple[str, str], list[str | None]]:
    """(concept, context id) -> each fact's `unitRef`, in document order.

    A list rather than a single value because the same concept and
    context can legitimately appear twice with different units: MA
    files eight figures in both USD and INR that way. Collapsing them
    would put one currency's number under the other's unit, which is
    worse than having no unit at all.
    """
    out: dict[tuple[str, str], list[str | None]] = {}
    for concept, attributes in _FACT_RE.findall(instance_xml):
        if _NIL_RE.search(attributes):
            continue
        context = _CTXREF_RE.search(attributes)
        if context is None:
            continue
        unit = _UNITREF_RE.search(attributes)
        out.setdefault((concept, context.group(1)), []).append(unit.group(1) if unit else None)
    return out


#: `<unit id="...">` with either one `<measure>` or a `<divide>`.
_UNIT_RE = re.compile(r'<(?:\w+:)?unit\b[^>]*\bid="([^"]+)"(.*?)</(?:\w+:)?unit>', re.S)
_MEASURE_RE = re.compile(r"<(?:\w+:)?measure>\s*([^<]+?)\s*</(?:\w+:)?measure>", re.S)
_NUM_RE = re.compile(r"<(?:\w+:)?unitNumerator>(.*?)</(?:\w+:)?unitNumerator>", re.S)
_DEN_RE = re.compile(r"<(?:\w+:)?unitDenominator>(.*?)</(?:\w+:)?unitDenominator>", re.S)


def filing_units(instance_xml: str) -> dict[str, str]:
    """Unit id -> the measure as written, namespace and all.

    The shared reader returns a unit's *local name* and, for a unit
    built from a `<divide>`, returns `None`. Both lose something this
    layer must keep. `None` is the same answer it gives for a fact with
    no unit at all, so an earnings-per-share figure becomes
    indistinguishable from a text disclosure -- and every one of the
    four benchmark filings contains exactly one such unit. Dropping the
    namespace is smaller but the same mistake: `iso4217:USD` is a
    currency by construction, `USD` is a string that happens to look
    like one.

    Returns `iso4217:USD`, `xbrli:shares`, `iso4217:USD/xbrli:shares`.
    """
    units: dict[str, str] = {}
    for unit_id, body in _UNIT_RE.findall(instance_xml):
        numerator, denominator = _NUM_RE.search(body), _DEN_RE.search(body)
        if numerator and denominator:
            top = "*".join(_MEASURE_RE.findall(numerator.group(1)))
            bottom = "*".join(_MEASURE_RE.findall(denominator.group(1)))
            if top and bottom:
                units[unit_id] = f"{top}/{bottom}"
                continue
        measures = _MEASURE_RE.findall(body)
        if measures:
            units[unit_id] = "*".join(measures)
    return units


#: `<xbrldi:typedMember dimension="...">` inside a context, with whatever
#: element the filer put in it. Matched on the raw XML rather than the
#: parsed tree because the shared instance reader does not expose typed
#: members at all -- it records only how many a context had.
_CONTEXT_RE = re.compile(r'<(?:\w+:)?context\b[^>]*\bid="([^"]+)"(.*?)</(?:\w+:)?context>', re.S)
_TYPED_RE = re.compile(
    r'<(?:\w+:)?typedMember\b[^>]*\bdimension="([^"]+)"[^>]*>(.*?)</(?:\w+:)?typedMember>', re.S)
_TAGS_RE = re.compile(r"<[^>]+>")


def typed_members(instance_xml: str) -> dict[str, tuple[tuple[str, str], ...]]:
    """Context id -> its typed dimensions, as (dimension, value).

    The shared instance reader reports a context's typed dimensions as a
    *count* and discards what was in them. That is enough for the
    share-class work it was written for and not enough here: VST files
    its remaining-performance-obligation by time band as six facts that
    differ only in a typed member, so dropping the values collapses six
    real figures -- 1,768m, 1,665m, 733m, 215m, 215m, 3,293m -- into
    one. Reading them here is a complement, not a second parser: the
    facts, contexts, units and explicit dimensions still come from the
    one reader, and nothing about its behaviour changes.

    The typed value is the element content with tags stripped, because a
    typed member's content is filer-defined and Atlas has no schema for
    it -- keeping the text as filed is the only honest option.
    """
    out: dict[str, tuple[tuple[str, str], ...]] = {}
    for context_id, body in _CONTEXT_RE.findall(instance_xml):
        members = tuple(
            (dimension, " ".join(_TAGS_RE.sub(" ", inner).split()))
            for dimension, inner in _TYPED_RE.findall(body)
        )
        if members:
            out[context_id] = tuple(sorted(members))
    return out


@dataclass(frozen=True)
class FilingIdentity:
    """Everything needed to say where a fact came from.

    `source_locator` is what goes into a fact's semantic key, and it is
    the accession plus the primary document rather than a URL: the
    accession is SEC's own permanent identifier for one filing, while a
    URL is a location that can change."""

    cik: str
    accession: str
    primary_document: str
    primary_document_url: str
    instance_document: str
    instance_url: str
    form_type: str | None = None
    period_end: str | None = None
    filed_at: str | None = None

    @property
    def source_locator(self) -> str:
        return f"{self.accession}:{self.primary_document}"


def _period(context) -> tuple[str, PeriodKind, str | None]:
    """The context's period, as filed.

    No following-midnight correction here, unlike the ESEF reader: an
    xbrl-json document writes a closing balance as the next day's
    midnight, but an SEC XML context writes the real end date. Applying
    ESEF's correction would move every SEC figure back one day.
    """
    if context.instant is not None:
        return context.instant.isoformat(), PeriodKind.INSTANT, context.instant.isoformat()
    if context.start is not None and context.end is not None:
        return (f"{context.start.isoformat()}/{context.end.isoformat()}",
                PeriodKind.DURATION, context.end.isoformat())
    return "", PeriodKind.UNKNOWN, None


def _entity_wide(facts, concept: str) -> str | None:
    values = {text for c, ctx, _, text, _ in facts
              if c == concept and not ctx.explicit and not ctx.typed and text}
    return values.pop() if len(values) == 1 else None


def filing_facts(
    instance_xml: str, identity: FilingIdentity
) -> tuple[FilingIdentity, tuple[DimensionalFact, ...]]:
    """Every non-nil fact in one filing, dimensioned or not.

    Unlike the ESEF reader, this does *not* partition the document.
    ESEF has a separate consolidated reader that owns undimensioned
    facts, and the two must not overlap. Here CompanyFacts owns the
    consolidated numbers Atlas actually uses and this layer has no
    production consumer at all, so withholding undimensioned facts
    would discard evidence -- a segment total is only interpretable
    beside the company total it belongs to -- without protecting
    anything. Nothing downstream can double count, because nothing
    downstream reads this.
    """
    _, raw = read_instance(instance_xml)
    typed = typed_members(instance_xml)
    units = filing_units(instance_xml)
    pending = {key: list(values) for key, values in unit_refs(instance_xml).items()}

    cik = _entity_wide(raw, "dei:EntityCentralIndexKey") or identity.cik
    resolved = FilingIdentity(
        cik=f"{int(cik):010d}" if cik.isdigit() else cik,
        accession=identity.accession,
        primary_document=identity.primary_document,
        primary_document_url=identity.primary_document_url,
        instance_document=identity.instance_document,
        instance_url=identity.instance_url,
        form_type=identity.form_type or _entity_wide(raw, "dei:DocumentType"),
        period_end=identity.period_end or _entity_wide(raw, "dei:DocumentPeriodEndDate"),
        filed_at=identity.filed_at,
    )

    facts: list[DimensionalFact] = []
    for concept, context, _shared_unit, text, decimals in raw:
        period_raw, kind, period_end = _period(context)
        # Explicit and typed dimensions together. A typed member is
        # classified UNKNOWN: its content is filer-defined, so Atlas
        # cannot say what it partitions without a schema it does not have.
        pairs = [(axis, member, classify_sec_axis(axis)) for axis, member in context.explicit]
        pairs += [(axis, value, AxisClass.UNKNOWN) for axis, value in typed.get(context.id, ())]
        dimensions = tuple(
            Dimension(axis_qname=axis, member_qname=member, axis_class=axis_class)
            for axis, member, axis_class in sorted(pairs)
        )
        queue = pending.get((concept, context.id))
        unit_id = queue.pop(0) if queue else None
        # Fall back to the shared reader's local name only when this
        # index has nothing to say, so a miss degrades rather than lies.
        unit = units.get(unit_id) if unit_id else (_shared_unit or None)
        try:
            precision = int(decimals) if decimals not in (None, "", "INF") else None
        except ValueError:
            precision = None
        facts.append(
            DimensionalFact(
                fact_id=f"{context.id}:{concept}",
                entity=resolved.cik,
                concept=concept,
                value_text=text,
                decimals=precision,
                unit=unit,
                period_raw=period_raw,
                period_kind=kind,
                period_end=period_end,
                dimensions=dimensions,
                source_locator=resolved.source_locator,
            )
        )
    return resolved, tuple(facts)
