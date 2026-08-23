"""Governance Intelligence: transforms Filing Content Intelligence's
own structured filing objects into structured, traceable governance
knowledge (Capability Expansion Sprint 15).

**Phase 1 audit finding.** Re-read fresh, not assumed: Atlas can
already discover filings (`regulatory_filings.py`), fetch and structure
their content (`filing_content_intelligence.py`, Sprints 13-14 --
sections, subsections, paragraphs, tables, references, all with full
provenance), and detect 10-K's own real `GOVERNANCE`/`EXECUTIVE_
COMPENSATION`/`DIRECTOR_COMPENSATION` sections and 8-K's own real
`EXECUTIVE_CHANGE` section (Item 5.02 -- "Departure of Directors or
Certain Officers; Election of Directors"). No existing module reads
that structure and produces governance-specific knowledge -- this is
the one, real gap this sprint fills. `KnowledgeDomain` had no existing
member for it either: `MANAGEMENT` covers executive/management
intelligence (a distinct, already-shipped capability), `OWNERSHIP`/
`INSTITUTIONAL_OWNERSHIP`/`INSIDER_ACTIVITY` cover shareholding, not
board structure -- `KnowledgeDomain.GOVERNANCE` is a new, minimum
necessary registry addition (`knowledge_coverage/models.py`), not a
redesign.

**The load-bearing constraint this sprint's whole design turns on**:
`filing_content_intelligence.FilingTable` deliberately never extracts
table *cell content* -- only row/column counts (see that module's own
docstring: "cell content is never extracted here"). Real director
rosters, committee-membership matrices, and share-class tables in a
DEF 14A are presented in HTML tables. Without cell text, Governance
Intelligence has no reliable, disclosed, non-inferential way to
extract *who* sits on a board or committee -- attempting to parse names
out of free-text paragraphs instead would require exactly the kind of
inference ("this capitalized phrase is probably a person's name") this
sprint's own "never infer, never fabricate" instruction forbids, and
modifying Filing Content Intelligence to extract cell text is out of
this sprint's own explicit scope. `BoardComposition.directors`,
`Committee.members`/`.chair`, and `VotingStructure.share_classes`
therefore stay real, typed, always-`()` framework today -- the same
disclosed "framework, not complete dataset" pattern `incentive_
intelligence.py` (Sprint 12) already established for facts no existing
provider supplies, re-applied here for a fact no existing *extractor
boundary* supplies. A future sprint that gives Filing Content
Intelligence (or a new Form 3/4/5 provider) real per-cell/per-person
data can populate these types without changing their shape.

**What genuinely is safe and deterministic today**: whether a filing's
own real, verbatim text *names* a standard governance construct --
"Audit Committee," "Lead Independent Director," "dual-class," a real
`EXECUTIVE_CHANGE` (Item 5.02) section's own presence. Matching a
literal, disclosed phrase is preservation, not inference -- the same
category of fact as Filing Content Intelligence's own `Item N` heading
match. This module is careful to keep the resulting claim exactly that
narrow: a `GovernanceFinding` says the filing's own text *discloses*
the phrase, never that the company *has* whatever the phrase names as
an organizational conclusion.

**Phase 9 boundary**: reads only `FilingContent` (Filing Content
Intelligence's own output) and produces `GovernanceKnowledge` -- it
never imports an evaluator, is never called from `models.py`/
`service.py`/the API schema, and generates no score, rank, or opinion.

**Capability Expansion Sprint 16 audit finding.** The Table Extraction
infrastructure sprint removed the exact constraint this module's own
docstring above described: `FilingTable` now preserves real
`TableHeader`/`TableRow`/`TableCell` structure, including verbatim cell
text. This sprint teaches this module to consume that structure --
`BoardComposition.directors`, `Committee.members`/`.chair`, and
`VotingStructure.share_classes` are no longer permanently-empty
framework; they are populated when a table's own header row literally
labels a column (e.g. `"Name"`, `"Independent"`, `"Class"`).

**Why reading a labeled column is preservation, not inference.** This
is the same distinction Filing Content Intelligence's own `Item N`
heading match already relies on: the filer itself declares a column's
own meaning via its own header text (e.g. a column literally headed
`"Name"`). Reading the values under that column as names is reading
disclosed, author-declared structure -- categorically different from
guessing which capitalized word in a paragraph is a person's name
(which this module still never attempts). `disclosed_independence` is
set only from a literal, exact `"yes"`/`"no"` cell value under a
column literally headed `"Independent"`/`"Independence"` -- any other
value is honestly `None`, never classified. Committee membership is
read from a per-committee mark column (matched via this module's own
existing `_COMMITTEE_PATTERNS`) inside the *same* director-per-row
table: a non-empty cell under a column headed e.g. `"Audit"` means
that row's own director is disclosed as an Audit Committee member; a
literal `"Chair"`/`"Chairman"` cell additionally marks that director
as that committee's own chair. A cell empty of any mark is never read
as a disclosed "not a member" fact -- it simply produces no record.

**A real, disclosed limitation, not a silent gap**: this only
recognizes the "one row per director, with a `Name` column plus
optional labeled columns" table shape -- the common, real DEF 14A
pattern this module's own live verification found. A *transposed*
committee-membership matrix (committees as rows, directors as columns)
is a different, real shape this module does not attempt to parse --
attempting to guess an unlabeled orientation would risk exactly the
kind of invented structure this sprint forbids. A table using this
module's supported shape but a column count that shifts across rows
(uncommon; typically caused by `colspan`) can misalign a lookup by
literal cell position -- documented, not silently masked.

**Phase 9 re-verification**: Filing Content Intelligence required zero
changes (confirmed by re-reading its own module fresh) -- this module
only ever calls `find_section`/reads `FilingContent`'s own already-
existing table fields. `KnowledgeDomain`/Knowledge Coverage/Knowledge
Strategy/Knowledge Orchestration are untouched (no import from this
module anywhere in those packages) -- this module remains unwired from
`models.py`/`service.py`/the API schema, exactly as Sprint 15 left it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import replace as dataclasses_replace
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
    "CommitteeKind",
    "GovernanceFindingKind",
    "GovernanceChangeKind",
    "GovernanceObservationKind",
    "Director",
    "Committee",
    "ShareClass",
    "VotingStructure",
    "GovernancePolicy",
    "GovernanceFinding",
    "GovernanceChange",
    "GovernanceObservation",
    "BoardComposition",
    "GovernanceKnowledge",
    "extract_governance_knowledge",
]


class CommitteeKind(str, Enum):
    """A closed, disclosed vocabulary of standard board committees
    (Phase 4). `OTHER` exists for a future sprint with a reliable
    signal for a non-standard committee name -- this module never
    guesses a committee name into `OTHER` from free text, since an
    unbounded name-matching heuristic is exactly the kind of invented
    taxonomy entry Filing Content Intelligence's own Phase 3 already
    forbids for section detection."""

    AUDIT = "audit"
    COMPENSATION = "compensation"
    NOMINATING = "nominating"
    RISK = "risk"
    ESG = "esg"
    OTHER = "other"


class GovernanceFindingKind(str, Enum):
    """What a `GovernanceFinding` actually observed -- always a
    disclosure fact ("the filing's own text names X"), never a
    conclusion about the company."""

    GOVERNANCE_SECTION_DISCLOSED = "governance_section_disclosed"
    """A 10-K's own real Item 10 (`FilingSectionKind.GOVERNANCE`)."""
    EXECUTIVE_COMPENSATION_DISCLOSED = "executive_compensation_disclosed"
    """A 10-K's own real Item 11, or a DEF 14A."""
    DIRECTOR_COMPENSATION_DISCLOSED = "director_compensation_disclosed"
    PROXY_STATEMENT_DISCLOSED = "proxy_statement_disclosed"
    """The mere real existence of a DEF 14A -- the primary evidentiary
    artifact for governance, even though Filing Content Intelligence
    assigns it no internal section structure (Sprint 13's own,
    already-reviewed decision: a proxy statement has no SEC-mandated
    heading convention)."""
    BOARD_CHAIR_ROLE_DISCLOSED = "board_chair_role_disclosed"
    LEAD_INDEPENDENT_DIRECTOR_ROLE_DISCLOSED = "lead_independent_director_role_disclosed"
    COMMITTEE_DISCLOSED = "committee_disclosed"
    """The filing's own text names a standard committee -- see this
    module's own top docstring for why this stops short of membership."""
    DUAL_CLASS_STRUCTURE_DISCLOSED = "dual_class_structure_disclosed"
    CONTROLLED_COMPANY_STATUS_DISCLOSED = "controlled_company_status_disclosed"
    BOARD_TABLE_DISCLOSED = "board_table_disclosed"
    """A table whose own header row literally labels a `"Name"` column
    (Sprint 16, Phase 2/3) -- at least one director's own name was
    read from it."""
    COMMITTEE_MEMBERSHIP_TABLE_DISCLOSED = "committee_membership_table_disclosed"
    """The same table as `BOARD_TABLE_DISCLOSED` also carried at least
    one labeled per-committee mark column -- real, disclosed
    membership, not merely a committee name mention."""
    VOTING_STRUCTURE_TABLE_DISCLOSED = "voting_structure_table_disclosed"
    """A table whose own header row literally labels a `"Class"`/
    `"Share Class"` column (Sprint 16, Phase 5)."""


