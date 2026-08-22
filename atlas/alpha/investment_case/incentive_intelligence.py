"""Incentive Knowledge Model + Incentive Timeline + Ownership Alignment
+ Dilution Knowledge + Incentive Structure + Incentive Change
Intelligence (Capability Expansion Sprint 12: Incentive Intelligence,
Phases 2 through 8).

**Phase 1 audit finding, the load-bearing fact this entire module is
built around**: this codebase has never read the *content* of a single
SEC filing, and until this sprint had never even discovered that a
proxy statement (SEC Form `DEF 14A` -- the real-world document that
discloses executive compensation, equity awards, performance metrics,
and ownership guidelines) exists. `regulatory_filings.py`'s own module
docstring already establishes that Atlas reads a filing's *existence
and metadata only*; `sec_edgar.SecEdgarFilingHistoryProvider`'s own
`_TRACKED_FORM_TYPES` set, before this sprint, tracked only `10-K`/
`10-Q`/`8-K`. No provider anywhere fetches Form 4 (insider transactions),
no `BusinessFactKind` carries a compensation figure, and no XBRL
`companyfacts` tag `SecEdgarFundamentalsProvider` reads corresponds to
executive pay. Earnings call transcripts (the one real source Sprint
10/11 build on) never state an executive's own RSU count, option grant,
or bonus target -- management does not read out its own compensation
figures on an earnings call.

**This sprint's one, minimal, additive provider change**: `"DEF 14A"`
was added to `sec_edgar._TRACKED_FORM_TYPES` -- a one-line registry
addition (Phase 9's own "introduce only the minimum provider support
necessary"), never a new provider, never a filing-content parser. This
lets Atlas discover *that* a proxy statement was filed, and when --
real, honest, traceable metadata -- without ever attempting to read,
parse, or estimate what that filing actually says. Insider ownership
(Form 4) is deliberately **not** added: this codebase's own existing
`_TRACKED_FORM_TYPES` comment already excludes it by design ("never
every administrative SEC form"), and this sprint's own Long-Term Vision
names "Insider Alignment Intelligence" as a distinct, separate future
capability -- adding Form 4 tracking here would be scope creep into
that sprint's own subject, not this one's.

**Every Phase 2-7 knowledge object below is a complete, correctly-typed,
closed-vocabulary framework -- and every one of them is always empty in
this build.** There is no path in this codebase from "a proxy statement
exists" to "here is what it says": no provider reads DEF 14A content,
so Atlas cannot honestly populate a single `EquityIncentive`, `CashIncentive`,
`PerformanceIncentive`, `IncentiveTimelineEvent`, `OwnershipAlignment`,
`DilutionEvent`, or `IncentiveStructure` record -- doing so would be
exactly the "estimate compensation values that are not available" this
sprint's own non-goals forbid. This is the identical "framework, not
complete dataset" discipline `KnowledgeDomain`'s own docstring already
establishes for domains with no wired extractor, and the same discipline
`SegmentGrowthInformation` (Sprint 6) and `return_on_invested_capital_
unavailable_reason` (Sprint 5) already establish for a single field --
applied here to an entire capability, honestly, because the underlying
evidence genuinely does not exist yet.

**`compensation_disclosure_filings` is the one real, non-empty signal
this module produces**: a pure re-labeling of `RegulatoryFiling` records
(Sprint 1's own Foundation Provider) whose `form_type == "DEF 14A"` --
proof a compensation-disclosing document exists and exactly when it was
filed, reused directly rather than duplicated.

**Phase 9 audit**: every record this module could ever read (`RegulatoryFiling`)
is already covered by the existing `KnowledgeDomain.REGULATORY_FILINGS`
domain -- this module introduces no new `BusinessFactKind`, no new
`SourceKind`, and reads richer evidence from that same, already-wired
domain (one more tracked form type). No new `KnowledgeDomain` is
registered.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from atlas.alpha.investment_case.regulatory_filings import RegulatoryFiling

__all__ = [
    "IncentiveEvidenceStatus",
    "EquityIncentiveKind",
    "EquityIncentive",
    "CashIncentiveKind",
    "CashIncentive",
    "PerformanceMetricKind",
    "PerformanceIncentive",
    "ExecutiveIncentiveProgram",
    "IncentiveTimelineEventKind",
    "IncentiveTimelineEvent",
    "OwnershipAlignmentStatus",
    "OwnershipAlignment",
    "DilutionEventKind",
    "DilutionEvent",
    "IncentiveStructureComponent",
    "IncentiveStructure",
    "IncentiveChangeFindingKind",
    "IncentiveChangeFinding",
    "CompensationDisclosureFiling",
    "IncentiveKnowledge",
    "extract_incentive_intelligence",
]

_COMPENSATION_DISCLOSURE_FORM_TYPE = "DEF 14A"


class IncentiveEvidenceStatus(str, Enum):
    """Phase 11's own explicit three-way distinction. `INFERRED` is
    never used in this build -- Atlas performs no inference for
    incentive data at all -- kept as a real, closed member only so a
    future capability that genuinely derives (never guesses) an
    incentive fact from explicit source text has a place to say so
    honestly, without redefining this enum."""

    OBSERVED = "observed"
    INFERRED = "inferred"
    UNAVAILABLE = "unavailable"


# -- Phase 2: Incentive Knowledge Model --------------------------------------


class EquityIncentiveKind(str, Enum):
    RSU = "rsu"
    OPTION = "option"
    PSU = "psu"
    RESTRICTED_STOCK = "restricted_stock"
    STOCK_OWNERSHIP = "stock_ownership"


@dataclass(frozen=True)
class EquityIncentive:
    """Never instantiated in this build -- see this module's own
    docstring. Shape only, for a future filing-content-reading
    capability to populate without redesigning this module."""

    executive_name: str
    kind: EquityIncentiveKind
    program: str | None
    source: str | None
    effective_period: str | None
    status: IncentiveEvidenceStatus
    provenance: str


class CashIncentiveKind(str, Enum):
    ANNUAL_BONUS = "annual_bonus"
    LONG_TERM_BONUS = "long_term_bonus"
    MILESTONE_BONUS = "milestone_bonus"


@dataclass(frozen=True)
class CashIncentive:
    """Never instantiated in this build."""

    executive_name: str
    kind: CashIncentiveKind
    program: str | None
    source: str | None
    effective_period: str | None
    status: IncentiveEvidenceStatus
    provenance: str


class PerformanceMetricKind(str, Enum):
    EPS_TARGET = "eps_target"
    REVENUE_TARGET = "revenue_target"
    MARGIN_TARGET = "margin_target"
    TSR_TARGET = "tsr_target"
    ROIC_TARGET = "roic_target"
    OTHER_EXPLICIT_METRIC = "other_explicit_metric"


@dataclass(frozen=True)
class PerformanceIncentive:
    """Never instantiated in this build. `explicit_target` is `None`
    always -- Phase 2's own "never estimate," made structurally
    impossible to violate rather than merely disclaimed."""

    executive_name: str
    metric_kind: PerformanceMetricKind
    explicit_target: float | None
    program: str | None
    source: str | None
    status: IncentiveEvidenceStatus
    provenance: str


@dataclass(frozen=True)
class ExecutiveIncentiveProgram:
    """Never instantiated in this build -- `IncentiveKnowledge.
    executive_incentive_programs` is always `()`. Shape preserved for a
    future capability that reads real proxy-statement content."""

    executive_name: str
    role: str | None
    program: str | None
    source: str | None
    effective_period: str | None
    status: IncentiveEvidenceStatus
    equity_incentives: tuple[EquityIncentive, ...]
    cash_incentives: tuple[CashIncentive, ...]
    performance_incentives: tuple[PerformanceIncentive, ...]


# -- Phase 3: Incentive Timeline ----------------------------------------------


class IncentiveTimelineEventKind(str, Enum):
    PROGRAM_INTRODUCED = "program_introduced"
    PROGRAM_MODIFIED = "program_modified"
    PROGRAM_REPLACED = "program_replaced"
    PROGRAM_EXPIRED = "program_expired"
    PROGRAM_DISCONTINUED = "program_discontinued"


@dataclass(frozen=True)
class IncentiveTimelineEvent:
    """Never instantiated in this build."""

    kind: IncentiveTimelineEventKind
    executive_name: str | None
    program: str | None
    effective_date: date | None
    source: str | None
    provenance: str


# -- Phase 4: Ownership Alignment ---------------------------------------------


class OwnershipAlignmentStatus(str, Enum):
    OWNERSHIP_INCREASE = "ownership_increase"
    OWNERSHIP_DECREASE = "ownership_decrease"
    OWNERSHIP_UNAVAILABLE = "ownership_unavailable"


@dataclass(frozen=True)
class OwnershipAlignment:
    """Never instantiated in this build -- see this module's own
    docstring for why insider/ownership data (Form 4) is explicitly out
    of this sprint's scope. `status` would always resolve to
    `OWNERSHIP_UNAVAILABLE` if this were ever constructed."""

    executive_name: str
    shares_owned: float | None
    ownership_guideline: str | None
    status: OwnershipAlignmentStatus
    source: str | None
    provenance: str


# -- Phase 5: Dilution Knowledge ----------------------------------------------


class DilutionEventKind(str, Enum):
    OPTION_ISSUANCE = "option_issuance"
    RSU_ISSUANCE = "rsu_issuance"
    SHARE_RESERVE_CHANGE = "share_reserve_change"
    VESTING_EVENT = "vesting_event"


@dataclass(frozen=True)
class DilutionEvent:
    """Never instantiated in this build."""

    kind: DilutionEventKind
    executive_name: str | None
    shares: float | None
    effective_date: date | None
    source: str | None
    provenance: str


# -- Phase 6: Incentive Structure ---------------------------------------------


class IncentiveStructureComponent(str, Enum):
    FIXED_SALARY = "fixed_salary"
    ANNUAL_BONUS = "annual_bonus"
    EQUITY_AWARDS = "equity_awards"
    LONG_TERM_INCENTIVES = "long_term_incentives"
    PERFORMANCE_AWARDS = "performance_awards"
    DEFERRED_COMPENSATION = "deferred_compensation"


@dataclass(frozen=True)
class IncentiveStructure:
    """Never instantiated in this build. `components` would only ever
    list elements explicitly supported by source material (Phase 6's
    own instruction) -- since no source material is read, it is always
    empty, never a guessed default composition."""

    executive_name: str
    components: tuple[IncentiveStructureComponent, ...]
    source: str | None
    provenance: str


# -- Phase 7 + 8: Incentive Change Intelligence + Findings -------------------


class IncentiveChangeFindingKind(str, Enum):
    """Closed, presence-only findings -- never a score, never an
    alignment judgment (this sprint's own "no incentive score, no
    alignment score" non-goal)."""

    INCENTIVE_PLAN_REVISED = "incentive_plan_revised"
    EQUITY_WEIGHTING_INCREASED = "equity_weighting_increased"
    OWNERSHIP_GUIDELINE_INTRODUCED = "ownership_guideline_introduced"
    PERFORMANCE_METRICS_CHANGED = "performance_metrics_changed"
    COMPENSATION_STRUCTURE_UNCHANGED = "compensation_structure_unchanged"
    COMPENSATION_DATA_UNAVAILABLE = "compensation_data_unavailable"
    """The only finding this build ever reaches -- see this module's
    own docstring for why every other member above, while real and
    closed, is currently unreachable."""


@dataclass(frozen=True)
class IncentiveChangeFinding:
    kind: IncentiveChangeFindingKind
    evidence_count: int
    """A disclosed count of the supporting `compensation_disclosure_
    filings` -- the only real evidence this module has."""


# -- The one real signal: compensation-disclosing filings --------------------


@dataclass(frozen=True)
class CompensationDisclosureFiling:
    """The one real, non-empty signal this module produces: a pure
    re-labeling of an already-real `RegulatoryFiling` (Sprint 1) whose
    own `form_type` is `"DEF 14A"` -- proof a compensation-disclosing
    document exists, and exactly when it was filed. Its content is
    never read."""

    filing: RegulatoryFiling


def _compensation_disclosure_filings(
    regulatory_filings: tuple[RegulatoryFiling, ...],
) -> tuple[CompensationDisclosureFiling, ...]:
    return tuple(
        CompensationDisclosureFiling(filing=filing)
        for filing in regulatory_filings
        if filing.form_type == _COMPENSATION_DISCLOSURE_FORM_TYPE
    )


def _findings(disclosures: tuple[CompensationDisclosureFiling, ...]) -> tuple[IncentiveChangeFinding, ...]:
    """Always the single honest finding this build can support:
    compensation data is unavailable, regardless of how many disclosure
    filings are known to exist -- knowing a proxy statement was filed
    is not the same as knowing what it says (Phase 11's own "whenever
    evidence is unavailable, it should remain unavailable")."""
    return (
        IncentiveChangeFinding(
            kind=IncentiveChangeFindingKind.COMPENSATION_DATA_UNAVAILABLE, evidence_count=len(disclosures),
        ),
    )


# -- Composition ---------------------------------------------------------------


@dataclass(frozen=True)
class IncentiveKnowledge:
    compensation_disclosure_filings: tuple[CompensationDisclosureFiling, ...]
    executive_incentive_programs: tuple[ExecutiveIncentiveProgram, ...]
    timeline: tuple[IncentiveTimelineEvent, ...]
    ownership_alignment: tuple[OwnershipAlignment, ...]
    dilution_events: tuple[DilutionEvent, ...]
    incentive_structures: tuple[IncentiveStructure, ...]
    findings: tuple[IncentiveChangeFinding, ...]


def extract_incentive_intelligence(regulatory_filings: tuple[RegulatoryFiling, ...]) -> IncentiveKnowledge:
    """Pure, no I/O. `regulatory_filings == ()` (or no `DEF 14A` among
    them) yields an empty `compensation_disclosure_filings` -- an
    honest absence, never a fabricated one."""
    disclosures = _compensation_disclosure_filings(regulatory_filings)
    return IncentiveKnowledge(
        compensation_disclosure_filings=disclosures, executive_incentive_programs=(), timeline=(),
        ownership_alignment=(), dilution_events=(), incentive_structures=(), findings=_findings(disclosures),
    )
