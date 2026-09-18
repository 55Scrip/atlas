"""Filing-level SEC XBRL share-class evidence (Security-Level Share-Class
Evidence v1).

`SecEdgarFundamentalsProvider` reads companyfacts, which flattens a filing
to undimensioned issuer-level facts: an issuer with several classes of
common stock gets one issuer-wide count (or none), never one per listed
security. The class detail lives only in each filing's own XBRL instance,
on `us-gaap:StatementClassOfStockAxis`. This sibling adapter reads that
instance -- through the same `SecEdgarIdentity` headers and the same
`http` fetchers -- and says, per class member, whether *this filing itself*
proves which exchange-listed security the member is.

**The only proof is a shared dimension, inside one filing.** A 2019+
cover page tags each §12(b) security (`dei:Security12bTitle`,
`dei:TradingSymbol`, `dei:SecurityExchangeName`) in a context carrying
one member of the class axis; the balance sheet tags each class's
outstanding shares (`us-gaap:CommonStockSharesOutstanding`) with the
same member. A share fact is linked to a trading symbol only when its
member carries exactly one such cover row in the same instance
(`LinkKind.PROVEN_BY_SHARED_DIMENSION`). Nothing else links:

- no member continuity across filings -- a member one filing leaves
  unlinked is never linked by what a later filing says it is;
- no reading of titles, labels or member names (`"Class A"` is text);
- no "the issuer lists one security, so it must be this class";
- no symbol history (`FB` in a 2021 cover is `FB`).

A filing with §12(b) rows that do not share the class dimension
(one undimensioned row beside class-dimensioned share facts) leaves every
class `AMBIGUOUS`; a filing with no §12(b) row at all (pre-2019 covers,
where one undimensioned `TradingSymbol` may even list several symbols)
leaves every class `NO_LINK`, as does a member with no row of its own
(an unlisted class). Rows for notes or other non-share securities never
produce anything: only a member that carries an eligible share fact is
ever considered -- the member relation, not the row's wording.

**Eligible share facts.** An outstanding-share concept
(`OUTSTANDING_SHARE_CONCEPTS`; weighted-average and cover-date counts are
not), unit `shares`, an instant context whose only dimension is the class
axis, dated at one of the filing's own annual period ends (the end of an
entity-wide duration of about a year, or the day before its start -- the
comparative year-ends the same statements show). Two facts for one member
and date that disagree are kept as a conflict, never resolved.

**Current cover-page counts** (Current Share-Count Evidence v1) are a
separate reading of the same instances: `dei:EntityCommonStockSharesOutstanding`
dated by its own instant (`parse_cover_share_counts`). A class-dimensioned
count links by the same shared-member rule; an undimensioned count links
to an undimensioned §12(b) row only when the filing reports no share
classes at all. Latest 10-K/10-Q filings are located through SEC
submissions, which are never evidence themselves.

Pure parsing and linking are separate from fetching, so a saved instance
reparses with no request. Structural only: no score, no conclusion, no
Atlas identity -- joining a linked symbol to an Atlas security happens
downstream, by CIK, symbol and MIC.
"""
from __future__ import annotations

import io
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

from atlas.business_data_providers.xbrl_instance import (  # the plumbing moved, the names did not
    XBRLDI as _XBRLDI,
    XBRLI as _XBRLI,
    Context as _Context,
    parse_day as _day,
    read_instance as _read_instance,
)
from atlas.business_data_providers.errors import MalformedProviderResponse
from atlas.business_data_providers.http import JsonFetcher, TextFetcher, fetch_text
from atlas.business_data_providers.sec_edgar_identity import SecEdgarIdentity

