"""Sprint 225 — Snapshot Draft research notes export tests.

Tests cover: CLI availability, confirmed export success, markdown content,
blocked cases (unconfirmed, wrong type, missing ticker, unsafe ticker,
overwrite guard), file mutation safety, safety boundary, language guardrails,
and provider/network boundary.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest
from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.snapshot_input.export import export_research_notes
from atlas.snapshot_input.render import (
    render_research_notes_export_blocked,
    render_research_notes_export_success,
)
from atlas.snapshot_input.schema import (
    SnapshotConfidence,
    SnapshotConfirmationStatus,
    SnapshotDraft,
    SnapshotType,
)

runner = CliRunner()

CONFIRMED_DRAFT_PATH = Path("examples/snapshot_drafts/research_notes_snapshot_confirmed.json")
UNCONFIRMED_DRAFT_PATH = Path("examples/snapshot_drafts/research_notes_snapshot.json")

FORBIDDEN_LANGUAGE = [
    "Buy",
    "Sell",
    "Strong Buy",
    "Strong Sell",
    "Price Target",
    "Target Price",
    "Urgent",
    "Act Now",
    "Must Buy",
    "Must Sell",
    "Guaranteed",
    "Will Outperform",
    "Financial Advice",
    "Entry",
    "Exit",
]


def _confirmed_draft(**kwargs) -> SnapshotDraft:
    defaults = dict(
        draft_id="draft-test-confirmed-001",
        snapshot_type=SnapshotType.RESEARCH_NOTES_SNAPSHOT,
        source_description="Test research notes",
        extracted_fields={
            "ticker": "ASML",
            "thesis_notes": ["Strong EUV moat."],
            "evidence_gaps": ["Margin data missing."],
            "open_questions": ["Next capex cycle timing?"],
            "risks_to_monitor": ["Export control risk."],
            "reasons_to_wait": ["Evidence gaps not yet resolved."],
        },
        uncertainties=[],
        missing_required_fields=[],
        confirmation_status=SnapshotConfirmationStatus.CONFIRMED,
        target_local_file="research_notes/ASML/notes.md",
        created_at="2026-01-05",
    )
    defaults.update(kwargs)
    return SnapshotDraft(**defaults)


def _draft_with_overrides(**kwargs) -> SnapshotDraft:
    return _confirmed_draft(**kwargs)


# ---------------------------------------------------------------------------
# CLI availability
# ---------------------------------------------------------------------------

def test_export_research_notes_command_available():
    result = runner.invoke(app, ["snapshot", "export-research-notes", "--help"])
    assert result.exit_code == 0


def test_export_research_notes_help_mentions_output_dir():
    result = runner.invoke(app, ["snapshot", "export-research-notes", "--help"])
    assert "output-dir" in result.output.lower() or "OUTPUT_DIR" in result.output


def test_export_research_notes_help_no_forbidden_language():
    result = runner.invoke(app, ["snapshot", "export-research-notes", "--help"])
    for term in FORBIDDEN_LANGUAGE:
        assert term not in result.output, f"Forbidden in help: {term!r}"


# ---------------------------------------------------------------------------
# Confirmed export — end-to-end CLI
# ---------------------------------------------------------------------------

def test_confirmed_draft_exports_via_cli(tmp_path):
    if not CONFIRMED_DRAFT_PATH.exists():
        pytest.skip("confirmed draft example not found")
    result = runner.invoke(
        app,
        ["snapshot", "export-research-notes", str(CONFIRMED_DRAFT_PATH), "--output-dir", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output


def test_confirmed_draft_cli_output_status_written(tmp_path):
    if not CONFIRMED_DRAFT_PATH.exists():
        pytest.skip("confirmed draft example not found")
    result = runner.invoke(
        app,
        ["snapshot", "export-research-notes", str(CONFIRMED_DRAFT_PATH), "--output-dir", str(tmp_path)],
    )
    assert "Status: written" in result.output


def test_confirmed_draft_cli_output_ticker(tmp_path):
    if not CONFIRMED_DRAFT_PATH.exists():
        pytest.skip("confirmed draft example not found")
    result = runner.invoke(
        app,
        ["snapshot", "export-research-notes", str(CONFIRMED_DRAFT_PATH), "--output-dir", str(tmp_path)],
    )
    assert "Ticker: ASML" in result.output


def test_confirmed_draft_cli_output_file_path(tmp_path):
    if not CONFIRMED_DRAFT_PATH.exists():
        pytest.skip("confirmed draft example not found")
    result = runner.invoke(
        app,
        ["snapshot", "export-research-notes", str(CONFIRMED_DRAFT_PATH), "--output-dir", str(tmp_path)],
    )
    assert "ASML" in result.output
    assert "notes.md" in result.output


def test_confirmed_draft_cli_output_safety_boundary(tmp_path):
    if not CONFIRMED_DRAFT_PATH.exists():
        pytest.skip("confirmed draft example not found")
    result = runner.invoke(
        app,
        ["snapshot", "export-research-notes", str(CONFIRMED_DRAFT_PATH), "--output-dir", str(tmp_path)],
    )
    assert "Safety Boundary" in result.output
    assert "portfolio" in result.output.lower()


def test_confirmed_draft_cli_output_no_forbidden_language(tmp_path):
    if not CONFIRMED_DRAFT_PATH.exists():
        pytest.skip("confirmed draft example not found")
    result = runner.invoke(
        app,
        ["snapshot", "export-research-notes", str(CONFIRMED_DRAFT_PATH), "--output-dir", str(tmp_path)],
    )
    for term in FORBIDDEN_LANGUAGE:
        assert term not in result.output, f"Forbidden in CLI output: {term!r}"


# ---------------------------------------------------------------------------
# Output file — ticker uppercasing and path
# ---------------------------------------------------------------------------

def test_output_path_uses_uppercase_ticker(tmp_path):
    draft = _confirmed_draft(extracted_fields={"ticker": "asml", "evidence_gaps": ["Gap 1."]})
    result = export_research_notes(draft, tmp_path)
    assert result.success
    assert result.ticker == "ASML"
    assert result.output_path == tmp_path / "ASML" / "notes.md"


def test_output_file_is_created(tmp_path):
    draft = _confirmed_draft()
    export_research_notes(draft, tmp_path)
    assert (tmp_path / "ASML" / "notes.md").exists()


# ---------------------------------------------------------------------------
# Markdown content
# ---------------------------------------------------------------------------

def test_generated_markdown_has_ticker_header(tmp_path):
    draft = _confirmed_draft()
    export_research_notes(draft, tmp_path)
    content = (tmp_path / "ASML" / "notes.md").read_text(encoding="utf-8")
    assert "# ASML" in content


def test_generated_markdown_has_evidence_gaps(tmp_path):
    draft = _confirmed_draft()
    export_research_notes(draft, tmp_path)
    content = (tmp_path / "ASML" / "notes.md").read_text(encoding="utf-8")
    assert "Evidence Gaps" in content
    assert "Margin data missing." in content


def test_generated_markdown_has_open_questions(tmp_path):
    draft = _confirmed_draft()
    export_research_notes(draft, tmp_path)
    content = (tmp_path / "ASML" / "notes.md").read_text(encoding="utf-8")
    assert "Open Questions" in content
    assert "Next capex cycle timing?" in content


def test_generated_markdown_has_risks_to_monitor(tmp_path):
    draft = _confirmed_draft()
    export_research_notes(draft, tmp_path)
    content = (tmp_path / "ASML" / "notes.md").read_text(encoding="utf-8")
    assert "Risks to Monitor" in content
    assert "Export control risk." in content


def test_generated_markdown_has_reason_to_wait(tmp_path):
    draft = _confirmed_draft()
    export_research_notes(draft, tmp_path)
    content = (tmp_path / "ASML" / "notes.md").read_text(encoding="utf-8")
    assert "Reason to Wait" in content
    assert "Evidence gaps not yet resolved." in content


def test_generated_markdown_has_source_section(tmp_path):
    draft = _confirmed_draft()
    export_research_notes(draft, tmp_path)
    content = (tmp_path / "ASML" / "notes.md").read_text(encoding="utf-8")
    assert "## Source" in content
    assert "draft-test-confirmed-001" in content
    assert "Test research notes" in content


def test_generated_markdown_no_forbidden_language(tmp_path):
    draft = _confirmed_draft()
    export_research_notes(draft, tmp_path)
    content = (tmp_path / "ASML" / "notes.md").read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in content, f"Forbidden in markdown: {term!r}"


def test_generated_markdown_readable_by_weekly_review_parser(tmp_path):
    """Markdown output must be parseable by the Weekly Review research notes loader."""
    from atlas.weekly_review.inputs import _load_research_note
    draft = _confirmed_draft()
    export_research_notes(draft, tmp_path)
    note = _load_research_note("ASML", tmp_path / "ASML" / "notes.md")
    assert note.available
    assert note.ticker == "ASML"
    assert len(note.evidence_gaps) > 0
    assert len(note.open_questions) > 0
    assert len(note.risks_to_monitor) > 0
    assert len(note.reasons_to_wait) > 0


def test_reasons_to_wait_alias_supported(tmp_path):
    """reason_to_wait (singular) in extracted_fields should be accepted."""
    draft = _confirmed_draft(extracted_fields={
        "ticker": "XYL",
        "reason_to_wait": ["Single alias reason."],
        "evidence_gaps": [],
    })
    result = export_research_notes(draft, tmp_path)
    assert result.success
    content = (tmp_path / "XYL" / "notes.md").read_text(encoding="utf-8")
    assert "Reason to Wait" in content
    assert "Single alias reason." in content


# ---------------------------------------------------------------------------
# Blocked — unconfirmed draft
# ---------------------------------------------------------------------------

def test_unconfirmed_draft_is_blocked(tmp_path):
    draft = _confirmed_draft(confirmation_status=SnapshotConfirmationStatus.DRAFT)
    result = export_research_notes(draft, tmp_path)
    assert not result.success
    assert "not confirmed" in result.reason.lower()


def test_needs_review_draft_is_blocked(tmp_path):
    draft = _confirmed_draft(confirmation_status=SnapshotConfirmationStatus.NEEDS_USER_REVIEW)
    result = export_research_notes(draft, tmp_path)
    assert not result.success


def test_rejected_draft_is_blocked(tmp_path):
    draft = _confirmed_draft(confirmation_status=SnapshotConfirmationStatus.REJECTED)
    result = export_research_notes(draft, tmp_path)
    assert not result.success


def test_unconfirmed_cli_exits_nonzero(tmp_path):
    if not UNCONFIRMED_DRAFT_PATH.exists():
        pytest.skip("unconfirmed draft example not found")
    result = runner.invoke(
        app,
        ["snapshot", "export-research-notes", str(UNCONFIRMED_DRAFT_PATH), "--output-dir", str(tmp_path)],
    )
    assert result.exit_code != 0


def test_unconfirmed_cli_output_status_blocked(tmp_path):
    if not UNCONFIRMED_DRAFT_PATH.exists():
        pytest.skip("unconfirmed draft example not found")
    result = runner.invoke(
        app,
        ["snapshot", "export-research-notes", str(UNCONFIRMED_DRAFT_PATH), "--output-dir", str(tmp_path)],
    )
    assert "Status: blocked" in result.output


# ---------------------------------------------------------------------------
# Blocked — wrong snapshot type
# ---------------------------------------------------------------------------

def test_portfolio_snapshot_type_is_blocked(tmp_path):
    draft = _confirmed_draft(
        snapshot_type=SnapshotType.PORTFOLIO_SNAPSHOT,
        target_local_file="portfolio.json",
    )
    result = export_research_notes(draft, tmp_path)
    assert not result.success
    assert "research_notes_snapshot" in result.reason


def test_watchlist_snapshot_type_is_blocked(tmp_path):
    draft = _confirmed_draft(
        snapshot_type=SnapshotType.WATCHLIST_SNAPSHOT,
        target_local_file="watchlist.json",
    )
    result = export_research_notes(draft, tmp_path)
    assert not result.success


def test_unknown_snapshot_type_is_blocked(tmp_path):
    draft = _confirmed_draft(
        snapshot_type=SnapshotType.UNKNOWN_SNAPSHOT,
        target_local_file="unknown.json",
    )
    result = export_research_notes(draft, tmp_path)
    assert not result.success


# ---------------------------------------------------------------------------
# Blocked — missing ticker
# ---------------------------------------------------------------------------

def test_missing_ticker_in_extracted_fields_uses_related_tickers(tmp_path):
    draft = _confirmed_draft(
        extracted_fields={"evidence_gaps": ["A gap."]},
        related_tickers=["XYL"],
    )
    result = export_research_notes(draft, tmp_path)
    assert result.success
    assert result.ticker == "XYL"


def test_missing_ticker_everywhere_is_blocked(tmp_path):
    draft = _confirmed_draft(
        extracted_fields={"evidence_gaps": ["A gap."]},
        related_tickers=[],
    )
    result = export_research_notes(draft, tmp_path)
    assert not result.success
    assert "ticker" in result.reason.lower()


def test_empty_ticker_is_blocked(tmp_path):
    draft = _confirmed_draft(
        extracted_fields={"ticker": "  ", "evidence_gaps": []},
        related_tickers=[],
    )
    result = export_research_notes(draft, tmp_path)
    assert not result.success


# ---------------------------------------------------------------------------
# Blocked — unsafe ticker
# ---------------------------------------------------------------------------

def test_ticker_with_forward_slash_is_blocked(tmp_path):
    draft = _confirmed_draft(
        extracted_fields={"ticker": "AS/ML"},
        related_tickers=[],
    )
    result = export_research_notes(draft, tmp_path)
    assert not result.success
    assert "path" in result.reason.lower() or "separator" in result.reason.lower()


def test_ticker_with_backslash_is_blocked(tmp_path):
    draft = _confirmed_draft(
        extracted_fields={"ticker": "AS\\ML"},
        related_tickers=[],
    )
    result = export_research_notes(draft, tmp_path)
    assert not result.success


def test_ticker_with_dotdot_is_blocked(tmp_path):
    draft = _confirmed_draft(
        extracted_fields={"ticker": ".."},
        related_tickers=[],
    )
    result = export_research_notes(draft, tmp_path)
    assert not result.success


# ---------------------------------------------------------------------------
# Overwrite guard
# ---------------------------------------------------------------------------

def test_existing_notes_not_overwritten_by_default(tmp_path):
    original = "# Original Content\n"
    out = tmp_path / "ASML" / "notes.md"
    out.parent.mkdir(parents=True)
    out.write_text(original, encoding="utf-8")
    draft = _confirmed_draft()
    result = export_research_notes(draft, tmp_path, overwrite=False)
    assert not result.success
    assert out.read_text(encoding="utf-8") == original


def test_overwrite_flag_replaces_existing_file(tmp_path):
    original = "# Original Content\n"
    out = tmp_path / "ASML" / "notes.md"
    out.parent.mkdir(parents=True)
    out.write_text(original, encoding="utf-8")
    draft = _confirmed_draft()
    result = export_research_notes(draft, tmp_path, overwrite=True)
    assert result.success
    assert out.read_text(encoding="utf-8") != original


def test_default_collision_cli_exits_nonzero(tmp_path):
    out = tmp_path / "ASML" / "notes.md"
    out.parent.mkdir(parents=True)
    out.write_text("# Existing\n", encoding="utf-8")
    if not CONFIRMED_DRAFT_PATH.exists():
        pytest.skip("confirmed draft example not found")
    result = runner.invoke(
        app,
        ["snapshot", "export-research-notes", str(CONFIRMED_DRAFT_PATH), "--output-dir", str(tmp_path)],
    )
    assert result.exit_code != 0


def test_overwrite_cli_succeeds(tmp_path):
    out = tmp_path / "ASML" / "notes.md"
    out.parent.mkdir(parents=True)
    out.write_text("# Existing\n", encoding="utf-8")
    if not CONFIRMED_DRAFT_PATH.exists():
        pytest.skip("confirmed draft example not found")
    result = runner.invoke(
        app,
        [
            "snapshot", "export-research-notes", str(CONFIRMED_DRAFT_PATH),
            "--output-dir", str(tmp_path), "--overwrite",
        ],
    )
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# File mutation safety
# ---------------------------------------------------------------------------

def test_export_does_not_mutate_draft_file(tmp_path):
    if not CONFIRMED_DRAFT_PATH.exists():
        pytest.skip("confirmed draft example not found")
    content_before = CONFIRMED_DRAFT_PATH.read_text(encoding="utf-8")
    runner.invoke(
        app,
        ["snapshot", "export-research-notes", str(CONFIRMED_DRAFT_PATH), "--output-dir", str(tmp_path)],
    )
    assert CONFIRMED_DRAFT_PATH.read_text(encoding="utf-8") == content_before


def test_export_writes_only_under_output_dir(tmp_path):
    """Only files under output_dir should be created; no portfolio/watchlist/journal files."""
    draft = _confirmed_draft()
    files_before = set(Path(".").glob("**/*.json"))
    export_research_notes(draft, tmp_path)
    files_after = set(Path(".").glob("**/*.json"))
    # No new JSON files should appear in the project directory
    assert files_before == files_after


def test_export_creates_output_dir_if_needed(tmp_path):
    out_dir = tmp_path / "new_subdir"
    assert not out_dir.exists()
    draft = _confirmed_draft()
    result = export_research_notes(draft, out_dir)
    assert result.success
    assert (out_dir / "ASML" / "notes.md").exists()


# ---------------------------------------------------------------------------
# render helpers (unit tests)
# ---------------------------------------------------------------------------

def test_render_success_includes_status_written():
    output = render_research_notes_export_success("ASML", Path("/tmp/ASML/notes.md"))
    assert "Status: written" in output


def test_render_success_includes_ticker():
    output = render_research_notes_export_success("XYL", Path("/tmp/XYL/notes.md"))
    assert "Ticker: XYL" in output


def test_render_success_includes_safety_boundary():
    output = render_research_notes_export_success("ASML", Path("/tmp/ASML/notes.md"))
    assert "Safety Boundary" in output


def test_render_blocked_includes_status_blocked():
    output = render_research_notes_export_blocked("Draft is not confirmed.")
    assert "Status: blocked" in output


def test_render_blocked_includes_reason():
    output = render_research_notes_export_blocked("Only research_notes_snapshot allowed.")
    assert "research_notes_snapshot" in output


def test_render_success_no_forbidden_language():
    output = render_research_notes_export_success("ASML", Path("/tmp/ASML/notes.md"))
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output, f"Forbidden in render: {term!r}"


# ---------------------------------------------------------------------------
# Bounded output
# ---------------------------------------------------------------------------

def test_long_bullet_is_truncated(tmp_path):
    long_text = "A" * 1000
    draft = _confirmed_draft(extracted_fields={
        "ticker": "ASML",
        "evidence_gaps": [long_text],
    })
    export_research_notes(draft, tmp_path)
    content = (tmp_path / "ASML" / "notes.md").read_text(encoding="utf-8")
    # No line in the markdown should exceed 500 chars + "- " prefix
    for line in content.splitlines():
        assert len(line) <= 502, f"Line too long: {len(line)} chars"


def test_many_bullets_are_capped(tmp_path):
    many_gaps = [f"Gap number {i}." for i in range(50)]
    draft = _confirmed_draft(extracted_fields={
        "ticker": "ASML",
        "evidence_gaps": many_gaps,
    })
    export_research_notes(draft, tmp_path)
    content = (tmp_path / "ASML" / "notes.md").read_text(encoding="utf-8")
    bullet_lines = [l for l in content.splitlines() if l.startswith("- ")]
    # Cap is 20 per content section; Source section adds up to 3 meta bullets
    assert len(bullet_lines) <= 23


# ---------------------------------------------------------------------------
# Provider / network boundary
# ---------------------------------------------------------------------------

def test_no_provider_imports_in_export_module():
    import atlas.snapshot_input.export as mod
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
                assert "providers" not in name, f"Provider import in export.py: {name}"
                assert "requests" not in name, f"Network import: {name}"
                assert "urllib" not in name, f"Network import: {name}"
                assert "httpx" not in name, f"Network import: {name}"


# ---------------------------------------------------------------------------
# Weekly Review regression
# ---------------------------------------------------------------------------

def test_snapshot_validate_still_works():
    if not CONFIRMED_DRAFT_PATH.exists():
        pytest.skip("confirmed draft example not found")
    result = runner.invoke(app, ["snapshot", "validate", str(CONFIRMED_DRAFT_PATH)])
    assert result.exit_code == 0
    assert "Status: valid" in result.output


def test_weekly_review_still_available():
    result = runner.invoke(app, ["weekly-review", "--help"])
    assert result.exit_code == 0
