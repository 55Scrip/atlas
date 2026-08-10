"""Investment Case Monitoring & Change Intelligence v1.

Turns two structured `CanonicalAnalysis` states -- "what Atlas concluded
before" and "what Atlas concludes now" -- into a small, traceable list
of meaningful `ChangeFinding`s, an overall `ThesisImpact`, and a
concise, deterministic summary narrative.

**Not a second reasoning engine.** Nothing here re-derives a
`BusinessCategoryStatus`/`RiskStatus`/`ValuationStatus` conclusion or a
`HighlightKind`/`OpenQuestionOrigin` -- both `AnalyticalSnapshot`s this
module compares are pure, direct projections of a `CanonicalAnalysis`
another stage already computed (`business_analysis`, `risk_analysis`,
`valuation_engine`, `synthesis`). This module's only new computation is
the *comparison* between two such projections -- a deterministic,
sign-comparison rule table, the same discipline `growth.py`'s own
`classify_metric_trend` already established for a single dimension,
applied here across every dimension `investment_case_synthesis.py`
already tracks.

**Deterministic, no LLM.** `capture_snapshot` and `compare_snapshots`
are pure functions: identical inputs always produce identical outputs.
Where language is produced (`ChangeIntelligence.summary_narrative`), it
is assembled from fixed sentence templates keyed by already-computed
structured fields -- never a generated-text call, matching
`investment_case_synthesis._atlas_thesis`'s own "structured first,
language second" discipline exactly.

**Pure, no persistence.** This module never reads or writes a
`BusinessRecord`, never touches a repository, and never knows "the
previous analytical state" exists anywhere durable -- it only compares
two `AnalyticalSnapshot` values a caller already has. *Deciding* when to
persist a new snapshot, and *fetching* the previous one, is an Alpha-layer
concern (`atlas.alpha.investment_case_change`), the same "Core computes,
Alpha persists" split `business_data_refresh`/`business_data.pipeline`
already establish for `BusinessRecord`s themselves.

**Investor Model boundary.** This sprint is about the *company* changing,
not the investor. `AnalyticalSnapshot` deliberately excludes Conviction,
Evidence Coverage, and every other investor-evidence-derived signal --
those depend on what the investor has recorded, not what changed about
the business, and mixing them in here would blur exactly the boundary
`APP-000`'s "Investor Judgment cannot be delegated" doctrine protects.
A future sprint that wants "Atlas noticed you tend to ignore risk
increases" is a *different*, Investor-Model-aware capability -- it is
not built here, and nothing here assumes it exists.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Mapping

from atlas.analysis_engine.business_contracts import BusinessCategory
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus as BizStatus
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.investment_case_synthesis import HighlightKind, OpenQuestionOrigin
from atlas.analysis_engine.models import CanonicalAnalysis
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind
from atlas.analysis_engine.valuation.contracts import ValuationStatus as ValStatus

__all__ = [
    "ChangeCategory",
    "ChangeDirection",
    "ThesisImpact",
    "ChangeFinding",
    "AnalyticalSnapshot",
    "ChangeIntelligence",
    "capture_snapshot",
    "compare_snapshots",
    "describe_change",
    "dimension_label",
    "thesis_impact_sentence",
]

#: Mirrors `investment_case_synthesis._RISK_CATEGORIES_FOR_SYNTHESIS`
#: exactly, and for the same documented reason: `THESIS_RISK` reflects
#: the investor's own recorded Evidence/Observations contradicting each
#: other, not a fact about the company -- excluded from company Change
#: Intelligence for the identical Investor Model boundary reason this
#: module's own docstring states.
_COMPARED_RISK_CATEGORIES = (RiskCategory.BUSINESS_RISK, RiskCategory.FINANCIAL_RISK, RiskCategory.VALUATION_RISK)

_INSUFFICIENT_BUSINESS_STATUSES = (BizStatus.NOT_EVALUATED, BizStatus.INSUFFICIENT_INPUT)
_INSUFFICIENT_RISK_STATUSES = (RiskStatus.NOT_EVALUATED, RiskStatus.INSUFFICIENT_INPUT)
_INSUFFICIENT_VALUATION_STATUSES = (ValStatus.NOT_EVALUATED, ValStatus.INSUFFICIENT_INPUT)

#: Ordering by which "more" is closer to a real conclusion -- never a
#: numeric score, only ever used to compare two members of the *same*
#: closed enum against each other (never across enums, never exposed).
_BUSINESS_RANK = {BizStatus.WEAK: 0, BizStatus.MODERATE: 1, BizStatus.STRONG: 2}
_RISK_RANK = {RiskStatus.LOW: 0, RiskStatus.MODERATE: 1, RiskStatus.HIGH: 2}
_VALUATION_RANK = {ValStatus.UNDERVALUED: 0, ValStatus.FAIRLY_VALUED: 1, ValStatus.EXPENSIVE: 2}

#: Which `OpenQuestionOrigin` traces to which dimension's own snapshot
#: state -- used only to decide whether a *disappeared* question was a
#: genuine resolution (the dimension is still real, just no longer
#: triggers the condition) or an analytical-coverage regression (the
#: dimension itself became `INSUFFICIENT_INPUT`, which is never
#: reported as a resolution -- see `_open_question_changes`).
_ORIGIN_DIMENSION: Mapping[OpenQuestionOrigin, tuple[str, str]] = {
    OpenQuestionOrigin.GROWTH_INCONCLUSIVE: ("business", BusinessCategory.GROWTH.value),
    OpenQuestionOrigin.GROWTH_MIXED: ("business", BusinessCategory.GROWTH.value),
    OpenQuestionOrigin.CAPITAL_ALLOCATION_INCONCLUSIVE: ("business", BusinessCategory.CAPITAL_ALLOCATION.value),
    OpenQuestionOrigin.CAPITAL_ALLOCATION_WEAK: ("business", BusinessCategory.CAPITAL_ALLOCATION.value),
    OpenQuestionOrigin.VALUATION_INCONCLUSIVE: ("valuation", ValuationMethodKind.FCF_YIELD_RELATIVE.value),
    OpenQuestionOrigin.VALUATION_EXPENSIVE_VERSUS_GROWTH: ("valuation", ValuationMethodKind.FCF_YIELD_RELATIVE.value),
    OpenQuestionOrigin.SCENARIO_VALUATION_UNAVAILABLE: ("valuation", ValuationMethodKind.FCF_YIELD_RELATIVE.value),
}


class ChangeCategory(str, Enum):
    """A small, closed set -- one member per *kind* of user-facing
    change an Investment Case can meaningfully report. Direction
    (better/worse/neutral) is deliberately a separate field
    (`ChangeFinding.direction`), not folded into the category name, so
    this enum stays small (14 members) rather than doubling for every
    dimension's improved/weakened variant."""

    GROWTH_CHANGED = "growth_changed"
    CAPITAL_ALLOCATION_CHANGED = "capital_allocation_changed"
    BUSINESS_QUALITY_CHANGED = "business_quality_changed"
    """Reserved for the four `BusinessCategory` members with no real
    evaluator yet (`business_model`/`competitive_position`/`management`/
    `durability`) -- unreachable today (both sides are always
    `INSUFFICIENT_INPUT`, which never enters this branch; see
    `_business_category_changes`), kept so a future evaluator landing
    for one of them does not require a new `ChangeCategory` member."""
    BUSINESS_RISK_CHANGED = "business_risk_changed"
    FINANCIAL_RISK_CHANGED = "financial_risk_changed"
    VALUATION_RISK_CHANGED = "valuation_risk_changed"
    VALUATION_CHANGED = "valuation_changed"
    STRENGTH_ADDED = "strength_added"
    STRENGTH_REMOVED = "strength_removed"
    RISK_ADDED = "risk_added"
    RISK_REMOVED = "risk_removed"
    OPEN_QUESTION_ADDED = "open_question_added"
    OPEN_QUESTION_RESOLVED = "open_question_resolved"
    ANALYTICAL_COVERAGE_CHANGED = "analytical_coverage_changed"
    """A dimension moved between `INSUFFICIENT_INPUT`/`NOT_EVALUATED`
    and a real conclusion, in either direction -- "Atlas learned
    something new" or "Atlas lost a data source," never itself read as
    the company getting better or worse (`direction` is always
    `NEUTRAL`; see this module's own "Data Availability Changes"
    handling in `_business_category_changes`/`_risk_category_changes`/
    `_valuation_change`)."""


