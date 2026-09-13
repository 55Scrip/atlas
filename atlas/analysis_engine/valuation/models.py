"""The canonical `ValuationFinding` and `ValuationEngineResult` (ATLAS-024,
Phase 9) -- structurally consistent with
`atlas.analysis_engine.business_contracts.BusinessFinding`/
`BusinessAnalysisResult`, by explicit instruction.

**Naming collision, disclosed once here:** `atlas.decision_engine
.contracts` already defines its own `ValuationFinding` -- permanently
locked to `INSUFFICIENT_INPUT`, with no `fair_value`/`cheap`/`expensive`
field ever ("Sprint 3 lock"). This is a *different* type in a different
module; nothing here modifies, subclasses, or reads that one. Import
both qualified (`decision_engine.contracts.ValuationFinding` vs.
`analysis_engine.valuation.models.ValuationFinding`) if a reader ever
needs to distinguish them in the same file.

**No free-text `conclusion` field**, despite Phase 9's own suggested
structure naming one -- the same deliberate departure
`atlas.analysis_engine.business_contracts.BusinessFinding` and
`atlas.analysis_engine.findings.Finding` already document: `status` (a
closed `ValuationStatus`) *is* the conclusion.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.findings import FindingSeverity
from atlas.analysis_engine.provenance import Provenance
from atlas.analysis_engine.valuation.contracts import (
    HistoricalYieldPosition,
    ShareCountMethod,
    ValuationAssumptionKind,
    ValuationDataGapKind,
    ValuationDecisionEligibility,
    ValuationFactExclusionReason,
    ValuationMethodKind,
    ValuationStatus,
)
from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel

__all__ = [
    "FcfYieldEpochObservation",
    "FcfYieldExclusion",
    "FcfYieldEvidence",
    "ValuationFinding",
    "ValuationEngineResult",
    "position_of",
]

_STATUS_FOR_POSITION = {
    HistoricalYieldPosition.ABOVE_ALL_PRIOR: ValuationStatus.UNDERVALUED,
    HistoricalYieldPosition.WITHIN_PRIOR_RANGE: ValuationStatus.FAIRLY_VALUED,
    HistoricalYieldPosition.BELOW_ALL_PRIOR: ValuationStatus.EXPENSIVE,
}


def _fail(message: str) -> None:
    raise AnalysisEngineContractError(message)


@dataclass(frozen=True)
class FcfYieldEpochObservation:
    """One fiscal valuation epoch: a fiscal year's free cash flow, priced
    by one market observation taken while that fiscal year was the latest
    one disclosed.

    `fiscal_period` is the period end the free cash flow *represents*;
    `available_from` is the earliest annual-statement filing Atlas holds
    dated after that period end -- when the figure first became public.
    `observed_on` is the market observation's own trading date, never
    before `available_from`.

    Market capitalisation is `share_price * shares_outstanding` under
    `ShareCountMethod.CURRENT_SHARE_COUNT_PROXY` -- a proxy, never an
    exact historical market capitalisation; see that member.
    """

    fiscal_period: str
    available_from: date
    observed_on: str
    free_cash_flow: float
    share_price: float
    shares_outstanding: float
    currency: str
    free_cash_flow_fact_id: str
    share_price_fact_id: str
    shares_outstanding_fact_id: str

    def __post_init__(self) -> None:
        if not (self.free_cash_flow > 0 and self.share_price > 0 and self.shares_outstanding > 0):
            _fail("An FCF-yield epoch needs positive free cash flow, price and shares.")
        if not self.available_from > date.fromisoformat(self.fiscal_period):
            _fail("A fiscal year's figures cannot be available before the fiscal year ends.")
        if date.fromisoformat(self.observed_on) < self.available_from:
            _fail("An epoch cannot be priced before its free cash flow was available (look-ahead).")
        ids = (self.free_cash_flow_fact_id, self.share_price_fact_id, self.shares_outstanding_fact_id)
        if not all(ids) or len(set(ids)) != 3:
            _fail("An FCF-yield epoch names three distinct facts.")

    @property
    def market_cap_proxy(self) -> float:
        return self.share_price * self.shares_outstanding

    @property
    def fcf_yield(self) -> float:
        return self.free_cash_flow / self.market_cap_proxy

    @property
    def fact_ids(self) -> tuple[str, str, str]:
        return (self.free_cash_flow_fact_id, self.share_price_fact_id, self.shares_outstanding_fact_id)


@dataclass(frozen=True)
class FcfYieldExclusion:
    fact_id: str
    reason: ValuationFactExclusionReason


def position_of(current_yield: float, prior_yields: tuple[float, ...]) -> HistoricalYieldPosition:
    """The unchanged ATLAS-024 comparison, in yield terms: strictly above
    every prior yield, strictly below every one, or inside the range."""
    if current_yield > max(prior_yields):
        return HistoricalYieldPosition.ABOVE_ALL_PRIOR
    if current_yield < min(prior_yields):
        return HistoricalYieldPosition.BELOW_ALL_PRIOR
    return HistoricalYieldPosition.WITHIN_PRIOR_RANGE


@dataclass(frozen=True)
class FcfYieldEvidence:
    """What the FCF-yield method compared, and whether that comparison may
    decide anything.

    `current` is the latest market observation priced against the latest
    fiscal year disclosed by then. `prior_epochs` are the earlier fiscal
    years, one observation each, oldest first -- never two observations of
    the same fiscal year, however many snapshots were taken in it.
    `consolidated_observations` are the market observation dates set aside
    because an earlier (or, for the current fiscal year, a later)
    observation already represents their fiscal year. `position` describes;
    `eligibility` decides whether the description may reach the
    recommendation.
    """

    eligibility: ValuationDecisionEligibility
    minimum_prior_epochs: int
    share_count_method: ShareCountMethod
    current: FcfYieldEpochObservation | None = None
    prior_epochs: tuple[FcfYieldEpochObservation, ...] = ()
    position: HistoricalYieldPosition | None = None
    consolidated_observations: tuple[str, ...] = ()
    excluded: tuple[FcfYieldExclusion, ...] = ()

    def __post_init__(self) -> None:
        if self.minimum_prior_epochs < 1:
            _fail("Decision use needs at least one prior fiscal epoch by construction.")
        periods = [epoch.fiscal_period for epoch in self.prior_epochs]
        if periods != sorted(set(periods)):
            _fail("Prior epochs are distinct fiscal years, oldest first.")
        if self.eligibility is ValuationDecisionEligibility.NOT_APPLICABLE:
            if self.current is not None or self.prior_epochs or self.position is not None:
                _fail("A not-applicable FCF yield carries no observations.")
            return
        if self.current is not None and any(p >= self.current.fiscal_period for p in periods):
            _fail("Every prior epoch precedes the current fiscal year.")
        expected_position = (
            position_of(self.current.fcf_yield, self.prior_yields)
            if self.current is not None and self.prior_epochs else None
        )
        if self.position is not expected_position:
            _fail("The historical position must be the one the observations imply.")
        if self.current is None or not self.prior_epochs:
            expected = ValuationDecisionEligibility.INSUFFICIENT
        elif len(self.prior_epochs) < self.minimum_prior_epochs:
            expected = ValuationDecisionEligibility.LIMITED
        else:
            expected = ValuationDecisionEligibility.ELIGIBLE
        if self.eligibility is not expected:
            _fail(f"Eligibility {self.eligibility.value} contradicts the evidence ({expected.value}).")

    @property
    def prior_yields(self) -> tuple[float, ...]:
        return tuple(epoch.fcf_yield for epoch in self.prior_epochs)

    @property
    def prior_epoch_count(self) -> int:
        return len(self.prior_epochs)

    @property
    def earliest_prior_epoch(self) -> str | None:
        return self.prior_epochs[0].fiscal_period if self.prior_epochs else None

    @property
    def latest_prior_epoch(self) -> str | None:
        return self.prior_epochs[-1].fiscal_period if self.prior_epochs else None

    @property
    def span_years(self) -> float | None:
        """Fiscal years covered, earliest prior epoch to the current one."""
        if self.current is None or not self.prior_epochs:
            return None
        days = (date.fromisoformat(self.current.fiscal_period) - date.fromisoformat(self.prior_epochs[0].fiscal_period)).days
        return round(days / 365.25, 2)

    @property
    def decision_status(self) -> ValuationStatus:
        """The only status the recommendation may act on."""
        if self.eligibility is ValuationDecisionEligibility.ELIGIBLE and self.position is not None:
            return _STATUS_FOR_POSITION[self.position]
        return ValuationStatus.INSUFFICIENT_INPUT


@dataclass(frozen=True)
class ValuationFinding:
    """One method's structured, canonical conclusion.

    `supporting_facts`/`contradicting_facts` name real
    `ValuationFact`/`business_facts.BusinessFact` ids -- opaque
    reference strings, the same convention `BusinessFinding` already
    uses. `assumptions` is always `()` this sprint (see module and
    `atlas.analysis_engine.valuation.contracts.ValuationAssumptionKind`'s
    own docstrings for why); kept as a real field now so a future
    scenario-assumption input mechanism does not need a shape change.
    """

    id: str
    kind: ValuationMethodKind
    status: ValuationStatus
    severity: FindingSeverity
    supporting_facts: tuple[str, ...]
    contradicting_facts: tuple[str, ...]
    assumptions: tuple[ValuationAssumptionKind, ...]
    missing_evidence: tuple[ValuationDataGapKind, ...]
    confidence: EvidenceCoverageLevel
    provenance: Provenance
    evaluated_at: datetime
    current_yield: float | None = None
    """(ATLAS-032) The most recent market observation's own FCF yield
    (latest eligible Free Cash Flow ÷ that observation's market cap),
    populated whenever it is genuinely computable -- including when
    `status` stays `INSUFFICIENT_INPUT` for lack of historical periods
    to classify it against. Not a generic "score": one specific, named,
    unit-explicit ratio (FCF / market cap), real and traceable via
    `supporting_facts` whenever set, `None` when no current observation
    exists at all. Only `FCF_YIELD_RELATIVE` ever populates this; the
    scenario methods leave it `None`."""
    historical_yields: tuple[float, ...] = ()
    """(Outlook Intelligence Sprint 1) Every *other* valid market
    observation's own FCF yield -- i.e. `cash_flow.py`'s own
    `historical` dict, exposed rather than discarded after it decides
    `UNDERVALUED`/`FAIRLY_VALUED`/`EXPENSIVE`. Populated only when the
    relative classification itself is reachable (two or more valid
    observations); empty otherwise, including when only `current_yield`
    is real. This is not a new assumption or a new method -- it is the
    exact evidence `FCF_YIELD_RELATIVE` already computes and already
    relies on for its own real conclusion, now surfaced so
    `atlas.analysis_engine.outlook` can derive a real re-rating range
    (reversion toward this company's own recorded historical yields)
    without recomputing raw facts or inventing a forward growth,
    discount-rate, or terminal-multiple assumption (see
    `atlas.analysis_engine.valuation.scenarios`'s own module docstring
    for why that kind of assumption is refused). Only `FCF_YIELD_RELATIVE`
    ever populates this; the scenario methods leave it empty.

    (Valuation Observation Integrity) One yield per *prior fiscal epoch*,
    and only when that history is decision-eligible -- every consumer
    reading this field (Outlook, Valuation Support, the reasoning's
    percentile) therefore only ever sees history deep enough to decide
    on. Thinner history stays describable on `fcf_yield_evidence`."""
    fcf_yield_evidence: FcfYieldEvidence | None = None
    """(Valuation Observation Integrity) The epochs behind this finding
    and their decision eligibility. Always set by the production
    `FCF_YIELD_RELATIVE` evaluator; `None` for the scenario methods (and
    hand-built legacy fixtures)."""

    def __post_init__(self) -> None:
        evidence = self.fcf_yield_evidence
        if evidence is None:
            return
        if self.kind is not ValuationMethodKind.FCF_YIELD_RELATIVE:
            _fail("Only the FCF-yield finding carries FCF-yield evidence.")
        if self.status is not evidence.decision_status:
            _fail(
                f"Status {self.status.value} is not what the evidence permits "
                f"({evidence.decision_status.value}): only decision-eligible history classifies."
            )
        expected_current = evidence.current.fcf_yield if evidence.current is not None else None
        if self.current_yield != expected_current:
            _fail("current_yield must be the current epoch's own yield.")
        expected_history = (
            tuple(sorted(evidence.prior_yields))
            if evidence.eligibility is ValuationDecisionEligibility.ELIGIBLE else ()
        )
        if self.historical_yields != expected_history:
            _fail("historical_yields carries decision-eligible prior epochs only.")
        if (evidence.eligibility is ValuationDecisionEligibility.NOT_APPLICABLE) != (
            ValuationDataGapKind.VALUATION_METHOD_NOT_APPLICABLE in self.missing_evidence
        ):
            _fail("Not-applicable is stated by exactly one gap.")


@dataclass(frozen=True)
class ValuationEngineResult:
    """The stage-level wrapper -- mirrors
    `atlas.analysis_engine.business_contracts.BusinessAnalysisResult`'s
    own `state` tier exactly. Always `EVALUATED`: assembling four
    honest conclusions (one real, three structurally
    `INSUFFICIENT_INPUT` this sprint) is itself a real, deterministic
    result.

    Deliberately has **no top-level summary `status` field** -- mirrors
    `BusinessAnalysisResult`'s own choice not to collapse six categories
    into one number; a caller that wants "the" valuation reads
    `findings` and inspects `ValuationMethodKind.FCF_YIELD_RELATIVE`'s
    own finding directly (see `pipeline.assemble_analysis`'s Conviction
    wiring for exactly this pattern).
    """

    state: EvaluationState
    findings: tuple[ValuationFinding, ...]

    def __post_init__(self) -> None:
        if self.state is EvaluationState.EVALUATED:
            kinds = {finding.kind for finding in self.findings}
            if kinds != set(ValuationMethodKind):
                raise AnalysisEngineContractError(
                    "An EVALUATED ValuationEngineResult must carry a "
                    "ValuationFinding for every ValuationMethodKind member, "
                    "never a partial list."
                )
