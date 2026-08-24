"""Pure, deterministic Mandatory Core / Publication / Lifecycle-state
logic -- Investment Case Lifecycle Specification, Sections 1-4. No I/O,
no wall-clock read beyond what callers pass in, no randomness: identical
inputs always produce an identical output, the same discipline every
sibling Decision Layer `engine.py` already follows.

Every check reads an already-real signal `atlas.analysis_engine`
computes -- `business_analysis`/`risk_analysis`/`recommendation` on
`CanonicalAnalysis` -- and `company_profile`/`market_snapshot` already
on `InvestmentCaseComposition`. Nothing here recomputes or overrides
any of them.
"""
from __future__ import annotations

from datetime import datetime

from atlas.analysis_engine.business_contracts import BusinessCategory, BusinessCategoryStatus
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.models import CanonicalAnalysis
from atlas.analysis_engine.recommendation import ComputedDirectionalRecommendation
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind, ValuationStatus
from atlas.alpha.investment_case.models import InvestmentCaseComposition
from atlas.alpha.investment_case_lifecycle.models import (
    AtlasStatus,
    EvidenceTier,
    LifecycleState,
    MandatoryCoreAssessment,
    MandatoryItemAssessment,
    MandatoryItemId,
    MissingReasonCode,
    PublicationEligibility,
    RegressionRecord,
)

__all__ = [
    "evaluate_mandatory_core",
    "evaluate_publication_eligibility",
    "derive_lifecycle_state",
    "evaluate_important_gaps",
    "evidence_tier_for",
    "detect_regression",
    "next_expected_action",
    "build_atlas_status",
]

_BUSINESS_REAL_STATUSES = frozenset(
    {BusinessCategoryStatus.WEAK, BusinessCategoryStatus.MODERATE, BusinessCategoryStatus.STRONG}
)
_RISK_REAL_STATUSES = frozenset({RiskStatus.LOW, RiskStatus.MODERATE, RiskStatus.HIGH})


def _business_status(canonical: CanonicalAnalysis, category: BusinessCategory) -> BusinessCategoryStatus:
    return next(f.status for f in canonical.business_analysis.findings if f.kind is category)


def _risk_status(canonical: CanonicalAnalysis, category: RiskCategory) -> RiskStatus:
    return next(f.status for f in canonical.risk_analysis.findings if f.category is category)


def _real_risk_categories(canonical: CanonicalAnalysis) -> tuple[RiskCategory, ...]:
    return tuple(
        f.category for f in canonical.risk_analysis.findings if f.status in _RISK_REAL_STATUSES
    )


def _evaluate_m1(composition: InvestmentCaseComposition, ticker: str | None) -> MandatoryItemAssessment:
    """Company identity and business are known. Reuses
    `InvestmentCaseComposition.company_profile` (Company Profile
    business record) and the case's own resolved ticker -- every real
    Case's `case_id` already resolved through the Canonical Security
    Identity Gate before it could exist at all, so a resolvable ticker
    is itself real identity evidence, not a second identity system."""
    satisfied = composition.company_profile is not None or ticker is not None
    satisfied_via = "company_profile" if composition.company_profile is not None else ("resolved_ticker" if ticker is not None else None)
    reason = None if satisfied else MissingReasonCode.WAITING_FOR_COMPANY_PROFILE
    return MandatoryItemAssessment(
        item=MandatoryItemId.M1_IDENTITY_KNOWN, satisfied=satisfied, satisfied_via=satisfied_via, reason=reason
    )


def _evaluate_m2(canonical: CanonicalAnalysis) -> MandatoryItemAssessment:
    """Current economics are available. Satisfied by any one of
    Growth, Capital Allocation, or Financial Risk reaching a real
    status -- deliberately not `business_conclusive`
    (`atlas.analysis_engine.conviction`'s own AND-of-Growth-and-
    Capital-Allocation concept, built for a different question). A
    weak, negative, or declining reading satisfies this exactly as a
    strong one does; only `NOT_EVALUATED`/`INSUFFICIENT_INPUT` does
    not."""
    growth = _business_status(canonical, BusinessCategory.GROWTH)
    capital_allocation = _business_status(canonical, BusinessCategory.CAPITAL_ALLOCATION)
    financial_risk = _risk_status(canonical, RiskCategory.FINANCIAL_RISK)

    if growth in _BUSINESS_REAL_STATUSES:
        return MandatoryItemAssessment(MandatoryItemId.M2_CURRENT_ECONOMICS, True, "growth", None)
    if capital_allocation in _BUSINESS_REAL_STATUSES:
        return MandatoryItemAssessment(MandatoryItemId.M2_CURRENT_ECONOMICS, True, "capital_allocation", None)
    if financial_risk in _RISK_REAL_STATUSES:
        return MandatoryItemAssessment(MandatoryItemId.M2_CURRENT_ECONOMICS, True, "financial_risk", None)
    return MandatoryItemAssessment(
        MandatoryItemId.M2_CURRENT_ECONOMICS, False, None, MissingReasonCode.WAITING_FOR_CURRENT_ECONOMICS
    )


