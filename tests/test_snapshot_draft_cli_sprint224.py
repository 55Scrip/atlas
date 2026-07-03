"""Sprint 224 — Snapshot Draft CLI validation tests.

Tests cover: command availability, valid draft output, invalid JSON failure,
invalid schema failure, missing file failure, file mutation safety, safety
boundary line, language guardrails, and provider/network boundary.
"""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.snapshot_input.render import (
    render_snapshot_draft_validation,
    render_snapshot_draft_validation_error,
)
from atlas.snapshot_input.schema import (
    SnapshotConfidence,
    SnapshotConfirmationStatus,
    SnapshotDraft,
    SnapshotType,
)

runner = CliRunner()

EXAMPLES_DIR = Path("examples/snapshot_drafts")
PORTFOLIO_DRAFT = EXAMPLES_DIR / "portfolio_snapshot.json"
RESEARCH_DRAFT = EXAMPLES_DIR / "research_notes_snapshot.json"
NEWS_DRAFT = EXAMPLES_DIR / "news_snapshot.json"

FORBIDDEN_LANGUAGE = [
    "Strong Buy", "Strong Sell", "Price Target", "Target Price",
    "Act Now", "Must Buy", "Must Sell", "Guaranteed",
    "Will Outperform", "Financial Advice",
]


def _minimal_draft(**kwargs) -> SnapshotDraft:
    defaults = dict(
        draft_id="draft-test-001",
        snapshot_type=SnapshotType.PORTFOLIO_SNAPSHOT,
        source_description="Test source",
        extracted_fields={"key": "value"},
        uncertainties=[],
        missing_required_fields=[],
        confirmation_status=SnapshotConfirmationStatus.DRAFT,
        target_local_file="portfolio.json",
        created_at="2026-01-05",
    )
    defaults.update(kwargs)
    return SnapshotDraft(**defaults)


# ---------------------------------------------------------------------------
# CLI availability
# ---------------------------------------------------------------------------

def test_snapshot_group_is_registered():
    result = runner.invoke(app, ["snapshot", "--help"])
    assert result.exit_code == 0
    assert "validate" in result.output.lower()


def test_snapshot_validate_help():
    result = runner.invoke(app, ["snapshot", "validate", "--help"])
    assert result.exit_code == 0
    assert "validate" in result.output.lower()


def test_snapshot_validate_help_has_no_forbidden_language():
    result = runner.invoke(app, ["snapshot", "validate", "--help"])
    for term in FORBIDDEN_LANGUAGE:
        assert term not in result.output, f"Forbidden language in help: '{term}'"


# ---------------------------------------------------------------------------
# Valid draft — exit code
# ---------------------------------------------------------------------------

def test_valid_portfolio_draft_exits_zero():
    if not PORTFOLIO_DRAFT.exists():
        pytest.skip("portfolio_snapshot.json not found")
    result = runner.invoke(app, ["snapshot", "validate", str(PORTFOLIO_DRAFT)])
    assert result.exit_code == 0


def test_valid_research_draft_exits_zero():
    if not RESEARCH_DRAFT.exists():
        pytest.skip("research_notes_snapshot.json not found")
    result = runner.invoke(app, ["snapshot", "validate", str(RESEARCH_DRAFT)])
    assert result.exit_code == 0


def test_valid_news_draft_exits_zero():
    if not NEWS_DRAFT.exists():
        pytest.skip("news_snapshot.json not found")
    result = runner.invoke(app, ["snapshot", "validate", str(NEWS_DRAFT)])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Valid draft — output content
# ---------------------------------------------------------------------------

def test_valid_output_includes_status_valid():
    if not PORTFOLIO_DRAFT.exists():
        pytest.skip("portfolio_snapshot.json not found")
    result = runner.invoke(app, ["snapshot", "validate", str(PORTFOLIO_DRAFT)])
    assert "Status: valid" in result.output


def test_valid_output_includes_snapshot_type():
    if not PORTFOLIO_DRAFT.exists():
        pytest.skip("portfolio_snapshot.json not found")
    result = runner.invoke(app, ["snapshot", "validate", str(PORTFOLIO_DRAFT)])
    assert "portfolio_snapshot" in result.output


def test_valid_output_includes_confidence():
    if not PORTFOLIO_DRAFT.exists():
        pytest.skip("portfolio_snapshot.json not found")
    result = runner.invoke(app, ["snapshot", "validate", str(PORTFOLIO_DRAFT)])
    assert "Confidence:" in result.output


def test_valid_output_includes_confirmation_status():
    if not PORTFOLIO_DRAFT.exists():
        pytest.skip("portfolio_snapshot.json not found")
    result = runner.invoke(app, ["snapshot", "validate", str(PORTFOLIO_DRAFT)])
    assert "Confirmation Status:" in result.output


def test_valid_output_includes_target_local_file():
    if not PORTFOLIO_DRAFT.exists():
        pytest.skip("portfolio_snapshot.json not found")
    result = runner.invoke(app, ["snapshot", "validate", str(PORTFOLIO_DRAFT)])
    assert "Target Local File:" in result.output