class GovernanceChangeKind(str, Enum):
    """Phase 6's own immutable governance history -- currently the one
    kind this module can honestly derive: a real 8-K Item 5.02."""

    DIRECTOR_OR_OFFICER_CHANGE_DISCLOSED = "director_or_officer_change_disclosed"
    """"Departure of Directors or Certain Officers; Election of
    Directors" (Item 5.02) -- the verbatim disclosed text is preserved
    as `GovernanceChange.excerpt`; this module never parses *who*
    changed out of that prose (the same "never infer a name" boundary
    as everywhere else in this module).

    **Live-verified limitation**: many real 8-K filers (confirmed
    against several real, current AAPL Item 5.02 8-Ks) present their
    own cover-page Item number inside an HTML `<table>` cell, not a
    `<p>` heading -- Filing Content Intelligence's own parser
    deliberately never collects table-cell text as paragraph prose
    (its own docstring: "table cell text is never collected as
    paragraph prose"), so `find_section` finds no `EXECUTIVE_CHANGE`
    section for these filings and this module honestly detects zero
    changes, rather than guess. This is an upstream Filing Content
    Intelligence boundary, not a bug here -- fixing it would mean
    redesigning that module's own table handling, explicitly out of
    this sprint's scope."""


class GovernanceObservationKind(str, Enum):
    """Phase 7's own reusable, comparative observations -- derived by
    comparing what a filing discloses against everything already
    disclosed by every earlier filing this call was given. Deliberately
    narrow: a flag can only ever newly turn `True` here (a real,
    monotonic disclosure event) -- a flag's *absence* in a later filing
    is never read as "this was reversed" (silence is not a disclosed
    fact), so "board reduced"/"committee removed"-style observations
    from Phase 7's own example list are not implemented; they would
    require inferring meaning from the absence of a mention, which this
    module's own guiding principle forbids."""

    NEW_COMMITTEE_DISCLOSED = "new_committee_disclosed"
    """Live-verified against real AAPL filings: a 10-K's own Item 10
    frequently only names the Audit Committee by name (deferring the
    rest to the proxy "by reference"), so a Compensation/Nominating
    committee genuinely first *matched in the text this call was given*
    at the DEF 14A. This observation's own claim is exactly that
    narrow -- "newly disclosed by the text this call examined" -- never
    "newly formed by the company," which this module has no way to
    know and does not claim."""
    VOTING_STRUCTURE_DISCLOSURE_CHANGED = "voting_structure_disclosure_changed"

    #: -- Sprint 16: table-sourced, membership-level observations --
    #: unlike the two above (mere name/keyword mentions), these compare
    #: real, disclosed roster data read from labeled table columns --
    #: still gated the identical way: never fired for the first filing
    #: examined (nothing to compare against), and a "removed"/"changed"
    #: claim only ever fires when the *later* filing itself produced
    #: real table-sourced roster data to compare -- silence in a later
    #: filing (no matching table at all) is never read as evidence of
    #: anything, matching the same "silence is not a disclosed fact"
    #: principle the two observations above already established.
    COMMITTEE_CREATED = "committee_created"
    """A committee's own table-sourced member roster appears for the
    first time, relative to every earlier filing's own table-sourced
    data this call examined. Narrower and stronger evidence than
    `NEW_COMMITTEE_DISCLOSED` (a name mention) -- this reflects a real,
    disclosed member list, not just a phrase match. Still a disclosure
    claim, not an organizational one: a company that already had this
    committee, but never tabulated its roster until now, is
    indistinguishable here from a genuinely new committee -- this
    module has no way to tell the two apart and does not claim to."""
    COMMITTEE_REMOVED = "committee_removed"
    """A committee kind with a real, table-sourced roster in an earlier
    filing has no entry in the *latest* filing's own table-sourced
    data, even though that latest filing *did* produce real
    committee-table evidence for other committees. Read narrowly: this
    filing's own table no longer discloses that roster -- never a
    claim the committee was dissolved, which this module cannot know."""
    COMMITTEE_MEMBERSHIP_CHANGED = "committee_membership_changed"
    """A committee kind's own table-sourced member set differs between
    two filings that both disclosed a real roster for it -- see
    `GovernanceObservation.added_names`/`.removed_names` for exactly
    which real, disclosed names differed."""
    BOARD_COMPOSITION_CHANGED = "board_composition_changed"
    """The table-sourced set of director names differs between two
    filings that both produced a real board table. The mirror of
    `COMMITTEE_MEMBERSHIP_CHANGED` at the whole-board level."""