class ChangeDirection(str, Enum):
    """Never a numeric impact score -- a three-way categorical read,
    derived only from existing analytical semantics (which end of an
    already-ranked closed enum a transition moved toward). `NEUTRAL` is
    the honest, deliberate choice whenever a transition cannot safely
    be called better or worse (every `ANALYTICAL_COVERAGE_CHANGED`
    finding, by construction)."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class ThesisImpact(str, Enum):
    """How this run's changes, taken together, read against the
    existing Atlas Thesis -- never a numeric score, never itself a
    Recommendation or a Decision. `MIXED` is the deliberate, honest
    middle ground the sprint's own instruction requires: "one weakening
    component does NOT necessarily mean thesis invalidated." """

    STRENGTHENED = "strengthened"
    WEAKENED = "weakened"
    MIXED = "mixed"
    UNCHANGED = "unchanged"


@dataclass(frozen=True)
class ChangeFinding:
    """One meaningful, traceable change between two `AnalyticalSnapshot`s.

    `details` always carries a `"dimension"` key (which `BusinessCategory`/
    `RiskCategory`/`ValuationMethodKind`/`HighlightKind`/`OpenQuestionOrigin`
    value this change is about) -- the same "closed `category` plus a
    documented, free-form `details` dict" shape
    `atlas.analysis_engine.findings.Finding` already uses, chosen here
    for the identical reason: a handful of category members stays
    readable, while `details` still names exactly what changed without
    inventing a new enum member per dimension.
    """

    id: str
    category: ChangeCategory
    direction: ChangeDirection
    previous_state: str
    current_state: str
    details: Mapping[str, str]
    evidence_references: tuple[str, ...]
    source_finding_id: str | None


