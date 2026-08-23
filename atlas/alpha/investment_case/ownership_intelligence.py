"""Ownership Intelligence: transforms Filing Content Intelligence's own
structured filing objects into structured, traceable ownership
knowledge (Capability Expansion Sprint 19).

**Phase 1 audit finding.** Re-read fresh, not assumed: `FilingSectionKind.
OWNERSHIP` already exists in Filing Content Intelligence's own taxonomy
(Sprint 13, DEF 14A category list), but it is **never actually
populated**: DEF 14A gets no section detection at all in this build
(Sprint 13's own deliberate decision -- a proxy statement carries no
SEC-mandated heading convention the way `Item N` does), so
`find_section(content, OWNERSHIP)` always returns `None` for a real
DEF 14A. This module still checks it, for forward-compatibility and
honesty, but it is dead code today, documented as such rather than
silently assumed to work. 10-K's own real Item 12 ("Security Ownership
of Certain Beneficial Owners and Management") has no item-map entry
either -- a smaller practical gap than 10-Q's missing Item 1 was for
Legal Proceedings Intelligence, since most real 10-Ks incorporate Item
12 by reference to the proxy rather than reprint it, but the same real,
disclosed limitation in kind. This sprint's own Success Criteria lists
"Filing Content Intelligence remains unchanged" as a pass/fail
condition (as did Sprint 18's), so neither gap is closed here.

**This module's real, reachable evidence is therefore almost entirely
DEF 14A content read from `unattributed_paragraphs`/`unattributed_
tables`** -- the same fallback `governance_intelligence.py` already
established and proved out (Sprint 15/16), not the "never fall back"
discipline `risk_factor_intelligence.py`/`legal_proceedings_
intelligence.py` use, because those two modules' own *primary* sections
(Item 1A, Item 3) *are* reliably mapped and Ownership's is not. Scanning
DEF 14A's unattributed content broadly is bounded the same way
Governance Intelligence already bounds it: a disclosure is only ever
created when a real, disclosed signal is present (a labeled table
column, or an explicit ownership-disclosure phrase in prose) -- never
merely because a paragraph happens to appear in a proxy statement.

`KnowledgeDomain.OWNERSHIP` already existed in the base enum (unlike
`GOVERNANCE`/`LEGAL_PROCEEDINGS`, which needed new domains) -- this
sprint only wires its first real Coverage extractor.

**Phase 7's own table awareness, reusing Filing Content Intelligence's
already-proven model, never re-parsing anything**: a director/committee-
style "labeled column" table reader, the identical architecture
Governance Intelligence 2.0 (Sprint 16) already proved against real
DEF 14A data -- including the same real-world fix that sprint found:
many real filers style a header-looking row with bold `<td>` cells, not
real `<th>` tags, so this module also falls back to a table's own first
body row when it literally matches a recognized label. This is *not* a
duplication of Filing Content Intelligence's own HTML parsing -- it
reads only the already-structured `FilingTable`/`TableRow`/`TableCell`
objects that module already produced; the label-matching logic itself
is Ownership Intelligence's own classification concern, the same way
`legal_proceedings_intelligence.py`'s own category patterns are that
module's concern, not a copy of `risk_factor_intelligence.py`'s.

**"Investor X owns Y%" vs. "Investor X controls the company"**: this
module never estimates ownership that is not explicitly disclosed,
never infers beneficial ownership, and never infers control.
`disclosed_percentage`/`disclosed_share_count` are always verbatim
disclosed text, never a parsed number -- a malformed or unusual
disclosure could be silently misread as a different real value, the
same "preserve the disclosed text, not a derived number" discipline
`governance_intelligence.ShareClass.votes_per_share` already
established. `OwnerCategory.UNKNOWN` is preferred over guessing, per
this sprint's own explicit instruction; `OwnershipChangeKind.OWNER_NO_
LONGER_DISCLOSED` means only that a later comparable filing omits an
owner -- never that shares were sold, ownership reduced, ownership
eliminated, or control lost, which this module has no way to know."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.alpha.investment_case.filing_content_intelligence import (
    FilingContent,
    FilingParagraph,
    FilingSection,
    FilingSectionKind,
    FilingSubsection,
    FilingTable,
    TableRow,
    ExtractionStatus,
    find_section,
)

__all__ = [
    "OwnerCategory",
    "OwnershipDisclosureSource",
    "OwnershipChangeKind",
    "OwnershipDisclosure",
    "OwnerCategorySummary",
    "OwnershipChangeObservation",
    "OwnershipKnowledge",
    "extract_ownership_knowledge",
]


class OwnerCategory(str, Enum):
    """A closed, disclosed vocabulary of owner types -- the eight named
    in this sprint's own mission, plus `OTHER` and `UNKNOWN`. `UNKNOWN`
    is the sole fallback this module's own classification logic ever
    produces -- "Unknown is preferred over guessing" (this sprint's own
    explicit instruction). `OTHER` is real, closed vocabulary, defined
    for a future sprint with a reliable signal for a real-but-
    unlisted owner type -- this module never guesses an owner into
    `OTHER` either, the same "framework, not fabricated dataset"
    precedent `governance_intelligence.CommitteeKind.OTHER` already
    established."""

    DIRECTOR = "director"
    EXECUTIVE_OFFICER = "executive_officer"
    INSTITUTIONAL_INVESTOR = "institutional_investor"
    BENEFICIAL_OWNER = "beneficial_owner"
    INSIDER = "insider"
    EMPLOYEE_PLAN = "employee_plan"
    GOVERNMENT = "government"
    FOUNDATION = "foundation"
    OTHER = "other"
    UNKNOWN = "unknown"


class OwnershipDisclosureSource(str, Enum):
    """Where an `OwnershipDisclosure` was read from -- not a strength
    judgment in itself, but real, disclosed provenance a reader can
    weigh."""

    DEF_14A_CONTENT = "def_14a_content"
    """A DEF 14A's own `unattributed_paragraphs`/`unattributed_tables`
    -- this module's own primary, real, reachable source (see this
    module's own top docstring for why no finer-grained section is
    available)."""
    OWNERSHIP_SECTION = "ownership_section"
    """`FilingSectionKind.OWNERSHIP` -- real in Filing Content
    Intelligence's own taxonomy, but never actually populated for a
    real DEF 14A today; checked for forward-compatibility only."""
    GOVERNANCE_SECTION = "governance_section"
    """10-K Item 10 (`FilingSectionKind.GOVERNANCE`) -- reliably
    mapped, and occasionally carries incidental ownership mentions."""


class OwnershipChangeKind(str, Enum):
    """Phase 6's own closed, explicit change vocabulary -- derived by
    comparing one filing's own table-sourced, named ownership
    disclosure against the *immediately preceding* comparable filing
    this call was given (an immutable, pairwise history keyed by owner
    name, not a single cumulative snapshot)."""

    OWNER_NEWLY_DISCLOSED = "owner_newly_disclosed"
    """An owner present in this filing with no matching owner in the
    immediately preceding comparable filing -- never a claim the
    underlying ownership is new, which this module cannot know."""
    OWNER_CONTINUES = "owner_continues"
    """An owner present in both filings, with byte-identical disclosed
    evidence (percentage and share-count text) on both sides."""
    OWNER_WORDING_CHANGED = "owner_wording_changed"
    """An owner present in both filings, but the disclosed percentage/
    share-count text differs -- see `previous_excerpts`/`current_
    excerpts` for exactly what changed. This module never computes or
    characterizes the *size* of the change -- only that the disclosed
    text differs."""
    OWNER_NO_LONGER_DISCLOSED = "owner_no_longer_disclosed"
    """An owner present in the earlier filing's own comparable
    ownership disclosure, absent from the later one -- **only** when
    the later filing is itself expected to comprehensively restate its
    own ownership table (i.e. a DEF 14A; see `OWNER_DISCLOSURE_NOT_
    COMPARABLE`). Means only: the later filing's own text does not
    repeat this owner in the comparable disclosure scope. **It must
    never be read as: shares sold, ownership reduced, ownership
    eliminated, or control lost** -- this module has no way to know
    any of those (Phase 6's own explicit semantic rule)."""
    OWNER_DISCLOSURE_NOT_COMPARABLE = "owner_disclosure_not_comparable"
    """An owner present in the earlier filing's own comparable
    ownership disclosure, absent from the later one, where the later
    filing is not itself a DEF 14A. A 10-K/10-Q's own occasional,
    incidental ownership mention was never expected to comprehensively
    restate the full ownership table the way each year's own DEF 14A
    independently does -- its own silence is expected and
    uninformative, never evidence an owner's position ended."""


@dataclass(frozen=True)
class OwnershipDisclosure:
    """The bottom of Phase 2's own hierarchy -- one real, disclosed
    record, always traceable to the exact filing, section, subsection,
    and paragraph or table cell it came from."""

    owner_name: str | None
    """The literal disclosed name -- populated only from a table whose
    own header row labels a `"Name"`-style column (the filer's own
    declared structure, the same "reading a labeled column is
    preservation, not inference" discipline `governance_intelligence.
    Director.name` already established). `None` for a paragraph-
    sourced disclosure: extracting a person or entity name out of free
    prose would require exactly the kind of inference this module
    forbids."""
    categories: tuple[OwnerCategory, ...]
    """Never empty -- at least `(UNKNOWN,)`. May hold more than one
    real category when the text explicitly supports both (e.g. a
    director who is also an executive officer)."""
    disclosed_percentage: str | None
    """Verbatim disclosed text from a column literally headed
    `"Percent of Class"`/`"% Owned"`/similar -- never a parsed number.
    `None` when no such column exists or this owner's own cell is
    empty."""
    disclosed_share_count: str | None
    """Verbatim disclosed text from a column literally headed `"Shares
    Beneficially Owned"`/similar -- never a parsed number. `None` when
    no such column exists or this owner's own cell is empty."""
    text: str
    """The original disclosure this record was read from -- the full
    paragraph text for a paragraph-sourced disclosure, or the owner's
    own name-cell text for a table-sourced one (the percentage/share-
    count cells are already preserved as their own structured fields
    above, not duplicated here)."""
    source: OwnershipDisclosureSource
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    section_kind: FilingSectionKind | None
    section_item_number: str | None
    subsection_heading: str | None
    paragraph_order_index: int | None
    """Set for a paragraph-sourced disclosure; `None` for a table-
    sourced one (mutually exclusive with `table_order_index`)."""
    table_order_index: int | None = None
    row_index: int | None = None


@dataclass(frozen=True)
class OwnerCategorySummary:
    kind: OwnerCategory
    disclosures: tuple[OwnershipDisclosure, ...]
    """Never empty -- an `OwnerCategorySummary` only exists for a kind
    at least one real disclosure matched. A disclosure with more than
    one category appears in more than one summary's own `disclosures`
    -- an index, not a partition."""


@dataclass(frozen=True)
class OwnershipChangeObservation:
    kind: OwnershipChangeKind
    owner_name: str
    """Always a real, disclosed name -- this comparison is only ever
    performed for table-sourced, named owners (see this module's own
    top docstring for why a paragraph-sourced disclosure has no name
    to compare by)."""
    previous_excerpts: tuple[str, ...]
    """Every distinct verbatim percentage/share-count text disclosed
    for this owner in the earlier filing -- empty for `OWNER_NEWLY_
    DISCLOSED`, where there is no earlier side."""
    current_excerpts: tuple[str, ...]
    """The mirror of `previous_excerpts` for the later filing -- empty
    for `OWNER_NO_LONGER_DISCLOSED`/`OWNER_DISCLOSURE_NOT_COMPARABLE`,
    where there is no later side."""
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    """The *later* filing in the comparison -- the one whose own
    content this observation is reported against."""


@dataclass(frozen=True)
class OwnershipKnowledge:
    categories: tuple[OwnerCategorySummary, ...]
    """Every owner category with at least one real disclosure, across
    every filing supplied -- ordered by `OwnerCategory.value`."""
    changes: tuple[OwnershipChangeObservation, ...]
    """Phase 5/6's own immutable, pairwise disclosure history, keyed by
    owner name -- chronologically ordered, one full comparison per pair
    of consecutive filings (among those with any real table-sourced,
    named ownership evidence) this call was given."""
    disclosures: tuple[OwnershipDisclosure, ...]
    """Every disclosure this call detected, across every filing
    supplied, in filing-then-document order."""
    filings_considered: tuple[str, ...]
    """Accession numbers of every filing actually used, chronological
    -- `extraction_status in (EXTRACTED, STRUCTURE_UNKNOWN)` only; a
    `FETCH_FAILED`/`NOT_ATTEMPTED` filing contributes nothing, silently,
    the same way Filing Content Intelligence itself never raises on one."""


# -- Phase 4: deterministic classification -----------------------------------

#: Every alternative below allows a trailing plural `s?` where English
#: naturally takes one -- real disclosed text overwhelmingly uses the
#: plural in table captions and headings ("Security Ownership of
#: *Directors* and *Executive Officers*"), confirmed by hand-testing
#: against exactly that real, standard DEF 14A caption wording before
#: this module's own test suite was finalized, not assumed.
_DIRECTOR_RE = re.compile(r"\b(directors?|board members?)\b", re.IGNORECASE)
_EXECUTIVE_RE = re.compile(
    r"\b(chief executive officers?|chief financial officers?|chief operating officers?|executive officers?|presidents?)\b",
    re.IGNORECASE,
)
#: Live-verified against a real AAPL DEF 14A: its own two largest real
#: institutional holders are named "The Vanguard Group" and
#: "BlackRock, Inc." -- neither contains "Capital"/"Management"/"LLC"/
#: "LP," the entity-suffix words this pattern originally shipped with,
#: so both were missed on first live verification and honestly fell
#: through to `UNKNOWN`. Expanded with the real, common corporate-
#: entity suffixes actually found -- still a bounded, closed, literal-
#: word list, never an open-ended heuristic. Also fixed to be
#: case-insensitive, matching every other pattern in this module (a
#: real, if narrow, latent gap -- entity suffixes are almost always
#: disclosed title-cased in practice, so this rarely changed a result,
#: but was inconsistent and is corrected here regardless).
_INSTITUTIONAL_RE = re.compile(
    r"\b(LP|L\.P\.|LLC|L\.L\.C\.|Inc\.?|Incorporated|Corp\.?|Corporation|Capital|Management|Advisors?|"
    r"Asset Management|Partners|Fund|Group|Trust|N\.A\.)\b",
    re.IGNORECASE,
)
_BENEFICIAL_OWNER_RE = re.compile(r"\bbeneficial(ly)?\s+(own(s)?|ownership|owners?)\b", re.IGNORECASE)
_INSIDER_RE = re.compile(r"\binsiders?\b", re.IGNORECASE)
_EMPLOYEE_PLAN_RE = re.compile(r"\b(employee stock ownership plans?|ESOP|401\(k\)|employee benefit plans?)\b", re.IGNORECASE)
_GOVERNMENT_RE = re.compile(r"\b(governments?|sovereign wealth funds?|treasury)\b", re.IGNORECASE)
_FOUNDATION_RE = re.compile(r"\b(foundations?|charitable trusts?)\b", re.IGNORECASE)

#: Order reflects reading intent only -- every pattern is independently
#: tested against the full classification text regardless of order (an
#: owner may match more than one), the same "no early-exit, no forced
#: single choice" discipline `risk_factor_intelligence._CATEGORY_
#: PATTERNS`/`legal_proceedings_intelligence._CATEGORY_PATTERNS`
#: already apply.
_CATEGORY_PATTERNS: tuple[tuple[re.Pattern[str], OwnerCategory], ...] = (
    (_DIRECTOR_RE, OwnerCategory.DIRECTOR),
    (_EXECUTIVE_RE, OwnerCategory.EXECUTIVE_OFFICER),
    (_INSTITUTIONAL_RE, OwnerCategory.INSTITUTIONAL_INVESTOR),
    (_BENEFICIAL_OWNER_RE, OwnerCategory.BENEFICIAL_OWNER),
    (_INSIDER_RE, OwnerCategory.INSIDER),
    (_EMPLOYEE_PLAN_RE, OwnerCategory.EMPLOYEE_PLAN),
    (_GOVERNMENT_RE, OwnerCategory.GOVERNMENT),
    (_FOUNDATION_RE, OwnerCategory.FOUNDATION),
)

#: A real, disclosed signal that a paragraph is *about* ownership --
#: bounds this module's own broad DEF 14A prose scan to paragraphs that
#: actually say so, never merely because they appear in a proxy
#: statement.
_OWNERSHIP_MENTION_RE = re.compile(
    r"\b(beneficial(ly)?\s+(own(s)?|ownership|owners?)|principal shareholders?|percent(age)? of (our|the) outstanding "
    r"(common stock|shares|voting power))\b",
    re.IGNORECASE,
)


def _classify(text: str) -> tuple[OwnerCategory, ...]:
    matched = tuple(category for pattern, category in _CATEGORY_PATTERNS if pattern.search(text) is not None)
    return matched if matched else (OwnerCategory.UNKNOWN,)


# -- Phase 7: table awareness (reuses Filing Content Intelligence's own
# already-structured FilingTable/TableRow/TableCell -- never re-parses) -----

#: Live-verified against a real AAPL DEF 14A: the real column headers
#: read "Name of Beneficial Owner," "Shares of Common Stock
#: Beneficially Owned(1)," and "Percent of Common Stock Outstanding" --
#: none of which an exact-label match would recognize. A bounded,
#: word-boundary substring match against each header cell's own full
#: text (the same fix Governance Intelligence 2.0, Sprint 16, already
#: needed for real committee-column headers) is used instead: a real
#: word ("name," "shares," "percent") that every genuine column of that
#: kind always contains, regardless of surrounding phrasing or a
#: trailing footnote marker.
_NAME_HEADER_RE = re.compile(r"\bname\b", re.IGNORECASE)
_PERCENT_HEADER_RE = re.compile(r"\bpercent(age)?\b", re.IGNORECASE)
_SHARES_HEADER_RE = re.compile(r"\bshares?\b", re.IGNORECASE)
_TITLE_HEADER_RE = re.compile(r"\b(title|position|role)\b", re.IGNORECASE)

#: Live-verified against the real AAPL DEF 14A (accession
#: 0001308179-26-000008): its own "Outstanding Equity Awards at Fiscal
#: Year-End" table -- an unvested-equity-award disclosure, not a
#: beneficial-ownership one -- has a "Number of Shares or Units of
#: Stock That Have Not Vested" column, which `_SHARES_HEADER_RE` alone
#: also matches, and that table also carries a "Name" column (the
#: named executive). Since that table has no "Percent"-labeled column,
#: the `percent_index is None and shares_index is None` gate in
#: `_extract_owners_from_table` did not reject it on shares_index
#: alone, so a row's own *unvested equity award count* (e.g. Tim
#: Cook's "85,080") was read as `disclosed_share_count` -- exactly the
#: "equity award" vs. "ownership" conflation this module's own top
#: docstring says it must never make. No genuine beneficial-ownership
#: column is ever phrased in terms of vesting, so a header cell that
#: also mentions vesting is excluded from matching as the shares
#: column, the same targeted, word-boundary tightening
#: `executive_compensation_intelligence.py`'s own Summary Compensation
#: Table gate already used for `Salary` specifically.
_VESTING_HEADER_RE = re.compile(r"\bvest(ed|ing)?\b", re.IGNORECASE)

#: Live-verified against a real AAPL DEF 14A: a *separate* footnotes
#: table (columns: footnote number, footnote prose) was misidentified
#: as an ownership table, because its own footnote sentences
#: incidentally contain "shares"/"name" as ordinary words ("held in
#: the *name* of a family trust," "404 *shares* of Apple's common
#: stock") -- not a real column label at all. A genuine column header
#: cell is short (a few words); a footnote sentence is not. Mirrors
#: Filing Content Intelligence's own `_MAX_HEADING_LENGTH` discipline
#: (a short label vs. a paragraph that merely mentions the same word)
#: -- a disclosed length bound, not a semantic judgment, applied only
#: to this fallback path (a table with a real `<thead>`/`<th>` header
#: needs no such guard, since the HTML tag itself already establishes
#: it as a header regardless of length).
_MAX_FALLBACK_HEADER_CELL_LENGTH = 40


def _header_row(table: FilingTable) -> TableRow | None:
    if table.header is None or not table.header.rows:
        return None
    return table.header.rows[0]


def _looks_like_a_header_cell(text: str) -> bool:
    if len(text) > _MAX_FALLBACK_HEADER_CELL_LENGTH:
        return False
    return bool(_NAME_HEADER_RE.search(text) or _PERCENT_HEADER_RE.search(text) or _SHARES_HEADER_RE.search(text))


def _resolve_header_and_body(table: FilingTable) -> tuple[TableRow | None, tuple[TableRow, ...]]:
    """Identical fallback to `governance_intelligence._resolve_header_
    and_body` (Sprint 16), reimplemented here since it is this module's
    own classification concern, not a duplication of Filing Content
    Intelligence's own HTML parsing: many real filers style a header-
    looking row with bold `<td>` cells instead of real `<th>` tags
    (live-verified against the same real AAPL DEF 14A ownership table),
    so a table with no real `<thead>`/`<th>` header still gets
    recognized if its own first body row's cells match a real, short
    column signal this module recognizes."""
    header = _header_row(table)
    if header is not None:
        return header, table.rows
    if not table.rows:
        return None, ()
    candidate = table.rows[0]
    if any(_looks_like_a_header_cell(cell.text) for cell in candidate.cells):
        return candidate, table.rows[1:]
    return None, table.rows


def _header_column_index(header: TableRow, pattern: re.Pattern[str], exclude: re.Pattern[str] | None = None) -> int | None:
    for cell in header.cells:
        if exclude is not None and exclude.search(cell.text):
            continue
        if pattern.search(cell.text):
            return cell.order_index
    return None


def _cell_text(row: TableRow, column_index: int | None) -> str | None:
    if column_index is None or column_index >= len(row.cells):
        return None
    return row.cells[column_index].text.strip()


@dataclass(frozen=True)
class _TableOwner:
    name: str
    categories: tuple[OwnerCategory, ...]
    percent: str | None
    shares: str | None
    row_index: int


def _extract_owners_from_table(table: FilingTable) -> tuple[_TableOwner, ...]:
    """Returns `()` when the table has no header row (even after the
    bold-`<td>` fallback), no `"Name"`-labeled column, or -- live-
    verified against a real AAPL DEF 14A, where this exact confusion
    was found -- neither a percentage nor a share-count column either.
    A "Name"-only table (e.g. a board/committee roster, Governance
    Intelligence's own concern) is not an *ownership* disclosure at
    all; this module's own Phase 2 defines ownership evidence around
    the percentage/share-count fields specifically, so a table
    offering neither is honestly not read as one, never guessed into
    being one merely because it happens to have a "Name" column too.
    A table caption/heading (real, disclosed text) informs every row's
    own classification alongside that row's own name/title cells -- a
    table captioned "Security Ownership of Directors and Executive
    Officers" is itself real, disclosed evidence about what its own
    rows represent.

    The share-count column match itself excludes any header cell that
    also mentions vesting (`_VESTING_HEADER_RE`) -- live-verified
    against the same real AAPL DEF 14A: its own "Outstanding Equity
    Awards at Fiscal Year-End" table has a "Name" column and a "Number
    of Shares or Units of Stock That Have Not Vested" column (which
    `_SHARES_HEADER_RE` alone also matches) but no "Percent" column, so
    without this exclusion it was misread as an ownership table and a
    named executive's *unvested equity award count* was recorded as
    `disclosed_share_count` -- conflating an equity award with
    ownership, which this module's own top docstring says it must
    never do."""
    header, body_rows = _resolve_header_and_body(table)
    if header is None:
        return ()
    name_index = _header_column_index(header, _NAME_HEADER_RE)
    if name_index is None:
        return ()
    percent_index = _header_column_index(header, _PERCENT_HEADER_RE)
    shares_index = _header_column_index(header, _SHARES_HEADER_RE, exclude=_VESTING_HEADER_RE)
    if percent_index is None and shares_index is None:
        return ()
    title_index = _header_column_index(header, _TITLE_HEADER_RE)

    table_context = " ".join(filter(None, (table.caption, table.heading_context)))

    owners: list[_TableOwner] = []
    for row in body_rows:
        name = _cell_text(row, name_index)
        if not name:
            continue
        percent = _cell_text(row, percent_index) or None
        shares = _cell_text(row, shares_index) or None
        title = _cell_text(row, title_index) or ""
        classification_text = " ".join(filter(None, (name, title, table_context)))
        owners.append(_TableOwner(name=name, categories=_classify(classification_text), percent=percent, shares=shares, row_index=row.order_index))
    return tuple(owners)


# -- Extraction ---------------------------------------------------------------

_RELEVANT_SECTION_SOURCE: dict[FilingSectionKind, OwnershipDisclosureSource] = {
    FilingSectionKind.OWNERSHIP: OwnershipDisclosureSource.OWNERSHIP_SECTION,
    FilingSectionKind.GOVERNANCE: OwnershipDisclosureSource.GOVERNANCE_SECTION,
}
_USABLE_STATUSES = frozenset({ExtractionStatus.EXTRACTED, ExtractionStatus.STRUCTURE_UNKNOWN})


def _iter_relevant_paragraphs(
    content: FilingContent,
) -> "list[tuple[FilingParagraph, OwnershipDisclosureSource, FilingSection | None, FilingSubsection | None]]":
    result: list[tuple[FilingParagraph, OwnershipDisclosureSource, FilingSection | None, FilingSubsection | None]] = []
    for section_kind, source in _RELEVANT_SECTION_SOURCE.items():
        section = find_section(content, section_kind)
        if section is None:
            continue
        for paragraph in section.paragraphs:
            result.append((paragraph, source, section, None))
        for subsection in section.subsections:
            for paragraph in subsection.paragraphs:
                result.append((paragraph, source, section, subsection))
    if content.form_type == "DEF 14A":
        for paragraph in content.unattributed_paragraphs:
            result.append((paragraph, OwnershipDisclosureSource.DEF_14A_CONTENT, None, None))
    return result


def _iter_relevant_tables(
    content: FilingContent,
) -> "list[tuple[FilingTable, OwnershipDisclosureSource, FilingSection | None, FilingSubsection | None]]":
    result: list[tuple[FilingTable, OwnershipDisclosureSource, FilingSection | None, FilingSubsection | None]] = []
    for section_kind, source in _RELEVANT_SECTION_SOURCE.items():
        section = find_section(content, section_kind)
        if section is None:
            continue
        for table in section.tables:
            result.append((table, source, section, None))
        for subsection in section.subsections:
            for table in subsection.tables:
                result.append((table, source, section, subsection))
    if content.form_type == "DEF 14A":
        for table in content.unattributed_tables:
            result.append((table, OwnershipDisclosureSource.DEF_14A_CONTENT, None, None))
    return result


def _no_longer_disclosed_is_reliable(later_form_type: str) -> bool:
    """`True` only when the *later* filing is itself a DEF 14A -- the
    one filing type independently, comprehensively required (SEC Item
    403) to restate its own full ownership table every time. A 10-K/
    10-Q's own occasional, incidental ownership mention was never
    expected to do that, so its own silence is never reliable evidence
    either way."""
    return later_form_type == "DEF 14A"


def extract_ownership_knowledge(filing_contents: tuple[FilingContent, ...]) -> OwnershipKnowledge:
    """Built entirely upon Filing Content Intelligence's own output --
    never fetches, parses HTML, or reads a `RegulatoryFiling` directly.
    Filings are processed chronologically (`filed_at`, oldest first);
    `changes` compares each filing with real table-sourced, named
    ownership evidence against the *immediately preceding* such filing
    only -- an immutable, pairwise history (Phase 5), keyed by owner
    name."""
    usable = tuple(sorted((c for c in filing_contents if c.extraction_status in _USABLE_STATUSES), key=lambda c: c.filed_at))

    all_disclosures: list[OwnershipDisclosure] = []
    disclosures_by_category: dict[OwnerCategory, list[OwnershipDisclosure]] = {}
    #: (filing, {owner_name: frozenset(comparable texts)}) -- table-
    #: sourced, named owners only, one entry per usable filing that
    #: produced any such evidence at all.
    filing_summaries: list[tuple[FilingContent, dict[str, frozenset[str]]]] = []

    for content in usable:
        owner_texts: dict[str, set[str]] = {}

        for table, source, section, subsection in _iter_relevant_tables(content):
            for owner in _extract_owners_from_table(table):
                disclosure = OwnershipDisclosure(
                    owner_name=owner.name, categories=owner.categories, disclosed_percentage=owner.percent,
                    disclosed_share_count=owner.shares, text=owner.name, source=source,
                    accession_number=content.accession_number, form_type=content.form_type, filed_at=content.filed_at,
                    source_reference=content.source_reference, section_kind=section.kind if section else None,
                    section_item_number=section.item_number if section else None,
                    subsection_heading=subsection.heading_text if subsection is not None else None,
                    paragraph_order_index=None, table_order_index=table.order_index, row_index=owner.row_index,
                )
                all_disclosures.append(disclosure)
                for category in owner.categories:
                    disclosures_by_category.setdefault(category, []).append(disclosure)
                comparable = owner_texts.setdefault(owner.name, set())
                if owner.percent is not None:
                    comparable.add(owner.percent)
                if owner.shares is not None:
                    comparable.add(owner.shares)
                if owner.percent is None and owner.shares is None:
                    comparable.add(owner.name)

        for paragraph, source, section, subsection in _iter_relevant_paragraphs(content):
            text = paragraph.text
            if not _OWNERSHIP_MENTION_RE.search(text):
                continue
            disclosure = OwnershipDisclosure(
                owner_name=None, categories=_classify(text), disclosed_percentage=None, disclosed_share_count=None,
                text=text, source=source, accession_number=content.accession_number, form_type=content.form_type,
                filed_at=content.filed_at, source_reference=content.source_reference,
                section_kind=section.kind if section else None, section_item_number=section.item_number if section else None,
                subsection_heading=subsection.heading_text if subsection is not None else None,
                paragraph_order_index=paragraph.order_index,
            )
            all_disclosures.append(disclosure)
            for category in disclosure.categories:
                disclosures_by_category.setdefault(category, []).append(disclosure)

        if owner_texts:
            filing_summaries.append((content, {name: frozenset(texts) for name, texts in owner_texts.items()}))

    changes: list[OwnershipChangeObservation] = []
    for i in range(1, len(filing_summaries)):
        earlier_content, earlier_owners = filing_summaries[i - 1]
        later_content, later_owners = filing_summaries[i]
        no_longer_disclosed_reliable = _no_longer_disclosed_is_reliable(later_content.form_type)
        all_names = set(earlier_owners) | set(later_owners)

        for name in sorted(all_names):
            earlier_texts = earlier_owners.get(name)
            later_texts = later_owners.get(name)

            if earlier_texts is not None and later_texts is not None:
                kind = OwnershipChangeKind.OWNER_CONTINUES if earlier_texts == later_texts else OwnershipChangeKind.OWNER_WORDING_CHANGED
            elif later_texts is not None:
                kind = OwnershipChangeKind.OWNER_NEWLY_DISCLOSED
            elif no_longer_disclosed_reliable:
                kind = OwnershipChangeKind.OWNER_NO_LONGER_DISCLOSED
            else:
                kind = OwnershipChangeKind.OWNER_DISCLOSURE_NOT_COMPARABLE

            changes.append(
                OwnershipChangeObservation(
                    kind=kind, owner_name=name, previous_excerpts=tuple(sorted(earlier_texts or ())),
                    current_excerpts=tuple(sorted(later_texts or ())), accession_number=later_content.accession_number,
                    form_type=later_content.form_type, filed_at=later_content.filed_at,
                    source_reference=later_content.source_reference,
                )
            )

    categories = tuple(
        OwnerCategorySummary(kind=kind, disclosures=tuple(disclosures_by_category[kind]))
        for kind in sorted(disclosures_by_category, key=lambda k: k.value)
    )

    return OwnershipKnowledge(
        categories=categories, changes=tuple(changes), disclosures=tuple(all_disclosures),
        filings_considered=tuple(c.accession_number for c in usable),
    )