def test_valid_output_includes_related_tickers():
    if not PORTFOLIO_DRAFT.exists():
        pytest.skip("portfolio_snapshot.json not found")
    result = runner.invoke(app, ["snapshot", "validate", str(PORTFOLIO_DRAFT)])
    assert "Related Tickers:" in result.output
    assert "ASML" in result.output


def test_valid_output_includes_uncertainties():
    if not PORTFOLIO_DRAFT.exists():
        pytest.skip("portfolio_snapshot.json not found")
    result = runner.invoke(app, ["snapshot", "validate", str(PORTFOLIO_DRAFT)])
    assert "Uncertainties:" in result.output


def test_valid_output_includes_missing_required_fields():
    if not PORTFOLIO_DRAFT.exists():
        pytest.skip("portfolio_snapshot.json not found")
    result = runner.invoke(app, ["snapshot", "validate", str(PORTFOLIO_DRAFT)])
    assert "Missing Required Fields:" in result.output


def test_valid_output_includes_safety_boundary():
    if not PORTFOLIO_DRAFT.exists():
        pytest.skip("portfolio_snapshot.json not found")
    result = runner.invoke(app, ["snapshot", "validate", str(PORTFOLIO_DRAFT)])
    assert "Safety Boundary" in result.output
    assert "does not write" in result.output


def test_valid_output_no_forbidden_language():
    if not PORTFOLIO_DRAFT.exists():
        pytest.skip("portfolio_snapshot.json not found")
    result = runner.invoke(app, ["snapshot", "validate", str(PORTFOLIO_DRAFT)])
    for term in FORBIDDEN_LANGUAGE:
        assert term not in result.output, f"Forbidden language in output: '{term}'"


def test_research_notes_draft_output_includes_type():
    if not RESEARCH_DRAFT.exists():
        pytest.skip("research_notes_snapshot.json not found")
    result = runner.invoke(app, ["snapshot", "validate", str(RESEARCH_DRAFT)])
    assert "research_notes_snapshot" in result.output


def test_no_uncertainties_shows_none():
    if not RESEARCH_DRAFT.exists():
        pytest.skip("research_notes_snapshot.json not found")
    result = runner.invoke(app, ["snapshot", "validate", str(RESEARCH_DRAFT)])
    # Research notes draft has empty uncertainties
    assert "Uncertainties: none" in result.output or "Uncertainties:" in result.output


# ---------------------------------------------------------------------------
# Invalid JSON
# ---------------------------------------------------------------------------

def test_invalid_json_exits_nonzero(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("this is not json {{{", encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "validate", str(bad)])
    assert result.exit_code != 0


def test_invalid_json_output_includes_status_invalid(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "validate", str(bad)])
    assert "Status: invalid" in result.output


def test_invalid_json_output_includes_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("[1, 2, 3]", encoding="utf-8")  # valid JSON but not object
    result = runner.invoke(app, ["snapshot", "validate", str(bad)])
    assert result.exit_code != 0
    assert "Status: invalid" in result.output


# ---------------------------------------------------------------------------
# Invalid schema
# ---------------------------------------------------------------------------

def test_invalid_schema_exits_nonzero(tmp_path):
    bad = tmp_path / "bad_schema.json"
    data = {"draft_id": "", "snapshot_type": "portfolio_snapshot",
            "source_description": "test", "extracted_fields": {},
            "uncertainties": [], "missing_required_fields": [],
            "confirmation_status": "draft",
            "target_local_file": "portfolio.json", "created_at": "2026-01-01"}
    bad.write_text(json.dumps(data), encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "validate", str(bad)])
    assert result.exit_code != 0


def test_invalid_schema_output_includes_status_invalid(tmp_path):
    bad = tmp_path / "bad_schema.json"
    data = {"draft_id": "ok", "snapshot_type": "not_a_valid_type",
            "source_description": "test", "extracted_fields": {},
            "uncertainties": [], "missing_required_fields": [],
            "confirmation_status": "draft",
            "target_local_file": "portfolio.json", "created_at": "2026-01-01"}
    bad.write_text(json.dumps(data), encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "validate", str(bad)])
    assert "Status: invalid" in result.output


# ---------------------------------------------------------------------------
# Missing file
# ---------------------------------------------------------------------------

def test_missing_file_exits_nonzero():
    result = runner.invoke(app, ["snapshot", "validate", "nonexistent_path/no.json"])
    assert result.exit_code != 0


def test_missing_file_output_includes_status_invalid():
    result = runner.invoke(app, ["snapshot", "validate", "nonexistent_path/no.json"])
    assert "Status: invalid" in result.output


def test_missing_file_output_includes_error_message():
    result = runner.invoke(app, ["snapshot", "validate", "nonexistent_path/no.json"])
    assert "Error:" in result.output


# ---------------------------------------------------------------------------
# File mutation safety
# ---------------------------------------------------------------------------