@dataclass(frozen=True)
class AnalyticalSnapshot:
    """"What did Atlas believe the structured state of this Case was at
    time T" -- never rendered prose, never a raw provider value.
    Structural columns only, the same "facts, not judgments... never
    what it says" discipline `business_data.models.BusinessRecord`
    already documents for itself.

    `content_hash` is computed over every field below **except**
    `current_yield`/`captured_at` -- deliberately excludes the one raw
    numeric value this snapshot carries (current FCF yield) so a share
    price tick that does not cross `ValuationStatus`'s own category
    boundary never counts as "the analytical state changed" (see this
    module's own top-level docstring and `capture_snapshot`'s own
    comment for the full reasoning). `current_yield` is still carried on
    the snapshot -- for display/traceability -- it is simply not part of
    this snapshot's own comparison identity.
    """

    business_category_states: tuple[tuple[str, str, str], ...]
    """`(BusinessCategory.value, BusinessCategoryStatus.value, finding_id)`, sorted by category -- every member of the six-category taxonomy, always."""
    risk_category_states: tuple[tuple[str, str, str], ...]
    """`(RiskCategory.value, RiskStatus.value, finding_id)`, sorted by category -- `_COMPARED_RISK_CATEGORIES` only."""
    valuation_status: str
    valuation_finding_id: str
    current_yield: float | None
    strength_kinds: tuple[str, ...]
    """Sorted `HighlightKind.value`s present in `synthesis.strengths`."""
    risk_highlight_kinds: tuple[str, ...]
    """Sorted `HighlightKind.value`s present in `synthesis.risks`."""
    open_question_origins: tuple[str, ...]
    """Sorted `OpenQuestionOrigin.value`s present in `synthesis.open_questions`."""
    content_hash: str
    captured_at: datetime


@dataclass(frozen=True)
class ChangeIntelligence:
    """The full Change Intelligence result for one comparison -- either
    "this is the first snapshot, there is nothing to compare against
    yet" (`is_baseline=True`, `changes=()`), or a real comparison
    against a genuinely different previous state (a caller must never
    invoke `compare_snapshots` for two snapshots with an identical
    `content_hash`; see that function's own docstring)."""

    is_baseline: bool
    changes: tuple[ChangeFinding, ...]
    thesis_impact: ThesisImpact
    summary_narrative: str
    previous_captured_at: datetime | None
    current_captured_at: datetime