@dataclass(frozen=True)
class Director:
    """Phase 3's full disclosed shape. Populated (Sprint 16) only from
    a table whose own header row literally labels a `"Name"` column --
    see this module's own top docstring for exactly what is and is not
    read, and why that is preservation, not inference."""

    name: str
    is_chair: bool
    is_lead_independent_director: bool
    disclosed_independence: bool | None
    """`None` unless a column literally headed `"Independent"`/
    `"Independence"` carries an exact `"yes"`/`"no"` cell value for
    this director's own row -- any other value is honestly `None`,
    never classified."""
    committee_assignments: tuple[CommitteeKind, ...]
    appointment_status: str | None
    """Verbatim, e.g. `"nominee"` -- only when a column literally
    headed `"Status"` carries text for this director's own row, never
    classified by this module."""
    tenure_years: int | None
    """Only when a column literally headed `"Tenure"` carries a plain
    integer for this director's own row -- never computed from a
    `"Director Since"`-style year, which would be a derivation this
    module does not perform."""
    table_order_index: int
    """The `FilingTable.order_index` this director's own row came from."""
    row_index: int
    """This director's own row index within that table's body rows."""
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str


@dataclass(frozen=True)
class Committee:
    kind: CommitteeKind
    disclosed_name: str
    """The literal text this committee's name was matched from --
    either a paragraph mention or a table's own per-committee column
    header, whichever was found first."""
    members: tuple[Director, ...]
    """Populated (Sprint 16) from a director-per-row table's own
    per-committee mark column -- a non-empty cell under a column
    matching this committee's own name pattern. Always `()` when no
    such table was found."""
    chair: Director | None
    """The one member, if any, whose own mark cell under this
    committee's column read exactly `"Chair"`/`"Chairman"`/
    `"Chairperson"` -- `None` when no member's mark said so, even if
    `members` is non-empty."""
    responsibilities: tuple[str, ...]
    """Always `()` today -- no reliable, disclosed, non-inferential
    signal distinguishes a committee's own charter/responsibilities
    text from ordinary surrounding prose, and this module's own Phase 4
    table support reads director-per-row tables, not a standalone
    per-committee description table."""
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str


@dataclass(frozen=True)
class ShareClass:
    """Populated (Sprint 16) from a table whose own header row
    literally labels a `"Class"`/`"Share Class"` column."""

    name: str
    votes_per_share: str
    """Verbatim disclosed text from a column literally headed `"Votes
    Per Share"`/`"Voting Rights"`/`"Votes"` (e.g. `"10 votes per
    share"`) -- never a parsed number, since a malformed or unusual
    disclosure could be silently misread as a different real value.
    Empty string when this table has no such column."""
    table_order_index: int
    row_index: int
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str


@dataclass(frozen=True)
class VotingStructure:
    dual_class_disclosed: bool
    controlled_company_disclosed: bool
    share_classes: tuple[ShareClass, ...]
    """Populated (Sprint 16) -- see `ShareClass`'s own docstring."""


@dataclass(frozen=True)
class GovernancePolicy:
    """Framework only -- always `()` on `GovernanceKnowledge.policies`
    today. No reliable, disclosed, non-inferential signal in the
    current pipeline distinguishes a real named policy (e.g. a clawback
    or insider-trading policy) from ordinary governance prose without
    the same table/structured-list access this module lacks elsewhere.
    Defined so a future sprint can populate it without a shape change."""

    kind: str
    description: str
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str


@dataclass(frozen=True)
class GovernanceFinding:
    """The bottom of Phase 2's own hierarchy -- one real, disclosed
    observation, always traceable to the exact filing, section,
    subsection, and paragraph it came from (Phase 10)."""

    kind: GovernanceFindingKind
    excerpt: str | None
    """Verbatim disclosed text this finding was matched from -- `None`
    only for `PROXY_STATEMENT_DISCLOSED`, which reflects the filing's
    own existence, not one paragraph."""
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    section_kind: FilingSectionKind | None
    section_item_number: str | None
    subsection_heading: str | None
    paragraph_order_index: int | None
    table_order_index: int | None = None
    """Set instead of `paragraph_order_index` for a table-sourced
    finding (Sprint 16) -- the two are mutually exclusive, never both
    set on the same finding."""


@dataclass(frozen=True)
class GovernanceChange:
    kind: GovernanceChangeKind
    excerpt: str
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    section_item_number: str | None
    paragraph_order_index: int


