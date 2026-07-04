"""Sprint 229 — Snapshot Draft confirm CLI tests.

Tests cover: command availability, confirmation of draft/needs_user_review/confirmed
states, blocking of rejected/superseded, error cases, file mutation safety,
output draft validation chain, language guardrails, and provider/network boundary.
"""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.snapshot_input.confirm import SnapshotConfirmResult, confirm_snapshot_draft
from atlas.snapshot_input.render import (
    render_snapshot_confirm_blocked,
    render_snapshot_confirm_error,
    render_snapshot_confirm_success,
)
from atlas.snapshot_input.schema import (
    SnapshotConfidence,
    SnapshotConfirmationStatus,
    SnapshotDraft,
    SnapshotType,
)

runner = CliRunner()

RESEARCH_NOTES_DRAFT = Path(
    "examples/snapshot_drafts/research_notes_snapshot.json"
)
CONFIRMED_DRAFT = Path(
    "examples/snapshot_drafts/research_notes_snapshot_confirmed.json"
)

FORBIDDEN_LANGUAGE = [
    "Strong Buy",
    "Strong Sell",
    "Price Target",
    "Target Price",
    "Act Now",
    "Must Buy",
    "Must Sell",
    "Guaranteed",
    "Will Outperform",
    "Financial Advice",
]


def _make_draft(**kwargs) -> SnapshotDraft:
    defaults = dict(
        draft_id="draft-229",
        snapshot_type=SnapshotType.RESEARCH_NOTES_SNAPSHOT,
        source_description="Sprint 229 test notes",
        extracted_fields={
            "ticker": "ASML",
            "title": "ASML notes",
            "evidence_gaps": ["Gap 1."],
            "open_questions": ["Q1?"],
            "risks_to_monitor": ["Risk 1."],
            "reasons_to_wait": ["Reason 1."],
        },
        uncertainties=[],
        missing_required_fields=[],
        confirmation_status=SnapshotConfirmationStatus.DRAFT,
        target_local_file="research_notes/ASML/notes.md",
        created_at="2026-01-10",
    )
    defaults.update(kwargs)
    return SnapshotDraft(**defaults)


