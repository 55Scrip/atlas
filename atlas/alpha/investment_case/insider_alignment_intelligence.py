"""Insider Alignment Intelligence (Capability Expansion Sprint 21).

**Mission.** Atlas already knows executive identity (`executive_change_
intelligence.py`), executive compensation (`executive_compensation_
intelligence.py`), incentive structure (`incentive_intelligence.py`'s
own types, populated via Sprint 20's bridge functions), and ownership
(`ownership_intelligence.py`) -- each as an independent capability that
has never been connected to any other. This module is the connection:
for each real `ExecutiveIdentity`, what does Atlas actually know about
that specific person's own disclosed ownership and equity compensation?
Never a score, never a judgment about whether the answer is good --
"alignment is evidence, not judgment" (this sprint's own Product
Philosophy).

**Phase 1 audit findings, re-read fresh (not assumed from any prior
sprint's own report).**

*Ownership Intelligence never imports Executive Identity.*
`ownership_intelligence.py`'s only import is `filing_content_
intelligence`; `OwnershipDisclosure.owner_name` is a real, verbatim,
table-sourced string for a table-sourced disclosure, `None` for a
paragraph-sourced one -- there is no existing link from an ownership
disclosure to an `ExecutiveIdentity` anywhere in this codebase. This
module builds that link, and builds it the only way Phase 3 permits:
exact, case-insensitive name equality. No fuzzy matching, no role veto,
no matching a disclosure that has no name at all (a paragraph-sourced
disclosure can never be linked to a specific executive -- extracting a
person's name out of free prose would be exactly the "never infer
identity" this module is required to honor).

*`incentive_intelligence.extract_incentive_intelligence` is not the real
compensation-linked evidence source.* Re-read fresh: that function's own
`executive_incentive_programs`/`incentive_structures` outputs are still
always `()` in this build -- see that module's own docstring, unchanged
since Sprint 12. The real, non-empty bridge is Sprint 20's own
`executive_compensation_intelligence.build_incentive_knowledge`/
`build_incentive_structures`, which construct real `incentive_
intelligence.ExecutiveIncentiveProgram`/`IncentiveStructure` instances
from real, disclosed `ExecutiveCompensationKnowledge` evidence. This
module calls those two functions directly (reused, not duplicated) --
never `extract_incentive_intelligence` itself, which would silently
produce an always-empty result.

*Executive Track Record Intelligence adds nothing this module needs.*
Re-read fresh: `ExecutiveTenureRecord.executive` is the exact same
`ExecutiveIdentity` object `executive_change_intelligence.py` already
produces; Track Record's own value-add (tenure-filtered financial
periods, guidance history, timeline) is about company performance
*during* a tenure, not about that executive's own ownership or
compensation. Consuming the full `ExecutiveTrackRecordKnowledge` object
here would import a large, irrelevant dependency for a single field
(`.executive`) already available directly from `ExecutiveChangeKnowledge.
executives`. This module therefore takes `tuple[ExecutiveIdentity, ...]`
directly, matching Sprint 20's own precedent for the identical need.

*No production caller of `extract_filing_content` exists anywhere in
this codebase.* Confirmed by a repo-wide search: `extract_filing_content`
is called only from its own defining module and from unit tests --
`service.py`'s own `InvestmentCaseCompositionService.build()` never
calls it, for any filing, for any purpose. This means `Ownership
Intelligence` and `Executive Compensation Intelligence` are both real,
complete, tested capabilities that are currently unreachable from the
live Investment Case composition pipeline -- there is no wired path
from a `RegulatoryFiling` to a `FilingContent` in production code today.
This is a genuine, pre-existing infrastructure gap, not something this
"aggregation sprint" is scoped to close (building a live HTML-fetching
pipeline into `service.py` would be new infrastructure, not
aggregation, and is not what Phase 8 asks for). This module's own
`extract_insider_alignment_knowledge` is therefore pure and no-I/O, like
every sibling it aggregates -- it is wired into `InvestmentCaseComposition`
/the API exactly like `incentive_intelligence.py` itself already is,
honestly empty in the live build until a future sprint wires a real
DEF 14A content-fetching path into `service.py` (a distinct, separate
capability). Live verification (Phase 10) therefore runs this module
directly against manually-fetched real filings, the same standalone
pattern every Filing-Content-Intelligence-family sprint since Sprint 14
has used for its own live verification.

**Phase 9 audit: no new `KnowledgeDomain` is introduced.** Every piece
of evidence this module reads is already covered by an existing domain:
`KnowledgeDomain.OWNERSHIP` (Sprint 19) and `KnowledgeDomain.
EXECUTIVE_COMPENSATION` (Sprint 20) for the underlying disclosures,
`KnowledgeDomain.MANAGEMENT` for executive identity. This module
introduces no new `BusinessFactKind`, no new `SourceKind`, no new
provider call, and computes nothing beyond linking and presenting
already-real evidence -- the identical precedent `executive_track_
record_intelligence.py`'s own Phase 9 finding already established for
an aggregation module one layer up. No new domain is registered.

**Design note on Phase 2's own example type list.** The spec lists both
`ExecutiveEquityExposure` and `EquityCompensationExposure` as example
type names. Building both would produce two dataclasses with no real
semantic difference -- the same per-executive equity/cash compensation
summary under two names. This module keeps one: `EquityCompensationExposure`.
Similarly, `AlignmentObservation` (the full, explainable, per-observation
record Phase 7 requires) and `AlignmentFinding` (a closed-vocabulary,
count-only summary) are kept distinct, mirroring the exact `TrackRecordFinding`
vs. its own underlying evidence precedent already established in
`executive_track_record_intelligence.py`.

**Design note on Phase 6's "ownership concentration changed" example.**
Ownership Intelligence computes no aggregate ownership-concentration
metric (e.g. percent held by the top N owners) -- doing so here would
be new statistical computation this sprint's own "avoid recomputing
anything already available" (Phase 1) and "aggregation sprint" framing
both counsel against. This module instead reuses Ownership Intelligence's
own real per-owner change vocabulary (`OwnershipChangeKind`), scoped to
disclosures matched to a specific executive, and adds a real, narrow,
disclosed numeric trend (Phase 5) computed the same way Sprint 20's own
compensation-change comparison was: reading an already-disclosed number
in its own native numeric form for a purely mechanical directional
comparison is not estimation. A concentration metric is deliberately
not fabricated to fill this gap.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.alpha.investment_case.executive_change_intelligence import ExecutiveIdentity
from atlas.alpha.investment_case.executive_compensation_intelligence import (
    ExecutiveCompensationKnowledge,
    build_incentive_knowledge,
    build_incentive_structures,
)
from atlas.alpha.investment_case.incentive_intelligence import (
    EquityIncentiveKind,
    ExecutiveIncentiveProgram,
    IncentiveStructure,
    IncentiveStructureComponent,
)
from atlas.alpha.investment_case.ownership_intelligence import (
    OwnershipDisclosure,
    OwnershipDisclosureSource,
    OwnershipKnowledge,
)

__all__ = [
    "OwnershipTrend",
    "AlignmentObservationKind",
    "AlignmentFindingKind",
    "InsiderHolding",
    "ExecutiveOwnership",
    "OwnershipChange",
    "EquityCompensationExposure",
    "AlignmentObservation",
    "AlignmentFinding",
    "ExecutiveAlignmentProfile",
    "InsiderAlignmentKnowledge",
    "extract_insider_alignment_knowledge",
]


# -- Phase 2: Alignment Knowledge Model ---------------------------------------


class OwnershipTrend(str, Enum):
    """Phase 5's own closed trend vocabulary -- a real, mechanical
    directional comparison of already-disclosed numbers, never a
    prediction and never computed from fewer than two comparable
    disclosures."""

    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    INSUFFICIENT_HISTORY = "insufficient_history"
    """Fewer than two matched, comparable disclosures exist for this
    executive -- or the two most recent disclosures' own text could not
    be cleanly parsed as a plain number. Never a guessed trend."""


class AlignmentObservationKind(str, Enum):
    """Phase 6's own closed, evidence-only observation vocabulary --
    never a score, never a judgment about whether the observed fact is
    good or bad."""

    EXECUTIVE_OWNS_STOCK = "executive_owns_stock"
    EXECUTIVE_HAS_NO_DISCLOSED_OWNERSHIP = "executive_has_no_disclosed_ownership"
    EXECUTIVE_HAS_EQUITY_AWARDS = "executive_has_equity_awards"
    EQUITY_COMPENSATION_DISCLOSED = "equity_compensation_disclosed"
    CASH_ONLY_COMPENSATION_DISCLOSED = "cash_only_compensation_disclosed"
    """Real, disclosed compensation components exist for this executive,
    and none of them is `IncentiveStructureComponent.EQUITY_AWARDS` --
    never a claim that no equity was ever granted, only that none is
    disclosed among the components this module could classify."""
    OWNERSHIP_INCREASING = "ownership_increasing"
    OWNERSHIP_DECREASING = "ownership_decreasing"
    OWNERSHIP_STABLE = "ownership_stable"


class AlignmentFindingKind(str, Enum):
    """Closed, presence-only findings -- never a score, never a
    ranking, mirrors `executive_track_record_intelligence.
    TrackRecordFindingKind`'s own discipline exactly."""

    OWNERSHIP_EVIDENCE_LINKED = "ownership_evidence_linked"
    EQUITY_COMPENSATION_EVIDENCE_LINKED = "equity_compensation_evidence_linked"
    OWNERSHIP_HISTORY_AVAILABLE = "ownership_history_available"
    NO_ALIGNMENT_EVIDENCE = "no_alignment_evidence"