def _evaluate_m3(composition: InvestmentCaseComposition) -> MandatoryItemAssessment:
    """A current market price exists. Deliberately does not require a
    resolved Valuation status -- see the Lifecycle Specification's own
    design decision (Section 1, M3): requiring a real valuation verdict
    would silently re-exclude every hard-to-value company, since the
    "how or whether this can be valued" capability does not exist yet.
    Valuation narrows its own claim post-Publication instead of
    blocking it."""
    has_price = composition.market_snapshot is not None and composition.market_snapshot.share_price is not None
    reason = None if has_price else MissingReasonCode.WAITING_FOR_MARKET_PRICE
    return MandatoryItemAssessment(
        MandatoryItemId.M3_MARKET_PRICE, has_price, "market_snapshot" if has_price else None, reason
    )


def _evaluate_m4(canonical: CanonicalAnalysis) -> MandatoryItemAssessment:
    """At least one evidence-backed material risk is understood.
    Satisfied by any one of the four real risk sub-categories (business,
    financial, valuation, thesis) reaching a real status -- not full
    coverage across all four."""
    real_categories = _real_risk_categories(canonical)
    if real_categories:
        return MandatoryItemAssessment(MandatoryItemId.M4_RISK_EVIDENCE, True, real_categories[0].value, None)
    return MandatoryItemAssessment(
        MandatoryItemId.M4_RISK_EVIDENCE, False, None, MissingReasonCode.WAITING_FOR_RISK_EVIDENCE
    )


def evaluate_mandatory_core(composition: InvestmentCaseComposition, *, ticker: str | None) -> MandatoryCoreAssessment:
    """`M1 AND M2 AND M3 AND M4` -- always names all four, satisfied or
    not."""
    canonical = composition.canonical_analysis
    items = (
        _evaluate_m1(composition, ticker),
        _evaluate_m2(canonical),
        _evaluate_m3(composition),
        _evaluate_m4(canonical),
    )
    return MandatoryCoreAssessment(items=items, all_satisfied=all(i.satisfied for i in items))


def _has_genuine_recommendation(canonical: CanonicalAnalysis) -> bool:
    """Mirrors `atlas.alpha.decision_support.describe_recommendation`'s
    own `isinstance` check exactly -- a real directional recommendation
    (including a negative/cautious direction) counts; a withheld one
    does not. Never equates "no recommendation yet" with a negative
    recommendation, and never equates "insufficient evidence" with a
    recommendation."""
    return isinstance(canonical.recommendation.recommendation, ComputedDirectionalRecommendation)


def evaluate_publication_eligibility(composition: InvestmentCaseComposition, *, ticker: str | None) -> PublicationEligibility:
    """Investment Case Lifecycle Specification, Section 2's decision
    flow. Mandatory Core satisfied AND a genuine recommendation exists
    -> eligible. A Mandatory-Core-satisfied case with a withheld
    recommendation is `WAITING_FOR_RECOMMENDATION` -- a normal,
    deterministic outcome of `select_direction` legitimately declining
    to state a direction, never conflated with `INTERNAL_EVALUATION_ERROR`
    (reserved for a genuine evaluator exception, handled in the service
    layer's own try/except, never constructed here)."""
    core = evaluate_mandatory_core(composition, ticker=ticker)
    if not core.all_satisfied:
        return PublicationEligibility(
            eligible=False, mandatory_core=core, recommendation_exists=False, blocking_reason=None
        )
    recommendation_exists = _has_genuine_recommendation(composition.canonical_analysis)
    if not recommendation_exists:
        return PublicationEligibility(
            eligible=False,
            mandatory_core=core,
            recommendation_exists=False,
            blocking_reason=MissingReasonCode.WAITING_FOR_RECOMMENDATION,
        )
    return PublicationEligibility(
        eligible=True, mandatory_core=core, recommendation_exists=True, blocking_reason=None
    )


