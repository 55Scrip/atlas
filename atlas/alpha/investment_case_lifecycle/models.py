"""Domain vocabulary for the Investment Case Lifecycle -- categorical,
never numeric, mirroring every sibling Decision Layer package's own
`str, Enum` + frozen-dataclass discipline (`atlas.alpha.decision_readiness
.models`, `atlas.alpha.materiality.models`, etc.).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

__all__ = [
    "LifecycleState",
    "MandatoryItemId",
    "MandatoryItemAssessment",
    "MandatoryCoreAssessment",
    "MissingReasonCode",
    "EvidenceTier",
    "PublicationEligibility",
    "RegressionRecord",
    "AtlasStatus",
    "LifecycleSnapshot",
]


class LifecycleState(str, Enum):
    """The five first-class states -- Investment Case Lifecycle
    Specification, Section 3. Represents Atlas's own state of work,
    never the quality of the investment: a poor company, a negative
    recommendation, or incomplete secondary analysis can all be
    `PUBLISHED`."""

    COMPANY_ADDED = "company_added"
    DATA_COLLECTION = "data_collection"
    ANALYSIS_RUNNING = "analysis_running"
    PUBLISHED = "published"
    CONTINUOUS_MONITORING = "continuous_monitoring"


class MandatoryItemId(str, Enum):
    """The four independent checks. Each internally accepts any one of
    several real evidence paths (see `engine.py`) -- this is what
    distinguishes the Mandatory Core from the rejected "every analysis
    dimension must be complete" rule."""

    M1_IDENTITY_KNOWN = "m1_identity_known"
    M2_CURRENT_ECONOMICS = "m2_current_economics"
    M3_MARKET_PRICE = "m3_market_price"
    M4_RISK_EVIDENCE = "m4_risk_evidence"


class MissingReasonCode(str, Enum):
    """Precise, deterministically-derived reasons -- never one generic
    "analysis incomplete." `INTERNAL_EVALUATION_ERROR` is categorically
    distinct from the others: it means the required evidence exists but
    an evaluator failed unexpectedly, and must never be presented as a
    normal waiting state."""

    WAITING_FOR_COMPANY_PROFILE = "waiting_for_company_profile"
    WAITING_FOR_CURRENT_ECONOMICS = "waiting_for_current_economics"
    WAITING_FOR_MARKET_PRICE = "waiting_for_market_price"
    WAITING_FOR_RISK_EVIDENCE = "waiting_for_risk_evidence"
    WAITING_FOR_RECOMMENDATION = "waiting_for_recommendation"
    INTERNAL_EVALUATION_ERROR = "internal_evaluation_error"


class EvidenceTier(str, Enum):
    """Mirrors the governing three-tier evidence model. Phase 1 has no
    real, granular Optional-enrichment signal to check against yet
    (peer comparison, earnings-call intelligence, deep filing review
    are not separately tracked anywhere in the current backend) --
    `MANDATORY_PLUS_IMPORTANT_PLUS_OPTIONAL` is kept in this enum for
    forward compatibility with the governing model, but this phase's
    own `engine.py` never produces it. That is a disclosed, honest
    limitation, not a silently-broken promise -- see `engine.py`'s own
    `evaluate_important_gaps` docstring."""

    MANDATORY_ONLY = "mandatory_only"
    MANDATORY_PLUS_IMPORTANT = "mandatory_plus_important"
    MANDATORY_PLUS_IMPORTANT_PLUS_OPTIONAL = "mandatory_plus_important_plus_optional"


@dataclass(frozen=True)
class MandatoryItemAssessment:
    """One M-item's own outcome. `satisfied_via` names which real
    evidence path satisfied it (e.g. `"growth"`, `"financial_risk"`),
    `None` when unsatisfied. `reason` is the `MissingReasonCode` to
    show when unsatisfied, `None` when satisfied."""

    item: MandatoryItemId
    satisfied: bool
    satisfied_via: str | None
    reason: MissingReasonCode | None


@dataclass(frozen=True)
class MandatoryCoreAssessment:
    """The full `M1 AND M2 AND M3 AND M4` breakdown -- always names
    every one of the four items, satisfied or not (the same "always
    name every member, never a partial list" discipline
    `atlas.analysis_engine.business.BusinessAnalysisResult` and
    `atlas.analysis_engine.risk.models.RiskAnalysisResult` already
    established for their own six/four-member results)."""

    items: tuple[MandatoryItemAssessment, ...]
    all_satisfied: bool

    def item(self, item_id: MandatoryItemId) -> MandatoryItemAssessment:
        return next(i for i in self.items if i.item is item_id)

    def satisfied_count(self) -> int:
        return sum(1 for i in self.items if i.satisfied)

    def missing_items(self) -> tuple[MandatoryItemAssessment, ...]:
        return tuple(i for i in self.items if not i.satisfied)


@dataclass(frozen=True)
class PublicationEligibility:
    """The complete Published-gate decision (Investment Case Lifecycle
    Specification, Section 2) -- never a bare pass/fail, always the
    full reasoning behind it."""

    eligible: bool
    mandatory_core: MandatoryCoreAssessment
    recommendation_exists: bool
    blocking_reason: MissingReasonCode | None


@dataclass(frozen=True)
class RegressionRecord:
    """Present only when a regression from `PUBLISHED`/
    `CONTINUOUS_MONITORING` back to `ANALYSIS_RUNNING` has occurred --
    the concrete mechanism behind "regression must never be silent."
    `invalidated_items` names exactly which M-item(s) flipped from
    satisfied to unsatisfied; never a generic "something changed."""

    occurred_at: datetime
    invalidated_items: tuple[MandatoryItemId, ...]
    reasons: tuple[MissingReasonCode, ...]


@dataclass(frozen=True)
class AtlasStatus:
    """The conceptual object the future UI will read to understand
    Atlas's own state without inferring it from null values or
    placeholder text (Investment Case Lifecycle Specification, Section
    5). Every field here describes Atlas itself -- never a claim about
    the company or the investment (that boundary is the entire point
    of this phase)."""

    case_id: str
    lifecycle_state: LifecycleState
    mandatory_core: MandatoryCoreAssessment
    evidence_tier: EvidenceTier
    important_missing_items: tuple[str, ...]
    optional_missing_items: tuple[str, ...]
    next_expected_action: str
    last_updated: datetime | None
    next_refresh_description: str
    published_since: datetime | None
    last_regression: RegressionRecord | None
    generated_at: datetime


@dataclass(frozen=True)
class LifecycleSnapshot:
    """The minimal, previous-evaluation record persisted purely for
    regression detection (`engine.detect_regression`) and to recall
    `published_since` across runs. Deliberately narrower than
    `AtlasStatus`: it omits every field that is always re-derived fresh
    on each read (`important_missing_items`, `next_expected_action`,
    `next_refresh_description`, `last_regression` itself) -- persisting
    those would risk them silently going stale, which the governing
    "always recompute live" discipline forbids."""

    case_id: str
    lifecycle_state: LifecycleState
    mandatory_core: MandatoryCoreAssessment
    published_since: datetime | None
    generated_at: datetime
