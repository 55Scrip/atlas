"""Executive Compensation Intelligence: transforms Filing Content
Intelligence's own structured filing objects into structured,
traceable executive-compensation knowledge (Capability Expansion
Sprint 20).

**Phase 1 audit finding.** Re-read fresh, not assumed. Sprint 12's
`incentive_intelligence.py` already discovers *that* a DEF 14A exists
(`CompensationDisclosureFiling`, a pure re-labeling of `RegulatoryFiling`)
but explicitly never reads its content -- every one of its own Phase
2-7 knowledge objects (`EquityIncentive`, `CashIncentive`,
`PerformanceIncentive`, `ExecutiveIncentiveProgram`, `IncentiveTimelineEvent`,
`IncentiveStructure`) is a real, correctly-typed, closed-vocabulary
dataclass that is *never instantiated* in that build, by its own
explicit, disclosed design ("no path in this codebase from 'a proxy
statement exists' to 'here is what it says'"). That path now exists:
Filing Content Intelligence (Sprints 13-14), Table Extraction
(infrastructure sprint), and three table-aware domain consumers
(Governance/Ownership Intelligence, Sprints 15-19) have already proven
the pattern this module reuses -- Ownership Intelligence's own
column-header resolution (bold-`<td>`-not-`<th>` fallback, bounded
substring column matching, a length guard against footnote-table false
positives) is the *identical* real-world DEF 14A styling this module's
own live verification confirmed applies equally to the Summary
Compensation Table.

`executive_change_intelligence.py` already has a real `ExecutiveIdentity`
model (Phase 2/3 of that sprint) -- but it is built entirely from
*earnings-call* evidence (`source_transcripts`/`statement_count`), a
genuinely different evidence source than a DEF 14A's own compensation
table. Phase 4's own "link compensation records to Executive Identity"
is honored here as an **optional, read-only correlation**: a caller may
pass that module's own already-computed `tuple[ExecutiveIdentity, ...]`
in, and a compensation record links to one only on an exact (case-
insensitive) name match with a role-category-compatible title --
`executive_change_intelligence.py` itself is never imported for
anything beyond its own already-public types, never modified, and this
module never computes `ExecutiveIdentity` records itself (that would be
duplicating that module's own earnings-call-parsing job).

No existing `KnowledgeDomain` cleanly covers this: `MANAGEMENT`'s own
real sources are exclusively earnings-call-derived
(`management_credibility_intelligence.py`/`executive_change_
intelligence.py`); wiring a DEF-14A-only presence check under that
broader label would misrepresent what `MANAGEMENT` coverage actually
means. `KnowledgeDomain.EXECUTIVE_COMPENSATION` is a new, minimum
necessary registry addition (`knowledge_coverage/models.py`), the same
category of change Sprint 15/18 made for `GOVERNANCE`/`LEGAL_
PROCEEDINGS` -- not a redesign.

**"The filing discloses $X in stock awards" vs. "this executive is well
aligned"**: this module assigns no score, no rank, no alignment
judgment. Every dollar figure is preserved as verbatim disclosed text
(`str | None`, never a fabricated or estimated number) -- with one
narrow, disclosed exception: Phase 8's own explicit ask for "salary
increased/decreased"-style historical observations requires *comparing*
two real, already-disclosed numbers. A value is parsed into a
comparable number **only** when its own text is unambiguously plain (an
optional `$`, digit groups, commas, an optional decimal -- no footnote
marker, no range, nothing else); anything else honestly yields no
comparison rather than a guessed one. This is reading an already-
disclosed number in its own native numeric form, not estimating a
missing one -- a different act from the "never estimate" the rest of
this module holds to everywhere else.

**Phase 9's own integration is one-directional and additive, by
construction**: `incentive_intelligence.py` is not touched at all --
confirmed by this sprint's own diff. This module instead exports
`build_incentive_knowledge`, a pure function that *consumes*
`ExecutiveCompensationKnowledge` and constructs real instances of
`incentive_intelligence`'s own existing dataclasses
(`EquityIncentive`/`CashIncentive`/`PerformanceIncentive`/
`ExecutiveIncentiveProgram`/`IncentiveStructure`), reusing their exact,
unmodified shapes and closed vocabularies. `incentive_intelligence.
extract_incentive_intelligence()` itself remains completely unchanged --
callers that only pass `regulatory_filings` see byte-identical
behavior; a caller with real `ExecutiveCompensationKnowledge` available
may additionally call `build_incentive_knowledge` to get a genuinely
populated `IncentiveKnowledge`. "Filing Content -> Executive
Compensation Intelligence -> Incentive Intelligence," never the
reverse.

**Phase 10's ownership boundary**: this module never imports
`ownership_intelligence.py` and has no field resembling beneficial
ownership, voting power, or granted-vs-vested share counts. An equity
award's own disclosed grant value/unit count is compensation evidence
(what the company says it paid); it is never conflated with, derived
from, or cross-referenced against ownership evidence (what the company
says someone owns) -- two disclosures about the same person answering
two different questions."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.alpha.investment_case.executive_change_intelligence import ExecutiveIdentity
from atlas.alpha.investment_case.filing_content_intelligence import (
    FilingContent,
    FilingParagraph,
    FilingSection,
    FilingSectionKind,
    FilingSubsection,
    FilingTable,
    TableRow,
    ExtractionStatus,
)
from atlas.alpha.investment_case.incentive_intelligence import (
    CashIncentive,
    CashIncentiveKind,
    EquityIncentive,
    EquityIncentiveKind,
    ExecutiveIncentiveProgram,
    IncentiveEvidenceStatus,
    IncentiveStructure,
    IncentiveStructureComponent,
    PerformanceIncentive,
    PerformanceMetricKind,
)

__all__ = [
    "CompensationComponentKind",
    "CompensationDisclosureSource",
    "CompensationChangeKind",
    "ExecutiveCompensationRecord",
    "EquityAwardDisclosure",
    "PerformanceMetricDisclosure",
    "CompensationChangeObservation",
    "ExecutiveCompensationKnowledge",
    "extract_executive_compensation_knowledge",
    "build_incentive_knowledge",
    "build_incentive_structures",
]


class CompensationComponentKind(str, Enum):
    """A closed vocabulary matching Phase 2's own named Summary
    Compensation Table components exactly -- one member per real,
    SEC-mandated column."""

    SALARY = "salary"
    BONUS = "bonus"
    STOCK_AWARDS = "stock_awards"
    OPTION_AWARDS = "option_awards"
    NON_EQUITY_INCENTIVE = "non_equity_incentive"
    PENSION_CHANGE = "pension_change"
    OTHER_COMPENSATION = "other_compensation"
    TOTAL = "total"


class CompensationDisclosureSource(str, Enum):
    SUMMARY_COMPENSATION_TABLE = "summary_compensation_table"
    EQUITY_AWARD_TABLE = "equity_award_table"
    """A DEF 14A equity-award disclosure table beyond the Summary
    Compensation Table's own aggregate dollar columns -- e.g. "Grants
    of Plan-Based Awards" (new-grant detail) or "Outstanding Equity
    Awards at Fiscal Year-End" (cumulative unvested holdings). Live
    verification against a real DEF 14A (AAPL) found no reliable way to
    tell these apart from column headers alone (neither table carried a
    caption in that filing) -- this source label deliberately does not
    claim which specific named table it was, only that it is a real
    equity-award table, not the Summary Compensation Table."""
    DEF_14A_CONTENT = "def_14a_content"
    """DEF 14A's own `unattributed_paragraphs` -- used only for
    explicitly disclosed performance-metric mentions (Phase 6); mirrors
    `ownership_intelligence.py`'s own DEF 14A fallback."""


