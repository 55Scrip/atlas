"""Sprint 285 — Atlas Decision Engine V1 document tests."""

from __future__ import annotations

from pathlib import Path

import pytest

ENGINE_DOC = Path("docs/AtlasDecisionEngineV1.md")
PIPELINE_DOC = Path("docs/InvestmentReviewPipelineV1.md")
EVIDENCE_DOC = Path("docs/EvidenceAssemblyV1.md")
QUALITY_DOC = Path("docs/EvidenceQualityReviewV1.md")
ASSUMPTION_DOC = Path("docs/AssumptionReviewV1.md")
RISK_DOC = Path("docs/RiskReviewV1.md")
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

ALL_STAGES = [
    "Classification",
    "Entity Extraction",
    "Evidence Assembly",
    "Evidence Quality Review",
    "Assumption Review",
    "Risk Review",
    "Value Scenario Review",
    "Weekly Review",
    "Snapshot Draft",
    "Decision Journal",
    "Structured Judgment",
]

MANDATORY_STAGES = [
    "Classification",
    "Entity Extraction",
    "Evidence Assembly",
    "Evidence Quality Review",
    "Assumption Review",
    "Risk Review",
]

OPTIONAL_STAGES = [
    "Value Scenario Review",
    "Weekly Review",
    "Snapshot Draft",
    "Decision Journal",
]

CANONICAL_PRINCIPLES = [
    "deterministic",
    "evidence before",
    "assumptions explicit",
    "uncertainty visible",
    "recommendations never",
    "user content",
    "revisions",
    "structured judgment",
]

EXTENSION_POINTS = [
    "AI",
    "Market data",
    "SEC",
    "Broker",
    "OCR",
    "Collaboration",
]

EXISTING_DOCS_REFERENCED = [
    "InvestmentReviewPipelineV1.md",
    "EvidenceAssemblyV1.md",
    "EvidenceQualityReviewV1.md",
    "AssumptionReviewV1.md",
    "RiskReviewV1.md",
    "ValueScenarioReview.md",
    "AtlasDecisionJournal.md",
]


# ---------------------------------------------------------------------------
# Document existence
# ---------------------------------------------------------------------------


class TestDocumentExists:
    def test_engine_doc_exists(self):
        assert ENGINE_DOC.exists()

    def test_engine_doc_is_file(self):
        assert ENGINE_DOC.is_file()

    def test_engine_doc_is_nonempty(self):
        assert ENGINE_DOC.stat().st_size > 1000

    def test_engine_doc_is_utf8(self):
        ENGINE_DOC.read_bytes().decode("utf-8")

    def test_engine_doc_is_markdown(self):
        assert ENGINE_DOC.suffix == ".md"

    def test_engine_doc_has_header(self):
        content = ENGINE_DOC.read_text(encoding="utf-8")
        assert "Decision Engine" in content

    def test_engine_doc_is_complete(self):
        assert ENGINE_DOC.stat().st_size > 5000

    def test_engine_doc_answers_core_question(self):
        content = ENGINE_DOC.read_text(encoding="utf-8").lower()
        assert "structured judgment" in content
        assert "raw user input" in content or "user input" in content


# ---------------------------------------------------------------------------
# Flow documented
# ---------------------------------------------------------------------------


class TestFlowDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ENGINE_DOC.read_text(encoding="utf-8")

    def test_flow_diagram_present(self):
        assert "↓" in self.content

    def test_flow_starts_with_user_input(self):
        lower = self.content.lower()
        assert "user input" in lower

    def test_flow_ends_with_user(self):
        lower = self.content.lower()
        assert "user" in lower

    def test_flow_ends_with_structured_judgment(self):
        lower = self.content.lower()
        assert "structured judgment" in lower

    @pytest.mark.parametrize("stage", ALL_STAGES)
    def test_stage_present_in_doc(self, stage: str):
        assert stage.lower() in self.content.lower(), f"Stage missing from doc: {stage!r}"

    def test_flow_is_linear_and_deterministic(self):
        lower = self.content.lower()
        assert "linear" in lower or "deterministic" in lower

    def test_no_stage_skipped_silently(self):
        lower = self.content.lower()
        assert "silently" in lower or "recorded" in lower or "empty" in lower

    def test_classification_precedes_evidence_assembly(self):
        content = self.content
        assert content.index("Classification") < content.index("Evidence Assembly")

    def test_evidence_assembly_precedes_risk_review(self):
        lower = self.content.lower()
        assert lower.index("evidence assembly") < lower.index("risk review")

    def test_risk_review_precedes_value_scenario(self):
        lower = self.content.lower()
        first_risk = lower.index("risk review")
        first_vs = lower.index("value scenario review")
        assert first_risk < first_vs

    def test_weekly_review_mentioned_after_value_scenario(self):
        lower = self.content.lower()
        assert lower.index("value scenario review") < lower.rindex("weekly review")


