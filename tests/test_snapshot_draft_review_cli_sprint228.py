"""Sprint 228 — Snapshot Draft read-only review CLI tests.

Tests cover: command availability, confirmed draft review, non-confirmed draft
review, exportability display, blocking issues, extracted fields summary,
research notes review section, error cases, file mutation safety, language
guardrails, and provider/network boundary.
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
    collect_snapshot_draft_review_issues,
    render_snapshot_draft_review,
    render_snapshot_draft_review_error,
)
from atlas.snapshot_input.schema import (
    SnapshotConfidence,
    SnapshotConfirmationStatus,
    SnapshotDraft,
    SnapshotType,
)

runner = CliRunner()

CONFIRMED_DRAFT = Path("examples/snapshot_drafts/research_notes_snapshot_confirmed.json")
PORTFOLIO_DRAFT = Path("examples/snapshot_drafts/portfolio_snapshot.json")

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
        draft_id="draft-test-228",
        snapshot_type=SnapshotType.RESEARCH_NOTES_SNAPSHOT,
        source_description="Test notes",
        extracted_fields={
            "ticker": "ASML",
            "title": "ASML notes",
            "evidence_gaps": ["Gap 1.", "Gap 2."],
            "open_questions": ["Question 1?"],
            "risks_to_monitor": ["Risk 1."],
            "reasons_to_wait": ["Reason 1."],
        },
        uncertainties=[],
        missing_required_fields=[],
        confirmation_status=SnapshotConfirmationStatus.CONFIRMED,
        target_local_file="research_notes/ASML/notes.md",
        created_at="2026-01-05",
    )
    defaults.update(kwargs)
    return SnapshotDraft(**defaults)


def _make_draft_status(status: SnapshotConfirmationStatus) -> SnapshotDraft:
    return _make_draft(confirmation_status=status)


# ---------------------------------------------------------------------------
# CLI availability
# ---------------------------------------------------------------------------

def test_snapshot_review_help_available():
    result = runner.invoke(app, ["snapshot", "review", "--help"])
    assert result.exit_code == 0


def test_snapshot_review_in_snapshot_group():
    result = runner.invoke(app, ["snapshot", "--help"])
    assert result.exit_code == 0
    assert "review" in result.output.lower()


def test_snapshot_review_help_no_forbidden_language():
    result = runner.invoke(app, ["snapshot", "review", "--help"])
    for term in FORBIDDEN_LANGUAGE:
        assert term not in result.output, f"Forbidden in help: {term!r}"


# ---------------------------------------------------------------------------
# Valid confirmed draft — exit code and header
# ---------------------------------------------------------------------------

def test_confirmed_draft_exits_zero():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(CONFIRMED_DRAFT)])
    assert result.exit_code == 0


def test_review_output_status_reviewable():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(CONFIRMED_DRAFT)])
    assert "Status: reviewable" in result.output


def test_review_output_includes_snapshot_type():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(CONFIRMED_DRAFT)])
    assert "Snapshot Type:" in result.output
    assert "research_notes_snapshot" in result.output


def test_review_output_includes_confidence():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(CONFIRMED_DRAFT)])
    assert "Confidence:" in result.output


def test_review_output_includes_confirmation_status():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(CONFIRMED_DRAFT)])
    assert "Confirmation Status:" in result.output


def test_review_output_includes_target_local_file():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(CONFIRMED_DRAFT)])
    assert "Target Local File:" in result.output


def test_review_output_includes_related_tickers():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(CONFIRMED_DRAFT)])
    assert "Related Tickers:" in result.output
    assert "ASML" in result.output


# ---------------------------------------------------------------------------
# Exportability display
# ---------------------------------------------------------------------------

def test_confirmed_draft_shows_exportable_yes():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(CONFIRMED_DRAFT)])
    assert "Exportable: yes" in result.output


def test_non_confirmed_draft_shows_exportable_no():
    if not PORTFOLIO_DRAFT.exists():
        pytest.skip("portfolio draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(PORTFOLIO_DRAFT)])
    assert "Exportable: no" in result.output


def test_non_confirmed_draft_shows_exportable_reason():
    if not PORTFOLIO_DRAFT.exists():
        pytest.skip("portfolio draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(PORTFOLIO_DRAFT)])
    assert "only confirmed drafts are exportable" in result.output.lower()


def test_draft_status_shows_exportable_no():
    draft = _make_draft_status(SnapshotConfirmationStatus.DRAFT)
    output = render_snapshot_draft_review(draft)
    assert "Exportable: no" in output


def test_needs_user_review_status_shows_exportable_no():
    draft = _make_draft_status(SnapshotConfirmationStatus.NEEDS_USER_REVIEW)
    output = render_snapshot_draft_review(draft)
    assert "Exportable: no" in output


def test_rejected_status_shows_exportable_no():
    draft = _make_draft_status(SnapshotConfirmationStatus.REJECTED)
    output = render_snapshot_draft_review(draft)
    assert "Exportable: no" in output


def test_superseded_status_shows_exportable_no():
    draft = _make_draft_status(SnapshotConfirmationStatus.SUPERSEDED)
    output = render_snapshot_draft_review(draft)
    assert "Exportable: no" in output


# ---------------------------------------------------------------------------
# Extracted fields summary
# ---------------------------------------------------------------------------

def test_review_output_includes_extracted_fields():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(CONFIRMED_DRAFT)])
    assert "Extracted Fields:" in result.output


def test_extracted_fields_shows_list_counts():
    draft = _make_draft()
    output = render_snapshot_draft_review(draft)
    assert "evidence_gaps: 2 item(s)" in output
    assert "open_questions: 1 item(s)" in output


def test_extracted_fields_shows_scalar_value():
    draft = _make_draft()
    output = render_snapshot_draft_review(draft)
    assert "ticker" in output
    assert "ASML" in output


def test_extracted_fields_empty_shows_empty():
    draft = _make_draft(
        snapshot_type=SnapshotType.PORTFOLIO_SNAPSHOT,
        extracted_fields={},
        target_local_file="portfolio.json",
    )
    output = render_snapshot_draft_review(draft)
    assert "(empty)" in output


def test_extracted_fields_not_unbounded():
    """Long string values must be truncated."""
    long_value = "A" * 200
    draft = _make_draft(extracted_fields={"ticker": "ASML", "notes": long_value})
    output = render_snapshot_draft_review(draft)
    # The long value should not appear in full
    assert long_value not in output


# ---------------------------------------------------------------------------
# Uncertainties and missing required fields
# ---------------------------------------------------------------------------

def test_review_output_includes_uncertainties_section():
    if not PORTFOLIO_DRAFT.exists():
        pytest.skip("portfolio draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(PORTFOLIO_DRAFT)])
    assert "Uncertainties" in result.output


def test_review_shows_uncertainties_none_listed_when_empty():
    draft = _make_draft(uncertainties=[])
    output = render_snapshot_draft_review(draft)
    assert "Uncertainties: none listed" in output


def test_review_shows_uncertainties_count_when_present():
    draft = _make_draft(uncertainties=["Gap A.", "Gap B."])
    output = render_snapshot_draft_review(draft)
    assert "Uncertainties: 2 listed" in output


def test_review_shows_uncertainty_detail():
    draft = _make_draft(uncertainties=["Currency unclear."])
    output = render_snapshot_draft_review(draft)
    assert "Currency unclear." in output


def test_review_shows_missing_fields_none_listed_when_empty():
    draft = _make_draft(missing_required_fields=[])
    output = render_snapshot_draft_review(draft)
    assert "Missing Required Fields: none listed" in output


def test_review_shows_missing_fields_count_when_present():
    draft = _make_draft(missing_required_fields=["cost_basis", "sector"])
    output = render_snapshot_draft_review(draft)
    assert "Missing Required Fields: 2 listed" in output


def test_review_shows_missing_fields_as_warnings():
    draft = _make_draft(missing_required_fields=["cost_basis"])
    output = render_snapshot_draft_review(draft)
    assert "cost_basis" in output
    assert "warning" in output.lower() or "review before confirming" in output.lower()


# ---------------------------------------------------------------------------
# Blocking issues
# ---------------------------------------------------------------------------

def test_review_includes_blocking_issues_section():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(CONFIRMED_DRAFT)])
    assert "Blocking Issues:" in result.output


def test_no_blocking_issues_for_clean_draft():
    # A draft/needs_user_review research_notes draft with ticker and fields should have no blocks
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.DRAFT)
    issues = collect_snapshot_draft_review_issues(draft)
    assert len(issues) == 0


def test_unknown_snapshot_type_is_a_blocking_issue():
    draft = _make_draft(
        snapshot_type=SnapshotType.UNKNOWN_SNAPSHOT,
        target_local_file="unknown.json",
    )
    issues = collect_snapshot_draft_review_issues(draft)
    assert any("unknown" in i.lower() for i in issues)


def test_confirmed_status_surfaces_as_blocking_issue():
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.CONFIRMED)
    issues = collect_snapshot_draft_review_issues(draft)
    assert any("terminal" in i.lower() or "confirmed" in i.lower() for i in issues)


def test_rejected_status_surfaces_as_blocking_issue():
    draft = _make_draft_status(SnapshotConfirmationStatus.REJECTED)
    issues = collect_snapshot_draft_review_issues(draft)
    assert any("terminal" in i.lower() or "rejected" in i.lower() for i in issues)


def test_superseded_status_surfaces_as_blocking_issue():
    draft = _make_draft_status(SnapshotConfirmationStatus.SUPERSEDED)
    issues = collect_snapshot_draft_review_issues(draft)
    assert any("terminal" in i.lower() or "superseded" in i.lower() for i in issues)


def test_empty_extracted_fields_is_blocking_issue():
    draft = _make_draft(
        snapshot_type=SnapshotType.PORTFOLIO_SNAPSHOT,
        extracted_fields={},
        target_local_file="portfolio.json",
        confirmation_status=SnapshotConfirmationStatus.DRAFT,
    )
    issues = collect_snapshot_draft_review_issues(draft)
    assert any("empty" in i.lower() or "extracted" in i.lower() for i in issues)


def test_missing_ticker_for_research_notes_is_blocking_issue():
    draft = _make_draft(
        extracted_fields={"evidence_gaps": ["Gap."]},
        related_tickers=[],
        confirmation_status=SnapshotConfirmationStatus.DRAFT,
    )
    issues = collect_snapshot_draft_review_issues(draft)
    assert any("ticker" in i.lower() for i in issues)


def test_unsafe_ticker_is_blocking_issue():
    draft = _make_draft(
        extracted_fields={"ticker": "AS/ML"},
        confirmation_status=SnapshotConfirmationStatus.DRAFT,
    )
    issues = collect_snapshot_draft_review_issues(draft)
    assert any("unsafe" in i.lower() or "separator" in i.lower() for i in issues)


def test_portfolio_type_does_not_require_ticker():
    draft = _make_draft(
        snapshot_type=SnapshotType.PORTFOLIO_SNAPSHOT,
        extracted_fields={"holdings": []},
        related_tickers=[],
        target_local_file="portfolio.json",
        confirmation_status=SnapshotConfirmationStatus.DRAFT,
    )
    issues = collect_snapshot_draft_review_issues(draft)
    # Portfolio type doesn't require ticker — no ticker blocking issue
    assert not any("ticker" in i.lower() for i in issues)


# ---------------------------------------------------------------------------
# Research Notes Review section
# ---------------------------------------------------------------------------

def test_research_notes_review_section_present():
    draft = _make_draft()
    output = render_snapshot_draft_review(draft)
    assert "Research Notes Review:" in output


def test_research_notes_review_shows_ticker():
    draft = _make_draft()
    output = render_snapshot_draft_review(draft)
    assert "Ticker: ASML" in output


def test_research_notes_review_shows_title_present():
    draft = _make_draft()
    output = render_snapshot_draft_review(draft)
    assert "Title: present" in output


def test_research_notes_review_shows_evidence_gaps_present():
    draft = _make_draft()
    output = render_snapshot_draft_review(draft)
    assert "Evidence Gaps: present" in output


def test_research_notes_review_shows_open_questions_present():
    draft = _make_draft()
    output = render_snapshot_draft_review(draft)
    assert "Open Questions: present" in output


def test_research_notes_review_shows_risks_to_monitor_present():
    draft = _make_draft()
    output = render_snapshot_draft_review(draft)
    assert "Risks to Monitor: present" in output


def test_research_notes_review_shows_reasons_to_wait_present():
    draft = _make_draft()
    output = render_snapshot_draft_review(draft)
    assert "Reasons to Wait: present" in output


def test_research_notes_missing_field_shows_missing():
    draft = _make_draft(extracted_fields={"ticker": "ASML"})
    output = render_snapshot_draft_review(draft)
    assert "Evidence Gaps: missing" in output
    assert "Open Questions: missing" in output


def test_portfolio_type_has_no_research_notes_section():
    draft = _make_draft(
        snapshot_type=SnapshotType.PORTFOLIO_SNAPSHOT,
        extracted_fields={"holdings": [{"ticker": "ASML"}]},
        target_local_file="portfolio.json",
    )
    output = render_snapshot_draft_review(draft)
    assert "Research Notes Review" not in output


# ---------------------------------------------------------------------------
# Safety boundary
# ---------------------------------------------------------------------------

def test_review_output_includes_safety_boundary():
    draft = _make_draft()
    output = render_snapshot_draft_review(draft)
    assert "Safety Boundary:" in output
    assert "read-only" in output.lower()
    assert "does not confirm" in output.lower()
    assert "does not write" in output.lower()


def test_cli_output_includes_safety_boundary():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(CONFIRMED_DRAFT)])
    assert "Safety Boundary" in result.output
    assert "read-only" in result.output.lower()


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_missing_file_exits_nonzero():
    result = runner.invoke(app, ["snapshot", "review", "nonexistent/path.json"])
    assert result.exit_code != 0


def test_missing_file_output_status_invalid():
    result = runner.invoke(app, ["snapshot", "review", "nonexistent/path.json"])
    assert "Status: invalid" in result.output


def test_missing_file_output_error_message():
    result = runner.invoke(app, ["snapshot", "review", "nonexistent/path.json"])
    assert "Error:" in result.output


def test_invalid_json_exits_nonzero(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json {{", encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "review", str(bad)])
    assert result.exit_code != 0


def test_invalid_json_output_status_invalid(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "review", str(bad)])
    assert "Status: invalid" in result.output


def test_invalid_schema_exits_nonzero(tmp_path):
    bad = tmp_path / "bad.json"
    data = {"draft_id": "", "snapshot_type": "research_notes_snapshot",
            "source_description": "test", "extracted_fields": {},
            "uncertainties": [], "missing_required_fields": [],
            "confirmation_status": "draft",
            "target_local_file": "notes.md", "created_at": "2026-01-05"}
    bad.write_text(json.dumps(data), encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "review", str(bad)])
    assert result.exit_code != 0


def test_invalid_schema_output_status_invalid(tmp_path):
    bad = tmp_path / "bad.json"
    data = {"draft_id": "ok", "snapshot_type": "not_a_valid_type",
            "source_description": "test", "extracted_fields": {},
            "uncertainties": [], "missing_required_fields": [],
            "confirmation_status": "draft",
            "target_local_file": "notes.md", "created_at": "2026-01-05"}
    bad.write_text(json.dumps(data), encoding="utf-8")
    result = runner.invoke(app, ["snapshot", "review", str(bad)])
    assert "Status: invalid" in result.output


def test_render_review_error_status_invalid():
    output = render_snapshot_draft_review_error("file not found: bad.json")
    assert "Status: invalid" in output
    assert "Error:" in output


# ---------------------------------------------------------------------------
# File mutation safety
# ---------------------------------------------------------------------------

def test_review_does_not_modify_draft_file(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.DRAFT)
    path = tmp_path / "draft.json"
    path.write_text(draft.to_json(), encoding="utf-8")
    content_before = path.read_text(encoding="utf-8")
    runner.invoke(app, ["snapshot", "review", str(path)])
    assert path.read_text(encoding="utf-8") == content_before


def test_review_creates_no_new_files(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.DRAFT)
    path = tmp_path / "draft.json"
    path.write_text(draft.to_json(), encoding="utf-8")
    files_before = set(tmp_path.iterdir())
    runner.invoke(app, ["snapshot", "review", str(path)])
    assert set(tmp_path.iterdir()) == files_before


def test_review_creates_no_output_directories(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.DRAFT)
    path = tmp_path / "draft.json"
    path.write_text(draft.to_json(), encoding="utf-8")
    runner.invoke(app, ["snapshot", "review", str(path)])
    dirs = [p for p in tmp_path.iterdir() if p.is_dir()]
    assert len(dirs) == 0


# ---------------------------------------------------------------------------
# Language guardrails
# ---------------------------------------------------------------------------

def test_review_output_no_forbidden_language():
    draft = _make_draft()
    output = render_snapshot_draft_review(draft)
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output, f"Forbidden in output: {term!r}"


def test_cli_review_output_no_forbidden_language():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(CONFIRMED_DRAFT)])
    for term in FORBIDDEN_LANGUAGE:
        assert term not in result.output, f"Forbidden in CLI output: {term!r}"


def test_render_review_error_no_forbidden_language():
    output = render_snapshot_draft_review_error("source not found.")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output, f"Forbidden in error output: {term!r}"


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
                assert "providers" not in name, f"Provider import: {name}"
                assert "requests" not in name, f"Network import: {name}"
                assert "urllib" not in name, f"Network import: {name}"
                assert "httpx" not in name, f"Network import: {name}"


# ---------------------------------------------------------------------------
# Regression — other commands still work
# ---------------------------------------------------------------------------

def test_snapshot_validate_still_works():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(app, ["snapshot", "validate", str(CONFIRMED_DRAFT)])
    assert result.exit_code == 0
    assert "Status: valid" in result.output


def test_export_research_notes_still_works(tmp_path):
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("confirmed draft not found")
    result = runner.invoke(
        app,
        ["snapshot", "export-research-notes", str(CONFIRMED_DRAFT), "--output-dir", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert "Status: written" in result.output


def test_weekly_review_still_available():
    result = runner.invoke(app, ["weekly-review", "--help"])
    assert result.exit_code == 0
