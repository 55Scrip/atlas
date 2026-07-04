"""Sprint 233 — Snapshot company facts export tests.

Tests cover: command availability, confirmed company_facts_snapshot export,
JSON content, blocking cases, file mutation safety, overwrite behavior,
Weekly Review detection, language guardrails, and provider/network boundary.
"""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.snapshot_input.export_company_facts import (
    CompanyFactsExportResult,
    export_company_facts,
)
from atlas.snapshot_input.render import (
    render_company_facts_export_blocked,
    render_company_facts_export_success,
)
from atlas.snapshot_input.schema import (
    SnapshotConfirmationStatus,
    SnapshotDraft,
    SnapshotType,
)

runner = CliRunner()

CONFIRMED_DRAFT = Path(
    "examples/snapshot_drafts/company_facts_snapshot_confirmed.json"
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
        draft_id="draft-233-cf",
        snapshot_type=SnapshotType.COMPANY_FACTS_SNAPSHOT,
        source_description="Sprint 233 test company facts",
        extracted_fields={
            "ticker": "ASML",
            "company_name": "ASML Holding N.V.",
            "business_summary": "Supplier of lithography equipment.",
            "sector": "Semiconductors",
            "geography": ["Netherlands", "Global"],
            "revenue_drivers": ["EUV systems", "DUV systems"],
            "key_risks": ["Export controls", "Cyclicality"],
        },
        uncertainties=[],
        missing_required_fields=[],
        confirmation_status=SnapshotConfirmationStatus.CONFIRMED,
        target_local_file="company_facts/ASML.json",
        created_at="2026-01-10",
    )
    defaults.update(kwargs)
    return SnapshotDraft(**defaults)


def _write_draft(path: Path, draft: SnapshotDraft) -> None:
    path.write_text(draft.to_json(), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI availability
# ---------------------------------------------------------------------------

def test_export_company_facts_help_available():
    result = runner.invoke(app, ["snapshot", "export-company-facts", "--help"])
    assert result.exit_code == 0


def test_export_company_facts_in_snapshot_group():
    result = runner.invoke(app, ["snapshot", "--help"])
    assert result.exit_code == 0
    assert "export-company-facts" in result.output


def test_export_company_facts_help_no_forbidden_language():
    result = runner.invoke(app, ["snapshot", "export-company-facts", "--help"])
    for term in FORBIDDEN_LANGUAGE:
        assert term not in result.output


# ---------------------------------------------------------------------------
# Confirmed example draft — validate and review still work
# ---------------------------------------------------------------------------

def test_example_draft_validates():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("example draft not found")
    result = runner.invoke(app, ["snapshot", "validate", str(CONFIRMED_DRAFT)])
    assert result.exit_code == 0
    assert "Status: valid" in result.output


def test_example_draft_reviews_as_exportable():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("example draft not found")
    result = runner.invoke(app, ["snapshot", "review", str(CONFIRMED_DRAFT)])
    assert result.exit_code == 0
    assert "Exportable: yes" in result.output


# ---------------------------------------------------------------------------
# Successful export
# ---------------------------------------------------------------------------

def test_confirmed_company_facts_export_exits_zero(tmp_path):
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("example draft not found")
    result = runner.invoke(
        app, ["snapshot", "export-company-facts", str(CONFIRMED_DRAFT), "--output-dir", str(tmp_path)]
    )
    assert result.exit_code == 0


def test_export_status_written(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "company_facts"
    _write_draft(src, draft)
    result = runner.invoke(
        app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)]
    )
    assert "Status: written" in result.output


def test_output_file_uses_uppercase_ticker(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "company_facts"
    _write_draft(src, draft)
    runner.invoke(
        app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)]
    )
    assert (out_dir / "ASML.json").exists()


def test_output_file_actual_name_is_uppercase(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "company_facts"
    _write_draft(src, draft)
    runner.invoke(
        app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)]
    )
    written = list(out_dir.iterdir())
    assert len(written) == 1
    assert written[0].name == "ASML.json"


def test_generated_json_includes_ticker(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)])
    data = json.loads((out_dir / "ASML.json").read_text(encoding="utf-8"))
    assert data["ticker"] == "ASML"


def test_generated_json_includes_company_name(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)])
    data = json.loads((out_dir / "ASML.json").read_text(encoding="utf-8"))
    assert data.get("company_name") == "ASML Holding N.V."


def test_generated_json_includes_business_summary(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)])
    data = json.loads((out_dir / "ASML.json").read_text(encoding="utf-8"))
    assert "business_summary" in data
    assert "lithography" in data["business_summary"].lower()


def test_generated_json_includes_sector(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)])
    data = json.loads((out_dir / "ASML.json").read_text(encoding="utf-8"))
    assert data.get("sector") == "Semiconductors"


def test_generated_json_includes_geography(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)])
    data = json.loads((out_dir / "ASML.json").read_text(encoding="utf-8"))
    assert isinstance(data.get("geography"), list)
    assert "Netherlands" in data["geography"]


