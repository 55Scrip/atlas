"""Business Evaluation stage (`Doctrine` §4; Sprint 2).

Real, deterministic evaluator for two of Doctrine §4's three
dimensions — Evidence Quality (dimension 2) and Knowable vs. Assumed
(dimension 3) — built entirely from structural, id-based facts already
present in `DecisionEngineInput.observations` and
`DecisionEngineInput.evidence`: counts, presence/absence, and
cross-references between real ids. No semantic or NLP-derived judgment
about any statement's text is performed anywhere in this module.

Dimension 1, Durability, is always `INSUFFICIENT_INPUT`
(`DurabilityFinding`) — Sprint 2's own repository-discovery finding,
confirmed and locked by the sprint's own scope: `DecisionEngineInput`
carries no external company-fact, financial, or market data to reason
about competitive position or balance-sheet resilience from. This
module does not, and structurally cannot, produce a moat conclusion, a
competitive-position conclusion, a balance-sheet conclusion, a
management conclusion, a business-quality conclusion, or a
growth-quality conclusion — `DurabilityFinding` has no field any of
those could occupy.

Not to be confused with `atlas.core.domain.evaluation` — a distinct,
unrelated Core Domain Object (the Investor's own assessment of an
Outcome). This module never reads, writes, or references that Core
package.
"""
from __future__ import annotations

from atlas.core.domain.evidence.entity import Evidence
from atlas.core.domain.evidence.value_objects import Direction
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.decision_engine.contracts import (
    BusinessEvaluationResult,
    DecisionEngineInput,
    DurabilityFinding,
    DurabilityNotAssessableReason,
    EvaluationState,
    EvidenceCoverageLevel,
    EvidenceGap,
    EvidenceGapKind,
    EvidenceQualityFindings,
    ObservationEpistemicStatus,
    ObservationEvidenceClassification,
)

_DURABILITY_FINDING = DurabilityFinding(
    state=EvaluationState.INSUFFICIENT_INPUT,
    reason=DurabilityNotAssessableReason.NO_BUSINESS_FACT_DATA_IN_INPUT,
)


def _classify_observation(
    observation: Observation, evidence_by_observation: dict[ObservationId, list[Evidence]]
) -> ObservationEvidenceClassification:
    linked = evidence_by_observation.get(observation.id, [])
    supporting_count = sum(1 for item in linked if item.direction is Direction.SUPPORTS)
    challenging_count = sum(1 for item in linked if item.direction is Direction.CHALLENGES)

    if supporting_count > 0 and challenging_count > 0:
        status = ObservationEpistemicStatus.CONTRADICTED
    elif supporting_count > 0:
        status = ObservationEpistemicStatus.SUPPORTED
    elif challenging_count > 0:
        status = ObservationEpistemicStatus.CHALLENGED
    else:
        status = ObservationEpistemicStatus.ASSUMED

    return ObservationEvidenceClassification(
        observation_id=observation.id,
        status=status,
        supporting_evidence_count=supporting_count,
        challenging_evidence_count=challenging_count,
    )


def _coverage(
    observation_count: int, observations_with_evidence_count: int
) -> EvidenceCoverageLevel:
    if observation_count == 0:
        return EvidenceCoverageLevel.NOT_APPLICABLE
    if observations_with_evidence_count == 0:
        return EvidenceCoverageLevel.NONE
    if observations_with_evidence_count == observation_count:
        return EvidenceCoverageLevel.FULL
    return EvidenceCoverageLevel.PARTIAL


def _evaluate_evidence_quality(engine_input: DecisionEngineInput) -> EvidenceQualityFindings:
    evidence_by_observation: dict[ObservationId, list[Evidence]] = {}
    for item in engine_input.evidence:
        evidence_by_observation.setdefault(item.observation_id, []).append(item)

    classifications = tuple(
        _classify_observation(observation, evidence_by_observation)
        for observation in engine_input.observations
    )

    observations_with_evidence_count = sum(
        1
        for classification in classifications
        if classification.status is not ObservationEpistemicStatus.ASSUMED
    )

    gaps: list[EvidenceGap] = []
    if not engine_input.evidence:
        gaps.append(EvidenceGap(kind=EvidenceGapKind.NO_EVIDENCE_RECORDED))
    for classification in classifications:
        if classification.status is ObservationEpistemicStatus.ASSUMED:
            gaps.append(
                EvidenceGap(
                    kind=EvidenceGapKind.OBSERVATION_WITHOUT_EVIDENCE,
                    reference=str(classification.observation_id),
                )
            )
    for decision in engine_input.decisions:
        if decision.observation_id is None:
            gaps.append(
                EvidenceGap(
                    kind=EvidenceGapKind.DECISION_WITHOUT_LINKED_OBSERVATION,
                    reference=str(decision.id),
                )
            )

    supporting_evidence_count = sum(
        1 for item in engine_input.evidence if item.direction is Direction.SUPPORTS
    )
    challenging_evidence_count = sum(
        1 for item in engine_input.evidence if item.direction is Direction.CHALLENGES
    )

    return EvidenceQualityFindings(
        total_evidence_count=len(engine_input.evidence),
        supporting_evidence_count=supporting_evidence_count,
        challenging_evidence_count=challenging_evidence_count,
        coverage=_coverage(len(engine_input.observations), observations_with_evidence_count),
        observation_classifications=classifications,
        evidence_gaps=tuple(gaps),
    )


def evaluate_business(engine_input: DecisionEngineInput) -> BusinessEvaluationResult:
    """Deterministic: identical `engine_input` always produces a deeply
    equal result. No timestamp, no randomness, no UUID generation, no
    wall-clock access, no global state, no side effect."""
    return BusinessEvaluationResult(
        state=EvaluationState.EVALUATED,
        durability=_DURABILITY_FINDING,
        evidence_quality=_evaluate_evidence_quality(engine_input),
    )
