"""Sprint 282 — Evidence Quality Review V1 document tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

QUALITY_DOC = Path("docs/EvidenceQualityReviewV1.md")
EVIDENCE_DOC = Path("docs/EvidenceAssemblyV1.md")
PIPELINE_DOC = Path("docs/InvestmentReviewPipelineV1.md")
CLI_FILE = Path("atlas/cli/main.py")
ATLAS_DIR = Path("atlas")

PROHIBITED_PHRASES = [
    "strong buy",
    "price target",
    "act now",
    "must purchase",
    "must sell",
    "buy now",
    "sell now",
    "guaranteed return",
    "risk-free",
    "outperform",
]

QUALITY_DIMENSIONS = [
    "Freshness",
    "Source quality",
    "Corroboration",
    "Conflicting",
    "Missing",
    "Traceability",
    "Documentation",
    "User verification",
]

QUALITY_LEVELS = [
    "Strong",
    "Adequate",
    "Incomplete",
    "Weak",
    "Outdated",
    "Conflicting",
]

REVIEW_FLOW_STEPS = [
    "Freshness",
    "Source",
    "Corroboration",
    "Conflict",
    "Missing",
    "Traceability",
    "Overall",
]

DOWNSTREAM_INFLUENCES = [
    "uncertainty",
    "scenario",
    "follow-up",
    "reasons to wait",
    "revision",
]

CANONICAL_PRINCIPLES = [
    "independent of investment",
    "incomplete evidence",
    "conflicting evidence",
    "uncertainty",
    "stronger evidence",
    "change over time",
    "revision",
    "set",
]

FUTURE_SOURCES = [
    "SEC",
    "earnings",
    "broker",
    "market data",
    "AI",
    "OCR",
]


# ---------------------------------------------------------------------------
# Document existence
# ---------------------------------------------------------------------------


class TestDocumentExists:
    def test_quality_doc_exists(self):
        assert QUALITY_DOC.exists()

    def test_quality_doc_is_file(self):
        assert QUALITY_DOC.is_file()

    def test_quality_doc_is_nonempty(self):
        assert QUALITY_DOC.stat().st_size > 1000

    def test_quality_doc_is_utf8(self):
        QUALITY_DOC.read_bytes().decode("utf-8")

    def test_quality_doc_is_markdown(self):
        assert QUALITY_DOC.suffix == ".md"

    def test_quality_doc_has_header(self):
        content = QUALITY_DOC.read_text(encoding="utf-8")
        assert "Evidence Quality Review" in content


# ---------------------------------------------------------------------------
# Evidence quality dimensions documented
# ---------------------------------------------------------------------------


class TestEvidenceQualityDimensions:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = QUALITY_DOC.read_text(encoding="utf-8")

    @pytest.mark.parametrize("dimension", QUALITY_DIMENSIONS)
    def test_dimension_mentioned(self, dimension: str):
        assert dimension.lower() in self.content.lower(), (
            f"Quality dimension missing: {dimension!r}"
        )

    def test_freshness_why_it_matters(self):
        lower = self.content.lower()
        assert "freshness" in lower
        assert "matter" in lower or "why" in lower or "important" in lower or "relevant" in lower

    def test_source_quality_described(self):
        lower = self.content.lower()
        assert "source quality" in lower or "source" in lower

    def test_corroboration_described(self):
        assert "corroboration" in self.content.lower() or "corroborat" in self.content.lower()

    def test_conflicting_evidence_described(self):
        lower = self.content.lower()
        assert "conflict" in lower

    def test_missing_evidence_described(self):
        lower = self.content.lower()
        assert "missing" in lower

    def test_traceability_described(self):
        assert "traceab" in self.content.lower()

    def test_documentation_completeness_described(self):
        lower = self.content.lower()
        assert "documentation" in lower or "completeness" in lower

    def test_user_verification_described(self):
        lower = self.content.lower()
        assert "user" in lower and ("verif" in lower or "confirm" in lower)

    def test_no_scoring_stated(self):
        lower = self.content.lower()
        assert "no score" in lower or "not scored" in lower or "no scores" in lower or "do not assign" in lower

    def test_no_weights_calculated(self):
        lower = self.content.lower()
        assert "no weight" in lower or "not calculat" in lower or "do not calculat" in lower or "without weight" in lower or "no scores" in lower


# ---------------------------------------------------------------------------
# Quality levels documented
# ---------------------------------------------------------------------------


class TestQualityLevelsDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = QUALITY_DOC.read_text(encoding="utf-8")

    @pytest.mark.parametrize("level", QUALITY_LEVELS)
    def test_quality_level_mentioned(self, level: str):
        assert level in self.content, f"Quality level missing: {level!r}"

    def test_strong_characteristics(self):
        lower = self.content.lower()
        assert "strong" in lower
        assert "characteristic" in lower or "primary" in lower or "corroborated" in lower

    def test_adequate_described(self):
        assert "Adequate" in self.content or "adequate" in self.content.lower()

    def test_incomplete_described(self):
        assert "Incomplete" in self.content

    def test_weak_described(self):
        assert "Weak" in self.content

    def test_outdated_described(self):
        assert "Outdated" in self.content

    def test_conflicting_level_described(self):
        assert "Conflicting" in self.content

    def test_quality_levels_have_downstream_implications(self):
        lower = self.content.lower()
        assert "downstream" in lower or "implication" in lower

    def test_levels_are_descriptive_not_predictive(self):
        lower = self.content.lower()
        assert "descriptive" in lower or "not predictive" in lower or "not a prediction" in lower or "not predict" in lower

    def test_six_quality_levels_present(self):
        count = sum(1 for level in QUALITY_LEVELS if level in self.content)
        assert count == 6


# ---------------------------------------------------------------------------
# Deterministic review flow documented
# ---------------------------------------------------------------------------


class TestReviewFlowDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = QUALITY_DOC.read_text(encoding="utf-8")

    def test_flow_diagram_present(self):
        assert "↓" in self.content

    def test_evidence_set_at_top_of_flow(self):
        lower = self.content.lower()
        assert "evidence set" in lower

    @pytest.mark.parametrize("step", REVIEW_FLOW_STEPS)
    def test_flow_step_present(self, step: str):
        assert step.lower() in self.content.lower(), f"Flow step missing: {step!r}"

    def test_overall_quality_at_end(self):
        lower = self.content.lower()
        assert "overall evidence quality" in lower or "overall quality" in lower

    def test_flow_is_deterministic(self):
        lower = self.content.lower()
        assert "deterministic" in lower

    def test_no_ai_required_for_flow(self):
        lower = self.content.lower()
        assert "no ai" in lower or "ai is not required" in lower or "without ai" in lower or "ai optional" in lower or "no ai required" in lower

    def test_no_numeric_score_produced(self):
        lower = self.content.lower()
        assert "no score" in lower or "not a score" in lower or "no numeric" in lower or "descriptive output" in lower

    def test_most_significant_weakness_principle(self):
        lower = self.content.lower()
        assert "weakness" in lower or "weakest" in lower or "most significant" in lower


# ---------------------------------------------------------------------------
# Examples documented
# ---------------------------------------------------------------------------


class TestExamplesDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = QUALITY_DOC.read_text(encoding="utf-8")

    def test_at_least_two_examples_present(self):
        lower = self.content.lower()
        count = lower.count("example")
        assert count >= 2

    def test_strong_evidence_example(self):
        lower = self.content.lower()
        assert "strong evidence" in lower

    def test_weak_evidence_example(self):
        lower = self.content.lower()
        assert "weak evidence" in lower

    def test_conflicting_evidence_example(self):
        lower = self.content.lower()
        assert "conflicting evidence" in lower

    def test_example_shows_arrow_or_result(self):
        assert "→" in self.content or "produces" in self.content.lower()

    def test_incomplete_evidence_example_present(self):
        lower = self.content.lower()
        assert "incomplete" in lower and "example" in lower

    def test_outdated_evidence_example_present(self):
        lower = self.content.lower()
        assert "outdated" in lower


# ---------------------------------------------------------------------------
# Downstream behaviour documented
# ---------------------------------------------------------------------------


class TestDownstreamBehaviourDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = QUALITY_DOC.read_text(encoding="utf-8")

    def test_downstream_section_present(self):
        lower = self.content.lower()
        assert "downstream" in lower

    @pytest.mark.parametrize("influence", DOWNSTREAM_INFLUENCES)
    def test_downstream_influence_mentioned(self, influence: str):
        assert influence.lower() in self.content.lower(), (
            f"Downstream influence missing: {influence!r}"
        )

    def test_no_buy_recommendation_stated(self):
        lower = self.content.lower()
        assert "buy recommendation" in lower or "never" in lower
        # Must state that quality must never trigger buy/sell
        assert "must never" in lower or "never trigger" in lower or "never generate" in lower

    def test_no_sell_recommendation_stated(self):
        lower = self.content.lower()
        assert "sell" in lower and ("never" in lower or "must not" in lower)

    def test_no_execution_advice_stated(self):
        lower = self.content.lower()
        assert "execution" in lower and ("never" in lower or "must not" in lower or "must never" in lower)

    def test_scenario_width_mentioned(self):
        lower = self.content.lower()
        assert "scenario" in lower and ("width" in lower or "range" in lower or "wide" in lower or "narrow" in lower)

    def test_reasons_to_wait_mentioned(self):
        lower = self.content.lower()
        assert "reasons to wait" in lower or "reason to wait" in lower


# ---------------------------------------------------------------------------
# Cross-cutting principles documented
# ---------------------------------------------------------------------------


class TestCrossCuttingPrinciplesDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = QUALITY_DOC.read_text(encoding="utf-8")

    def test_principles_section_present(self):
        lower = self.content.lower()
        assert "principle" in lower

    def test_quality_independent_of_attractiveness(self):
        lower = self.content.lower()
        assert "independent" in lower and ("investment" in lower or "attractiveness" in lower)

    def test_incomplete_evidence_acceptable(self):
        lower = self.content.lower()
        assert "incomplete" in lower and ("acceptable" in lower or "valid" in lower)

    def test_conflict_must_remain_visible(self):
        lower = self.content.lower()
        assert "conflict" in lower and ("visible" in lower or "remain" in lower)

    def test_uncertainty_must_not_be_hidden(self):
        lower = self.content.lower()
        assert "uncertainty" in lower and ("hidden" in lower or "never" in lower or "not hidden" in lower)

    def test_stronger_evidence_narrows_not_guarantees(self):
        lower = self.content.lower()
        assert "narrows" in lower or "narrow" in lower or "not guarantee" in lower or "does not guarantee" in lower

    def test_quality_may_change_over_time(self):
        lower = self.content.lower()
        assert "change" in lower and "time" in lower

    def test_revisions_preserve_history(self):
        lower = self.content.lower()
        assert "revision" in lower and "histor" in lower or "preserv" in lower

    def test_quality_applies_to_set_not_conclusion(self):
        lower = self.content.lower()
        assert "set" in lower and ("conclusion" in lower or "thesis" in lower)

    @pytest.mark.parametrize("principle_fragment", CANONICAL_PRINCIPLES)
    def test_principle_fragment_present(self, principle_fragment: str):
        assert principle_fragment.lower() in self.content.lower(), (
            f"Principle fragment missing: {principle_fragment!r}"
        )


# ---------------------------------------------------------------------------
# Relationship diagram documented
# ---------------------------------------------------------------------------


class TestRelationshipDiagramDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = QUALITY_DOC.read_text(encoding="utf-8")

    def test_diagram_contains_arrow(self):
        assert "↓" in self.content

    def test_evidence_assembly_in_diagram(self):
        assert "Evidence Assembly" in self.content

    def test_evidence_quality_in_diagram(self):
        assert "Evidence Quality" in self.content

    def test_assumption_downstream_of_quality(self):
        content = self.content
        quality_pos = content.find("Evidence Quality Review")
        assumption_pos = content.find("Assumption")
        assert quality_pos != -1
        assert assumption_pos != -1
        assert quality_pos < assumption_pos

    def test_weekly_review_in_diagram(self):
        assert "Weekly Review" in self.content

    def test_pipeline_reference_present(self):
        assert "Pipeline" in self.content or "pipeline" in self.content.lower()


# ---------------------------------------------------------------------------
# Future extension points documented
# ---------------------------------------------------------------------------


class TestFutureExtensionPointsDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = QUALITY_DOC.read_text(encoding="utf-8")

    def test_future_extensions_section_present(self):
        lower = self.content.lower()
        assert "future" in lower and "extension" in lower

    @pytest.mark.parametrize("source", FUTURE_SOURCES)
    def test_future_source_mentioned(self, source: str):
        assert source.lower() in self.content.lower(), (
            f"Future source missing: {source!r}"
        )

    def test_no_source_bypasses_quality_review(self):
        lower = self.content.lower()
        assert "bypass" in lower or "does not bypass" in lower or "not bypass" in lower

    def test_ai_summaries_labelled(self):
        lower = self.content.lower()
        assert "ai" in lower and "label" in lower

    def test_same_eight_dimensions_apply(self):
        lower = self.content.lower()
        assert "same" in lower or "same eight" in lower or "same dimension" in lower or "same assessment" in lower or "same quality" in lower


# ---------------------------------------------------------------------------
# No recommendation language
# ---------------------------------------------------------------------------


class TestNoRecommendationLanguage:
    @pytest.mark.parametrize("phrase", PROHIBITED_PHRASES)
    def test_no_prohibited_phrase(self, phrase: str):
        content = QUALITY_DOC.read_text(encoding="utf-8").lower()
        assert phrase.lower() not in content, (
            f"Prohibited phrase {phrase!r} found in quality review document"
        )

    def test_no_buy_or_sell_directive(self):
        lower = QUALITY_DOC.read_text(encoding="utf-8").lower()
        for phrase in ["should buy", "should sell", "buy this", "sell this"]:
            assert phrase not in lower

    def test_quality_is_not_investment_quality(self):
        lower = QUALITY_DOC.read_text(encoding="utf-8").lower()
        assert "not investment quality" in lower or "is not investment" in lower or "independent of investment" in lower


# ---------------------------------------------------------------------------
# No runtime code added
# ---------------------------------------------------------------------------


class TestNoRuntimeCodeAdded:
    def test_no_new_cli_commands(self):
        cli_source = CLI_FILE.read_text(encoding="utf-8")
        assert "evidence_quality" not in cli_source
        assert "evidence-quality" not in cli_source

    def test_no_new_python_module(self):
        quality_module = ATLAS_DIR / "evidence_quality"
        assert not quality_module.exists()

    def test_document_is_markdown_not_python(self):
        assert QUALITY_DOC.suffix == ".md"

    def test_no_imports_added_to_atlas(self):
        for src_file in ATLAS_DIR.rglob("*.py"):
            content = src_file.read_text(encoding="utf-8")
            assert "EvidenceQualityReview" not in content

    def test_no_ai_imports_added(self):
        for src_file in ATLAS_DIR.rglob("*.py"):
            content = src_file.read_text(encoding="utf-8")
            for forbidden in ["import openai", "import anthropic", "import langchain"]:
                assert forbidden not in content


# ---------------------------------------------------------------------------
# Prior documents still exist
# ---------------------------------------------------------------------------


class TestPriorDocumentsExist:
    def test_evidence_assembly_doc_exists(self):
        assert EVIDENCE_DOC.exists()

    def test_pipeline_doc_exists(self):
        assert PIPELINE_DOC.exists()

    def test_quality_doc_references_assembly(self):
        content = QUALITY_DOC.read_text(encoding="utf-8")
        assert "EvidenceAssembly" in content or "Evidence Assembly" in content

    def test_quality_doc_references_pipeline(self):
        content = QUALITY_DOC.read_text(encoding="utf-8")
        assert "InvestmentReviewPipeline" in content or "Investment Review Pipeline" in content


# ---------------------------------------------------------------------------
# Sprint 283 recommendation
# ---------------------------------------------------------------------------


class TestSprint283Recommendation:
    def test_sprint_283_or_assumption_review_mentioned(self):
        content = QUALITY_DOC.read_text(encoding="utf-8")
        assert "283" in content or "Assumption Review" in content

    def test_assumption_review_recommended(self):
        content = QUALITY_DOC.read_text(encoding="utf-8")
        assert "Assumption Review" in content


# ---------------------------------------------------------------------------
# Compilation
# ---------------------------------------------------------------------------


class TestCompilation:
    def test_test_file_parses_as_python(self):
        src = Path(__file__).read_text(encoding="utf-8")
        ast.parse(src)