class CompensationChangeKind(str, Enum):
    """Phase 8's own closed, explicit change vocabulary -- historical
    observations only, never judgments. Derived by comparing one
    executive's own compensation record against the *immediately
    preceding comparable* record for the same (name, role) pair --
    across consecutive reporting years within one filing's own multi-
    year table, or across filings, whichever is chronologically
    adjacent."""

    SALARY_INCREASED = "salary_increased"
    SALARY_DECREASED = "salary_decreased"
    STOCK_AWARD_VALUE_INCREASED = "stock_award_value_increased"
    STOCK_AWARD_VALUE_DECREASED = "stock_award_value_decreased"
    BONUS_INTRODUCED = "bonus_introduced"
    """A bonus was disclosed for this executive in this year where none
    was disclosed the prior comparable year -- never a claim about
    *why*, and never the mirror "bonus removed" (an absent bonus
    column value the following year is not reliable evidence the
    company stopped paying bonuses -- silence is not a disclosed fact,
    the same principle every sibling module in this session already
    applies)."""
    OPTION_AWARDS_INTRODUCED = "option_awards_introduced"
    COMPENSATION_MIX_CHANGED = "compensation_mix_changed"
    """The *set* of non-empty compensation components disclosed for
    this executive differs between the two years -- a mechanical set
    comparison, never a judgment about which mix is better."""
    PERFORMANCE_MEASURE_CHANGED = "performance_measure_changed"
    """The *set* of disclosed performance-metric kinds (Phase 6)
    differs between the two years -- mechanical, mirrors `risk_factor_
    intelligence.py`'s own category-set comparison."""
    COMPENSATION_NOT_COMPARABLE = "compensation_not_comparable"
    """Either year's own disclosed value could not be read as a plain
    number (a footnote marker, a range, or any other non-numeric
    content) -- never a guessed direction from an ambiguous figure."""


@dataclass(frozen=True)
class ExecutiveCompensationRecord:
    """The bottom of Phase 2's own hierarchy -- one real, disclosed
    Summary Compensation Table row, always traceable to the exact
    filing, table, and row it came from. Every component field is
    verbatim disclosed text, never a parsed or estimated number --
    "never calculate a missing component from the total" (Phase 2's
    own explicit rule) is honored structurally: nothing here is ever
    computed from any other field."""

    executive_name: str
    disclosed_role: str | None
    """Verbatim text from the same "Name and Principal Position" cell
    as the name itself, when the filer discloses both together -- never
    looked up or inferred from any other source."""
    reporting_year: str | None
    """Verbatim disclosed year text (e.g. `"2023"`) -- read as a plain
    integer only for chronological ordering, never treated as a
    computed or estimated fact."""
    salary: str | None
    bonus: str | None
    stock_awards: str | None
    option_awards: str | None
    non_equity_incentive: str | None
    pension_change: str | None
    other_compensation: str | None
    total: str | None
    currency: str | None
    """Populated only when the table's own caption/heading explicitly
    names a currency (e.g. a foreign private issuer's own "(in EUR)")
    -- `None`, never assumed to be USD, when no such text exists."""
    source: CompensationDisclosureSource
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    section_kind: FilingSectionKind | None
    section_item_number: str | None
    subsection_heading: str | None
    table_order_index: int
    row_index: int
    linked_executive_identity_name: str | None = None
    """Set only when a caller-supplied `ExecutiveIdentity` (Phase 4)
    matched this record's own `executive_name` on an exact, case-
    insensitive name comparison with a role-category-compatible title
    -- never a fuzzy or similarity match. Carries only the matched
    identity's own name (not the full `ExecutiveIdentity` object) to
    keep this dataclass free of a hard dependency on `executive_change_
    intelligence.py`'s own types; a caller that needs the full record
    can look it up by name in the same `ExecutiveIdentity` tuple it
    supplied."""


@dataclass(frozen=True)
class EquityAwardDisclosure:
    """Phase 5's own grant-level detail -- populated only from a real
    equity-award table (see `CompensationDisclosureSource.EQUITY_AWARD_
    TABLE`), distinct from the Summary Compensation Table's own
    aggregate dollar columns."""

    executive_name: str
    disclosed_award_type: str | None
    """Verbatim text from an "Award Type"-labeled column, when present
    -- never classified into a closed vocabulary here (see `kind`)."""
    kind: EquityIncentiveKind | None
    """A bounded, literal keyword match against `disclosed_award_type`
    against `incentive_intelligence.EquityIncentiveKind`'s own closed
    vocabulary -- `None` when the disclosed text does not clearly say
    which of those five kinds applies. Reused directly (not
    reinvented) for `build_incentive_knowledge`'s own benefit."""
    grant_value: str | None
    unit_count: str | None
    vesting_disclosure: str | None
    """Verbatim text from a "Vesting Date"/"Vesting Schedule"-labeled
    column, when present -- never a computed vesting date."""
    performance_conditions: str | None
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    table_order_index: int
    row_index: int


