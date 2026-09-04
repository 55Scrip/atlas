"""`DE-016` conformance: which open questions may reach Conviction.

`DE-016` §7 partitions every open question into exactly one owner, and
§8.2 forbids Capability Gaps from reducing Conviction. Before this,
Recommendation Conviction read `decision_engine`'s evidence-linkage gap
list, every member of which §7 owns elsewhere -- so a permanent floor of
capability markers held `has_open_questions` true for every company and
HIGH was unreachable regardless of the evidence.

These pin the partition and the wiring. The production-path test is the
one that matters: it fails if capability gaps ever reach Conviction
again, which a table-only test could not see.

Deliberately NOT asserted here: that the full question lists are
unchanged. That is `test_pipeline`'s territory and is asserted there;
duplicating it would couple this file to unrelated vocabulary. What is
asserted is the narrower claim §8.2 actually makes -- filtering what
Conviction reads never removes anything Atlas says.
"""
from __future__ import annotations

import pytest

import atlas.analysis_engine.recommendation as recommendation_module
from atlas.analysis_engine.investment_case_synthesis import (
    CaseOpenQuestion,
    CaseOpenQuestionCategory,
    OpenQuestionOrigin,
    classify_case_open_question,
    material_case_open_questions,
)
from atlas.analysis_engine.pipeline import assemble_analysis
from atlas.decision_engine.pipeline import run_pipeline
from tests.unit.analysis_engine._fixtures import GENERATED_AT, build_minimal_input

_CAPABILITY_GAPS = (OpenQuestionOrigin.SCENARIO_VALUATION_UNAVAILABLE,)
_INSUFFICIENT = (
    OpenQuestionOrigin.GROWTH_INCONCLUSIVE,
    OpenQuestionOrigin.CAPITAL_ALLOCATION_INCONCLUSIVE,
    OpenQuestionOrigin.VALUATION_INCONCLUSIVE,
)
_EVIDENTIAL = (
    OpenQuestionOrigin.GROWTH_MIXED,
    OpenQuestionOrigin.CAPITAL_ALLOCATION_WEAK,
    OpenQuestionOrigin.VALUATION_EXPENSIVE_VERSUS_GROWTH,
)


class TestPartition:
    def test_every_origin_has_exactly_one_category(self):
        """`DE-016` §7 requires one canonical owner per question. A new
        vocabulary member with no classification must fail loudly rather
        than default into, or out of, Conviction."""
        for origin in OpenQuestionOrigin:
            assert isinstance(classify_case_open_question(origin), CaseOpenQuestionCategory)

    @pytest.mark.parametrize("origin", _CAPABILITY_GAPS)
    def test_capability_gaps_are_classified_as_such(self, origin):
        assert classify_case_open_question(origin) is CaseOpenQuestionCategory.CAPABILITY_GAP

    @pytest.mark.parametrize("origin", _INSUFFICIENT)
    def test_could_not_run_is_insufficient_input_not_evidential(self, origin):
        """An analysis that could not run for want of data is a Coverage
        fact, not a mixed answer (`DE-016` §5)."""
        assert classify_case_open_question(origin) is CaseOpenQuestionCategory.INSUFFICIENT_INPUT

    @pytest.mark.parametrize("origin", _EVIDENTIAL)
    def test_complete_but_mixed_is_evidential_uncertainty(self, origin):
        """Ran to completion, answer genuinely mixed or adverse -- the one
        category `DE-016` §7 lets reach Conviction."""
        assert classify_case_open_question(origin) is CaseOpenQuestionCategory.EVIDENTIAL_UNCERTAINTY


class TestMaterialSubset:
    def test_capability_gaps_are_excluded(self):
        questions = (CaseOpenQuestion(origin=OpenQuestionOrigin.SCENARIO_VALUATION_UNAVAILABLE, reference="v"),)
        assert material_case_open_questions(questions) == ()

    def test_insufficient_input_is_excluded(self):
        questions = tuple(CaseOpenQuestion(origin=o, reference=None) for o in _INSUFFICIENT)
        assert material_case_open_questions(questions) == ()

    def test_evidential_uncertainty_is_kept(self):
        questions = (CaseOpenQuestion(origin=OpenQuestionOrigin.GROWTH_MIXED, reference="g"),)
        assert material_case_open_questions(questions) == questions

    def test_a_capability_gap_never_masks_a_real_question(self):
        """The AVGO/AMAT distinction: one company's only question is a
        capability gap, another's is a genuine mixed result. They must
        not collapse to the same answer."""
        gap = CaseOpenQuestion(origin=OpenQuestionOrigin.SCENARIO_VALUATION_UNAVAILABLE, reference="v")
        mixed = CaseOpenQuestion(origin=OpenQuestionOrigin.GROWTH_MIXED, reference="g")
        assert material_case_open_questions((gap,)) == ()
        assert material_case_open_questions((gap, mixed)) == (mixed,)

    def test_filtering_does_not_mutate_the_source(self):
        """`DE-016` §8.2: capability gaps remain visible. This decides
        what Conviction reads, never what Atlas keeps."""
        questions = (
            CaseOpenQuestion(origin=OpenQuestionOrigin.SCENARIO_VALUATION_UNAVAILABLE, reference="v"),
            CaseOpenQuestion(origin=OpenQuestionOrigin.GROWTH_MIXED, reference="g"),
        )
        material_case_open_questions(questions)
        assert len(questions) == 2


class TestProductionPathExcludesCapabilityGaps:
    def test_conviction_does_not_receive_the_evidence_linkage_list(self):
        """The regression this exists to prevent.

        Minimal input produces a full evidence-linkage list (durability
        plus all seven portfolio factors, none resolvable) and no
        Evidential Uncertainty. Conviction must therefore be told there
        are no open questions. Reading the linkage list -- the
        pre-`DE-016` behaviour -- makes this True and fails the test."""
        engine_input = build_minimal_input()
        output = run_pipeline(engine_input, generated_at=GENERATED_AT)
        real = recommendation_module.calculate_recommendation_conviction
        captured = {}

        def spy(**kwargs):
            captured.update(kwargs)
            return real(**kwargs)

        recommendation_module.calculate_recommendation_conviction = spy
        try:
            analysis = assemble_analysis(
                engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT)
        finally:
            recommendation_module.calculate_recommendation_conviction = real

        assert captured, "production never called the conviction calculator"
        assert captured["has_open_questions"] is False, (
            "a capability gap reached Conviction; DE-016 §8.2 forbids it")

        # And the same run must still disclose them -- excluded from
        # Conviction, never hidden from the investor.
        assert analysis.open_questions, (
            "capability information disappeared; DE-016 §8.2 requires it stay visible")


class TestCounterEvidenceMateriality:
    def test_recorded_counter_evidence_is_treated_as_material(self):
        """`DE-016` §6's closing rule: where materiality cannot be
        determined for a specific piece of Counter-Evidence it is treated
        as material, because understating uncertainty is the more
        damaging error. Atlas holds no conclusion-relative materiality
        record today (`DE-016` §17 Q1), so this is the whole of the
        judgment -- pinned here so a future refinement is a deliberate
        change to one named function, not an accident."""
        engine_input = build_minimal_input()
        output = run_pipeline(engine_input, generated_at=GENERATED_AT)
        assert recommendation_module._has_material_counter_evidence(
            output.reasoning
        ) is recommendation_module._safe_has_contradicting_evidence(output.reasoning)
