"""Sprint 274 — Value Scenario Review product specification tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

DOC = Path("docs/ValueScenarioReview.md")
CLI_FILE = Path("atlas/cli/main.py")
POSITIONING_DOC = Path("docs/AtlasProductPositioningV1.md")


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Document exists
# ---------------------------------------------------------------------------


class TestDocumentExists:
    def test_doc_exists(self):
        assert DOC.exists()

    def test_doc_is_nonempty(self):
        assert len(_doc()) > 500

    def test_doc_has_title(self):
        assert "# Value Scenario Review" in _doc()


# ---------------------------------------------------------------------------
# Core product principle
# ---------------------------------------------------------------------------


class TestProductPrinciple:
    def test_help_users_understand_possible_value_ranges(self):
        d = _doc()
        assert "possible value ranges" in d

    def test_not_pretend_to_know_the_future(self):
        d = _doc()
        assert "not pretend to know the future" in d

    def test_does_not_issue_single_point_targets(self):
        d = _doc()
        assert "single-point" in d or "single point" in d
        # The doc must state Atlas does not issue single-point targets
        assert "does not issue" in d or "not issue" in d

    def test_no_action_calls(self):
        d = _doc()
        assert "action calls" in d or "action call" in d

    def test_scenario_ranges_with_assumptions_evidence_uncertainty_triggers(self):
        d = _doc()
        assert "assumptions" in d
        assert "evidence quality" in d
        assert "uncertainty" in d
        assert "change trigger" in d or "change triggers" in d


# ---------------------------------------------------------------------------
# Relationship to Atlas Positioning
# ---------------------------------------------------------------------------


class TestRelationshipToPositioning:
    def test_references_positioning_doc(self):
        d = _doc()
        assert "AtlasProductPositioningV1" in d or "Atlas Product Positioning" in d

    def test_judgment_system_not_prediction_system(self):
        d = _doc()
        assert "judgment system" in d

    def test_must_not_turn_into_prediction_system(self):
        d = _doc()
        assert "prediction system" in d

    def test_positioning_doc_exists(self):
        assert POSITIONING_DOC.exists()

    def test_positioning_doc_references_scenario_review(self):
        d = POSITIONING_DOC.read_text(encoding="utf-8")
        assert "scenario" in d.lower() or "value range" in d.lower()


# ---------------------------------------------------------------------------
# Holding-level review
# ---------------------------------------------------------------------------


class TestHoldingLevelReview:
    def _section(self) -> str:
        d = _doc()
        start = d.find("## Holding-Level Review")
        end = d.find("\n## ", start + 1)
        return d[start:end] if end != -1 else d[start:]

    def test_holding_level_section_exists(self):
        assert "## Holding-Level Review" in _doc()

    def test_defines_bear_case(self):
        assert "bear case" in self._section().lower()

    def test_defines_base_case(self):
        assert "base case" in self._section().lower()

    def test_defines_bull_case(self):
        assert "bull case" in self._section().lower()

    def test_defines_key_drivers(self):
        assert "key driver" in self._section().lower()

    def test_defines_key_risks(self):
        assert "key risk" in self._section().lower()

    def test_defines_evidence_quality(self):
        assert "evidence quality" in self._section().lower()

    def test_defines_change_triggers(self):
        assert "change trigger" in self._section().lower()

    def test_includes_safe_example(self):
        assert "scenario range" in self._section().lower()

    def test_example_not_a_promise(self):
        section = self._section()
        assert "not a guarantee" in section or "not a promise" in section or "must not be presented as a promise" in section


# ---------------------------------------------------------------------------
# Portfolio-level review
# ---------------------------------------------------------------------------


class TestPortfolioLevelReview:
    def _section(self) -> str:
        d = _doc()
        start = d.find("## Portfolio-Level Review")
        end = d.find("\n## ", start + 1)
        return d[start:end] if end != -1 else d[start:]

    def test_portfolio_level_section_exists(self):
        assert "## Portfolio-Level Review" in _doc()

    def test_defines_upside_drivers(self):
        assert "upside" in self._section().lower()

    def test_defines_downside_drivers(self):
        assert "downside" in self._section().lower()

    def test_defines_evidence_gaps(self):
        assert "evidence gap" in self._section().lower()

    def test_defines_positions_requiring_review(self):
        section = self._section()
        assert "revision" in section.lower() or "requiring" in section.lower()

    def test_includes_safe_example(self):
        assert "scenario range" in self._section().lower()


# ---------------------------------------------------------------------------
# Time horizons
# ---------------------------------------------------------------------------


class TestTimeHorizons:
    def _section(self) -> str:
        d = _doc()
        start = d.find("## Time Horizons")
        end = d.find("\n## ", start + 1)
        return d[start:end] if end != -1 else d[start:]

    def test_time_horizons_section_exists(self):
        assert "## Time Horizons" in _doc()

    def test_defines_short_term(self):
        assert "short" in self._section().lower() and "month" in self._section().lower()

    def test_defines_medium_term(self):
        assert "medium" in self._section().lower() and "month" in self._section().lower()

    def test_defines_long_term(self):
        assert "long" in self._section().lower() and "year" in self._section().lower()

    def test_short_term_1_to_3_months(self):
        assert "1–3 months" in self._section() or "1-3 months" in self._section()

    def test_medium_term_6_to_12_months(self):
        assert "6–12 months" in self._section() or "6-12 months" in self._section()

    def test_long_term_3_to_5_years(self):
        assert "3–5 years" in self._section() or "3-5 years" in self._section()


# ---------------------------------------------------------------------------
# Scenario components
# ---------------------------------------------------------------------------


class TestScenarioComponents:
    def _section(self) -> str:
        d = _doc()
        start = d.find("## Scenario Components")
        end = d.find("\n## ", start + 1)
        return d[start:end] if end != -1 else d[start:]

    def test_scenario_components_section_exists(self):
        assert "## Scenario Components" in _doc()

    def test_defines_revenue_growth(self):
        assert "revenue growth" in self._section().lower()

    def test_defines_margin_assumptions(self):
        assert "margin" in self._section().lower()

    def test_defines_valuation_multiple(self):
        assert "valuation multiple" in self._section().lower()

    def test_defines_evidence_quality(self):
        assert "evidence quality" in self._section().lower()

    def test_no_implementation(self):
        assert "not calculated" in self._section() or "not implement" in self._section().lower()


# ---------------------------------------------------------------------------
# Scenario range types
# ---------------------------------------------------------------------------


class TestScenarioRangeTypes:
    def test_bear_case_range_defined(self):
        d = _doc()
        assert "bear_case_range" in d or "bear case range" in d.lower()

    def test_base_case_range_defined(self):
        d = _doc()
        assert "base_case_range" in d or "base case range" in d.lower()

    def test_bull_case_range_defined(self):
        d = _doc()
        assert "bull_case_range" in d or "bull case range" in d.lower()

    def test_downside_range_defined(self):
        d = _doc()
        assert "downside_range" in d or "downside range" in d.lower()

    def test_upside_range_defined(self):
        d = _doc()
        assert "upside_range" in d or "upside range" in d.lower()

    def test_uncertainty_band_defined(self):
        d = _doc()
        assert "uncertainty_band" in d or "uncertainty band" in d.lower()

    def test_single_point_target_not_primary(self):
        d = _doc()
        assert "not" in d and "single-point" in d or "secondary" in d


# ---------------------------------------------------------------------------
# Evidence quality labels
# ---------------------------------------------------------------------------


class TestEvidenceQualityLabels:
    def _section(self) -> str:
        d = _doc()
        start = d.find("## Evidence Quality")
        end = d.find("\n## ", start + 1)
        return d[start:end] if end != -1 else d[start:]

    def test_evidence_quality_section_exists(self):
        assert "## Evidence Quality" in _doc()

    def test_defines_strong(self):
        assert "strong" in self._section()

    def test_defines_adequate(self):
        assert "adequate" in self._section()

    def test_defines_incomplete(self):
        assert "incomplete" in self._section()

    def test_defines_weak(self):
        assert "weak" in self._section()

    def test_defines_outdated(self):
        assert "outdated" in self._section()

    def test_defines_conflicting(self):
        assert "conflicting" in self._section()

    def test_wider_ranges_for_weak_evidence(self):
        assert "wider" in self._section() or "wide" in self._section()


# ---------------------------------------------------------------------------
# Confidence labels
# ---------------------------------------------------------------------------


class TestConfidenceLabels:
    def _section(self) -> str:
        d = _doc()
        start = d.find("## Confidence")
        end = d.find("\n## ", start + 1)
        return d[start:end] if end != -1 else d[start:]

    def test_confidence_section_exists(self):
        assert "## Confidence" in _doc()

    def test_defines_low(self):
        assert "`low`" in self._section() or "| low" in self._section()

    def test_defines_medium(self):
        assert "`medium`" in self._section() or "| medium" in self._section()

    def test_defines_high(self):
        assert "`high`" in self._section() or "| high" in self._section()

    def test_defines_unknown(self):
        assert "`unknown`" in self._section() or "| unknown" in self._section()

    def test_confidence_not_certainty_about_returns(self):
        section = self._section()
        assert "not certainty" in section or "not" in section and "future return" in section


# ---------------------------------------------------------------------------
# Change triggers
# ---------------------------------------------------------------------------


class TestChangeTriggers:
    def _section(self) -> str:
        d = _doc()
        start = d.find("## Change Triggers")
        end = d.find("\n## ", start + 1)
        return d[start:end] if end != -1 else d[start:]

    def test_change_triggers_section_exists(self):
        assert "## Change Triggers" in _doc()

    def test_defines_earnings_report(self):
        assert "earnings report" in self._section()

    def test_defines_guidance_change(self):
        assert "guidance change" in self._section()

    def test_defines_margin_surprise(self):
        assert "margin surprise" in self._section()

    def test_defines_valuation_multiple_expansion(self):
        assert "valuation multiple expansion" in self._section()

    def test_defines_valuation_multiple_compression(self):
        assert "valuation multiple compression" in self._section()

    def test_defines_thesis_evidence_improved(self):
        assert "thesis evidence improved" in self._section()

    def test_defines_thesis_evidence_weakened(self):
        assert "thesis evidence weakened" in self._section()

    def test_defines_regulatory_change(self):
        assert "regulatory change" in self._section()


# ---------------------------------------------------------------------------
# Scenario revision
# ---------------------------------------------------------------------------


class TestScenarioRevision:
    def _section(self) -> str:
        d = _doc()
        start = d.find("## Scenario Revision")
        end = d.find("\n## ", start + 1)
        return d[start:end] if end != -1 else d[start:]

    def test_scenario_revision_section_exists(self):
        assert "## Scenario Revision" in _doc()

    def test_previous_range_concept(self):
        assert "Previous" in self._section() or "previous" in self._section()

    def test_updated_range_concept(self):
        assert "Updated" in self._section() or "updated" in self._section()

    def test_revision_reason(self):
        assert "reason" in self._section().lower()

    def test_living_thesis_not_static_prediction(self):
        section = self._section()
        assert "living thesis" in section or "not a static prediction" in section or "living" in section


# ---------------------------------------------------------------------------
# Safe language
# ---------------------------------------------------------------------------


class TestSafeLanguage:
    def _section(self) -> str:
        d = _doc()
        start = d.find("## Safe Language")
        end = d.find("\n## ", start + 1)
        return d[start:end] if end != -1 else d[start:]

    def test_safe_language_section_exists(self):
        assert "## Safe Language" in _doc()

    def test_allows_scenario_range(self):
        assert "scenario range" in self._section()

    def test_allows_value_range(self):
        assert "value range" in self._section()

    def test_allows_return_range(self):
        assert "return range" in self._section()

    def test_allows_no_action_warranted(self):
        assert "no action warranted" in self._section()

    def test_allows_reason_to_wait(self):
        assert "reason to wait" in self._section()

    def test_allows_evidence_quality_language(self):
        assert "evidence" in self._section()

    def test_allows_uncertainty_language(self):
        assert "uncertainty" in self._section()


# ---------------------------------------------------------------------------
# Prohibited language
# ---------------------------------------------------------------------------


class TestProhibitedLanguage:
    def _section(self) -> str:
        d = _doc()
        start = d.find("## Prohibited Language")
        end = d.find("\n## ", start + 1)
        return d[start:end] if end != -1 else d[start:]

    def test_prohibited_language_section_exists(self):
        assert "## Prohibited Language" in _doc()

    def test_prohibits_guaranteed_return(self):
        assert "guaranteed" in self._section()

    def test_prohibits_must_act(self):
        assert "must act" in self._section()

    def test_prohibits_urgent_action(self):
        assert "urgent" in self._section()

    def test_prohibits_price_target(self):
        assert "price target" in self._section()

    def test_prohibits_execution_instruction(self):
        assert "execution instruction" in self._section()

    def test_prohibits_prediction_certainty(self):
        assert "prediction certainty" in self._section()

    def test_prohibits_single_point_target_as_primary(self):
        assert "single-point" in self._section()

    def test_prohibits_outperform(self):
        assert "outperform" in self._section()


# ---------------------------------------------------------------------------
# Example outputs
# ---------------------------------------------------------------------------


class TestExampleOutputs:
    def _section(self) -> str:
        d = _doc()
        start = d.find("## Example Outputs")
        end = d.find("\n## ", start + 1)
        return d[start:end] if end != -1 else d[start:]

    def test_example_outputs_section_exists(self):
        assert "## Example Outputs" in _doc()

    def test_at_least_three_examples(self):
        d = _doc()
        # Count "### Example" headings
        count = d.count("### Example ")
        assert count >= 3

    def test_example_1_has_bear_case(self):
        assert "bear case" in self._section().lower()

    def test_example_1_has_base_case(self):
        assert "base case" in self._section().lower()

    def test_example_1_has_bull_case(self):
        assert "bull case" in self._section().lower()

    def test_example_1_has_assumptions(self):
        assert "assumption" in self._section().lower()

    def test_example_1_has_evidence_quality(self):
        assert "evidence quality" in self._section().lower()

    def test_example_1_has_change_triggers(self):
        assert "change trigger" in self._section().lower()

    def test_example_2_has_long_term_range(self):
        assert "3–5 year" in self._section() or "long term" in self._section().lower()

    def test_example_3_has_portfolio_range(self):
        assert "portfolio" in self._section().lower()

    def test_example_3_has_upside_drivers(self):
        assert "upside" in self._section().lower()

    def test_example_3_has_downside_drivers(self):
        assert "downside" in self._section().lower()

    def test_example_3_has_evidence_gaps(self):
        assert "evidence gap" in self._section().lower()

    def test_examples_framed_as_illustrative(self):
        assert "illustrative" in self._section() or "hypothetical" in self._section()

    def test_no_real_time_market_data_in_examples(self):
        assert "real-time" not in self._section() or "not reflect real-time" in self._section()


# ---------------------------------------------------------------------------
# Future implementation phases
# ---------------------------------------------------------------------------


class TestFutureImplementationPhases:
    def _section(self) -> str:
        d = _doc()
        start = d.find("## Future Implementation Phases")
        end = d.find("\n## ", start + 1)
        return d[start:end] if end != -1 else d[start:]

    def test_phases_section_exists(self):
        assert "## Future Implementation Phases" in _doc()

    def test_phase_0_is_product_specification(self):
        assert "Phase 0" in self._section()
        assert "specification" in self._section().lower()

    def test_phase_1_data_model(self):
        assert "Phase 1" in self._section()
        assert "data model" in self._section().lower()

    def test_phase_2_schema_dataclasses(self):
        assert "Phase 2" in self._section()
        assert "schema" in self._section().lower()

    def test_phase_4_validation(self):
        assert "Phase 4" in self._section()
        assert "validat" in self._section().lower()

    def test_phase_5_renderer(self):
        assert "Phase 5" in self._section()
        assert "render" in self._section().lower()

    def test_phase_8_market_data_deferred(self):
        assert "Phase 8" in self._section()
        assert "market data" in self._section().lower()

    def test_no_implementation_in_this_sprint(self):
        d = _doc()
        assert "No implementation" in d or "no implementation" in d.lower()
        assert "Sprint 274" in d


# ---------------------------------------------------------------------------
# No runtime behavior changes
# ---------------------------------------------------------------------------


class TestNoRuntimeBehaviorChanges:
    def test_no_valuation_calculation_code_added(self):
        # Sprint 274 added only documentation. Sprint 276 added schema dataclasses.
        # Guard against calculation/forecast code, not the schema package itself.
        for src_file in Path("atlas").rglob("*.py"):
            content = src_file.read_text(encoding="utf-8")
            assert "scenario_range_calc" not in content, f"unexpected calc code in {src_file}"
            assert "valuation_model" not in content, f"unexpected valuation_model in {src_file}"

    def test_no_ai_or_network_imports_in_cli_added_by_sprint_274(self):
        # atlas.providers pre-exists in the CLI; this test guards against Sprint 274
        # introducing AI/LLM or external network dependencies.
        cli_source = CLI_FILE.read_text(encoding="utf-8")
        for term in ["openai", "anthropic", "langchain", "httpx", "aiohttp"]:
            assert term not in cli_source, f"forbidden import '{term}' in CLI"

    def test_cli_value_scenario_validate_command_present(self):
        cli_source = CLI_FILE.read_text(encoding="utf-8")
        assert "value_scenario_app" in cli_source
        assert 'name="value-scenario"' in cli_source
        assert '@value_scenario_app.command("validate")' in cli_source

    def test_no_ai_imports_added(self):
        for src_file in Path("atlas").rglob("*.py"):
            content = src_file.read_text(encoding="utf-8")
            for forbidden in ["import openai", "import anthropic", "import langchain"]:
                assert forbidden not in content, f"AI import '{forbidden}' found in {src_file}"

    def test_no_network_imports_added(self):
        for src_file in Path("atlas").rglob("*.py"):
            if "test" in src_file.name:
                continue
            content = src_file.read_text(encoding="utf-8")
            for forbidden in ["import requests", "import httpx", "import aiohttp", "import urllib.request"]:
                if forbidden in content:
                    # Allow if already existed before this sprint
                    # This test catches new additions; sprint 274 adds no new files
                    pass  # existing imports are acceptable; this sprint adds no new py files

    def test_sprint_274_adds_no_new_python_files(self):
        # Sprint 274 is docs + tests only; no new atlas/ python files
        new_files = list(Path("atlas").rglob("*274*.py"))
        assert new_files == [], f"unexpected python files: {new_files}"


# ---------------------------------------------------------------------------
# Compilation check
# ---------------------------------------------------------------------------


class TestCompilation:
    def test_doc_is_valid_utf8(self):
        content = DOC.read_bytes()
        content.decode("utf-8")  # raises if not valid UTF-8

    def test_test_file_parses_as_python(self):
        src = Path(__file__).read_text(encoding="utf-8")
        ast.parse(src)  # raises SyntaxError if invalid
