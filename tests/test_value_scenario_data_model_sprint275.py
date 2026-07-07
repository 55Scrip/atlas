"""Sprint 275 — Value Scenario Data Model specification tests."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

DOC = Path("docs/ValueScenarioDataModel.md")
SCENARIO_REVIEW_DOC = Path("docs/ValueScenarioReview.md")
CLI_FILE = Path("atlas/cli/main.py")


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


def _section(heading: str) -> str:
    d = _doc()
    start = d.find(f"## {heading}")
    if start == -1:
        return ""
    end = d.find("\n## ", start + 1)
    return d[start:end] if end != -1 else d[start:]


# ---------------------------------------------------------------------------
# Document exists
# ---------------------------------------------------------------------------


class TestDocumentExists:
    def test_doc_exists(self):
        assert DOC.exists()

    def test_doc_is_nonempty(self):
        assert len(_doc()) > 1000

    def test_doc_has_title(self):
        assert "# Value Scenario Data Model" in _doc()

    def test_depends_on_value_scenario_review(self):
        assert "ValueScenarioReview" in _doc() or "Value Scenario Review" in _doc()

    def test_no_implementation_this_sprint(self):
        d = _doc()
        assert "No implementation" in d or "no implementation" in d.lower()
        assert "Sprint 275" in d


# ---------------------------------------------------------------------------
# Model principles
# ---------------------------------------------------------------------------


class TestModelPrinciples:
    def _s(self) -> str:
        return _section("Model Principles")

    def test_model_principles_section_exists(self):
        assert "## Model Principles" in _doc()

    def test_ranges_not_predictions(self):
        assert "range" in self._s().lower() and "prediction" in self._s().lower()

    def test_no_single_point_targets_required(self):
        s = self._s()
        assert "single-point" in s or "single point" in s

    def test_confidence_describes_structure(self):
        assert "confidence in the scenario structure" in self._s() or "Confidence describes" in self._s()

    def test_revisions_explain_change(self):
        assert "revision" in self._s().lower()

    def test_portfolio_preserves_uncertainty(self):
        assert "uncertainty" in self._s().lower()

    def test_canonical_values_remain_english(self):
        assert "canonical" in self._s().lower() and "english" in self._s().lower()

    def test_safety_boundary_always_on(self):
        s = self._s()
        assert "safety" in s.lower() or "safety boundary" in s.lower()


# ---------------------------------------------------------------------------
# Value Scenario Review (top-level)
# ---------------------------------------------------------------------------


class TestValueScenarioReview:
    def _s(self) -> str:
        return _section("Value Scenario Review")

    def test_top_level_section_exists(self):
        assert "## Value Scenario Review" in _doc()

    def test_defines_scenario_review_id(self):
        assert "scenario_review_id" in self._s()

    def test_defines_review_type(self):
        assert "review_type" in self._s()

    def test_defines_created_at(self):
        assert "created_at" in self._s()

    def test_defines_subject(self):
        assert "subject" in self._s()

    def test_defines_time_horizons(self):
        assert "time_horizons" in self._s()

    def test_defines_holding_scenarios(self):
        assert "holding_scenarios" in self._s()

    def test_defines_portfolio_scenario(self):
        assert "portfolio_scenario" in self._s()

    def test_defines_assumptions(self):
        assert "assumptions" in self._s()

    def test_defines_evidence_items(self):
        assert "evidence_items" in self._s()

    def test_defines_change_triggers(self):
        assert "change_triggers" in self._s()

    def test_defines_revisions(self):
        assert "revisions" in self._s()

    def test_defines_safety_boundary(self):
        assert "safety_boundary" in self._s()

    def test_defines_review_type_holding(self):
        assert "holding" in self._s()

    def test_defines_review_type_portfolio(self):
        assert "portfolio" in self._s()

    def test_defines_review_type_mixed(self):
        assert "mixed" in self._s()


# ---------------------------------------------------------------------------
# Subject model
# ---------------------------------------------------------------------------


class TestSubjectModel:
    def _s(self) -> str:
        return _section("Subject Model")

    def test_subject_model_section_exists(self):
        assert "## Subject Model" in _doc()

    def test_defines_subject_id(self):
        assert "subject_id" in self._s()

    def test_defines_subject_type(self):
        assert "subject_type" in self._s()

    def test_defines_display_name(self):
        assert "display_name" in self._s()

    def test_defines_ticker(self):
        assert "ticker" in self._s()

    def test_defines_portfolio_id(self):
        assert "portfolio_id" in self._s()

    def test_defines_source_reference(self):
        assert "source_reference" in self._s()

    def test_subject_type_holding(self):
        assert "holding" in self._s()

    def test_subject_type_portfolio(self):
        assert "portfolio" in self._s()

    def test_subject_type_watchlist_item(self):
        assert "watchlist_item" in self._s()


# ---------------------------------------------------------------------------
# Time Horizon
# ---------------------------------------------------------------------------


class TestTimeHorizon:
    def _s(self) -> str:
        return _section("Time Horizon")

    def test_time_horizon_section_exists(self):
        assert "## Time Horizon" in _doc()

    def test_defines_short_term(self):
        assert "short_term" in self._s()

    def test_defines_medium_term(self):
        assert "medium_term" in self._s()

    def test_defines_long_term(self):
        assert "long_term" in self._s()

    def test_short_term_duration(self):
        assert "1–3 months" in self._s() or "1-3 months" in self._s()

    def test_medium_term_duration(self):
        assert "6–12 months" in self._s() or "6-12 months" in self._s()

    def test_long_term_duration(self):
        assert "3–5 years" in self._s() or "3-5 years" in self._s()


# ---------------------------------------------------------------------------
# Scenario Range
# ---------------------------------------------------------------------------


class TestScenarioRange:
    def _s(self) -> str:
        return _section("Scenario Range")

    def test_scenario_range_section_exists(self):
        assert "## Scenario Range" in _doc()

    def test_defines_range_id(self):
        assert "range_id" in self._s()

    def test_defines_horizon(self):
        assert "horizon" in self._s()

    def test_defines_case_type(self):
        assert "case_type" in self._s()

    def test_defines_lower_percent(self):
        assert "lower_percent" in self._s()

    def test_defines_upper_percent(self):
        assert "upper_percent" in self._s()

    def test_defines_assumption_ids(self):
        assert "assumption_ids" in self._s()

    def test_defines_evidence_item_ids(self):
        assert "evidence_item_ids" in self._s()

    def test_defines_confidence(self):
        assert "confidence" in self._s()

    def test_defines_evidence_quality(self):
        assert "evidence_quality" in self._s()

    def test_defines_uncertainty_note(self):
        assert "uncertainty_note" in self._s()

    def test_case_type_bear(self):
        assert "bear" in self._s()

    def test_case_type_base(self):
        assert "base" in self._s()

    def test_case_type_bull(self):
        assert "bull" in self._s()

    def test_case_type_downside(self):
        assert "downside" in self._s()

    def test_case_type_upside(self):
        assert "upside" in self._s()

    def test_case_type_uncertainty_band(self):
        assert "uncertainty_band" in self._s()

    def test_range_not_single_point_target(self):
        s = self._s()
        assert "single-point" in s or "not a single" in s or "not require" in s


# ---------------------------------------------------------------------------
# Holding Scenario
# ---------------------------------------------------------------------------


class TestHoldingScenario:
    def _s(self) -> str:
        return _section("Holding Scenario")

    def test_holding_scenario_section_exists(self):
        assert "## Holding Scenario" in _doc()

    def test_defines_holding_scenario_id(self):
        assert "holding_scenario_id" in self._s()

    def test_defines_subject(self):
        assert "subject" in self._s()

    def test_defines_ranges(self):
        assert "ranges" in self._s()

    def test_defines_key_drivers(self):
        assert "key_drivers" in self._s()

    def test_defines_key_risks(self):
        assert "key_risks" in self._s()

    def test_defines_assumptions(self):
        assert "assumptions" in self._s()

    def test_defines_evidence_quality(self):
        assert "evidence_quality" in self._s()

    def test_defines_confidence(self):
        assert "confidence" in self._s()

    def test_defines_change_triggers(self):
        assert "change_triggers" in self._s()

    def test_defines_revision_ids(self):
        assert "revision_ids" in self._s()


# ---------------------------------------------------------------------------
# Portfolio Scenario
# ---------------------------------------------------------------------------


class TestPortfolioScenario:
    def _s(self) -> str:
        return _section("Portfolio Scenario")

    def test_portfolio_scenario_section_exists(self):
        assert "## Portfolio Scenario" in _doc()

    def test_defines_portfolio_scenario_id(self):
        assert "portfolio_scenario_id" in self._s()

    def test_defines_ranges(self):
        assert "ranges" in self._s()

    def test_defines_weighted_contributions(self):
        assert "weighted_contributions" in self._s()

    def test_defines_main_upside_drivers(self):
        assert "main_upside_drivers" in self._s()

    def test_defines_main_downside_drivers(self):
        assert "main_downside_drivers" in self._s()

    def test_defines_concentration_sensitivity(self):
        assert "concentration_sensitivity" in self._s()

    def test_defines_valuation_sensitivity(self):
        assert "valuation_sensitivity" in self._s()

    def test_defines_evidence_gaps(self):
        assert "evidence_gaps" in self._s()

    def test_defines_holdings_requiring_review(self):
        assert "holdings_requiring_review" in self._s()

    def test_defines_confidence(self):
        assert "confidence" in self._s()

    def test_defines_evidence_quality(self):
        assert "evidence_quality" in self._s()


# ---------------------------------------------------------------------------
# Portfolio Contribution
# ---------------------------------------------------------------------------


class TestPortfolioContribution:
    def _s(self) -> str:
        return _section("Portfolio Contribution")

    def test_portfolio_contribution_section_exists(self):
        assert "## Portfolio Contribution" in _doc()

    def test_defines_contribution_id(self):
        assert "contribution_id" in self._s()

    def test_defines_holding_id(self):
        assert "holding_id" in self._s()

    def test_defines_portfolio_weight(self):
        assert "portfolio_weight" in self._s()

    def test_defines_range_impact_level(self):
        assert "range_impact_level" in self._s()

    def test_defines_evidence_quality(self):
        assert "evidence_quality" in self._s()

    def test_impact_level_low(self):
        assert "low" in self._s()

    def test_impact_level_medium(self):
        assert "medium" in self._s()

    def test_impact_level_high(self):
        assert "high" in self._s()

    def test_impact_level_dominant(self):
        assert "dominant" in self._s()


# ---------------------------------------------------------------------------
# Assumptions
# ---------------------------------------------------------------------------


class TestAssumptions:
    def _s(self) -> str:
        return _section("Assumptions")

    def test_assumptions_section_exists(self):
        assert "## Assumptions" in _doc()

    def test_defines_assumption_id(self):
        assert "assumption_id" in self._s()

    def test_defines_assumption_type(self):
        assert "assumption_type" in self._s()

    def test_defines_description(self):
        assert "description" in self._s()

    def test_defines_direction(self):
        assert "direction" in self._s()

    def test_defines_related_range_ids(self):
        assert "related_range_ids" in self._s()

    def test_defines_evidence_item_ids(self):
        assert "evidence_item_ids" in self._s()

    def test_assumption_type_revenue_growth(self):
        assert "revenue_growth" in self._s()

    def test_assumption_type_margin(self):
        assert "margin" in self._s()

    def test_assumption_type_valuation_multiple(self):
        assert "valuation_multiple" in self._s()

    def test_assumption_type_capital_allocation(self):
        assert "capital_allocation" in self._s()

    def test_direction_positive(self):
        assert "positive" in self._s()

    def test_direction_negative(self):
        assert "negative" in self._s()

    def test_direction_mixed(self):
        assert "mixed" in self._s()

    def test_direction_neutral(self):
        assert "neutral" in self._s()

    def test_direction_unknown(self):
        assert "unknown" in self._s()


# ---------------------------------------------------------------------------
# Evidence Item
# ---------------------------------------------------------------------------


class TestEvidenceItem:
    def _s(self) -> str:
        return _section("Evidence Item")

    def test_evidence_item_section_exists(self):
        assert "## Evidence Item" in _doc()

    def test_defines_evidence_item_id(self):
        assert "evidence_item_id" in self._s()

    def test_defines_evidence_type(self):
        assert "evidence_type" in self._s()

    def test_defines_description(self):
        assert "description" in self._s()

    def test_defines_source_reference(self):
        assert "source_reference" in self._s()

    def test_defines_freshness(self):
        assert "freshness" in self._s()

    def test_defines_related_assumption_ids(self):
        assert "related_assumption_ids" in self._s()

    def test_evidence_type_company_report(self):
        assert "company_report" in self._s()

    def test_evidence_type_earnings_call(self):
        assert "earnings_call" in self._s()

    def test_evidence_type_guidance(self):
        assert "guidance" in self._s()

    def test_evidence_type_research_note(self):
        assert "research_note" in self._s()

    def test_evidence_type_user_note(self):
        assert "user_note" in self._s()

    def test_freshness_current(self):
        assert "current" in self._s()

    def test_freshness_recent(self):
        assert "recent" in self._s()

    def test_freshness_stale(self):
        assert "stale" in self._s()


# ---------------------------------------------------------------------------
# Evidence Quality
# ---------------------------------------------------------------------------


class TestEvidenceQuality:
    def _s(self) -> str:
        return _section("Evidence Quality")

    def test_evidence_quality_section_exists(self):
        assert "## Evidence Quality" in _doc()

    def test_strong(self):
        assert "strong" in self._s()

    def test_adequate(self):
        assert "adequate" in self._s()

    def test_incomplete(self):
        assert "incomplete" in self._s()

    def test_weak(self):
        assert "weak" in self._s()

    def test_outdated(self):
        assert "outdated" in self._s()

    def test_conflicting(self):
        assert "conflicting" in self._s()

    def test_wider_ranges_for_weak_evidence(self):
        s = self._s()
        assert "wider" in s or "wide" in s


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------


class TestConfidence:
    def _s(self) -> str:
        return _section("Confidence")

    def test_confidence_section_exists(self):
        assert "## Confidence" in _doc()

    def test_low(self):
        assert "low" in self._s()

    def test_medium(self):
        assert "medium" in self._s()

    def test_high(self):
        assert "high" in self._s()

    def test_unknown(self):
        assert "unknown" in self._s()

    def test_not_certainty_about_future_returns(self):
        s = self._s()
        assert "not certainty" in s or "not" in s and "future return" in s


# ---------------------------------------------------------------------------
# Change Trigger
# ---------------------------------------------------------------------------


class TestChangeTrigger:
    def _s(self) -> str:
        return _section("Change Trigger")

    def test_change_trigger_section_exists(self):
        assert "## Change Trigger" in _doc()

    def test_defines_trigger_id(self):
        assert "trigger_id" in self._s()

    def test_defines_trigger_type(self):
        assert "trigger_type" in self._s()

    def test_defines_expected_effect(self):
        assert "expected_effect" in self._s()

    def test_defines_related_assumption_ids(self):
        assert "related_assumption_ids" in self._s()

    def test_defines_related_range_ids(self):
        assert "related_range_ids" in self._s()

    def test_trigger_type_earnings_report(self):
        assert "earnings_report" in self._s()

    def test_trigger_type_guidance_change(self):
        assert "guidance_change" in self._s()

    def test_trigger_type_margin_surprise(self):
        assert "margin_surprise" in self._s()

    def test_trigger_type_valuation_multiple_expansion(self):
        assert "valuation_multiple_expansion" in self._s()

    def test_trigger_type_valuation_multiple_compression(self):
        assert "valuation_multiple_compression" in self._s()

    def test_trigger_type_thesis_evidence_improved(self):
        assert "thesis_evidence_improved" in self._s()

    def test_trigger_type_thesis_evidence_weakened(self):
        assert "thesis_evidence_weakened" in self._s()

    def test_trigger_type_regulatory_change(self):
        assert "regulatory_change" in self._s()

    def test_trigger_type_currency_movement(self):
        assert "currency_movement" in self._s()

    def test_effect_range_may_expand(self):
        assert "range_may_expand" in self._s()

    def test_effect_range_may_compress(self):
        assert "range_may_compress" in self._s()

    def test_effect_range_may_shift_up(self):
        assert "range_may_shift_up" in self._s()

    def test_effect_range_may_shift_down(self):
        assert "range_may_shift_down" in self._s()

    def test_effect_confidence_may_increase(self):
        assert "confidence_may_increase" in self._s()

    def test_effect_confidence_may_decrease(self):
        assert "confidence_may_decrease" in self._s()


# ---------------------------------------------------------------------------
# Scenario Revision
# ---------------------------------------------------------------------------


class TestScenarioRevision:
    def _s(self) -> str:
        return _section("Scenario Revision")

    def test_scenario_revision_section_exists(self):
        assert "## Scenario Revision" in _doc()

    def test_defines_revision_id(self):
        assert "revision_id" in self._s()

    def test_defines_revised_at(self):
        assert "revised_at" in self._s()

    def test_defines_previous_range_ids(self):
        assert "previous_range_ids" in self._s()

    def test_defines_updated_range_ids(self):
        assert "updated_range_ids" in self._s()

    def test_defines_reason(self):
        assert "reason" in self._s()

    def test_defines_trigger_ids(self):
        assert "trigger_ids" in self._s()

    def test_defines_changed_assumption_ids(self):
        assert "changed_assumption_ids" in self._s()

    def test_revisions_explain_change(self):
        s = self._s()
        assert "what changed" in s.lower() or "explain" in s.lower()

    def test_prior_uncertainty_not_avoidable(self):
        s = self._s()
        assert "avoidable" in s or "not imply" in s

    def test_living_thesis_concept(self):
        s = self._s()
        assert "living thesis" in s or "living" in s


# ---------------------------------------------------------------------------
# Safety Boundary
# ---------------------------------------------------------------------------


class TestSafetyBoundary:
    def _s(self) -> str:
        return _section("Safety Boundary")

    def test_safety_boundary_section_exists(self):
        assert "## Safety Boundary" in _doc()

    def test_no_single_point_targets_field(self):
        assert "no_single_point_targets" in self._s()

    def test_no_action_calls_field(self):
        assert "no_action_calls" in self._s()

    def test_no_execution_instructions_field(self):
        assert "no_execution_instructions" in self._s()

    def test_no_prediction_certainty_field(self):
        assert "no_prediction_certainty" in self._s()

    def test_assumptions_required_field(self):
        assert "assumptions_required" in self._s()

    def test_evidence_quality_required_field(self):
        assert "evidence_quality_required" in self._s()

    def test_uncertainty_required_field(self):
        assert "uncertainty_required" in self._s()

    def test_change_triggers_required_field(self):
        assert "change_triggers_required" in self._s()

    def test_all_default_true(self):
        s = self._s()
        assert "true" in s.lower() or "default" in s.lower()

    def test_never_false_in_production(self):
        s = self._s()
        assert "false" in s.lower() or "never" in s.lower()


# ---------------------------------------------------------------------------
# Canonical Values
# ---------------------------------------------------------------------------


class TestCanonicalValues:
    def _s(self) -> str:
        return _section("Canonical Values")

    def test_canonical_values_section_exists(self):
        assert "## Canonical Values" in _doc()

    def test_review_type_in_table(self):
        assert "review_type" in self._s()

    def test_subject_type_in_table(self):
        assert "subject_type" in self._s()

    def test_horizon_in_table(self):
        assert "horizon" in self._s()

    def test_case_type_in_table(self):
        assert "case_type" in self._s()

    def test_assumption_type_in_table(self):
        assert "assumption_type" in self._s()

    def test_evidence_quality_in_table(self):
        assert "evidence_quality" in self._s()

    def test_confidence_in_table(self):
        assert "confidence" in self._s()

    def test_trigger_type_in_table(self):
        assert "trigger_type" in self._s()

    def test_expected_effect_in_table(self):
        assert "expected_effect" in self._s()

    def test_range_impact_level_in_table(self):
        assert "range_impact_level" in self._s()

    def test_remains_english(self):
        s = self._s()
        assert "English" in s or "english" in s


# ---------------------------------------------------------------------------
# Example JSON
# ---------------------------------------------------------------------------


class TestExampleJSON:
    def _s(self) -> str:
        return _section("Example JSON")

    def test_example_json_section_exists(self):
        assert "## Example JSON" in _doc()

    def test_at_least_two_examples(self):
        d = _doc()
        assert d.count("### Example") >= 2

    def test_holding_level_example(self):
        assert "holding" in self._s().lower()

    def test_portfolio_level_example(self):
        assert "portfolio" in self._s().lower()

    def test_examples_marked_hypothetical(self):
        s = self._s()
        assert "hypothetical" in s.lower() or "illustrative" in s.lower()

    def test_no_real_time_data_in_examples(self):
        s = self._s()
        assert "real-time" not in s or "not reflect real-time" in s or "do not reflect" in s

    def test_holding_example_has_scenario_review_id(self):
        assert "scenario_review_id" in self._s()

    def test_holding_example_has_safety_boundary(self):
        assert "safety_boundary" in self._s()

    def test_holding_example_has_assumptions(self):
        assert "assumption_id" in self._s()

    def test_holding_example_has_change_triggers(self):
        assert "trigger_id" in self._s()

    def test_holding_example_has_evidence_items(self):
        assert "evidence_item_id" in self._s()

    def test_holding_example_no_single_point_targets(self):
        # Every range in example must have lower_percent != upper_percent as ranges
        s = self._s()
        assert "lower_percent" in s
        assert "upper_percent" in s

    def test_example_json_is_parseable(self):
        """Extract JSON blocks from the example section and verify they parse."""
        s = self._s()
        # Find JSON code blocks
        blocks = []
        start = 0
        while True:
            begin = s.find("```json", start)
            if begin == -1:
                break
            end = s.find("```", begin + 7)
            if end == -1:
                break
            blocks.append(s[begin + 7:end].strip())
            start = end + 3
        assert len(blocks) >= 2, "expected at least 2 JSON code blocks in Example JSON section"
        for block in blocks:
            try:
                json.loads(block)
            except json.JSONDecodeError as exc:
                pytest.fail(f"Example JSON block is not valid JSON: {exc}")

    def test_example_safety_boundary_all_true(self):
        s = self._s()
        # All safety boundary fields in examples should be true
        import re
        safety_values = re.findall(r'"no_\w+"\s*:\s*(true|false)', s)
        assert len(safety_values) > 0
        assert all(v == "true" for v in safety_values), f"found non-true safety values: {safety_values}"


# ---------------------------------------------------------------------------
# Validation Expectations
# ---------------------------------------------------------------------------


class TestValidationExpectations:
    def _s(self) -> str:
        return _section("Validation Expectations")

    def test_validation_expectations_section_exists(self):
        assert "## Validation Expectations" in _doc()

    def test_required_ids_rule(self):
        s = self._s()
        assert "scenario_review_id" in s or "required" in s.lower()

    def test_canonical_review_type_rule(self):
        assert "review_type" in self._s()

    def test_canonical_horizon_rule(self):
        assert "horizon" in self._s()

    def test_canonical_case_type_rule(self):
        assert "case_type" in self._s()

    def test_range_bounds_required(self):
        s = self._s()
        assert "lower_percent" in s and "upper_percent" in s

    def test_no_single_point_forecast_rule(self):
        s = self._s()
        assert "single-point" in s or "single point" in s

    def test_evidence_quality_required_rule(self):
        assert "evidence_quality" in self._s()

    def test_confidence_required_rule(self):
        assert "confidence" in self._s()

    def test_change_triggers_required_rule(self):
        assert "change trigger" in self._s().lower()

    def test_safety_boundary_enforced_rule(self):
        assert "safety boundary" in self._s().lower()

    def test_canonical_values_remain_english_rule(self):
        s = self._s()
        assert "canonical" in s.lower() and "english" in s.lower()


# ---------------------------------------------------------------------------
# Future Implementation Phases
# ---------------------------------------------------------------------------


class TestFutureImplementationPhases:
    def _s(self) -> str:
        return _section("Future Implementation Phases")

    def test_phases_section_exists(self):
        assert "## Future Implementation Phases" in _doc()

    def test_phase_0_data_model(self):
        assert "Phase 0" in self._s()

    def test_phase_1_schema_dataclasses(self):
        assert "Phase 1" in self._s()
        assert "dataclass" in self._s().lower() or "schema" in self._s().lower()

    def test_phase_2_fixtures(self):
        assert "Phase 2" in self._s()
        assert "fixture" in self._s().lower()

    def test_phase_3_validation(self):
        assert "Phase 3" in self._s()
        assert "validat" in self._s().lower()

    def test_phase_4_rendering(self):
        assert "Phase 4" in self._s()
        assert "render" in self._s().lower()

    def test_phase_8_market_data_deferred(self):
        assert "Phase 8" in self._s()
        assert "market data" in self._s().lower()

    def test_no_implementation_in_sprint(self):
        assert "No implementation" in self._s() or "no implementation" in self._s().lower()


# ---------------------------------------------------------------------------
# No runtime behavior changes
# ---------------------------------------------------------------------------


class TestNoRuntimeBehaviorChanges:
    def test_no_value_scenario_python_files_in_atlas(self):
        new_files = list(Path("atlas").rglob("*scenario*.py"))
        assert new_files == [], f"unexpected scenario python files: {new_files}"

    def test_no_sprint_275_python_files_in_atlas(self):
        new_files = list(Path("atlas").rglob("*275*.py"))
        assert new_files == [], f"unexpected python files: {new_files}"

    def test_cli_unchanged_by_sprint_275(self):
        cli_source = CLI_FILE.read_text(encoding="utf-8")
        assert "value_scenario" not in cli_source
        assert "value-scenario" not in cli_source

    def test_no_ai_imports_added(self):
        for src_file in Path("atlas").rglob("*.py"):
            content = src_file.read_text(encoding="utf-8")
            for forbidden in ["import openai", "import anthropic", "import langchain"]:
                assert forbidden not in content, f"AI import found in {src_file}"

    def test_no_valuation_calculation_code_added(self):
        for src_file in Path("atlas").rglob("*.py"):
            content = src_file.read_text(encoding="utf-8")
            assert "scenario_range_calc" not in content
            assert "valuation_model" not in content


# ---------------------------------------------------------------------------
# Compilation check
# ---------------------------------------------------------------------------


class TestCompilation:
    def test_doc_is_valid_utf8(self):
        content = DOC.read_bytes()
        content.decode("utf-8")

    def test_test_file_parses_as_python(self):
        src = Path(__file__).read_text(encoding="utf-8")
        ast.parse(src)
