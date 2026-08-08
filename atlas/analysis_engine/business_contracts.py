"""Shared Business Analysis vocabulary (ATLAS-023) -- `BusinessCategory`,
`BusinessCategoryStatus`, `BusinessDataGapKind`, `severity_for_status`,
`BusinessFinding`, and `BusinessAnalysisResult`.

Split out of `atlas.analysis_engine.business` this sprint for a purely
structural reason: `atlas.analysis_engine.growth` and
`.capital_allocation` need these same types, and `business.py` itself
needs to import `growth.py`/`capital_allocation.py` to dispatch to them
-- importing `business.py` from either evaluator would be a circular
import. Putting the shared vocabulary in its own module, imported by
all three, breaks the cycle the same way `atlas.decision_engine
.contracts` already sits below `pipeline.py` and every file in
`stages/`, never importing either back. `business.py` re-exports every
name here via its own `__all__`, so `from atlas.analysis_engine.business
import BusinessCategory` (every pre-ATLAS-023 caller and test) keeps
working unchanged -- this is a location split, not a rename.

`business.py` remains the one and only Business Analysis *owner*: it
is still the sole place `evaluate_business_analysis` is defined and the
sole place a `BusinessAnalysisResult` is assembled. This module holds
shared shape, not shared behavior.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.findings import FindingSeverity
from atlas.analysis_engine.provenance import Provenance
from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel

__all__ = [
    "BusinessCategory",
    "BusinessCategoryStatus",
    "BusinessDataGapKind",
    "severity_for_status",
    "BusinessFinding",
    "BusinessAnalysisResult",
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
    """Categorical, five levels, never numeric -- ATLAS-021's Phase 4
    list, applied verbatim. `NOT_EVALUATED` is reserved for a future
    category with no evaluator implemented at all; every category this
    codebase ships today has a real evaluator (see `business.py`'s own
    module docstring), so `NOT_EVALUATED` is never constructed."""

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
    adapter is connected -- true for Business Model, Competitive
    Position, Management, and (absent a reused Durability signal)
    Durability, every run."""

    EXTERNAL_DATA_NOT_YET_INTERPRETED = "external_data_not_yet_interpreted"
    """`external_records` for this category is non-empty, but no
    evaluator exists yet that reads record *content* rather than
    counting records. Never constructed for Growth/Capital Allocation
    (see `growth.py`/`capital_allocation.py`, which read
    `BusinessFact`s instead); reachable for the other four categories
    only via `test_business.py`'s extensibility test."""

    # -- ATLAS-023: fact-based Growth / Capital Allocation reasons ------
    INSUFFICIENT_HISTORICAL_PERIODS = "insufficient_historical_periods"
    """Growth: zero `BusinessFactKind` relevant to this category has
    two or more periods -- no metric has enough history to compare at
    all."""

    MISSING_REVENUE_HISTORY = "missing_revenue_history"
    """Growth: fewer than two `REVENUE` facts across distinct periods."""

    MISSING_CASH_FLOW_HISTORY = "missing_cash_flow_history"
    """Growth: fewer than two `FREE_CASH_FLOW` facts across distinct
    periods."""

    MISSING_BUYBACK_DATA = "missing_buyback_data"
    """Capital Allocation: `SHARE_BUYBACKS` and/or `SHARE_ISSUANCE`
    facts are unavailable, so the capital-return signal cannot be
    computed -- covers either or both sides of that comparison being
    absent, never assumed to be zero."""

    MISSING_DEBT_DATA = "missing_debt_data"
    """Capital Allocation: `DEBT_ISSUANCE` and/or `DEBT_REPAYMENT`
    facts are unavailable, so the leverage signal cannot be computed."""

    MISSING_DIVIDEND_DATA = "missing_dividend_data"
    """Capital Allocation: no `DIVIDENDS` facts exist. Informational
    this sprint -- dividends do not yet drive `status` (see
    `atlas.analysis_engine.capital_allocation`'s own module docstring
    for why), so this reason is always present alongside whatever
    reasons do drive the outcome, never on its own."""

    MISSING_CAPEX_DATA = "missing_capex_data"
    """Capital Allocation: no `CAPITAL_EXPENDITURE` facts exist.
    Informational this sprint, same status as
    `MISSING_DIVIDEND_DATA`."""


def severity_for_status(status: BusinessCategoryStatus) -> FindingSeverity:
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

    No free-text `conclusion` field exists here, despite ATLAS-021's
    own suggested structure naming one -- the same deliberate departure
    `atlas.analysis_engine.findings.Finding` already documents:
    `status` (a closed enum) *is* the conclusion; any elaboration
    belongs in `supporting_evidence`/`contradicting_evidence`/
    `missing_evidence`, all structured, never prose. `updated_at` is
    always the caller-supplied evaluation timestamp, never a
    wall-clock read.
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
    category's own `BusinessCategoryStatus`. Always `EVALUATED` --
    assembling six conclusions, honest or real, is itself a real,
    deterministic result, the same "even an audit trail that is mostly
    'not yet assessable' is a real conclusion" principle `ReasoningResult`
    already established.

    `available_business_records` (ATLAS-022) holds the `id`s of every
    `business_data.models.BusinessRecord` made available to this
    evaluation -- case-wide, not per-category, and never folded into
    any `BusinessFinding`'s own `status` or `confidence`.
    """

    state: EvaluationState
    findings: tuple[BusinessFinding, ...]
    available_business_records: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.state is EvaluationState.EVALUATED:
            categories = {finding.kind for finding in self.findings}
            if categories != set(BusinessCategory):
                raise AnalysisEngineContractError(
                    "An EVALUATED BusinessAnalysisResult must carry a "
                    "BusinessFinding for every BusinessCategory member, "
                    "never a partial list."
                )