__all__ = [
    "PARSER_VERSION",
    "COVER_PARSER_VERSION",
    "CLASS_AXIS",
    "OUTSTANDING_SHARE_CONCEPTS",
    "EXCHANGE_MICS",
    "LinkKind",
    "CountScope",
    "CoverRow",
    "CoverShareCount",
    "CoverShareFiling",
    "COVER_SHARE_CONCEPTS",
    "PERIODIC_FORMS",
    "PeriodicFiling",
    "ClassShareFact",
    "ShareClassFiling",
    "FetchedInstance",
    "SecEdgarShareClassProvider",
    "exchange_mic",
    "filing_index_url",
    "parse_share_class_filing",
    "parse_cover_share_counts",
    "latest_periodic_filing",
    "submissions_url",
    "select_instance",
]

#: Stored beside every result: a later parser that reads more (or less)
#: re-processes a filing instead of trusting an older reading.
PARSER_VERSION = "share_class_links_v1"
#: The cover-page share-count reading's own identity (a separate evidence type).
COVER_PARSER_VERSION = "cover_share_counts_v1"

_US_GAAP_PREFIX = "http://fasb.org/us-gaap/"
_DEI_PREFIX = "http://xbrl.sec.gov/dei/"

#: The class axis, as (namespace family, local name) -- the us-gaap
#: namespace carries its taxonomy year, which changes every filing season.
CLASS_AXIS = "us-gaap:StatementClassOfStockAxis"

#: Outstanding-share concepts a class count may come from. Deliberately
#: not `WeightedAverageNumberOf...` (a period average, not a period-end
#: count) and not `dei:EntityCommonStockSharesOutstanding` (the cover
#: count, dated weeks after the period end -- identity only).
OUTSTANDING_SHARE_CONCEPTS = frozenset({"us-gaap:CommonStockSharesOutstanding"})

#: `dei:SecurityExchangeName` is a closed SEC enumeration; its values map
#: to ISO 10383 operating MICs. Generic -- never keyed by issuer or
#: symbol -- and pinned by a test. An exchange name missing here links
#: nothing downstream (no MIC, no join), it is never guessed.
EXCHANGE_MICS = {
    "NASDAQ": "XNAS",
    "NYSE": "XNYS",
    "NYSEAMER": "XASE",
    "NYSEArca": "ARCX",
    "CboeBZX": "BATS",
}

#: An entity-wide duration of about one year is a fiscal year.
_ANNUAL_DAYS = (350, 380)

_ANNUAL_FORMS = frozenset({"10-K", "20-F", "40-F"})


def exchange_mic(exchange_name: str | None) -> str | None:
    return EXCHANGE_MICS.get(exchange_name.strip()) if exchange_name else None


class LinkKind(str, Enum):
    """What one filing proves about one class member. There is no
    continuity kind: a link is proven inside a filing or not at all."""

    PROVEN_BY_SHARED_DIMENSION = "proven_by_shared_dimension"
    AMBIGUOUS = "ambiguous"
    NO_LINK = "no_link"


@dataclass(frozen=True)
class CoverRow:
    """One §12(b) row of a filing's cover page. `class_member` is the
    class-axis member its context carries, `None` for an undimensioned
    row; `other_dimensions` counts any further dimension (such a row
    shares no single member with a share fact)."""

    context_id: str
    class_member: str | None
    other_dimensions: int
    title: str | None
    symbol: str | None
    exchange: str | None
    no_trading_symbol: bool


@dataclass(frozen=True)
class ClassShareFact:
    """One class member's outstanding shares at one annual period end, as
    one filing reports and links it. `shares` is `None` when the filing
    itself reports disagreeing values (`conflict`)."""

    class_member: str
    period_end: date
    shares: float | None
    conflict: bool
    source_concept: str
    context_id: str
    link_kind: LinkKind
    cover: CoverRow | None


@dataclass(frozen=True)
class ShareClassFiling:
    """What one annual filing's instance says about share classes."""

    entity_cik: str | None
    document_type: str | None
    amendment: bool
    document_period_end: date | None
    fiscal_year_focus: str | None
    fiscal_period_focus: str | None
    annual_period_ends: tuple[date, ...]
    cover_rows: tuple[CoverRow, ...]
    facts: tuple[ClassShareFact, ...]

    @property
    def fiscal_period(self) -> str | None:
        if self.fiscal_year_focus and self.fiscal_period_focus:
            return f"{self.fiscal_period_focus}{self.fiscal_year_focus}"
        return None


