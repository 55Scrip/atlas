"""Sprint 278 — Value Scenario validation CLI tests."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

CLI = Path(".venv/bin/atlas")
CLI_FILE = Path("atlas/cli/main.py")
HOLDING_FIXTURE = Path("examples/value_scenarios/holding_scenario_review.json")
PORTFOLIO_FIXTURE = Path("examples/value_scenarios/portfolio_scenario_review.json")

PROHIBITED_PHRASES = [
    "buy",
    "sell",
    "strong buy",
    "price target",
    "act now",
    "urgent",
    "should purchase",
    "should exit",
    "outperform",
    "recommendation",
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
    def test_value_scenario_app_in_cli_source(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        assert "value_scenario_app" in src

    def test_value_scenario_typer_registered(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        assert 'name="value-scenario"' in src

    def test_validate_command_in_cli_source(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        assert '@value_scenario_app.command("validate")' in src

    def test_help_includes_value_scenario(self):
        result = _run("--help")
        assert "value-scenario" in result.stdout

    def test_value_scenario_help_includes_validate(self):
        result = _run("value-scenario", "--help")
        assert "validate" in result.stdout

    def test_validate_help_text(self):
        result = _run("value-scenario", "validate", "--help")
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# Valid holding fixture
# ---------------------------------------------------------------------------


class TestValidHoldingFixture:
    def setup_method(self):
        self.result = _run("value-scenario", "validate", str(HOLDING_FIXTURE))

    def test_exit_code_zero(self):
        assert self.result.returncode == 0

    def test_valid_message(self):
        assert "Value scenario is valid." in self.result.stdout

    def test_scenario_review_id(self):
        assert "vsr_holding_hyp_001" in self.result.stdout

    def test_review_type_holding(self):
        assert "Review Type: holding" in self.result.stdout

    def test_holding_scenarios_count(self):
        assert "Holding Scenarios: 1" in self.result.stdout

    def test_portfolio_scenario_no(self):
        assert "Portfolio Scenario: no" in self.result.stdout

    def test_ranges_count(self):
        assert "Ranges: 4" in self.result.stdout

    def test_assumptions_count(self):
        assert "Assumptions: 5" in self.result.stdout

    def test_evidence_items_count(self):
        assert "Evidence Items: 2" in self.result.stdout

    def test_change_triggers_count(self):
        assert "Change Triggers: 3" in self.result.stdout

    def test_no_stderr(self):
        assert self.result.stderr == ""


# ---------------------------------------------------------------------------
# Valid portfolio fixture
# ---------------------------------------------------------------------------


class TestValidPortfolioFixture:
    def setup_method(self):
        self.result = _run("value-scenario", "validate", str(PORTFOLIO_FIXTURE))

    def test_exit_code_zero(self):
        assert self.result.returncode == 0

    def test_valid_message(self):
        assert "Value scenario is valid." in self.result.stdout

    def test_scenario_review_id(self):
        assert "vsr_portfolio_hyp_001" in self.result.stdout

    def test_review_type_portfolio(self):
        assert "Review Type: portfolio" in self.result.stdout

    def test_holding_scenarios_count(self):
        assert "Holding Scenarios: 0" in self.result.stdout

    def test_portfolio_scenario_yes(self):
        assert "Portfolio Scenario: yes" in self.result.stdout

    def test_ranges_count(self):
        assert "Ranges: 3" in self.result.stdout

    def test_assumptions_count(self):
        assert "Assumptions: 3" in self.result.stdout

    def test_evidence_items_count(self):
        assert "Evidence Items: 2" in self.result.stdout

    def test_change_triggers_count(self):
        assert "Change Triggers: 2" in self.result.stdout

    def test_no_stderr(self):
        assert self.result.stderr == ""


# ---------------------------------------------------------------------------
# Invalid JSON
# ---------------------------------------------------------------------------


class TestInvalidJson:
    def _run_with_content(self, content: str) -> subprocess.CompletedProcess:
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write(content)
            path = f.name
        return _run("value-scenario", "validate", path)

    def test_invalid_json_exits_nonzero(self):
        result = self._run_with_content("{not valid json")
        assert result.returncode != 0

    def test_invalid_json_prints_error(self):
        result = self._run_with_content("{not valid json")
        assert "invalid JSON" in result.stdout

    def test_invalid_json_no_stack_trace(self):
        result = self._run_with_content("{not valid json")
        assert "Traceback" not in result.stdout
        assert "Traceback" not in result.stderr

    def test_empty_file_exits_nonzero(self):
        result = self._run_with_content("")
        assert result.returncode != 0

    def test_empty_file_prints_error(self):
        result = self._run_with_content("")
        assert "failed" in result.stdout.lower()


# ---------------------------------------------------------------------------
# Missing file
# ---------------------------------------------------------------------------


class TestMissingFile:
    def test_missing_file_exits_nonzero(self):
        result = _run("value-scenario", "validate", "does_not_exist_xyz.json")
        assert result.returncode != 0

    def test_missing_file_prints_error(self):
        result = _run("value-scenario", "validate", "does_not_exist_xyz.json")
        assert "file not found" in result.stdout

    def test_missing_file_no_stack_trace(self):
        result = _run("value-scenario", "validate", "does_not_exist_xyz.json")
        assert "Traceback" not in result.stdout
        assert "Traceback" not in result.stderr


# ---------------------------------------------------------------------------
# Directory path
# ---------------------------------------------------------------------------


class TestDirectoryPath:
    def test_directory_exits_nonzero(self):
        result = _run("value-scenario", "validate", "examples/value_scenarios")
        assert result.returncode != 0

    def test_directory_prints_error(self):
        result = _run("value-scenario", "validate", "examples/value_scenarios")
        assert "expected a JSON file path" in result.stdout

    def test_directory_no_stack_trace(self):
        result = _run("value-scenario", "validate", "examples/value_scenarios")
        assert "Traceback" not in result.stdout


# ---------------------------------------------------------------------------
# Schema-invalid scenario
# ---------------------------------------------------------------------------


class TestSchemaInvalid:
    def _invalid_fixture(self, overrides: dict) -> Path:
        data = json.loads(HOLDING_FIXTURE.read_text(encoding="utf-8"))
        data.update(overrides)
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(data, f)
            return Path(f.name)

    def test_missing_review_id_exits_nonzero(self):
        path = self._invalid_fixture({"scenario_review_id": ""})
        result = _run("value-scenario", "validate", str(path))
        assert result.returncode != 0

    def test_missing_review_id_prints_error(self):
        path = self._invalid_fixture({"scenario_review_id": ""})
        result = _run("value-scenario", "validate", str(path))
        assert "failed" in result.stdout.lower()

    def test_invalid_review_type_exits_nonzero(self):
        path = self._invalid_fixture({"review_type": "not_a_valid_type"})
        result = _run("value-scenario", "validate", str(path))
        assert result.returncode != 0

    def test_invalid_review_type_prints_field_error(self):
        path = self._invalid_fixture({"review_type": "not_a_valid_type"})
        result = _run("value-scenario", "validate", str(path))
        assert "review_type" in result.stdout or "failed" in result.stdout.lower()

    def test_schema_error_no_stack_trace(self):
        path = self._invalid_fixture({"scenario_review_id": ""})
        result = _run("value-scenario", "validate", str(path))
        assert "Traceback" not in result.stdout
        assert "Traceback" not in result.stderr


# ---------------------------------------------------------------------------
# Single-point range rejected
# ---------------------------------------------------------------------------


class TestSinglePointRangeRejected:
    def test_single_point_range_exits_nonzero(self):
        data = json.loads(HOLDING_FIXTURE.read_text(encoding="utf-8"))
        data["holding_scenarios"][0]["ranges"][0]["lower_percent"] = 10.0
        data["holding_scenarios"][0]["ranges"][0]["upper_percent"] = 10.0
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(data, f)
            path = Path(f.name)
        result = _run("value-scenario", "validate", str(path))
        assert result.returncode != 0

    def test_single_point_range_prints_error(self):
        data = json.loads(HOLDING_FIXTURE.read_text(encoding="utf-8"))
        data["holding_scenarios"][0]["ranges"][0]["lower_percent"] = 10.0
        data["holding_scenarios"][0]["ranges"][0]["upper_percent"] = 10.0
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(data, f)
            path = Path(f.name)
        result = _run("value-scenario", "validate", str(path))
        assert "failed" in result.stdout.lower()

    def test_single_point_range_no_stack_trace(self):
        data = json.loads(HOLDING_FIXTURE.read_text(encoding="utf-8"))
        data["holding_scenarios"][0]["ranges"][0]["lower_percent"] = 10.0
        data["holding_scenarios"][0]["ranges"][0]["upper_percent"] = 10.0
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(data, f)
            path = Path(f.name)
        result = _run("value-scenario", "validate", str(path))
        assert "Traceback" not in result.stdout
        assert "Traceback" not in result.stderr


# ---------------------------------------------------------------------------
# No modification / no output files
# ---------------------------------------------------------------------------


class TestNoModification:
    def test_holding_fixture_not_modified(self):
        before = HOLDING_FIXTURE.read_bytes()
        _run("value-scenario", "validate", str(HOLDING_FIXTURE))
        after = HOLDING_FIXTURE.read_bytes()
        assert before == after

    def test_portfolio_fixture_not_modified(self):
        before = PORTFOLIO_FIXTURE.read_bytes()
        _run("value-scenario", "validate", str(PORTFOLIO_FIXTURE))
        after = PORTFOLIO_FIXTURE.read_bytes()
        assert before == after

    def test_no_output_files_written(self):
        before = set(Path("examples/value_scenarios").iterdir())
        _run("value-scenario", "validate", str(HOLDING_FIXTURE))
        after = set(Path("examples/value_scenarios").iterdir())
        assert before == after

    def test_cwd_not_polluted(self):
        before = {f for f in Path(".").iterdir() if f.suffix == ".json"}
        _run("value-scenario", "validate", str(HOLDING_FIXTURE))
        after = {f for f in Path(".").iterdir() if f.suffix == ".json"}
        assert before == after


# ---------------------------------------------------------------------------
# Safe language in validator output
# ---------------------------------------------------------------------------


class TestSafeLanguage:
    def _output(self, fixture: Path) -> str:
        return _run("value-scenario", "validate", str(fixture)).stdout.lower()

    @pytest.mark.parametrize("phrase", PROHIBITED_PHRASES)
    def test_holding_output_no_prohibited_phrase(self, phrase: str):
        assert phrase.lower() not in self._output(HOLDING_FIXTURE), (
            f"Prohibited phrase {phrase!r} found in holding validator output"
        )

    @pytest.mark.parametrize("phrase", PROHIBITED_PHRASES)
    def test_portfolio_output_no_prohibited_phrase(self, phrase: str):
        assert phrase.lower() not in self._output(PORTFOLIO_FIXTURE), (
            f"Prohibited phrase {phrase!r} found in portfolio validator output"
        )


# ---------------------------------------------------------------------------
# Existing CLI commands unchanged
# ---------------------------------------------------------------------------


class TestExistingCliUnchanged:
    def test_weekly_review_help_still_works(self):
        result = _run("weekly-review", "--help")
        assert result.returncode == 0

    def test_temporary_workspace_validate_still_works(self):
        result = _run(
            "temporary-workspace", "validate",
            "examples/temporary_workspaces/portfolio_snapshot_workspace.json",
        )
        assert result.returncode == 0

    def test_snapshot_validate_still_works(self):
        result = _run("snapshot", "--help")
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# No provider / network / AI imports
# ---------------------------------------------------------------------------


class TestNoBoundaryViolations:
    def test_no_provider_imports_added(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        for forbidden in ["import openai", "import anthropic", "import langchain", "import httpx"]:
            assert forbidden not in src

    def test_value_scenario_schema_no_network(self):
        src = Path("atlas/value_scenario/schema.py").read_text(encoding="utf-8")
        for forbidden in ["requests", "httpx", "urllib.request", "socket"]:
            assert forbidden not in src

    def test_value_scenario_schema_no_ai(self):
        src = Path("atlas/value_scenario/schema.py").read_text(encoding="utf-8")
        for forbidden in ["openai", "anthropic", "langchain"]:
            assert forbidden not in src

    def test_validate_command_uses_local_import(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        assert "from atlas.value_scenario import ValueScenarioReview" in src

    def test_no_calculation_code_in_validate_command(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        for forbidden in ["numpy", "scipy", "pandas", "math.log", "statistics.mean"]:
            assert forbidden not in src