@dataclass(frozen=True)
class GovernanceObservation:
    kind: GovernanceObservationKind
    committee_kind: CommitteeKind | None
    """Set for every kind except `BOARD_COMPOSITION_CHANGED` and
    `VOTING_STRUCTURE_DISCLOSURE_CHANGED`, which are whole-board/
    whole-filing facts, not committee-specific."""
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    """The filing whose own content first disclosed the change."""
    added_names: tuple[str, ...] = ()
    """Real, disclosed names present in this filing's own table-sourced
    roster that were absent from the immediately preceding comparison
    baseline -- a mechanical set difference over disclosed data, never
    an inference about why. Set only for `COMMITTEE_CREATED`/
    `COMMITTEE_MEMBERSHIP_CHANGED`/`BOARD_COMPOSITION_CHANGED`."""
    removed_names: tuple[str, ...] = ()
    """The mirror of `added_names` -- present in the baseline, absent
    from this filing's own table-sourced roster. Reflects a change in
    what this filing's own table discloses, never a claim that a
    person left a board or committee in reality. Set only for
    `COMMITTEE_REMOVED`/`COMMITTEE_MEMBERSHIP_CHANGED`/
    `BOARD_COMPOSITION_CHANGED`."""


@dataclass(frozen=True)
class BoardComposition:
    chair_disclosed: bool
    lead_independent_director_disclosed: bool
    directors: tuple[Director, ...]
    """Populated (Sprint 16) from every table-sourced board table this
    call found -- `()` when no table in the supplied filings had a
    column literally headed `"Name"`."""
    findings: tuple[GovernanceFinding, ...]
    """Every `BOARD_CHAIR_ROLE_DISCLOSED`/`LEAD_INDEPENDENT_DIRECTOR_
    ROLE_DISCLOSED` finding that set the two flags above."""


@dataclass(frozen=True)
class GovernanceKnowledge:
    board_composition: BoardComposition
    committees: tuple[Committee, ...]
    voting_structure: VotingStructure
    policies: tuple[GovernancePolicy, ...]
    changes: tuple[GovernanceChange, ...]
    """Phase 6's own immutable history, chronologically ordered."""
    observations: tuple[GovernanceObservation, ...]
    """Phase 7's own reusable, comparative observations, chronologically ordered."""
    findings: tuple[GovernanceFinding, ...]
    """Every disclosure this call detected, across every filing supplied."""
    filings_considered: tuple[str, ...]
    """Accession numbers of every filing actually used, chronological
    -- `extraction_status in (EXTRACTED, STRUCTURE_UNKNOWN)` only; a
    `FETCH_FAILED`/`NOT_ATTEMPTED` filing contributes nothing, silently,
    the same way Filing Content Intelligence itself never raises on one."""


_CHAIR_RE = re.compile(r"\b(chairman of the board|chair of the board|non-executive chairman|board chair)\b", re.IGNORECASE)
_LEAD_INDEPENDENT_RE = re.compile(r"\blead independent director\b", re.IGNORECASE)
_DUAL_CLASS_RE = re.compile(r"\bdual[- ]class\b", re.IGNORECASE)
_CONTROLLED_COMPANY_RE = re.compile(r"\bcontrolled company\b", re.IGNORECASE)

#: A closed, disclosed set of standard committee name phrases -- the
#: same "match a real, bounded, literal phrase, never an open-ended
#: heuristic" discipline `_ITEM_HEADING_RE` already applies at the
#: section level.
_COMMITTEE_PATTERNS: tuple[tuple[re.Pattern[str], CommitteeKind], ...] = (
    (re.compile(r"\baudit committee\b", re.IGNORECASE), CommitteeKind.AUDIT),
    (re.compile(r"\bcompensation committee\b", re.IGNORECASE), CommitteeKind.COMPENSATION),
    (
        re.compile(r"\b(nominating and corporate governance committee|nominating committee|corporate governance committee)\b", re.IGNORECASE),
        CommitteeKind.NOMINATING,
    ),
    (re.compile(r"\brisk committee\b", re.IGNORECASE), CommitteeKind.RISK),
    (
        re.compile(r"\b(esg committee|sustainability committee|corporate responsibility committee)\b", re.IGNORECASE),
        CommitteeKind.ESG,
    ),
)

_USABLE_STATUSES = frozenset({ExtractionStatus.EXTRACTED, ExtractionStatus.STRUCTURE_UNKNOWN})


def _iter_paragraphs_with_context(
    content: FilingContent,
) -> "list[tuple[FilingParagraph, FilingSection | None, FilingSubsection | None]]":
    result: list[tuple[FilingParagraph, FilingSection | None, FilingSubsection | None]] = []
    for section in content.sections:
        for paragraph in section.paragraphs:
            result.append((paragraph, section, None))
        for subsection in section.subsections:
            for paragraph in subsection.paragraphs:
                result.append((paragraph, section, subsection))
    for paragraph in content.unattributed_paragraphs:
        result.append((paragraph, None, None))
    return result


def _iter_tables_with_context(
    content: FilingContent,
) -> "list[tuple[FilingTable, FilingSection | None, FilingSubsection | None]]":
    result: list[tuple[FilingTable, FilingSection | None, FilingSubsection | None]] = []
    for section in content.sections:
        for table in section.tables:
            result.append((table, section, None))
        for subsection in section.subsections:
            for table in subsection.tables:
                result.append((table, section, subsection))
    for table in content.unattributed_tables:
        result.append((table, None, None))
    return result


def _finding(
    kind: GovernanceFindingKind, excerpt: str | None, content: FilingContent,
    section: FilingSection | None = None, subsection: FilingSubsection | None = None,
    paragraph_order_index: int | None = None, table_order_index: int | None = None,
) -> GovernanceFinding:
    return GovernanceFinding(
        kind=kind, excerpt=excerpt, accession_number=content.accession_number, form_type=content.form_type,
        filed_at=content.filed_at, source_reference=content.source_reference,
        section_kind=section.kind if section is not None else None,
        section_item_number=section.item_number if section is not None else None,
        subsection_heading=subsection.heading_text if subsection is not None else None,
        paragraph_order_index=paragraph_order_index, table_order_index=table_order_index,
    )


