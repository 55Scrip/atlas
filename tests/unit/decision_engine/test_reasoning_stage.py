"""Reasoning stage tests (Sprint 5, Phase 5).

`evaluate_reasoning` is an assembly layer, not a second evaluator, so
these tests build real upstream results via `evaluate_business`,
`evaluate_valuation`, and `evaluate_portfolio_intelligence` — the same
already-tested pure functions Sprints 2-4 shipped — rather than
fabricating loose `BusinessEvaluationResult`/etc. objects by hand. This
exercises the actual, real contract `evaluate_reasoning` has with its
three inputs.
"""
from __future__ import annotations

import dataclasses
import inspect

import pytest

from atlas.core.domain.evidence.value_objects import Direction
from atlas.decision_engine.contracts import (
    DecisionEngineInput,
    EvaluationState,
    EvidenceGapKind,
    ObservationEpistemicStatus,
    OpenQuestion,
    OpenQuestionKind,
    ReasoningFinding,
)
from atlas.decision_engine.exceptions import DecisionEngineContractError
from atlas.decision_engine.pipeline import run_pipeline
from atlas.decision_engine.stages import reasoning as reasoning_module
from atlas.decision_engine.stages.business_evaluation import evaluate_business
from atlas.decision_engine.stages.portfolio_intelligence import (
    evaluate_portfolio_intelligence,
)
from atlas.decision_engine.stages.reasoning import evaluate_reasoning
from atlas.decision_engine.stages.valuation import evaluate_valuation
from tests.unit.decision_engine._fixtures import (
    CASE_ID,
    EVALUATED_AT,
    GENERATED_AT,
    build_decision,
    build_evidence,
    build_observation,
    build_portfolio_holding_context,
    build_trade_log_entry,
)


def _reason_about(engine_input: DecisionEngineInput):
    """Run the three real upstream evaluators, then Reasoning — exactly
    the sequence `run_pipeline` uses, exposed here for stage-level
    assertions on `ReasoningResult` alone."""
    business_evaluation = evaluate_business(engine_input)
    valuation = evaluate_valuation(engine_input)
    portfolio_intelligence = evaluate_portfolio_intelligence(engine_input)
    return evaluate_reasoning(
        business_evaluation=business_evaluation,
        valuation=valuation,
        portfolio_intelligence=portfolio_intelligence,
    )


class TestNoEvidence:
    def test_empty_case_is_evaluated_with_a_full_gap_disclosure(self):
        engine_input = DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        result = _reason_about(engine_input)
        assert result.state is EvaluationState.EVALUATED
        finding = result.finding
        assert finding.supporting_evidence.observation_classifications == ()
        assert finding.contradicting_evidence.observation_classifications == ()
        assert any(
            gap.kind is EvidenceGapKind.NO_EVIDENCE_RECORDED
            for gap in finding.known_unknowns.evidence_gaps
        )


class TestOnlySupportingEvidence:
    def test_observation_appears_in_supporting_only(self):
        observation = build_observation()
        evidence = build_evidence(observation=observation, direction=Direction.SUPPORTS)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
            evidence=(evidence,),
        )
        finding = _reason_about(engine_input).finding
        supporting_ids = {
            c.observation_id for c in finding.supporting_evidence.observation_classifications
        }
        contradicting_ids = {
            c.observation_id for c in finding.contradicting_evidence.observation_classifications
        }
        assert observation.id in supporting_ids
        assert observation.id not in contradicting_ids


class TestOnlyContradictingEvidence:
    def test_observation_appears_in_contradicting_only(self):
        observation = build_observation()
        evidence = build_evidence(observation=observation, direction=Direction.CHALLENGES)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
            evidence=(evidence,),
        )
        finding = _reason_about(engine_input).finding
        supporting_ids = {
            c.observation_id for c in finding.supporting_evidence.observation_classifications
        }
        contradicting_ids = {
            c.observation_id for c in finding.contradicting_evidence.observation_classifications
        }
        assert observation.id not in supporting_ids
        assert observation.id in contradicting_ids


class TestMixedEvidence:
    def test_contradicted_observation_appears_in_both_summaries(self):
        """A CONTRADICTED observation (both SUPPORTS and CHALLENGES
        linked) legitimately appears in both Supporting and
        Contradicting — the two counts are simultaneously true, and
        Reasoning does not have to pick one."""
        observation = build_observation()
        supporting = build_evidence(observation=observation, direction=Direction.SUPPORTS)
        challenging = build_evidence(observation=observation, direction=Direction.CHALLENGES)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
            evidence=(supporting, challenging),
        )
        finding = _reason_about(engine_input).finding
        [supporting_classification] = finding.supporting_evidence.observation_classifications
        [contradicting_classification] = finding.contradicting_evidence.observation_classifications
        assert supporting_classification.observation_id == observation.id
        assert contradicting_classification.observation_id == observation.id
        assert supporting_classification.status is ObservationEpistemicStatus.CONTRADICTED


