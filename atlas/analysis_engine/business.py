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

**Designed for extensibility without a future redesign** (ATLAS-021's
explicit requirement): `evaluate_business_analysis` accepts
`external_records` -- a typed slot for category-attributed,
directional evidentiary facts. A future ingestion adapter only needs
to populate this tuple; nothing about `BusinessFinding`,
`BusinessAnalysisResult`, or this function's signature needs to change.
`test_business.py::TestExtensibility` proves this wiring is real, not
decorative, by constructing non-empty `external_records` and confirming
coverage/evidence-reference behavior actually changes.

**ATLAS-022 supersession note:** `ExternalBusinessRecord.source_kind`
previously typed against this module's own `ExternalSourceKind` --
explicitly reserved, never constructed, "named now so a future
ingestion adapter does not need to widen this enum." That future sprint
was ATLAS-022: `atlas.analysis_engine.business_data.sources.SourceKind`
is now the one canonical document-type taxonomy in the repository, and
`ExternalSourceKind` is removed rather than kept alongside it or
adapted through a mapping function -- per that sprint's own audit, two
overlapping enums for the same concept would itself be the
duplicate-ownership violation this whole package exists to prevent.

**ATLAS-022 also adds `business_records`** -- `evaluate_business_analysis`
now accepts whole, canonical `business_data.models.BusinessRecord`
documents (not just category-attributed `ExternalBusinessRecord`
facts), because Business Analysis should be aware that raw source
material exists even before anything has extracted a category-specific
claim from it. A `BusinessRecord` carries no category or direction
(Phase 3 of ATLAS-022 forbids inventing either without reading document
content, which this codebase still does not do) -- so its presence is
surfaced only as an honest, case-wide count
(`BusinessAnalysisResult.available_business_records`), never folded
into any single category's `status` or `confidence`. Turning "an
annual report exists" into "this supports Capital Allocation" is
exactly the interpretation step neither this sprint nor ATLAS-022 built.

**Even once `external_records` exist, `status` deliberately stays
`INSUFFICIENT_INPUT`** -- for the three categories still on this path
(Business Model, Competitive Position, Management). Classifying one of
them as `WEAK`/`MODERATE`/`STRONG` requires *interpreting what a record
says* -- a real evaluator reading and judging content, which does not
exist yet even in design for these three -- never *how many records
exist*. This function proves
the extensibility path works (confidence and evidence references
genuinely change) without pretending record-counting is business
judgment.

**ATLAS-023: Growth and Capital Allocation graduate to real
evaluators.** `atlas.analysis_engine.growth.evaluate_growth` and
`.capital_allocation.evaluate_capital_allocation` now produce these two
categories' `BusinessFinding`s, reading `BusinessFact`s (extracted from
`business_records` by `atlas.analysis_engine.business_facts`) instead
of `external_records` -- documented, deterministic rule tables that can
genuinely reach `WEAK`/`MODERATE`/`STRONG` from real structured facts.
`external_records` tagged to `GROWTH`/`CAPITAL_ALLOCATION` are no
longer read at all; this module remains the sole *owner* (it still
assembles every `BusinessAnalysisResult` and decides which evaluator
produces which category's Finding), it simply now delegates two of the
six categories to their own rule-heavy modules rather than computing
them inline -- the same "stage lives in its own file, orchestrator
dispatches to it" pattern `atlas.decision_engine.pipeline` already
established for its own stages.

**Durability graduates the same way (Stage 3).**
`atlas.analysis_engine.durability.evaluate_durability` now produces this
category's `BusinessFinding` from the same `BusinessFact`s, through the
identical dispatch entry -- there is no special durability path. The
previous branch, which reused `decision_engine`'s permanently
`INSUFFICIENT_INPUT` `DurabilityFinding` whenever no external record
overrode it, is removed as unreachable: Durability no longer arrives at
`_evaluate_category` at all. `decision_engine`'s own `DurabilityFinding`
is untouched and remains locked -- it answers a different question
(whether `DecisionEngineInput` *alone* can assess durability, which it
still cannot), so the readiness layer continues to report
`business_durability_not_assessable` from it. That is a known, bounded
gap between the two objects, not an inconsistency to paper over here.

The shared vocabulary every category (and both new evaluators) uses --
`BusinessCategory`, `BusinessCategoryStatus`, `BusinessDataGapKind`,
`severity_for_status`, `BusinessFinding`, `BusinessAnalysisResult` --
now lives in `atlas.analysis_engine.business_contracts`, re-exported
here unchanged (see that module's own docstring for why: importing
`growth.py`/`capital_allocation.py` from this file, while they import
these shared types back, would otherwise be a circular import).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.analysis_engine.business_contracts import (
    BusinessAnalysisResult,
    BusinessCategory,
    BusinessCategoryStatus,
    BusinessDataGapKind,
    BusinessFinding,
    severity_for_status,
)
from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind as DocumentSourceKind
from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.capital_allocation import evaluate_capital_allocation
from atlas.analysis_engine.durability import evaluate_durability
from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.growth import evaluate_growth
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.core.domain.evidence.value_objects import Direction
from atlas.decision_engine.contracts import BusinessEvaluationResult, EvaluationState, EvidenceCoverageLevel

__all__ = [
    "BusinessCategory",
    "BusinessCategoryStatus",
    "BusinessDataGapKind",
    "ExternalBusinessRecord",
    "BusinessFinding",
    "BusinessAnalysisResult",
    "evaluate_business_analysis",
    "severity_for_status",
]


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

    `source_kind` types against
    `atlas.analysis_engine.business_data.sources.SourceKind` (ATLAS-022)
    -- the one canonical document-type taxonomy in the repository; see
    this module's own supersession note for why no second, parallel
    enum lives here anymore.
    """

    source_kind: DocumentSourceKind
    category: BusinessCategory
    direction: Direction
    reference: str


_ALL_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
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

    return BusinessFinding(
        id=f"business_finding:{category.value}",
        kind=category,
        status=status,
        severity=severity_for_status(status),
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
    business_records: tuple[BusinessRecord, ...] = (),
    evaluated_at: datetime,
) -> BusinessAnalysisResult:
    """Deterministic: identical inputs always produce a deeply equal
    `BusinessAnalysisResult`. `external_records` and `business_records`
    are both always `()` at every real call site today (see module
    docstring); real, tested code, not stubs -- populating them is the
    entire extension point future ingestion needs.

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

    # ATLAS-023: Growth and Capital Allocation read BusinessFacts, not
    # ExternalBusinessRecord -- extracted once, from the current head of
    # every document lineage the caller supplied, and handed to both
    # evaluators (both may draw from the same fact, e.g. a future
    # Valuation stage reusing REVENUE the identical way Growth already
    # does; see business_facts/__init__.py).
    facts = extract_facts_from_records(business_records, evaluated_at=evaluated_at)

    dispatch = {
        BusinessCategory.GROWTH: lambda: evaluate_growth(facts, evaluated_at=evaluated_at),
        BusinessCategory.CAPITAL_ALLOCATION: lambda: evaluate_capital_allocation(facts, evaluated_at=evaluated_at),
        BusinessCategory.DURABILITY: lambda: evaluate_durability(facts, evaluated_at=evaluated_at),
    }

    findings = tuple(
        dispatch[category]()
        if category in dispatch
        else _evaluate_category(
            category,
            records=tuple(records_by_category[category]),
            evaluated_at=evaluated_at,
        )
        for category in BusinessCategory
    )

    return BusinessAnalysisResult(
        state=EvaluationState.EVALUATED,
        findings=findings,
        available_business_records=tuple(record.id for record in business_records),
    )