def test_validate_does_not_modify_draft_file(tmp_path):
    draft = _minimal_draft(
        uncertainties=["Test uncertainty"],
        related_tickers=["ASML"],
    )
    path = tmp_path / "draft.json"
    path.write_text(draft.to_json(), encoding="utf-8")
    content_before = path.read_text(encoding="utf-8")
    runner.invoke(app, ["snapshot", "validate", str(path)])
    content_after = path.read_text(encoding="utf-8")
    assert content_before == content_after


def test_validate_creates_no_new_files(tmp_path):
    draft = _minimal_draft()
    path = tmp_path / "draft.json"
    path.write_text(draft.to_json(), encoding="utf-8")
    files_before = set(tmp_path.iterdir())
    runner.invoke(app, ["snapshot", "validate", str(path)])
    files_after = set(tmp_path.iterdir())
    assert files_before == files_after


# ---------------------------------------------------------------------------
# render_snapshot_draft_validation (unit tests)
# ---------------------------------------------------------------------------

def test_render_includes_status_valid():
    draft = _minimal_draft()
    output = render_snapshot_draft_validation(draft)
    assert "Status: valid" in output


def test_render_includes_snapshot_type():
    draft = _minimal_draft(snapshot_type=SnapshotType.RESEARCH_NOTES_SNAPSHOT)
    output = render_snapshot_draft_validation(draft)
    assert "research_notes_snapshot" in output


def test_render_includes_confidence():
    draft = _minimal_draft(confidence=SnapshotConfidence.HIGH)
    output = render_snapshot_draft_validation(draft)
    assert "Confidence: high" in output


def test_render_includes_confirmation_status():
    draft = _minimal_draft(confirmation_status=SnapshotConfirmationStatus.NEEDS_USER_REVIEW)
    output = render_snapshot_draft_validation(draft)
    assert "Confirmation Status: needs_user_review" in output


def test_render_includes_target_local_file():
    draft = _minimal_draft(target_local_file="my_review/watchlist.json")
    output = render_snapshot_draft_validation(draft)
    assert "my_review/watchlist.json" in output


def test_render_includes_related_tickers():
    draft = _minimal_draft(related_tickers=["ASML", "XYL"])
    output = render_snapshot_draft_validation(draft)
    assert "ASML" in output
    assert "XYL" in output


def test_render_includes_uncertainties():
    draft = _minimal_draft(uncertainties=["Currency unclear", "Sector inferred"])
    output = render_snapshot_draft_validation(draft)
    assert "Currency unclear" in output
    assert "Sector inferred" in output


def test_render_shows_none_for_empty_uncertainties():
    draft = _minimal_draft(uncertainties=[])
    output = render_snapshot_draft_validation(draft)
    assert "Uncertainties: none" in output


def test_render_includes_missing_required_fields():
    draft = _minimal_draft(missing_required_fields=["cost_basis", "sector"])
    output = render_snapshot_draft_validation(draft)
    assert "cost_basis" in output
    assert "sector" in output


def test_render_includes_safety_boundary():
    draft = _minimal_draft()
    output = render_snapshot_draft_validation(draft)
    assert "Safety Boundary" in output
    assert "does not write" in output


def test_render_error_includes_status_invalid():
    output = render_snapshot_draft_validation_error("draft_id must be non-empty.")
    assert "Status: invalid" in output
    assert "draft_id" in output


def test_render_is_deterministic():
    draft = _minimal_draft(uncertainties=["u1", "u2"], related_tickers=["ASML"])
    assert render_snapshot_draft_validation(draft) == render_snapshot_draft_validation(draft)


def test_render_no_forbidden_language():
    draft = _minimal_draft(
        uncertainties=["Currency unclear"],
        missing_required_fields=["sector"],
    )
    output = render_snapshot_draft_validation(draft)
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output, f"Forbidden language in render output: '{term}'"


# ---------------------------------------------------------------------------
# Provider / network boundary
# ---------------------------------------------------------------------------

def test_no_provider_imports_in_render_module():
    import atlas.snapshot_input.render as mod
    source = inspect.getsource(mod)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            for alias in node.names:
                names.append(alias.name)
            for name in names:
                assert "providers" not in name, f"Provider import in render.py: {name}"
                assert "requests" not in name, f"Network import: {name}"
                assert "urllib" not in name, f"Network import: {name}"


# ---------------------------------------------------------------------------
# Weekly Review regression check
# ---------------------------------------------------------------------------

def test_weekly_review_command_still_available():
    result = runner.invoke(app, ["weekly-review", "--help"])
    assert result.exit_code == 0
    assert "weekly-review" in result.output or "Weekly" in result.output


def test_snapshot_command_does_not_break_weekly_review(tmp_path):
    result = runner.invoke(app, ["snapshot", "validate", "nonexistent.json"])
    assert result.exit_code != 0
    # Confirm weekly-review still loads
    wr_result = runner.invoke(app, ["weekly-review", "--help"])
    assert wr_result.exit_code == 0