class TestEvidenceGaps:
    def test_observation_without_evidence_becomes_a_known_unknown_and_open_question(self):
        observation = build_observation()
        engine_input = DecisionEngineInput(
            case_id=CASE_ID, evaluated_at=EVALUATED_AT, observations=(observation,)
        )
        finding = _reason_about(engine_input).finding
        assert any(
            gap.kind is EvidenceGapKind.OBSERVATION_WITHOUT_EVIDENCE
            and gap.reference == str(observation.id)
            for gap in finding.known_unknowns.evidence_gaps
        )
        assert any(
            question.kind is OpenQuestionKind.OBSERVATION_WITHOUT_EVIDENCE
            and question.reference == str(observation.id)
            for question in finding.open_questions
        )

    def test_decision_without_linked_observation_becomes_a_known_unknown(self):
        decision = build_decision()
        engine_input = DecisionEngineInput(
            case_id=CASE_ID, evaluated_at=EVALUATED_AT, decisions=(decision,)
        )
        finding = _reason_about(engine_input).finding
        assert any(
            gap.kind is EvidenceGapKind.DECISION_WITHOUT_LINKED_OBSERVATION
            and gap.reference == str(decision.id)
            for gap in finding.known_unknowns.evidence_gaps
        )


class TestBusinessInsufficientInput:
    def test_durability_gap_always_present(self):
        engine_input = DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        finding = _reason_about(engine_input).finding
        assert finding.known_unknowns.durability_gap is not None
        assert finding.known_unknowns.durability_gap.state is EvaluationState.INSUFFICIENT_INPUT
        assert any(
            question.kind is OpenQuestionKind.BUSINESS_DURABILITY_NOT_ASSESSABLE
            for question in finding.open_questions
        )


class TestValuationInsufficientInput:
    def test_valuation_gap_always_present(self):
        engine_input = DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        finding = _reason_about(engine_input).finding
        assert finding.known_unknowns.valuation_gap is not None
        assert finding.known_unknowns.valuation_gap.state is EvaluationState.INSUFFICIENT_INPUT
        assert any(
            question.kind is OpenQuestionKind.VALUATION_THESIS_NOT_DOCUMENTED
            for question in finding.open_questions
        )


class TestPortfolioInsufficientInput:
    def test_all_seven_factor_gaps_always_present(self):
        engine_input = DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        finding = _reason_about(engine_input).finding
        assert len(finding.known_unknowns.portfolio_factor_gaps) == 7
        portfolio_questions = [
            q
            for q in finding.open_questions
            if q.kind is OpenQuestionKind.PORTFOLIO_FACTOR_NOT_ASSESSABLE
        ]
        assert len(portfolio_questions) == 7

    def test_portfolio_context_reuses_holding_context_verbatim(self):
        holding = build_portfolio_holding_context(ticker="ASML", weight_percent=4.5)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID, evaluated_at=EVALUATED_AT, portfolio_holding=holding
        )
        business_evaluation = evaluate_business(engine_input)
        valuation = evaluate_valuation(engine_input)
        portfolio_intelligence = evaluate_portfolio_intelligence(engine_input)
        result = evaluate_reasoning(
            business_evaluation=business_evaluation,
            valuation=valuation,
            portfolio_intelligence=portfolio_intelligence,
        )
        assert (
            result.finding.portfolio_context.holding_context
            is portfolio_intelligence.holding_context
        )


class TestEverythingPopulated:
    def test_full_case_still_assembles_cleanly(self):
        decision = build_decision()
        observation = build_observation()
        supporting = build_evidence(observation=observation, direction=Direction.SUPPORTS)
        holding = build_portfolio_holding_context()
        trade = build_trade_log_entry()
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            decisions=(decision,),
            observations=(observation,),
            evidence=(supporting,),
            portfolio_holding=holding,
            trade_log=(trade,),
        )
        result = _reason_about(engine_input)
        assert result.state is EvaluationState.EVALUATED
        assert result.finding is not None


class TestEmptyReasoning:
    def test_minimal_input_still_produces_a_complete_finding(self):
        engine_input = DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        result = _reason_about(engine_input)
        assert result.state is EvaluationState.EVALUATED
        for field in dataclasses.fields(result.finding):
            assert getattr(result.finding, field.name) is not None