def capture_snapshot(canonical_analysis: CanonicalAnalysis) -> AnalyticalSnapshot:
    """Pure projection of an already-computed `CanonicalAnalysis` --
    reads only `business_analysis`/`risk_analysis`/`valuation_engine`/
    `synthesis`, never a `BusinessRecord` or raw provider data (the
    exact same "reuse, never re-derive" discipline
    `investment_case_synthesis.synthesize_investment_case` already
    documents for itself). `captured_at` is `canonical_analysis
    .generated_at` -- no wall-clock read here, matching every other
    pure function in this package.
    """
    business_states = tuple(
        sorted(
            (finding.kind.value, finding.status.value, finding.id)
            for finding in canonical_analysis.business_analysis.findings
        )
    )
    risk_states = tuple(
        sorted(
            (finding.category.value, finding.status.value, finding.id)
            for finding in canonical_analysis.risk_analysis.findings
            if finding.category in _COMPARED_RISK_CATEGORIES
        )
    )
    valuation_finding = next(
        f for f in canonical_analysis.valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE
    )
    strength_kinds = tuple(sorted({h.kind.value for h in canonical_analysis.synthesis.strengths}))
    risk_highlight_kinds = tuple(sorted({h.kind.value for h in canonical_analysis.synthesis.risks}))
    open_question_origins = tuple(sorted({q.origin.value for q in canonical_analysis.synthesis.open_questions}))

    #: Deliberately excludes `current_yield` -- see `AnalyticalSnapshot`'s
    #: own docstring.
    hashed_content = {
        "business_category_states": business_states,
        "risk_category_states": risk_states,
        "valuation_status": valuation_finding.status.value,
        "strength_kinds": strength_kinds,
        "risk_highlight_kinds": risk_highlight_kinds,
        "open_question_origins": open_question_origins,
    }
    content_hash = hashlib.sha256(json.dumps(hashed_content, sort_keys=True).encode("utf-8")).hexdigest()

    return AnalyticalSnapshot(
        business_category_states=business_states,
        risk_category_states=risk_states,
        valuation_status=valuation_finding.status.value,
        valuation_finding_id=valuation_finding.id,
        current_yield=valuation_finding.current_yield,
        strength_kinds=strength_kinds,
        risk_highlight_kinds=risk_highlight_kinds,
        open_question_origins=open_question_origins,
        content_hash=content_hash,
        captured_at=canonical_analysis.generated_at,
    )


def _business_category_changes(
    previous: AnalyticalSnapshot, current: AnalyticalSnapshot
) -> tuple[ChangeFinding, ...]:
    previous_by_category = {category: (status, finding_id) for category, status, finding_id in previous.business_category_states}
    current_by_category = {category: (status, finding_id) for category, status, finding_id in current.business_category_states}
    category_to_change_category = {
        BusinessCategory.GROWTH.value: ChangeCategory.GROWTH_CHANGED,
        BusinessCategory.CAPITAL_ALLOCATION.value: ChangeCategory.CAPITAL_ALLOCATION_CHANGED,
    }

    changes: list[ChangeFinding] = []
    for category in sorted(current_by_category):
        prev_status, prev_finding_id = previous_by_category.get(category, (None, None))
        cur_status, cur_finding_id = current_by_category[category]
        if prev_status is None or prev_status == cur_status:
            continue

        prev_insufficient = BizStatus(prev_status) in _INSUFFICIENT_BUSINESS_STATUSES
        cur_insufficient = BizStatus(cur_status) in _INSUFFICIENT_BUSINESS_STATUSES

        if prev_insufficient and cur_insufficient:
            continue  # e.g. NOT_EVALUATED -> INSUFFICIENT_INPUT: still no real signal either side.

        if prev_insufficient != cur_insufficient:
            changes.append(
                ChangeFinding(
                    id=f"{ChangeCategory.ANALYTICAL_COVERAGE_CHANGED.value}:business:{category}",
                    category=ChangeCategory.ANALYTICAL_COVERAGE_CHANGED,
                    direction=ChangeDirection.NEUTRAL,
                    previous_state=prev_status,
                    current_state=cur_status,
                    details={"dimension": category},
                    evidence_references=(),
                    source_finding_id=cur_finding_id,
                )
            )
            continue

        # Both real, both different -- a genuine business-quality transition.
        rank_delta = _BUSINESS_RANK[BizStatus(cur_status)] - _BUSINESS_RANK[BizStatus(prev_status)]
        direction = ChangeDirection.POSITIVE if rank_delta > 0 else ChangeDirection.NEGATIVE
        change_category = category_to_change_category.get(category, ChangeCategory.BUSINESS_QUALITY_CHANGED)
        changes.append(
            ChangeFinding(
                id=f"{change_category.value}:{category}",
                category=change_category,
                direction=direction,
                previous_state=prev_status,
                current_state=cur_status,
                details={"dimension": category},
                evidence_references=(),
                source_finding_id=cur_finding_id,
            )
        )
    return tuple(changes)


