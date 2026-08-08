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
from datetime import datetime

from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.findings import FindingSeverity
from atlas.analysis_engine.provenance import Provenance
from atlas.analysis_engine.valuation.contracts import (
    ValuationAssumptionKind,
    ValuationDataGapKind,
    ValuationMethodKind,
    ValuationStatus,
)
from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel

__all__ = ["ValuationFinding", "ValuationEngineResult"]


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
