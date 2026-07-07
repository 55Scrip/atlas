"""Sprint 281 — Evidence Assembly V1 document tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

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

EVIDENCE_CATEGORIES = [
    "Company Facts",
    "Research Notes",
    "Decision Journal",
    "Portfolio",
    "Watchlist",
    "Weekly Review",
    "Snapshot",
    "User",
    "Historical",
    "External",
]

INFORMATION_TYPES = [
    "Evidence",
    "Observation",
    "Assumption",
    "Question",
    "Hypothesis",
    "Risk",
    "Opinion",
    "Decision",
]

ASSEMBLY_FLOW_STEPS = [
    "Extract",
    "Normaliz",
    "Deduplicat",
    "Source",
    "Preserv",
    "Canonical",
]

EVIDENCE_QUALITY_FACTORS = [
    "freshness",
    "source quality",
    "conflicting",
    "missing",
    "traceability",
]

SOURCE_TYPES = [
    "company_facts",
    "research_notes",
    "journal",
    "portfolio",
    "weekly_review",
    "snapshot",
]

FUTURE_EXTENSIONS = [
    "SEC",
    "earnings",
    "broker",
    "OCR",
    "AI",
    "market data",
]

CANONICAL_PRINCIPLES = [
    "evidence before conclusions",
    "provenance",
    "user wording",
    "conflict",
    "uncertainty",
    "missing evidence",
    "history",
    "deterministic",
]


# ---------------------------------------------------------------------------
# Document existence
# ---------------------------------------------------------------------------


class TestDocumentExists:
    def test_evidence_doc_exists(self):
        assert EVIDENCE_DOC.exists()

    def test_evidence_doc_is_file(self):
        assert EVIDENCE_DOC.is_file()

    def test_evidence_doc_is_nonempty(self):
        assert EVIDENCE_DOC.stat().st_size > 1000

    def test_evidence_doc_is_utf8(self):
        EVIDENCE_DOC.read_bytes().decode("utf-8")

    def test_evidence_doc_is_markdown(self):
        assert EVIDENCE_DOC.suffix == ".md"


# ---------------------------------------------------------------------------
# Evidence categories documented
# ---------------------------------------------------------------------------


class TestEvidenceCategoriesDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = EVIDENCE_DOC.read_text(encoding="utf-8")

    @pytest.mark.parametrize("category", EVIDENCE_CATEGORIES)
    def test_category_mentioned(self, category: str):
        assert category in self.content, f"Evidence category missing: {category!r}"

    def test_company_facts_purpose_described(self):
        content_lower = self.content.lower()
        assert "company facts" in content_lower
        assert "purpose" in content_lower or "structured" in content_lower

    def test_research_notes_described(self):
        assert "Research Notes" in self.content

    def test_decision_journal_described(self):
        assert "Decision Journal" in self.content

    def test_portfolio_holdings_described(self):
        assert "Portfolio" in self.content

    def test_watchlist_described(self):
        assert "Watchlist" in self.content

    def test_weekly_review_observations_described(self):
        assert "Weekly Review" in self.content

    def test_snapshot_drafts_described(self):
        assert "Snapshot" in self.content

    def test_historical_revisions_described(self):
        assert "Historical" in self.content or "revision" in self.content.lower()

    def test_external_documents_mentioned(self):
        assert "External" in self.content or "external" in self.content.lower()

    def test_at_least_eight_categories(self):
        count = sum(1 for c in EVIDENCE_CATEGORIES if c in self.content)
        assert count >= 8

    def test_freshness_described_per_category(self):
        assert "freshness" in self.content.lower() or "fresh" in self.content.lower()

    def test_strengths_weaknesses_described(self):
        lower = self.content.lower()
        assert "strength" in lower
        assert "weakness" in lower


# ---------------------------------------------------------------------------
# Evidence vs assumption distinction
# ---------------------------------------------------------------------------


class TestEvidenceVsAssumptionDistinction:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = EVIDENCE_DOC.read_text(encoding="utf-8")

    @pytest.mark.parametrize("info_type", INFORMATION_TYPES)
    def test_information_type_mentioned(self, info_type: str):
        assert info_type in self.content, f"Information type missing: {info_type!r}"

    def test_evidence_vs_opinion_example(self):
        lower = self.content.lower()
        assert "opinion" in lower

    def test_evidence_vs_assumption_example(self):
        lower = self.content.lower()
        assert "assumption" in lower

    def test_example_of_evidence_present(self):
        # Document must show a concrete evidence example
        assert "revenue grew" in self.content.lower() or "revenue" in self.content.lower()

    def test_example_of_opinion_present(self):
        lower = self.content.lower()
        assert "probably" in lower or "undervalued" in lower or "opinion" in lower

    def test_example_of_assumption_present(self):
        lower = self.content.lower()
        assert "ai demand" in lower or "demand continues" in lower or "assumption" in lower

    def test_example_of_question_present(self):
        lower = self.content.lower()
        assert "verify" in lower or "question" in lower

    def test_types_are_distinct(self):
        # All eight types must be named
        for t in INFORMATION_TYPES:
            assert t in self.content

    def test_not_interchangeable_stated(self):
        lower = self.content.lower()
        assert "not interchangeable" in lower or "distinct" in lower or "not the same" in lower


# ---------------------------------------------------------------------------
# Evidence assembly flow documented
# ---------------------------------------------------------------------------


class TestAssemblyFlowDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = EVIDENCE_DOC.read_text(encoding="utf-8")

    def test_flow_diagram_present(self):
        assert "↓" in self.content

    def test_raw_input_in_flow(self):
        lower = self.content.lower()
        assert "raw input" in lower or "input" in lower

    @pytest.mark.parametrize("step", ASSEMBLY_FLOW_STEPS)
    def test_flow_step_present(self, step: str):
        assert step.lower() in self.content.lower(), f"Flow step missing: {step!r}"

    def test_canonical_evidence_set_named(self):
        assert "Canonical Evidence Set" in self.content or "canonical evidence set" in self.content.lower()

    def test_evidence_quality_review_at_end_of_flow(self):
        content = self.content
        canonical_pos = content.lower().find("canonical evidence set")
        quality_pos = content.lower().find("evidence quality review")
        assert canonical_pos != -1
        assert quality_pos != -1
        assert canonical_pos < quality_pos

    def test_flow_is_deterministic(self):
        lower = self.content.lower()
        assert "deterministic" in lower

    def test_no_ai_required_for_flow(self):
        lower = self.content.lower()
        assert "no ai required" in lower or "no ai is required" in lower or "ai is not required" in lower or "ai optional" in lower or "without ai" in lower or "no ai" in lower


# ---------------------------------------------------------------------------
# Provenance and traceability documented
# ---------------------------------------------------------------------------


class TestProvenanceDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = EVIDENCE_DOC.read_text(encoding="utf-8")

    def test_provenance_mentioned(self):
        assert "provenance" in self.content.lower()

    def test_traceability_mentioned(self):
        assert "traceab" in self.content.lower()

    @pytest.mark.parametrize("source_type", SOURCE_TYPES)
    def test_source_type_mentioned(self, source_type: str):
        assert source_type in self.content, f"Source type missing: {source_type!r}"

    def test_source_reference_mentioned(self):
        lower = self.content.lower()
        assert "source reference" in lower or "source_reference" in lower

    def test_evidence_date_mentioned(self):
        lower = self.content.lower()
        assert "date" in lower

    def test_no_source_means_not_evidence(self):
        lower = self.content.lower()
        assert "no traceable source" in lower or "without a source" in lower or "not evidence" in lower


# ---------------------------------------------------------------------------
# User content preservation documented
# ---------------------------------------------------------------------------


class TestUserContentPreservationDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = EVIDENCE_DOC.read_text(encoding="utf-8")

    def test_user_content_preserved_stated(self):
        lower = self.content.lower()
        assert "preserved" in lower
        assert "user" in lower

    def test_no_rewriting_stated(self):
        lower = self.content.lower()
        assert "never rewr" in lower or "not rewr" in lower or "never silently" in lower

    def test_verbatim_preservation_mentioned(self):
        lower = self.content.lower()
        assert "verbatim" in lower

    def test_attribution_mentioned(self):
        lower = self.content.lower()
        assert "attribution" in lower or "attributed" in lower or "referenc" in lower


# ---------------------------------------------------------------------------
# Future extension points documented
# ---------------------------------------------------------------------------


class TestFutureExtensionPointsDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = EVIDENCE_DOC.read_text(encoding="utf-8")

    def test_future_extensions_section_present(self):
        lower = self.content.lower()
        assert "future" in lower and "extension" in lower

    @pytest.mark.parametrize("extension", FUTURE_EXTENSIONS)
    def test_extension_mentioned(self, extension: str):
        assert extension.lower() in self.content.lower(), f"Future extension missing: {extension!r}"

    def test_extensions_do_not_bypass_assembly(self):
        lower = self.content.lower()
        assert "do not bypass" in lower or "not bypass" in lower or "does not bypass" in lower

    def test_extensions_do_not_skip_quality_review(self):
        lower = self.content.lower()
        assert "quality review" in lower or "evidence quality" in lower


# ---------------------------------------------------------------------------
# Canonical principles documented
# ---------------------------------------------------------------------------


class TestCanonicalPrinciplesDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = EVIDENCE_DOC.read_text(encoding="utf-8")

    def test_principles_section_present(self):
        lower = self.content.lower()
        assert "principle" in lower

    @pytest.mark.parametrize("principle", CANONICAL_PRINCIPLES)
    def test_principle_mentioned(self, principle: str):
        assert principle.lower() in self.content.lower(), (
            f"Canonical principle missing: {principle!r}"
        )

    def test_missing_evidence_is_evidence_principle(self):
        lower = self.content.lower()
        assert "missing evidence" in lower

    def test_uncertainty_allowed_principle(self):
        lower = self.content.lower()
        assert "uncertainty" in lower

    def test_revisions_preserve_history_principle(self):
        lower = self.content.lower()
        assert "revision" in lower and "histor" in lower

    def test_newer_does_not_replace_older_principle(self):
        lower = self.content.lower()
        assert "not automatically replace" in lower or "does not automatically" in lower or "newer" in lower


# ---------------------------------------------------------------------------
# No recommendation language
# ---------------------------------------------------------------------------


class TestNoRecommendationLanguage:
    @pytest.mark.parametrize("phrase", PROHIBITED_PHRASES)
    def test_no_prohibited_phrase(self, phrase: str):
        content = EVIDENCE_DOC.read_text(encoding="utf-8").lower()
        assert phrase.lower() not in content, (
            f"Prohibited phrase {phrase!r} found in evidence assembly document"
        )

    def test_no_buy_sell_language(self):
        lower = EVIDENCE_DOC.read_text(encoding="utf-8").lower()
        for phrase in ["buy this", "sell this", "should buy", "should sell"]:
            assert phrase not in lower

    def test_evidence_independent_of_recommendations(self):
        lower = EVIDENCE_DOC.read_text(encoding="utf-8").lower()
        assert "independent of recommendation" in lower or "before any recommendation" in lower or "independent" in lower


# ---------------------------------------------------------------------------
# No runtime code added
# ---------------------------------------------------------------------------


class TestNoRuntimeCodeAdded:
    def test_no_new_cli_commands(self):
        cli_source = CLI_FILE.read_text(encoding="utf-8")
        assert "evidence_assembly" not in cli_source
        assert "evidence-assembly" not in cli_source

    def test_no_new_evidence_module(self):
        evidence_module = ATLAS_DIR / "evidence_assembly"
        assert not evidence_module.exists()

    def test_document_is_markdown_not_python(self):
        assert EVIDENCE_DOC.suffix == ".md"

    def test_no_imports_added_to_atlas(self):
        for src_file in ATLAS_DIR.rglob("*.py"):
            content = src_file.read_text(encoding="utf-8")
            assert "EvidenceAssembly" not in content

    def test_no_ai_imports_added(self):
        for src_file in ATLAS_DIR.rglob("*.py"):
            content = src_file.read_text(encoding="utf-8")
            for forbidden in ["import openai", "import anthropic", "import langchain"]:
                assert forbidden not in content


# ---------------------------------------------------------------------------
# Relationship to pipeline documented
# ---------------------------------------------------------------------------


class TestPipelineRelationshipDocumented:
    def test_pipeline_reference_present(self):
        content = EVIDENCE_DOC.read_text(encoding="utf-8")
        assert "Pipeline" in content or "pipeline" in content.lower()

    def test_stage_4_reference(self):
        content = EVIDENCE_DOC.read_text(encoding="utf-8")
        assert "Stage 4" in content or "stage 4" in content.lower()

    def test_pipeline_doc_referenced(self):
        content = EVIDENCE_DOC.read_text(encoding="utf-8")
        assert "InvestmentReviewPipeline" in content or "Investment Review Pipeline" in content

    def test_pipeline_doc_exists(self):
        assert PIPELINE_DOC.exists()


# ---------------------------------------------------------------------------
# Evidence quality inputs documented
# ---------------------------------------------------------------------------


class TestEvidenceQualityInputsDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = EVIDENCE_DOC.read_text(encoding="utf-8").lower()

    @pytest.mark.parametrize("factor", EVIDENCE_QUALITY_FACTORS)
    def test_quality_factor_mentioned(self, factor: str):
        assert factor.lower() in self.content, f"Quality factor missing: {factor!r}"

    def test_no_scoring_at_this_stage(self):
        assert "no scoring" in self.content or "not scored" in self.content or "do not score" in self.content

    def test_no_calculation_at_this_stage(self):
        assert (
            "no calculation" in self.content
            or "not calculat" in self.content
            or "do not calculat" in self.content
            or "not a calculation" in self.content
        )


# ---------------------------------------------------------------------------
# Sprint 282 recommendation
# ---------------------------------------------------------------------------


class TestSprint282Recommendation:
    def test_sprint_282_or_evidence_quality_review_mentioned(self):
        content = EVIDENCE_DOC.read_text(encoding="utf-8")
        assert "282" in content or "Evidence Quality Review" in content

    def test_evidence_quality_review_recommended(self):
        content = EVIDENCE_DOC.read_text(encoding="utf-8")
        assert "Evidence Quality Review" in content


# ---------------------------------------------------------------------------
# Compilation
# ---------------------------------------------------------------------------


class TestCompilation:
    def test_test_file_parses_as_python(self):
        src = Path(__file__).read_text(encoding="utf-8")
        ast.parse(src)
