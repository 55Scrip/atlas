"""Thesis Risk evaluator v1 (ATLAS-025, Phase 9/15).

**Phase 15's architecture decision, made explicit here.** ATLAS-020's
`pipeline.py::_build_findings` already builds one generic `Finding`
(`FindingKind.CONTRADICTING_EVIDENCE`, tagged
`details["risk_category"] = "thesis_risk"`) per contradicted
`ObservationEvidenceClassification` -- that mechanism is **preserved
exactly as-is**, zero regression, since it is already tested and real.
This module *adds* what that mechanism never had: one real, categorical
`RiskStatus` conclusion for `RiskCategory.THESIS_RISK`, the same shape
every other Risk category now has -- reusing the identical
`ContradictionSummary`, never a second, independent scan for
contradictions. The per-observation Findings and this one summary
`RiskFinding` are two views of the same underlying fact, not competing
computations.

**The rule table, documented before it was implemented:**

1. Case-wide `EvidenceCoverageLevel` (the same value already threaded
   through every `Finding.confidence` in `pipeline.py`) is
   `NOT_APPLICABLE` or `NONE` -> `RiskStatus.INSUFFICIENT_INPUT`. There
   is no Evidence recorded to check for contradiction at all -- a
   fundamentally different fact from "checked, found none," and Phase
   10's own instruction against a generic "more information needed"
   answer when the real gap is known.
2. Otherwise (coverage is `PARTIAL`/`FULL`), `contradicting_evidence
   .observation_classifications` is non-empty -> `RiskStatus.HIGH` --
   at least one Observation has real challenging Evidence against it.
3. Otherwise -> `RiskStatus.LOW` -- Evidence exists and was checked;
   none of it contradicts the recorded thesis.

No `MODERATE` tier: this is fundamentally a binary "checked, found a
contradiction or not," once evidence exists to check at all.
"""
from __future__ import annotations

from datetime import datetime

from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.risk.contracts import RiskDataGapKind, RiskStatus, severity_for_risk_status
from atlas.analysis_engine.risk.models import RiskFinding
from atlas.decision_engine.contracts import ContradictionSummary, EvidenceCoverageLevel

__all__ = ["evaluate_thesis_risk"]

_ALL_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)

_NO_EVIDENCE_COVERAGE = (EvidenceCoverageLevel.NOT_APPLICABLE, EvidenceCoverageLevel.NONE)


def evaluate_thesis_risk(
    contradicting_evidence: ContradictionSummary,
    *,
    evidence_coverage: EvidenceCoverageLevel,
    evaluated_at: datetime,
) -> RiskFinding:
    """Deterministic: identical inputs always produce a deeply equal
    `RiskFinding`. Reads only the already-computed `ContradictionSummary`
    and case-wide `EvidenceCoverageLevel` -- never a Core Evidence/
    Observation record directly, never a second classification pass.
    """
    contradicted = tuple(
        str(classification.observation_id)
        for classification in contradicting_evidence.observation_classifications
    )

    if evidence_coverage in _NO_EVIDENCE_COVERAGE:
        status = RiskStatus.INSUFFICIENT_INPUT
        missing = (RiskDataGapKind.NO_EVIDENCE_TO_EVALUATE,)
    elif contradicted:
        status = RiskStatus.HIGH
        missing = ()
    else:
        status = RiskStatus.LOW
        missing = ()

    return RiskFinding(
        id=f"risk_finding:{RiskCategory.THESIS_RISK.value}",
        category=RiskCategory.THESIS_RISK,
        status=status,
        severity=severity_for_risk_status(status),
        supporting_facts=(),
        contradicting_facts=contradicted,
        missing_evidence=missing,
        confidence=evidence_coverage,
        provenance=Provenance(
            source_kind=SourceKind.DECISION_ENGINE_STAGE,
            source_references=contradicted,
            dependencies=contradicted,
            update_trigger=UpdateTrigger.NEW_EVIDENCE_RECORDED,
            consumers=_ALL_CONSUMERS,
            computed_at=evaluated_at,
        ),
        evaluated_at=evaluated_at,
    )
