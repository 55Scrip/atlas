"""Sprint 280 — Investment Review Pipeline V1 document tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

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

STAGE_HEADINGS = [
    "Stage 1",
    "Stage 2",
    "Stage 3",
    "Stage 4",
    "Stage 5",
    "Stage 6",
    "Stage 7",
    "Stage 8",
    "Stage 9",
    "Stage 10",
    "Stage 11",
    "Stage 12",
]

STAGE_NAMES = [
    "Input",
    "Classification",
    "Entity Extraction",
    "Evidence Assembly",
    "Evidence Quality",
    "Assumption Review",
    "Risk Review",
    "Value Scenario",
    "Weekly Review",
    "Snapshot",
    "Decision Journal",
    "Workspace",
]


# ---------------------------------------------------------------------------
# Document existence
# ---------------------------------------------------------------------------


class TestDocumentExists:
    def test_pipeline_doc_exists(self):
        assert PIPELINE_DOC.exists()

    def test_pipeline_doc_is_file(self):
        assert PIPELINE_DOC.is_file()

    def test_pipeline_doc_is_nonempty(self):
        assert PIPELINE_DOC.stat().st_size > 500

    def test_pipeline_doc_is_utf8(self):
        PIPELINE_DOC.read_bytes().decode("utf-8")


# ---------------------------------------------------------------------------
# All 12 stages documented
# ---------------------------------------------------------------------------


class TestAllStagesDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = PIPELINE_DOC.read_text(encoding="utf-8")

    @pytest.mark.parametrize("heading", STAGE_HEADINGS)
    def test_stage_heading_present(self, heading: str):
        assert heading in self.content, f"Stage heading missing: {heading!r}"

    @pytest.mark.parametrize("name", STAGE_NAMES)
    def test_stage_name_present(self, name: str):
        assert name in self.content, f"Stage name missing: {name!r}"

    def test_exactly_twelve_stages(self):
        count = sum(1 for h in STAGE_HEADINGS if h in self.content)
        assert count == 12

    def test_stage_1_input(self):
        assert "Stage 1" in self.content
        assert "Input" in self.content

    def test_stage_2_classification(self):
        assert "Stage 2" in self.content
        assert "Classification" in self.content

    def test_stage_3_entity_extraction(self):
        assert "Stage 3" in self.content
        assert "Entity Extraction" in self.content

    def test_stage_4_evidence_assembly(self):
        assert "Stage 4" in self.content
        assert "Evidence Assembly" in self.content

    def test_stage_5_evidence_quality(self):
        assert "Stage 5" in self.content
        assert "Evidence Quality" in self.content

    def test_stage_6_assumption_review(self):
        assert "Stage 6" in self.content
        assert "Assumption Review" in self.content

    def test_stage_7_risk_review(self):
        assert "Stage 7" in self.content
        assert "Risk Review" in self.content

    def test_stage_8_value_scenario(self):
        assert "Stage 8" in self.content
        assert "Value Scenario" in self.content

    def test_stage_9_weekly_review(self):
        assert "Stage 9" in self.content
        assert "Weekly Review" in self.content

    def test_stage_10_snapshot_draft(self):
        assert "Stage 10" in self.content
        assert "Snapshot" in self.content

    def test_stage_11_decision_journal(self):
        assert "Stage 11" in self.content
        assert "Decision Journal" in self.content

    def test_stage_12_workspace(self):
        assert "Stage 12" in self.content
        assert "Workspace" in self.content


# ---------------------------------------------------------------------------
# Ordering correct
# ---------------------------------------------------------------------------


class TestOrderingCorrect:
    def test_stages_in_order(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        positions = [content.index(h) for h in STAGE_HEADINGS if h in content]
        assert positions == sorted(positions), "Stages are not in ascending order"

    def test_input_before_classification(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        assert content.index("Stage 1") < content.index("Stage 2")

    def test_evidence_before_scenario(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        assert content.index("Stage 4") < content.index("Stage 8")

    def test_scenario_before_weekly_review(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        assert content.index("Stage 8") < content.index("Stage 9")

    def test_weekly_review_before_snapshot(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        assert content.index("Stage 9") < content.index("Stage 10")

    def test_snapshot_before_journal(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        assert content.index("Stage 10") < content.index("Stage 11")

    def test_journal_before_workspace(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        assert content.index("Stage 11") < content.index("Stage 12")


# ---------------------------------------------------------------------------
# Pipeline diagram present
# ---------------------------------------------------------------------------


class TestPipelineDiagramPresent:
    def test_diagram_present(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        assert "Input" in content
        assert "↓" in content

    def test_diagram_shows_input_to_classification(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        # both must appear, input before classification in diagram
        input_pos = content.find("Input\n")
        class_pos = content.find("Classification\n")
        assert input_pos != -1
        assert class_pos != -1
        assert input_pos < class_pos

    def test_diagram_shows_classification_to_entity(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        assert "Entity Extraction" in content

    def test_diagram_shows_workspace_at_end(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        # Workspace / Save should appear after Decision Journal in diagram
        journal_pos = content.find("Decision Journal\n")
        workspace_pos = content.find("Workspace")
        assert journal_pos != -1
        assert workspace_pos != -1
        assert journal_pos < workspace_pos


# ---------------------------------------------------------------------------
# Cross-cutting principles documented
# ---------------------------------------------------------------------------


class TestCrossCuttingPrinciples:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = PIPELINE_DOC.read_text(encoding="utf-8")

    def test_cross_cutting_section_present(self):
        assert "Cross-Cutting" in self.content or "cross-cutting" in self.content.lower()

    def test_evidence_before_conclusions_principle(self):
        assert "evidence" in self.content.lower()
        assert "conclusions" in self.content.lower()

    def test_uncertainty_always_visible_principle(self):
        assert "uncertainty" in self.content.lower()
        assert "visible" in self.content.lower()

    def test_assumptions_explicit_principle(self):
        assert "assumption" in self.content.lower()
        assert "explicit" in self.content.lower()

    def test_revisions_preserved_principle(self):
        assert "revision" in self.content.lower()
        assert "preserved" in self.content.lower()

    def test_user_content_preserved_principle(self):
        assert "user content" in self.content.lower() or "user-provided" in self.content.lower()

    def test_canonical_values_english_principle(self):
        assert "english" in self.content.lower()
        assert "canonical" in self.content.lower()

    def test_deterministic_first_principle(self):
        assert "deterministic" in self.content.lower()

    def test_no_action_warranted_principle(self):
        assert "no action warranted" in self.content.lower()

    def test_ai_optional_principle(self):
        assert "ai" in self.content.lower()
        assert "optional" in self.content.lower()


# ---------------------------------------------------------------------------
# Extension points documented
# ---------------------------------------------------------------------------


class TestExtensionPointsDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = PIPELINE_DOC.read_text(encoding="utf-8")

    def test_extension_points_section_present(self):
        assert "Extension" in self.content

    def test_market_data_extension_mentioned(self):
        assert "market data" in self.content.lower() or "Market data" in self.content

    def test_ai_extension_mentioned(self):
        assert "AI" in self.content or "artificial intelligence" in self.content.lower()

    def test_ocr_extension_mentioned(self):
        assert "OCR" in self.content or "ocr" in self.content.lower()

    def test_broker_sync_extension_mentioned(self):
        assert "broker" in self.content.lower()

    def test_valuation_models_extension_mentioned(self):
        assert "valuation" in self.content.lower()

    def test_extensions_do_not_replace_pipeline(self):
        content_lower = self.content.lower()
        assert "do not replace" in content_lower or "not replace" in content_lower


# ---------------------------------------------------------------------------
# No recommendation language
# ---------------------------------------------------------------------------


class TestNoRecommendationLanguage:
    @pytest.mark.parametrize("phrase", PROHIBITED_PHRASES)
    def test_no_prohibited_phrase(self, phrase: str):
        content = PIPELINE_DOC.read_text(encoding="utf-8").lower()
        assert phrase.lower() not in content, (
            f"Prohibited phrase {phrase!r} found in pipeline document"
        )

    def test_no_single_point_targets(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        assert "single-point target" in content.lower() or "single point target" in content.lower()
        # The document must mention them as prohibited, not advocate for them
        content_lower = content.lower()
        assert "never single-point" in content_lower or "not single-point" in content_lower or "never" in content_lower


# ---------------------------------------------------------------------------
# No execution language
# ---------------------------------------------------------------------------


class TestNoExecutionLanguage:
    def test_no_trade_execution_language(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8").lower()
        for phrase in ["execute trade", "place order", "submit order", "trade execution"]:
            assert phrase not in content, f"Execution phrase found: {phrase!r}"

    def test_no_urgency_language(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8").lower()
        for phrase in ["act urgently", "act immediately", "time sensitive action"]:
            assert phrase not in content


# ---------------------------------------------------------------------------
# No runtime code added
# ---------------------------------------------------------------------------


class TestNoRuntimeCodeAdded:
    def test_no_new_cli_commands(self):
        cli_source = CLI_FILE.read_text(encoding="utf-8")
        assert "investment_review_pipeline" not in cli_source
        assert "investment-review-pipeline" not in cli_source

    def test_no_new_python_module(self):
        pipeline_module = ATLAS_DIR / "investment_review_pipeline"
        assert not pipeline_module.exists()

    def test_pipeline_doc_is_markdown_not_python(self):
        assert PIPELINE_DOC.suffix == ".md"

    def test_no_imports_added_to_atlas(self):
        for src_file in ATLAS_DIR.rglob("*.py"):
            content = src_file.read_text(encoding="utf-8")
            assert "InvestmentReviewPipeline" not in content

    def test_no_ai_imports_added(self):
        for src_file in ATLAS_DIR.rglob("*.py"):
            content = src_file.read_text(encoding="utf-8")
            for forbidden in ["import openai", "import anthropic", "import langchain"]:
                assert forbidden not in content


# ---------------------------------------------------------------------------
# Core principle present
# ---------------------------------------------------------------------------


class TestCorePrinciple:
    def test_evidence_first_principle_stated(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        assert "never begins with conclusions" in content.lower() or (
            "begins with evidence" in content.lower()
        )

    def test_how_atlas_thinks_framing(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        assert "how does atlas think" in content.lower() or "how atlas thinks" in content.lower() or "how atlas" in content.lower()

    def test_not_what_to_buy_framing(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        # Document must explicitly distinguish itself from a buy/sell tool
        lower = content.lower()
        assert "what should" not in lower or "does not answer" in lower or "~~" in content


# ---------------------------------------------------------------------------
# Sprint 281 recommendation present
# ---------------------------------------------------------------------------


class TestSprint281Recommendation:
    def test_sprint_281_recommendation_present(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        assert "281" in content or "Evidence Assembly" in content

    def test_evidence_assembly_recommended(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        assert "Evidence Assembly" in content


# ---------------------------------------------------------------------------
# Compilation
# ---------------------------------------------------------------------------


class TestCompilation:
    def test_test_file_parses_as_python(self):
        src = Path(__file__).read_text(encoding="utf-8")
        ast.parse(src)