def _risk_category_changes(previous: AnalyticalSnapshot, current: AnalyticalSnapshot) -> tuple[ChangeFinding, ...]:
    previous_by_category = {category: (status, finding_id) for category, status, finding_id in previous.risk_category_states}
    current_by_category = {category: (status, finding_id) for category, status, finding_id in current.risk_category_states}
    category_to_change_category = {
        RiskCategory.BUSINESS_RISK.value: ChangeCategory.BUSINESS_RISK_CHANGED,
        RiskCategory.FINANCIAL_RISK.value: ChangeCategory.FINANCIAL_RISK_CHANGED,
        RiskCategory.VALUATION_RISK.value: ChangeCategory.VALUATION_RISK_CHANGED,
    }

    changes: list[ChangeFinding] = []
    for category in sorted(current_by_category):
        prev_status, prev_finding_id = previous_by_category.get(category, (None, None))
        cur_status, cur_finding_id = current_by_category[category]
        if prev_status is None or prev_status == cur_status:
            continue

        prev_insufficient = RiskStatus(prev_status) in _INSUFFICIENT_RISK_STATUSES
        cur_insufficient = RiskStatus(cur_status) in _INSUFFICIENT_RISK_STATUSES

        if prev_insufficient and cur_insufficient:
            continue

        if prev_insufficient != cur_insufficient:
            changes.append(
                ChangeFinding(
                    id=f"{ChangeCategory.ANALYTICAL_COVERAGE_CHANGED.value}:risk:{category}",
                    category=ChangeCategory.ANALYTICAL_COVERAGE_CHANGED,
                    direction=ChangeDirection.NEUTRAL,
                    previous_state=prev_status,
                    current_state=cur_status,
                    details={"dimension": category},
                    evidence_references=(),
                    source_finding_id=cur_finding_id,
                )
            )
            continue

        # Higher rank = closer to HIGH = worse -- rising risk is NEGATIVE.
        rank_delta = _RISK_RANK[RiskStatus(cur_status)] - _RISK_RANK[RiskStatus(prev_status)]
        direction = ChangeDirection.NEGATIVE if rank_delta > 0 else ChangeDirection.POSITIVE
        change_category = category_to_change_category[category]
        changes.append(
            ChangeFinding(
                id=f"{change_category.value}:{category}",
                category=change_category,
                direction=direction,
                previous_state=prev_status,
                current_state=cur_status,
                details={"dimension": category},
                evidence_references=(),
                source_finding_id=cur_finding_id,
            )
        )
    return tuple(changes)


def _valuation_change(previous: AnalyticalSnapshot, current: AnalyticalSnapshot) -> tuple[ChangeFinding, ...]:
    prev_status, cur_status = previous.valuation_status, current.valuation_status
    if prev_status == cur_status:
        return ()

    prev_insufficient = ValStatus(prev_status) in _INSUFFICIENT_VALUATION_STATUSES
    cur_insufficient = ValStatus(cur_status) in _INSUFFICIENT_VALUATION_STATUSES
    dimension = ValuationMethodKind.FCF_YIELD_RELATIVE.value

    if prev_insufficient and cur_insufficient:
        return ()

    if prev_insufficient != cur_insufficient:
        return (
            ChangeFinding(
                id=f"{ChangeCategory.ANALYTICAL_COVERAGE_CHANGED.value}:valuation:{dimension}",
                category=ChangeCategory.ANALYTICAL_COVERAGE_CHANGED,
                direction=ChangeDirection.NEUTRAL,
                previous_state=prev_status,
                current_state=cur_status,
                details={"dimension": dimension},
                evidence_references=(),
                source_finding_id=current.valuation_finding_id,
            ),
        )

    # Higher rank = closer to EXPENSIVE = less attractive -- NEGATIVE.
    rank_delta = _VALUATION_RANK[ValStatus(cur_status)] - _VALUATION_RANK[ValStatus(prev_status)]
    direction = ChangeDirection.NEGATIVE if rank_delta > 0 else ChangeDirection.POSITIVE
    return (
        ChangeFinding(
            id=f"{ChangeCategory.VALUATION_CHANGED.value}:{dimension}",
            category=ChangeCategory.VALUATION_CHANGED,
            direction=direction,
            previous_state=prev_status,
            current_state=cur_status,
            details={"dimension": dimension},
            evidence_references=(),
            source_finding_id=current.valuation_finding_id,
        ),
    )


