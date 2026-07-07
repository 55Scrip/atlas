"""Sprint 277 — Value Scenario example fixture tests."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from atlas.value_scenario import (
    HoldingScenario,
    PortfolioScenario,
    ScenarioAssumptionType,
    ScenarioCaseType,
    ScenarioChangeTriggerType,
    ScenarioConfidence,
    ScenarioEvidenceQuality,
    ScenarioEvidenceType,
    ScenarioExpectedEffect,
    ScenarioFreshness,
    ScenarioRangeImpactLevel,
    ScenarioReviewType,
    ScenarioSubjectType,
    ScenarioTimeHorizon,
    ValueScenarioReview,
)

EXAMPLE_DIR = Path("examples/value_scenarios")
HOLDING_FIXTURE = EXAMPLE_DIR / "holding_scenario_review.json"
PORTFOLIO_FIXTURE = EXAMPLE_DIR / "portfolio_scenario_review.json"
CLI_FILE = Path("atlas/cli/main.py")

PROHIBITED_PHRASES = [
    "strong buy",
    "price target",
    "target price",
    "buy now",
    "sell now",
    "must act",
    "urgent action",
    "guaranteed",
    "guaranteed return",
    "risk-free",
    "outperform",
    "entry point",
    "exit point",
    "execution instruction",
    "prediction certainty",
    "will return",
    "will reach",
    "the stock will",
    "personalized financial advice",
]

# ---------------------------------------------------------------------------
# Directory and file existence
# ---------------------------------------------------------------------------


class TestDirectoryAndFiles:
    def test_example_dir_exists(self):
        assert EXAMPLE_DIR.exists()
        assert EXAMPLE_DIR.is_dir()

    def test_holding_fixture_exists(self):
        assert HOLDING_FIXTURE.exists()

    def test_portfolio_fixture_exists(self):
        assert PORTFOLIO_FIXTURE.exists()

    def test_holding_fixture_is_nonempty(self):
        assert HOLDING_FIXTURE.stat().st_size > 100

    def test_portfolio_fixture_is_nonempty(self):
        assert PORTFOLIO_FIXTURE.stat().st_size > 100


# ---------------------------------------------------------------------------
# Valid JSON
# ---------------------------------------------------------------------------


class TestValidJson:
    def test_holding_fixture_is_valid_json(self):
        text = HOLDING_FIXTURE.read_text(encoding="utf-8")
        data = json.loads(text)
        assert isinstance(data, dict)

    def test_portfolio_fixture_is_valid_json(self):
        text = PORTFOLIO_FIXTURE.read_text(encoding="utf-8")
        data = json.loads(text)
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------


class TestSchemaLoading:
    def test_holding_fixture_loads_via_from_json(self):
        text = HOLDING_FIXTURE.read_text(encoding="utf-8")
        r = ValueScenarioReview.from_json(text)
        assert r.scenario_review_id == "vsr_holding_hyp_001"

    def test_portfolio_fixture_loads_via_from_json(self):
        text = PORTFOLIO_FIXTURE.read_text(encoding="utf-8")
        r = ValueScenarioReview.from_json(text)
        assert r.scenario_review_id == "vsr_portfolio_hyp_001"

    def test_holding_fixture_loads_via_from_dict(self):
        data = json.loads(HOLDING_FIXTURE.read_text(encoding="utf-8"))
        r = ValueScenarioReview.from_dict(data)
        assert isinstance(r, ValueScenarioReview)

    def test_portfolio_fixture_loads_via_from_dict(self):
        data = json.loads(PORTFOLIO_FIXTURE.read_text(encoding="utf-8"))
        r = ValueScenarioReview.from_dict(data)
        assert isinstance(r, ValueScenarioReview)


# ---------------------------------------------------------------------------
# Round-trip serialization
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_holding_fixture_roundtrip_id(self):
        text = HOLDING_FIXTURE.read_text(encoding="utf-8")
        r = ValueScenarioReview.from_json(text)
        r2 = ValueScenarioReview.from_json(r.to_json())
        assert r2.scenario_review_id == r.scenario_review_id

    def test_portfolio_fixture_roundtrip_id(self):
        text = PORTFOLIO_FIXTURE.read_text(encoding="utf-8")
        r = ValueScenarioReview.from_json(text)
        r2 = ValueScenarioReview.from_json(r.to_json())
        assert r2.scenario_review_id == r.scenario_review_id

    def test_holding_fixture_roundtrip_review_type(self):
        text = HOLDING_FIXTURE.read_text(encoding="utf-8")
        r = ValueScenarioReview.from_json(text)
        r2 = ValueScenarioReview.from_json(r.to_json())
        assert r2.review_type == r.review_type

    def test_holding_fixture_roundtrip_holding_scenario_count(self):
        text = HOLDING_FIXTURE.read_text(encoding="utf-8")
        r = ValueScenarioReview.from_json(text)
        r2 = ValueScenarioReview.from_json(r.to_json())
        assert len(r2.holding_scenarios) == len(r.holding_scenarios)

    def test_portfolio_fixture_roundtrip_portfolio_scenario(self):
        text = PORTFOLIO_FIXTURE.read_text(encoding="utf-8")
        r = ValueScenarioReview.from_json(text)
        r2 = ValueScenarioReview.from_json(r.to_json())
        assert r2.portfolio_scenario is not None
        assert isinstance(r2.portfolio_scenario, PortfolioScenario)

    def test_holding_fixture_roundtrip_assumption_count(self):
        text = HOLDING_FIXTURE.read_text(encoding="utf-8")
        r = ValueScenarioReview.from_json(text)
        r2 = ValueScenarioReview.from_json(r.to_json())
        assert len(r2.assumptions) == len(r.assumptions)

    def test_holding_fixture_roundtrip_evidence_count(self):
        text = HOLDING_FIXTURE.read_text(encoding="utf-8")
        r = ValueScenarioReview.from_json(text)
        r2 = ValueScenarioReview.from_json(r.to_json())
        assert len(r2.evidence_items) == len(r.evidence_items)


# ---------------------------------------------------------------------------
# Canonical English values
# ---------------------------------------------------------------------------


class TestCanonicalValues:
    def _load(self, path: Path) -> ValueScenarioReview:
        return ValueScenarioReview.from_json(path.read_text(encoding="utf-8"))

    def _valid_enum_values(self, enum_cls) -> set[str]:
        return {e.value for e in enum_cls}

    def test_holding_review_type_canonical(self):
        r = self._load(HOLDING_FIXTURE)
        assert r.review_type in self._valid_enum_values(ScenarioReviewType)

    def test_portfolio_review_type_canonical(self):
        r = self._load(PORTFOLIO_FIXTURE)
        assert r.review_type in self._valid_enum_values(ScenarioReviewType)

    def test_holding_subject_type_canonical(self):
        r = self._load(HOLDING_FIXTURE)
        assert r.subject.subject_type in self._valid_enum_values(ScenarioSubjectType)

    def test_portfolio_subject_type_canonical(self):
        r = self._load(PORTFOLIO_FIXTURE)
        assert r.subject.subject_type in self._valid_enum_values(ScenarioSubjectType)

    def test_holding_time_horizons_canonical(self):
        r = self._load(HOLDING_FIXTURE)
        valid = self._valid_enum_values(ScenarioTimeHorizon)
        for h in r.time_horizons:
            assert h in valid

    def test_portfolio_time_horizons_canonical(self):
        r = self._load(PORTFOLIO_FIXTURE)
        valid = self._valid_enum_values(ScenarioTimeHorizon)
        for h in r.time_horizons:
            assert h in valid

    def test_holding_range_case_types_canonical(self):
        r = self._load(HOLDING_FIXTURE)
        valid = self._valid_enum_values(ScenarioCaseType)
        for hs in r.holding_scenarios:
            for rng in hs.ranges:
                assert rng.case_type in valid

    def test_portfolio_range_case_types_canonical(self):
        r = self._load(PORTFOLIO_FIXTURE)
        valid = self._valid_enum_values(ScenarioCaseType)
        assert r.portfolio_scenario is not None
        for rng in r.portfolio_scenario.ranges:
            assert rng.case_type in valid

    def test_holding_assumption_types_canonical(self):
        r = self._load(HOLDING_FIXTURE)
        valid = self._valid_enum_values(ScenarioAssumptionType)
        for a in r.assumptions:
            assert a.assumption_type in valid

    def test_portfolio_assumption_types_canonical(self):
        r = self._load(PORTFOLIO_FIXTURE)
        valid = self._valid_enum_values(ScenarioAssumptionType)
        for a in r.assumptions:
            assert a.assumption_type in valid

    def test_holding_evidence_types_canonical(self):
        r = self._load(HOLDING_FIXTURE)
        valid = self._valid_enum_values(ScenarioEvidenceType)
        for e in r.evidence_items:
            assert e.evidence_type in valid

    def test_portfolio_evidence_types_canonical(self):
        r = self._load(PORTFOLIO_FIXTURE)
        valid = self._valid_enum_values(ScenarioEvidenceType)
        for e in r.evidence_items:
            assert e.evidence_type in valid

    def test_holding_evidence_quality_canonical(self):
        r = self._load(HOLDING_FIXTURE)
        valid = self._valid_enum_values(ScenarioEvidenceQuality)
        for hs in r.holding_scenarios:
            assert hs.evidence_quality in valid
            for rng in hs.ranges:
                assert rng.evidence_quality in valid

    def test_holding_confidence_canonical(self):
        r = self._load(HOLDING_FIXTURE)
        valid = self._valid_enum_values(ScenarioConfidence)
        for hs in r.holding_scenarios:
            assert hs.confidence in valid
            for rng in hs.ranges:
                assert rng.confidence in valid

    def test_holding_trigger_types_canonical(self):
        r = self._load(HOLDING_FIXTURE)
        valid = self._valid_enum_values(ScenarioChangeTriggerType)
        for t in r.change_triggers:
            assert t.trigger_type in valid

    def test_holding_expected_effects_canonical(self):
        r = self._load(HOLDING_FIXTURE)
        valid = self._valid_enum_values(ScenarioExpectedEffect)
        for t in r.change_triggers:
            assert t.expected_effect in valid

    def test_portfolio_range_impact_levels_canonical(self):
        r = self._load(PORTFOLIO_FIXTURE)
        valid = self._valid_enum_values(ScenarioRangeImpactLevel)
        assert r.portfolio_scenario is not None
        for c in r.portfolio_scenario.weighted_contributions:
            assert c.range_impact_level in valid

    def test_holding_freshness_canonical(self):
        r = self._load(HOLDING_FIXTURE)
        valid = self._valid_enum_values(ScenarioFreshness)
        for e in r.evidence_items:
            assert e.freshness in valid


# ---------------------------------------------------------------------------
# No single-point ranges
# ---------------------------------------------------------------------------


class TestNoSinglePointRanges:
    def _load(self, path: Path) -> ValueScenarioReview:
        return ValueScenarioReview.from_json(path.read_text(encoding="utf-8"))

    def test_holding_ranges_not_single_point(self):
        r = self._load(HOLDING_FIXTURE)
        for hs in r.holding_scenarios:
            for rng in hs.ranges:
                assert rng.lower_percent < rng.upper_percent, (
                    f"Range {rng.range_id} is a single-point target: {rng.lower_percent}"
                )

    def test_portfolio_ranges_not_single_point(self):
        r = self._load(PORTFOLIO_FIXTURE)
        assert r.portfolio_scenario is not None
        for rng in r.portfolio_scenario.ranges:
            assert rng.lower_percent < rng.upper_percent, (
                f"Range {rng.range_id} is a single-point target: {rng.lower_percent}"
            )

    def test_holding_bear_range_is_range(self):
        r = self._load(HOLDING_FIXTURE)
        bear_ranges = [
            rng
            for hs in r.holding_scenarios
            for rng in hs.ranges
            if rng.case_type == "bear"
        ]
        assert len(bear_ranges) >= 1
        for rng in bear_ranges:
            assert rng.upper_percent - rng.lower_percent >= 1.0

    def test_holding_base_range_is_range(self):
        r = self._load(HOLDING_FIXTURE)
        base_ranges = [
            rng
            for hs in r.holding_scenarios
            for rng in hs.ranges
            if rng.case_type == "base"
        ]
        assert len(base_ranges) >= 1

    def test_holding_bull_range_is_range(self):
        r = self._load(HOLDING_FIXTURE)
        bull_ranges = [
            rng
            for hs in r.holding_scenarios
            for rng in hs.ranges
            if rng.case_type == "bull"
        ]
        assert len(bull_ranges) >= 1


# ---------------------------------------------------------------------------
# Safety boundary
# ---------------------------------------------------------------------------


class TestSafetyBoundary:
    def _load(self, path: Path) -> ValueScenarioReview:
        return ValueScenarioReview.from_json(path.read_text(encoding="utf-8"))

    def test_holding_safety_boundary_all_true(self):
        r = self._load(HOLDING_FIXTURE)
        sb = r.safety_boundary
        assert sb.no_single_point_targets is True
        assert sb.no_action_calls is True
        assert sb.no_execution_instructions is True
        assert sb.no_prediction_certainty is True
        assert sb.assumptions_required is True
        assert sb.evidence_quality_required is True
        assert sb.uncertainty_required is True
        assert sb.change_triggers_required is True

    def test_portfolio_safety_boundary_all_true(self):
        r = self._load(PORTFOLIO_FIXTURE)
        sb = r.safety_boundary
        assert sb.no_single_point_targets is True
        assert sb.no_action_calls is True
        assert sb.no_execution_instructions is True
        assert sb.no_prediction_certainty is True
        assert sb.assumptions_required is True
        assert sb.evidence_quality_required is True
        assert sb.uncertainty_required is True
        assert sb.change_triggers_required is True


# ---------------------------------------------------------------------------
# Assumptions present
# ---------------------------------------------------------------------------


class TestAssumptions:
    def _load(self, path: Path) -> ValueScenarioReview:
        return ValueScenarioReview.from_json(path.read_text(encoding="utf-8"))

    def test_holding_has_assumptions(self):
        r = self._load(HOLDING_FIXTURE)
        assert len(r.assumptions) >= 3

    def test_portfolio_has_assumptions(self):
        r = self._load(PORTFOLIO_FIXTURE)
        assert len(r.assumptions) >= 3

    def test_holding_assumptions_have_descriptions(self):
        r = self._load(HOLDING_FIXTURE)
        for a in r.assumptions:
            assert a.description.strip(), f"Assumption {a.assumption_id} has empty description"

    def test_portfolio_assumptions_have_descriptions(self):
        r = self._load(PORTFOLIO_FIXTURE)
        for a in r.assumptions:
            assert a.description.strip()

    def test_holding_assumption_types_diverse(self):
        r = self._load(HOLDING_FIXTURE)
        types = {a.assumption_type for a in r.assumptions}
        assert len(types) >= 2


# ---------------------------------------------------------------------------
# Evidence items present
# ---------------------------------------------------------------------------


class TestEvidenceItems:
    def _load(self, path: Path) -> ValueScenarioReview:
        return ValueScenarioReview.from_json(path.read_text(encoding="utf-8"))

    def test_holding_has_evidence_items(self):
        r = self._load(HOLDING_FIXTURE)
        assert len(r.evidence_items) >= 2

    def test_portfolio_has_evidence_items(self):
        r = self._load(PORTFOLIO_FIXTURE)
        assert len(r.evidence_items) >= 2

    def test_holding_evidence_has_descriptions(self):
        r = self._load(HOLDING_FIXTURE)
        for e in r.evidence_items:
            assert e.description.strip()

    def test_holding_evidence_has_quality(self):
        r = self._load(HOLDING_FIXTURE)
        valid = {e.value for e in ScenarioEvidenceQuality}
        for e in r.evidence_items:
            assert e.evidence_quality in valid


# ---------------------------------------------------------------------------
# Change triggers present
# ---------------------------------------------------------------------------


class TestChangeTriggers:
    def _load(self, path: Path) -> ValueScenarioReview:
        return ValueScenarioReview.from_json(path.read_text(encoding="utf-8"))

    def test_holding_has_change_triggers(self):
        r = self._load(HOLDING_FIXTURE)
        assert len(r.change_triggers) >= 2

    def test_portfolio_has_change_triggers(self):
        r = self._load(PORTFOLIO_FIXTURE)
        assert len(r.change_triggers) >= 2

    def test_holding_triggers_have_descriptions(self):
        r = self._load(HOLDING_FIXTURE)
        for t in r.change_triggers:
            assert t.description.strip()

    def test_portfolio_triggers_have_expected_effects(self):
        r = self._load(PORTFOLIO_FIXTURE)
        valid = {e.value for e in ScenarioExpectedEffect}
        for t in r.change_triggers:
            assert t.expected_effect in valid


# ---------------------------------------------------------------------------
# Holding fixture structure
# ---------------------------------------------------------------------------


class TestHoldingFixtureStructure:
    def _load(self) -> ValueScenarioReview:
        return ValueScenarioReview.from_json(HOLDING_FIXTURE.read_text(encoding="utf-8"))

    def test_review_type_is_holding(self):
        r = self._load()
        assert r.review_type == "holding"

    def test_has_at_least_one_holding_scenario(self):
        r = self._load()
        assert len(r.holding_scenarios) >= 1

    def test_holding_scenario_has_subject(self):
        r = self._load()
        assert r.holding_scenarios[0].subject is not None

    def test_holding_scenario_has_ranges(self):
        r = self._load()
        assert len(r.holding_scenarios[0].ranges) >= 3

    def test_holding_scenario_has_bear_range(self):
        r = self._load()
        case_types = {rng.case_type for hs in r.holding_scenarios for rng in hs.ranges}
        assert "bear" in case_types

    def test_holding_scenario_has_base_range(self):
        r = self._load()
        case_types = {rng.case_type for hs in r.holding_scenarios for rng in hs.ranges}
        assert "base" in case_types

    def test_holding_scenario_has_bull_range(self):
        r = self._load()
        case_types = {rng.case_type for hs in r.holding_scenarios for rng in hs.ranges}
        assert "bull" in case_types

    def test_portfolio_scenario_is_null(self):
        r = self._load()
        assert r.portfolio_scenario is None

    def test_holding_scenario_has_key_drivers(self):
        r = self._load()
        assert len(r.holding_scenarios[0].key_drivers) >= 1

    def test_holding_scenario_has_key_risks(self):
        r = self._load()
        assert len(r.holding_scenarios[0].key_risks) >= 1

    def test_holding_scenario_has_notes(self):
        r = self._load()
        assert r.holding_scenarios[0].notes is not None
        assert len(r.holding_scenarios[0].notes) > 0

    def test_has_at_least_one_time_horizon(self):
        r = self._load()
        assert len(r.time_horizons) >= 1


# ---------------------------------------------------------------------------
# Portfolio fixture structure
# ---------------------------------------------------------------------------


class TestPortfolioFixtureStructure:
    def _load(self) -> ValueScenarioReview:
        return ValueScenarioReview.from_json(PORTFOLIO_FIXTURE.read_text(encoding="utf-8"))

    def test_review_type_is_portfolio(self):
        r = self._load()
        assert r.review_type == "portfolio"

    def test_has_portfolio_scenario(self):
        r = self._load()
        assert r.portfolio_scenario is not None
        assert isinstance(r.portfolio_scenario, PortfolioScenario)

    def test_portfolio_scenario_has_ranges(self):
        r = self._load()
        assert len(r.portfolio_scenario.ranges) >= 2

    def test_portfolio_scenario_has_weighted_contributions(self):
        r = self._load()
        assert len(r.portfolio_scenario.weighted_contributions) >= 2

    def test_portfolio_scenario_has_upside_drivers(self):
        r = self._load()
        assert len(r.portfolio_scenario.main_upside_drivers) >= 1

    def test_portfolio_scenario_has_downside_drivers(self):
        r = self._load()
        assert len(r.portfolio_scenario.main_downside_drivers) >= 1

    def test_portfolio_scenario_has_evidence_gaps(self):
        r = self._load()
        assert len(r.portfolio_scenario.evidence_gaps) >= 1

    def test_portfolio_scenario_has_concentration_sensitivity(self):
        r = self._load()
        assert r.portfolio_scenario.concentration_sensitivity is not None

    def test_holding_scenarios_empty_for_portfolio_review(self):
        r = self._load()
        assert r.holding_scenarios == []

    def test_contribution_impact_levels_present(self):
        r = self._load()
        impact_levels = {c.range_impact_level for c in r.portfolio_scenario.weighted_contributions}
        assert len(impact_levels) >= 1

    def test_contribution_weights_present(self):
        r = self._load()
        for c in r.portfolio_scenario.weighted_contributions:
            assert c.portfolio_weight is not None
            assert 0.0 < c.portfolio_weight < 1.0


# ---------------------------------------------------------------------------
# Descriptive text preservation
# ---------------------------------------------------------------------------


class TestDescriptiveTextPreservation:
    HOLDING_TEXTS = [
        "Revenue growth assumption requires confirmation.",
        "Margin durability evidence is incomplete.",
        "Scenario range should be revisited after the next company update.",
    ]
    PORTFOLIO_TEXTS = [
        "Portfolio range is sensitive to valuation assumptions and concentration.",
        "Several holdings require evidence refresh before confidence can improve.",
        "Downside range could widen if margin assumptions weaken.",
    ]

    def _all_text(self, path: Path) -> str:
        r = ValueScenarioReview.from_json(path.read_text(encoding="utf-8"))
        # Collect all string fields across the review
        parts = [r.to_json()]
        return " ".join(parts)

    @pytest.mark.parametrize("phrase", HOLDING_TEXTS)
    def test_holding_descriptive_text_present(self, phrase: str):
        text = self._all_text(HOLDING_FIXTURE)
        assert phrase in text, f"Expected phrase not found: {phrase!r}"

    @pytest.mark.parametrize("phrase", PORTFOLIO_TEXTS)
    def test_portfolio_descriptive_text_present(self, phrase: str):
        text = self._all_text(PORTFOLIO_FIXTURE)
        assert phrase in text, f"Expected phrase not found: {phrase!r}"

    def test_holding_text_preserved_through_roundtrip(self):
        r = ValueScenarioReview.from_json(HOLDING_FIXTURE.read_text(encoding="utf-8"))
        r2 = ValueScenarioReview.from_json(r.to_json())
        text2 = r2.to_json()
        for phrase in self.HOLDING_TEXTS:
            assert phrase in text2

    def test_portfolio_text_preserved_through_roundtrip(self):
        r = ValueScenarioReview.from_json(PORTFOLIO_FIXTURE.read_text(encoding="utf-8"))
        r2 = ValueScenarioReview.from_json(r.to_json())
        text2 = r2.to_json()
        for phrase in self.PORTFOLIO_TEXTS:
            assert phrase in text2


# ---------------------------------------------------------------------------
# Safe language — no prohibited phrases
# ---------------------------------------------------------------------------


class TestSafeLanguage:
    @pytest.mark.parametrize("phrase", PROHIBITED_PHRASES)
    def test_holding_fixture_no_prohibited_phrase(self, phrase: str):
        text = HOLDING_FIXTURE.read_text(encoding="utf-8").lower()
        assert phrase.lower() not in text, f"Prohibited phrase found in holding fixture: {phrase!r}"

    @pytest.mark.parametrize("phrase", PROHIBITED_PHRASES)
    def test_portfolio_fixture_no_prohibited_phrase(self, phrase: str):
        text = PORTFOLIO_FIXTURE.read_text(encoding="utf-8").lower()
        assert phrase.lower() not in text, f"Prohibited phrase found in portfolio fixture: {phrase!r}"


# ---------------------------------------------------------------------------
# No calculations, no runtime changes
# ---------------------------------------------------------------------------


class TestNoRuntimeBehaviorChanges:
    def test_no_new_value_scenario_cli_commands(self):
        cli_source = CLI_FILE.read_text(encoding="utf-8")
        assert "value_scenario" not in cli_source
        assert "value-scenario" not in cli_source

    def test_no_ai_imports_added(self):
        for src_file in Path("atlas").rglob("*.py"):
            content = src_file.read_text(encoding="utf-8")
            for forbidden in ["import openai", "import anthropic", "import langchain"]:
                assert forbidden not in content, f"AI import found in {src_file}"

    def test_fixtures_not_written_by_runtime_code(self):
        src = Path("atlas/value_scenario/schema.py").read_text(encoding="utf-8")
        assert "write_text" not in src
        assert "open(" not in src

    def test_fixture_files_are_static_json(self):
        for fixture in [HOLDING_FIXTURE, PORTFOLIO_FIXTURE]:
            assert fixture.suffix == ".json"
            assert fixture.exists()

    def test_no_calculation_code_in_schema(self):
        src = Path("atlas/value_scenario/schema.py").read_text(encoding="utf-8")
        for forbidden in ["math.log", "numpy", "scipy", "pandas", "statistics.mean"]:
            assert forbidden not in src


# ---------------------------------------------------------------------------
# Compilation
# ---------------------------------------------------------------------------


class TestCompilation:
    def test_test_file_parses_as_python(self):
        src = Path(__file__).read_text(encoding="utf-8")
        ast.parse(src)

    def test_holding_fixture_utf8(self):
        HOLDING_FIXTURE.read_bytes().decode("utf-8")

    def test_portfolio_fixture_utf8(self):
        PORTFOLIO_FIXTURE.read_bytes().decode("utf-8")
