"""SEC Filing Content Intelligence: Filing Content Model + Section
Taxonomy + deterministic Content Extraction + Filing Navigation
(Capability Expansion Sprint 13, Phases 2 through 7).

**Phase 1 audit finding**: Atlas already discovers a filing's own
*existence and metadata* (`regulatory_filings.RegulatoryFiling` --
form type, accession number, filing date, and, load-bearing for this
sprint, a real, already-constructed `filing_url` pointing at the
filing's own primary document on SEC's public archive). No provider
anywhere fetches or reads that document's own content -- this sprint's
entire job is the one, clean gap between "a filing exists" and "here is
its structure."

**Fetching is injectable, and `TextFetcher`'s own `(url, headers) -> str`
shape is duplicated here, not imported** from the real
`atlas.business_data_providers.http.TextFetcher` this sprint also adds
(mirroring `JsonFetcher`/`fetch_json` exactly). A real, enforced
architecture boundary (`tests/test_architecture_boundaries.py::
test_only_business_data_refresh_imports_business_data_providers`) says
`atlas.business_data_providers` may only ever be imported from
`atlas.alpha.business_data_refresh` -- discovered by running that test
suite before this module's first commit, not assumed. This module
therefore never imports the provider package at all: every test injects
its own fake fetcher (the identical shape, a plain `Callable`), and live
verification calls the real `atlas.business_data_providers.http.
fetch_text` from *outside* this package and passes it in, the same
"caller supplies the real thing, this module only describes its shape"
discipline every other injectable fetcher in this codebase already
follows.

**HTML parsing uses only the Python standard library**
(`html.parser.HTMLParser`) -- no new third-party dependency. It performs
one, deterministic job: split the document into ordered text blocks at
block-level tag boundaries, record `<table>` locations (with row/column
*counts* only -- never cell content, which is exactly the "must not
redesign Financial Statement Intelligence" boundary this sprint is
told to respect), and record `<a href>` targets. It never interprets,
never summarizes, and never reorders anything the document did not
itself present in that order.

**Section detection (Phase 3/4) is real SEC-mandated structure, not an
invented taxonomy**: 10-K, 10-Q, and 8-K filings are legally required
(Regulation S-K / S-T) to organize their own content under numbered
"Item N" headings -- a federally mandated convention, not a heuristic
Atlas invented. This module detects a short text block beginning with
`Item <number>` (case-insensitive) and maps that *real, disclosed* item
number to this sprint's own closed `FilingSectionKind` vocabulary, via
a table keyed by `form_type` (10-K's own Item 1A means "Risk Factors";
10-Q's own Item 1A, in a different Part of that filing, means "Risk
Updates" -- the two numbering schemes are genuinely different and are
never conflated). A block is only treated as a heading, never a
mid-paragraph cross-reference (e.g. "as discussed in Item 1A"), when it
is short (Phase 4's own "do not interpret" -- a disclosed length bound,
not a semantic judgment).

**DEF 14A intentionally receives no section detection in this build.**
Unlike 10-K/10-Q/8-K, a proxy statement carries no SEC-mandated
numbering convention -- its own headings are free text chosen by each
company. Inventing a heading-matching heuristic here would be exactly
the "never invent taxonomy entries" this sprint's own Phase 3 forbids;
a DEF 14A's `extraction_status` is always `STRUCTURE_UNKNOWN`, honestly,
even though its raw paragraph text is still preserved.

**Phase 9 audit**: this module reads only `RegulatoryFiling` (Sprint
1's own Foundation Provider, already covered by `KnowledgeDomain.
REGULATORY_FILINGS`) and fetches content on demand -- it is never
eagerly computed as part of `InvestmentCaseComposition` (fetching and
parsing a real filing is a genuinely expensive, live network operation,
unlike every prior Management/Financial Intelligence sprint's pure,
cheap, in-memory aggregation). No new `KnowledgeDomain` is registered,
and -- per this sprint's own Phase 9 instruction ("Future capabilities
may consume it. This sprint should not.") -- this module is not wired
into `models.py`/`service.py`/the API schema at all. It is delivered as
a complete, tested, standalone capability for a future sprint to adopt.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from html.parser import HTMLParser
from typing import Callable

from atlas.alpha.investment_case.regulatory_filings import RegulatoryFiling

__all__ = [
    "TextFetcher",
    "FilingSectionKind",
    "ExtractionStatus",
    "FilingParagraph",
    "FilingTable",
    "FilingReference",
    "FilingSection",
    "FilingContent",
    "extract_filing_content",
    "find_section",
]

#: `(url, headers) -> raw response text`. Duplicated from `atlas.
#: business_data_providers.http.TextFetcher`'s own identical shape --
#: see this module's own docstring for why it is never imported.
TextFetcher = Callable[[str, "dict[str, str] | None"], str]

_MAX_HEADING_LENGTH = 200
"""A text block longer than this is a paragraph that happens to
mention an Item number mid-sentence (e.g. "as discussed in Item 1A of
this report"), never a real heading -- a disclosed length bound, not a
semantic judgment (Phase 4's own "do not interpret")."""


class FilingSectionKind(str, Enum):
    """The complete, closed union of every section name Phase 3's own
    per-filing-type lists name -- deduplicated where the identical name
    appears under more than one filing type (e.g. `GOVERNANCE` is real
    for both 10-K and DEF 14A). `UNKNOWN` is the only member ever
    reached for content this module could not confidently attribute to
    a named section -- never invented, never guessed."""

    # -- 10-K --
    BUSINESS = "business"
    RISK_FACTORS = "risk_factors"
    PROPERTIES = "properties"
    LEGAL_PROCEEDINGS = "legal_proceedings"
    MDA = "mda"
    FINANCIAL_STATEMENTS = "financial_statements"
    NOTES = "notes"
    CONTROLS = "controls"
    EXECUTIVE_COMPENSATION = "executive_compensation"
    GOVERNANCE = "governance"
    EXHIBITS = "exhibits"
    # -- 10-Q (beyond members already listed above) --
    RISK_UPDATES = "risk_updates"
    # -- 8-K --
    ENTRY_INTO_AGREEMENT = "entry_into_agreement"
    EXECUTIVE_CHANGE = "executive_change"
    ACQUISITION = "acquisition"
    FINANCIAL_RESULTS = "financial_results"
    BANKRUPTCY = "bankruptcy"
    OTHER_EVENTS = "other_events"
    # -- DEF 14A (beyond members already listed above) --
    DIRECTOR_COMPENSATION = "director_compensation"
    OWNERSHIP = "ownership"
    AUDIT = "audit"
    SHAREHOLDER_MATTERS = "shareholder_matters"
    # -- shared --
    UNKNOWN = "unknown"


class ExtractionStatus(str, Enum):
    EXTRACTED = "extracted"
    """Raw content was fetched and parsed into blocks; section
    detection may still have found nothing (10-K/10-Q/8-K with no
    matching `Item` heading) -- `sections` and `STRUCTURE_UNKNOWN` are
    orthogonal to this status."""
    STRUCTURE_UNKNOWN = "structure_unknown"
    """Content was fetched and paragraphs/tables/references were
    extracted, but this module has no reliable, disclosed rule to
    attribute them to named sections (always true for `DEF 14A` in this
    build) -- `sections` is empty, `paragraphs` on the filing's own
    single implicit section is not."""
    FETCH_FAILED = "fetch_failed"
    NOT_ATTEMPTED = "not_attempted"


# -- Phase 2 + 7: Filing Content Model + Provenance --------------------------


@dataclass(frozen=True)
class FilingParagraph:
    order_index: int
    text: str
    """Verbatim, whitespace-normalized text -- never rewritten,
    summarized, or reordered."""


@dataclass(frozen=True)
class FilingTable:
    order_index: int
    row_count: int
    column_count: int
    """Structural counts only -- cell content is never extracted here
    (that is Financial Statement Intelligence's own, unmodified job)."""


@dataclass(frozen=True)
class FilingReference:
    order_index: int
    text: str
    target: str
    """The literal `href` attribute value -- may be an internal anchor
    (`#note5`), a relative document path, or an absolute URL; never
    resolved or interpreted."""


@dataclass(frozen=True)
class FilingSection:
    kind: FilingSectionKind
    heading_text: str
    """The verbatim heading text this section was detected from."""
    item_number: str | None
    """The real, disclosed SEC Item number this section was matched
    from (e.g. `"1A"`, `"5.02"`) -- `None` only when `kind` is
    `UNKNOWN`."""
    paragraphs: tuple[FilingParagraph, ...]
    tables: tuple[FilingTable, ...]
    references: tuple[FilingReference, ...]


@dataclass(frozen=True)
class FilingContent:
    form_type: str
    filed_at: datetime
    accession_number: str
    source_reference: str
    extraction_status: ExtractionStatus
    sections: tuple[FilingSection, ...]
    """Empty when `extraction_status` is `STRUCTURE_UNKNOWN`,
    `FETCH_FAILED`, or `NOT_ATTEMPTED`."""
    unattributed_paragraphs: tuple[FilingParagraph, ...]
    """Every extracted paragraph when section detection found nothing
    to attribute it to -- populated exactly when `sections == ()` but
    `extraction_status is EXTRACTED or STRUCTURE_UNKNOWN`. Content is
    never discarded merely because Atlas could not name its section."""
    unattributed_tables: tuple[FilingTable, ...]
    unattributed_references: tuple[FilingReference, ...]


# -- Phase 4: deterministic HTML -> block extraction (stdlib only) ----------

_BLOCK_TAGS = frozenset({"p", "div", "li", "br", "h1", "h2", "h3", "h4", "h5", "h6"})
_SKIP_CONTENT_TAGS = frozenset({"script", "style"})


@dataclass(frozen=True)
class _BlockEvent:
    text: str


@dataclass(frozen=True)
class _TableEvent:
    row_count: int
    column_count: int


@dataclass(frozen=True)
class _AnchorEvent:
    text: str
    target: str


_ParsedEvent = _BlockEvent | _TableEvent | _AnchorEvent


class _FilingHTMLParser(HTMLParser):
    """Extracts one, single, document-ordered stream of text blocks,
    table markers (row/column counts only), and anchor targets from raw
    filing HTML -- a single linear pass, no backtracking, no
    interpretation of what any block says. Kept as one ordered stream
    (rather than three separate lists) so a table or reference can be
    honestly attributed to whichever section it physically falls
    within, the same document position a human reader would see it in."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.events: list[_ParsedEvent] = []
        self._current: list[str] = []
        self._skip_depth = 0
        #: A stack, not a flat counter -- a table nested inside another
        #: table's own cell (a real, if uncommon, pattern in filing
        #: HTML) gets its own independent row/column count, on its own
        #: frame, rather than polluting the enclosing table's counts.
        self._table_stack: list[dict[str, object]] = []
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []

    def _flush_block(self) -> None:
        text = re.sub(r"\s+", " ", "".join(self._current)).strip()
        if text:
            self.events.append(_BlockEvent(text=text))
        self._current = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP_CONTENT_TAGS:
            self._skip_depth += 1
            return
        if tag == "table":
            self._flush_block()
            self._table_stack.append({"rows": 0, "row_cell_counts": [], "current_row_cells": 0})
        elif tag == "tr" and self._table_stack:
            self._table_stack[-1]["current_row_cells"] = 0
        elif tag in ("td", "th") and self._table_stack:
            self._table_stack[-1]["current_row_cells"] += 1
        elif tag == "a":
            href = next((value for name, value in attrs if name == "href" and value), None)
            if href:
                self._anchor_href = href
                self._anchor_text = []
        if tag in _BLOCK_TAGS:
            self._flush_block()

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_CONTENT_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if tag == "tr" and self._table_stack:
            frame = self._table_stack[-1]
            if frame["current_row_cells"] > 0:
                frame["rows"] += 1
                frame["row_cell_counts"].append(frame["current_row_cells"])
        elif tag == "table" and self._table_stack:
            frame = self._table_stack.pop()
            column_count = max(frame["row_cell_counts"], default=0)
            self.events.append(_TableEvent(row_count=frame["rows"], column_count=column_count))
        elif tag == "a" and self._anchor_href is not None:
            text = re.sub(r"\s+", " ", "".join(self._anchor_text)).strip()
            self.events.append(_AnchorEvent(text=text, target=self._anchor_href))
            self._anchor_href = None
            self._anchor_text = []
        if tag in _BLOCK_TAGS:
            self._flush_block()

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        if self._anchor_href is not None:
            self._anchor_text.append(data)
        if self._table_stack:
            return  # table cell text is never collected as paragraph prose -- structural counts only
        self._current.append(data)

    def finish(self) -> None:
        self._flush_block()


def _parse_html(html: str) -> tuple[_ParsedEvent, ...]:
    parser = _FilingHTMLParser()
    parser.feed(html)
    parser.finish()
    return tuple(parser.events)


# -- Phase 3: Filing Section Taxonomy (real SEC Item numbers only) ----------

#: Keyed by `(part, item_number)`. `part` is `None` for 10-K/8-K, whose
#: own Item numbers are never reused across Parts of the same filing
#: (10-K: Items 1-4 are Part I, 5-9 Part II, 10-14 Part III, 15 Part IV
#: -- no collisions). `10-Q` genuinely reuses Item numbers 1/1A/2/3/4
#: across two different Parts with two different meanings each (Part I
#: "Financial Information" vs. Part II "Other Information") -- a real
#: SEC-mandated structural fact confirmed against a real, live AAPL
#: 10-Q during this sprint's own verification, not assumed. Ignoring
#: `part` here would have silently mislabeled Part II's own "Item 2 --
#: Unregistered Sales of Equity Securities" as "MD&A" (Part I's Item 2)
#: -- exactly the kind of fabricated structure this sprint forbids.
_TEN_K_ITEM_MAP: dict[tuple[str | None, str], FilingSectionKind] = {
    (None, "1"): FilingSectionKind.BUSINESS,
    (None, "1A"): FilingSectionKind.RISK_FACTORS,
    (None, "2"): FilingSectionKind.PROPERTIES,
    (None, "3"): FilingSectionKind.LEGAL_PROCEEDINGS,
    (None, "7"): FilingSectionKind.MDA,
    (None, "8"): FilingSectionKind.FINANCIAL_STATEMENTS,
    (None, "9A"): FilingSectionKind.CONTROLS,
    (None, "10"): FilingSectionKind.GOVERNANCE,
    (None, "11"): FilingSectionKind.EXECUTIVE_COMPENSATION,
    (None, "15"): FilingSectionKind.EXHIBITS,
}
_TEN_Q_ITEM_MAP: dict[tuple[str | None, str], FilingSectionKind] = {
    ("I", "1"): FilingSectionKind.FINANCIAL_STATEMENTS,
    ("I", "2"): FilingSectionKind.MDA,
    ("I", "4"): FilingSectionKind.CONTROLS,
    ("II", "1A"): FilingSectionKind.RISK_UPDATES,
    #: Part II Items 1/2/3/5/6 ("Legal Proceedings," "Unregistered
    #: Sales," "Defaults," "Other Information," "Exhibits") have no
    #: member in Phase 3's own 10-Q taxonomy list -- left unmapped,
    #: resolving to `unattributed` content rather than force-fit into
    #: an existing, wrong category.
}
_EIGHT_K_ITEM_MAP: dict[tuple[str | None, str], FilingSectionKind] = {
    (None, "1.01"): FilingSectionKind.ENTRY_INTO_AGREEMENT,
    (None, "1.03"): FilingSectionKind.BANKRUPTCY,
    (None, "2.01"): FilingSectionKind.ACQUISITION,
    (None, "2.02"): FilingSectionKind.FINANCIAL_RESULTS,
    (None, "5.02"): FilingSectionKind.EXECUTIVE_CHANGE,
    (None, "8.01"): FilingSectionKind.OTHER_EVENTS,
}
_ITEM_MAPS_BY_FORM: dict[str, dict[tuple[str | None, str], FilingSectionKind]] = {
    "10-K": _TEN_K_ITEM_MAP, "10-Q": _TEN_Q_ITEM_MAP, "8-K": _EIGHT_K_ITEM_MAP,
}
#: Only `10-Q` uses Part-qualified keys -- 10-K/8-K item maps are keyed
#: `(None, item_number)` and never need Part tracking.
_PART_AWARE_FORMS = frozenset({"10-Q"})

_ITEM_HEADING_RE = re.compile(r"^item\s+(\d+[A-Za-z]?(?:\.\d+)?)\.?\s*(.*)$", re.IGNORECASE)
_PART_HEADING_RE = re.compile(r"^part\s+(i{1,3}|iv)\b", re.IGNORECASE)


def _match_part_heading(block: str) -> str | None:
    if len(block) > _MAX_HEADING_LENGTH:
        return None
    match = _PART_HEADING_RE.match(block.strip())
    return match.group(1).upper() if match else None


def _match_item_heading_shape(block: str) -> str | None:
    """`Item <number>` shape only, independent of whether that number
    means anything in this sprint's own taxonomy -- a real heading
    Atlas cannot name is still a real section *boundary*, and must
    close the previous section rather than silently absorbing
    unrelated trailing content into it."""
    if len(block) > _MAX_HEADING_LENGTH:
        return None
    match = _ITEM_HEADING_RE.match(block.strip())
    return match.group(1).upper() if match else None


def _resolve_item_kind(
    item_number: str, form_type: str, item_map: dict[tuple[str | None, str], FilingSectionKind], part: str | None,
) -> FilingSectionKind | None:
    lookup_part = part if form_type in _PART_AWARE_FORMS else None
    return item_map.get((lookup_part, item_number))


# -- Phase 4 + 6: assembling sections, and navigation ------------------------


@dataclass
class _MutableSection:
    item_number: str
    kind: FilingSectionKind
    paragraphs: list[str]
    tables: list[tuple[int, int]]
    references: list[tuple[str, str]]


def _assign_events_to_sections(
    events: tuple[_ParsedEvent, ...], form_type: str,
    item_map: dict[tuple[str | None, str], FilingSectionKind] | None,
) -> tuple[
    tuple[FilingSection, ...], tuple[FilingParagraph, ...], tuple[FilingTable, ...], tuple[FilingReference, ...],
]:
    """Walks the single ordered event stream once, attributing every
    paragraph/table/reference to whichever section's `Item` heading it
    most recently followed -- the same document position a human reader
    would encounter it in. Everything before the first recognized
    heading (or everything, if `item_map` is `None` or nothing ever
    matches) is `unattributed` -- never guessed into a section. Tracks
    the real, SEC-mandated "PART I"/"PART II" heading alongside `Item`
    headings for `_PART_AWARE_FORMS` (10-Q) -- see `_TEN_Q_ITEM_MAP`'s
    own comment for why this genuinely changes what an Item number
    means."""
    sections: list[_MutableSection] = []
    unattributed_paragraphs: list[str] = []
    unattributed_tables: list[tuple[int, int]] = []
    unattributed_references: list[tuple[str, str]] = []
    current_part: str | None = None
    current_section: _MutableSection | None = None

    for event in events:
        if isinstance(event, _BlockEvent):
            if form_type in _PART_AWARE_FORMS:
                part = _match_part_heading(event.text)
                if part is not None:
                    current_part = part
                    continue
            item_number = _match_item_heading_shape(event.text)
            if item_number is not None:
                kind = _resolve_item_kind(item_number, form_type, item_map, current_part) if item_map is not None else None
                if kind is not None:
                    current_section = _MutableSection(item_number=item_number, kind=kind, paragraphs=[], tables=[], references=[])
                    sections.append(current_section)
                else:
                    #: A real heading Atlas cannot name (e.g. Part II's
                    #: own Item 2) still ends the previous section --
                    #: never silently absorbed into it.
                    current_section = None
                continue
            (current_section.paragraphs if current_section is not None else unattributed_paragraphs).append(event.text)
        elif isinstance(event, _TableEvent):
            (current_section.tables if current_section is not None else unattributed_tables).append(
                (event.row_count, event.column_count)
            )
        elif isinstance(event, _AnchorEvent):
            (current_section.references if current_section is not None else unattributed_references).append(
                (event.text, event.target)
            )

    section_objects = tuple(
        FilingSection(
            kind=section.kind, heading_text=f"Item {section.item_number}", item_number=section.item_number,
            paragraphs=tuple(FilingParagraph(order_index=i, text=t) for i, t in enumerate(section.paragraphs)),
            tables=tuple(FilingTable(order_index=i, row_count=r, column_count=c) for i, (r, c) in enumerate(section.tables)),
            references=tuple(
                FilingReference(order_index=i, text=t, target=target) for i, (t, target) in enumerate(section.references)
            ),
        )
        for section in sections
    )
    return (
        section_objects,
        tuple(FilingParagraph(order_index=i, text=t) for i, t in enumerate(unattributed_paragraphs)),
        tuple(FilingTable(order_index=i, row_count=r, column_count=c) for i, (r, c) in enumerate(unattributed_tables)),
        tuple(
            FilingReference(order_index=i, text=t, target=target) for i, (t, target) in enumerate(unattributed_references)
        ),
    )


def extract_filing_content(
    filing: RegulatoryFiling, fetch_text_fn: TextFetcher, *, headers: dict[str, str] | None = None,
) -> FilingContent:
    """Fetches `filing.filing_url` via the injected `fetch_text_fn` and
    deterministically parses it -- no LLM call, no summarization, no
    fabricated content. Returns `extraction_status = FETCH_FAILED`
    (never raises) when the fetch itself fails, so a caller can still
    inspect the filing's own real metadata.

    `headers` is passed straight through to `fetch_text_fn` -- real,
    live verification against `www.sec.gov/Archives` (unlike
    `data.sec.gov`'s own JSON endpoints) returns `403` without a
    descriptive `User-Agent`, confirmed by a real request during this
    sprint's own live verification, not assumed. The caller supplies
    it; this module has no fixed identity of its own to send."""
    try:
        html = fetch_text_fn(filing.filing_url, headers)
    except Exception:
        return FilingContent(
            form_type=filing.form_type, filed_at=filing.filed_at, accession_number=filing.accession_number,
            source_reference=filing.filing_url, extraction_status=ExtractionStatus.FETCH_FAILED, sections=(),
            unattributed_paragraphs=(), unattributed_tables=(), unattributed_references=(),
        )

    events = _parse_html(html)
    item_map = _ITEM_MAPS_BY_FORM.get(filing.form_type)
    sections, unattributed_paragraphs, unattributed_tables, unattributed_references = _assign_events_to_sections(
        events, filing.form_type, item_map
    )
    extraction_status = ExtractionStatus.EXTRACTED if item_map is not None else ExtractionStatus.STRUCTURE_UNKNOWN

    return FilingContent(
        form_type=filing.form_type, filed_at=filing.filed_at, accession_number=filing.accession_number,
        source_reference=filing.filing_url, extraction_status=extraction_status, sections=sections,
        unattributed_paragraphs=unattributed_paragraphs, unattributed_tables=unattributed_tables,
        unattributed_references=unattributed_references,
    )


def find_section(content: FilingContent, kind: FilingSectionKind) -> FilingSection | None:
    """Phase 6's own "find Risk Factors -> return section" navigation --
    a pure lookup over already-extracted sections, first match wins
    (a real filing has at most one heading per Item number)."""
    return next((section for section in content.sections if section.kind is kind), None)
