"""The canonical `RiskFinding` and `RiskAnalysisResult` (ATLAS-025,
Phase 4/13) -- structurally consistent with
`atlas.analysis_engine.business_contracts.BusinessFinding`/
`BusinessAnalysisResult` and
`atlas.analysis_engine.valuation.models.ValuationFinding`/
`ValuationEngineResult`, by explicit instruction.

**No free-text field**, same departure `BusinessFinding` and
`ValuationFinding` already document: `status` (a closed `RiskStatus`)
*is* the conclusion.

**No aggregate risk label.** Phase 13 explicitly permits omitting one --
"may be better to omit the aggregate label entirely in v1. Be
conservative." `RiskAnalysisResult` has no top-level `overall_status`,
the same choice `ValuationEngineResult` already made for its own four
methods: a caller that wants "the" answer for one category reads
`findings` and inspects that `RiskCategory`'s own Finding directly.
Collapsing four independent categories into one number is exactly the
"weighted aggregate" this sprint forbids.

**Not every `RiskCategory` gets a Finding.** Unlike
`BusinessAnalysisResult`/`ValuationEngineResult` (which always name
every member of their own six/four-member taxonomy), `RiskAnalysisResult
.findings` names only the categories this sprint built a real evaluator
for -- `BUSINESS_RISK`, `FINANCIAL_RISK`, `VALUATION_RISK`, `THESIS_RISK`.
The other six `RiskCategory` members stay real, named, and simply absent
from this tuple (Phase 3's own instruction: "Do not implement all
categories... do not implement unsupported categories merely to
complete a taxonomy"), the same "empty/absent is a real, honest state"
principle used everywhere else in this codebase.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.findings import FindingSeverity
from atlas.analysis_engine.provenance import Provenance
from atlas.analysis_engine.risk.contracts import (
    FinancialRiskCondition,
    FinancialRiskExclusionReason,
    FinancialRiskMeasure,
    RiskDataGapKind,
    RiskStatus,
)
from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel

__all__ = [
    "EVALUATED_RISK_CATEGORIES",
    "DebtBurdenBands",
    "DebtBurdenObservation",
    "FinancialRiskBasis",
    "FinancialRiskExclusion",
    "RiskFinding",
    "RiskAnalysisResult",
    "RiskProjection",
]

#: The only `RiskCategory` members ATLAS-025 builds a real evaluator for.
#: See this module's own docstring for why the other six are absent
#: rather than padded out with placeholder `NOT_EVALUATED` Findings.
EVALUATED_RISK_CATEGORIES = frozenset(
    {
        RiskCategory.BUSINESS_RISK,
        RiskCategory.FINANCIAL_RISK,
        RiskCategory.VALUATION_RISK,
        RiskCategory.THESIS_RISK,
    }
)


_CONDITION_LEVEL: dict[FinancialRiskCondition, RiskStatus] = {
    FinancialRiskCondition.DEBT_BURDEN_LOW: RiskStatus.LOW,
    FinancialRiskCondition.DEBT_BURDEN_MODERATE: RiskStatus.MODERATE,
    FinancialRiskCondition.DEBT_BURDEN_HIGH: RiskStatus.HIGH,
    FinancialRiskCondition.OPERATING_CASH_FLOW_NEGATIVE: RiskStatus.HIGH,
    FinancialRiskCondition.OPERATING_CASH_FLOW_ZERO: RiskStatus.HIGH,
    FinancialRiskCondition.MEASURE_NOT_APPLICABLE: RiskStatus.NOT_APPLICABLE,
    FinancialRiskCondition.NO_ELIGIBLE_EVIDENCE: RiskStatus.INSUFFICIENT_INPUT,
}

_BURDEN_CONDITIONS = frozenset({
    FinancialRiskCondition.DEBT_BURDEN_LOW,
    FinancialRiskCondition.DEBT_BURDEN_MODERATE,
    FinancialRiskCondition.DEBT_BURDEN_HIGH,
})


@dataclass(frozen=True)
class DebtBurdenBands:
    """Atlas policy bands for gross debt / operating cash flow -- where
    "low" ends and "high" begins. Product policy chosen on the evidence
    Atlas holds, **not credit-rating thresholds** and not a claim about
    what any lender or agency would consider safe. Carried in every basis
    so the classification can always be re-read against the exact
    policy that produced it."""

    low_below: float
    high_from: float

    def __post_init__(self) -> None:
        if not 0 < self.low_below < self.high_from:
            raise AnalysisEngineContractError("Debt-burden bands must satisfy 0 < low_below < high_from.")

    def condition_for(self, ratio: float) -> FinancialRiskCondition:
        if ratio >= self.high_from:
            return FinancialRiskCondition.DEBT_BURDEN_HIGH
        if ratio < self.low_below:
            return FinancialRiskCondition.DEBT_BURDEN_LOW
        return FinancialRiskCondition.DEBT_BURDEN_MODERATE


@dataclass(frozen=True)
class DebtBurdenObservation:
    """One fiscal period's debt burden, from three facts that share the
    period end and the unit: reported total debt, free cash flow and
    capital expenditure. Operating cash flow is derived here, not stored
    as a fact of its own: free cash flow plus capital expenditure, the
    identity the statement provider built free cash flow from.

    `ratio` is `None` exactly when operating cash flow is not positive --
    Atlas never divides by zero or by a negative figure, and never caps a
    large ratio: a small positive operating cash flow yields the large
    number it truly is."""

    period: str
    unit: str
    total_debt: float
    free_cash_flow: float
    capital_expenditure: float
    total_debt_fact_id: str
    free_cash_flow_fact_id: str
    capital_expenditure_fact_id: str
    source_record_ids: tuple[str, ...]

    @property
    def operating_cash_flow(self) -> float:
        return self.free_cash_flow + self.capital_expenditure

    @property
    def ratio(self) -> float | None:
        ocf = self.operating_cash_flow
        return self.total_debt / ocf if ocf > 0 else None

    @property
    def fact_ids(self) -> tuple[str, str, str]:
        return (self.total_debt_fact_id, self.free_cash_flow_fact_id, self.capital_expenditure_fact_id)

    def __post_init__(self) -> None:
        if not self.source_record_ids or len(set(self.fact_ids)) != 3:
            raise AnalysisEngineContractError("A debt-burden observation names its three facts and their sources.")


@dataclass(frozen=True)
class FinancialRiskExclusion:
    """A debt or cash-flow fact left out before anything was computed."""

    fact_id: str
    reason: FinancialRiskExclusionReason


@dataclass(frozen=True)
class FinancialRiskBasis:
    """Why Financial Risk v2 reached its level -- the evaluator's own
    evidence, retained as it decided.

    - `latest` is the observation the level rests on (absent for
      `NOT_APPLICABLE`/`INSUFFICIENT_INPUT`); `history` is every aligned
      observation up to three, oldest first, ending with `latest`. The
      earlier ones are **trend context only**: they never move the level.
    - `gaps` says why no level could be reached; `excluded` names the
      facts the eligibility gates removed, so a left-out figure is
      visible rather than silently absent.
    - `industry` is the profile label the applicability gate read.

    Describes reported history only: gross debt and cash from operations
    for periods Atlas holds. No rating, maturity, interest cost, liquidity
    or forecast is in it."""

    level: RiskStatus
    condition: FinancialRiskCondition
    bands: DebtBurdenBands
    measure: FinancialRiskMeasure | None = None
    latest: DebtBurdenObservation | None = None
    history: tuple[DebtBurdenObservation, ...] = ()
    industry: str | None = None
    gaps: tuple[RiskDataGapKind, ...] = ()
    excluded: tuple[FinancialRiskExclusion, ...] = ()

    def __post_init__(self) -> None:
        if _CONDITION_LEVEL[self.condition] is not self.level:
            raise AnalysisEngineContractError(f"{self.condition.value} does not decide {self.level.value}.")
        periods = [o.period for o in self.history]
        if periods != sorted(set(periods)) or len(self.history) > 3:
            raise AnalysisEngineContractError("History is at most three distinct periods, oldest first.")
        rests_on_latest = self.level not in (RiskStatus.NOT_APPLICABLE, RiskStatus.INSUFFICIENT_INPUT)
        if rests_on_latest != (self.latest is not None) or self.history[-1:] != ((self.latest,) if self.latest else ()):
            # Without a level there is no history either: a stale or
            # misaligned figure is reported as a gap, never shown as context.
            raise AnalysisEngineContractError("A level rests on the latest observation, which ends the history.")
        if rests_on_latest != (self.measure is FinancialRiskMeasure.GROSS_DEBT_TO_OPERATING_CASH_FLOW):
            raise AnalysisEngineContractError("Exactly the levels resting on an observation name the measure.")
        if (self.level is RiskStatus.INSUFFICIENT_INPUT) != bool(self.gaps):
            raise AnalysisEngineContractError("Gaps explain an insufficient level and nothing else.")
        latest = self.latest
        if latest is None:
            return
        ocf = latest.operating_cash_flow
        if self.condition in _BURDEN_CONDITIONS:
            if latest.ratio is None or self.bands.condition_for(latest.ratio) is not self.condition:
                raise AnalysisEngineContractError(f"{self.condition.value} does not describe the latest ratio.")
        elif (self.condition is FinancialRiskCondition.OPERATING_CASH_FLOW_NEGATIVE) != (ocf < 0) or \
                (self.condition is FinancialRiskCondition.OPERATING_CASH_FLOW_ZERO) != (ocf == 0):
            raise AnalysisEngineContractError(f"{self.condition.value} does not describe the latest cash flow.")


@dataclass(frozen=True)
class RiskFinding:
    """One category's structured, canonical conclusion.

    `supporting_facts`/`contradicting_facts` name real upstream ids --
    for the three evaluators built from an already-computed
    `BusinessFinding`/`ValuationFinding` (Business, Financial, Valuation
    Risk), these are that Finding's own `id` plus, where the evaluator
    reads one directly, a raw `BusinessFact` id (Financial Risk's own
    cash-generation check). For Thesis Risk they are the contradicted
    `ObservationEvidenceClassification.observation_id` values, reused
    verbatim from `ContradictionSummary`. Never a second, independently
    recomputed judgment -- Risk Analysis interprets what an earlier
    stage already established (Phase 8/9's own explicit rule), it never
    re-derives it.
    """

    id: str
    category: RiskCategory
    status: RiskStatus
    severity: FindingSeverity
    supporting_facts: tuple[str, ...]
    contradicting_facts: tuple[str, ...]
    missing_evidence: tuple[RiskDataGapKind, ...]
    confidence: EvidenceCoverageLevel
    provenance: Provenance
    evaluated_at: datetime
    #: Financial Risk only: the evaluator's own basis for `status`,
    #: retained in the same pass that decided it. Explanatory -- nothing
    #: that decides a level, a direction or a driver reads it. `None` on
    #: every other category, which states its basis in `supporting_facts`.
    financial_risk_basis: FinancialRiskBasis | None = None

    def __post_init__(self) -> None:
        basis = self.financial_risk_basis
        if basis is None:
            return
        if self.category is not RiskCategory.FINANCIAL_RISK:
            raise AnalysisEngineContractError("Only a Financial Risk finding carries a Financial Risk basis.")
        if basis.level is not self.status:
            raise AnalysisEngineContractError(
                f"A {self.status.value} Financial Risk finding cannot rest on a {basis.level.value} basis."
            )


@dataclass(frozen=True)
class RiskAnalysisResult:
    """The stage-level wrapper -- mirrors `BusinessAnalysisResult`'s and
    `ValuationEngineResult`'s own `state` tier exactly. Always
    `EVALUATED`: assembling four honest, independent conclusions is
    itself a real, deterministic result."""

    state: EvaluationState
    findings: tuple[RiskFinding, ...]

    def __post_init__(self) -> None:
        if self.state is EvaluationState.EVALUATED:
            categories = {finding.category for finding in self.findings}
            if categories != EVALUATED_RISK_CATEGORIES:
                raise AnalysisEngineContractError(
                    "An EVALUATED RiskAnalysisResult must carry exactly "
                    "one RiskFinding per category in EVALUATED_RISK_CATEGORIES, "
                    "never a partial or padded-out list."
                )


@dataclass(frozen=True)
class RiskProjection:
    """The single highest-severity `RiskCategory` among
    `EVALUATED_RISK_CATEGORIES`, for compact display only -- a
    projection, explicitly never an aggregate score. Severity order:
    `HIGH > MODERATE > LOW > INSUFFICIENT_INPUT`. Ties are broken by
    `RiskCategory`'s own declared enum order (never an invented
    priority) -- deterministic, not arbitrary.

    Originally `atlas.alpha.portfolio_cockpit.models.RiskProjection`
    (ATLAS-028 Phase 8); relocated here so `atlas.alpha.investment_case`
    can reuse the same real projection for its own Atlas View scorecard
    without creating a package cycle (`investment_case` cannot import
    from `portfolio_cockpit`, which itself depends on `investment_case`
    at the service layer) -- both Alpha packages already depend on
    `analysis_engine`, so this is its correct shared home."""

    category: RiskCategory
    status: RiskStatus