# -- parsing --------------------------------------------------------------------------------------------






def _family(uri: str) -> str | None:
    if uri.startswith(_US_GAAP_PREFIX):
        return "us-gaap"
    if uri.startswith(_DEI_PREFIX):
        return "dei"
    return None














def _entity_wide(facts, concept: str) -> str | None:
    values = {text for c, ctx, _, text, _ in facts if c == concept and not ctx.explicit and not ctx.typed and text}
    return values.pop() if len(values) == 1 else None


def parse_share_class_filing(instance_xml: str) -> ShareClassFiling:
    """Parse one XBRL instance and link its class share facts. Pure: the
    same instance always gives the same result."""
    contexts, facts = _read_instance(instance_xml)
    document_period_end = _day(_entity_wide(facts, "dei:DocumentPeriodEndDate"))
    annual_durations = [
        ctx for ctx in contexts
        if not ctx.explicit and not ctx.typed and ctx.start and ctx.end
        and _ANNUAL_DAYS[0] <= (ctx.end - ctx.start).days <= _ANNUAL_DAYS[1]
    ]
    annual_period_ends = tuple(sorted(
        {ctx.end for ctx in annual_durations} | {ctx.start - timedelta(days=1) for ctx in annual_durations}
    ))

    cover_rows = _cover_rows(facts)
    return ShareClassFiling(
        entity_cik=(_entity_wide(facts, "dei:EntityCentralIndexKey") or None),
        document_type=_entity_wide(facts, "dei:DocumentType"),
        amendment=(_entity_wide(facts, "dei:AmendmentFlag") or "").lower() == "true",
        document_period_end=document_period_end,
        fiscal_year_focus=_entity_wide(facts, "dei:DocumentFiscalYearFocus"),
        fiscal_period_focus=_entity_wide(facts, "dei:DocumentFiscalPeriodFocus"),
        annual_period_ends=annual_period_ends,
        cover_rows=cover_rows,
        facts=_class_facts(facts, frozenset(annual_period_ends), cover_rows),
    )


_COVER = {
    "dei:Security12bTitle": "title",
    "dei:TradingSymbol": "symbol",
    "dei:SecurityExchangeName": "exchange",
    "dei:NoTradingSymbolFlag": "no_trading_symbol",
}


def _class_member(ctx: _Context) -> tuple[str | None, int]:
    """(the class-axis member, how many other dimensions) of a context."""
    members = [m for d, m in ctx.explicit if d == CLASS_AXIS]
    others = len(ctx.explicit) - len(members) + ctx.typed
    if len(members) > 1:
        return None, others + len(members)
    return (members[0] if members else None), others


def _cover_rows(facts) -> tuple[CoverRow, ...]:
    """Cover rows grouped by their dimensional signature (not by context
    id: one row's facts may sit in more than one context). Only rows with
    a `dei:Security12bTitle` are §12(b) rows."""
    rows: dict[tuple, dict] = {}
    for concept, ctx, _, text, _ in facts:
        field = _COVER.get(concept)
        if field is None:
            continue
        row = rows.setdefault(ctx.explicit + (("#typed", str(ctx.typed)),), {"context_id": ctx.id, "ctx": ctx})
        row.setdefault(field, set()).add(text)
        row["context_id"] = min(row["context_id"], ctx.id)
    out = []
    for row in rows.values():
        titles = row.get("title", set())
        if not titles:
            continue
        member, others = _class_member(row["ctx"])

        def one(field):
            values = row.get(field, set())
            return next(iter(values)) if len(values) == 1 else None

        out.append(CoverRow(
            context_id=row["context_id"],
            class_member=member,
            other_dimensions=others,
            title=one("title"),
            # Two different symbols on one row are not one symbol.
            symbol=one("symbol"),
            exchange=one("exchange"),
            no_trading_symbol=(one("no_trading_symbol") or "").lower() == "true",
        ))
    return tuple(sorted(out, key=lambda r: (r.class_member or "", r.context_id)))


