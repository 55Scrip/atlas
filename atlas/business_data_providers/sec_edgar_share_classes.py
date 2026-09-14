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

from atlas.business_data_providers.errors import MalformedProviderResponse
from atlas.business_data_providers.http import JsonFetcher, TextFetcher, fetch_text
from atlas.business_data_providers.sec_edgar_identity import SecEdgarIdentity

__all__ = [
    "PARSER_VERSION",
    "CLASS_AXIS",
    "OUTSTANDING_SHARE_CONCEPTS",
    "EXCHANGE_MICS",
    "LinkKind",
    "CoverRow",
    "ClassShareFact",
    "ShareClassFiling",
    "FetchedInstance",
    "SecEdgarShareClassProvider",
    "exchange_mic",
    "filing_index_url",
    "parse_share_class_filing",
    "select_instance",
]

#: Stored beside every result: a later parser that reads more (or less)
#: re-processes a filing instead of trusting an older reading.
PARSER_VERSION = "share_class_links_v1"

_XBRLI = "http://www.xbrl.org/2003/instance"
_XBRLDI = "http://xbrl.org/2006/xbrldi"
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


@dataclass(frozen=True)
class _Context:
    id: str
    instant: date | None
    start: date | None
    end: date | None
    explicit: tuple[tuple[str, str], ...]  # (dimension, member), normalised
    typed: int


def _day(text: str | None) -> date | None:
    try:
        return date.fromisoformat(text.strip()[:10]) if text else None
    except ValueError:
        return None


def _family(uri: str) -> str | None:
    if uri.startswith(_US_GAAP_PREFIX):
        return "us-gaap"
    if uri.startswith(_DEI_PREFIX):
        return "dei"
    return None


class _Names:
    """QName normalisation. Standard taxonomies are named by family
    (`us-gaap:`, `dei:`) because their namespace URI carries a year; a
    company extension keeps the prefix the filing itself declares."""

    def __init__(self, prefixes: dict[str, str]) -> None:
        self._prefixes = prefixes
        self._uri_to_prefix = {uri: prefix for prefix, uri in prefixes.items()}

    def of_tag(self, tag: str) -> str:
        if not tag.startswith("{"):
            return tag
        uri, local = tag[1:].split("}", 1)
        family = _family(uri)
        return f"{family or self._uri_to_prefix.get(uri, uri)}:{local}"

    def of_qname(self, text: str) -> str:
        text = (text or "").strip()
        if ":" not in text:
            return text
        prefix, local = text.split(":", 1)
        uri = self._prefixes.get(prefix)
        family = _family(uri) if uri else None
        return f"{family or prefix}:{local}"


def _prefixes(instance_xml: str) -> dict[str, str]:
    prefixes: dict[str, str] = {}
    for _, (prefix, uri) in ElementTree.iterparse(io.StringIO(instance_xml), events=("start-ns",)):
        prefixes.setdefault(prefix, uri)
    return prefixes


def _contexts(root, names: _Names) -> dict[str, _Context]:
    out: dict[str, _Context] = {}
    for element in root.iter(f"{{{_XBRLI}}}context"):
        period = element.find(f"{{{_XBRLI}}}period")
        explicit, typed = [], 0
        for holder in (f"{{{_XBRLI}}}entity/{{{_XBRLI}}}segment", f"{{{_XBRLI}}}scenario"):
            container = element.find(holder)
            if container is None:
                continue
            for member in container:
                if member.tag == f"{{{_XBRLDI}}}explicitMember":
                    explicit.append((names.of_qname(member.get("dimension", "")), names.of_qname(member.text or "")))
                else:
                    typed += 1
        out[element.get("id", "")] = _Context(
            id=element.get("id", ""),
            instant=_day(period.findtext(f"{{{_XBRLI}}}instant")) if period is not None else None,
            start=_day(period.findtext(f"{{{_XBRLI}}}startDate")) if period is not None else None,
            end=_day(period.findtext(f"{{{_XBRLI}}}endDate")) if period is not None else None,
            explicit=tuple(sorted(explicit)),
            typed=typed,
        )
    return out


def _units(root) -> dict[str, str | None]:
    """Unit id -> its single measure's local name (`xbrli:shares` ->
    `shares`); a divide or multi-measure unit -> `None`."""
    out: dict[str, str | None] = {}
    for element in root.iter(f"{{{_XBRLI}}}unit"):
        measures = [m.text for m in element.findall(f"{{{_XBRLI}}}measure")]
        out[element.get("id", "")] = measures[0].strip().split(":")[-1] if len(measures) == 1 and measures[0] else None
    return out


def _is_nil(element) -> bool:
    return element.get("{http://www.w3.org/2001/XMLSchema-instance}nil") in ("true", "1")


def parse_share_class_filing(instance_xml: str) -> ShareClassFiling:
    """Parse one XBRL instance and link its class share facts. Pure: the
    same instance always gives the same result."""
    try:
        root = ElementTree.fromstring(instance_xml)
        names = _Names(_prefixes(instance_xml))
    except ElementTree.ParseError as exc:
        raise MalformedProviderResponse(f"XBRL instance did not parse: {exc}") from exc
    contexts = _contexts(root, names)
    units = _units(root)

    facts: list[tuple[str, _Context, str | None, str]] = []  # (concept, context, unit, text)
    for element in root:
        ref = element.get("contextRef")
        if ref is None or _is_nil(element) or ref not in contexts:
            continue
        facts.append((names.of_tag(element.tag), contexts[ref], units.get(element.get("unitRef", "")), (element.text or "").strip()))

    def entity_wide(concept: str) -> str | None:
        values = {text for c, ctx, _, text in facts if c == concept and not ctx.explicit and not ctx.typed and text}
        return values.pop() if len(values) == 1 else None

    document_period_end = _day(entity_wide("dei:DocumentPeriodEndDate"))
    annual_durations = [
        ctx for ctx in contexts.values()
        if not ctx.explicit and not ctx.typed and ctx.start and ctx.end
        and _ANNUAL_DAYS[0] <= (ctx.end - ctx.start).days <= _ANNUAL_DAYS[1]
    ]
    annual_period_ends = tuple(sorted(
        {ctx.end for ctx in annual_durations} | {ctx.start - timedelta(days=1) for ctx in annual_durations}
    ))

    cover_rows = _cover_rows(facts)
    return ShareClassFiling(
        entity_cik=(entity_wide("dei:EntityCentralIndexKey") or None),
        document_type=entity_wide("dei:DocumentType"),
        amendment=(entity_wide("dei:AmendmentFlag") or "").lower() == "true",
        document_period_end=document_period_end,
        fiscal_year_focus=entity_wide("dei:DocumentFiscalYearFocus"),
        fiscal_period_focus=entity_wide("dei:DocumentFiscalPeriodFocus"),
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
    for concept, ctx, _, text in facts:
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
    for concept, ctx, unit, text in facts:
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


# -- fetching -------------------------------------------------------------------------------------------


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