def _highlight_changes(
    previous_kinds: tuple[str, ...],
    current_kinds: tuple[str, ...],
    *,
    added_category: ChangeCategory,
    removed_category: ChangeCategory,
    added_direction: ChangeDirection,
    removed_direction: ChangeDirection,
) -> tuple[ChangeFinding, ...]:
    previous_set, current_set = set(previous_kinds), set(current_kinds)
    changes: list[ChangeFinding] = []
    for kind in sorted(current_set - previous_set):
        changes.append(
            ChangeFinding(
                id=f"{added_category.value}:{kind}",
                category=added_category,
                direction=added_direction,
                previous_state="absent",
                current_state=kind,
                details={"highlight_kind": kind},
                evidence_references=(),
                source_finding_id=None,
            )
        )
    for kind in sorted(previous_set - current_set):
        changes.append(
            ChangeFinding(
                id=f"{removed_category.value}:{kind}",
                category=removed_category,
                direction=removed_direction,
                previous_state=kind,
                current_state="absent",
                details={"highlight_kind": kind},
                evidence_references=(),
                source_finding_id=None,
            )
        )
    return tuple(changes)


def _dimension_lost_coverage(previous: AnalyticalSnapshot, current: AnalyticalSnapshot, dimension: tuple[str, str]) -> bool:
    """`True` only when the `OpenQuestionOrigin`'s own underlying
    dimension regressed from a real conclusion to `INSUFFICIENT_INPUT`/
    `NOT_EVALUATED` -- the one case a disappeared question must never be
    read as "resolved" (see `_open_question_changes`'s own docstring)."""
    kind, name = dimension
    if kind == "business":
        previous_status = next((status for category, status, _ in previous.business_category_states if category == name), None)
        current_status = next((status for category, status, _ in current.business_category_states if category == name), None)
        insufficient = _INSUFFICIENT_BUSINESS_STATUSES
        status_type = BizStatus
    else:
        previous_status = previous.valuation_status
        current_status = current.valuation_status
        insufficient = _INSUFFICIENT_VALUATION_STATUSES
        status_type = ValStatus
    if previous_status is None or current_status is None:
        return False
    return status_type(previous_status) not in insufficient and status_type(current_status) in insufficient


def _open_question_changes(previous: AnalyticalSnapshot, current: AnalyticalSnapshot) -> tuple[ChangeFinding, ...]:
    """New questions are always reported. A *disappeared* question is
    reported as `OPEN_QUESTION_RESOLVED` only when its own underlying
    dimension did **not** regress to `INSUFFICIENT_INPUT` -- otherwise
    the gap did not close, Atlas simply lost the data that let it ask
    the question in the first place, and that regression is already
    reported once, correctly, as an `ANALYTICAL_COVERAGE_CHANGED`
    finding for that same dimension (see the sprint's own "do not
    assume disappearance always means resolved... if it disappeared
    only because data was removed, that is not resolution" instruction).
    """
    previous_set, current_set = set(previous.open_question_origins), set(current.open_question_origins)
    changes: list[ChangeFinding] = []
    for origin in sorted(current_set - previous_set):
        changes.append(
            ChangeFinding(
                id=f"{ChangeCategory.OPEN_QUESTION_ADDED.value}:{origin}",
                category=ChangeCategory.OPEN_QUESTION_ADDED,
                direction=ChangeDirection.NEGATIVE,
                previous_state="absent",
                current_state=origin,
                details={"open_question_origin": origin},
                evidence_references=(),
                source_finding_id=None,
            )
        )
    for origin in sorted(previous_set - current_set):
        dimension = _ORIGIN_DIMENSION.get(OpenQuestionOrigin(origin))
        if dimension is not None and _dimension_lost_coverage(previous, current, dimension):
            continue
        changes.append(
            ChangeFinding(
                id=f"{ChangeCategory.OPEN_QUESTION_RESOLVED.value}:{origin}",
                category=ChangeCategory.OPEN_QUESTION_RESOLVED,
                direction=ChangeDirection.POSITIVE,
                previous_state=origin,
                current_state="absent",
                details={"open_question_origin": origin},
                evidence_references=(),
                source_finding_id=None,
            )
        )
    return tuple(changes)