def _has_any_real_evidence(composition: InvestmentCaseComposition) -> bool:
    """The `COMPANY_ADDED` / `DATA_COLLECTION` boundary's own
    precondition: has anything at all arrived yet, beyond the bare
    Case existing."""
    canonical = composition.canonical_analysis
    if composition.company_profile is not None or composition.market_snapshot is not None:
        return True
    any_real_business = any(f.status in _BUSINESS_REAL_STATUSES for f in canonical.business_analysis.findings)
    any_real_risk = bool(_real_risk_categories(canonical))
    return any_real_business or any_real_risk


def derive_lifecycle_state(
    composition: InvestmentCaseComposition,
    eligibility: PublicationEligibility,
    *,
    has_ever_monitored: bool,
    previous_state: LifecycleState | None,
) -> tuple[LifecycleState, bool]:
    """Investment Case Lifecycle Specification, Section 2's state-
    assignment table plus Section 3's regression cap. Returns
    `(state, regression_occurred)`. `previous_state` is the last
    persisted state for this case, `None` for a case never evaluated
    before -- passed explicitly so this function stays pure and fully
    unit-testable without a real repository."""
    if eligibility.eligible:
        return (LifecycleState.CONTINUOUS_MONITORING if has_ever_monitored else LifecycleState.PUBLISHED), False

    was_published = previous_state in (LifecycleState.PUBLISHED, LifecycleState.CONTINUOUS_MONITORING)
    if was_published:
        # Regression is capped at ANALYSIS_RUNNING -- never lower.
        # Atlas retains historical knowledge; it never "forgets" the
        # company (Lifecycle Specification, Section 3's "must never
        # happen" list).
        return LifecycleState.ANALYSIS_RUNNING, True

    core = eligibility.mandatory_core
    m1 = core.item(MandatoryItemId.M1_IDENTITY_KNOWN)
    beyond_m1_satisfied = core.satisfied_count() - (1 if m1.satisfied else 0)

    if not _has_any_real_evidence(composition):
        return LifecycleState.COMPANY_ADDED, False
    if m1.satisfied and beyond_m1_satisfied > 0:
        return LifecycleState.ANALYSIS_RUNNING, False
    return LifecycleState.DATA_COLLECTION, False


def evaluate_important_gaps(canonical: CanonicalAnalysis, core: MandatoryCoreAssessment) -> tuple[str, ...]:
    """Important-but-non-blocking gaps -- derived from the same real
    evidence the Mandatory Core already reads, never a separate,
    invented signal. Whichever of Growth / Capital Allocation /
    Financial Risk did *not* satisfy M2, and whichever risk categories
    beyond the one that satisfied M4 stayed unreal, are real,
    inspectable gaps that would strengthen an already-published case
    without ever being required to publish it. Valuation not yet
    resolved is included here too -- it never blocks Publication (M3),
    but it is a real, honest gap worth naming."""
    gaps: list[str] = []
    growth = _business_status(canonical, BusinessCategory.GROWTH)
    capital_allocation = _business_status(canonical, BusinessCategory.CAPITAL_ALLOCATION)
    if growth not in _BUSINESS_REAL_STATUSES:
        gaps.append("growth_not_yet_evaluated")
    if capital_allocation not in _BUSINESS_REAL_STATUSES:
        gaps.append("capital_allocation_not_yet_evaluated")

    real_risk_categories = {c.value for c in _real_risk_categories(canonical)}
    for category in RiskCategory:
        if category.value not in real_risk_categories and category in (
            RiskCategory.BUSINESS_RISK,
            RiskCategory.FINANCIAL_RISK,
            RiskCategory.VALUATION_RISK,
            RiskCategory.THESIS_RISK,
        ):
            gaps.append(f"{category.value}_not_yet_evaluated")

    fcf_yield = next(
        (f for f in canonical.valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE), None
    )
    if fcf_yield is None or fcf_yield.status is ValuationStatus.INSUFFICIENT_INPUT:
        gaps.append("valuation_not_yet_resolved")

    return tuple(gaps)


def evaluate_optional_gaps() -> tuple[str, ...]:
    """Deliberately empty this phase. No granular Optional-enrichment
    signal (peer comparison coverage, earnings-call intelligence depth,
    filing-review depth) is separately tracked anywhere in the current
    backend to check against -- returning a real, honest empty tuple
    here is correct; inventing placeholder gap names to populate this
    field would violate the governing spec's own "do not create vague
    pseudo-reasons merely to populate UI text" instruction."""
    return ()


