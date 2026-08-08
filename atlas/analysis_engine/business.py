"""Business Analysis (ATLAS-021) -- the canonical owner of every
business-quality conclusion Atlas produces: Business Model, Competitive
Position, Management, Capital Allocation, Growth, and Durability.

Per the Phase 1 audit performed before this module was written: neither
`atlas.core.domain.observation.entity.Observation` nor
`atlas.core.domain.evidence.entity.Evidence` carries any structural
field distinguishing which of these six categories a given record
concerns -- `Observation.subject` names *what company or topic*, never
*which business dimension*. Attributing free-text `Statement` content to
a category would require semantic/NLP parsing, which is forbidden
everywhere this codebase already touches Business Evaluation (see
`atlas.decision_engine.stages.business_evaluation`'s own module
docstring). No Financial Statement, Annual Report, Filing, or Transcript
Core Domain Object exists yet either. **Consequently, all six categories
are structurally indistinguishable from each other today** -- every one
reports the identical real reason: no category-attributable evidence
source exists yet, Case-scoped or external.

Durability is not recomputed here -- it is **reused verbatim** from
`atlas.decision_engine.stages.business_evaluation`'s own
`DurabilityFinding` (already real, already `INSUFFICIENT_INPUT`, for
the identical underlying reason). `decision_engine` remains the sole
producer of that raw signal; this module owns the six-category
*taxonomy* it is presented through, never a second computation of it.

**Designed for extensibility without a future redesign** (an explicit
requirement of this sprint): `evaluate_business_analysis` already
accepts `external_records` -- a typed, currently-always-empty slot for
future financial-statement/filing/transcript/macro/news ingestion (see
`ExternalSourceKind`, reserved and unconstructed this sprint, matching
`atlas.analysis_engine.provenance.SourceKind.EXTERNAL_DATA_SOURCE`'s own
"reserve the name now, construct it later" discipline). A future
ingestion adapter only needs to populate this tuple; nothing about
`BusinessFinding`, `BusinessAnalysisResult`, or this function's
signature needs to change. `test_business.py::TestExtensibility` proves
this wiring is real, not decorative, by constructing non-empty
`external_records` and confirming coverage/evidence-reference behavior
actually changes.

**Even once `external_records` exist, `status` deliberately stays
`INSUFFICIENT_INPUT`.** Classifying a category as `WEAK`/`MODERATE`/
`STRONG` requires *interpreting what a record says* -- a real evaluator
reading and judging content, which does not exist yet even in design --
never *how many records exist*. Turning a record count into a strength
verdict would be exactly the fabricated heuristic this codebase's
"no invented scoring systems, no hidden heuristics" principle forbids.
This function proves the extensibility path works (confidence and
evidence references genuinely change) without pretending record-counting
is business judgment.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.findings import FindingSeverity
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.core.domain.evidence.value_objects import Direction
from atlas.decision_engine.contracts import BusinessEvaluationResult, EvaluationState, EvidenceCoverageLevel

__all__ = [
    "BusinessCategory",
    "BusinessCategoryStatus",
    "BusinessDataGapKind",
    "ExternalSourceKind",
    "ExternalBusinessRecord",
    "BusinessFinding",
    "BusinessAnalysisResult",
    "evaluate_business_analysis",
]


class BusinessCategory(str, Enum):
    """A closed, six-member taxonomy -- Phase 2's explicit ownership
    list. Every `BusinessAnalysisResult.findings` names all six, every
    run, never a partial list (mirrors
    `atlas.decision_engine.contracts.PortfolioFinding`'s own "always
    name every factor" discipline)."""

    BUSINESS_MODEL = "business_model"
    COMPETITIVE_POSITION = "competitive_position"
    MANAGEMENT = "management"
    CAPITAL_ALLOCATION = "capital_allocation"
    GROWTH = "growth"
    DURABILITY = "durability"


class BusinessCategoryStatus(str, Enum):
    """Categorical, five levels, never numeric -- this sprint's own
    Phase 4 list, applied verbatim. `NOT_EVALUATED` is reserved for a
    future category this module has not yet implemented an evaluator
    for at all; every category this sprint ships has a real evaluator
    (see module docstring), so `NOT_EVALUATED` is never constructed
    today -- the same "name it, don't construct it yet" pattern
    `EvaluationState.EVALUATED`/`INSUFFICIENT_INPUT` already established
    for `DurabilityFinding`."""

    NOT_EVALUATED = "not_evaluated"
    INSUFFICIENT_INPUT = "insufficient_input"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class BusinessDataGapKind(str, Enum):
    """Why a category could not reach a `WEAK`/`MODERATE`/`STRONG`
    conclusion -- always a real, named reason, never a placeholder
    guess. No separate wrapper type pairs this with a reference (unlike
    `atlas.decision_engine.contracts.EvidenceGap`): a per-category gap
    has nothing more specific to reference than the category itself,
    already `BusinessFinding.kind` -- pairing would only duplicate that
    field, so `BusinessFinding.missing_evidence` is typed
    `tuple[BusinessDataGapKind, ...]` directly."""

    NO_EXTERNAL_DATA_SOURCE_CONNECTED = "no_external_data_source_connected"
    """No financial-statement/filing/transcript/macro/news ingestion
    adapter is connected -- true for every category, every run, this
    sprint."""

    EXTERNAL_DATA_NOT_YET_INTERPRETED = "external_data_not_yet_interpreted"
    """`external_records` for this category is non-empty, but no
    evaluator exists yet that reads record *content* rather than
    counting records -- see module docstring. Never constructed this
    sprint (`external_records` is always empty at every real call
    site); reachable only via `test_business.py`'s extensibility test."""


class ExternalSourceKind(str, Enum):
    """Reserved -- named now so a future ingestion adapter does not need
    to widen this enum. No code in this sprint ever constructs an
    `ExternalBusinessRecord`, so no member here is ever instantiated
    yet either -- the same "reserve the name, never construct it this
    sprint" discipline `SourceKind.EXTERNAL_DATA_SOURCE` and
    `RecommendationOutcomeKind.DIRECTIONAL` already established."""

    FINANCIAL_STATEMENT = "financial_statement"
    ANNUAL_REPORT = "annual_report"
    QUARTERLY_REPORT = "quarterly_report"
    COMPANY_FILING = "company_filing"
    EARNINGS_TRANSCRIPT = "earnings_transcript"
    MACRO_INDICATOR = "macro_indicator"
    NEWS_ITEM = "news_item"


@dataclass(frozen=True)
class ExternalBusinessRecord:
    """A single external, non-Core evidentiary record tagged to one
    `BusinessCategory`. Deliberately generic and minimal -- this sprint
    invents no financial-statement schema (no revenue/EPS/margin
    fields): a future ingestion adapter maps its own strongly-typed
    provider response onto this one generic shape before handing it to
    Business Analysis, the same way `Observation`/`Evidence` already
    give investor-sourced evidence one generic shape rather than one
    type per topic. `direction` reuses Evidence's own `SUPPORTS`/
    `CHALLENGES` vocabulary rather than inventing a second one.
    `reference` is an opaque id into whatever future store holds the
    real record -- this module never reads or interprets record
    content, only counts and directions (see module docstring on why
    that structurally cannot yield a strength verdict).
    """

    source_kind: ExternalSourceKind
    category: BusinessCategory
    direction: Direction
    reference: str


_ALL_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)