def _thesis_impact(changes: tuple[ChangeFinding, ...]) -> ThesisImpact:
    positive = sum(1 for c in changes if c.direction is ChangeDirection.POSITIVE)
    negative = sum(1 for c in changes if c.direction is ChangeDirection.NEGATIVE)
    if positive == 0 and negative == 0:
        return ThesisImpact.UNCHANGED
    if positive > 0 and negative == 0:
        return ThesisImpact.STRENGTHENED
    if negative > 0 and positive == 0:
        return ThesisImpact.WEAKENED
    return ThesisImpact.MIXED


_DIMENSION_LABEL = {
    BusinessCategory.GROWTH.value: "Growth",
    BusinessCategory.CAPITAL_ALLOCATION.value: "Capital allocation",
    BusinessCategory.BUSINESS_MODEL.value: "Business model",
    BusinessCategory.COMPETITIVE_POSITION.value: "Competitive position",
    BusinessCategory.MANAGEMENT.value: "Management",
    BusinessCategory.DURABILITY.value: "Durability",
    RiskCategory.BUSINESS_RISK.value: "Business risk",
    RiskCategory.FINANCIAL_RISK.value: "Financial risk",
    RiskCategory.VALUATION_RISK.value: "Valuation risk",
    ValuationMethodKind.FCF_YIELD_RELATIVE.value: "Valuation",
}

_STATUS_LABEL = {
    "weak": "Weak",
    "moderate": "Moderate",
    "strong": "Strong",
    "low": "Low",
    "high": "High",
    "undervalued": "undervalued",
    "fairly_valued": "fairly valued",
    "expensive": "expensive",
    "insufficient_input": "not yet evaluable",
    "not_evaluated": "not yet evaluated",
}

_HIGHLIGHT_LABEL = {kind.value: kind.value.replace("_", " ") for kind in HighlightKind}


def dimension_label(dimension: str) -> str:
    """Public accessor for `_DIMENSION_LABEL` -- reused as-is by
    `atlas.analysis_engine.daily_brief` (Daily Brief v1) so that module
    never re-derives its own dimension vocabulary; falls back to a
    humanized raw value for any dimension not in the fixed table."""
    return _DIMENSION_LABEL.get(dimension, dimension.replace("_", " "))


def thesis_impact_sentence(thesis_impact: ThesisImpact) -> str:
    """Public accessor for `_THESIS_IMPACT_SENTENCE` -- the exact "why
    it matters" sentence this module already assembles into
    `ChangeIntelligence.summary_narrative`, reused verbatim by
    `atlas.analysis_engine.daily_brief` rather than re-derived."""
    return _THESIS_IMPACT_SENTENCE[thesis_impact]


def describe_change(change: ChangeFinding) -> str:
    if change.category is ChangeCategory.ANALYTICAL_COVERAGE_CHANGED:
        dimension = change.details["dimension"]
        label = _DIMENSION_LABEL.get(dimension, dimension.replace("_", " "))
        if change.current_state in ("insufficient_input", "not_evaluated"):
            return f"Atlas can no longer evaluate {label.lower()} -- prior supporting data is no longer available."
        return f"Atlas can now evaluate {label.lower()} after new data became available."

    if change.category in (
        ChangeCategory.GROWTH_CHANGED,
        ChangeCategory.CAPITAL_ALLOCATION_CHANGED,
        ChangeCategory.BUSINESS_QUALITY_CHANGED,
        ChangeCategory.BUSINESS_RISK_CHANGED,
        ChangeCategory.FINANCIAL_RISK_CHANGED,
        ChangeCategory.VALUATION_RISK_CHANGED,
    ):
        dimension = change.details["dimension"]
        label = _DIMENSION_LABEL.get(dimension, dimension.replace("_", " "))
        verb = "improved" if change.direction is ChangeDirection.POSITIVE else "weakened"
        previous_label = _STATUS_LABEL.get(change.previous_state, change.previous_state)
        current_label = _STATUS_LABEL.get(change.current_state, change.current_state)
        return f"{label} {verb} from {previous_label} to {current_label}."

    if change.category is ChangeCategory.VALUATION_CHANGED:
        verb = "more attractive" if change.direction is ChangeDirection.POSITIVE else "less attractive"
        return f"Valuation became {verb} ({_STATUS_LABEL.get(change.previous_state, change.previous_state)} -> {_STATUS_LABEL.get(change.current_state, change.current_state)})."

    if change.category is ChangeCategory.STRENGTH_ADDED:
        return f"New strength identified: {_HIGHLIGHT_LABEL.get(change.current_state, change.current_state)}."
    if change.category is ChangeCategory.STRENGTH_REMOVED:
        return f"{_HIGHLIGHT_LABEL.get(change.previous_state, change.previous_state).capitalize()} is no longer classified as a strength."
    if change.category is ChangeCategory.RISK_ADDED:
        return f"New risk identified: {_HIGHLIGHT_LABEL.get(change.current_state, change.current_state)}."
    if change.category is ChangeCategory.RISK_REMOVED:
        return f"{_HIGHLIGHT_LABEL.get(change.previous_state, change.previous_state).capitalize()} is no longer classified as a risk."
    if change.category is ChangeCategory.OPEN_QUESTION_ADDED:
        return "A new open question has emerged."
    if change.category is ChangeCategory.OPEN_QUESTION_RESOLVED:
        return "A previously open question has been resolved."
    return "The analytical state changed."  # pragma: no cover -- exhaustive above; defensive only.


