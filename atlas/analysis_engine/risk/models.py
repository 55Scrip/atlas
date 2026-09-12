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
    FinancialRiskMetric,
    FinancialRiskRule,
    FinancialRiskSignal,
    RiskDataGapKind,
    RiskStatus,
)
from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel

__all__ = [
    "EVALUATED_RISK_CATEGORIES",
    "FinancialRiskBasis",
    "FinancialRiskObservation",
    "FinancialRiskSignalBasis",
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


#: Every condition belongs to exactly one signal and implies exactly one
#: signal level -- `financial_risk.py`'s own rule table, indexed.
_CONDITION_SIGNAL_LEVEL: dict[FinancialRiskCondition, tuple[FinancialRiskSignal, RiskStatus]] = {
    FinancialRiskCondition.CAPITAL_ALLOCATION_WEAK: (FinancialRiskSignal.CAPITAL_ALLOCATION, RiskStatus.HIGH),
    FinancialRiskCondition.CAPITAL_ALLOCATION_MODERATE: (FinancialRiskSignal.CAPITAL_ALLOCATION, RiskStatus.MODERATE),
    FinancialRiskCondition.CAPITAL_ALLOCATION_STRONG: (FinancialRiskSignal.CAPITAL_ALLOCATION, RiskStatus.LOW),
    FinancialRiskCondition.CAPITAL_ALLOCATION_UNAVAILABLE:
        (FinancialRiskSignal.CAPITAL_ALLOCATION, RiskStatus.INSUFFICIENT_INPUT),
    FinancialRiskCondition.LATEST_FREE_CASH_FLOW_NEGATIVE: (FinancialRiskSignal.CASH_GENERATION, RiskStatus.HIGH),
    FinancialRiskCondition.LATEST_FREE_CASH_FLOW_NOT_NEGATIVE: (FinancialRiskSignal.CASH_GENERATION, RiskStatus.LOW),
    FinancialRiskCondition.NO_FREE_CASH_FLOW: (FinancialRiskSignal.CASH_GENERATION, RiskStatus.INSUFFICIENT_INPUT),
    FinancialRiskCondition.TOTAL_DEBT_INCREASED_EVERY_PERIOD: (FinancialRiskSignal.DEBT_TREND, RiskStatus.HIGH),
    FinancialRiskCondition.TOTAL_DEBT_DECREASED_EVERY_PERIOD: (FinancialRiskSignal.DEBT_TREND, RiskStatus.LOW),
    FinancialRiskCondition.TOTAL_DEBT_NO_CONSISTENT_DIRECTION:
        (FinancialRiskSignal.DEBT_TREND, RiskStatus.INSUFFICIENT_INPUT),
    FinancialRiskCondition.TOTAL_DEBT_FEWER_THAN_TWO_PERIODS:
        (FinancialRiskSignal.DEBT_TREND, RiskStatus.INSUFFICIENT_INPUT),
}

_SIGNAL_METRIC = {
    FinancialRiskSignal.CAPITAL_ALLOCATION: None,
    FinancialRiskSignal.CASH_GENERATION: FinancialRiskMetric.FREE_CASH_FLOW,
    FinancialRiskSignal.DEBT_TREND: FinancialRiskMetric.TOTAL_DEBT,
}

_RULE_LEVEL = {
    FinancialRiskRule.ANY_SIGNAL_HIGH: RiskStatus.HIGH,
    FinancialRiskRule.NO_CORE_SIGNAL_ASSESSED: RiskStatus.INSUFFICIENT_INPUT,
    FinancialRiskRule.CORE_SIGNALS_BOTH_LOW: RiskStatus.LOW,
    FinancialRiskRule.CORE_SIGNAL_NOT_LOW: RiskStatus.MODERATE,
}

_SIGNAL_ORDER = tuple(FinancialRiskSignal)
_CORE_SIGNALS = (FinancialRiskSignal.CAPITAL_ALLOCATION, FinancialRiskSignal.CASH_GENERATION)


@dataclass(frozen=True)
class FinancialRiskObservation:
    """One reported figure a Financial Risk signal read, exactly as the
    `BusinessFact` states it -- metric, period end, value and unit, plus
    the fact and source record it came from. Never rescaled, never
    combined with another figure."""

    metric: FinancialRiskMetric
    period: str
    value: float
    unit: str
    fact_id: str
    source_record_id: str


@dataclass(frozen=True)
class FinancialRiskSignalBasis:
    """What one signal concluded and on what: its level, the branch of its
    rule that matched, and the observations (or upstream finding) it read.

    The condition must be literally true of the observations carried --
    "increased every period" over figures that did not increase is
    rejected at construction, so a basis cannot describe more than its
    own evidence shows."""

    signal: FinancialRiskSignal
    level: RiskStatus
    condition: FinancialRiskCondition
    observations: tuple[FinancialRiskObservation, ...] = ()
    source_finding_id: str | None = None

    def __post_init__(self) -> None:
        if _CONDITION_SIGNAL_LEVEL[self.condition] != (self.signal, self.level):
            raise AnalysisEngineContractError(
                f"{self.condition.value} is not a {self.level.value} {self.signal.value} condition."
            )
        metric = _SIGNAL_METRIC[self.signal]
        if any(o.metric is not metric for o in self.observations):
            raise AnalysisEngineContractError(f"{self.signal.value} reads only {metric} observations.")
        if (self.source_finding_id is not None) != (self.signal is FinancialRiskSignal.CAPITAL_ALLOCATION):
            raise AnalysisEngineContractError("Only the capital allocation signal restates an upstream finding.")
        values = [o.value for o in self.observations]
        periods = [o.period for o in self.observations]
        condition = self.condition
        if periods != sorted(periods):
            raise AnalysisEngineContractError("Observations are carried in period order.")
        if condition in (FinancialRiskCondition.LATEST_FREE_CASH_FLOW_NEGATIVE,
                         FinancialRiskCondition.LATEST_FREE_CASH_FLOW_NOT_NEGATIVE):
            negative = condition is FinancialRiskCondition.LATEST_FREE_CASH_FLOW_NEGATIVE
            if len(values) != 1 or (values[0] < 0) is not negative:
                raise AnalysisEngineContractError(f"{condition.value} does not describe its observation.")
        if condition is FinancialRiskCondition.NO_FREE_CASH_FLOW and values:
            raise AnalysisEngineContractError("no_free_cash_flow carries no observation.")
        if condition in (FinancialRiskCondition.TOTAL_DEBT_INCREASED_EVERY_PERIOD,
                         FinancialRiskCondition.TOTAL_DEBT_DECREASED_EVERY_PERIOD):
            pairs = list(zip(values, values[1:]))
            rising = condition is FinancialRiskCondition.TOTAL_DEBT_INCREASED_EVERY_PERIOD
            if not pairs or not all((b > a) if rising else (b < a) for a, b in pairs):
                raise AnalysisEngineContractError(f"{condition.value} does not describe its observations.")
        if condition is FinancialRiskCondition.TOTAL_DEBT_FEWER_THAN_TWO_PERIODS and len(values) >= 2:
            raise AnalysisEngineContractError("total_debt_fewer_than_two_periods carries at most one observation.")


@dataclass(frozen=True)
class FinancialRiskBasis:
    """Why Financial Risk reached its level -- the evaluator's own
    evidence, retained as it decided, never reconstructed afterwards.

    `signals` always names all three signals in rule-table order, firing
    or not. `determining` names the ones the matched `rule` turned on:
    for `HIGH`, every `HIGH` signal and nothing else -- none netted
    against another, none promoted to a main reason. A signal outside
    `determining` is context, never a cause.

    Describes reported history only: absolute figures for the periods
    Atlas holds. No ratio, rating, coverage or forecast is in it."""

    level: RiskStatus
    rule: FinancialRiskRule
    signals: tuple[FinancialRiskSignalBasis, ...]
    determining: tuple[FinancialRiskSignal, ...]

    def __post_init__(self) -> None:
        if tuple(s.signal for s in self.signals) != _SIGNAL_ORDER:
            raise AnalysisEngineContractError("A Financial Risk basis names every signal once, in rule order.")
        if _RULE_LEVEL[self.rule] is not self.level:
            raise AnalysisEngineContractError(f"{self.rule.value} does not decide {self.level.value}.")
        levels = {s.signal: s.level for s in self.signals}
        core = {levels[s] for s in _CORE_SIGNALS}
        determining = self.determining
        matches = {
            FinancialRiskRule.ANY_SIGNAL_HIGH: RiskStatus.HIGH in levels.values(),
            FinancialRiskRule.NO_CORE_SIGNAL_ASSESSED: core == {RiskStatus.INSUFFICIENT_INPUT},
            FinancialRiskRule.CORE_SIGNALS_BOTH_LOW: core == {RiskStatus.LOW},
            FinancialRiskRule.CORE_SIGNAL_NOT_LOW: core not in ({RiskStatus.LOW}, {RiskStatus.INSUFFICIENT_INPUT}),
        }
        # First match wins: the rule named must be the first one its
        # signals satisfy, or the basis would describe a different level.
        first = next(rule for rule in FinancialRiskRule if matches[rule])
        if first is not self.rule:
            raise AnalysisEngineContractError(f"These signals decide {first.value}, not {self.rule.value}.")
        if self.rule is FinancialRiskRule.ANY_SIGNAL_HIGH:
            expected = tuple(s for s in _SIGNAL_ORDER if levels[s] is RiskStatus.HIGH)
        elif self.rule is FinancialRiskRule.CORE_SIGNAL_NOT_LOW:
            expected = tuple(s for s in _CORE_SIGNALS if levels[s] is not RiskStatus.LOW)
        else:
            expected = _CORE_SIGNALS
        if not expected or determining != expected:
            raise AnalysisEngineContractError(f"{self.rule.value} does not rest on {[s.value for s in determining]}.")

    def signal(self, signal: FinancialRiskSignal) -> FinancialRiskSignalBasis:
        return next(s for s in self.signals if s.signal is signal)


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