def _severity_for_status(status: BusinessCategoryStatus) -> FindingSeverity:
    """Deterministic, mechanical mapping -- severity describes how much
    attention a gap deserves, never a business-quality judgment (the
    same distinction `findings.py`'s own `FindingSeverity` docstring
    already draws)."""
    if status in (BusinessCategoryStatus.NOT_EVALUATED, BusinessCategoryStatus.INSUFFICIENT_INPUT):
        return FindingSeverity.ATTENTION
    if status is BusinessCategoryStatus.WEAK:
        return FindingSeverity.MATERIAL
    return FindingSeverity.INFO


@dataclass(frozen=True)
class BusinessFinding:
    """One category's structured, canonical conclusion.

    No free-text `conclusion` field exists here, despite this sprint's
    own suggested structure naming one -- the same deliberate departure
    `atlas.analysis_engine.findings.Finding` already documents and this
    module repeats for consistency: `status` (a closed enum) *is* the
    conclusion; any elaboration belongs in `supporting_evidence`/
    `contradicting_evidence`/`missing_evidence`, all structured, never
    prose. `updated_at` is always the caller-supplied evaluation
    timestamp, never a wall-clock read.
    """

    id: str
    kind: BusinessCategory
    status: BusinessCategoryStatus
    severity: FindingSeverity
    supporting_evidence: tuple[str, ...]
    contradicting_evidence: tuple[str, ...]
    missing_evidence: tuple[BusinessDataGapKind, ...]
    confidence: EvidenceCoverageLevel
    provenance: Provenance
    updated_at: datetime