@dataclass(frozen=True)
class InsiderHolding:
    """One real, disclosed ownership record matched to a specific
    executive -- every field a direct pass-through of the matched
    `OwnershipDisclosure` this module never recomputes."""

    disclosed_percentage: str | None
    disclosed_share_count: str | None
    source: OwnershipDisclosureSource
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    provenance: str


@dataclass(frozen=True)
class OwnershipChange:
    """One consecutive-pair comparison between two of this executive's
    own matched holdings, chronologically adjacent -- mirrors Ownership
    Intelligence's own pairwise history discipline, scoped to a single
    executive."""

    executive_name: str
    trend: OwnershipTrend
    compared_field: str | None
    """`"disclosed_share_count"` or `"disclosed_percentage"` -- whichever
    field this comparison actually used. `None` when `trend` is
    `INSUFFICIENT_HISTORY` because neither field was cleanly comparable."""
    previous_value: str | None
    current_value: str | None
    previous_holding: InsiderHolding
    current_holding: InsiderHolding
    provenance: str


@dataclass(frozen=True)
class ExecutiveOwnership:
    """Every real, disclosed ownership record matched to this executive
    by exact name, plus the trend derived from the most recent
    comparable pair (Phase 5)."""

    executive_name: str
    holdings: tuple[InsiderHolding, ...]
    """Chronological, oldest first -- every matched disclosure across
    every filing supplied, never deduplicated (a real filer may repeat
    the same disclosure verbatim across consecutive filings, which is
    itself real evidence, not noise)."""
    trend: OwnershipTrend