_THESIS_IMPACT_SENTENCE = {
    ThesisImpact.STRENGTHENED: "Overall, the Atlas Thesis has strengthened.",
    ThesisImpact.WEAKENED: "Overall, the Atlas Thesis has weakened, but remains intact.",
    ThesisImpact.MIXED: (
        "Overall, the case shows mixed signals -- some parts strengthened while others weakened -- "
        "but the broader Atlas Thesis remains intact."
    ),
    ThesisImpact.UNCHANGED: "Overall, the Atlas Thesis is materially unchanged.",
}


def _summary_narrative(changes: tuple[ChangeFinding, ...], thesis_impact: ThesisImpact) -> str:
    if not changes:
        return "No material change since the previous analysis."
    bullets = "\n".join(f"- {describe_change(change)}" for change in changes)
    return f"Since the previous analysis:\n{bullets}\n\n{_THESIS_IMPACT_SENTENCE[thesis_impact]}"


def compare_snapshots(previous: AnalyticalSnapshot | None, current: AnalyticalSnapshot) -> ChangeIntelligence:
    """`previous=None` means "no prior snapshot exists" -- the first
    analysis ever recorded for this Case. This is a **baseline**, not a
    change: `changes` is always `()`, `thesis_impact` is always
    `UNCHANGED`, and the summary says so explicitly. A caller should
    never invoke this with two snapshots sharing an identical
    `content_hash` (that is "recomputed, not changed" -- the caller's
    own idempotency check, not this function's; see
    `atlas.alpha.investment_case_change`'s own module docstring), but if
    it does, every comparison below naturally produces zero changes
    anyway, so this remains safe either way.
    """
    if previous is None:
        return ChangeIntelligence(
            is_baseline=True,
            changes=(),
            thesis_impact=ThesisImpact.UNCHANGED,
            summary_narrative="Baseline established -- this is Atlas's first recorded analysis of this Case.",
            previous_captured_at=None,
            current_captured_at=current.captured_at,
        )

    changes = (
        _business_category_changes(previous, current)
        + _risk_category_changes(previous, current)
        + _valuation_change(previous, current)
        + _highlight_changes(
            previous.strength_kinds,
            current.strength_kinds,
            added_category=ChangeCategory.STRENGTH_ADDED,
            removed_category=ChangeCategory.STRENGTH_REMOVED,
            added_direction=ChangeDirection.POSITIVE,
            removed_direction=ChangeDirection.NEGATIVE,
        )
        + _highlight_changes(
            previous.risk_highlight_kinds,
            current.risk_highlight_kinds,
            added_category=ChangeCategory.RISK_ADDED,
            removed_category=ChangeCategory.RISK_REMOVED,
            added_direction=ChangeDirection.NEGATIVE,
            removed_direction=ChangeDirection.POSITIVE,
        )
        + _open_question_changes(previous, current)
    )

    thesis_impact = _thesis_impact(changes)
    return ChangeIntelligence(
        is_baseline=False,
        changes=changes,
        thesis_impact=thesis_impact,
        summary_narrative=_summary_narrative(changes, thesis_impact),
        previous_captured_at=previous.captured_at,
        current_captured_at=current.captured_at,
    )