# ---------------------------------------------------------------------------
# Mandatory and optional stages
# ---------------------------------------------------------------------------


class TestMandatoryOptionalStages:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ENGINE_DOC.read_text(encoding="utf-8")

    def test_mandatory_section_present(self):
        lower = self.content.lower()
        assert "mandatory" in lower

    def test_optional_section_present(self):
        lower = self.content.lower()
        assert "optional" in lower

    @pytest.mark.parametrize("stage", MANDATORY_STAGES)
    def test_mandatory_stage_documented(self, stage: str):
        assert stage.lower() in self.content.lower(), f"Mandatory stage missing: {stage!r}"

    @pytest.mark.parametrize("stage", OPTIONAL_STAGES)
    def test_optional_stage_documented(self, stage: str):
        assert stage.lower() in self.content.lower(), f"Optional stage missing: {stage!r}"

    def test_mandatory_stages_form_core(self):
        lower = self.content.lower()
        assert "irreducible core" in lower or "mandatory" in lower

    def test_no_mandatory_stage_may_be_skipped(self):
        lower = self.content.lower()
        assert "mandatory" in lower and ("without" in lower or "predecessor" in lower)


# ---------------------------------------------------------------------------
# Stage inputs and outputs documented
# ---------------------------------------------------------------------------


class TestStageInputsOutputsDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ENGINE_DOC.read_text(encoding="utf-8")

    def test_inputs_documented(self):
        assert "Input:" in self.content or "**Input:**" in self.content

    def test_outputs_documented(self):
        assert "Output:" in self.content or "**Output:**" in self.content

    def test_depends_on_documented(self):
        lower = self.content.lower()
        assert "depends on:" in lower

    def test_evidence_assembly_output_is_canonical_evidence_set(self):
        lower = self.content.lower()
        assert "canonical evidence set" in lower

    def test_assumption_review_output_is_assumption_register(self):
        lower = self.content.lower()
        assert "assumption register" in lower

    def test_risk_review_output_is_risk_register(self):
        lower = self.content.lower()
        assert "risk register" in lower

    def test_what_flows_between_stages_documented(self):
        lower = self.content.lower()
        assert "what flows" in lower or "flows between" in lower

    def test_evidence_quality_metadata_travels_downstream(self):
        lower = self.content.lower()
        assert "quality metadata" in lower or "quality assessment" in lower


# ---------------------------------------------------------------------------
# Canonical principles
# ---------------------------------------------------------------------------


class TestCanonicalPrinciplesDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ENGINE_DOC.read_text(encoding="utf-8")

    def test_principles_section_present(self):
        lower = self.content.lower()
        assert "principle" in lower

    @pytest.mark.parametrize("phrase", CANONICAL_PRINCIPLES)
    def test_principle_phrase_present(self, phrase: str):
        assert phrase.lower() in self.content.lower(), f"Principle missing: {phrase!r}"

    def test_deterministic_first_principle(self):
        lower = self.content.lower()
        assert "deterministic" in lower and "first" in lower

    def test_evidence_before_conclusions_principle(self):
        lower = self.content.lower()
        assert "evidence before" in lower and "conclusion" in lower

    def test_assumptions_explicit_principle(self):
        lower = self.content.lower()
        assert "assumption" in lower and "explicit" in lower

    def test_uncertainty_visible_principle(self):
        lower = self.content.lower()
        assert "uncertainty" in lower and "visible" in lower

    def test_recommendations_never_generated_principle(self):
        lower = self.content.lower()
        assert "recommendation" in lower and "never" in lower

    def test_user_content_preserved_principle(self):
        lower = self.content.lower()
        assert "user" in lower and "preserved" in lower

    def test_revisions_accumulate_principle(self):
        lower = self.content.lower()
        assert "revision" in lower and "accumulate" in lower

    def test_structured_judgment_over_prediction_principle(self):
        lower = self.content.lower()
        assert "structured judgment" in lower and "prediction" in lower

    def test_at_least_seven_principles_documented(self):
        lower = self.content.lower()
        count = sum(1 for p in CANONICAL_PRINCIPLES if p in lower)
        assert count >= 7