@dataclass(frozen=True)
class EquityCompensationExposure:
    """Per-executive equity/cash compensation exposure -- built entirely
    from Sprint 20's own `build_incentive_knowledge`/`build_incentive_
    structures` bridge functions, never recomputed from raw compensation
    records here."""

    executive_name: str
    has_equity_awards: bool
    equity_incentive_kinds: tuple[EquityIncentiveKind, ...]
    has_cash_compensation: bool
    disclosed_components: tuple[IncentiveStructureComponent, ...]
    program: ExecutiveIncentiveProgram | None
    structure: IncentiveStructure | None


@dataclass(frozen=True)
class AlignmentObservation:
    """Phase 7's own explainability requirement, in full: every
    observation exposes its source filing, reporting period, executive,
    provenance, and disclosure source -- no hidden reasoning."""

    kind: AlignmentObservationKind
    executive_name: str
    accession_number: str | None
    form_type: str | None
    filed_at: datetime | None
    source_reference: str | None
    disclosure_source: str | None
    """The originating disclosure's own source label (`OwnershipDisclosureSource`
    or `CompensationDisclosureSource`, as its real `.value` string) --
    kept as `str` since either type may back a given observation."""
    provenance: str


@dataclass(frozen=True)
class AlignmentFinding:
    kind: AlignmentFindingKind
    evidence_count: int