@dataclass(frozen=True)
class BusinessAnalysisResult:
    """The stage-level wrapper -- mirrors
    `atlas.decision_engine.contracts.BusinessEvaluationResult`'s own
    `state` tier: whether the *stage* ran, kept separate from each
    category's own `BusinessCategoryStatus`. Always `EVALUATED` this
    sprint -- assembling six honest `INSUFFICIENT_INPUT` conclusions is
    itself a real, deterministic result, the same "even an audit trail
    that is mostly 'not yet assessable' is a real conclusion" principle
    `ReasoningResult` already established.
    """

    state: EvaluationState
    findings: tuple[BusinessFinding, ...]

    def __post_init__(self) -> None:
        if self.state is EvaluationState.EVALUATED:
            categories = {finding.kind for finding in self.findings}
            if categories != set(BusinessCategory):
                raise AnalysisEngineContractError(
                    "An EVALUATED BusinessAnalysisResult must carry a "
                    "BusinessFinding for every BusinessCategory member, "
                    "never a partial list."
                )


def _evaluate_category(
    category: BusinessCategory,
    *,
    records: tuple[ExternalBusinessRecord, ...],
    evaluated_at: datetime,
) -> BusinessFinding:
    supporting = tuple(record.reference for record in records if record.direction is Direction.SUPPORTS)
    contradicting = tuple(record.reference for record in records if record.direction is Direction.CHALLENGES)

    # WEAK/MODERATE/STRONG remain out of reach regardless of this
    # branch -- see module docstring. Only confidence, evidence
    # references, and the missing-evidence reason change.
    status = BusinessCategoryStatus.INSUFFICIENT_INPUT

    if records:
        confidence = EvidenceCoverageLevel.FULL if (supporting or contradicting) else EvidenceCoverageLevel.NONE
        missing_evidence = (BusinessDataGapKind.EXTERNAL_DATA_NOT_YET_INTERPRETED,)
        source_kind = SourceKind.EXTERNAL_DATA_SOURCE
    else:
        confidence = EvidenceCoverageLevel.NOT_APPLICABLE
        missing_evidence = (BusinessDataGapKind.NO_EXTERNAL_DATA_SOURCE_CONNECTED,)
        source_kind = SourceKind.ANALYSIS_ENGINE_STAGE

    dependencies: tuple[str, ...] = ()
    update_trigger = UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED

    if category is BusinessCategory.DURABILITY:
        # Reused, not recomputed -- decision_engine's DurabilityFinding
        # is the real source of truth for this one category whenever no
        # external record overrides it; its own state is asserted, not
        # re-derived, by the caller (see evaluate_business_analysis).
        if not records:
            source_kind = SourceKind.DECISION_ENGINE_STAGE
            dependencies = ("business_analysis_unavailable",)
            update_trigger = UpdateTrigger.UPSTREAM_STAGE_CHANGED

    return BusinessFinding(
        id=f"business_finding:{category.value}",
        kind=category,
        status=status,
        severity=_severity_for_status(status),
        supporting_evidence=supporting,
        contradicting_evidence=contradicting,
        missing_evidence=missing_evidence,
        confidence=confidence,
        provenance=Provenance(
            source_kind=source_kind,
            source_references=supporting + contradicting,
            dependencies=dependencies,
            update_trigger=update_trigger,
            consumers=_ALL_CONSUMERS,
            computed_at=evaluated_at,
        ),
        updated_at=evaluated_at,
    )


def evaluate_business_analysis(
    business_evaluation: BusinessEvaluationResult,
    *,
    external_records: tuple[ExternalBusinessRecord, ...] = (),
    evaluated_at: datetime,
) -> BusinessAnalysisResult:
    """Deterministic: identical inputs always produce a deeply equal
    `BusinessAnalysisResult`. `external_records` is always `()` at
    every real call site in this sprint (see module docstring); it is
    real, tested code, not a stub -- populating it is the entire
    extension point a future ingestion sprint needs.

    Requires `business_evaluation.state is EvaluationState.EVALUATED` --
    Durability reuse depends on `business_evaluation.durability`
    existing, the same precondition `evaluate_reasoning` already
    enforces implicitly by requiring its own three upstream results.
    """
    if business_evaluation.state is not EvaluationState.EVALUATED or business_evaluation.durability is None:
        raise AnalysisEngineContractError(
            "evaluate_business_analysis requires an EVALUATED "
            "BusinessEvaluationResult carrying a durability finding."
        )

    records_by_category: dict[BusinessCategory, list[ExternalBusinessRecord]] = {
        category: [] for category in BusinessCategory
    }
    for record in external_records:
        records_by_category[record.category].append(record)

    findings = tuple(
        _evaluate_category(
            category,
            records=tuple(records_by_category[category]),
            evaluated_at=evaluated_at,
        )
        for category in BusinessCategory
    )

    return BusinessAnalysisResult(state=EvaluationState.EVALUATED, findings=findings)
