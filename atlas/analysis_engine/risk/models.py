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
from atlas.analysis_engine.risk.contracts import RiskDataGapKind, RiskStatus
from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel

__all__ = ["EVALUATED_RISK_CATEGORIES", "RiskFinding", "RiskAnalysisResult"]

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
