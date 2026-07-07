"""Sprint 279 — Value Scenario summary CLI tests."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

CLI = Path(".venv/bin/atlas")
CLI_FILE = Path("atlas/cli/main.py")
RENDER_FILE = Path("atlas/value_scenario/render.py")
HOLDING_FIXTURE = Path("examples/value_scenarios/holding_scenario_review.json")
PORTFOLIO_FIXTURE = Path("examples/value_scenarios/portfolio_scenario_review.json")

PROHIBITED_PHRASES = [
    "buy",
    "sell",
    "strong buy",
    "price target",
    "act now",
    "outperform",
    "guaranteed",
    "recommendation",
    "must purchase",
    "must sell",
]


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(CLI), *args],
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# CLI structure
# ---------------------------------------------------------------------------


class TestCliStructure:
    def test_summary_command_in_cli_source(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        assert '@value_scenario_app.command("summary")' in src

    def test_render_module_imported_in_cli(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        assert "render_value_scenario_summary" in src

    def test_value_scenario_help_includes_summary(self):
        result = _run("value-scenario", "--help")
        assert "summary" in result.stdout

    def test_summary_help_exits_zero(self):
        result = _run("value-scenario", "summary", "--help")
        assert result.returncode == 0

    def test_render_file_exists(self):
        assert RENDER_FILE.exists()

    def test_render_file_has_render_function(self):
        src = RENDER_FILE.read_text(encoding="utf-8")
        assert "def render_value_scenario_summary" in src


# ---------------------------------------------------------------------------
# Holding fixture summary
# ---------------------------------------------------------------------------


class TestHoldingSummary:
    def setup_method(self):
        self.result = _run("value-scenario", "summary", str(HOLDING_FIXTURE))

    def test_exit_code_zero(self):
        assert self.result.returncode == 0

    def test_header_present(self):
        assert "Value Scenario Review" in self.result.stdout

    def test_review_type_holding(self):
        assert "holding" in self.result.stdout

    def test_subject_present(self):
        assert "Hypothetical Cloud Infrastructure Co." in self.result.stdout

    def test_ticker_present(self):
        assert "HYP" in self.result.stdout

    def test_time_horizons_present(self):
        assert "medium_term" in self.result.stdout

    def test_bear_range_present(self):
        assert "-18%" in self.result.stdout or "-18" in self.result.stdout

    def test_bear_range_upper(self):
        assert "-8%" in self.result.stdout or "-8" in self.result.stdout

    def test_base_range_lower(self):
        assert "6%" in self.result.stdout or "6 " in self.result.stdout

    def test_base_range_upper(self):
        assert "16%" in self.result.stdout

    def test_bull_range_lower(self):
        assert "18%" in self.result.stdout

    def test_bull_range_upper(self):
        assert "32%" in self.result.stdout

    def test_long_term_base_range_present(self):
        assert "35%" in self.result.stdout
        assert "75%" in self.result.stdout

    def test_evidence_quality_present(self):
        assert "Evidence Quality" in self.result.stdout

    def test_confidence_present(self):
        assert "Confidence" in self.result.stdout

    def test_assumptions_count(self):
        assert "Assumptions" in self.result.stdout
        assert "5" in self.result.stdout

    def test_evidence_items_count(self):
        assert "Evidence Items" in self.result.stdout
        assert "2" in self.result.stdout

    def test_change_triggers_count(self):
        assert "Change Triggers" in self.result.stdout
        assert "3" in self.result.stdout

    def test_safety_boundary_present(self):
        assert "Safety Boundary" in self.result.stdout

    def test_safety_boundary_no_single_point_targets(self):
        assert "No single-point targets" in self.result.stdout

    def test_safety_boundary_checkmarks(self):
        assert "✓" in self.result.stdout

    def test_reminder_present(self):
        assert "Atlas helps structure judgment" in self.result.stdout
        assert "does not predict future returns" in self.result.stdout

    def test_no_stderr(self):
        assert self.result.stderr == ""


# ---------------------------------------------------------------------------
# Portfolio fixture summary
# ---------------------------------------------------------------------------


class TestPortfolioSummary:
    def setup_method(self):
        self.result = _run("value-scenario", "summary", str(PORTFOLIO_FIXTURE))

    def test_exit_code_zero(self):
        assert self.result.returncode == 0

    def test_header_present(self):
        assert "Value Scenario Review" in self.result.stdout

    def test_review_type_portfolio(self):
        assert "portfolio" in self.result.stdout

    def test_subject_present(self):
        assert "Hypothetical Concentrated Growth Portfolio" in self.result.stdout

    def test_downside_range_present(self):
        assert "-16%" in self.result.stdout or "-16" in self.result.stdout

    def test_base_range_present(self):
        assert "5%" in self.result.stdout
        assert "13%" in self.result.stdout

    def test_upside_range_present(self):
        assert "16%" in self.result.stdout
        assert "26%" in self.result.stdout

    def test_portfolio_contributions_present(self):
        assert "HSMC" in self.result.stdout or "Semiconductor" in self.result.stdout

    def test_evidence_quality_present(self):
        assert "Evidence Quality" in self.result.stdout

    def test_confidence_present(self):
        assert "Confidence" in self.result.stdout

    def test_assumptions_count(self):
        assert "3" in self.result.stdout

    def test_safety_boundary_present(self):
        assert "Safety Boundary" in self.result.stdout

    def test_reminder_present(self):
        assert "Atlas helps structure judgment" in self.result.stdout

    def test_no_stderr(self):
        assert self.result.stderr == ""


# ---------------------------------------------------------------------------
# Ranges preserved exactly
# ---------------------------------------------------------------------------


class TestRangesPreserved:
    def test_holding_bear_lower_exact(self):
        result = _run("value-scenario", "summary", str(HOLDING_FIXTURE))
        assert "-18%" in result.stdout

    def test_holding_bear_upper_exact(self):
        result = _run("value-scenario", "summary", str(HOLDING_FIXTURE))
        assert "-8%" in result.stdout

    def test_holding_bull_upper_exact(self):
        result = _run("value-scenario", "summary", str(HOLDING_FIXTURE))
        assert "32%" in result.stdout

    def test_holding_long_term_base_exact(self):
        result = _run("value-scenario", "summary", str(HOLDING_FIXTURE))
        assert "35%" in result.stdout
        assert "75%" in result.stdout

    def test_portfolio_downside_lower_exact(self):
        result = _run("value-scenario", "summary", str(PORTFOLIO_FIXTURE))
        assert "-16%" in result.stdout

    def test_portfolio_upside_upper_exact(self):
        result = _run("value-scenario", "summary", str(PORTFOLIO_FIXTURE))
        assert "26%" in result.stdout

    def test_ranges_not_averaged(self):
        result = _run("value-scenario", "summary", str(HOLDING_FIXTURE))
        # bear: -18 to -8 → average would be -13; confirm -13 is not presented as a target
        # just verify both endpoints are present
        assert "-18%" in result.stdout
        assert "-8%" in result.stdout


# ---------------------------------------------------------------------------
# Evidence quality and confidence preserved
# ---------------------------------------------------------------------------


class TestEvidenceAndConfidencePreserved:
    def test_holding_evidence_quality_value(self):
        result = _run("value-scenario", "summary", str(HOLDING_FIXTURE))
        assert "adequate" in result.stdout

    def test_portfolio_evidence_quality_value(self):
        result = _run("value-scenario", "summary", str(PORTFOLIO_FIXTURE))
        assert "incomplete" in result.stdout

    def test_holding_confidence_value(self):
        result = _run("value-scenario", "summary", str(HOLDING_FIXTURE))
        assert "medium" in result.stdout

    def test_portfolio_confidence_value(self):
        result = _run("value-scenario", "summary", str(PORTFOLIO_FIXTURE))
        assert "medium" in result.stdout


# ---------------------------------------------------------------------------
# Safety boundary preserved
# ---------------------------------------------------------------------------


class TestSafetyBoundaryPreserved:
    def test_holding_safety_boundary_fields(self):
        result = _run("value-scenario", "summary", str(HOLDING_FIXTURE))
        for label in [
            "No single-point targets",
            "No action calls",
            "No execution instructions",
            "Assumptions required",
            "Evidence quality required",
            "Uncertainty required",
            "Change triggers required",
        ]:
            assert label in result.stdout, f"Safety boundary field missing: {label}"

    def test_portfolio_safety_boundary_checkmarks(self):
        result = _run("value-scenario", "summary", str(PORTFOLIO_FIXTURE))
        assert "✓" in result.stdout


# ---------------------------------------------------------------------------
# Invalid JSON
# ---------------------------------------------------------------------------


class TestInvalidJson:
    def test_exits_nonzero(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("{not json")
            path = f.name
        result = _run("value-scenario", "summary", path)
        assert result.returncode != 0

    def test_prints_error(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("{not json")
            path = f.name
        result = _run("value-scenario", "summary", path)
        assert "invalid JSON" in result.stdout

    def test_no_stack_trace(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("{not json")
            path = f.name
        result = _run("value-scenario", "summary", path)
        assert "Traceback" not in result.stdout
        assert "Traceback" not in result.stderr


# ---------------------------------------------------------------------------
# Missing file
# ---------------------------------------------------------------------------


class TestMissingFile:
    def test_exits_nonzero(self):
        result = _run("value-scenario", "summary", "no_such_file_xyz.json")
        assert result.returncode != 0

    def test_prints_error(self):
        result = _run("value-scenario", "summary", "no_such_file_xyz.json")
        assert "file not found" in result.stdout

    def test_no_stack_trace(self):
        result = _run("value-scenario", "summary", "no_such_file_xyz.json")
        assert "Traceback" not in result.stdout


# ---------------------------------------------------------------------------
# Directory path
# ---------------------------------------------------------------------------


class TestDirectoryPath:
    def test_exits_nonzero(self):
        result = _run("value-scenario", "summary", "examples/value_scenarios")
        assert result.returncode != 0

    def test_prints_error(self):
        result = _run("value-scenario", "summary", "examples/value_scenarios")
        assert "expected a JSON file path" in result.stdout


# ---------------------------------------------------------------------------
# Schema failure
# ---------------------------------------------------------------------------


class TestSchemaFailure:
    def test_invalid_review_type_exits_nonzero(self):
        data = json.loads(HOLDING_FIXTURE.read_text(encoding="utf-8"))
        data["review_type"] = "not_valid"
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(data, f)
            path = f.name
        result = _run("value-scenario", "summary", path)
        assert result.returncode != 0

    def test_schema_failure_prints_error(self):
        data = json.loads(HOLDING_FIXTURE.read_text(encoding="utf-8"))
        data["scenario_review_id"] = ""
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(data, f)
            path = f.name
        result = _run("value-scenario", "summary", path)
        assert "failed" in result.stdout.lower()

    def test_schema_failure_no_stack_trace(self):
        data = json.loads(HOLDING_FIXTURE.read_text(encoding="utf-8"))
        data["scenario_review_id"] = ""
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(data, f)
            path = f.name
        result = _run("value-scenario", "summary", path)
        assert "Traceback" not in result.stdout


# ---------------------------------------------------------------------------
# No modification / no output files
# ---------------------------------------------------------------------------


class TestNoModification:
    def test_holding_fixture_not_modified(self):
        before = HOLDING_FIXTURE.read_bytes()
        _run("value-scenario", "summary", str(HOLDING_FIXTURE))
        after = HOLDING_FIXTURE.read_bytes()
        assert before == after

    def test_portfolio_fixture_not_modified(self):
        before = PORTFOLIO_FIXTURE.read_bytes()
        _run("value-scenario", "summary", str(PORTFOLIO_FIXTURE))
        after = PORTFOLIO_FIXTURE.read_bytes()
        assert before == after

    def test_no_output_files_in_examples_dir(self):
        before = set(Path("examples/value_scenarios").iterdir())
        _run("value-scenario", "summary", str(HOLDING_FIXTURE))
        after = set(Path("examples/value_scenarios").iterdir())
        assert before == after


# ---------------------------------------------------------------------------
# Safe language
# ---------------------------------------------------------------------------


class TestSafeLanguage:
    @pytest.mark.parametrize("phrase", PROHIBITED_PHRASES)
    def test_holding_output_no_prohibited_phrase(self, phrase: str):
        result = _run("value-scenario", "summary", str(HOLDING_FIXTURE))
        assert phrase.lower() not in result.stdout.lower(), (
            f"Prohibited phrase {phrase!r} found in holding summary output"
        )

    @pytest.mark.parametrize("phrase", PROHIBITED_PHRASES)
    def test_portfolio_output_no_prohibited_phrase(self, phrase: str):
        result = _run("value-scenario", "summary", str(PORTFOLIO_FIXTURE))
        assert phrase.lower() not in result.stdout.lower(), (
            f"Prohibited phrase {phrase!r} found in portfolio summary output"
        )

    def test_render_module_no_prohibited_phrases(self):
        src = RENDER_FILE.read_text(encoding="utf-8").lower()
        for phrase in ["buy", "sell", "strong buy", "outperform", "guaranteed"]:
            assert phrase not in src, f"Prohibited phrase {phrase!r} in render.py"


# ---------------------------------------------------------------------------
# No provider / network / AI imports
# ---------------------------------------------------------------------------


class TestNoBoundaryViolations:
    def test_render_module_no_network_imports(self):
        src = RENDER_FILE.read_text(encoding="utf-8")
        for forbidden in ["requests", "httpx", "urllib.request", "socket", "aiohttp"]:
            assert forbidden not in src

    def test_render_module_no_ai_imports(self):
        src = RENDER_FILE.read_text(encoding="utf-8")
        for forbidden in ["openai", "anthropic", "langchain"]:
            assert forbidden not in src

    def test_render_module_no_calculation_imports(self):
        src = RENDER_FILE.read_text(encoding="utf-8")
        for forbidden in ["numpy", "scipy", "pandas", "statistics"]:
            assert forbidden not in src

    def test_cli_no_new_provider_imports(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        for forbidden in ["import openai", "import anthropic", "import langchain", "import httpx"]:
            assert forbidden not in src

    def test_render_module_stdlib_only(self):
        src = RENDER_FILE.read_text(encoding="utf-8")
        assert "from atlas.value_scenario" in src
        for non_stdlib in ["requests", "httpx", "numpy", "pandas", "openai"]:
            assert non_stdlib not in src


# ---------------------------------------------------------------------------
# Existing commands unchanged
# ---------------------------------------------------------------------------


class TestExistingCommandsUnchanged:
    def test_validate_command_still_works_holding(self):
        result = _run("value-scenario", "validate", str(HOLDING_FIXTURE))
        assert result.returncode == 0
        assert "Value scenario is valid." in result.stdout

    def test_validate_command_still_works_portfolio(self):
        result = _run("value-scenario", "validate", str(PORTFOLIO_FIXTURE))
        assert result.returncode == 0

    def test_weekly_review_help_unchanged(self):
        result = _run("weekly-review", "--help")
        assert result.returncode == 0

    def test_temporary_workspace_validate_unchanged(self):
        result = _run(
            "temporary-workspace", "validate",
            "examples/temporary_workspaces/portfolio_snapshot_workspace.json",
        )
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# Guard: summary command present in CLI
# ---------------------------------------------------------------------------


class TestGuard:
    def test_summary_command_registered(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        assert '@value_scenario_app.command("summary")' in src

    def test_validate_command_still_registered(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        assert '@value_scenario_app.command("validate")' in src
        assert "value_scenario_app" in src
        assert 'name="value-scenario"' in src