@dataclass(frozen=True)
class ExecutiveAlignmentProfile:
    executive: ExecutiveIdentity
    ownership: ExecutiveOwnership
    ownership_changes: tuple[OwnershipChange, ...]
    equity_compensation: EquityCompensationExposure
    observations: tuple[AlignmentObservation, ...]


@dataclass(frozen=True)
class InsiderAlignmentKnowledge:
    profiles: tuple[ExecutiveAlignmentProfile, ...]
    """One profile per `ExecutiveIdentity` supplied -- same count, same
    order, never a re-derivation of who the executives are."""
    findings: tuple[AlignmentFinding, ...]
    filings_considered: tuple[str, ...]
    """The union of `ownership.filings_considered` and `compensation.
    filings_considered` -- every accession number either source actually
    used, deduplicated, chronological."""


# -- Phase 3: Ownership Aggregation (literal name matching only) -------------


def _match_ownership(executive: ExecutiveIdentity, ownership: OwnershipKnowledge) -> tuple[OwnershipDisclosure, ...]:
    """Exact, case-insensitive name equality only -- never a fuzzy
    match, never a partial match. A paragraph-sourced `OwnershipDisclosure`
    (`owner_name is None`) can never match anything, by construction."""
    target = executive.name.strip().lower()
    matched = [
        d for d in ownership.disclosures
        if d.owner_name is not None and d.owner_name.strip().lower() == target
    ]
    return tuple(sorted(matched, key=lambda d: (d.filed_at, d.table_order_index or 0, d.row_index or 0)))


def _holding_from_disclosure(disclosure: OwnershipDisclosure) -> InsiderHolding:
    provenance = f"{disclosure.accession_number}:table{disclosure.table_order_index}:row{disclosure.row_index}"
    return InsiderHolding(
        disclosed_percentage=disclosure.disclosed_percentage, disclosed_share_count=disclosure.disclosed_share_count,
        source=disclosure.source, accession_number=disclosure.accession_number, form_type=disclosure.form_type,
        filed_at=disclosure.filed_at, source_reference=disclosure.source_reference, provenance=provenance,
    )


# -- Phase 5: Historical Ownership (a real, disclosed number, mechanically
# compared -- never estimated; mirrors executive_compensation_intelligence's
# own `_parse_plain_number` precedent, reimplemented here for percentage/
# share-count text specifically, never imported across a module boundary
# neither module exposes.) ----------------------------------------------------

_PLAIN_NUMBER_RE = re.compile(r"-?[\d,]+(\.\d+)?")


def _parse_ownership_number(text: str | None) -> float | None:
    """`None` unless `text`, once a trailing `%` and surrounding
    whitespace are stripped, is *entirely* a plain number -- a
    footnote marker, an approximation word ("approximately"), or any
    other non-numeric content makes the value honestly unparseable
    rather than silently truncated."""
    if text is None:
        return None
    stripped = text.strip()
    if stripped.endswith("%"):
        stripped = stripped[:-1].strip()
    if not _PLAIN_NUMBER_RE.fullmatch(stripped):
        return None
    return float(stripped.replace(",", ""))


def _compare_holdings(executive_name: str, earlier: InsiderHolding, later: InsiderHolding) -> OwnershipChange:
    provenance = f"{earlier.accession_number}->{later.accession_number}"
    for field_name, earlier_text, later_text in (
        ("disclosed_share_count", earlier.disclosed_share_count, later.disclosed_share_count),
        ("disclosed_percentage", earlier.disclosed_percentage, later.disclosed_percentage),
    ):
        earlier_value = _parse_ownership_number(earlier_text)
        later_value = _parse_ownership_number(later_text)
        if earlier_value is None or later_value is None:
            continue
        if later_value > earlier_value:
            trend = OwnershipTrend.INCREASING
        elif later_value < earlier_value:
            trend = OwnershipTrend.DECREASING
        else:
            trend = OwnershipTrend.STABLE
        return OwnershipChange(
            executive_name=executive_name, trend=trend, compared_field=field_name,
            previous_value=earlier_text, current_value=later_text, previous_holding=earlier,
            current_holding=later, provenance=provenance,
        )
    return OwnershipChange(
        executive_name=executive_name, trend=OwnershipTrend.INSUFFICIENT_HISTORY, compared_field=None,
        previous_value=None, current_value=None, previous_holding=earlier, current_holding=later,
        provenance=provenance,
    )


