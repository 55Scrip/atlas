from dataclasses import FrozenInstanceError

import pytest

from atlas.domains.decision import (
    Decision,
    DecisionCard,
    DecisionContext,
    DecisionEngine,
    Evidence,
    EvidenceCategory,
    EvidenceEngine,
    EvidenceStrength,
    ReasoningEngine,
)


def _decision() -> Decision:
    return Decision(
        id="decision-1",
        title="Evaluate Nvidia position context",
        subject="NVDA",
    )


def _evidence() -> tuple[Evidence, ...]:
    return (
        Evidence(
            id="risk-1",
            category=EvidenceCategory.RISK,
            statement="Largest position weight is 42% of portfolio value.",
            source="Portfolio domain",
            strength=EvidenceStrength.STRONG,
            data={"weight": 0.42},
        ),
        Evidence(
            id="valuation-1",
            category=EvidenceCategory.VALUATION,
            statement="Price to earnings multiple is above portfolio median.",
            source="Valuation model",
            strength=EvidenceStrength.LIMITED,
        ),
        Evidence(
            id="portfolio-1",
            category=EvidenceCategory.PORTFOLIO,
            statement="Portfolio spans three sectors.",
            source="Portfolio summary",
            strength=EvidenceStrength.MODERATE,
        ),
    )


def test_decision_models_are_immutable() -> None:
    decision = _decision()
    evidence = _evidence()[0]

    with pytest.raises(FrozenInstanceError):
        decision.title = "Changed"  # type: ignore[misc]

    with pytest.raises(TypeError):
        evidence.data["weight"] = 0.5


def test_evidence_engine_collects_facts_deterministically() -> None:
    context = DecisionContext(decision=_decision(), evidence=_evidence())

    collected = EvidenceEngine().collect(context)

    assert [item.id for item in collected] == ["portfolio-1", "risk-1", "valuation-1"]
    assert all(item.statement for item in collected)


def test_reasoning_pipeline_references_supporting_evidence() -> None:
    context = DecisionContext(decision=_decision(), evidence=_evidence())

    result = ReasoningEngine().reason(context)

    assert len(result.observations) == 3
    assert len(result.reasoning_steps) == 3
    assert all(step.evidence_ids for step in result.reasoning_steps)
    assert all(step.observation_ids for step in result.reasoning_steps)
    assert "material unknown" in result.explanation


def test_unknown_detection_uses_required_categories() -> None:
    context = DecisionContext(
        decision=_decision(),
        evidence=_evidence(),
        required_categories=(
            EvidenceCategory.PORTFOLIO,
            EvidenceCategory.COMPANY,
            EvidenceCategory.RISK,
        ),
    )

    result = ReasoningEngine().reason(context)

    assert [unknown.category for unknown in result.unknowns] == [EvidenceCategory.COMPANY]
    assert "company evidence" in result.unknowns[0].question


def test_confidence_calculation_accounts_for_strength_and_unknowns() -> None:
    context = DecisionContext(
        decision=_decision(),
        evidence=_evidence(),
        required_categories=(
            EvidenceCategory.PORTFOLIO,
            EvidenceCategory.RISK,
            EvidenceCategory.VALUATION,
        ),
    )

    result = ReasoningEngine().reason(context)

    assert result.confidence.score == 73
    assert result.confidence.level == "High"
    assert "Risk: Strong" in result.confidence.drivers
    assert result.confidence.uncertainty == ()


def test_decision_card_generation_is_non_advisory() -> None:
    context = DecisionContext(decision=_decision(), evidence=_evidence())

    card = DecisionEngine().evaluate(context)
    rendered_text = " ".join(
        [
            card.summary,
            card.explanation,
            " ".join(observation.statement for observation in card.key_observations),
        ]
    )

    assert isinstance(card, DecisionCard)
    assert card.evidence
    assert card.key_observations
    assert card.unknowns
    assert card.confidence.explanation
    assert card.risks == ("Risk evidence states: Largest position weight is 42% of portfolio value.",)
    assert "buy" not in rendered_text.lower()
    assert "sell" not in rendered_text.lower()
    assert "prediction" not in rendered_text.lower()


def test_pipeline_is_repeatable() -> None:
    context = DecisionContext(decision=_decision(), evidence=_evidence())
    engine = DecisionEngine()

    first = engine.evaluate(context)
    second = engine.evaluate(context)

    assert first == second


def test_empty_evidence_edge_case_is_explainable() -> None:
    context = DecisionContext(decision=_decision())

    card = DecisionEngine().evaluate(context)

    assert card.evidence == ()
    assert card.key_observations == ()
    assert card.confidence.score == 10
    assert card.confidence.level == "Very Low"
    assert len(card.unknowns) == len(tuple(EvidenceCategory))