# -- Sprint 16, Phase 2/3/4/5: table consumption -----------------------------

#: Real, disclosed column-header labels this module recognizes -- an
#: exact match (case-insensitive, stripped) against a header cell's own
#: text, never a substring/keyword guess. A header this module does not
#: recognize simply contributes nothing; it is never a parse error.
_NAME_HEADER_LABELS = frozenset({"name", "director", "nominee", "director nominee"})
_INDEPENDENT_HEADER_LABELS = frozenset({"independent", "independence"})
_POSITION_HEADER_LABELS = frozenset({"position", "role", "title"})
_STATUS_HEADER_LABELS = frozenset({"status"})
_TENURE_HEADER_LABELS = frozenset({"tenure"})
_CLASS_HEADER_LABELS = frozenset({"class", "share class", "title of class"})
_VOTES_HEADER_LABELS = frozenset({"votes per share", "voting rights", "votes"})
_CHAIR_CELL_RE = re.compile(r"^(chair|chairman|chairperson)$", re.IGNORECASE)

#: A director-per-row table's own per-committee mark column is
#: routinely headed by a short abbreviation ("Audit," "Comp.") rather
#: than the full "Audit Committee" phrase `_COMMITTEE_PATTERNS` (used
#: for body prose, where a bare word risks a false match in ordinary
#: sentences) requires -- live-verified against real DEF 14A director
#: tables. Also live-verified: real header text varies in ways an
#: exact-label match cannot anticipate -- Apple's own real, current
#: proxy statement headers this exact column "People and
#: Compensation Committee," not "Compensation Committee." A bounded,
#: word-boundary substring match against the header cell's own full
#: text (the same real anchor word every genuine committee name of
#: that kind always contains) is used instead -- still a real,
#: disclosed word, matched the identical way `_COMMITTEE_PATTERNS`
#: already matches body prose, just without requiring the literal word
#: "committee" to immediately follow (a header column is not a
#: sentence). A header cell containing none of these words
#: contributes nothing -- never a guess.
_COMMITTEE_HEADER_PATTERNS: tuple[tuple[re.Pattern[str], CommitteeKind], ...] = (
    (re.compile(r"\baudit\b", re.IGNORECASE), CommitteeKind.AUDIT),
    (re.compile(r"\bcompensation\b", re.IGNORECASE), CommitteeKind.COMPENSATION),
    (re.compile(r"\bnominat", re.IGNORECASE), CommitteeKind.NOMINATING),
    (re.compile(r"\brisk\b", re.IGNORECASE), CommitteeKind.RISK),
    (re.compile(r"\b(esg|sustainability)\b", re.IGNORECASE), CommitteeKind.ESG),
)


def _header_row(table: FilingTable) -> TableRow | None:
    if table.header is None or not table.header.rows:
        return None
    return table.header.rows[0]


_ALL_RECOGNIZED_HEADER_LABELS = _NAME_HEADER_LABELS | _CLASS_HEADER_LABELS


def _resolve_header_and_body(table: FilingTable) -> tuple[TableRow | None, tuple[TableRow, ...]]:
    """`table.header` first -- a real, disclosed `<thead>` or all-`<th>`
    row, exactly as Filing Content Intelligence (unmodified) classifies
    it. Live-verified against real AAPL DEF 14A tables: many real
    filers style a header-looking row with bold `<td>` cells instead of
    real `<th>` tags, so Filing Content Intelligence's own correct,
    unmodified HTML-tag-based split does not classify it as a header --
    it is not one by the HTML spec. This module still recognizes it
    structurally, entirely within its own scope: if a table has no
    `<thead>`/`<th>` header at all, but its own first body row's cells
    literally match a label this module recognizes (e.g. `"Name"`),
    that row is treated as this table's header for lookup purposes --
    still reading the filing's own disclosed text, from wherever Filing
    Content Intelligence's own unmodified split actually put it, never
    inferring a header where none of its cells say so."""
    header = _header_row(table)
    if header is not None:
        return header, table.rows
    if not table.rows:
        return None, ()
    candidate = table.rows[0]
    if any(cell.text.strip().lower() in _ALL_RECOGNIZED_HEADER_LABELS for cell in candidate.cells):
        return candidate, table.rows[1:]
    return None, table.rows


def _header_column_index(header: TableRow, labels: frozenset[str]) -> int | None:
    for cell in header.cells:
        if cell.text.strip().lower() in labels:
            return cell.order_index
    return None


def _cell_text(row: TableRow, column_index: int | None) -> str | None:
    """`None` when there is no such column, or this particular row has
    no cell at that literal position (e.g. a short row) -- distinct
    from an empty string, which means the column exists and the cell
    is genuinely empty."""
    if column_index is None or column_index >= len(row.cells):
        return None
    return row.cells[column_index].text.strip()


