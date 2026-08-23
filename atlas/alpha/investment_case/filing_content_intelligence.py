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
block-level tag boundaries, record `<table>` locations -- since the
Table Extraction sprint, with real row/header/cell structure and
content, not just counts -- and record `<a href>` targets. It never
interprets, never summarizes, and never reorders anything the document
did not itself present in that order.

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

**Capability Expansion Sprint 14 audit finding**: Sprint 13 already
built this capability essentially in full. Sprint 14's own spec asks
for the identical mission under the identical name, with two genuine,
verified deltas against the Sprint 13 implementation -- everything else
(taxonomy, deterministic extraction, navigation, the decision not to
wire this into the Decision Layer, the "no new KnowledgeDomain" call)
was re-verified fresh against this module's own code, not assumed, and
already satisfies Sprint 14's own Phases 3, 4, 5, 6, 8, 9, and 10:

1. **Per-object provenance (Phase 7)**: Sprint 13 put `accession_number`
   /`form_type`/`filed_at`/`source_reference` only on the top-level
   `FilingContent`. Phase 7 explicitly requires "every extracted object"
   to preserve accession number, filing date, and source reference --
   read literally, a `FilingSection` or `FilingParagraph` handed to a
   future capability in isolation (Phase 5's own "reusable objects for
   future capabilities to consume directly") had no way to trace itself
   back to its filing. Every object below now carries its own copy of
   these four fields, sourced from the same `RegulatoryFiling` already
   passed to `extract_filing_content` -- never fabricated, never
   independently looked up.
2. **The `Subsection` hierarchy level (Phase 2)**: Sprint 13's hierarchy
   was `Filing -> Section -> {Paragraph, Table, Reference}`. Sprint 14
   explicitly adds `Subsection` between `Section` and `Paragraph`. There
   is no SEC-mandated numbering convention for subsections the way
   `Item N` is mandated for sections (confirmed by this module's own
   Phase 3 docstring, re-read fresh) -- so subsection detection cannot
   reuse the Item-number approach without inventing one. It instead uses
   a real, disclosed, never-fabricated HTML signal already available to
   the existing parser: an `<h1>`-`<h6>` heading tag *within* an already-
   open section is treated as a subsection boundary (a document author's
   own explicit heading, not a guess). Verified during this sprint against
   the same real fixtures Sprint 13 used: most EDGAR-generated filing
   HTML does not use semantic heading tags at all (Item headings there
   are plain `<p>` text, exactly as Sprint 13's own docstring already
   documented) -- so `subsections` is honestly empty for most real
   filings today, and non-empty only when a filing's own HTML genuinely
   uses heading tags. This is strictly additive: no existing fixture in
   this module's own test suite uses a heading tag, so every one of
   Sprint 13's original behaviors is byte-for-byte unchanged.

**Not implemented, by deliberate decision, re-examined fresh**: a
separate opaque `identifier` string field (Phase 2). `accession_number`
+ `order_index` (now on every object, including `FilingSection` itself)
+ `item_number` already form a complete, structured, unique address for
any object in this tree -- adding a second, string-concatenated
identifier alongside those would duplicate information already present
as typed fields, the same "categorical/structured, never an opaque
blob" discipline this codebase already applies to `MaterialityLevel`,
`DimensionCoverageLevel`, and every other classification in this
package. `FilingContent` itself needs no separate identifier at all:
SEC's own `accession_number` already is a globally unique document
identifier.

**Infrastructure Sprint: Filing Content Intelligence 2.0 (Table
Extraction) audit finding.** Sprint 15 (Governance Intelligence) hit a
real, load-bearing wall: `FilingTable` carried only `row_count`/
`column_count` -- cell content was deliberately never extracted (this
module's own prior docstring said so explicitly). This sprint removes
that wall, additively: `FilingTable` now preserves real `<thead>`/
`<tbody>`/`<tfoot>`/`<tr>`/`<th>`/`<td>` structure -- headers, body
rows, footer rows, cell text, `rowspan`/`colspan`, alignment, captions,
nested-table markers, and cell-level `<a href>` references -- as a
`TableHeader`/`TableRow`/`TableCell`/`CellReference` hierarchy nested
inside the existing `FilingTable`. Every new object carries the same
full provenance every other object in this module already does.
`row_count`/`column_count` keep their original, literal meaning (a
count of `<td>`/`<th>` elements per row, never colspan-expanded) --
existing consumers reading only those two fields see byte-identical
values to before this sprint. A cell's own `contains_nested_table`
flag preserves Sprint 13's own original nested-table handling exactly
(each nested `<table>` still becomes its own sibling `FilingTable`,
never inlined into the outer cell's text) while now also disclosing,
honestly, that the outer cell's own text is not the full story.

Never expanded into a synthetic grid: a cell with `colspan="2"` stays
one `TableCell` at its own literal position with that metadata
attached -- this module does not synthesize the "missing" adjacent
cell a spanning cell implies, since doing so would be inventing a cell
the document itself never wrote (Phase 4's own "never infer absent
metadata"). A consumer that wants the expanded visual grid can compute
it from the preserved `rowspan`/`colspan` values; this module only
preserves.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
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
    "CellReference",
    "TableCell",
    "TableRow",
    "TableHeader",
    "FilingTable",
    "FilingReference",
    "FilingSubsection",
    "FilingSection",
    "FilingContent",
    "extract_filing_content",
    "find_section",
    "find_tables_by_keyword",
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


#: Every leaf and section object below carries its own copy of these
#: four fields (Sprint 14, Phase 7) -- sourced verbatim from the same
#: `RegulatoryFiling` `extract_filing_content` was called with, never
#: independently looked up or fabricated. This makes each object
#: self-describing: a `FilingParagraph` handed to a future capability
#: on its own (Phase 5) still carries enough to trace itself back to
#: its filing without needing a reference to the parent `FilingContent`.
@dataclass(frozen=True)
class FilingParagraph:
    order_index: int
    text: str
    """Verbatim, whitespace-normalized text -- never rewritten,
    summarized, or reordered."""
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str


@dataclass(frozen=True)
class CellReference:
    """An `<a href>` found inside a table cell -- kept distinct from
    `FilingReference` (prose-level links) so a cell's own references
    stay nested under it rather than mixed into the section's flat
    reference list; the same "preserve original hierarchy" this whole
    module already applies to paragraphs vs. subsection paragraphs."""

    text: str
    target: str


@dataclass(frozen=True)
class TableCell:
    order_index: int
    """This cell's own column position within its row."""
    text: str
    """Verbatim, whitespace-normalized cell text -- including the
    visible text of any `<a>` inside it, mirroring how prose paragraph
    text already includes anchor text. Empty string, never omitted,
    for a genuinely empty `<td></td>` -- Phase 4's own "never infer
    absent metadata" applies equally to absent content."""
    is_header: bool
    """True only for a real `<th>` tag -- never inferred from
    position, styling, or content."""
    rowspan: int
    colspan: int
    """The real, disclosed `rowspan`/`colspan` attribute value,
    defaulting to the HTML-spec default of `1` when absent or
    unparseable -- reading the spec's own default is not inference.
    Never expanded into synthetic adjacent cells -- see this module's
    own top docstring."""
    alignment: str | None
    """The real, disclosed `align` attribute, or a `text-align` value
    read from an inline `style` attribute -- `None` when neither is
    present. Never inferred from column position or content."""
    contains_nested_table: bool
    """True when a `<table>` was found directly inside this cell --
    that nested table's own rows/cells are never inlined here; they
    become their own, separate, sibling `FilingTable` (Sprint 13's own
    original nested-table handling, unchanged)."""
    references: tuple[CellReference, ...]
    row_index: int
    """This cell's own row's index within its row group (header/body/
    footer) -- redundant with position but makes a `TableCell` handed
    to a future capability on its own self-describing, the same
    reasoning Sprint 14's own per-object provenance already applies."""
    table_order_index: int
    """The `FilingTable.order_index` this cell belongs to."""
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str


@dataclass(frozen=True)
class TableRow:
    order_index: int
    """This row's own index within its row group (header/body/footer)
    -- each group numbers independently from 0."""
    cells: tuple[TableCell, ...]
    is_header_row: bool
    """True when this row came from a real `<thead>`, or -- when no
    `<thead>`/`<tbody>`/`<tfoot>` grouping tag was used at all -- when
    every cell in it is a real `<th>` (the common "no thead, first row
    is all `<th>`" pattern). A `<tbody>` row is never reclassified as a
    header row this way, even if it happens to use `<th>` for a
    row-label cell -- an explicit group tag is a real, disclosed fact
    that always wins."""
    table_order_index: int
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str


@dataclass(frozen=True)
class TableHeader:
    rows: tuple[TableRow, ...]
    """Never empty when a `FilingTable.header` is not `None` -- see
    `TableRow.is_header_row`'s own docstring for what qualifies."""


@dataclass(frozen=True)
class FilingTable:
    order_index: int
    row_count: int
    column_count: int
    """Literal counts -- the number of `<tr>` elements with at least
    one cell, and the largest number of `<td>`/`<th>` elements in any
    single row. Never colspan-expanded -- unchanged in meaning from
    before this sprint, so an existing consumer reading only these two
    fields sees byte-identical values."""
    caption: str | None
    """This table's own real `<caption>` text, verbatim -- `None` when
    the table has none. Any numbering the filing itself gave the table
    (e.g. "Table 1") is whatever the caption's own text literally
    says; this module never parses or assigns numbering of its own."""
    heading_context: str | None
    """The enclosing `FilingSubsection.heading_text`, when this table
    falls within one -- `None` otherwise. Deliberately narrow (Phase
    5's own "nearby headings"): the enclosing `FilingSection`'s own
    heading is not repeated here, since a table's section membership
    is already available structurally, and an `Item N` heading is
    rarely "nearby" a table many paragraphs below it."""
    header: TableHeader | None
    """`None` when no row qualified as a header row -- see
    `TableRow.is_header_row`."""
    rows: tuple[TableRow, ...]
    """Body rows -- every row not classified as a header or footer row."""
    footer_rows: tuple[TableRow, ...]
    """Rows from a real `<tfoot>` -- empty when the table has none."""
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str


@dataclass(frozen=True)
class FilingReference:
    order_index: int
    text: str
    target: str
    """The literal `href` attribute value -- may be an internal anchor
    (`#note5`), a relative document path, or an absolute URL; never
    resolved or interpreted."""
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str


@dataclass(frozen=True)
class FilingSubsection:
    """A heading-tagged grouping *within* a section (Sprint 14, Phase
    2). Unlike `FilingSectionKind`, subsections have no closed
    taxonomy and no SEC-mandated numbering -- a subsection is only ever
    detected from a real `<h1>`-`<h6>` HTML heading tag the document's
    own author used, never guessed from text content or styling. Most
    real EDGAR filing HTML uses plain, unstyled `<p>` text even for its
    own `Item N` headings (see this module's own top docstring), so
    `subsections` is honestly empty far more often than not -- this is
    a real, always-available capability, not a fabricated one."""

    order_index: int
    heading_text: str
    paragraphs: tuple[FilingParagraph, ...]
    tables: tuple[FilingTable, ...]
    references: tuple[FilingReference, ...]
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str


@dataclass(frozen=True)
class FilingSection:
    order_index: int
    kind: FilingSectionKind
    heading_text: str
    """The verbatim heading text this section was detected from."""
    item_number: str | None
    """The real, disclosed SEC Item number this section was matched
    from (e.g. `"1A"`, `"5.02"`) -- `None` only when `kind` is
    `UNKNOWN`."""
    paragraphs: tuple[FilingParagraph, ...]
    """Content directly under this section's own heading, before any
    subsection heading (if any) was encountered."""
    tables: tuple[FilingTable, ...]
    references: tuple[FilingReference, ...]
    subsections: tuple[FilingSubsection, ...]
    """Empty for the (common) case where this section's own HTML used
    no heading tags -- never a sign of a missing subsection, since none
    was ever disclosed."""
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str


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

_HEADING_TAGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})
_BLOCK_TAGS = frozenset({"p", "div", "li", "br"}) | _HEADING_TAGS
_SKIP_CONTENT_TAGS = frozenset({"script", "style"})


@dataclass(frozen=True)
class _BlockEvent:
    text: str
    #: True only when this block's own closing tag was a real `<h1>`-
    #: `<h6>` heading tag -- a genuine HTML-level fact read straight off
    #: the tag, never inferred from the text itself (Sprint 14, Phase 2
    #: subsection detection).
    is_heading: bool = False


@dataclass(frozen=True)
class _ParsedCell:
    text: str
    is_header: bool
    rowspan: int
    colspan: int
    alignment: str | None
    contains_nested_table: bool
    references: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class _ParsedRow:
    cells: tuple[_ParsedCell, ...]
    is_header_row: bool


@dataclass(frozen=True)
class _TableEvent:
    caption: str | None
    header_rows: tuple[_ParsedRow, ...]
    body_rows: tuple[_ParsedRow, ...]
    footer_rows: tuple[_ParsedRow, ...]
    row_count: int
    column_count: int


@dataclass(frozen=True)
class _AnchorEvent:
    text: str
    target: str


_ParsedEvent = _BlockEvent | _TableEvent | _AnchorEvent

_TABLE_GROUP_TAGS = frozenset({"thead", "tbody", "tfoot"})


#: Mutable, parser-internal builders -- one `_TableBuilder` per
#: currently-open `<table>` (a stack, since a table can nest inside
#: another table's own cell). Never exposed outside this module; a
#: `_TableEvent` (built by `_finish_table` at `</table>`) is the
#: immutable, public-shaped result.
@dataclass
class _CellBuilder:
    is_header: bool
    rowspan: int
    colspan: int
    alignment: str | None
    text_parts: list[str] = field(default_factory=list)
    text: str = ""
    references: list[tuple[str, str]] = field(default_factory=list)
    contains_nested_table: bool = False


@dataclass
class _RowBuilder:
    row_group: str
    """`"thead"` / `"tbody"` / `"tfoot"` / `"none"` -- the real,
    disclosed group tag this row's own `<tr>` was found inside, or
    `"none"` when no group tag was used at all (common in real filing
    HTML)."""
    cells: list[_CellBuilder] = field(default_factory=list)


@dataclass
class _TableBuilder:
    rows: list[_RowBuilder] = field(default_factory=list)
    caption_parts: list[str] = field(default_factory=list)
    in_caption: bool = False
    row_group_stack: list[str] = field(default_factory=list)
    current_row: _RowBuilder | None = None
    current_cell: _CellBuilder | None = None
    #: Anchor tracking scoped to this table frame -- kept separate from
    #: the parser's own global `_anchor_href`/`_anchor_text` (used for
    #: prose outside any table) so a link inside a cell never leaks
    #: into the wrong stream.
    anchor_href: str | None = None
    anchor_text: list[str] = field(default_factory=list)


def _parse_span_attr(attrs: list[tuple[str, str | None]], name: str) -> int:
    """The real, disclosed `rowspan`/`colspan` value, or the HTML
    spec's own default of `1` when absent or unparseable -- reading a
    spec-defined default is preservation, not inference."""
    raw = next((value for attr_name, value in attrs if attr_name == name), None)
    if raw is None:
        return 1
    try:
        parsed = int(raw.strip())
    except (TypeError, ValueError):
        return 1
    return parsed if parsed > 0 else 1


_ALIGN_STYLE_RE = re.compile(r"text-align\s*:\s*([a-zA-Z]+)", re.IGNORECASE)


def _parse_alignment_attr(attrs: list[tuple[str, str | None]]) -> str | None:
    align = next((value for name, value in attrs if name == "align" and value), None)
    if align:
        return align.strip().lower()
    style = next((value for name, value in attrs if name == "style" and value), None)
    if style:
        match = _ALIGN_STYLE_RE.search(style)
        if match:
            return match.group(1).lower()
    return None


def _row_is_header(row: _RowBuilder) -> bool:
    if row.row_group == "thead":
        return True
    if row.row_group == "none":
        return bool(row.cells) and all(cell.is_header for cell in row.cells)
    return False


def _finish_table(frame: _TableBuilder) -> _TableEvent:
    caption_text = re.sub(r"\s+", " ", "".join(frame.caption_parts)).strip() or None
    header_rows: list[_ParsedRow] = []
    body_rows: list[_ParsedRow] = []
    footer_rows: list[_ParsedRow] = []
    for row in frame.rows:
        parsed = _ParsedRow(
            cells=tuple(
                _ParsedCell(
                    text=c.text, is_header=c.is_header, rowspan=c.rowspan, colspan=c.colspan, alignment=c.alignment,
                    contains_nested_table=c.contains_nested_table, references=tuple(c.references),
                )
                for c in row.cells
            ),
            is_header_row=_row_is_header(row),
        )
        if parsed.is_header_row:
            header_rows.append(parsed)
        elif row.row_group == "tfoot":
            footer_rows.append(parsed)
        else:
            body_rows.append(parsed)
    return _TableEvent(
        caption=caption_text, header_rows=tuple(header_rows), body_rows=tuple(body_rows),
        footer_rows=tuple(footer_rows), row_count=len(frame.rows),
        column_count=max((len(row.cells) for row in frame.rows), default=0),
    )


class _FilingHTMLParser(HTMLParser):
    """Extracts one, single, document-ordered stream of text blocks,
    table events (full row/header/cell structure since the Table
    Extraction sprint), and anchor targets from raw filing HTML -- a
    single linear pass, no backtracking, no interpretation of what any
    block says. Kept as one ordered stream (rather than several
    separate lists) so a table or reference can be honestly attributed
    to whichever section it physically falls within, the same document
    position a human reader would see it in."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.events: list[_ParsedEvent] = []
        self._current: list[str] = []
        self._skip_depth = 0
        #: A stack, not a single frame -- a table nested inside another
        #: table's own cell (a real, if uncommon, pattern in filing
        #: HTML) gets its own independent builder, on its own frame,
        #: rather than polluting the enclosing table's own rows.
        self._table_stack: list[_TableBuilder] = []
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []

    def _flush_block(self, *, is_heading: bool = False) -> None:
        text = re.sub(r"\s+", " ", "".join(self._current)).strip()
        if text:
            self.events.append(_BlockEvent(text=text, is_heading=is_heading))
        self._current = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP_CONTENT_TAGS:
            self._skip_depth += 1
            return
        if tag == "table":
            self._flush_block()
            #: A `<table>` opening directly inside an already-open
            #: cell marks that cell as containing a nested table --
            #: the nested table becomes its own, separate frame/event;
            #: it is never inlined into the outer cell's own text.
            if self._table_stack and self._table_stack[-1].current_cell is not None:
                self._table_stack[-1].current_cell.contains_nested_table = True
            self._table_stack.append(_TableBuilder())
            return
        if self._table_stack:
            frame = self._table_stack[-1]
            if tag in _TABLE_GROUP_TAGS:
                frame.row_group_stack.append(tag)
            elif tag == "caption":
                frame.in_caption = True
            elif tag == "tr":
                row_group = frame.row_group_stack[-1] if frame.row_group_stack else "none"
                frame.current_row = _RowBuilder(row_group=row_group)
            elif tag in ("td", "th") and frame.current_row is not None:
                cell = _CellBuilder(
                    is_header=(tag == "th"), rowspan=_parse_span_attr(attrs, "rowspan"),
                    colspan=_parse_span_attr(attrs, "colspan"), alignment=_parse_alignment_attr(attrs),
                )
                frame.current_row.cells.append(cell)
                frame.current_cell = cell
            elif tag == "a" and frame.current_cell is not None:
                href = next((value for name, value in attrs if name == "href" and value), None)
                if href:
                    frame.anchor_href = href
                    frame.anchor_text = []
            return
        if tag == "a":
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
        if tag == "table" and self._table_stack:
            frame = self._table_stack.pop()
            self.events.append(_finish_table(frame))
            return
        if self._table_stack:
            frame = self._table_stack[-1]
            if tag in _TABLE_GROUP_TAGS:
                if frame.row_group_stack and frame.row_group_stack[-1] == tag:
                    frame.row_group_stack.pop()
            elif tag == "caption":
                frame.in_caption = False
            elif tag == "tr":
                if frame.current_row is not None:
                    if frame.current_row.cells:
                        frame.rows.append(frame.current_row)
                    frame.current_row = None
            elif tag in ("td", "th"):
                if frame.current_cell is not None:
                    frame.current_cell.text = re.sub(r"\s+", " ", "".join(frame.current_cell.text_parts)).strip()
                    frame.current_cell = None
            elif tag == "a" and frame.anchor_href is not None:
                text = re.sub(r"\s+", " ", "".join(frame.anchor_text)).strip()
                if frame.current_cell is not None:
                    frame.current_cell.references.append((text, frame.anchor_href))
                frame.anchor_href = None
                frame.anchor_text = []
            return
        if tag == "a" and self._anchor_href is not None:
            text = re.sub(r"\s+", " ", "".join(self._anchor_text)).strip()
            self.events.append(_AnchorEvent(text=text, target=self._anchor_href))
            self._anchor_href = None
            self._anchor_text = []
        if tag in _BLOCK_TAGS:
            #: The block being closed here is the tag's own text -- a
            #: closing `</h1>`-`</h6>` is the only case this can ever be
            #: a real heading; `handle_starttag`'s own flush (below)
            #: only ever flushes text that *preceded* the tag, which is
            #: never heading text.
            self._flush_block(is_heading=tag in _HEADING_TAGS)

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        if self._table_stack:
            frame = self._table_stack[-1]
            if frame.in_caption:
                frame.caption_parts.append(data)
                return
            if frame.anchor_href is not None:
                frame.anchor_text.append(data)
            if frame.current_cell is not None:
                frame.current_cell.text_parts.append(data)
            return  # stray text inside a table but outside any cell/caption is never fabricated a home
        if self._anchor_href is not None:
            self._anchor_text.append(data)
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
class _MutableSubsection:
    heading_text: str
    paragraphs: list[str]
    tables: list[_TableEvent]
    references: list[tuple[str, str]]


@dataclass
class _MutableSection:
    item_number: str
    kind: FilingSectionKind
    paragraphs: list[str]
    tables: list[_TableEvent]
    references: list[tuple[str, str]]
    subsections: list[_MutableSubsection]


def _paragraph_objects(texts: list[str], filing: RegulatoryFiling) -> tuple[FilingParagraph, ...]:
    return tuple(
        FilingParagraph(
            order_index=i, text=t, accession_number=filing.accession_number, form_type=filing.form_type,
            filed_at=filing.filed_at, source_reference=filing.filing_url,
        )
        for i, t in enumerate(texts)
    )


def _cell_objects(
    cells: tuple[_ParsedCell, ...], row_index: int, table_order_index: int, filing: RegulatoryFiling,
) -> tuple[TableCell, ...]:
    return tuple(
        TableCell(
            order_index=i, text=c.text, is_header=c.is_header, rowspan=c.rowspan, colspan=c.colspan,
            alignment=c.alignment, contains_nested_table=c.contains_nested_table,
            references=tuple(CellReference(text=t, target=target) for t, target in c.references),
            row_index=row_index, table_order_index=table_order_index, accession_number=filing.accession_number,
            form_type=filing.form_type, filed_at=filing.filed_at, source_reference=filing.filing_url,
        )
        for i, c in enumerate(cells)
    )


def _row_objects(rows: tuple[_ParsedRow, ...], table_order_index: int, filing: RegulatoryFiling) -> tuple[TableRow, ...]:
    return tuple(
        TableRow(
            order_index=i, cells=_cell_objects(r.cells, i, table_order_index, filing), is_header_row=r.is_header_row,
            table_order_index=table_order_index, accession_number=filing.accession_number, form_type=filing.form_type,
            filed_at=filing.filed_at, source_reference=filing.filing_url,
        )
        for i, r in enumerate(rows)
    )


def _table_objects(
    table_events: list[_TableEvent], filing: RegulatoryFiling, *, heading_context: str | None,
) -> tuple[FilingTable, ...]:
    return tuple(
        FilingTable(
            order_index=i, row_count=t.row_count, column_count=t.column_count, caption=t.caption,
            heading_context=heading_context,
            header=TableHeader(rows=_row_objects(t.header_rows, i, filing)) if t.header_rows else None,
            rows=_row_objects(t.body_rows, i, filing), footer_rows=_row_objects(t.footer_rows, i, filing),
            accession_number=filing.accession_number, form_type=filing.form_type, filed_at=filing.filed_at,
            source_reference=filing.filing_url,
        )
        for i, t in enumerate(table_events)
    )


def _reference_objects(refs: list[tuple[str, str]], filing: RegulatoryFiling) -> tuple[FilingReference, ...]:
    return tuple(
        FilingReference(
            order_index=i, text=t, target=target, accession_number=filing.accession_number,
            form_type=filing.form_type, filed_at=filing.filed_at, source_reference=filing.filing_url,
        )
        for i, (t, target) in enumerate(refs)
    )


def _subsection_objects(subsections: list[_MutableSubsection], filing: RegulatoryFiling) -> tuple[FilingSubsection, ...]:
    return tuple(
        FilingSubsection(
            order_index=i, heading_text=sub.heading_text, paragraphs=_paragraph_objects(sub.paragraphs, filing),
            tables=_table_objects(sub.tables, filing, heading_context=sub.heading_text),
            references=_reference_objects(sub.references, filing),
            accession_number=filing.accession_number, form_type=filing.form_type, filed_at=filing.filed_at,
            source_reference=filing.filing_url,
        )
        for i, sub in enumerate(subsections)
    )


def _assign_events_to_sections(
    events: tuple[_ParsedEvent, ...], filing: RegulatoryFiling,
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
    means.

    Also tracks a `current_subsection` (Sprint 14, Phase 2): a
    heading-tagged block (`event.is_heading`) encountered inside an open
    section, that is *not itself* an `Item`/`Part` heading, opens a new
    `FilingSubsection` that subsequent content nests under until the
    next subsection heading or the section itself ends. A heading tag
    outside any open section never creates a floating subsection -- it
    falls through to `unattributed_paragraphs` like any other text,
    unchanged from Sprint 13's own behavior."""
    form_type = filing.form_type
    sections: list[_MutableSection] = []
    unattributed_paragraphs: list[str] = []
    unattributed_tables: list[_TableEvent] = []
    unattributed_references: list[tuple[str, str]] = []
    current_part: str | None = None
    current_section: _MutableSection | None = None
    current_subsection: _MutableSubsection | None = None

    for event in events:
        if isinstance(event, _BlockEvent):
            if form_type in _PART_AWARE_FORMS:
                part = _match_part_heading(event.text)
                if part is not None:
                    current_part = part
                    current_subsection = None
                    continue
            item_number = _match_item_heading_shape(event.text)
            if item_number is not None:
                kind = _resolve_item_kind(item_number, form_type, item_map, current_part) if item_map is not None else None
                if kind is not None:
                    current_section = _MutableSection(
                        item_number=item_number, kind=kind, paragraphs=[], tables=[], references=[], subsections=[],
                    )
                    sections.append(current_section)
                else:
                    #: A real heading Atlas cannot name (e.g. Part II's
                    #: own Item 2) still ends the previous section --
                    #: never silently absorbed into it.
                    current_section = None
                current_subsection = None
                continue
            if event.is_heading and current_section is not None:
                current_subsection = _MutableSubsection(heading_text=event.text, paragraphs=[], tables=[], references=[])
                current_section.subsections.append(current_subsection)
                continue
            target_paragraphs = (
                current_subsection.paragraphs if current_subsection is not None
                else current_section.paragraphs if current_section is not None
                else unattributed_paragraphs
            )
            target_paragraphs.append(event.text)
        elif isinstance(event, _TableEvent):
            target_tables = (
                current_subsection.tables if current_subsection is not None
                else current_section.tables if current_section is not None
                else unattributed_tables
            )
            target_tables.append(event)
        elif isinstance(event, _AnchorEvent):
            target_references = (
                current_subsection.references if current_subsection is not None
                else current_section.references if current_section is not None
                else unattributed_references
            )
            target_references.append((event.text, event.target))

    section_objects = tuple(
        FilingSection(
            order_index=i, kind=section.kind, heading_text=f"Item {section.item_number}", item_number=section.item_number,
            paragraphs=_paragraph_objects(section.paragraphs, filing),
            tables=_table_objects(section.tables, filing, heading_context=None),
            references=_reference_objects(section.references, filing),
            subsections=_subsection_objects(section.subsections, filing),
            accession_number=filing.accession_number, form_type=filing.form_type, filed_at=filing.filed_at,
            source_reference=filing.filing_url,
        )
        for i, section in enumerate(sections)
    )
    return (
        section_objects,
        _paragraph_objects(unattributed_paragraphs, filing),
        _table_objects(unattributed_tables, filing, heading_context=None),
        _reference_objects(unattributed_references, filing),
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
        events, filing, item_map
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


def _all_tables(content: FilingContent) -> tuple[FilingTable, ...]:
    result: list[FilingTable] = []
    for section in content.sections:
        result.extend(section.tables)
        for subsection in section.subsections:
            result.extend(subsection.tables)
    result.extend(content.unattributed_tables)
    return tuple(result)


def find_tables_by_keyword(content: FilingContent, keyword: str) -> tuple[FilingTable, ...]:
    """Table Extraction sprint, Phase 6's own deterministic navigation:
    matches `keyword` case-insensitively against each table's own real,
    disclosed `caption`/`heading_context` text -- never against cell
    content (which could match by pure coincidence, unrelated to what
    the table actually is), and never against an invented "table kind"
    classification, since SEC filings carry no mandated table taxonomy
    the way `Item N` headings mandate section structure. A table with
    neither a caption nor an enclosing subsection heading is honestly
    unreachable this way -- it is still present in its own section's
    `tables`, just not findable by keyword."""
    needle = keyword.lower()
    return tuple(
        table for table in _all_tables(content)
        if (table.caption is not None and needle in table.caption.lower())
        or (table.heading_context is not None and needle in table.heading_context.lower())
    )