def _link(member: str, cover_rows: tuple[CoverRow, ...]) -> tuple[LinkKind, CoverRow | None]:
    if not cover_rows:
        return LinkKind.NO_LINK, None
    own = [r for r in cover_rows if r.class_member == member and r.other_dimensions == 0]
    if len(own) == 1:
        row = own[0]
        listed = row.symbol and row.exchange and not row.no_trading_symbol
        # The same listing on another row (another member, or none) is two
        # claims to one security: not proven.
        rivals = [r for r in cover_rows if r is not row and r.symbol == row.symbol and r.exchange == row.exchange]
        if listed and not rivals:
            return LinkKind.PROVEN_BY_SHARED_DIMENSION, row
        return LinkKind.AMBIGUOUS, None
    if len(own) > 1:
        return LinkKind.AMBIGUOUS, None
    # No row of its own. Beside an undimensioned (or otherwise unshared)
    # row, the member could be that row's security: ambiguous. When every
    # row names another member, this class is not a §12(b) security here.
    if any(r.class_member is None or r.other_dimensions for r in cover_rows):
        return LinkKind.AMBIGUOUS, None
    return LinkKind.NO_LINK, None


def _class_facts(facts, annual_period_ends: frozenset[date], cover_rows) -> tuple[ClassShareFact, ...]:
    by_key: dict[tuple[str, date], list[tuple[str, str, float]]] = {}
    for concept, ctx, unit, text, _ in facts:
        if concept not in OUTSTANDING_SHARE_CONCEPTS or unit != "shares" or ctx.instant is None:
            continue
        member, others = _class_member(ctx)
        if member is None or others or ctx.instant not in annual_period_ends:
            continue
        try:
            value = float(text)
        except ValueError:
            continue
        by_key.setdefault((member, ctx.instant), []).append((concept, ctx.id, value))
    out = []
    for (member, period_end), reported in sorted(by_key.items()):
        values = {v for _, _, v in reported}
        concept, context_id, _ = min(reported)
        kind, row = _link(member, cover_rows)
        out.append(ClassShareFact(
            class_member=member, period_end=period_end,
            shares=values.pop() if len(values) == 1 else None, conflict=len(values) > 1,
            source_concept=concept, context_id=context_id, link_kind=kind, cover=row,
        ))
    return tuple(out)


# -- current cover-page share counts (Current Share-Count Evidence v1) ------------------------------------

#: The cover-page count of outstanding common shares "as of the latest
#: practicable date": dated by its own instant context -- never by the
#: document period end, never by the filing date. A different evidence
#: type from the period-end balance-sheet count `_class_facts` reads.
COVER_SHARE_CONCEPTS = frozenset({"dei:EntityCommonStockSharesOutstanding"})


class CountScope(str, Enum):
    #: One member of the class axis: one class of the filer's stock.
    CLASS = "class"
    #: Undimensioned: the filer's common stock reported as one count.
    ISSUER = "issuer"


@dataclass(frozen=True)
class CoverShareCount:
    """One cover-page share count, as one filing reports and links it.
    `as_of` is the count's own instant. `shares` is `None` when the filing
    reports disagreeing values for the same scope and date (`conflict`)."""

    scope: CountScope
    class_member: str | None
    as_of: date
    shares: float | None
    conflict: bool
    #: The fact's own `decimals`, as reported (`"INF"` exact, `"-6"` rounded to millions).
    decimals: str | None
    concept: str
    context_id: str
    link_kind: LinkKind
    cover: CoverRow | None