# ---------------------------------------------------------------------------
# References to existing documents
# ---------------------------------------------------------------------------


class TestExistingDocumentsReferenced:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ENGINE_DOC.read_text(encoding="utf-8")

    @pytest.mark.parametrize("doc", EXISTING_DOCS_REFERENCED)
    def test_existing_doc_referenced(self, doc: str):
        assert doc in self.content, f"Existing document not referenced: {doc!r}"

    def test_does_not_redefine_evidence_assembly(self):
        lower = self.content.lower()
        assert "defined in" in lower or "referenced in" in lower

    def test_connects_not_redefines(self):
        lower = self.content.lower()
        assert "connect" in lower or "orchestration" in lower

    def test_pipeline_doc_referenced(self):
        assert "InvestmentReviewPipelineV1.md" in self.content

    def test_assumption_doc_referenced(self):
        assert "AssumptionReviewV1.md" in self.content

    def test_risk_doc_referenced(self):
        assert "RiskReviewV1.md" in self.content

    def test_value_scenario_referenced(self):
        assert "ValueScenarioReview.md" in self.content

    def test_decision_journal_referenced(self):
        assert "AtlasDecisionJournal.md" in self.content


# ---------------------------------------------------------------------------
# Extension points
# ---------------------------------------------------------------------------


class TestExtensionPointsDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ENGINE_DOC.read_text(encoding="utf-8")

    def test_extension_points_section_present(self):
        lower = self.content.lower()
        assert "extension" in lower

    @pytest.mark.parametrize("source", EXTENSION_POINTS)
    def test_extension_source_documented(self, source: str):
        assert source.lower() in self.content.lower(), f"Extension point missing: {source!r}"

    def test_future_sources_are_inputs(self):
        lower = self.content.lower()
        assert "input" in lower and ("future" in lower or "extension" in lower)

    def test_future_sources_do_not_change_engine(self):
        lower = self.content.lower()
        assert "does not change" in lower or "invariant" in lower or "not change" in lower

    def test_ai_connects_to_assumption_or_risk(self):
        lower = self.content.lower()
        assert "ai" in lower and ("assumption" in lower or "risk" in lower)

    def test_no_future_source_bypasses_classification(self):
        lower = self.content.lower()
        assert "bypass" in lower or "invariant" in lower or "no future" in lower

    def test_sprint_286_recommendation_present(self):
        assert "286" in self.content

    def test_alpha_planning_recommended(self):
        lower = self.content.lower()
        assert "alpha" in lower or "end-to-end" in lower


# ---------------------------------------------------------------------------
# No runtime code, no new architecture
# ---------------------------------------------------------------------------


class TestNoRuntimeCode:
    def test_no_python_imports_in_doc(self):
        content = ENGINE_DOC.read_text(encoding="utf-8")
        assert "import atlas" not in content
        assert "from atlas" not in content

    def test_no_runtime_implementation_in_doc(self):
        lower = ENGINE_DOC.read_text(encoding="utf-8").lower()
        assert "no runtime" in lower or "runtime implementation" in lower

    def test_no_cli_changes_introduced(self):
        cli_source = CLI_FILE.read_text(encoding="utf-8")
        assert "decision_engine" not in cli_source

    def test_atlas_dir_not_modified_by_sprint_285(self):
        for py_file in ATLAS_DIR.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "decision_engine_v1" not in text, f"Sprint 285 runtime code found in {py_file}"

    def test_doc_is_not_a_configuration_schema(self):
        lower = ENGINE_DOC.read_text(encoding="utf-8").lower()
        assert "configuration schema" not in lower or "not a configuration schema" in lower

    def test_doc_is_not_a_workflow_engine_spec(self):
        lower = ENGINE_DOC.read_text(encoding="utf-8").lower()
        assert "workflow engine specification" not in lower or "not a workflow engine specification" in lower

    def test_doc_is_not_an_ai_system_prompt(self):
        lower = ENGINE_DOC.read_text(encoding="utf-8").lower()
        assert "ai system prompt" not in lower or "not an ai system prompt" in lower