@dataclass(frozen=True)
class PerformanceMetricDisclosure:
    """Phase 6's own explicitly-disclosed performance-linked
    compensation evidence. `target`/`range_disclosure`/`weighting`/
    `outcome` are verbatim disclosed text -- "do not estimate targets"
    (Phase 6's own rule) is honored structurally: every one of these is
    `None` unless the filing's own text states it."""

    executive_name: str | None
    """`None` when the metric mention is not clearly attributed to one
    named executive (e.g. a plan-wide metric description) -- never
    guessed."""
    metric_kind: PerformanceMetricKind
    metric_label: str | None
    """Verbatim text for `OTHER_EXPLICIT_METRIC` -- what the filing
    itself calls the measure, when it is not one of the five named
    kinds."""
    target: str | None
    range_disclosure: str | None
    performance_period: str | None
    weighting: str | None
    outcome: str | None
    text: str
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    paragraph_order_index: int | None
    table_order_index: int | None = None
    row_index: int | None = None


@dataclass(frozen=True)
class CompensationChangeObservation:
    kind: CompensationChangeKind
    executive_name: str
    component: CompensationComponentKind | None
    """`None` for `COMPENSATION_MIX_CHANGED`/`PERFORMANCE_MEASURE_
    CHANGED`, which describe a set difference, not one component."""
    previous_value: str | None
    current_value: str | None
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    """The *later* filing/record in the comparison."""


@dataclass(frozen=True)
class ExecutiveCompensationKnowledge:
    records: tuple[ExecutiveCompensationRecord, ...]
    """Every Summary Compensation Table row this call detected, across
    every filing supplied, in filing-then-document order."""
    equity_awards: tuple[EquityAwardDisclosure, ...]
    performance_metrics: tuple[PerformanceMetricDisclosure, ...]
    changes: tuple[CompensationChangeObservation, ...]
    """Phase 7/8's own immutable, pairwise compensation history."""
    filings_considered: tuple[str, ...]
    """Accession numbers of every filing actually used, chronological
    -- `extraction_status in (EXTRACTED, STRUCTURE_UNKNOWN)` only."""


# -- Phase 3: Summary Compensation Table recognition + column mapping --------

#: Live-verified pattern discipline, reused directly from `ownership_
#: intelligence.py`'s own two real fixes: real DEF 14A column headers
#: vary in phrasing ("Non-Equity Incentive Plan Compensation," "Change
#: in Pension Value and Nonqualified Deferred Compensation Earnings")
#: and are frequently styled with bold `<td>` cells rather than real
#: `<th>` tags -- a bounded, word-boundary substring match against each
#: header cell's own full text, plus the identical fallback-header
#: length guard, are used from the start here rather than rediscovering
#: the same two fixes through a second round of live verification.
_NAME_COLUMN_RE = re.compile(r"\bname\b", re.IGNORECASE)
_YEAR_COLUMN_RE = re.compile(r"\byear\b", re.IGNORECASE)
_SALARY_COLUMN_RE = re.compile(r"\bsalary\b", re.IGNORECASE)
_BONUS_COLUMN_RE = re.compile(r"\bbonus\b", re.IGNORECASE)
_STOCK_AWARDS_COLUMN_RE = re.compile(r"\bstock awards?\b", re.IGNORECASE)
_OPTION_AWARDS_COLUMN_RE = re.compile(r"\boption awards?\b", re.IGNORECASE)
_NON_EQUITY_COLUMN_RE = re.compile(r"\bnon-?equity incentive\b", re.IGNORECASE)
_PENSION_COLUMN_RE = re.compile(r"\b(change in pension|pension value)\b", re.IGNORECASE)
_OTHER_COMP_COLUMN_RE = re.compile(r"\ball other compensation\b", re.IGNORECASE)
_TOTAL_COLUMN_RE = re.compile(r"\btotal\b", re.IGNORECASE)
_ROLE_COLUMN_RE = re.compile(r"\b(principal position|title|position)\b", re.IGNORECASE)

#: Equity-award-table-specific column labels (Phase 5) -- a distinct
#: table shape from the Summary Compensation Table, so matched
#: separately rather than folded into the patterns above.
_GRANT_DATE_COLUMN_RE = re.compile(r"\bgrant date\b", re.IGNORECASE)
_AWARD_TYPE_COLUMN_RE = re.compile(r"\b(award type|type of award)\b", re.IGNORECASE)
_UNIT_COUNT_COLUMN_RE = re.compile(r"\b(number of (shares|units)|shares or units)\b", re.IGNORECASE)
_GRANT_VALUE_COLUMN_RE = re.compile(r"\b(grant date fair value|fair value)\b", re.IGNORECASE)
_VESTING_COLUMN_RE = re.compile(r"\bvest(ing)?\b", re.IGNORECASE)
_PERFORMANCE_CONDITION_COLUMN_RE = re.compile(r"\bperformance (condition|goal|criteria)s?\b", re.IGNORECASE)

_MAX_FALLBACK_HEADER_CELL_LENGTH = 40
_ALL_SUMMARY_TABLE_HEADER_RES = (
    _NAME_COLUMN_RE, _YEAR_COLUMN_RE, _SALARY_COLUMN_RE, _BONUS_COLUMN_RE, _STOCK_AWARDS_COLUMN_RE,
    _OPTION_AWARDS_COLUMN_RE, _NON_EQUITY_COLUMN_RE, _PENSION_COLUMN_RE, _OTHER_COMP_COLUMN_RE, _TOTAL_COLUMN_RE,
)
_ALL_EQUITY_TABLE_HEADER_RES = (
    _NAME_COLUMN_RE, _GRANT_DATE_COLUMN_RE, _AWARD_TYPE_COLUMN_RE, _UNIT_COUNT_COLUMN_RE, _GRANT_VALUE_COLUMN_RE,
)


def _header_row(table: FilingTable) -> TableRow | None:
    if table.header is None or not table.header.rows:
        return None
    return table.header.rows[0]


