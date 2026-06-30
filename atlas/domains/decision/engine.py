from collections import defaultdict

from atlas.domains.decision.models import (
    Confidence,
    DecisionCard,
    DecisionContext,
    DecisionResult,
    Evidence,
    EvidenceCategory,
    EvidenceStrength,
    Observation,
    ReasoningStep,
    Unknown,
)


class EvidenceEngine:
    """Collect and normalize factual evidence for decision reasoning."""

    def collect(self, context: DecisionContext) -> tuple[Evidence, ...]:
        return tuple(sorted(context.evidence, key=lambda item: (item.category.value, item.id)))


class ReasoningEngine:
    """Transform factual evidence into observations and explainable reasoning."""

    def reason(self, context: DecisionContext) -> DecisionResult:
        evidence = EvidenceEngine().collect(context)
        observations = _observations_from_evidence(evidence)
        unknowns = _unknowns_from_context(context, evidence)
        reasoning_steps = _reasoning_steps(observations)
        confidence = _confidence(evidence, unknowns)
        explanation = _explanation(reasoning_steps, unknowns, confidence)
        return DecisionResult(
            decision=context.decision,
            evidence=evidence,
            observations=observations,
            reasoning_steps=reasoning_steps,
            unknowns=unknowns,
            confidence=confidence,
            explanation=explanation,
        )


class DecisionEngine:
    """Create explainable non-advisory decision cards."""

    def __init__(self, reasoning_engine: ReasoningEngine | None = None) -> None:
        self.reasoning_engine = reasoning_engine or ReasoningEngine()

    def evaluate(self, context: DecisionContext) -> DecisionCard:
        result = self.reasoning_engine.reason(context)
        risks = tuple(
            observation.statement
            for observation in result.observations
            if observation.category == EvidenceCategory.RISK
            or "concentration" in observation.statement.lower()
            or "uncertain" in observation.statement.lower()
        )
        return DecisionCard(
            summary=_summary(result),
            evidence=result.evidence,
            key_observations=result.observations,
            unknowns=result.unknowns,
            confidence=result.confidence,
            risks=risks,
            explanation=result.explanation,
        )


def _observations_from_evidence(evidence: tuple[Evidence, ...]) -> tuple[Observation, ...]:
    observations: list[Observation] = []
    for index, item in enumerate(evidence, start=1):
        observations.append(
            Observation(
                id=f"observation-{index:03d}",
                category=item.category,
                statement=f"{item.category.value} evidence states: {item.statement}",
                evidence_ids=(item.id,),
            )
        )
    return tuple(observations)


def _unknowns_from_context(
    context: DecisionContext,
    evidence: tuple[Evidence, ...],
) -> tuple[Unknown, ...]:
    available_categories = {item.category for item in evidence if item.strength != EvidenceStrength.MISSING}
    unknowns: list[Unknown] = []
    for category in context.required_categories:
        if category not in available_categories:
            unknowns.append(
                Unknown(
                    id=f"unknown-{category.name.lower()}",
                    question=f"What reliable {category.value.lower()} evidence is available?",
                    category=category,
                )
            )
    return tuple(unknowns)


def _reasoning_steps(observations: tuple[Observation, ...]) -> tuple[ReasoningStep, ...]:
    grouped: dict[EvidenceCategory, list[Observation]] = defaultdict(list)
    for observation in observations:
        grouped[observation.category].append(observation)

    steps: list[ReasoningStep] = []
    for index, category in enumerate(sorted(grouped, key=lambda item: item.value), start=1):
        category_observations = tuple(grouped[category])
        evidence_ids = tuple(
            evidence_id
            for observation in category_observations
            for evidence_id in observation.evidence_ids
        )
        steps.append(
            ReasoningStep(
                id=f"step-{index:03d}",
                statement=(
                    f"{category.value} reasoning is based on "
                    f"{len(category_observations)} factual observation(s)."
                ),
                evidence_ids=evidence_ids,
                observation_ids=tuple(observation.id for observation in category_observations),
            )
        )
    return tuple(steps)


def _confidence(evidence: tuple[Evidence, ...], unknowns: tuple[Unknown, ...]) -> Confidence:
    if not evidence:
        score = 10
    else:
        strength_points = {
            EvidenceStrength.STRONG: 100,
            EvidenceStrength.MODERATE: 75,
            EvidenceStrength.LIMITED: 45,
            EvidenceStrength.MISSING: 0,
        }
        average_strength = round(
            sum(strength_points[item.strength] for item in evidence) / len(evidence)
        )
        coverage_penalty = min(len(unknowns) * 8, 50)
        score = max(0, min(100, average_strength - coverage_penalty))
    level = _confidence_level(score)
    drivers = tuple(
        f"{item.category.value}: {item.strength.value}" for item in evidence if item.strength != EvidenceStrength.MISSING
    )
    uncertainty = tuple(unknown.question for unknown in unknowns)
    explanation = (
        f"Confidence is {level.lower()} because Atlas has {len(evidence)} evidence item(s) "
        f"and {len(unknowns)} material unknown(s)."
    )
    return Confidence(
        score=score,
        level=level,
        explanation=explanation,
        drivers=drivers,
        uncertainty=uncertainty,
    )


def _confidence_level(score: int) -> str:
    if score >= 85:
        return "Very High"
    if score >= 70:
        return "High"
    if score >= 50:
        return "Moderate"
    if score >= 30:
        return "Low"
    return "Very Low"


def _explanation(
    reasoning_steps: tuple[ReasoningStep, ...],
    unknowns: tuple[Unknown, ...],
    confidence: Confidence,
) -> str:
    return (
        f"Atlas produced {len(reasoning_steps)} reasoning step(s) from factual evidence. "
        f"Confidence is {confidence.level.lower()} at {confidence.score}/100. "
        f"There are {len(unknowns)} material unknown(s) that limit certainty."
    )


def _summary(result: DecisionResult) -> str:
    return (
        f"{result.decision.title}: Atlas can explain the current evidence base, "
        f"with {len(result.observations)} observation(s), {len(result.unknowns)} unknown(s), "
        f"and {result.confidence.level.lower()} confidence."
    )