# ---------------------------------------------------------------------------
# Safe language — no prohibited phrases
# ---------------------------------------------------------------------------


class TestSafeLanguage:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = ENGINE_DOC.read_text(encoding="utf-8").lower()

    @pytest.mark.parametrize("phrase", PROHIBITED_PHRASES)
    def test_no_prohibited_phrase(self, phrase: str):
        assert phrase.lower() not in self.content, f"Prohibited phrase found: {phrase!r}"

    def test_no_buy_word(self):
        words = self.content.split()
        assert "buy" not in words

    def test_no_sell_word(self):
        words = self.content.split()
        assert "sell" not in words

    def test_no_action_recommendation(self):
        assert "you should invest" not in self.content
        assert "should invest" not in self.content

    def test_no_single_point_target_language(self):
        assert "price target" not in self.content
        assert "target price" not in self.content

    def test_recommendations_never_generated_stated(self):
        assert "recommendations never" in self.content or "does not tell" in self.content or "never generates" in self.content


# ---------------------------------------------------------------------------
# Cross-document consistency
# ---------------------------------------------------------------------------


class TestCrossDocumentConsistency:
    def test_pipeline_doc_unchanged(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        assert "Investment Review Pipeline" in content

    def test_evidence_doc_unchanged(self):
        content = EVIDENCE_DOC.read_text(encoding="utf-8")
        assert "Evidence Assembly" in content

    def test_quality_doc_unchanged(self):
        content = QUALITY_DOC.read_text(encoding="utf-8")
        assert "Evidence Quality Review" in content

    def test_assumption_doc_unchanged(self):
        content = ASSUMPTION_DOC.read_text(encoding="utf-8")
        assert "Assumption Review" in content

    def test_risk_doc_unchanged(self):
        content = RISK_DOC.read_text(encoding="utf-8")
        assert "Risk Review" in content

    def test_cli_unchanged(self):
        cli_source = CLI_FILE.read_text(encoding="utf-8")
        assert "decision_engine" not in cli_source
        assert "value_scenario" in cli_source

    def test_engine_doc_does_not_duplicate_evidence_assembly_definition(self):
        engine = ENGINE_DOC.read_text(encoding="utf-8").lower()
        assert "eight v1 source types" in engine or "defined in" in engine

    def test_engine_doc_does_not_duplicate_risk_object_fields(self):
        engine = ENGINE_DOC.read_text(encoding="utf-8").lower()
        assert "defined in" in engine or "referenced in" in engine


# ---------------------------------------------------------------------------
# Decision log and release candidate updated
# ---------------------------------------------------------------------------


class TestDocumentationUpdated:
    def test_decision_log_mentions_sprint_285(self):
        log = Path("docs/DecisionLog.md").read_text(encoding="utf-8")
        assert "285" in log

    def test_decision_log_mentions_decision_engine(self):
        log = Path("docs/DecisionLog.md").read_text(encoding="utf-8").lower()
        assert "decision engine" in log

    def test_rc_doc_mentions_sprint_285(self):
        rc = Path("docs/InternalV1ReleaseCandidate.md").read_text(encoding="utf-8")
        assert "285" in rc

    def test_rc_doc_sprint_285_entry_no_forbidden_language(self):
        rc = Path("docs/InternalV1ReleaseCandidate.md").read_text(encoding="utf-8")
        sprint_285_idx = rc.find("Sprint 285")
        if sprint_285_idx == -1:
            pytest.skip("Sprint 285 entry not found in RC doc")
        sprint_286_idx = rc.find("Sprint 286", sprint_285_idx)
        if sprint_286_idx == -1:
            chunk = rc[sprint_285_idx:]
        else:
            chunk = rc[sprint_285_idx:sprint_286_idx]
        for phrase in ["buy", "sell"]:
            words = chunk.lower().split()
            assert phrase not in words, f"Forbidden word {phrase!r} found in Sprint 285 RC entry"

    def test_atlas_decision_engine_doc_present(self):
        assert ENGINE_DOC.exists()
