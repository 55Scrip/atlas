"""Sprint 273 — Temporary workspace read-only validation CLI tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLE_DIR = Path("examples/temporary_workspaces")
PORTFOLIO_FIXTURE = EXAMPLE_DIR / "portfolio_snapshot_workspace.json"
WATCHLIST_FIXTURE = EXAMPLE_DIR / "watchlist_research_workspace.json"
ORDER_FIXTURE = EXAMPLE_DIR / "order_idea_workspace.json"
CLI_FILE = Path("atlas/cli/main.py")

ATLAS_BIN = Path(".venv/bin/atlas")


def run_validate(path: str | Path, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    cmd = [str(ATLAS_BIN), "temporary-workspace", "validate", str(path)]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True)


# ---------------------------------------------------------------------------
# CLI structure
# ---------------------------------------------------------------------------


class TestCLIStructure:
    def test_temporary_workspace_app_defined(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        assert "temporary_workspace_app = typer.Typer(" in src

    def test_temporary_workspace_app_registered(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        assert 'app.add_typer(temporary_workspace_app, name="temporary-workspace")' in src

    def test_validate_command_defined(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        assert '@temporary_workspace_app.command("validate")' in src

    def test_validate_command_uses_from_json(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        assert "TemporaryWorkspace.from_json(" in src

    def test_validate_command_no_language_option(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        # The temporary-workspace validate command should not have a --language option
        # Find the validate function for temporary_workspace_app specifically
        start = src.index('@temporary_workspace_app.command("validate")')
        # Find next command decorator or end of function
        next_decorator = src.find("\n@", start + 1)
        func_src = src[start:next_decorator] if next_decorator != -1 else src[start:]
        assert "--language" not in func_src

    def test_validate_command_is_read_only(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        start = src.index('@temporary_workspace_app.command("validate")')
        next_decorator = src.find("\n@", start + 1)
        func_src = src[start:next_decorator] if next_decorator != -1 else src[start:]
        assert "write_text" not in func_src
        assert "open(" not in func_src

    def test_validate_command_exits_1_on_file_not_found(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        start = src.index('@temporary_workspace_app.command("validate")')
        next_decorator = src.find("\n@", start + 1)
        func_src = src[start:next_decorator] if next_decorator != -1 else src[start:]
        assert "Exit(code=1)" in func_src

    def test_imports_temporary_workspace(self):
        src = CLI_FILE.read_text(encoding="utf-8")
        assert "from atlas.temporary_workspace import TemporaryWorkspace" in src


# ---------------------------------------------------------------------------
# Success cases — portfolio fixture
# ---------------------------------------------------------------------------


class TestPortfolioFixtureSuccess:
    def test_exit_code_zero(self):
        result = run_validate(PORTFOLIO_FIXTURE)
        assert result.returncode == 0

    def test_prints_valid_message(self):
        result = run_validate(PORTFOLIO_FIXTURE)
        assert "Temporary workspace is valid." in result.stdout

    def test_prints_workspace_id(self):
        result = run_validate(PORTFOLIO_FIXTURE)
        assert "Workspace ID: tmp_ws_portfolio_snapshot_001" in result.stdout

    def test_prints_status(self):
        result = run_validate(PORTFOLIO_FIXTURE)
        assert "Status: temporary" in result.stdout

    def test_prints_card_count(self):
        result = run_validate(PORTFOLIO_FIXTURE)
        assert "Cards: 7" in result.stdout

    def test_prints_entity_count(self):
        result = run_validate(PORTFOLIO_FIXTURE)
        assert "Detected entities: 3" in result.stdout

    def test_prints_uncertainty_count(self):
        result = run_validate(PORTFOLIO_FIXTURE)
        assert "Uncertainties: 1" in result.stdout

    def test_prints_missing_fields_count(self):
        result = run_validate(PORTFOLIO_FIXTURE)
        assert "Missing fields: 4" in result.stdout

    def test_no_stderr_output(self):
        result = run_validate(PORTFOLIO_FIXTURE)
        assert result.stderr == ""


# ---------------------------------------------------------------------------
# Success cases — watchlist fixture
# ---------------------------------------------------------------------------


class TestWatchlistFixtureSuccess:
    def test_exit_code_zero(self):
        result = run_validate(WATCHLIST_FIXTURE)
        assert result.returncode == 0

    def test_prints_valid_message(self):
        result = run_validate(WATCHLIST_FIXTURE)
        assert "Temporary workspace is valid." in result.stdout

    def test_prints_workspace_id(self):
        result = run_validate(WATCHLIST_FIXTURE)
        assert "Workspace ID: tmp_ws_watchlist_research_001" in result.stdout

    def test_prints_status(self):
        result = run_validate(WATCHLIST_FIXTURE)
        assert "Status: temporary" in result.stdout

    def test_prints_card_count(self):
        result = run_validate(WATCHLIST_FIXTURE)
        assert "Cards: 7" in result.stdout

    def test_prints_entity_count(self):
        result = run_validate(WATCHLIST_FIXTURE)
        assert "Detected entities: 2" in result.stdout

    def test_prints_uncertainty_count(self):
        result = run_validate(WATCHLIST_FIXTURE)
        assert "Uncertainties: 1" in result.stdout

    def test_prints_missing_fields_count(self):
        result = run_validate(WATCHLIST_FIXTURE)
        assert "Missing fields: 1" in result.stdout


# ---------------------------------------------------------------------------
# Success cases — order idea fixture
# ---------------------------------------------------------------------------


class TestOrderIdeaFixtureSuccess:
    def test_exit_code_zero(self):
        result = run_validate(ORDER_FIXTURE)
        assert result.returncode == 0

    def test_prints_valid_message(self):
        result = run_validate(ORDER_FIXTURE)
        assert "Temporary workspace is valid." in result.stdout

    def test_prints_workspace_id(self):
        result = run_validate(ORDER_FIXTURE)
        assert "Workspace ID: tmp_ws_order_idea_001" in result.stdout

    def test_prints_card_count(self):
        result = run_validate(ORDER_FIXTURE)
        assert "Cards: 6" in result.stdout

    def test_prints_entity_count(self):
        result = run_validate(ORDER_FIXTURE)
        assert "Detected entities: 2" in result.stdout

    def test_prints_uncertainty_count(self):
        result = run_validate(ORDER_FIXTURE)
        assert "Uncertainties: 1" in result.stdout

    def test_prints_missing_fields_count(self):
        result = run_validate(ORDER_FIXTURE)
        assert "Missing fields: 2" in result.stdout


# ---------------------------------------------------------------------------
# Error cases — file not found
# ---------------------------------------------------------------------------


class TestFileNotFound:
    def test_exit_code_nonzero(self, tmp_path):
        result = run_validate(tmp_path / "nonexistent.json")
        assert result.returncode != 0

    def test_exit_code_is_1(self, tmp_path):
        result = run_validate(tmp_path / "nonexistent.json")
        assert result.returncode == 1

    def test_prints_error_message(self, tmp_path):
        result = run_validate(tmp_path / "nonexistent.json")
        output = result.stdout + result.stderr
        assert "validation failed" in output.lower() or "not found" in output.lower()

    def test_does_not_print_valid_message(self, tmp_path):
        result = run_validate(tmp_path / "nonexistent.json")
        assert "Temporary workspace is valid." not in result.stdout


# ---------------------------------------------------------------------------
# Error cases — directory path
# ---------------------------------------------------------------------------


class TestDirectoryPath:
    def test_exit_code_nonzero(self):
        result = run_validate(EXAMPLE_DIR)
        assert result.returncode != 0

    def test_exit_code_is_1(self):
        result = run_validate(EXAMPLE_DIR)
        assert result.returncode == 1

    def test_prints_directory_error(self):
        result = run_validate(EXAMPLE_DIR)
        output = result.stdout + result.stderr
        assert "directory" in output.lower()

    def test_does_not_print_valid_message(self):
        result = run_validate(EXAMPLE_DIR)
        assert "Temporary workspace is valid." not in result.stdout


# ---------------------------------------------------------------------------
# Error cases — invalid JSON
# ---------------------------------------------------------------------------


class TestInvalidJson:
    def test_exit_code_is_1(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("this is not json", encoding="utf-8")
        result = run_validate(bad)
        assert result.returncode == 1

    def test_prints_error_message(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("this is not json", encoding="utf-8")
        result = run_validate(bad)
        output = result.stdout + result.stderr
        assert "validation failed" in output.lower()

    def test_does_not_print_valid_message(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("this is not json", encoding="utf-8")
        result = run_validate(bad)
        assert "Temporary workspace is valid." not in result.stdout


# ---------------------------------------------------------------------------
# Error cases — schema validation failure
# ---------------------------------------------------------------------------


class TestSchemaValidationFailure:
    def test_empty_workspace_id_fails(self, tmp_path):
        data = json.loads(PORTFOLIO_FIXTURE.read_text(encoding="utf-8"))
        data["workspace_id"] = ""
        bad = tmp_path / "bad_id.json"
        bad.write_text(json.dumps(data), encoding="utf-8")
        result = run_validate(bad)
        assert result.returncode == 1

    def test_missing_source_input_fails(self, tmp_path):
        data = json.loads(PORTFOLIO_FIXTURE.read_text(encoding="utf-8"))
        del data["source_input"]
        bad = tmp_path / "no_source.json"
        bad.write_text(json.dumps(data), encoding="utf-8")
        result = run_validate(bad)
        assert result.returncode == 1

    def test_invalid_status_fails(self, tmp_path):
        data = json.loads(PORTFOLIO_FIXTURE.read_text(encoding="utf-8"))
        data["status"] = "invalid_status_xyz"
        bad = tmp_path / "bad_status.json"
        bad.write_text(json.dumps(data), encoding="utf-8")
        result = run_validate(bad)
        assert result.returncode == 1

    def test_schema_failure_prints_error(self, tmp_path):
        data = json.loads(PORTFOLIO_FIXTURE.read_text(encoding="utf-8"))
        data["workspace_id"] = ""
        bad = tmp_path / "bad_id.json"
        bad.write_text(json.dumps(data), encoding="utf-8")
        result = run_validate(bad)
        output = result.stdout + result.stderr
        assert "validation failed" in output.lower()

    def test_schema_failure_no_valid_message(self, tmp_path):
        data = json.loads(PORTFOLIO_FIXTURE.read_text(encoding="utf-8"))
        data["workspace_id"] = ""
        bad = tmp_path / "bad_id.json"
        bad.write_text(json.dumps(data), encoding="utf-8")
        result = run_validate(bad)
        assert "Temporary workspace is valid." not in result.stdout


# ---------------------------------------------------------------------------
# Read-only guarantee
# ---------------------------------------------------------------------------


class TestReadOnly:
    def test_input_file_unmodified(self, tmp_path):
        original = PORTFOLIO_FIXTURE.read_text(encoding="utf-8")
        copy = tmp_path / "workspace.json"
        copy.write_text(original, encoding="utf-8")
        mtime_before = copy.stat().st_mtime
        run_validate(copy)
        mtime_after = copy.stat().st_mtime
        assert mtime_before == mtime_after

    def test_no_output_files_created(self, tmp_path):
        original = PORTFOLIO_FIXTURE.read_text(encoding="utf-8")
        copy = tmp_path / "workspace.json"
        copy.write_text(original, encoding="utf-8")
        files_before = set(tmp_path.iterdir())
        run_validate(copy)
        files_after = set(tmp_path.iterdir())
        assert files_before == files_after


# ---------------------------------------------------------------------------
# No recommendation language in output
# ---------------------------------------------------------------------------


PROHIBITED_PHRASES = [
    "strong buy",
    "price target",
    "target price",
    "buy now",
    "sell now",
    "guaranteed",
    "risk-free",
    "outperform",
    "entry point",
    "exit point",
]


class TestNoRecommendationLanguage:
    @pytest.mark.parametrize("fixture", [PORTFOLIO_FIXTURE, WATCHLIST_FIXTURE, ORDER_FIXTURE])
    @pytest.mark.parametrize("phrase", PROHIBITED_PHRASES)
    def test_no_prohibited_phrase_in_output(self, fixture, phrase):
        result = run_validate(fixture)
        assert phrase not in result.stdout.lower()
