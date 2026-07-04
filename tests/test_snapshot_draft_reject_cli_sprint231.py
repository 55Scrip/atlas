"""Sprint 231 — Snapshot Draft reject CLI tests.

Tests cover: command availability, rejection of all non-superseded states,
blocking of superseded, error cases, file mutation safety, output draft
validation/review chain, export-research-notes blocking, language guardrails,
and provider/network boundary.
"""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.snapshot_input.reject import SnapshotRejectResult, reject_snapshot_draft
from atlas.snapshot_input.render import (
    render_snapshot_reject_blocked,
    render_snapshot_reject_error,
    render_snapshot_reject_success,
)
from atlas.snapshot_input.schema import (
    SnapshotConfirmationStatus,
    SnapshotDraft,
    SnapshotType,
)

runner = CliRunner()

RESEARCH_NOTES_DRAFT = Path("examples/snapshot_drafts/research_notes_snapshot.json")
CONFIRMED_DRAFT = Path("examples/snapshot_drafts/research_notes_snapshot_confirmed.json")

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
        draft_id="draft-231",
        snapshot_type=SnapshotType.RESEARCH_NOTES_SNAPSHOT,
        source_description="Sprint 231 test notes",
        extracted_fields={
            "ticker": "ASML",
            "title": "ASML notes",
            "evidence_gaps": ["Gap 1."],
            "open_questions": ["Q1?"],
            "risks_to_monitor": ["Risk 1."],
        },
        uncertainties=[],
        missing_required_fields=[],
        confirmation_status=SnapshotConfirmationStatus.DRAFT,
        target_local_file="research_notes/ASML/notes.md",
        created_at="2026-01-15",
    )
    defaults.update(kwargs)
    return SnapshotDraft(**defaults)