def _looks_like_a_header_cell(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    if len(text) > _MAX_FALLBACK_HEADER_CELL_LENGTH:
        return False
    return any(pattern.search(text) for pattern in patterns)


def _resolve_header_and_body(
    table: FilingTable, patterns: tuple[re.Pattern[str], ...],
) -> tuple[TableRow | None, tuple[TableRow, ...]]:
    """Identical fallback to `ownership_intelligence._resolve_header_
    and_body`/`governance_intelligence._resolve_header_and_body`,
    reimplemented here since it is this module's own classification
    concern, not a duplication of Filing Content Intelligence's own
    HTML parsing."""
    header = _header_row(table)
    if header is not None:
        return header, table.rows
    if not table.rows:
        return None, ()
    candidate = table.rows[0]
    if any(_looks_like_a_header_cell(cell.text, patterns) for cell in candidate.cells):
        return candidate, table.rows[1:]
    return None, table.rows


def _column_index(header: TableRow, pattern: re.Pattern[str]) -> int | None:
    """Returns the header cell's true *grid* column position (summing
    `colspan`, not `cell.order_index`) -- see `_virtualize_body_rows`
    for why this must match the same grid a body row is read against."""
    col = 0
    for cell in header.cells:
        if pattern.search(cell.text):
            return col
        col += max(cell.colspan, 1)
    return None


def _grid_width(header: TableRow) -> int:
    return sum(max(cell.colspan, 1) for cell in header.cells)


def _virtualize_body_rows(header: TableRow, body_rows: tuple[TableRow, ...]) -> tuple[tuple[str | None, ...], ...]:
    """Re-expresses each body row's own literal cells at their true
    grid-column position, carrying `rowspan`/`colspan` state forward
    across rows exactly as a browser would when laying out the table.

    This is a real, mechanical need, not an optimization: a real DEF
    14A's Summary Compensation Table discloses each executive's
    multiple reporting years as one `rowspan`'d Name cell -- the HTML
    for every year *after* the first literally omits that cell, so a
    continuation row's own literal cell list is shorter than the
    header's, and every subsequent cell's literal position silently
    shifts left by however many cells were omitted. Reading a
    continuation row's "Salary" cell by the header's own column index
    without this correction reads the wrong cell entirely (confirmed
    live against a real AAPL DEF 14A, where an uncorrected read pulled
    an empty spacer cell instead of the real salary value). `rowspan`/
    `colspan` are real, disclosed attribute values (Filing Content
    Intelligence's own `TableCell.rowspan`/`colspan`) -- resolving them
    into a grid position is decoding, not inferring."""
    width = _grid_width(header)
    occupied: dict[int, int] = {}
    grid_rows: list[tuple[str | None, ...]] = []
    for row in body_rows:
        grid: list[str | None] = [None] * width
        cells = list(row.cells)
        cell_index = 0
        col = 0
        while col < width:
            remaining = occupied.get(col, 0)
            if remaining > 0:
                occupied[col] = remaining - 1
                col += 1
                continue
            if cell_index >= len(cells):
                break
            cell = cells[cell_index]
            cell_index += 1
            span = max(cell.colspan, 1)
            for offset in range(span):
                if col + offset < width:
                    grid[col + offset] = cell.text
            if cell.rowspan > 1:
                for offset in range(span):
                    if col + offset < width:
                        occupied[col + offset] = cell.rowspan - 1
            col += span
        grid_rows.append(tuple(grid))
    return tuple(grid_rows)


def _grid_cell_text(grid_row: tuple[str | None, ...], column_index: int | None) -> str | None:
    if column_index is None or column_index >= len(grid_row):
        return None
    text = grid_row[column_index]
    if text is None:
        return None
    text = text.strip()
    return text or None


@dataclass(frozen=True)
class _SummaryRow:
    name: str
    role: str | None
    year: str | None
    salary: str | None
    bonus: str | None
    stock_awards: str | None
    option_awards: str | None
    non_equity_incentive: str | None
    pension_change: str | None
    other_compensation: str | None
    total: str | None
    row_index: int


def _extract_summary_table(table: FilingTable) -> tuple[_SummaryRow, ...] | None:
    """Returns `None` when the table does not qualify as a Summary
    Compensation Table at all (no header, no `"Name"` column, or no
    `"Salary"` column) -- never a guess.

    Live verification against a real DEF 14A (AAPL, accession
    0001308179-26-000008) found this table must require a `Salary`
    column specifically, not merely a `Bonus` or `Total` column: a
    `Name` + `Total` gate alone was a false-positive magnet, matching
    the Director Compensation table ("Fees Earned or Paid in Cash" /
    "Total"), the post-employment "Estimated Total Value upon
    Retirement/Death/Disability" table, and an outstanding-equity share-
    count table -- none of which are the executive Summary Compensation
    Table, all of which happen to have a "Total"-labeled column. Only
    the real Summary Compensation Table discloses a per-named-executive
    `Salary` -- non-employee directors are paid fees, not salary, so
    this one column reliably separates the two."""
    header, body_rows = _resolve_header_and_body(table, _ALL_SUMMARY_TABLE_HEADER_RES)
    if header is None:
        return None
    name_index = _column_index(header, _NAME_COLUMN_RE)
    if name_index is None:
        return None
    salary_index = _column_index(header, _SALARY_COLUMN_RE)
    if salary_index is None:
        return None
    bonus_index = _column_index(header, _BONUS_COLUMN_RE)
    total_index = _column_index(header, _TOTAL_COLUMN_RE)
    role_index = _column_index(header, _ROLE_COLUMN_RE)
    if role_index == name_index:
        # Real DEF 14As commonly disclose a single combined "Name and
        # Principal Position" column (name and title joined by a <br>
        # inside one cell, which Filing Content Intelligence's own
        # whitespace collapsing renders as one space-joined string with
        # no reliable delimiter). Splitting that string into a name
        # part and a role part would require guessing where the name
        # ends and an unbounded-variety title begins -- exactly the
        # kind of inference Phase 2/4 forbid ("never infer a role from
        # name recognition"). So `role` is left unpopulated rather than
        # duplicated with the same verbatim text already captured in
        # `name`; `executive_name` itself keeps the full, verbatim,
        # un-split cell text, and cross-table/identity linking on that
        # combined string simply will not match a bare name elsewhere
        # -- an honest limitation, not a fabricated split.
        role_index = None
    year_index = _column_index(header, _YEAR_COLUMN_RE)
    stock_index = _column_index(header, _STOCK_AWARDS_COLUMN_RE)
    option_index = _column_index(header, _OPTION_AWARDS_COLUMN_RE)
    non_equity_index = _column_index(header, _NON_EQUITY_COLUMN_RE)
    pension_index = _column_index(header, _PENSION_COLUMN_RE)
    other_comp_index = _column_index(header, _OTHER_COMP_COLUMN_RE)

    grid_rows = _virtualize_body_rows(header, body_rows)
    rows: list[_SummaryRow] = []
    carried_name: str | None = None
    for row, grid in zip(body_rows, grid_rows):
        name = _grid_cell_text(grid, name_index)
        salary = _grid_cell_text(grid, salary_index)
        year = _grid_cell_text(grid, year_index)
        if not name:
            # A real DEF 14A discloses each named executive's multi-
            # year rows as a single HTML `rowspan`'d Name cell -- only
            # the first of that executive's rows carries the name text
            # at all; later years leave the Name cell empty in the raw
            # HTML. This is a mechanical, deterministic consequence of
            # `rowspan` layout (verified live against a real DEF 14A
            # where dropping these rows silently discarded the prior
            # two years' history for every executive), not an inferred
            # guess about identity -- so an empty Name cell inherits the
            # immediately preceding row's own name only when this row
            # otherwise carries real compensation data of its own
            # (Salary or Year present); a genuinely blank row (a
            # spacer, a footnote row) still yields no record.
            if carried_name is None or not (salary or year):
                continue
            name = carried_name
        else:
            carried_name = name
        rows.append(
            _SummaryRow(
                name=name, role=_grid_cell_text(grid, role_index), year=year,
                salary=salary, bonus=_grid_cell_text(grid, bonus_index),
                stock_awards=_grid_cell_text(grid, stock_index), option_awards=_grid_cell_text(grid, option_index),
                non_equity_incentive=_grid_cell_text(grid, non_equity_index),
                pension_change=_grid_cell_text(grid, pension_index),
                other_compensation=_grid_cell_text(grid, other_comp_index), total=_grid_cell_text(grid, total_index),
                row_index=row.order_index,
            )
        )
    return tuple(rows)


@dataclass(frozen=True)
class _EquityRow:
    name: str
    award_type: str | None
    grant_value: str | None
    unit_count: str | None
    vesting: str | None
    performance_conditions: str | None
    row_index: int


def _extract_equity_award_table(table: FilingTable) -> tuple[_EquityRow, ...] | None:
    header, body_rows = _resolve_header_and_body(table, _ALL_EQUITY_TABLE_HEADER_RES)
    if header is None:
        return None
    name_index = _column_index(header, _NAME_COLUMN_RE)
    if name_index is None:
        return None
    award_type_index = _column_index(header, _AWARD_TYPE_COLUMN_RE)
    unit_count_index = _column_index(header, _UNIT_COUNT_COLUMN_RE)
    grant_value_index = _column_index(header, _GRANT_VALUE_COLUMN_RE)
    if award_type_index is None and unit_count_index is None and grant_value_index is None:
        return None
    vesting_index = _column_index(header, _VESTING_COLUMN_RE)
    performance_index = _column_index(header, _PERFORMANCE_CONDITION_COLUMN_RE)

    grid_rows = _virtualize_body_rows(header, body_rows)
    rows: list[_EquityRow] = []
    carried_name: str | None = None
    for row, grid in zip(body_rows, grid_rows):
        name = _grid_cell_text(grid, name_index)
        award_type = _grid_cell_text(grid, award_type_index)
        grant_value = _grid_cell_text(grid, grant_value_index)
        unit_count = _grid_cell_text(grid, unit_count_index)
        vesting = _grid_cell_text(grid, vesting_index)
        performance_conditions = _grid_cell_text(grid, performance_index)
        if not name:
            # Mirrors `_extract_summary_table`'s own rowspan carry-
            # forward: a real DEF 14A equity-award table also discloses
            # one executive's several award rows (one per grant date)
            # under a single rowspan'd Name cell.
            if carried_name is None or not (award_type or grant_value or unit_count):
                continue
            name = carried_name
        else:
            carried_name = name
        rows.append(
            _EquityRow(
                name=name, award_type=award_type, grant_value=grant_value,
                unit_count=unit_count, vesting=vesting,
                performance_conditions=performance_conditions, row_index=row.order_index,
            )
        )
    return tuple(rows)


_EQUITY_KIND_PATTERNS: tuple[tuple[re.Pattern[str], EquityIncentiveKind], ...] = (
    (re.compile(r"\b(RSUs?|restricted stock units?)\b", re.IGNORECASE), EquityIncentiveKind.RSU),
    (re.compile(r"\b(PSUs?|performance stock units?|performance shares?)\b", re.IGNORECASE), EquityIncentiveKind.PSU),
    (re.compile(r"\brestricted stock\b", re.IGNORECASE), EquityIncentiveKind.RESTRICTED_STOCK),
    (re.compile(r"\b(stock )?options?\b", re.IGNORECASE), EquityIncentiveKind.OPTION),
)


def _classify_equity_kind(disclosed_award_type: str | None) -> EquityIncentiveKind | None:
    if disclosed_award_type is None:
        return None
    for pattern, kind in _EQUITY_KIND_PATTERNS:
        if pattern.search(disclosed_award_type):
            return kind
    return None


# -- Phase 6: performance-linked compensation (bounded keyword match) -------

_PERFORMANCE_METRIC_PATTERNS: tuple[tuple[re.Pattern[str], PerformanceMetricKind], ...] = (
    (re.compile(r"\b(EPS|earnings per share)\b", re.IGNORECASE), PerformanceMetricKind.EPS_TARGET),
    (re.compile(r"\brevenue\b", re.IGNORECASE), PerformanceMetricKind.REVENUE_TARGET),
    (re.compile(r"\bmargin\b", re.IGNORECASE), PerformanceMetricKind.MARGIN_TARGET),
    (re.compile(r"\b(TSR|total shareholder return)\b", re.IGNORECASE), PerformanceMetricKind.TSR_TARGET),
    (re.compile(r"\b(ROIC|return on invested capital)\b", re.IGNORECASE), PerformanceMetricKind.ROIC_TARGET),
)
#: A real, bounded signal that a paragraph discusses a performance
#: condition at all -- distinct from the specific metric patterns
#: above, which classify *which* metric once this gate is already true.
#: Hand-tested against real DEF 14A phrasing before finalizing: "Vesting
#: of the performance stock units is subject to achievement of a
#: revenue target over a three-year performance period" -- an early,
#: narrower version of this pattern required "vesting" and "subject to"
#: to sit immediately adjacent and missed this real sentence entirely
#: (the real text has "of the performance stock units" between them).
#: Broadened to independent phrase alternatives -- "performance period"/
#: "performance share(s)"/"performance unit(s)" and "subject to (the)
#: achievement of" are now also real, standalone triggers, each still a
#: bounded, literal phrase, never an open-ended "performance" alone.
_PERFORMANCE_LINKED_RE = re.compile(
    r"\b(performance[\s-]based|performance (condition|goal|criteria|metric|target|period)s?|"
    r"performance shares?|performance units?|subject to (the )?achievement of|"
    r"vesting (is|was|will be) (subject to|based on|contingent on|tied to))\b",
    re.IGNORECASE,
)


def _matching_performance_metrics(text: str) -> tuple[PerformanceMetricKind, ...]:
    matched = tuple(kind for pattern, kind in _PERFORMANCE_METRIC_PATTERNS if pattern.search(text))
    return matched


# -- Extraction ----------------------------------------------------------------

_USABLE_STATUSES = frozenset({ExtractionStatus.EXTRACTED, ExtractionStatus.STRUCTURE_UNKNOWN})


def _iter_tables(
    content: FilingContent,
) -> "list[tuple[FilingTable, FilingSection | None, FilingSubsection | None]]":
    result: list[tuple[FilingTable, FilingSection | None, FilingSubsection | None]] = []
    for table in content.unattributed_tables:
        result.append((table, None, None))
    for section in content.sections:
        for table in section.tables:
            result.append((table, section, None))
        for subsection in section.subsections:
            for table in subsection.tables:
                result.append((table, section, subsection))
    return result


def _iter_paragraphs(
    content: FilingContent,
) -> "list[tuple[FilingParagraph, FilingSection | None, FilingSubsection | None]]":
    result: list[tuple[FilingParagraph, FilingSection | None, FilingSubsection | None]] = []
    for paragraph in content.unattributed_paragraphs:
        result.append((paragraph, None, None))
    for section in content.sections:
        for paragraph in section.paragraphs:
            result.append((paragraph, section, None))
        for subsection in section.subsections:
            for paragraph in subsection.paragraphs:
                result.append((paragraph, section, subsection))
    return result


def _parse_plain_number(text: str | None) -> float | None:
    """Only succeeds for genuinely plain, disclosed numeric text -- an
    optional leading `$`, digit groups with commas, an optional
    decimal. A trailing footnote marker, a range, or any other
    character honestly returns `None` -- never a best-effort guess."""
    if text is None:
        return None
    cleaned = text.strip()
    if not re.fullmatch(r"\$?-?[\d,]+(\.\d+)?", cleaned):
        return None
    try:
        return float(cleaned.replace("$", "").replace(",", ""))
    except ValueError:
        return None


def _sort_key(record: ExecutiveCompensationRecord) -> tuple[int, datetime]:
    """Chronological ordering for pairwise comparison -- the disclosed
    `reporting_year`, when it parses as a plain 4-digit year, else the
    filing's own `filed_at` as a fallback. Reading a disclosed calendar
    year as an integer for ordering is not an estimate; it is the same
    category of read as Filing Content Intelligence's own `filed_at`."""
    if record.reporting_year is not None and re.fullmatch(r"\d{4}", record.reporting_year.strip()):
        return (int(record.reporting_year.strip()), record.filed_at)
    return (0, record.filed_at)


_COMPONENT_FIELDS: tuple[tuple[CompensationComponentKind, str], ...] = (
    (CompensationComponentKind.SALARY, "salary"),
    (CompensationComponentKind.BONUS, "bonus"),
    (CompensationComponentKind.STOCK_AWARDS, "stock_awards"),
    (CompensationComponentKind.OPTION_AWARDS, "option_awards"),
    (CompensationComponentKind.NON_EQUITY_INCENTIVE, "non_equity_incentive"),
    (CompensationComponentKind.PENSION_CHANGE, "pension_change"),
    (CompensationComponentKind.OTHER_COMPENSATION, "other_compensation"),
)


def _present_components(record: ExecutiveCompensationRecord) -> frozenset[CompensationComponentKind]:
    return frozenset(kind for kind, field in _COMPONENT_FIELDS if getattr(record, field) is not None)


def extract_executive_compensation_knowledge(
    filing_contents: tuple[FilingContent, ...], executive_identities: tuple[ExecutiveIdentity, ...] = (),
) -> ExecutiveCompensationKnowledge:
    """Built entirely upon Filing Content Intelligence's own output --
    never fetches, parses HTML, or reads a `RegulatoryFiling` directly.
    `executive_identities` is optional, read-only correlation input
    (Phase 4) -- a caller-supplied `tuple[executive_change_
    intelligence.ExecutiveIdentity, ...]`; this module never computes
    that itself, and never imports that module for anything beyond its
    own already-public `ExecutiveIdentity` type. Linking is exact,
    case-insensitive name equality only (Phase 4's own "do not link
    solely because names look similar") -- a disclosed role that
    differs from the identity's own `raw_title` never blocks the link
    (a compensation record's own "Name" column sometimes omits a
    title, or states it differently than an earnings call transcript
    did); it is not treated as an additional veto this module invents."""
    usable = tuple(sorted((c for c in filing_contents if c.extraction_status in _USABLE_STATUSES), key=lambda c: c.filed_at))
    identity_by_name = {identity.name.strip().lower(): identity for identity in executive_identities}

    all_records: list[ExecutiveCompensationRecord] = []
    all_equity_awards: list[EquityAwardDisclosure] = []
    all_performance_metrics: list[PerformanceMetricDisclosure] = []

    for content in usable:
        for table, section, subsection in _iter_tables(content):
            summary_rows = _extract_summary_table(table)
            if summary_rows is not None:
                currency = None
                context = " ".join(filter(None, (table.caption, table.heading_context)))
                currency_match = re.search(r"\b(USD|EUR|GBP|JPY|CHF|CAD)\b", context)
                if currency_match:
                    currency = currency_match.group(1)
                for row in summary_rows:
                    linked_name = None
                    identity = identity_by_name.get(row.name.strip().lower())
                    if identity is not None:
                        linked_name = identity.name
                    all_records.append(
                        ExecutiveCompensationRecord(
                            executive_name=row.name, disclosed_role=row.role, reporting_year=row.year,
                            salary=row.salary, bonus=row.bonus, stock_awards=row.stock_awards,
                            option_awards=row.option_awards, non_equity_incentive=row.non_equity_incentive,
                            pension_change=row.pension_change, other_compensation=row.other_compensation,
                            total=row.total, currency=currency, source=CompensationDisclosureSource.SUMMARY_COMPENSATION_TABLE,
                            accession_number=content.accession_number, form_type=content.form_type,
                            filed_at=content.filed_at, source_reference=content.source_reference,
                            section_kind=section.kind if section else None,
                            section_item_number=section.item_number if section else None,
                            subsection_heading=subsection.heading_text if subsection is not None else None,
                            table_order_index=table.order_index, row_index=row.row_index,
                            linked_executive_identity_name=linked_name,
                        )
                    )
                continue  # a table already recognized as the Summary Compensation Table is never also read as an equity-award table

            equity_rows = _extract_equity_award_table(table)
            if equity_rows is not None:
                for row in equity_rows:
                    all_equity_awards.append(
                        EquityAwardDisclosure(
                            executive_name=row.name, disclosed_award_type=row.award_type,
                            kind=_classify_equity_kind(row.award_type), grant_value=row.grant_value,
                            unit_count=row.unit_count, vesting_disclosure=row.vesting,
                            performance_conditions=row.performance_conditions, accession_number=content.accession_number,
                            form_type=content.form_type, filed_at=content.filed_at,
                            source_reference=content.source_reference, table_order_index=table.order_index,
                            row_index=row.row_index,
                        )
                    )

        for paragraph, section, subsection in _iter_paragraphs(content):
            text = paragraph.text
            if not _PERFORMANCE_LINKED_RE.search(text):
                continue
            metric_kinds = _matching_performance_metrics(text)
            targets = metric_kinds if metric_kinds else (PerformanceMetricKind.OTHER_EXPLICIT_METRIC,)
            for metric_kind in targets:
                all_performance_metrics.append(
                    PerformanceMetricDisclosure(
                        executive_name=None, metric_kind=metric_kind,
                        metric_label=text if metric_kind is PerformanceMetricKind.OTHER_EXPLICIT_METRIC else None,
                        target=None, range_disclosure=None, performance_period=None, weighting=None, outcome=None,
                        text=text, accession_number=content.accession_number, form_type=content.form_type,
                        filed_at=content.filed_at, source_reference=content.source_reference,
                        paragraph_order_index=paragraph.order_index,
                    )
                )

    changes = _compute_changes(all_records)

    return ExecutiveCompensationKnowledge(
        records=tuple(all_records), equity_awards=tuple(all_equity_awards),
        performance_metrics=tuple(all_performance_metrics), changes=changes,
        filings_considered=tuple(c.accession_number for c in usable),
    )


def _compute_changes(records: list[ExecutiveCompensationRecord]) -> tuple[CompensationChangeObservation, ...]:
    """Phase 7/8: groups records by (executive name, role) and compares
    each consecutive pair in chronological order (Phase 5's own "do not
    generate observations when periods are not comparable" -- only ever
    adjacent, real records are compared, never a record to itself or to
    a non-adjacent year)."""
    by_executive: dict[str, list[ExecutiveCompensationRecord]] = {}
    for record in records:
        by_executive.setdefault(record.executive_name.strip().lower(), []).append(record)

    changes: list[CompensationChangeObservation] = []
    for grouped in by_executive.values():
        ordered = sorted(grouped, key=_sort_key)
        for earlier, later in zip(ordered, ordered[1:]):
            changes.extend(_compare_pair(earlier, later))
    return tuple(changes)


def _compare_component(
    earlier: ExecutiveCompensationRecord, later: ExecutiveCompensationRecord, component: CompensationComponentKind,
    field: str, increased_kind: CompensationChangeKind, decreased_kind: CompensationChangeKind,
) -> CompensationChangeObservation | None:
    earlier_text = getattr(earlier, field)
    later_text = getattr(later, field)
    if earlier_text is None or later_text is None:
        return None
    earlier_value = _parse_plain_number(earlier_text)
    later_value = _parse_plain_number(later_text)
    if earlier_value is None or later_value is None:
        return CompensationChangeObservation(
            kind=CompensationChangeKind.COMPENSATION_NOT_COMPARABLE, executive_name=later.executive_name,
            component=component, previous_value=earlier_text, current_value=later_text,
            accession_number=later.accession_number, form_type=later.form_type, filed_at=later.filed_at,
            source_reference=later.source_reference,
        )
    if later_value == earlier_value:
        return None
    kind = increased_kind if later_value > earlier_value else decreased_kind
    return CompensationChangeObservation(
        kind=kind, executive_name=later.executive_name, component=component, previous_value=earlier_text,
        current_value=later_text, accession_number=later.accession_number, form_type=later.form_type,
        filed_at=later.filed_at, source_reference=later.source_reference,
    )


def _compare_pair(
    earlier: ExecutiveCompensationRecord, later: ExecutiveCompensationRecord,
) -> tuple[CompensationChangeObservation, ...]:
    observations: list[CompensationChangeObservation] = []

    salary_change = _compare_component(
        earlier, later, CompensationComponentKind.SALARY, "salary",
        CompensationChangeKind.SALARY_INCREASED, CompensationChangeKind.SALARY_DECREASED,
    )
    if salary_change is not None:
        observations.append(salary_change)

    stock_change = _compare_component(
        earlier, later, CompensationComponentKind.STOCK_AWARDS, "stock_awards",
        CompensationChangeKind.STOCK_AWARD_VALUE_INCREASED, CompensationChangeKind.STOCK_AWARD_VALUE_DECREASED,
    )
    if stock_change is not None:
        observations.append(stock_change)

    if earlier.bonus is None and later.bonus is not None:
        observations.append(
            CompensationChangeObservation(
                kind=CompensationChangeKind.BONUS_INTRODUCED, executive_name=later.executive_name,
                component=CompensationComponentKind.BONUS, previous_value=None, current_value=later.bonus,
                accession_number=later.accession_number, form_type=later.form_type, filed_at=later.filed_at,
                source_reference=later.source_reference,
            )
        )
    if earlier.option_awards is None and later.option_awards is not None:
        observations.append(
            CompensationChangeObservation(
                kind=CompensationChangeKind.OPTION_AWARDS_INTRODUCED, executive_name=later.executive_name,
                component=CompensationComponentKind.OPTION_AWARDS, previous_value=None, current_value=later.option_awards,
                accession_number=later.accession_number, form_type=later.form_type, filed_at=later.filed_at,
                source_reference=later.source_reference,
            )
        )

    earlier_mix = _present_components(earlier)
    later_mix = _present_components(later)
    if earlier_mix != later_mix:
        observations.append(
            CompensationChangeObservation(
                kind=CompensationChangeKind.COMPENSATION_MIX_CHANGED, executive_name=later.executive_name,
                component=None, previous_value=None, current_value=None, accession_number=later.accession_number,
                form_type=later.form_type, filed_at=later.filed_at, source_reference=later.source_reference,
            )
        )

    return tuple(observations)


# -- Phase 9: Incentive Intelligence integration (additive; incentive_
# intelligence.py itself is never modified) ----------------------------------

def build_incentive_knowledge(compensation: ExecutiveCompensationKnowledge) -> tuple[ExecutiveIncentiveProgram, ...]:
    """Constructs real `incentive_intelligence.ExecutiveIncentiveProgram`
    instances from this module's own already-extracted, real evidence
    -- `incentive_intelligence.py` itself is never imported for
    modification, only for its own existing, unmodified types. Only
    populates what the evidence honestly supports: a `CashIncentive`
    only when a real bonus/non-equity-incentive value was disclosed, an
    `EquityIncentive` only from a real equity-award-table row with a
    classifiable `kind`, a `PerformanceIncentive` only from a real,
    disclosed metric mention. Fields this module has no evidence for
    (`OwnershipAlignment`, `DilutionEvent`, `IncentiveTimelineEvent`)
    are never populated here -- doing so would require ownership or
    Form-4 evidence explicitly out of this module's own scope
    (Phase 10)."""
    programs_by_name: dict[str, dict] = {}

    for record in compensation.records:
        entry = programs_by_name.setdefault(
            record.executive_name,
            {"role": record.disclosed_role, "cash": [], "equity": [], "performance": [], "source": []},
        )
        if entry["role"] is None and record.disclosed_role is not None:
            entry["role"] = record.disclosed_role
        entry["source"].append(record.accession_number)
        if record.bonus is not None:
            entry["cash"].append(
                CashIncentive(
                    executive_name=record.executive_name, kind=CashIncentiveKind.ANNUAL_BONUS,
                    program="Summary Compensation Table", source=record.accession_number,
                    effective_period=record.reporting_year, status=IncentiveEvidenceStatus.OBSERVED,
                    provenance=f"{record.accession_number}:table{record.table_order_index}:row{record.row_index}",
                )
            )
        if record.non_equity_incentive is not None:
            entry["cash"].append(
                CashIncentive(
                    executive_name=record.executive_name, kind=CashIncentiveKind.MILESTONE_BONUS,
                    program="Summary Compensation Table (Non-Equity Incentive Plan Compensation)",
                    source=record.accession_number, effective_period=record.reporting_year,
                    status=IncentiveEvidenceStatus.OBSERVED,
                    provenance=f"{record.accession_number}:table{record.table_order_index}:row{record.row_index}",
                )
            )

    for award in compensation.equity_awards:
        if award.kind is None:
            continue
        entry = programs_by_name.setdefault(
            award.executive_name, {"role": None, "cash": [], "equity": [], "performance": [], "source": []},
        )
        entry["source"].append(award.accession_number)
        entry["equity"].append(
            EquityIncentive(
                executive_name=award.executive_name, kind=award.kind, program="DEF 14A equity award table",
                source=award.accession_number, effective_period=None, status=IncentiveEvidenceStatus.OBSERVED,
                provenance=f"{award.accession_number}:table{award.table_order_index}:row{award.row_index}",
            )
        )

    for metric in compensation.performance_metrics:
        if metric.executive_name is None:
            continue
        entry = programs_by_name.setdefault(
            metric.executive_name, {"role": None, "cash": [], "equity": [], "performance": [], "source": []},
        )
        entry["source"].append(metric.accession_number)
        entry["performance"].append(
            PerformanceIncentive(
                executive_name=metric.executive_name, metric_kind=metric.metric_kind, explicit_target=None,
                program="Proxy statement disclosure", source=metric.accession_number,
                status=IncentiveEvidenceStatus.OBSERVED,
                provenance=f"{metric.accession_number}:paragraph{metric.paragraph_order_index}",
            )
        )

    programs: list[ExecutiveIncentiveProgram] = []
    for name in sorted(programs_by_name):
        entry = programs_by_name[name]
        if not (entry["cash"] or entry["equity"] or entry["performance"]):
            continue
        programs.append(
            ExecutiveIncentiveProgram(
                executive_name=name, role=entry["role"], program="Proxy statement compensation disclosure",
                source=entry["source"][0] if entry["source"] else None, effective_period=None,
                status=IncentiveEvidenceStatus.OBSERVED, equity_incentives=tuple(entry["equity"]),
                cash_incentives=tuple(entry["cash"]), performance_incentives=tuple(entry["performance"]),
            )
        )
    return tuple(programs)


def build_incentive_structures(compensation: ExecutiveCompensationKnowledge) -> tuple[IncentiveStructure, ...]:
    """A second, independent bridge into `incentive_intelligence.
    IncentiveStructure` -- the *set* of real, disclosed compensation
    components per executive, mapped onto that dataclass's own closed
    `IncentiveStructureComponent` vocabulary. Only components this
    module has direct, disclosed evidence for are ever included."""
    _COMPONENT_MAP = {
        CompensationComponentKind.SALARY: IncentiveStructureComponent.FIXED_SALARY,
        CompensationComponentKind.BONUS: IncentiveStructureComponent.ANNUAL_BONUS,
        CompensationComponentKind.STOCK_AWARDS: IncentiveStructureComponent.EQUITY_AWARDS,
        CompensationComponentKind.OPTION_AWARDS: IncentiveStructureComponent.EQUITY_AWARDS,
        CompensationComponentKind.NON_EQUITY_INCENTIVE: IncentiveStructureComponent.LONG_TERM_INCENTIVES,
        CompensationComponentKind.PENSION_CHANGE: IncentiveStructureComponent.DEFERRED_COMPENSATION,
    }
    components_by_name: dict[str, set[IncentiveStructureComponent]] = {}
    source_by_name: dict[str, str] = {}
    for record in compensation.records:
        components = components_by_name.setdefault(record.executive_name, set())
        source_by_name.setdefault(record.executive_name, record.accession_number)
        for kind, field in _COMPONENT_FIELDS:
            if getattr(record, field) is not None and kind in _COMPONENT_MAP:
                components.add(_COMPONENT_MAP[kind])

    return tuple(
        IncentiveStructure(
            executive_name=name, components=tuple(sorted(components_by_name[name], key=lambda c: c.value)),
            source=source_by_name[name], provenance=f"{source_by_name[name]}:summary_compensation_table",
        )
        for name in sorted(components_by_name)
        if components_by_name[name]
    )