def test_generated_json_includes_revenue_drivers(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)])
    data = json.loads((out_dir / "ASML.json").read_text(encoding="utf-8"))
    assert isinstance(data.get("revenue_drivers"), list)
    assert len(data["revenue_drivers"]) >= 1


def test_generated_json_includes_key_risks(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)])
    data = json.loads((out_dir / "ASML.json").read_text(encoding="utf-8"))
    assert isinstance(data.get("key_risks"), list)
    assert len(data["key_risks"]) >= 1


def test_generated_json_includes_source_draft_id(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)])
    data = json.loads((out_dir / "ASML.json").read_text(encoding="utf-8"))
    assert data["source"]["draft_id"] == "draft-233-cf"


def test_generated_json_includes_source_description(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)])
    data = json.loads((out_dir / "ASML.json").read_text(encoding="utf-8"))
    assert "source_description" in data["source"]


# ---------------------------------------------------------------------------
# Blocking cases
# ---------------------------------------------------------------------------

def test_unconfirmed_draft_is_blocked(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.DRAFT)
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    result = runner.invoke(
        app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)]
    )
    assert result.exit_code != 0
    assert "Status: blocked" in result.output


def test_rejected_draft_is_blocked(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.REJECTED)
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    result = runner.invoke(
        app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)]
    )
    assert result.exit_code != 0
    assert "Status: blocked" in result.output


def test_wrong_snapshot_type_is_blocked(tmp_path):
    draft = _make_draft(
        snapshot_type=SnapshotType.RESEARCH_NOTES_SNAPSHOT,
        extracted_fields={"ticker": "ASML", "evidence_gaps": ["Gap."]},
        target_local_file="research_notes/ASML/notes.md",
    )
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    result = runner.invoke(
        app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)]
    )
    assert result.exit_code != 0
    assert "Status: blocked" in result.output


def test_missing_ticker_is_blocked(tmp_path):
    draft = _make_draft(
        extracted_fields={"company_name": "Unknown"},
        related_tickers=[],
    )
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    result = runner.invoke(
        app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)]
    )
    assert result.exit_code != 0
    assert "Status: blocked" in result.output


def test_unsafe_ticker_is_blocked(tmp_path):
    draft = _make_draft(extracted_fields={"ticker": "AS/ML", "company_name": "X"})
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    result = runner.invoke(
        app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)]
    )
    assert result.exit_code != 0
    assert "Status: blocked" in result.output


def test_missing_file_exits_nonzero(tmp_path):
    out_dir = tmp_path / "cf"
    result = runner.invoke(
        app, ["snapshot", "export-company-facts", "nonexistent.json", "--output-dir", str(out_dir)]
    )
    assert result.exit_code != 0


def test_invalid_json_exits_nonzero(tmp_path):
    src = tmp_path / "bad.json"
    out_dir = tmp_path / "cf"
    src.write_text("not json", encoding="utf-8")
    result = runner.invoke(
        app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)]
    )
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Overwrite behavior
# ---------------------------------------------------------------------------

def test_existing_file_not_overwritten_by_default(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    out_dir.mkdir()
    existing = out_dir / "ASML.json"
    existing.write_text("existing content", encoding="utf-8")
    _write_draft(src, draft)
    result = runner.invoke(
        app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)]
    )
    assert result.exit_code != 0
    assert existing.read_text(encoding="utf-8") == "existing content"


def test_overwrite_flag_replaces_existing(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    out_dir.mkdir()
    existing = out_dir / "ASML.json"
    existing.write_text("existing content", encoding="utf-8")
    _write_draft(src, draft)
    result = runner.invoke(
        app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir), "--overwrite"]
    )
    assert result.exit_code == 0
    assert existing.read_text(encoding="utf-8") != "existing content"


# ---------------------------------------------------------------------------
# File mutation safety
# ---------------------------------------------------------------------------

def test_draft_file_not_modified(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    before = src.read_text(encoding="utf-8")
    runner.invoke(app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)])
    assert src.read_text(encoding="utf-8") == before


def test_no_portfolio_files_written(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)])
    assert not (tmp_path / "portfolio.json").exists()
    assert not (tmp_path / "watchlist.json").exists()
    assert not (tmp_path / "decision_journal.json").exists()


def test_no_research_notes_written(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)])
    assert not (tmp_path / "research_notes").exists()


def test_only_ticker_json_written(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)])
    written = list(out_dir.iterdir())
    assert len(written) == 1
    assert written[0].name == "ASML.json"


# ---------------------------------------------------------------------------
# Weekly Review detection
# ---------------------------------------------------------------------------

def test_weekly_review_detects_exported_company_facts(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)])

    portfolio = Path("examples/weekly_review/portfolio.json")
    watchlist = Path("examples/weekly_review/watchlist.json")
    if not portfolio.exists() or not watchlist.exists():
        pytest.skip("weekly review examples not found")

    result = runner.invoke(app, [
        "weekly-review",
        "--portfolio", str(portfolio),
        "--watchlist", str(watchlist),
        "--company-facts", str(out_dir),
    ])
    assert result.exit_code == 0
    assert "company facts" in result.output.lower() or "Available" in result.output