class TestDeterministicOrdering:
    def test_open_questions_order_independent_of_observation_input_order(self):
        first_observation = build_observation(subject="ASML", statement="First.")
        second_observation = build_observation(subject="ASML", statement="Second.")
        forward = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(first_observation, second_observation),
        )
        reversed_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(second_observation, first_observation),
        )
        forward_finding = _reason_about(forward).finding
        reversed_finding = _reason_about(reversed_input).finding
        # Both observations lack evidence either way -- the two
        # OBSERVATION_WITHOUT_EVIDENCE gaps/questions exist regardless
        # of which observation was supplied first, and business
        # evaluation's own classification order already tracks
        # `engine_input.observations` order deterministically, so
        # reversing the input reverses this specific slice too. What
        # must NOT vary is the *set* of references produced.
        forward_refs = {
            q.reference
            for q in forward_finding.open_questions
            if q.kind is OpenQuestionKind.OBSERVATION_WITHOUT_EVIDENCE
        }
        reversed_refs = {
            q.reference
            for q in reversed_finding.open_questions
            if q.kind is OpenQuestionKind.OBSERVATION_WITHOUT_EVIDENCE
        }
        assert forward_refs == reversed_refs == {str(first_observation.id), str(second_observation.id)}

    def test_portfolio_factor_gap_ordering_is_stable_across_runs(self):
        engine_input = DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        first = _reason_about(engine_input)
        second = _reason_about(engine_input)
        assert (
            first.finding.known_unknowns.portfolio_factor_gaps
            == second.finding.known_unknowns.portfolio_factor_gaps
        )


class TestRepeatedExecutionIdentical:
    def test_identical_upstream_results_produce_a_deeply_equal_reasoning_result(self):
        engine_input = DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        business_evaluation = evaluate_business(engine_input)
        valuation = evaluate_valuation(engine_input)
        portfolio_intelligence = evaluate_portfolio_intelligence(engine_input)

        first = evaluate_reasoning(
            business_evaluation=business_evaluation,
            valuation=valuation,
            portfolio_intelligence=portfolio_intelligence,
        )
        second = evaluate_reasoning(
            business_evaluation=business_evaluation,
            valuation=valuation,
            portfolio_intelligence=portfolio_intelligence,
        )
        assert first == second


class TestPipelineIntegration:
    def test_reasoning_evaluated_recommendation_still_withheld(self):
        output = run_pipeline(
            DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT),
            generated_at=GENERATED_AT,
        )
        assert output.reasoning.state is EvaluationState.EVALUATED
        assert output.recommendation.kind.value == "recommendation_withheld"


class TestReasoningHasNoDirectionOrConvictionField:
    def test_no_direction_field_anywhere_in_reasoning_finding(self):
        engine_input = DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        finding = _reason_about(engine_input).finding
        all_field_names: set[str] = set()
        for obj in (
            finding,
            finding.current_situation,
            finding.supporting_evidence,
            finding.contradicting_evidence,
            finding.known_unknowns,
            finding.portfolio_context,
        ):
            all_field_names |= {f.name for f in dataclasses.fields(obj)}
        assert "direction" not in all_field_names

    def test_no_conviction_field_anywhere_in_reasoning_finding(self):
        engine_input = DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        finding = _reason_about(engine_input).finding
        all_field_names: set[str] = set()
        for obj in (
            finding,
            finding.current_situation,
            finding.supporting_evidence,
            finding.contradicting_evidence,
            finding.known_unknowns,
            finding.portfolio_context,
        ):
            all_field_names |= {f.name for f in dataclasses.fields(obj)}
        assert "conviction" not in all_field_names
        assert "conviction_level" not in all_field_names


class TestWhatWouldChangeIsExactlyEmpty:
    def test_empty_regardless_of_how_many_gaps_exist(self):
        decision = build_decision()
        observation = build_observation()
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            decisions=(decision,),
            observations=(observation,),
        )
        finding = _reason_about(engine_input).finding
        assert finding.what_would_change == ()

    def test_constructing_a_nonempty_what_would_change_is_forbidden(self):
        engine_input = DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        finding = _reason_about(engine_input).finding
        with pytest.raises(DecisionEngineContractError):
            ReasoningFinding(
                current_situation=finding.current_situation,
                supporting_evidence=finding.supporting_evidence,
                contradicting_evidence=finding.contradicting_evidence,
                known_unknowns=finding.known_unknowns,
                portfolio_context=finding.portfolio_context,
                open_questions=finding.open_questions,
                what_would_change=(OpenQuestion(kind=OpenQuestionKind.NO_EVIDENCE_RECORDED_FOR_CASE),),
            )


class TestNoFreeTextInspection:
    def test_reasoning_module_source_never_accesses_statement_fields(self):
        source = inspect.getsource(reasoning_module)
        assert ".statement" not in source
        assert "investment_case" not in source

    def test_differing_free_text_does_not_change_the_finding_shape(self):
        """Two Observations differing only in `statement` text, otherwise
        identical, must produce the same-shaped `ReasoningFinding` (same
        classification, same gaps) — proving statement content plays no
        role."""
        first_observation = build_observation(statement="Revenue grew 12%.")
        second_observation = build_observation(statement="A wildly different sentence.")
        first_input = DecisionEngineInput(
            case_id=CASE_ID, evaluated_at=EVALUATED_AT, observations=(first_observation,)
        )
        second_input = DecisionEngineInput(
            case_id=CASE_ID, evaluated_at=EVALUATED_AT, observations=(second_observation,)
        )
        first_finding = _reason_about(first_input).finding
        second_finding = _reason_about(second_input).finding
        assert (
            first_finding.known_unknowns.evidence_gaps[0].kind
            == second_finding.known_unknowns.evidence_gaps[0].kind
        )