def _extract_board_and_committees(
    table: FilingTable,
) -> tuple[
    tuple[Director, ...], dict[CommitteeKind, list[Director]], dict[CommitteeKind, Director], dict[CommitteeKind, str],
]:
    """One pass over a single director-per-row table: every row with a
    non-empty `"Name"` cell becomes a `Director`; a non-empty cell under
    a recognized per-committee column additionally records that
    director as a member (and, if the cell literally reads `"Chair"`/
    `"Chairman"`/`"Chairperson"`, as that committee's own chair) of the
    matching `CommitteeKind`. Returns `((), {}, {}, {})` when the table
    has no header row or no `"Name"` column at all -- never a guess."""
    header, body_rows = _resolve_header_and_body(table)
    if header is None:
        return (), {}, {}, {}
    name_index = _header_column_index(header, _NAME_HEADER_LABELS)
    if name_index is None:
        return (), {}, {}, {}

    independent_index = _header_column_index(header, _INDEPENDENT_HEADER_LABELS)
    position_index = _header_column_index(header, _POSITION_HEADER_LABELS)
    status_index = _header_column_index(header, _STATUS_HEADER_LABELS)
    tenure_index = _header_column_index(header, _TENURE_HEADER_LABELS)
    committee_columns: list[tuple[CommitteeKind, int]] = []
    committee_header_text: dict[CommitteeKind, str] = {}
    for pattern, kind in _COMMITTEE_HEADER_PATTERNS:
        idx = next((cell.order_index for cell in header.cells if pattern.search(cell.text)), None)
        if idx is not None:
            committee_columns.append((kind, idx))
            committee_header_text[kind] = header.cells[idx].text

    directors: list[Director] = []
    members_by_kind: dict[CommitteeKind, list[Director]] = {}
    chair_by_kind: dict[CommitteeKind, Director] = {}

    for row in body_rows:
        raw_name = _cell_text(row, name_index)
        if not raw_name:
            continue

        #: Live-verified against real AAPL DEF 14A tables: a filer
        #: routinely puts a role label in the *same* cell as the name,
        #: separated only by a `<br>` (e.g. "Art Levinson" / "Board
        #: Chair"), which this module's own cell text -- correctly,
        #: since Filing Content Intelligence treats a `<br>` inside a
        #: cell as whitespace, not a hard boundary -- receives as one
        #: joined string. Rather than guess where a name "probably"
        #: ends, this only ever removes a specific, already-trusted,
        #: bounded phrase this module already treats as a real role
        #: disclosure everywhere else (`_CHAIR_RE`/`_LEAD_INDEPENDENT_
        #: RE`) -- never an open-ended split. A real, disclosed
        #: limitation this relies on: real filing HTML source text
        #: around a `<br>` (confirmed against AAPL's own real markup)
        #: carries natural whitespace, which is what gives `_CHAIR_RE`'s
        #: own `\b` word boundary somewhere to match; a hypothetical
        #: filer whose markup joins the two with no whitespace at all
        #: would not be split here -- this module still never guesses.
        name = raw_name
        is_chair = False
        is_lead_independent = False
        chair_match = _CHAIR_RE.search(name)
        if chair_match:
            is_chair = True
            name = (name[: chair_match.start()] + name[chair_match.end() :]).strip(" ,.–—")
        lead_match = _LEAD_INDEPENDENT_RE.search(name)
        if lead_match:
            is_lead_independent = True
            name = (name[: lead_match.start()] + name[lead_match.end() :]).strip(" ,.–—")
        if not name:
            #: The whole cell *was* the role phrase, with no name text
            #: at all -- honestly not a director row (e.g. a legend
            #: entry), never fabricated back into one.
            continue

        disclosed_independence: bool | None = None
        independence_text = _cell_text(row, independent_index)
        if independence_text is not None:
            normalized = independence_text.lower()
            if normalized == "yes":
                disclosed_independence = True
            elif normalized == "no":
                disclosed_independence = False

        position_text = _cell_text(row, position_index) or ""
        if _CHAIR_RE.search(position_text):
            is_chair = True
        if _LEAD_INDEPENDENT_RE.search(position_text):
            is_lead_independent = True

        appointment_status = _cell_text(row, status_index) or None

        tenure_years: int | None = None
        tenure_text = _cell_text(row, tenure_index)
        if tenure_text is not None and tenure_text.isdigit():
            tenure_years = int(tenure_text)

        assignments: list[CommitteeKind] = []
        row_chair_of: list[CommitteeKind] = []
        for kind, idx in committee_columns:
            mark = _cell_text(row, idx)
            if not mark:
                continue
            assignments.append(kind)
            if _CHAIR_CELL_RE.match(mark):
                row_chair_of.append(kind)

        director = Director(
            name=name, is_chair=is_chair, is_lead_independent_director=is_lead_independent,
            disclosed_independence=disclosed_independence, committee_assignments=tuple(assignments),
            appointment_status=appointment_status, tenure_years=tenure_years, table_order_index=table.order_index,
            row_index=row.order_index, accession_number=table.accession_number, form_type=table.form_type,
            filed_at=table.filed_at, source_reference=table.source_reference,
        )
        directors.append(director)
        for kind in assignments:
            members_by_kind.setdefault(kind, []).append(director)
        for kind in row_chair_of:
            chair_by_kind[kind] = director

    return tuple(directors), members_by_kind, chair_by_kind, committee_header_text


def _extract_share_classes(table: FilingTable) -> tuple[ShareClass, ...]:
    header, body_rows = _resolve_header_and_body(table)
    if header is None:
        return ()
    class_index = _header_column_index(header, _CLASS_HEADER_LABELS)
    if class_index is None:
        return ()
    votes_index = _header_column_index(header, _VOTES_HEADER_LABELS)

    share_classes: list[ShareClass] = []
    for row in body_rows:
        name = _cell_text(row, class_index)
        if not name:
            continue
        votes_per_share = _cell_text(row, votes_index) or ""
        share_classes.append(
            ShareClass(
                name=name, votes_per_share=votes_per_share, table_order_index=table.order_index,
                row_index=row.order_index, accession_number=table.accession_number, form_type=table.form_type,
                filed_at=table.filed_at, source_reference=table.source_reference,
            )
        )
    return tuple(share_classes)