def _write_draft(path: Path, draft: SnapshotDraft) -> None:
    path.write_text(draft.to_json(), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI availability
# ---------------------------------------------------------------------------

def test_snapshot_confirm_help_available():
    result = runner.invoke(app, ["snapshot", "confirm", "--help"])
    assert result.exit_code == 0


def test_snapshot_confirm_in_snapshot_group():
    result = runner.invoke(app, ["snapshot", "--help"])
    assert result.exit_code == 0
    assert "confirm" in result.output.lower()


def test_snapshot_confirm_help_no_forbidden_language():
    result = runner.invoke(app, ["snapshot", "confirm", "--help"])
    for term in FORBIDDEN_LANGUAGE:
        assert term not in result.output


# ---------------------------------------------------------------------------
# Draft state → confirmed
# ---------------------------------------------------------------------------

def test_draft_status_can_be_confirmed(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.DRAFT)
    src = tmp_path / "draft.json"
    out = tmp_path / "confirmed.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert result.exit_code == 0
    assert "Status: confirmed" in result.output


def test_needs_user_review_can_be_confirmed(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.NEEDS_USER_REVIEW)
    src = tmp_path / "draft.json"
    out = tmp_path / "confirmed.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert result.exit_code == 0
    assert "Status: confirmed" in result.output


def test_already_confirmed_writes_copy_with_note(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.CONFIRMED)
    src = tmp_path / "confirmed_in.json"
    out = tmp_path / "confirmed_out.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert result.exit_code == 0
    assert "Status: confirmed" in result.output
    assert "already confirmed" in result.output.lower()


def test_confirmed_copy_has_confirmed_status(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.DRAFT)
    src = tmp_path / "draft.json"
    out = tmp_path / "confirmed.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    loaded = SnapshotDraft.from_json(out.read_text(encoding="utf-8"))
    assert loaded.confirmation_status == SnapshotConfirmationStatus.CONFIRMED


# ---------------------------------------------------------------------------
# Blocked states
# ---------------------------------------------------------------------------

def test_rejected_is_blocked(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.REJECTED)
    src = tmp_path / "rejected.json"
    out = tmp_path / "out.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert result.exit_code != 0
    assert "Status: blocked" in result.output


def test_superseded_is_blocked(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.SUPERSEDED)
    src = tmp_path / "superseded.json"
    out = tmp_path / "out.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert result.exit_code != 0
    assert "Status: blocked" in result.output


def test_unknown_snapshot_type_is_blocked(tmp_path):
    draft = _make_draft(
        snapshot_type=SnapshotType.UNKNOWN_SNAPSHOT,
        target_local_file="unknown.json",
    )
    src = tmp_path / "unknown.json"
    out = tmp_path / "out.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert result.exit_code != 0
    assert "Status: blocked" in result.output


def test_empty_extracted_fields_is_blocked(tmp_path):
    draft = _make_draft(
        snapshot_type=SnapshotType.PORTFOLIO_SNAPSHOT,
        extracted_fields={},
        target_local_file="portfolio.json",
    )
    src = tmp_path / "draft.json"
    out = tmp_path / "out.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert result.exit_code != 0
    assert "Status: blocked" in result.output


def test_missing_ticker_is_blocked(tmp_path):
    draft = _make_draft(
        extracted_fields={"evidence_gaps": ["Gap."]},
        related_tickers=[],
    )
    src = tmp_path / "draft.json"
    out = tmp_path / "out.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert result.exit_code != 0
    assert "Status: blocked" in result.output


def test_unsafe_ticker_is_blocked(tmp_path):
    draft = _make_draft(extracted_fields={"ticker": "AS/ML"})
    src = tmp_path / "draft.json"
    out = tmp_path / "out.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert result.exit_code != 0
    assert "Status: blocked" in result.output


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_missing_file_exits_nonzero(tmp_path):
    out = tmp_path / "out.json"
    result = runner.invoke(app, ["snapshot", "confirm", "nonexistent.json", "--output-draft", str(out)])
    assert result.exit_code != 0


def test_missing_file_status_invalid(tmp_path):
    out = tmp_path / "out.json"
    result = runner.invoke(app, ["snapshot", "confirm", "nonexistent.json", "--output-draft", str(out)])
    assert "Status: invalid" in result.output


def test_invalid_json_exits_nonzero(tmp_path):
    src = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    src.write_text("not json", encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert result.exit_code != 0


def test_invalid_json_status_invalid(tmp_path):
    src = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    src.write_text("{invalid", encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert "Status: invalid" in result.output


def test_invalid_schema_exits_nonzero(tmp_path):
    src = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    src.write_text(json.dumps({"snapshot_type": "not_valid_type", "draft_id": "x",
                               "source_description": "s", "extracted_fields": {},
                               "uncertainties": [], "missing_required_fields": [],
                               "confirmation_status": "draft",
                               "target_local_file": "f.json", "created_at": "2026-01-01"}),
                   encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert result.exit_code != 0


def test_invalid_schema_status_invalid(tmp_path):
    src = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    src.write_text(json.dumps({"snapshot_type": "not_valid_type", "draft_id": "x",
                               "source_description": "s", "extracted_fields": {},
                               "uncertainties": [], "missing_required_fields": [],
                               "confirmation_status": "draft",
                               "target_local_file": "f.json", "created_at": "2026-01-01"}),
                   encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert "Status: invalid" in result.output


# ---------------------------------------------------------------------------
# Output collision
# ---------------------------------------------------------------------------

def test_output_collision_blocked_by_default(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out = tmp_path / "out.json"
    _write_draft(src, draft)
    out.write_text("existing content", encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert result.exit_code != 0
    assert out.read_text(encoding="utf-8") == "existing content"


def test_overwrite_replaces_output(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out = tmp_path / "out.json"
    _write_draft(src, draft)
    out.write_text("existing content", encoding="utf-8")
    result = runner.invoke(
        app, ["snapshot", "confirm", str(src), "--output-draft", str(out), "--overwrite"]
    )
    assert result.exit_code == 0
    assert out.read_text(encoding="utf-8") != "existing content"


# ---------------------------------------------------------------------------
# In-place guard
# ---------------------------------------------------------------------------

def test_output_path_equal_input_path_is_blocked(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(src)])
    assert result.exit_code != 0
    assert "Status: blocked" in result.output


def test_in_place_guard_preserves_original(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    _write_draft(src, draft)
    original_content = src.read_text(encoding="utf-8")
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(src)])
    assert src.read_text(encoding="utf-8") == original_content


# ---------------------------------------------------------------------------
# File mutation safety
# ---------------------------------------------------------------------------

def test_input_draft_not_modified(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out = tmp_path / "confirmed.json"
    _write_draft(src, draft)
    content_before = src.read_text(encoding="utf-8")
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert src.read_text(encoding="utf-8") == content_before


def test_input_draft_status_not_changed_in_file(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.DRAFT)
    src = tmp_path / "draft.json"
    out = tmp_path / "confirmed.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    reloaded = SnapshotDraft.from_json(src.read_text(encoding="utf-8"))
    assert reloaded.confirmation_status == SnapshotConfirmationStatus.DRAFT


def test_no_extra_files_created(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out = tmp_path / "confirmed.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    names = {p.name for p in tmp_path.iterdir()}
    assert names == {"draft.json", "confirmed.json"}


def test_no_atlas_local_files_written(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out = tmp_path / "confirmed.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    for forbidden in ["portfolio.json", "watchlist.json", "decision_journal.json"]:
        assert not (tmp_path / forbidden).exists()


# ---------------------------------------------------------------------------
# Output draft preservation
# ---------------------------------------------------------------------------

def test_confirmed_copy_preserves_draft_id(tmp_path):
    draft = _make_draft(draft_id="draft-preserve-test")
    src = tmp_path / "d.json"
    out = tmp_path / "c.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    loaded = SnapshotDraft.from_json(out.read_text(encoding="utf-8"))
    assert loaded.draft_id == "draft-preserve-test"


def test_confirmed_copy_preserves_extracted_fields(tmp_path):
    draft = _make_draft()
    src = tmp_path / "d.json"
    out = tmp_path / "c.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    loaded = SnapshotDraft.from_json(out.read_text(encoding="utf-8"))
    assert loaded.extracted_fields == draft.extracted_fields


def test_confirmed_copy_preserves_uncertainties(tmp_path):
    draft = _make_draft(uncertainties=["Something unclear."])
    src = tmp_path / "d.json"
    out = tmp_path / "c.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    loaded = SnapshotDraft.from_json(out.read_text(encoding="utf-8"))
    assert loaded.uncertainties == ["Something unclear."]


def test_confirmed_copy_preserves_missing_required_fields(tmp_path):
    draft = _make_draft(missing_required_fields=["cost_basis"])
    src = tmp_path / "d.json"
    out = tmp_path / "c.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    loaded = SnapshotDraft.from_json(out.read_text(encoding="utf-8"))
    assert loaded.missing_required_fields == ["cost_basis"]


def test_confirmed_copy_preserves_source_description(tmp_path):
    draft = _make_draft(source_description="My hand-written notes.")
    src = tmp_path / "d.json"
    out = tmp_path / "c.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    loaded = SnapshotDraft.from_json(out.read_text(encoding="utf-8"))
    assert loaded.source_description == "My hand-written notes."


def test_confirmed_copy_preserves_created_at(tmp_path):
    draft = _make_draft(created_at="2026-02-15")
    src = tmp_path / "d.json"
    out = tmp_path / "c.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    loaded = SnapshotDraft.from_json(out.read_text(encoding="utf-8"))
    assert loaded.created_at == "2026-02-15"


def test_confirmed_copy_preserves_target_local_file(tmp_path):
    draft = _make_draft(target_local_file="research_notes/ASML/notes.md")
    src = tmp_path / "d.json"
    out = tmp_path / "c.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    loaded = SnapshotDraft.from_json(out.read_text(encoding="utf-8"))
    assert loaded.target_local_file == "research_notes/ASML/notes.md"


# ---------------------------------------------------------------------------
# Validation / review chain
# ---------------------------------------------------------------------------

def test_confirmed_copy_passes_validate(tmp_path):
    draft = _make_draft()
    src = tmp_path / "d.json"
    out = tmp_path / "confirmed.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    result = runner.invoke(app, ["snapshot", "validate", str(out)])
    assert result.exit_code == 0
    assert "Status: valid" in result.output


def test_confirmed_copy_reviews_as_exportable(tmp_path):
    draft = _make_draft()
    src = tmp_path / "d.json"
    out = tmp_path / "confirmed.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    result = runner.invoke(app, ["snapshot", "review", str(out)])
    assert result.exit_code == 0
    assert "Exportable: yes" in result.output
    assert "Confirmation Status: confirmed" in result.output


def test_export_research_notes_works_on_confirmed_copy(tmp_path):
    draft = _make_draft()
    src = tmp_path / "d.json"
    out = tmp_path / "confirmed.json"
    export_dir = tmp_path / "notes_export"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    result = runner.invoke(
        app,
        ["snapshot", "export-research-notes", str(out), "--output-dir", str(export_dir)],
    )
    assert result.exit_code == 0
    assert "Status: written" in result.output


def test_export_research_notes_on_confirmed_copy_writes_file(tmp_path):
    draft = _make_draft()
    src = tmp_path / "d.json"
    out = tmp_path / "confirmed.json"
    export_dir = tmp_path / "notes_export"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    runner.invoke(
        app,
        ["snapshot", "export-research-notes", str(out), "--output-dir", str(export_dir)],
    )
    notes_file = export_dir / "ASML" / "notes.md"
    assert notes_file.exists()


# ---------------------------------------------------------------------------
# Safety boundary in output
# ---------------------------------------------------------------------------

def test_success_output_includes_safety_boundary(tmp_path):
    draft = _make_draft()
    src = tmp_path / "d.json"
    out = tmp_path / "c.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert "Safety Boundary" in result.output
    assert "Original draft was not modified" in result.output
    assert "No Atlas local input files were changed" in result.output
    assert "Export commands must still be run separately" in result.output


def test_blocked_output_is_clear(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.REJECTED)
    src = tmp_path / "rejected.json"
    out = tmp_path / "out.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    assert "Status: blocked" in result.output
    assert "Reason:" in result.output


# ---------------------------------------------------------------------------
# Language guardrails
# ---------------------------------------------------------------------------

def test_success_render_no_forbidden_language():
    output = render_snapshot_confirm_success(
        input_path="in.json",
        output_path="out.json",
        snapshot_type="research_notes_snapshot",
        already_confirmed=False,
    )
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output


def test_blocked_render_no_forbidden_language():
    output = render_snapshot_confirm_blocked("Draft is rejected.")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output


def test_error_render_no_forbidden_language():
    output = render_snapshot_confirm_error("file not found: x.json")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output


def test_cli_output_no_forbidden_language(tmp_path):
    draft = _make_draft()
    src = tmp_path / "d.json"
    out = tmp_path / "c.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "confirm", str(src), "--output-draft", str(out)])
    for term in FORBIDDEN_LANGUAGE:
        assert term not in result.output


# ---------------------------------------------------------------------------
# Provider / network boundary
# ---------------------------------------------------------------------------

def test_no_provider_imports_in_confirm_module():
    import atlas.snapshot_input.confirm as mod
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
                assert "providers" not in name
                assert "requests" not in name
                assert "urllib" not in name
                assert "httpx" not in name


# ---------------------------------------------------------------------------
# Unit-level confirm_snapshot_draft
# ---------------------------------------------------------------------------

def test_confirm_draft_returns_success(tmp_path):
    draft = _make_draft()
    out = tmp_path / "c.json"
    result = confirm_snapshot_draft(draft, out)
    assert isinstance(result, SnapshotConfirmResult)
    assert result.success is True
    assert result.output_path == out
    assert result.already_confirmed is False


def test_confirm_draft_already_confirmed_flag(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.CONFIRMED)
    out = tmp_path / "c.json"
    result = confirm_snapshot_draft(draft, out)
    assert result.success is True
    assert result.already_confirmed is True


def test_confirm_rejected_returns_failure(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.REJECTED)
    out = tmp_path / "c.json"
    result = confirm_snapshot_draft(draft, out)
    assert result.success is False
    assert "rejected" in result.reason.lower()


def test_confirm_collision_no_overwrite_returns_failure(tmp_path):
    draft = _make_draft()
    out = tmp_path / "c.json"
    out.write_text("existing", encoding="utf-8")
    result = confirm_snapshot_draft(draft, out, overwrite=False)
    assert result.success is False
    assert "already exists" in result.reason.lower() or "overwrite" in result.reason.lower()


def test_confirm_collision_with_overwrite_succeeds(tmp_path):
    draft = _make_draft()
    out = tmp_path / "c.json"
    out.write_text("existing", encoding="utf-8")
    result = confirm_snapshot_draft(draft, out, overwrite=True)
    assert result.success is True


# ---------------------------------------------------------------------------
# Regression — other commands still work
# ---------------------------------------------------------------------------

def test_snapshot_validate_still_works():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(app, ["snapshot", "validate", str(CONFIRMED_DRAFT)])
    assert result.exit_code == 0


def test_snapshot_review_still_works():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(CONFIRMED_DRAFT)])
    assert result.exit_code == 0


def test_export_research_notes_still_works(tmp_path):
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(
        app,
        ["snapshot", "export-research-notes", str(CONFIRMED_DRAFT), "--output-dir", str(tmp_path)],
    )
    assert result.exit_code == 0
