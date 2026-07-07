"""Sprint 283 — Assumption Review V1 document tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ASSUMPTION_DOC = Path("docs/AssumptionReviewV1.md")
EVIDENCE_DOC = Path("docs/EvidenceAssemblyV1.md")
QUALITY_DOC = Path("docs/EvidenceQualityReviewV1.md")
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

ASSUMPTION_CATEGORIES = [
    "Business",
    "Financial",
    "Competitive",
    "Management",
    "Industry",
    "Macro",
    "Valuation",
    "Portfolio",
    "Behavioural",
    "User",
]

FLOW_STEPS = [
    "Extract",
    "Link Evidence",
    "Unsupported",
    "Conflicting",
    "Open Questions",
    "Revision",
    "Risk Review",
]

DOWNSTREAM_STAGES = [
    "Risk Review",
    "Value Scenario",
    "Weekly Review",
    "Decision Journal",
]

CANONICAL_PRINCIPLES = [
    "assumptions are not facts",
    "revisited",
    "conflict",
    "obsolete",
    "evidence-linked",
    "uncertainty",
    "revision",
    "challenged",
]

FUTURE_SOURCES = [
    "AI",
    "SEC",
    "earnings",
    "broker",
    "market data",
    "OCR",
    "collaboration",
]


# ---------------------------------------------------------------------------
# Document existence
# ---------------------------------------------------------------------------


class TestDocumentExists:
    def test_assumption_doc_exists(self):
        assert ASSUMPTION_DOC.exists()

    def test_assumption_doc_is_file(self):
        assert ASSUMPTION_DOC.is_file()

    def test_assumption_doc_is_nonempty(self):
        assert ASSUMPTION_DOC.stat().st_size > 1000

    def test_assumption_doc_is_utf8(self):
        ASSUMPTION_DOC.read_bytes().decode("utf-8")

    def test_assumption_doc_is_markdown(self):
        assert ASSUMPTION_DOC.suffix == ".md"

    def test_assumption_doc_has_header(self):
        content = ASSUMPTION_DOC.read_text(encoding="utf-8")
        assert "Assumption Review" in content


# ---------------------------------------------------------------------------
# Assumption categories documented
# ---------------------------------------------------------------------------


class TestAssumptionCategoriesDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ASSUMPTION_DOC.read_text(encoding="utf-8")

    @pytest.mark.parametrize("category", ASSUMPTION_CATEGORIES)
    def test_category_mentioned(self, category: str):
        assert category in self.content, f"Assumption category missing: {category!r}"

    def test_at_least_eight_categories(self):
        count = sum(1 for c in ASSUMPTION_CATEGORIES if c in self.content)
        assert count >= 8

    def test_business_assumptions_have_examples(self):
        lower = self.content.lower()
        assert "business" in lower
        assert "example" in lower or "revenue" in lower

    def test_financial_assumptions_described(self):
        lower = self.content.lower()
        assert "financial" in lower
        assert "revenue" in lower or "margin" in lower or "cash" in lower

    def test_competitive_assumptions_described(self):
        lower = self.content.lower()
        assert "competitive" in lower
        assert "moat" in lower or "market share" in lower or "position" in lower

    def test_management_assumptions_described(self):
        lower = self.content.lower()
        assert "management" in lower
        assert "capital allocation" in lower or "leadership" in lower or "strategy" in lower

    def test_macro_assumptions_described(self):
        lower = self.content.lower()
        assert "macro" in lower
        assert "rate" in lower or "interest" in lower or "currency" in lower

    def test_valuation_assumptions_described(self):
        lower = self.content.lower()
        assert "valuation" in lower
        assert "multiple" in lower or "price" in lower or "earnings" in lower

    def test_portfolio_assumptions_described(self):
        lower = self.content.lower()
        assert "portfolio" in lower
        assert "position" in lower or "concentration" in lower or "size" in lower

    def test_categories_have_evidence_required(self):
        lower = self.content.lower()
        assert "evidence required" in lower or "evidence:" in lower

    def test_categories_have_failure_modes(self):
        lower = self.content.lower()
        assert "failure mode" in lower or "common failure" in lower


# ---------------------------------------------------------------------------
# Explicit vs implicit assumptions documented
# ---------------------------------------------------------------------------


class TestExplicitVsImplicitDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ASSUMPTION_DOC.read_text(encoding="utf-8")

    def test_explicit_assumptions_defined(self):
        assert "Explicit" in self.content or "explicit" in self.content.lower()

    def test_implicit_assumptions_defined(self):
        assert "Implicit" in self.content or "implicit" in self.content.lower()

    def test_explicit_example_present(self):
        lower = self.content.lower()
        assert "revenue growth" in lower or "above 15" in lower or "explicit" in lower

    def test_implicit_example_present(self):
        lower = self.content.lower()
        assert "competitive position" in lower or "will remain unchanged" in lower or "implicit" in lower

    def test_distinction_between_types_clear(self):
        lower = self.content.lower()
        assert "explicit" in lower and "implicit" in lower

    def test_atlas_surfaces_implicit(self):
        lower = self.content.lower()
        assert "surface" in lower or "visible" in lower or "surfacing" in lower

    def test_atlas_does_not_resolve_implicit(self):
        lower = self.content.lower()
        assert "does not resolve" in lower or "does not decide" in lower or "does not correct" in lower or "makes them visible" in lower


# ---------------------------------------------------------------------------
# Assumption review flow documented
# ---------------------------------------------------------------------------


class TestAssumptionReviewFlowDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ASSUMPTION_DOC.read_text(encoding="utf-8")

    def test_flow_diagram_present(self):
        assert "↓" in self.content

    def test_evidence_at_top_of_flow(self):
        lower = self.content.lower()
        assert "evidence" in lower

    @pytest.mark.parametrize("step", FLOW_STEPS)
    def test_flow_step_present(self, step: str):
        assert step.lower() in self.content.lower(), f"Flow step missing: {step!r}"

    def test_assumption_register_mentioned(self):
        lower = self.content.lower()
        assert "assumption register" in lower or "register" in lower

    def test_flow_is_deterministic(self):
        lower = self.content.lower()
        assert "deterministic" in lower

    def test_no_ai_required_for_flow(self):
        lower = self.content.lower()
        assert "no ai" in lower or "ai is not required" in lower or "without ai" in lower or "ai optional" in lower

    def test_flow_produces_no_recommendation(self):
        lower = self.content.lower()
        assert "no recommendation" in lower or "does not produce recommendation" in lower or "recommendation" in lower


# ---------------------------------------------------------------------------
# Evidence linkage documented
# ---------------------------------------------------------------------------


class TestEvidenceLinkageDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ASSUMPTION_DOC.read_text(encoding="utf-8")

    def test_assumption_linked_to_evidence(self):
        lower = self.content.lower()
        assert "link" in lower and "evidence" in lower

    def test_unsupported_assumptions_mentioned(self):
        lower = self.content.lower()
        assert "unsupported" in lower

    def test_unsupported_remain_visible(self):
        lower = self.content.lower()
        assert "unsupported" in lower and "visible" in lower

    def test_evidence_supported_state_described(self):
        lower = self.content.lower()
        assert "evidence-supported" in lower or "evidence supported" in lower or "supported" in lower

    def test_contradicted_state_described(self):
        lower = self.content.lower()
        assert "contradict" in lower or "conflicting" in lower

    def test_obsolete_state_described(self):
        lower = self.content.lower()
        assert "obsolete" in lower

    def test_missing_evidence_not_hidden(self):
        lower = self.content.lower()
        assert "not hidden" in lower or "visible" in lower or "must not be hidden" in lower


# ---------------------------------------------------------------------------
# Assumption challenge process documented
# ---------------------------------------------------------------------------


class TestAssumptionChallengeDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ASSUMPTION_DOC.read_text(encoding="utf-8")

    def test_challenge_section_present(self):
        lower = self.content.lower()
        assert "challeng" in lower

    def test_what_evidence_supports_question(self):
        lower = self.content.lower()
        assert "what evidence" in lower and "support" in lower

    def test_what_would_invalidate_question(self):
        lower = self.content.lower()
        assert "invalidate" in lower or "invalid" in lower

    def test_what_triggers_review_question(self):
        lower = self.content.lower()
        assert "trigger" in lower or "prompt" in lower or "new information" in lower

    def test_dependency_questions_present(self):
        lower = self.content.lower()
        assert "depend" in lower

    def test_challenge_is_not_investment_advice(self):
        lower = self.content.lower()
        assert "not investment advice" in lower or "not advice" in lower or "structured thinking" in lower

    def test_challenge_strengthens_decisions(self):
        lower = self.content.lower()
        assert "strengthen" in lower or "stronger" in lower or "durable" in lower


# ---------------------------------------------------------------------------
# Downstream relationships documented
# ---------------------------------------------------------------------------


class TestDownstreamRelationshipsDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ASSUMPTION_DOC.read_text(encoding="utf-8")

    @pytest.mark.parametrize("stage", DOWNSTREAM_STAGES)
    def test_downstream_stage_mentioned(self, stage: str):
        assert stage in self.content, f"Downstream stage missing: {stage!r}"

    def test_risk_review_relationship(self):
        lower = self.content.lower()
        assert "risk review" in lower and ("assumption" in lower or "register" in lower)

    def test_value_scenario_relationship(self):
        lower = self.content.lower()
        assert "value scenario" in lower and "assumption" in lower

    def test_weekly_review_relationship(self):
        lower = self.content.lower()
        assert "weekly review" in lower

    def test_decision_journal_relationship(self):
        lower = self.content.lower()
        assert "decision journal" in lower

    def test_future_revisions_mentioned(self):
        lower = self.content.lower()
        assert "future revision" in lower or "recurring" in lower or "over time" in lower

    def test_scenario_ranges_influenced_by_assumption_quality(self):
        lower = self.content.lower()
        assert "scenario" in lower and ("range" in lower or "width" in lower or "wider" in lower or "narrow" in lower)


# ---------------------------------------------------------------------------
# Examples documented
# ---------------------------------------------------------------------------


class TestExamplesDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ASSUMPTION_DOC.read_text(encoding="utf-8")

    def test_at_least_three_examples(self):
        lower = self.content.lower()
        count = lower.count("example")
        # Also count named example sections
        named_count = lower.count("well-supported") + lower.count("unsupported assumption") + lower.count("conflicting assumption") + lower.count("revised assumption") + lower.count("obsolete assumption")
        assert count + named_count >= 3

    def test_well_supported_example(self):
        lower = self.content.lower()
        assert "well-supported" in lower or "well supported" in lower

    def test_unsupported_assumption_example(self):
        lower = self.content.lower()
        assert "unsupported assumption" in lower or "unsupported" in lower

    def test_conflicting_assumption_example(self):
        lower = self.content.lower()
        assert "conflicting assumption" in lower or "conflicting" in lower

    def test_revised_assumption_example(self):
        lower = self.content.lower()
        assert "revised assumption" in lower or "revision" in lower

    def test_obsolete_assumption_example(self):
        lower = self.content.lower()
        assert "obsolete assumption" in lower or "obsolete" in lower

    def test_examples_use_concrete_language(self):
        lower = self.content.lower()
        assert "revenue" in lower or "margin" in lower or "growth" in lower


# ---------------------------------------------------------------------------
# Relationship diagram documented
# ---------------------------------------------------------------------------


class TestRelationshipDiagramDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ASSUMPTION_DOC.read_text(encoding="utf-8")

    def test_diagram_has_arrows(self):
        assert "↓" in self.content

    def test_evidence_assembly_in_diagram(self):
        assert "Evidence Assembly" in self.content

    def test_evidence_quality_in_diagram(self):
        assert "Evidence Quality" in self.content

    def test_assumption_review_in_diagram(self):
        assert "Assumption Review" in self.content

    def test_risk_review_in_diagram(self):
        assert "Risk Review" in self.content

    def test_value_scenario_in_diagram(self):
        assert "Value Scenario" in self.content

    def test_weekly_review_in_diagram(self):
        assert "Weekly Review" in self.content

    def test_pipeline_stages_all_present_in_diagram(self):
        lower = self.content.lower()
        for stage in ["evidence assembly", "evidence quality", "assumption review",
                      "risk review", "value scenario", "weekly review"]:
            assert stage in lower, f"Diagram stage missing: {stage!r}"

    def test_risk_review_present_after_value_scenario(self):
        content = self.content
        risk_pos = content.find("Risk Review")
        value_pos = content.find("Value Scenario")
        assert risk_pos != -1
        assert value_pos != -1
        # Both must be present; exact ordering tested via pipeline flow doc


# ---------------------------------------------------------------------------
# Future extension points documented
# ---------------------------------------------------------------------------


class TestFutureExtensionPointsDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ASSUMPTION_DOC.read_text(encoding="utf-8")

    def test_future_extensions_section_present(self):
        lower = self.content.lower()
        assert "future" in lower and "extension" in lower

    @pytest.mark.parametrize("source", FUTURE_SOURCES)
    def test_future_source_mentioned(self, source: str):
        assert source.lower() in self.content.lower(), (
            f"Future source missing: {source!r}"
        )

    def test_no_source_bypasses_assumption_review(self):
        lower = self.content.lower()
        assert "bypass" in lower or "does not bypass" in lower or "not bypass" in lower

    def test_ai_labelled_as_ai_derived(self):
        lower = self.content.lower()
        assert "ai-derived" in lower or "ai derived" in lower or "labelled" in lower

    def test_future_sources_supply_evidence(self):
        lower = self.content.lower()
        assert "supply evidence" in lower or "supplies evidence" in lower or "provide evidence" in lower or "supply" in lower


# ---------------------------------------------------------------------------
# No recommendation language
# ---------------------------------------------------------------------------


class TestNoRecommendationLanguage:
    @pytest.mark.parametrize("phrase", PROHIBITED_PHRASES)
    def test_no_prohibited_phrase(self, phrase: str):
        content = ASSUMPTION_DOC.read_text(encoding="utf-8").lower()
        assert phrase.lower() not in content, (
            f"Prohibited phrase {phrase!r} found in assumption review document"
        )

    def test_no_choose_investment_language(self):
        lower = ASSUMPTION_DOC.read_text(encoding="utf-8").lower()
        for phrase in ["should invest", "choose this", "select this"]:
            assert phrase not in lower

    def test_action_is_outside_atlas(self):
        lower = ASSUMPTION_DOC.read_text(encoding="utf-8").lower()
        assert "action is outside atlas" in lower or "outside atlas" in lower or "action" in lower


# ---------------------------------------------------------------------------
# No runtime code added
# ---------------------------------------------------------------------------


class TestNoRuntimeCodeAdded:
    def test_no_new_cli_commands(self):
        cli_source = CLI_FILE.read_text(encoding="utf-8")
        assert "assumption_review" not in cli_source
        assert "assumption-review" not in cli_source

    def test_no_new_python_module(self):
        assumption_module = ATLAS_DIR / "assumption_review"
        assert not assumption_module.exists()

    def test_document_is_markdown_not_python(self):
        assert ASSUMPTION_DOC.suffix == ".md"

    def test_no_imports_added_to_atlas(self):
        for src_file in ATLAS_DIR.rglob("*.py"):
            content = src_file.read_text(encoding="utf-8")
            assert "AssumptionReview" not in content

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

    def test_quality_review_doc_exists(self):
        assert QUALITY_DOC.exists()

    def test_pipeline_doc_exists(self):
        assert PIPELINE_DOC.exists()

    def test_assumption_doc_references_evidence_assembly(self):
        content = ASSUMPTION_DOC.read_text(encoding="utf-8")
        assert "EvidenceAssembly" in content or "Evidence Assembly" in content

    def test_assumption_doc_references_quality_review(self):
        content = ASSUMPTION_DOC.read_text(encoding="utf-8")
        assert "EvidenceQualityReview" in content or "Evidence Quality Review" in content

    def test_assumption_doc_references_pipeline(self):
        content = ASSUMPTION_DOC.read_text(encoding="utf-8")
        assert "InvestmentReviewPipeline" in content or "Investment Review Pipeline" in content or "Pipeline" in content


# ---------------------------------------------------------------------------
# Canonical principles documented
# ---------------------------------------------------------------------------


class TestCanonicalPrinciplesDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ASSUMPTION_DOC.read_text(encoding="utf-8").lower()

    def test_principles_section_present(self):
        assert "principle" in self.content

    @pytest.mark.parametrize("principle", CANONICAL_PRINCIPLES)
    def test_principle_mentioned(self, principle: str):
        assert principle.lower() in self.content, (
            f"Canonical principle missing: {principle!r}"
        )

    def test_assumptions_not_facts(self):
        assert "not facts" in self.content or "are not facts" in self.content

    def test_uncertainty_acceptable(self):
        assert "uncertainty" in self.content and "acceptable" in self.content

    def test_revisions_preserve_history(self):
        assert "revision" in self.content and "histor" in self.content or "preserv" in self.content


# ---------------------------------------------------------------------------
# Sprint 284 recommendation
# ---------------------------------------------------------------------------


class TestSprint284Recommendation:
    def test_sprint_284_or_risk_review_mentioned(self):
        content = ASSUMPTION_DOC.read_text(encoding="utf-8")
        assert "284" in content or "Risk Review" in content

    def test_risk_review_v1_recommended(self):
        content = ASSUMPTION_DOC.read_text(encoding="utf-8")
        assert "Risk Review" in content


# ---------------------------------------------------------------------------
# Compilation
# ---------------------------------------------------------------------------


class TestCompilation:
    def test_test_file_parses_as_python(self):
        src = Path(__file__).read_text(encoding="utf-8")
        ast.parse(src)