def extract_governance_knowledge(filing_contents: tuple[FilingContent, ...]) -> GovernanceKnowledge:
    """Built entirely upon Filing Content Intelligence's own output --
    never fetches, parses HTML, or reads a `RegulatoryFiling` directly.
    Filings are processed chronologically (`filed_at`, oldest first) so
    Phase 7's own observations can honestly say "newly disclosed
    relative to every earlier filing already examined."""
    usable = tuple(sorted((c for c in filing_contents if c.extraction_status in _USABLE_STATUSES), key=lambda c: c.filed_at))

    findings: list[GovernanceFinding] = []
    changes: list[GovernanceChange] = []
    observations: list[GovernanceObservation] = []
    committees_by_kind: dict[CommitteeKind, Committee] = {}
    committee_table_members_by_kind: dict[CommitteeKind, list[Director]] = {}
    committee_table_chair_by_kind: dict[CommitteeKind, Director] = {}
    all_directors: list[Director] = []
    all_share_classes: list[ShareClass] = []
    board_findings: list[GovernanceFinding] = []
    voting_findings: list[GovernanceFinding] = []
    chair_disclosed = False
    lead_independent_director_disclosed = False
    dual_class_disclosed = False
    controlled_company_disclosed = False
    seen_committee_kinds: set[CommitteeKind] = set()
    #: Table-sourced-only comparison baselines (Phase 7's new,
    #: membership-level observations) -- deliberately separate from
    #: `seen_committee_kinds`/`dual_class_disclosed` above (which
    #: those two paragraph-keyword observations already use), since a
    #: mere name mention and a real, disclosed roster are different
    #: strengths of evidence and must never be conflated in a diff.
    seen_table_board_names: frozenset[str] = frozenset()
    has_board_table_baseline = False
    seen_table_committee_members: dict[CommitteeKind, frozenset[str]] = {}
    has_prior_filing = False

    for content in usable:
        this_filing_committee_kinds: set[CommitteeKind] = set()
        this_filing_dual_class = False
        this_filing_controlled_company = False
        this_filing_board_names: set[str] = set()
        this_filing_table_committee_names: dict[CommitteeKind, set[str]] = {}

        for paragraph, section, subsection in _iter_paragraphs_with_context(content):
            text = paragraph.text

            for pattern, committee_kind in _COMMITTEE_PATTERNS:
                match = pattern.search(text)
                if match is None:
                    continue
                this_filing_committee_kinds.add(committee_kind)
                if committee_kind not in committees_by_kind:
                    committees_by_kind[committee_kind] = Committee(
                        kind=committee_kind, disclosed_name=match.group(0), members=(), chair=None,
                        responsibilities=(), accession_number=content.accession_number, form_type=content.form_type,
                        filed_at=content.filed_at, source_reference=content.source_reference,
                    )
                findings.append(
                    _finding(GovernanceFindingKind.COMMITTEE_DISCLOSED, text, content, section, subsection, paragraph.order_index)
                )

            if _CHAIR_RE.search(text):
                chair_disclosed = True
                board_findings.append(
                    _finding(
                        GovernanceFindingKind.BOARD_CHAIR_ROLE_DISCLOSED, text, content, section, subsection,
                        paragraph.order_index,
                    )
                )
            if _LEAD_INDEPENDENT_RE.search(text):
                lead_independent_director_disclosed = True
                board_findings.append(
                    _finding(
                        GovernanceFindingKind.LEAD_INDEPENDENT_DIRECTOR_ROLE_DISCLOSED, text, content, section,
                        subsection, paragraph.order_index,
                    )
                )
            if _DUAL_CLASS_RE.search(text):
                this_filing_dual_class = True
                voting_findings.append(
                    _finding(
                        GovernanceFindingKind.DUAL_CLASS_STRUCTURE_DISCLOSED, text, content, section, subsection,
                        paragraph.order_index,
                    )
                )
            if _CONTROLLED_COMPANY_RE.search(text):
                this_filing_controlled_company = True
                voting_findings.append(
                    _finding(
                        GovernanceFindingKind.CONTROLLED_COMPANY_STATUS_DISCLOSED, text, content, section, subsection,
                        paragraph.order_index,
                    )
                )

        for table, section, subsection in _iter_tables_with_context(content):
            directors, members_by_kind, chair_by_kind, header_text_by_kind = _extract_board_and_committees(table)
            if directors:
                all_directors.extend(directors)
                this_filing_board_names.update(d.name for d in directors)
                findings.append(
                    _finding(
                        GovernanceFindingKind.BOARD_TABLE_DISCLOSED, None, content, section, subsection,
                        table_order_index=table.order_index,
                    )
                )
                for director in directors:
                    if director.is_chair:
                        chair_disclosed = True
                        board_findings.append(
                            _finding(
                                GovernanceFindingKind.BOARD_CHAIR_ROLE_DISCLOSED, director.name, content, section,
                                subsection, table_order_index=table.order_index,
                            )
                        )
                    if director.is_lead_independent_director:
                        lead_independent_director_disclosed = True
                        board_findings.append(
                            _finding(
                                GovernanceFindingKind.LEAD_INDEPENDENT_DIRECTOR_ROLE_DISCLOSED, director.name,
                                content, section, subsection, table_order_index=table.order_index,
                            )
                        )
                if members_by_kind:
                    findings.append(
                        _finding(
                            GovernanceFindingKind.COMMITTEE_MEMBERSHIP_TABLE_DISCLOSED, None, content, section,
                            subsection, table_order_index=table.order_index,
                        )
                    )
                for kind, members in members_by_kind.items():
                    committee_table_members_by_kind.setdefault(kind, []).extend(members)
                    this_filing_table_committee_names.setdefault(kind, set()).update(m.name for m in members)
                    this_filing_committee_kinds.add(kind)
                    if kind not in committees_by_kind:
                        committees_by_kind[kind] = Committee(
                            kind=kind, disclosed_name=header_text_by_kind[kind], members=(), chair=None,
                            responsibilities=(), accession_number=content.accession_number,
                            form_type=content.form_type, filed_at=content.filed_at,
                            source_reference=content.source_reference,
                        )
                for kind, chair in chair_by_kind.items():
                    committee_table_chair_by_kind[kind] = chair

            share_classes = _extract_share_classes(table)
            if share_classes:
                all_share_classes.extend(share_classes)
                findings.append(
                    _finding(
                        GovernanceFindingKind.VOTING_STRUCTURE_TABLE_DISCLOSED, None, content, section, subsection,
                        table_order_index=table.order_index,
                    )
                )

        governance_section = find_section(content, FilingSectionKind.GOVERNANCE)
        if governance_section is not None:
            findings.append(_finding(GovernanceFindingKind.GOVERNANCE_SECTION_DISCLOSED, None, content, governance_section))

        exec_comp_section = find_section(content, FilingSectionKind.EXECUTIVE_COMPENSATION)
        if exec_comp_section is not None:
            findings.append(
                _finding(GovernanceFindingKind.EXECUTIVE_COMPENSATION_DISCLOSED, None, content, exec_comp_section)
            )

        director_comp_section = find_section(content, FilingSectionKind.DIRECTOR_COMPENSATION)
        if director_comp_section is not None:
            findings.append(
                _finding(GovernanceFindingKind.DIRECTOR_COMPENSATION_DISCLOSED, None, content, director_comp_section)
            )

        if content.form_type == "DEF 14A":
            #: The proxy statement's own real existence is the finding
            #: -- not a claim about what it contains beyond what the
            #: keyword-matching above already found in its own
            #: (unattributed, since Filing Content Intelligence assigns
            #: DEF 14A no section structure) paragraph text.
            findings.append(_finding(GovernanceFindingKind.PROXY_STATEMENT_DISCLOSED, None, content))

        if content.form_type == "8-K":
            change_section = find_section(content, FilingSectionKind.EXECUTIVE_CHANGE)
            if change_section is not None:
                for paragraph in change_section.paragraphs:
                    changes.append(
                        GovernanceChange(
                            kind=GovernanceChangeKind.DIRECTOR_OR_OFFICER_CHANGE_DISCLOSED, excerpt=paragraph.text,
                            accession_number=content.accession_number, form_type=content.form_type,
                            filed_at=content.filed_at, source_reference=content.source_reference,
                            section_item_number=change_section.item_number, paragraph_order_index=paragraph.order_index,
                        )
                    )

        if has_prior_filing:
            for committee_kind in sorted(this_filing_committee_kinds - seen_committee_kinds, key=lambda k: k.value):
                observations.append(
                    GovernanceObservation(
                        kind=GovernanceObservationKind.NEW_COMMITTEE_DISCLOSED, committee_kind=committee_kind,
                        accession_number=content.accession_number, form_type=content.form_type,
                        filed_at=content.filed_at, source_reference=content.source_reference,
                    )
                )
            newly_dual_class = this_filing_dual_class and not dual_class_disclosed
            newly_controlled_company = this_filing_controlled_company and not controlled_company_disclosed
            if newly_dual_class or newly_controlled_company:
                observations.append(
                    GovernanceObservation(
                        kind=GovernanceObservationKind.VOTING_STRUCTURE_DISCLOSURE_CHANGED, committee_kind=None,
                        accession_number=content.accession_number, form_type=content.form_type,
                        filed_at=content.filed_at, source_reference=content.source_reference,
                    )
                )

            #: Table-sourced, membership-level observations -- gated
            #: the same way, plus each one individually gated on the
            #: *comparison itself* being meaningful (see each kind's
            #: own docstring on `GovernanceObservationKind`).
            for kind, names in this_filing_table_committee_names.items():
                names_frozen = frozenset(names)
                previous = seen_table_committee_members.get(kind)
                if previous is None:
                    observations.append(
                        GovernanceObservation(
                            kind=GovernanceObservationKind.COMMITTEE_CREATED, committee_kind=kind,
                            accession_number=content.accession_number, form_type=content.form_type,
                            filed_at=content.filed_at, source_reference=content.source_reference,
                            added_names=tuple(sorted(names_frozen)),
                        )
                    )
                elif previous != names_frozen:
                    observations.append(
                        GovernanceObservation(
                            kind=GovernanceObservationKind.COMMITTEE_MEMBERSHIP_CHANGED, committee_kind=kind,
                            accession_number=content.accession_number, form_type=content.form_type,
                            filed_at=content.filed_at, source_reference=content.source_reference,
                            added_names=tuple(sorted(names_frozen - previous)),
                            removed_names=tuple(sorted(previous - names_frozen)),
                        )
                    )
            if this_filing_table_committee_names:
                missing_kinds = set(seen_table_committee_members) - set(this_filing_table_committee_names)
                for kind in sorted(missing_kinds, key=lambda k: k.value):
                    observations.append(
                        GovernanceObservation(
                            kind=GovernanceObservationKind.COMMITTEE_REMOVED, committee_kind=kind,
                            accession_number=content.accession_number, form_type=content.form_type,
                            filed_at=content.filed_at, source_reference=content.source_reference,
                            removed_names=tuple(sorted(seen_table_committee_members[kind])),
                        )
                    )

            if this_filing_board_names and has_board_table_baseline:
                board_added = this_filing_board_names - seen_table_board_names
                board_removed = seen_table_board_names - this_filing_board_names
                if board_added or board_removed:
                    observations.append(
                        GovernanceObservation(
                            kind=GovernanceObservationKind.BOARD_COMPOSITION_CHANGED, committee_kind=None,
                            accession_number=content.accession_number, form_type=content.form_type,
                            filed_at=content.filed_at, source_reference=content.source_reference,
                            added_names=tuple(sorted(board_added)), removed_names=tuple(sorted(board_removed)),
                        )
                    )

        seen_committee_kinds |= this_filing_committee_kinds
        dual_class_disclosed = dual_class_disclosed or this_filing_dual_class
        controlled_company_disclosed = controlled_company_disclosed or this_filing_controlled_company
        for kind, names in this_filing_table_committee_names.items():
            seen_table_committee_members[kind] = frozenset(names)
        if this_filing_board_names:
            seen_table_board_names = frozenset(this_filing_board_names)
            has_board_table_baseline = True
        has_prior_filing = True

    findings.extend(board_findings)
    findings.extend(voting_findings)

    final_committees = tuple(
        dataclasses_replace(
            committees_by_kind[kind], members=tuple(committee_table_members_by_kind.get(kind, ())),
            chair=committee_table_chair_by_kind.get(kind),
        )
        for kind in sorted(committees_by_kind, key=lambda k: k.value)
    )

    return GovernanceKnowledge(
        board_composition=BoardComposition(
            chair_disclosed=chair_disclosed, lead_independent_director_disclosed=lead_independent_director_disclosed,
            directors=tuple(all_directors), findings=tuple(board_findings),
        ),
        committees=final_committees,
        voting_structure=VotingStructure(
            dual_class_disclosed=dual_class_disclosed, controlled_company_disclosed=controlled_company_disclosed,
            share_classes=tuple(all_share_classes),
        ),
        policies=(),
        changes=tuple(changes),
        observations=tuple(observations),
        findings=tuple(findings),
        filings_considered=tuple(c.accession_number for c in usable),
    )