def _ownership_changes(executive_name: str, holdings: tuple[InsiderHolding, ...]) -> tuple[OwnershipChange, ...]:
    return tuple(_compare_holdings(executive_name, holdings[i - 1], holdings[i]) for i in range(1, len(holdings)))


# -- Phase 4: Equity Compensation Integration ---------------------------------


def _match_program(
    executive: ExecutiveIdentity, programs: tuple[ExecutiveIncentiveProgram, ...],
) -> ExecutiveIncentiveProgram | None:
    target = executive.name.strip().lower()
    for program in programs:
        if program.executive_name.strip().lower() == target:
            return program
    return None


def _match_structure(
    executive: ExecutiveIdentity, structures: tuple[IncentiveStructure, ...],
) -> IncentiveStructure | None:
    target = executive.name.strip().lower()
    for structure in structures:
        if structure.executive_name.strip().lower() == target:
            return structure
    return None


def _equity_compensation_exposure(
    executive: ExecutiveIdentity, programs: tuple[ExecutiveIncentiveProgram, ...],
    structures: tuple[IncentiveStructure, ...],
) -> EquityCompensationExposure:
    program = _match_program(executive, programs)
    structure = _match_structure(executive, structures)
    equity_kinds = tuple(sorted({e.kind for e in program.equity_incentives}, key=lambda k: k.value)) if program else ()
    return EquityCompensationExposure(
        executive_name=executive.name, has_equity_awards=bool(equity_kinds),
        equity_incentive_kinds=equity_kinds, has_cash_compensation=bool(program.cash_incentives) if program else False,
        disclosed_components=structure.components if structure else (), program=program, structure=structure,
    )


# -- Phase 6: Alignment Observations ------------------------------------------


def _ownership_observations(executive: ExecutiveIdentity, ownership: ExecutiveOwnership) -> list[AlignmentObservation]:
    observations: list[AlignmentObservation] = []
    if ownership.holdings:
        latest = ownership.holdings[-1]
        observations.append(
            AlignmentObservation(
                kind=AlignmentObservationKind.EXECUTIVE_OWNS_STOCK, executive_name=executive.name,
                accession_number=latest.accession_number, form_type=latest.form_type, filed_at=latest.filed_at,
                source_reference=latest.source_reference, disclosure_source=latest.source.value,
                provenance=latest.provenance,
            )
        )
        if ownership.trend is not OwnershipTrend.INSUFFICIENT_HISTORY:
            trend_kind = {
                OwnershipTrend.INCREASING: AlignmentObservationKind.OWNERSHIP_INCREASING,
                OwnershipTrend.DECREASING: AlignmentObservationKind.OWNERSHIP_DECREASING,
                OwnershipTrend.STABLE: AlignmentObservationKind.OWNERSHIP_STABLE,
            }[ownership.trend]
            observations.append(
                AlignmentObservation(
                    kind=trend_kind, executive_name=executive.name, accession_number=latest.accession_number,
                    form_type=latest.form_type, filed_at=latest.filed_at, source_reference=latest.source_reference,
                    disclosure_source=latest.source.value, provenance=latest.provenance,
                )
            )
    else:
        observations.append(
            AlignmentObservation(
                kind=AlignmentObservationKind.EXECUTIVE_HAS_NO_DISCLOSED_OWNERSHIP, executive_name=executive.name,
                accession_number=None, form_type=None, filed_at=None, source_reference=None, disclosure_source=None,
                provenance=f"no matching ownership disclosure for {executive.name!r}",
            )
        )
    return observations