def _write_draft(path: Path, draft: SnapshotDraft) -> None:
    path.write_text(draft.to_json(), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI availability
# ---------------------------------------------------------------------------

def test_snapshot_reject_help_available():
    result = runner.invoke(app, ["snapshot", "reject", "--help"])
    assert result.exit_code == 0


def test_snapshot_reject_in_snapshot_group():
    result = runner.invoke(app, ["snapshot", "--help"])
    assert result.exit_code == 0
    assert "reject" in result.output.lower()


def test_snapshot_reject_help_no_forbidden_language():
    result = runner.invoke(app, ["snapshot", "reject", "--help"])
    for term in FORBIDDEN_LANGUAGE:
        assert term not in result.output


# ---------------------------------------------------------------------------
# Draft states that can be rejected
# ---------------------------------------------------------------------------

def test_draft_status_can_be_rejected(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.DRAFT)
    src = tmp_path / "draft.json"
    out = tmp_path / "rejected.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    assert result.exit_code == 0
    assert "Status: rejected" in result.output


def test_needs_user_review_can_be_rejected(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.NEEDS_USER_REVIEW)
    src = tmp_path / "draft.json"
    out = tmp_path / "rejected.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    assert result.exit_code == 0
    assert "Status: rejected" in result.output


def test_confirmed_draft_writes_rejected_copy_with_note(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.CONFIRMED)
    src = tmp_path / "confirmed.json"
    out = tmp_path / "rejected.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    assert result.exit_code == 0
    assert "Status: rejected" in result.output
    assert "confirmed" in result.output.lower()


def test_already_rejected_writes_copy_with_note(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.REJECTED)
    src = tmp_path / "rejected_in.json"
    out = tmp_path / "rejected_out.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    assert result.exit_code == 0
    assert "Status: rejected" in result.output
    assert "already rejected" in result.output.lower()


def test_rejected_copy_has_rejected_status(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.DRAFT)
    src = tmp_path / "draft.json"
    out = tmp_path / "rejected.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    loaded = SnapshotDraft.from_json(out.read_text(encoding="utf-8"))
    assert loaded.confirmation_status == SnapshotConfirmationStatus.REJECTED


# ---------------------------------------------------------------------------
# Blocked state
# ---------------------------------------------------------------------------

def test_superseded_is_blocked(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.SUPERSEDED)
    src = tmp_path / "superseded.json"
    out = tmp_path / "out.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    assert result.exit_code != 0
    assert "Status: blocked" in result.output


def test_superseded_block_reason_mentions_superseded(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.SUPERSEDED)
    src = tmp_path / "superseded.json"
    out = tmp_path / "out.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    assert "superseded" in result.output.lower()


def test_superseded_block_does_not_write_output(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.SUPERSEDED)
    src = tmp_path / "superseded.json"
    out = tmp_path / "out.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    assert not out.exists()


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_missing_file_exits_nonzero(tmp_path):
    out = tmp_path / "out.json"
    result = runner.invoke(app, ["snapshot", "reject", "nonexistent.json", "--output-draft", str(out)])
    assert result.exit_code != 0


def test_missing_file_status_invalid(tmp_path):
    out = tmp_path / "out.json"
    result = runner.invoke(app, ["snapshot", "reject", "nonexistent.json", "--output-draft", str(out)])
    assert "Status: invalid" in result.output


def test_invalid_json_exits_nonzero(tmp_path):
    src = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    src.write_text("not json", encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    assert result.exit_code != 0


def test_invalid_json_status_invalid(tmp_path):
    src = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    src.write_text("{bad", encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    assert "Status: invalid" in result.output


def test_invalid_schema_exits_nonzero(tmp_path):
    src = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    src.write_text(json.dumps({"snapshot_type": "not_valid", "draft_id": "x",
                               "source_description": "s", "extracted_fields": {},
                               "uncertainties": [], "missing_required_fields": [],
                               "confirmation_status": "draft",
                               "target_local_file": "f.json", "created_at": "2026-01-01"}),
                   encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    assert result.exit_code != 0


def test_invalid_schema_status_invalid(tmp_path):
    src = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    src.write_text(json.dumps({"snapshot_type": "not_valid", "draft_id": "x",
                               "source_description": "s", "extracted_fields": {},
                               "uncertainties": [], "missing_required_fields": [],
                               "confirmation_status": "draft",
                               "target_local_file": "f.json", "created_at": "2026-01-01"}),
                   encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
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
    result = runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    assert result.exit_code != 0
    assert out.read_text(encoding="utf-8") == "existing content"


def test_overwrite_replaces_output(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out = tmp_path / "out.json"
    _write_draft(src, draft)
    out.write_text("existing content", encoding="utf-8")
    result = runner.invoke(
        app, ["snapshot", "reject", str(src), "--output-draft", str(out), "--overwrite"]
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
    result = runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(src)])
    assert result.exit_code != 0
    assert "Status: blocked" in result.output


def test_in_place_guard_preserves_original(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    _write_draft(src, draft)
    original = src.read_text(encoding="utf-8")
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(src)])
    assert src.read_text(encoding="utf-8") == original


# ---------------------------------------------------------------------------
# File mutation safety
# ---------------------------------------------------------------------------

def test_input_draft_not_modified(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out = tmp_path / "rejected.json"
    _write_draft(src, draft)
    before = src.read_text(encoding="utf-8")
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    assert src.read_text(encoding="utf-8") == before


def test_input_draft_status_not_changed_in_file(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.DRAFT)
    src = tmp_path / "draft.json"
    out = tmp_path / "rejected.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    reloaded = SnapshotDraft.from_json(src.read_text(encoding="utf-8"))
    assert reloaded.confirmation_status == SnapshotConfirmationStatus.DRAFT


def test_no_extra_files_created(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out = tmp_path / "rejected.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    names = {p.name for p in tmp_path.iterdir()}
    assert names == {"draft.json", "rejected.json"}


def test_no_atlas_local_files_written(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out = tmp_path / "rejected.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    for forbidden in ["portfolio.json", "watchlist.json", "decision_journal.json"]:
        assert not (tmp_path / forbidden).exists()


def test_no_research_notes_written(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out = tmp_path / "rejected.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    assert not (tmp_path / "research_notes").exists()


# ---------------------------------------------------------------------------
# Output draft field preservation
# ---------------------------------------------------------------------------

def test_rejected_copy_preserves_draft_id(tmp_path):
    draft = _make_draft(draft_id="draft-preserve-231")
    src = tmp_path / "d.json"
    out = tmp_path / "r.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    loaded = SnapshotDraft.from_json(out.read_text(encoding="utf-8"))
    assert loaded.draft_id == "draft-preserve-231"


def test_rejected_copy_preserves_extracted_fields(tmp_path):
    draft = _make_draft()
    src = tmp_path / "d.json"
    out = tmp_path / "r.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    loaded = SnapshotDraft.from_json(out.read_text(encoding="utf-8"))
    assert loaded.extracted_fields == draft.extracted_fields


def test_rejected_copy_preserves_uncertainties(tmp_path):
    draft = _make_draft(uncertainties=["Data was unclear."])
    src = tmp_path / "d.json"
    out = tmp_path / "r.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    loaded = SnapshotDraft.from_json(out.read_text(encoding="utf-8"))
    assert loaded.uncertainties == ["Data was unclear."]


def test_rejected_copy_preserves_missing_required_fields(tmp_path):
    draft = _make_draft(missing_required_fields=["cost_basis"])
    src = tmp_path / "d.json"
    out = tmp_path / "r.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    loaded = SnapshotDraft.from_json(out.read_text(encoding="utf-8"))
    assert loaded.missing_required_fields == ["cost_basis"]


def test_rejected_copy_preserves_source_description(tmp_path):
    draft = _make_draft(source_description="Original source.")
    src = tmp_path / "d.json"
    out = tmp_path / "r.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    loaded = SnapshotDraft.from_json(out.read_text(encoding="utf-8"))
    assert loaded.source_description == "Original source."


def test_rejected_copy_preserves_created_at(tmp_path):
    draft = _make_draft(created_at="2026-03-01")
    src = tmp_path / "d.json"
    out = tmp_path / "r.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    loaded = SnapshotDraft.from_json(out.read_text(encoding="utf-8"))
    assert loaded.created_at == "2026-03-01"


def test_rejected_copy_preserves_target_local_file(tmp_path):
    draft = _make_draft(target_local_file="research_notes/ASML/notes.md")
    src = tmp_path / "d.json"
    out = tmp_path / "r.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    loaded = SnapshotDraft.from_json(out.read_text(encoding="utf-8"))
    assert loaded.target_local_file == "research_notes/ASML/notes.md"


# ---------------------------------------------------------------------------
# Validation / review / export-block chain
# ---------------------------------------------------------------------------

def test_rejected_copy_passes_validate(tmp_path):
    draft = _make_draft()
    src = tmp_path / "d.json"
    out = tmp_path / "rejected.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    result = runner.invoke(app, ["snapshot", "validate", str(out)])
    assert result.exit_code == 0
    assert "Status: valid" in result.output


def test_rejected_copy_reviews_as_not_exportable(tmp_path):
    draft = _make_draft()
    src = tmp_path / "d.json"
    out = tmp_path / "rejected.json"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    result = runner.invoke(app, ["snapshot", "review", str(out)])
    assert result.exit_code == 0
    assert "Exportable: no" in result.output
    assert "Confirmation Status: rejected" in result.output


def test_export_research_notes_blocks_rejected_copy(tmp_path):
    draft = _make_draft()
    src = tmp_path / "d.json"
    out = tmp_path / "rejected.json"
    export_dir = tmp_path / "notes_export"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    result = runner.invoke(
        app,
        ["snapshot", "export-research-notes", str(out), "--output-dir", str(export_dir)],
    )
    assert result.exit_code != 0
    assert not export_dir.exists() or not (export_dir / "ASML" / "notes.md").exists()


# ---------------------------------------------------------------------------
# Safety boundary in output
# ---------------------------------------------------------------------------

def test_success_output_includes_safety_boundary(tmp_path):
    draft = _make_draft()
    src = tmp_path / "d.json"
    out = tmp_path / "r.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    assert "Safety Boundary" in result.output
    assert "Original draft was not modified" in result.output
    assert "No Atlas local input files were changed" in result.output
    assert "Rejected drafts are not exportable" in result.output


def test_blocked_output_includes_reason(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.SUPERSEDED)
    src = tmp_path / "s.json"
    out = tmp_path / "r.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    assert "Status: blocked" in result.output
    assert "Reason:" in result.output


# ---------------------------------------------------------------------------
# Language guardrails
# ---------------------------------------------------------------------------

def test_success_render_no_forbidden_language():
    output = render_snapshot_reject_success(
        input_path="in.json",
        output_path="out.json",
        snapshot_type="research_notes_snapshot",
        already_rejected=False,
        was_confirmed=False,
    )
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output


def test_already_rejected_render_no_forbidden_language():
    output = render_snapshot_reject_success(
        input_path="in.json",
        output_path="out.json",
        snapshot_type="research_notes_snapshot",
        already_rejected=True,
        was_confirmed=False,
    )
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output


def test_was_confirmed_render_no_forbidden_language():
    output = render_snapshot_reject_success(
        input_path="in.json",
        output_path="out.json",
        snapshot_type="research_notes_snapshot",
        already_rejected=False,
        was_confirmed=True,
    )
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output


def test_blocked_render_no_forbidden_language():
    output = render_snapshot_reject_blocked("Draft is superseded.")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output


def test_error_render_no_forbidden_language():
    output = render_snapshot_reject_error("file not found: x.json")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output


def test_cli_output_no_forbidden_language(tmp_path):
    draft = _make_draft()
    src = tmp_path / "d.json"
    out = tmp_path / "r.json"
    _write_draft(src, draft)
    result = runner.invoke(app, ["snapshot", "reject", str(src), "--output-draft", str(out)])
    for term in FORBIDDEN_LANGUAGE:
        assert term not in result.output


# ---------------------------------------------------------------------------
# Provider / network boundary
# ---------------------------------------------------------------------------

def test_no_provider_imports_in_reject_module():
    import atlas.snapshot_input.reject as mod
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
# Unit-level reject_snapshot_draft
# ---------------------------------------------------------------------------

def test_reject_draft_returns_success(tmp_path):
    draft = _make_draft()
    out = tmp_path / "r.json"
    result = reject_snapshot_draft(draft, out)
    assert isinstance(result, SnapshotRejectResult)
    assert result.success is True
    assert result.output_path == out
    assert result.already_rejected is False
    assert result.was_confirmed is False


def test_reject_already_rejected_flag(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.REJECTED)
    out = tmp_path / "r.json"
    result = reject_snapshot_draft(draft, out)
    assert result.success is True
    assert result.already_rejected is True
    assert result.was_confirmed is False


def test_reject_confirmed_was_confirmed_flag(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.CONFIRMED)
    out = tmp_path / "r.json"
    result = reject_snapshot_draft(draft, out)
    assert result.success is True
    assert result.was_confirmed is True
    assert result.already_rejected is False


def test_reject_superseded_returns_failure(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.SUPERSEDED)
    out = tmp_path / "r.json"
    result = reject_snapshot_draft(draft, out)
    assert result.success is False
    assert "superseded" in result.reason.lower()


def test_reject_collision_no_overwrite_returns_failure(tmp_path):
    draft = _make_draft()
    out = tmp_path / "r.json"
    out.write_text("existing", encoding="utf-8")
    result = reject_snapshot_draft(draft, out, overwrite=False)
    assert result.success is False
    assert "already exists" in result.reason.lower() or "overwrite" in result.reason.lower()


def test_reject_collision_with_overwrite_succeeds(tmp_path):
    draft = _make_draft()
    out = tmp_path / "r.json"
    out.write_text("existing", encoding="utf-8")
    result = reject_snapshot_draft(draft, out, overwrite=True)
    assert result.success is True


# ---------------------------------------------------------------------------
# Regression — other commands still work
# ---------------------------------------------------------------------------

def test_snapshot_validate_still_works():
    if not RESEARCH_NOTES_DRAFT.exists():
        pytest.skip("draft not found")
    result = runner.invoke(app, ["snapshot", "validate", str(RESEARCH_NOTES_DRAFT)])
    assert result.exit_code == 0


def test_snapshot_review_still_works():
    if not RESEARCH_NOTES_DRAFT.exists():
        pytest.skip("draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(RESEARCH_NOTES_DRAFT)])
    assert result.exit_code == 0


def test_snapshot_confirm_still_works(tmp_path):
    if not RESEARCH_NOTES_DRAFT.exists():
        pytest.skip("draft not found")
    out = tmp_path / "confirmed.json"
    result = runner.invoke(
        app, ["snapshot", "confirm", str(RESEARCH_NOTES_DRAFT), "--output-draft", str(out)]
    )
    assert result.exit_code == 0


def test_export_research_notes_still_works(tmp_path):
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(
        app,
        ["snapshot", "export-research-notes", str(CONFIRMED_DRAFT), "--output-dir", str(tmp_path)],
    )
    assert result.exit_code == 0