def test_weekly_review_section8_no_longer_flags_asml_facts_missing(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)])

    portfolio = Path("examples/weekly_review/portfolio.json")
    watchlist = Path("examples/weekly_review/watchlist.json")
    if not portfolio.exists() or not watchlist.exists():
        pytest.skip("weekly review examples not found")

    result = runner.invoke(app, [
        "weekly-review",
        "--portfolio", str(portfolio),
        "--watchlist", str(watchlist),
        "--company-facts", str(out_dir),
    ])
    # ASML company facts present — Section 8 should not flag ASML facts as missing
    # (MSFT, NOVO, XYL may still be flagged)
    output = result.output
    lines = [l for l in output.splitlines() if "ASML" in l and "company facts" in l.lower()]
    assert len(lines) == 0


# ---------------------------------------------------------------------------
# Language guardrails
# ---------------------------------------------------------------------------

def test_success_render_no_forbidden_language():
    output = render_company_facts_export_success("ASML", "/tmp/cf/ASML.json")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output


def test_blocked_render_no_forbidden_language():
    output = render_company_facts_export_blocked("Draft is not confirmed.")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output


def test_generated_json_no_forbidden_language(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    runner.invoke(app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)])
    content = (out_dir / "ASML.json").read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in content


def test_cli_output_no_forbidden_language(tmp_path):
    draft = _make_draft()
    src = tmp_path / "draft.json"
    out_dir = tmp_path / "cf"
    _write_draft(src, draft)
    result = runner.invoke(
        app, ["snapshot", "export-company-facts", str(src), "--output-dir", str(out_dir)]
    )
    for term in FORBIDDEN_LANGUAGE:
        assert term not in result.output


def test_example_draft_json_no_forbidden_language():
    if not CONFIRMED_DRAFT.exists():
        pytest.skip("example draft not found")
    content = CONFIRMED_DRAFT.read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in content


# ---------------------------------------------------------------------------
# Provider / network boundary
# ---------------------------------------------------------------------------

def test_no_provider_imports_in_export_company_facts_module():
    import atlas.snapshot_input.export_company_facts as mod
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
# Unit-level export_company_facts
# ---------------------------------------------------------------------------

def test_unit_export_returns_success(tmp_path):
    draft = _make_draft()
    out_dir = tmp_path / "cf"
    result = export_company_facts(draft, out_dir)
    assert isinstance(result, CompanyFactsExportResult)
    assert result.success is True
    assert result.ticker == "ASML"
    assert result.output_path == out_dir / "ASML.json"


def test_unit_wrong_type_returns_failure(tmp_path):
    draft = _make_draft(
        snapshot_type=SnapshotType.RESEARCH_NOTES_SNAPSHOT,
        extracted_fields={"ticker": "ASML"},
        target_local_file="notes.md",
    )
    result = export_company_facts(draft, tmp_path / "cf")
    assert result.success is False
    assert "company_facts_snapshot" in result.reason


def test_unit_unconfirmed_returns_failure(tmp_path):
    draft = _make_draft(confirmation_status=SnapshotConfirmationStatus.DRAFT)
    result = export_company_facts(draft, tmp_path / "cf")
    assert result.success is False
    assert "confirmed" in result.reason.lower()


def test_unit_collision_no_overwrite_returns_failure(tmp_path):
    draft = _make_draft()
    out_dir = tmp_path / "cf"
    out_dir.mkdir()
    (out_dir / "ASML.json").write_text("existing", encoding="utf-8")
    result = export_company_facts(draft, out_dir, overwrite=False)
    assert result.success is False
    assert "already exists" in result.reason.lower() or "overwrite" in result.reason.lower()


def test_unit_collision_with_overwrite_succeeds(tmp_path):
    draft = _make_draft()
    out_dir = tmp_path / "cf"
    out_dir.mkdir()
    (out_dir / "ASML.json").write_text("existing", encoding="utf-8")
    result = export_company_facts(draft, out_dir, overwrite=True)
    assert result.success is True


# ---------------------------------------------------------------------------
# Regression — other commands still work
# ---------------------------------------------------------------------------

def test_snapshot_validate_still_works():
    result = runner.invoke(app, ["snapshot", "validate",
                                  "examples/snapshot_drafts/research_notes_snapshot_confirmed.json"])
    assert result.exit_code == 0


def test_snapshot_review_still_works():
    result = runner.invoke(app, ["snapshot", "review",
                                  "examples/snapshot_drafts/research_notes_snapshot_confirmed.json"])
    assert result.exit_code == 0


def test_export_research_notes_still_works(tmp_path):
    result = runner.invoke(app, [
        "snapshot", "export-research-notes",
        "examples/snapshot_drafts/research_notes_snapshot_confirmed.json",
        "--output-dir", str(tmp_path),
    ])
    assert result.exit_code == 0