def _equity_compensation_observations(
    executive: ExecutiveIdentity, exposure: EquityCompensationExposure,
) -> list[AlignmentObservation]:
    observations: list[AlignmentObservation] = []
    program = exposure.program
    if exposure.has_equity_awards and program is not None:
        award = program.equity_incentives[0]
        observations.append(
            AlignmentObservation(
                kind=AlignmentObservationKind.EXECUTIVE_HAS_EQUITY_AWARDS, executive_name=executive.name,
                accession_number=None, form_type=None, filed_at=None, source_reference=None, disclosure_source=None,
                provenance=award.provenance,
            )
        )
    structure = exposure.structure
    if structure is not None and structure.components:
        if IncentiveStructureComponent.EQUITY_AWARDS in structure.components:
            kind = AlignmentObservationKind.EQUITY_COMPENSATION_DISCLOSED
        else:
            kind = AlignmentObservationKind.CASH_ONLY_COMPENSATION_DISCLOSED
        observations.append(
            AlignmentObservation(
                kind=kind, executive_name=executive.name, accession_number=None, form_type=None, filed_at=None,
                source_reference=None, disclosure_source=None, provenance=structure.provenance,
            )
        )
    return observations


def _findings(profiles: tuple[ExecutiveAlignmentProfile, ...]) -> tuple[AlignmentFinding, ...]:
    with_ownership = sum(1 for p in profiles if p.ownership.holdings)
    with_equity_comp = sum(
        1 for p in profiles if p.equity_compensation.program is not None or p.equity_compensation.structure is not None
    )
    with_history = sum(1 for p in profiles if p.ownership.trend is not OwnershipTrend.INSUFFICIENT_HISTORY)

    findings: list[AlignmentFinding] = []
    if with_ownership:
        findings.append(AlignmentFinding(kind=AlignmentFindingKind.OWNERSHIP_EVIDENCE_LINKED, evidence_count=with_ownership))
    if with_equity_comp:
        findings.append(
            AlignmentFinding(kind=AlignmentFindingKind.EQUITY_COMPENSATION_EVIDENCE_LINKED, evidence_count=with_equity_comp)
        )
    if with_history:
        findings.append(AlignmentFinding(kind=AlignmentFindingKind.OWNERSHIP_HISTORY_AVAILABLE, evidence_count=with_history))
    if not findings:
        findings.append(AlignmentFinding(kind=AlignmentFindingKind.NO_ALIGNMENT_EVIDENCE, evidence_count=0))
    return tuple(findings)


# -- Composition ---------------------------------------------------------------


def extract_insider_alignment_knowledge(
    executives: tuple[ExecutiveIdentity, ...], ownership: OwnershipKnowledge, compensation: ExecutiveCompensationKnowledge,
) -> InsiderAlignmentKnowledge:
    """Pure, no I/O. `executives == ()` yields an empty `profiles` --
    never a fabricated roster. Calls Sprint 20's own `build_incentive_
    knowledge`/`build_incentive_structures` internally (Phase 4's own
    "Executive Compensation -> Incentive Intelligence -> Ownership"
    chain) -- never `incentive_intelligence.extract_incentive_intelligence`,
    which is always empty (see this module's own top docstring)."""
    programs = build_incentive_knowledge(compensation)
    structures = build_incentive_structures(compensation)

    profiles: list[ExecutiveAlignmentProfile] = []
    for executive in executives:
        matched_disclosures = _match_ownership(executive, ownership)
        holdings = tuple(_holding_from_disclosure(d) for d in matched_disclosures)
        changes = _ownership_changes(executive.name, holdings)
        trend = changes[-1].trend if changes else OwnershipTrend.INSUFFICIENT_HISTORY
        executive_ownership = ExecutiveOwnership(executive_name=executive.name, holdings=holdings, trend=trend)

        exposure = _equity_compensation_exposure(executive, programs, structures)

        observations = tuple(
            _ownership_observations(executive, executive_ownership) + _equity_compensation_observations(executive, exposure)
        )

        profiles.append(
            ExecutiveAlignmentProfile(
                executive=executive, ownership=executive_ownership, ownership_changes=changes,
                equity_compensation=exposure, observations=observations,
            )
        )

    filings_considered = tuple(sorted(set(ownership.filings_considered) | set(compensation.filings_considered)))

    return InsiderAlignmentKnowledge(
        profiles=tuple(profiles), findings=_findings(tuple(profiles)), filings_considered=filings_considered,
    )