def evidence_tier_for(important_gaps: tuple[str, ...], optional_gaps: tuple[str, ...]) -> EvidenceTier:
    """`MANDATORY_PLUS_IMPORTANT_PLUS_OPTIONAL` is never returned this
    phase, by construction: `evaluate_optional_gaps` always returns
    `()` (see its own docstring), so an empty `optional_gaps` here
    never means "all optional enrichment satisfied" -- it means
    optional enrichment isn't tracked at all yet. Returning the
    two-tier result a real signal actually backs is more honest than
    fabricating a third-tier distinction the current backend cannot
    make. `optional_gaps` is accepted as a parameter (unused this
    phase) so this function's signature does not need to change once a
    future phase gives it a real signal."""
    if important_gaps:
        return EvidenceTier.MANDATORY_ONLY
    return EvidenceTier.MANDATORY_PLUS_IMPORTANT


def detect_regression(
    *,
    previous_core: MandatoryCoreAssessment | None,
    current_core: MandatoryCoreAssessment,
    regression_occurred: bool,
    occurred_at: datetime,
) -> RegressionRecord | None:
    """Names exactly which M-item(s) flipped from satisfied to
    unsatisfied -- never a generic "something changed." `previous_core`
    is `None` only when no prior evaluation exists, in which case a
    regression cannot have occurred (guarded by `regression_occurred`
    already being `False` in that case at the call site)."""
    if not regression_occurred or previous_core is None:
        return None
    invalidated = tuple(
        current_item.item
        for current_item, previous_item in zip(current_core.items, previous_core.items)
        if previous_item.satisfied and not current_item.satisfied
    )
    reasons = tuple(current_core.item(item_id).reason for item_id in invalidated if current_core.item(item_id).reason is not None)
    return RegressionRecord(occurred_at=occurred_at, invalidated_items=invalidated, reasons=reasons)


def next_expected_action(state: LifecycleState, eligibility: PublicationEligibility) -> str:
    """Plain-language description of what Atlas expects to happen
    next -- never a promised ETA the system cannot actually predict."""
    if state is LifecycleState.COMPANY_ADDED:
        return "waiting for company profile"
    if state is LifecycleState.DATA_COLLECTION:
        return "collecting current financial data"
    if state is LifecycleState.ANALYSIS_RUNNING:
        if eligibility.blocking_reason is MissingReasonCode.WAITING_FOR_RECOMMENDATION:
            return "synthesizing recommendation"
        return "evaluating available evidence"
    return "monitoring for new evidence"


def build_atlas_status(
    *,
    case_id: str,
    composition: InvestmentCaseComposition,
    ticker: str | None,
    has_ever_monitored: bool,
    last_monitored_at: datetime | None,
    previous_state: LifecycleState | None,
    previous_core: MandatoryCoreAssessment | None,
    published_since: datetime | None,
    generated_at: datetime,
) -> AtlasStatus:
    """Assembles the complete `AtlasStatus` object -- Investment Case
    Lifecycle Specification, Section 5. Pure given all real inputs
    already resolved by the caller (`service.py`); performs no I/O
    itself."""
    eligibility = evaluate_publication_eligibility(composition, ticker=ticker)
    state, regression_occurred = derive_lifecycle_state(
        composition, eligibility, has_ever_monitored=has_ever_monitored, previous_state=previous_state
    )
    important_gaps = evaluate_important_gaps(composition.canonical_analysis, eligibility.mandatory_core)
    optional_gaps = evaluate_optional_gaps()
    regression = detect_regression(
        previous_core=previous_core,
        current_core=eligibility.mandatory_core,
        regression_occurred=regression_occurred,
        occurred_at=generated_at,
    )
    # Shown whenever the case is currently Published/Monitoring, or a
    # regression just occurred (so the UI can say "Published since
    # [date], currently re-evaluating" rather than looking like a case
    # that was never published) -- never shown otherwise.
    ever_published = state in (LifecycleState.PUBLISHED, LifecycleState.CONTINUOUS_MONITORING) or regression_occurred
    resolved_published_since = published_since if ever_published else None
    return AtlasStatus(
        case_id=case_id,
        lifecycle_state=state,
        mandatory_core=eligibility.mandatory_core,
        evidence_tier=evidence_tier_for(important_gaps, optional_gaps),
        important_missing_items=important_gaps,
        optional_missing_items=optional_gaps,
        next_expected_action=next_expected_action(state, eligibility),
        last_updated=last_monitored_at,
        next_refresh_description="next automatic check, triggered by new evidence (price refresh, filing, portfolio event)",
        published_since=resolved_published_since,
        last_regression=regression,
        generated_at=generated_at,
    )