@dataclass(frozen=True)
class CoverShareFiling:
    entity_cik: str | None
    document_type: str | None
    amendment: bool
    document_period_end: date | None
    fiscal_year_focus: str | None
    fiscal_period_focus: str | None
    cover_rows: tuple[CoverRow, ...]
    #: Whether any share count in the filing carries a class-axis member:
    #: then an undimensioned cover count is an aggregate, not one security.
    share_classes_reported: bool
    counts: tuple[CoverShareCount, ...]


def _link_undimensioned(cover_rows: tuple[CoverRow, ...], share_classes_reported: bool) -> tuple[LinkKind, CoverRow | None]:
    """An undimensioned count and an undimensioned §12(b) row share the
    default (empty) dimension. That is proof only when the filing reports
    no share classes at all, and exactly one undimensioned listed row
    exists -- otherwise the count may span several classes."""
    if not cover_rows:
        return LinkKind.NO_LINK, None
    if share_classes_reported:
        return LinkKind.AMBIGUOUS, None
    default = [r for r in cover_rows if r.class_member is None and r.other_dimensions == 0]
    if len(default) != 1:
        return LinkKind.AMBIGUOUS, None
    row = default[0]
    rivals = [r for r in cover_rows if r is not row and r.symbol == row.symbol and r.exchange == row.exchange]
    if row.symbol and row.exchange and not row.no_trading_symbol and not rivals:
        return LinkKind.PROVEN_BY_SHARED_DIMENSION, row
    return LinkKind.AMBIGUOUS, None


def parse_cover_share_counts(instance_xml: str) -> CoverShareFiling:
    """Parse one 10-K/10-Q instance's cover-page share counts and link each
    to a §12(b) security by the same-filing rule. Pure."""
    _, facts = _read_instance(instance_xml)
    cover_rows = _cover_rows(facts)
    share_classes_reported = any(
        unit == "shares" and _class_member(ctx)[0] is not None for _, ctx, unit, _, _ in facts
    )
    by_key: dict[tuple[str | None, date], list[tuple[str, str, float, str | None]]] = {}
    for concept, ctx, unit, text, decimals in facts:
        if concept not in COVER_SHARE_CONCEPTS or unit != "shares" or ctx.instant is None:
            continue
        member, others = _class_member(ctx)
        if others:
            continue
        try:
            value = float(text)
        except ValueError:
            continue
        by_key.setdefault((member, ctx.instant), []).append((concept, ctx.id, value, decimals))
    counts = []
    for (member, as_of), reported in sorted(by_key.items(), key=lambda kv: (kv[0][0] or "", kv[0][1])):
        values = {v for _, _, v, _ in reported}
        concept, context_id, _, decimals = min(reported, key=lambda r: r[:3])
        if member is None:
            kind, row = _link_undimensioned(cover_rows, share_classes_reported)
        else:
            kind, row = _link(member, cover_rows)
        counts.append(CoverShareCount(
            scope=CountScope.ISSUER if member is None else CountScope.CLASS, class_member=member, as_of=as_of,
            shares=values.pop() if len(values) == 1 else None, conflict=len(values) > 1,
            decimals=decimals, concept=concept, context_id=context_id, link_kind=kind, cover=row,
        ))
    return CoverShareFiling(
        entity_cik=_entity_wide(facts, "dei:EntityCentralIndexKey") or None,
        document_type=_entity_wide(facts, "dei:DocumentType"),
        amendment=(_entity_wide(facts, "dei:AmendmentFlag") or "").lower() == "true",
        document_period_end=_day(_entity_wide(facts, "dei:DocumentPeriodEndDate")),
        fiscal_year_focus=_entity_wide(facts, "dei:DocumentFiscalYearFocus"),
        fiscal_period_focus=_entity_wide(facts, "dei:DocumentFiscalPeriodFocus"),
        cover_rows=cover_rows,
        share_classes_reported=share_classes_reported,
        counts=tuple(counts),
    )


#: Periodic reports whose cover page states current shares outstanding.
PERIODIC_FORMS = frozenset({"10-K", "10-Q"})


