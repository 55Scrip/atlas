"""Sprint 284 — Risk Review V1 document tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

RISK_DOC = Path("docs/RiskReviewV1.md")
ASSUMPTION_DOC = Path("docs/AssumptionReviewV1.md")
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

RISK_CATEGORIES = [
    "Business",
    "Financial",
    "Competitive",
    "Management",
    "Industry",
    "Regulatory",
    "Macro",
    "Valuation",
    "Portfolio Construction",
    "Behavioural",
]

FLOW_STEPS = [
    "Evidence",
    "Risk Identification",
    "Risk Classification",
    "Evidence Link",
    "Open Questions",
    "Monitoring Trigger",
    "Risk Register",
    "Value Scenario",
]

CANONICAL_PRINCIPLES = [
    "assumptions",
    "evidence",
    "uncertainty",
    "evolve",
    "history",
    "monitoring",
    "missing evidence",
    "revision",
]

RISK_OBJECT_FIELDS = [
    "category",
    "description",
    "linked_assumptions",
    "supporting_evidence",
    "conflicting_evidence",
    "evidence_quality",
    "uncertainty",
    "monitoring_triggers",
    "review_status",
    "revision_history",
]

MONITORING_TRIGGER_EXAMPLES = [
    "earnings",
    "guidance",
    "regulatory",
    "capital allocation",
    "management",
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

EXAMPLE_TITLES = [
    "Business execution",
    "Valuation",
    "Customer concentration",
    "Management succession",
    "Portfolio concentration",
]

WORKED_EXAMPLE_INDICATORS = [
    "Category:",
    "Description:",
    "Linked assumptions:",
    "Supporting evidence:",
    "Monitoring triggers:",
    "Review status:",
]


# ---------------------------------------------------------------------------
# Document existence
# ---------------------------------------------------------------------------


class TestDocumentExists:
    def test_risk_doc_exists(self):
        assert RISK_DOC.exists()

    def test_risk_doc_is_file(self):
        assert RISK_DOC.is_file()

    def test_risk_doc_is_nonempty(self):
        assert RISK_DOC.stat().st_size > 1000

    def test_risk_doc_is_utf8(self):
        RISK_DOC.read_bytes().decode("utf-8")

    def test_risk_doc_is_markdown(self):
        assert RISK_DOC.suffix == ".md"

    def test_risk_doc_has_header(self):
        content = RISK_DOC.read_text(encoding="utf-8")
        assert "Risk Review" in content

    def test_risk_doc_large_enough_to_be_complete(self):
        assert RISK_DOC.stat().st_size > 5000


# ---------------------------------------------------------------------------
# Risk categories
# ---------------------------------------------------------------------------


class TestRiskCategoriesDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = RISK_DOC.read_text(encoding="utf-8")

    @pytest.mark.parametrize("category", RISK_CATEGORIES)
    def test_category_mentioned(self, category: str):
        assert category in self.content, f"Risk category missing: {category!r}"

    def test_exactly_ten_categories(self):
        count = sum(1 for c in RISK_CATEGORIES if c in self.content)
        assert count == 10

    def test_business_risk_has_examples(self):
        lower = self.content.lower()
        assert "business" in lower
        assert "revenue" in lower or "customer" in lower

    def test_financial_risk_has_examples(self):
        lower = self.content.lower()
        assert "financial" in lower
        assert "margin" in lower or "cash" in lower or "revenue" in lower

    def test_competitive_risk_has_examples(self):
        lower = self.content.lower()
        assert "competitive" in lower
        assert "moat" in lower or "market share" in lower or "pricing" in lower

    def test_management_risk_has_examples(self):
        lower = self.content.lower()
        assert "management" in lower
        assert "capital allocation" in lower or "leadership" in lower or "succession" in lower

    def test_industry_risk_has_examples(self):
        lower = self.content.lower()
        assert "industry" in lower
        assert "demand" in lower or "cycle" in lower or "structure" in lower

    def test_regulatory_risk_has_examples(self):
        lower = self.content.lower()
        assert "regulatory" in lower
        assert "regulation" in lower or "licence" in lower or "compliance" in lower

    def test_macro_risk_has_examples(self):
        lower = self.content.lower()
        assert "macro" in lower
        assert "rate" in lower or "inflation" in lower or "currency" in lower

    def test_valuation_risk_has_examples(self):
        lower = self.content.lower()
        assert "valuation" in lower
        assert "multiple" in lower or "earnings" in lower

    def test_portfolio_construction_risk_has_examples(self):
        lower = self.content.lower()
        assert "portfolio construction" in lower or "portfolio" in lower
        assert "concentration" in lower or "position" in lower

    def test_behavioural_risk_has_examples(self):
        lower = self.content.lower()
        assert "behavioural" in lower or "behavioral" in lower
        assert "bias" in lower or "journal" in lower or "user" in lower

    def test_each_category_has_evidence_sources(self):
        lower = self.content.lower()
        assert "evidence source" in lower or "common evidence" in lower

    def test_each_category_has_assumption_dependencies(self):
        lower = self.content.lower()
        assert "assumption" in lower and "depend" in lower

    def test_each_category_has_purpose(self):
        lower = self.content.lower()
        assert "purpose" in lower


# ---------------------------------------------------------------------------
# Canonical risk object
# ---------------------------------------------------------------------------


class TestRiskObjectDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = RISK_DOC.read_text(encoding="utf-8")

    @pytest.mark.parametrize("field", RISK_OBJECT_FIELDS)
    def test_field_mentioned(self, field: str):
        assert field in self.content, f"Risk object field missing: {field!r}"

    def test_no_probability_field(self):
        lower = self.content.lower()
        assert "probability field" not in lower or "no probability" in lower or "no field accepts a numeric probability" in lower

    def test_no_scoring_field(self):
        lower = self.content.lower()
        assert "no scoring" in lower or "no score" in lower or "no field accepts" in lower

    def test_no_numeric_probability(self):
        lower = self.content.lower()
        assert "no field accepts a numeric probability" in lower or "no probability" in lower

    def test_risk_object_makes_risks_visible(self):
        lower = self.content.lower()
        assert "visible" in lower and "traceable" in lower

    def test_risk_object_does_not_rank(self):
        lower = self.content.lower()
        assert "does not rank" in lower or "not rank" in lower

    def test_review_status_values_present(self):
        lower = self.content.lower()
        assert "active" in lower
        assert "resolved" in lower or "obsolete" in lower

    def test_revision_history_described(self):
        lower = self.content.lower()
        assert "revision history" in lower

    def test_risk_id_field_present(self):
        assert "risk_id" in self.content

    def test_uncertainty_field_present(self):
        assert "uncertainty" in self.content

    def test_linked_assumptions_field_present(self):
        assert "linked_assumptions" in self.content


# ---------------------------------------------------------------------------
# Deterministic risk review flow
# ---------------------------------------------------------------------------


class TestRiskReviewFlowDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = RISK_DOC.read_text(encoding="utf-8")

    def test_flow_diagram_present(self):
        assert "↓" in self.content

    @pytest.mark.parametrize("step", FLOW_STEPS)
    def test_flow_step_present(self, step: str):
        assert step.lower() in self.content.lower(), f"Flow step missing: {step!r}"

    def test_flow_starts_with_evidence(self):
        lower = self.content.lower()
        assert "evidence" in lower

    def test_flow_produces_risk_register(self):
        lower = self.content.lower()
        assert "risk register" in lower

    def test_risk_register_feeds_value_scenario(self):
        lower = self.content.lower()
        assert "value scenario" in lower

    def test_flow_is_deterministic(self):
        lower = self.content.lower()
        assert "deterministic" in lower

    def test_flow_generates_no_recommendation(self):
        lower = self.content.lower()
        assert "no recommendation" in lower or "does not generate" in lower or "no step generates" in lower

    def test_flow_depends_on_assumption_review(self):
        lower = self.content.lower()
        assert "assumption" in lower

    def test_flow_depends_on_evidence_quality(self):
        lower = self.content.lower()
        assert "evidence quality" in lower


# ---------------------------------------------------------------------------
# Monitoring philosophy
# ---------------------------------------------------------------------------


class TestMonitoringPhilosophyDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = RISK_DOC.read_text(encoding="utf-8")

    def test_monitoring_section_present(self):
        lower = self.content.lower()
        assert "monitoring" in lower

    def test_monitoring_is_observational(self):
        lower = self.content.lower()
        assert "observational" in lower

    def test_monitoring_is_not_predictive(self):
        lower = self.content.lower()
        assert "not predictive" in lower

    def test_monitoring_does_not_predict_probability(self):
        lower = self.content.lower()
        assert "probability" in lower or "does not predict" in lower or "not forecast" in lower

    def test_monitoring_identifies_what_to_watch(self):
        lower = self.content.lower()
        assert "watch" in lower or "identify" in lower

    def test_monitoring_prompts_review(self):
        lower = self.content.lower()
        assert "prompt" in lower or "trigger" in lower

    @pytest.mark.parametrize("example", MONITORING_TRIGGER_EXAMPLES)
    def test_monitoring_trigger_example_present(self, example: str):
        assert example.lower() in self.content.lower(), f"Monitoring trigger example missing: {example!r}"

    def test_monitoring_does_not_produce_prediction(self):
        lower = self.content.lower()
        assert "does not produce" in lower or "not predict" in lower

    def test_monitoring_does_not_autochange_register(self):
        lower = self.content.lower()
        assert (
            "automatic" not in lower
            or "not automatic" in lower
            or "does not automatically" in lower
            or "automatic changes" in lower
        )

    def test_monitoring_does_not_produce_recommendation(self):
        lower = self.content.lower()
        assert "does not produce" in lower or "no recommendation" in lower or "investment recommendation" not in lower

    def test_monitoring_supports_revision_not_prediction(self):
        lower = self.content.lower()
        assert "supports revision" in lower or "revision" in lower


# ---------------------------------------------------------------------------
# Worked examples
# ---------------------------------------------------------------------------


class TestWorkedExamplesPresent:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = RISK_DOC.read_text(encoding="utf-8")

    def test_at_least_five_examples(self):
        lower = self.content.lower()
        count = lower.count("example")
        assert count >= 5

    def test_business_execution_example_present(self):
        lower = self.content.lower()
        assert "business execution" in lower

    def test_valuation_example_present(self):
        lower = self.content.lower()
        assert "valuation" in lower and "example" in lower

    def test_customer_concentration_example_present(self):
        lower = self.content.lower()
        assert "customer concentration" in lower

    def test_management_succession_example_present(self):
        lower = self.content.lower()
        assert "management succession" in lower

    def test_portfolio_concentration_example_present(self):
        lower = self.content.lower()
        assert "portfolio concentration" in lower

    @pytest.mark.parametrize("indicator", WORKED_EXAMPLE_INDICATORS)
    def test_example_indicator_present(self, indicator: str):
        assert indicator in self.content, f"Worked example field missing: {indicator!r}"

    def test_examples_include_linked_assumptions(self):
        lower = self.content.lower()
        assert "linked assumption" in lower

    def test_examples_include_monitoring_triggers(self):
        lower = self.content.lower()
        assert "monitoring trigger" in lower

    def test_examples_include_evidence_quality(self):
        lower = self.content.lower()
        assert "evidence quality" in lower

    def test_examples_include_review_status(self):
        lower = self.content.lower()
        assert "review status" in lower

    def test_examples_do_not_include_probability_scores(self):
        lower = self.content.lower()
        assert "probability:" not in lower

    def test_examples_do_not_include_severity_scores(self):
        lower = self.content.lower()
        if "severity score" in lower:
            assert "no field accepts a severity score" in lower or "no severity score" in lower
        assert "risk score" not in lower


# ---------------------------------------------------------------------------
# Canonical principles
# ---------------------------------------------------------------------------


class TestCanonicalPrinciplesDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = RISK_DOC.read_text(encoding="utf-8")

    def test_principles_section_present(self):
        lower = self.content.lower()
        assert "principle" in lower

    def test_at_least_seven_principles(self):
        lower = self.content.lower()
        count = lower.count("principle") + lower.count("###")
        assert count >= 7

    @pytest.mark.parametrize("phrase", CANONICAL_PRINCIPLES)
    def test_principle_concept_present(self, phrase: str):
        assert phrase.lower() in self.content.lower(), f"Principle concept missing: {phrase!r}"

    def test_every_risk_links_to_assumptions(self):
        lower = self.content.lower()
        assert "every material risk" in lower and "assumption" in lower

    def test_every_risk_links_to_evidence(self):
        lower = self.content.lower()
        assert "evidence" in lower and ("link" in lower or "linked" in lower)

    def test_uncertainty_is_visible(self):
        lower = self.content.lower()
        assert "uncertainty" in lower and "visible" in lower

    def test_risks_evolve_over_time(self):
        lower = self.content.lower()
        assert "evolve" in lower or "recurring" in lower

    def test_resolved_risks_stay_in_history(self):
        lower = self.content.lower()
        assert "resolved" in lower and ("history" in lower or "revision" in lower)

    def test_missing_evidence_may_be_risk(self):
        lower = self.content.lower()
        assert "missing evidence" in lower and "risk" in lower

    def test_monitoring_supports_revision_principle(self):
        lower = self.content.lower()
        assert "monitoring" in lower and "revision" in lower


# ---------------------------------------------------------------------------
# Pipeline relationship documented
# ---------------------------------------------------------------------------


class TestPipelineRelationshipDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = RISK_DOC.read_text(encoding="utf-8")

    def test_pipeline_stage_7_mentioned(self):
        lower = self.content.lower()
        assert "stage 7" in lower

    def test_assumption_review_stage_6_mentioned(self):
        lower = self.content.lower()
        assert "stage 6" in lower

    def test_value_scenario_stage_8_mentioned(self):
        lower = self.content.lower()
        assert "stage 8" in lower

    def test_evidence_assembly_stage_4_mentioned(self):
        lower = self.content.lower()
        assert "stage 4" in lower

    def test_evidence_quality_stage_5_mentioned(self):
        lower = self.content.lower()
        assert "stage 5" in lower

    def test_weekly_review_mentioned(self):
        lower = self.content.lower()
        assert "weekly review" in lower

    def test_depends_on_header_present(self):
        assert "Depends on:" in self.content

    def test_depends_on_assumption_review(self):
        assert "AssumptionReviewV1.md" in self.content

    def test_depends_on_evidence_quality_review(self):
        assert "EvidenceQualityReviewV1.md" in self.content

    def test_risk_register_feeds_value_scenario(self):
        lower = self.content.lower()
        assert "value scenario" in lower and "risk register" in lower


# ---------------------------------------------------------------------------
# Future extension points
# ---------------------------------------------------------------------------


class TestFutureExtensionPointsDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = RISK_DOC.read_text(encoding="utf-8")

    def test_future_extension_section_present(self):
        lower = self.content.lower()
        assert "extension" in lower

    @pytest.mark.parametrize("source", FUTURE_SOURCES)
    def test_future_source_mentioned(self, source: str):
        assert source.lower() in self.content.lower(), f"Future source missing: {source!r}"

    def test_future_sources_do_not_bypass_risk_review(self):
        lower = self.content.lower()
        assert "bypass" in lower or "does not bypass" in lower or "no future source bypasses" in lower

    def test_future_sources_supply_evidence(self):
        lower = self.content.lower()
        assert "supply evidence" in lower or "supply" in lower

    def test_sprint_285_recommendation_present(self):
        assert "285" in self.content or "Sprint 285" in self.content

    def test_decision_review_recommended_next(self):
        lower = self.content.lower()
        assert "decision review" in lower


# ---------------------------------------------------------------------------
# No runtime code, no scoring, no probability
# ---------------------------------------------------------------------------


class TestNoRuntimeCode:
    def test_no_python_imports_in_doc(self):
        content = RISK_DOC.read_text(encoding="utf-8")
        assert "import atlas" not in content
        assert "from atlas" not in content

    def test_no_runtime_code_statement(self):
        lower = RISK_DOC.read_text(encoding="utf-8").lower()
        assert "no runtime" in lower or "runtime implementation" in lower

    def test_no_cli_commands_in_doc(self):
        lower = RISK_DOC.read_text(encoding="utf-8").lower()
        assert "atlas risk" not in lower

    def test_no_var_mentioned(self):
        lower = RISK_DOC.read_text(encoding="utf-8").lower()
        assert "value-at-risk" not in lower or "not a value-at-risk" in lower

    def test_no_monte_carlo(self):
        lower = RISK_DOC.read_text(encoding="utf-8").lower()
        assert "monte carlo" not in lower or "not a monte carlo" in lower

    def test_no_probability_model(self):
        lower = RISK_DOC.read_text(encoding="utf-8").lower()
        assert "probability model" not in lower or "not a probability model" in lower

    def test_no_scoring_system(self):
        lower = RISK_DOC.read_text(encoding="utf-8").lower()
        assert "scoring system" not in lower or "not a scoring system" in lower

    def test_no_forecast(self):
        lower = RISK_DOC.read_text(encoding="utf-8").lower()
        assert "not a forecast" in lower or "not forecast" in lower or "does not forecast" in lower

    def test_atlas_dir_not_modified_by_this_sprint(self):
        for py_file in ATLAS_DIR.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "risk_review_v1" not in text, f"Sprint 284 runtime code found in {py_file}"


# ---------------------------------------------------------------------------
# Safe language — no prohibited phrases
# ---------------------------------------------------------------------------


class TestSafeLanguage:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = RISK_DOC.read_text(encoding="utf-8").lower()

    @pytest.mark.parametrize("phrase", PROHIBITED_PHRASES)
    def test_no_prohibited_phrase(self, phrase: str):
        assert phrase.lower() not in self.content, f"Prohibited phrase found: {phrase!r}"

    def test_no_buy_recommendation(self):
        assert "buy" not in self.content.split() or all(
            w != "buy" for w in self.content.split()
        )

    def test_no_sell_recommendation(self):
        assert "sell" not in self.content.split() or all(
            w != "sell" for w in self.content.split()
        )

    def test_no_prediction_language(self):
        if "will happen" in self.content:
            assert "not about" in self.content or "does not predict" in self.content
        if "will occur" in self.content:
            assert "not" in self.content

    def test_no_action_recommendation_language(self):
        lower = self.content
        assert "you should invest" not in lower
        assert "should invest" not in lower

    def test_safe_language_statement_in_doc(self):
        assert "not a recommendation" in self.content or "no recommendation" in self.content or "does not" in self.content


# ---------------------------------------------------------------------------
# Cross-document consistency
# ---------------------------------------------------------------------------


class TestCrossDocumentConsistency:
    def test_pipeline_doc_still_exists(self):
        assert PIPELINE_DOC.exists()

    def test_assumption_doc_still_exists(self):
        assert ASSUMPTION_DOC.exists()

    def test_evidence_quality_doc_still_exists(self):
        assert QUALITY_DOC.exists()

    def test_evidence_assembly_doc_still_exists(self):
        assert EVIDENCE_DOC.exists()

    def test_risk_doc_references_pipeline_doc(self):
        content = RISK_DOC.read_text(encoding="utf-8")
        assert "InvestmentReviewPipelineV1.md" in content

    def test_risk_doc_references_assumption_doc(self):
        content = RISK_DOC.read_text(encoding="utf-8")
        assert "AssumptionReviewV1.md" in content

    def test_risk_doc_references_quality_doc(self):
        content = RISK_DOC.read_text(encoding="utf-8")
        assert "EvidenceQualityReviewV1.md" in content

    def test_risk_doc_references_evidence_doc(self):
        content = RISK_DOC.read_text(encoding="utf-8")
        assert "EvidenceAssemblyV1.md" in content

    def test_cli_unchanged_by_sprint_284(self):
        cli_source = CLI_FILE.read_text(encoding="utf-8")
        assert "risk_review" not in cli_source

    def test_assumption_doc_unchanged(self):
        content = ASSUMPTION_DOC.read_text(encoding="utf-8")
        assert "Assumption Review" in content
        assert "Sprint 283" in content or "2026" in content

    def test_quality_doc_unchanged(self):
        content = QUALITY_DOC.read_text(encoding="utf-8")
        assert "Evidence Quality Review" in content

    def test_evidence_doc_unchanged(self):
        content = EVIDENCE_DOC.read_text(encoding="utf-8")
        assert "Evidence Assembly" in content

    def test_pipeline_doc_unchanged(self):
        content = PIPELINE_DOC.read_text(encoding="utf-8")
        assert "Investment Review Pipeline" in content


# ---------------------------------------------------------------------------
# Decision log and release candidate updated
# ---------------------------------------------------------------------------


class TestDocumentationUpdated:
    def test_decision_log_mentions_sprint_284(self):
        log = Path("docs/DecisionLog.md").read_text(encoding="utf-8")
        assert "284" in log

    def test_decision_log_mentions_risk_review(self):
        log = Path("docs/DecisionLog.md").read_text(encoding="utf-8").lower()
        assert "risk review" in log

    def test_rc_doc_mentions_sprint_284(self):
        rc = Path("docs/InternalV1ReleaseCandidate.md").read_text(encoding="utf-8")
        assert "284" in rc

    def test_rc_doc_sprint_284_entry_no_forbidden_language(self):
        rc = Path("docs/InternalV1ReleaseCandidate.md").read_text(encoding="utf-8")
        sprint_284_idx = rc.find("Sprint 284")
        if sprint_284_idx == -1:
            pytest.skip("Sprint 284 entry not found in RC doc")
        sprint_285_idx = rc.find("Sprint 285", sprint_284_idx)
        if sprint_285_idx == -1:
            chunk = rc[sprint_284_idx:]
        else:
            chunk = rc[sprint_284_idx:sprint_285_idx]
        for phrase in ["buy", "sell"]:
            words = chunk.lower().split()
            assert phrase not in words, f"Forbidden word {phrase!r} found in Sprint 284 RC entry"

    def test_risk_review_v1_md_present(self):
        assert RISK_DOC.exists()