@dataclass(frozen=True)
class PeriodicFiling:
    """Where a filing is -- from SEC submissions, which locate filings and
    are never share-count evidence."""

    accession: str
    form: str
    filing_date: date
    report_date: date | None


def latest_periodic_filing(submissions: object, *, filed_by: date | None = None) -> PeriodicFiling | None:
    """The most recent original 10-K or 10-Q (never an amendment) in a
    filer's submissions, filed on or before `filed_by`."""
    recent = submissions.get("filings", {}).get("recent", {}) if isinstance(submissions, dict) else {}
    columns = [recent.get(k) or [] for k in ("accessionNumber", "form", "filingDate", "reportDate")]
    best = None
    for accession, form, filed, report in zip(*columns):
        filed_on = _day(filed)
        if form not in PERIODIC_FORMS or filed_on is None or (filed_by and filed_on > filed_by):
            continue
        candidate = PeriodicFiling(accession, form, filed_on, _day(report))
        if best is None or (candidate.filing_date, candidate.accession) > (best.filing_date, best.accession):
            best = candidate
    return best


# -- fetching -------------------------------------------------------------------------------------------


def submissions_url(cik: str) -> str:
    return f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"


def filing_index_url(cik: str, accession: str) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/index.json"


def select_instance(index_payload: object) -> str:
    """The XBRL instance's file name from a filing's `index.json`: the
    inline filing's extracted `*_htm.xml`, else the largest `.xml` that is
    not a linkbase or the filing summary."""
    items = index_payload.get("directory", {}).get("item", []) if isinstance(index_payload, dict) else []
    names = [(i.get("name", ""), i.get("size", "")) for i in items if isinstance(i, dict)]
    inline = sorted(n for n, _ in names if n.endswith("_htm.xml"))
    if len(inline) == 1:
        return inline[0]
    candidates = [
        (int(size) if str(size).isdigit() else 0, name) for name, size in names
        if name.endswith(".xml") and name != "FilingSummary.xml"
        and not name.endswith(("_cal.xml", "_def.xml", "_lab.xml", "_pre.xml"))
    ]
    if not candidates:
        raise MalformedProviderResponse("filing index lists no XBRL instance")
    return max(candidates)[1]


@dataclass(frozen=True)
class FetchedInstance:
    cik: str
    accession: str
    instance_name: str
    instance_url: str
    instance_xml: str
    requests: int


class SecEdgarShareClassProvider:
    """Fetches one annual filing's XBRL instance: two keyless requests
    (the filing index, then the instance), with the SEC identity headers
    every SEC provider sends."""

    canonical_provider_name = "SEC_EDGAR"
    annual_forms = _ANNUAL_FORMS

    def __init__(
        self,
        fetch_json_fn: JsonFetcher | None = None,
        fetch_text_fn: TextFetcher | None = None,
        *,
        instance_timeout: float = 90.0,
    ) -> None:
        self._identity = SecEdgarIdentity(fetch_json_fn)
        self._fetch_text = fetch_text_fn
        self._instance_timeout = instance_timeout

    def _text(self, url: str) -> str:
        if self._fetch_text is not None:
            return self._fetch_text(url, self._identity.headers())
        # Large filings' instances run to tens of megabytes.
        return fetch_text(url, self._identity.headers(), timeout=self._instance_timeout)

    def fetch_submissions(self, *, cik: str, on_request=None) -> object:
        """The filer's submissions index: one request, used only to locate filings."""
        if on_request:
            on_request()
        return self._identity.fetch_json(submissions_url(cik))

    def fetch_instance(self, *, cik: str, accession: str, on_request=None) -> FetchedInstance:
        """`on_request()` is called before each request, so a failure
        after the first one is still counted."""
        index_url = filing_index_url(cik, accession)
        if on_request:
            on_request()
        name = select_instance(self._identity.fetch_json(index_url))
        instance_url = index_url.rsplit("/", 1)[0] + "/" + name
        if on_request:
            on_request()
        return FetchedInstance(cik, accession, name, instance_url, self._text(instance_url), 2)
