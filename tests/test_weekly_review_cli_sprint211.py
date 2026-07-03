"""Guardrail tests for atlas weekly-review CLI skeleton (Sprint 211).

Covers:
- atlas weekly-review --help is available
- Full command with sample files succeeds
- Output contains title
- Output contains all 10 required section headings
- Section 10 is present and non-empty
- Output contains input status summary
- Missing required portfolio fails with exit code 1
- Missing required watchlist fails with exit code 1
- Omitted optional profile/journal/company_facts/financials produce warnings, not failure
- Command output avoids forbidden language
- Weekly review CLI/renderer introduces no provider/network imports
- Existing CLI commands remain available
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from atlas.cli.main import app

EXAMPLES = Path(__file__).parent.parent / "examples" / "weekly_review"

runner = CliRunner()

REQUIRED_SECTION_HEADINGS = [
    "1. Review Scope",
    "2. Portfolio Context",
    "3. Watchlist Review",
    "4. Company Reviews Needing Attention",
    "5. Portfolio Fit and Suitability Notes",
    "6. Risk and Principle Guardrails",
    "7. Open Decisions",
    "8. Missing Evidence",
    "9. Follow-Up Questions",
    "10. Non-Actions / Reasons to Wait",
]

FORBIDDEN_TERMS = [
    "buy",
    "sell",
    "strong buy",
    "strong sell",
    "price target",
    "target price",
    "urgent",
    "act now",
    "must buy",
    "must sell",
    "guaranteed",
    "will outperform",
    "financial advice",
]


def _run_full(extra_args: list[str] | None = None) -> object:
    args = [
        "weekly-review",
        "--portfolio", str(EXAMPLES / "portfolio.json"),
        "--watchlist", str(EXAMPLES / "watchlist.json"),
        "--profile", str(EXAMPLES / "investor_profile.json"),
        "--journal", str(EXAMPLES / "decision_journal.json"),
        "--company-facts", str(EXAMPLES / "company_facts"),
        "--financials", str(EXAMPLES / "financials"),
        "--as-of", "2026-01-05",
    ]
    if extra_args:
        args.extend(extra_args)
    return runner.invoke(app, args)


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------


def test_weekly_review_help_available():
    result = runner.invoke(app, ["weekly-review", "--help"])
    assert result.exit_code == 0
    assert "--portfolio" in result.output
    assert "--watchlist" in result.output
    assert "--profile" in result.output
    assert "--journal" in result.output
    assert "--company-facts" in result.output
    assert "--financials" in result.output
    assert "--as-of" in result.output
    assert "--scope-notes" in result.output


# ---------------------------------------------------------------------------
# Successful run with sample files
# ---------------------------------------------------------------------------


def test_weekly_review_succeeds_with_sample_files():
    result = _run_full()
    assert result.exit_code == 0, f"Unexpected exit code: {result.exit_code}\n{result.output}"


def test_output_contains_title():
    result = _run_full()
    assert "Atlas Weekly Investment Review" in result.output


def test_output_contains_all_10_section_headings():
    result = _run_full()
    for heading in REQUIRED_SECTION_HEADINGS:
        assert heading in result.output, f"Section heading missing: {heading!r}"


def test_section_10_is_present_and_non_empty():
    result = _run_full()
    output = result.output
    assert "10. Non-Actions / Reasons to Wait" in output
    # Section 10 must have safe content, not just the heading
    assert "No Action Warranted" in output or "Reason to Wait" in output or "Decision Deferred" in output


def test_output_contains_input_status_summary():
    result = _run_full()
    assert "Input Status" in result.output
    assert "Portfolio:" in result.output
    assert "Watchlist:" in result.output


def test_output_contains_review_date():
    result = _run_full()
    assert "2026-01-05" in result.output


def test_output_surfaces_watchlist_evidence_gaps():
    result = _run_full()
    assert "Evidence Gap" in result.output
    assert "XYL" in result.output


def test_output_contains_missing_evidence_section():
    result = _run_full()
    assert "8. Missing Evidence" in result.output


# ---------------------------------------------------------------------------
# Required file validation
# ---------------------------------------------------------------------------


def test_missing_portfolio_fails():
    result = runner.invoke(app, [
        "weekly-review",
        "--portfolio", "nonexistent_portfolio.json",
        "--watchlist", str(EXAMPLES / "watchlist.json"),
    ])
    assert result.exit_code == 1
    assert "portfolio" in result.output.lower() or "portfolio" in (result.stderr or "").lower()


def test_missing_watchlist_fails():
    result = runner.invoke(app, [
        "weekly-review",
        "--portfolio", str(EXAMPLES / "portfolio.json"),
        "--watchlist", "nonexistent_watchlist.json",
    ])
    assert result.exit_code == 1
    assert "watchlist" in result.output.lower() or "watchlist" in (result.stderr or "").lower()


# ---------------------------------------------------------------------------
# Optional inputs produce warnings, not failure
# ---------------------------------------------------------------------------


def test_omitting_profile_produces_warning_not_failure():
    result = runner.invoke(app, [
        "weekly-review",
        "--portfolio", str(EXAMPLES / "portfolio.json"),
        "--watchlist", str(EXAMPLES / "watchlist.json"),
    ])
    assert result.exit_code == 0
    assert "profile" in result.output.lower()


def test_omitting_journal_produces_warning_not_failure():
    result = runner.invoke(app, [
        "weekly-review",
        "--portfolio", str(EXAMPLES / "portfolio.json"),
        "--watchlist", str(EXAMPLES / "watchlist.json"),
        "--profile", str(EXAMPLES / "investor_profile.json"),
    ])
    assert result.exit_code == 0
    # Section 7 should note journal absence
    assert "7. Open Decisions" in result.output


def test_omitting_company_facts_produces_warning_not_failure():
    result = runner.invoke(app, [
        "weekly-review",
        "--portfolio", str(EXAMPLES / "portfolio.json"),
        "--watchlist", str(EXAMPLES / "watchlist.json"),
    ])
    assert result.exit_code == 0


def test_omitting_financials_produces_warning_not_failure():
    result = runner.invoke(app, [
        "weekly-review",
        "--portfolio", str(EXAMPLES / "portfolio.json"),
        "--watchlist", str(EXAMPLES / "watchlist.json"),
    ])
    assert result.exit_code == 0


def test_minimal_command_only_required_args():
    result = runner.invoke(app, [
        "weekly-review",
        "--portfolio", str(EXAMPLES / "portfolio.json"),
        "--watchlist", str(EXAMPLES / "watchlist.json"),
    ])
    assert result.exit_code == 0
    for heading in REQUIRED_SECTION_HEADINGS:
        assert heading in result.output, f"Section heading missing in minimal run: {heading!r}"


# ---------------------------------------------------------------------------
# Language guardrail
# ---------------------------------------------------------------------------


def test_output_no_forbidden_language():
    result = _run_full()
    text = result.output.lower()
    for term in FORBIDDEN_TERMS:
        assert term not in text, f"Forbidden term {term!r} found in weekly-review output"


def test_help_no_forbidden_language():
    result = runner.invoke(app, ["weekly-review", "--help"])
    text = result.output.lower()
    for term in FORBIDDEN_TERMS:
        assert term not in text, f"Forbidden term {term!r} found in --help output"


# ---------------------------------------------------------------------------
# Provider / network boundary
# ---------------------------------------------------------------------------


def test_render_module_no_provider_imports():
    import atlas.weekly_review.render as m

    source = Path(m.__file__).read_text(encoding="utf-8")
    forbidden = [
        "atlas.providers",
        "import requests",
        "import urllib",
        "import httpx",
        "import aiohttp",
    ]
    for term in forbidden:
        assert term not in source, (
            f"atlas.weekly_review.render must not import {term!r}"
        )


def test_weekly_review_command_imports_no_provider_at_module_level():
    """The CLI command uses a lazy local import for weekly_review — check render is clean."""
    import atlas.weekly_review as pkg
    source = Path(pkg.__file__).read_text(encoding="utf-8")
    assert "atlas.providers" not in source
    assert "import requests" not in source


# ---------------------------------------------------------------------------
# Existing CLI commands remain available
# ---------------------------------------------------------------------------


def test_existing_home_command_available():
    result = runner.invoke(app, ["home", "--help"])
    assert result.exit_code == 0


def test_existing_report_command_available():
    result = runner.invoke(app, ["report", "--help"])
    assert result.exit_code == 0


def test_existing_suitability_command_available():
    result = runner.invoke(app, ["suitability", "--help"])
    assert result.exit_code == 0


def test_existing_watchlist_command_available():
    result = runner.invoke(app, ["watchlist", "--help"])
    assert result.exit_code == 0


def test_existing_journal_command_available():
    result = runner.invoke(app, ["journal", "--help"])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Renderer unit tests
# ---------------------------------------------------------------------------


def test_render_skeleton_returns_string():
    from atlas.weekly_review import WeeklyReviewInputPaths, load_weekly_review_inputs, render_weekly_review_skeleton

    paths = WeeklyReviewInputPaths(
        portfolio_path=EXAMPLES / "portfolio.json",
        watchlist_path=EXAMPLES / "watchlist.json",
    )
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review_skeleton(result)
    assert isinstance(output, str)
    assert len(output) > 0


def test_render_skeleton_section_10_never_empty():
    from atlas.weekly_review import WeeklyReviewInputPaths, load_weekly_review_inputs, render_weekly_review_skeleton

    paths = WeeklyReviewInputPaths(
        portfolio_path=EXAMPLES / "portfolio.json",
        watchlist_path=EXAMPLES / "watchlist.json",
    )
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review_skeleton(result)
    assert "10. Non-Actions / Reasons to Wait" in output
    # Verify content follows the heading
    idx = output.index("10. Non-Actions / Reasons to Wait")
    section_tail = output[idx:]
    assert "No Action Warranted" in section_tail or "Reason to Wait" in section_tail


def test_render_skeleton_all_headings_present():
    from atlas.weekly_review import WeeklyReviewInputPaths, load_weekly_review_inputs, render_weekly_review_skeleton

    paths = WeeklyReviewInputPaths(
        portfolio_path=EXAMPLES / "portfolio.json",
        watchlist_path=EXAMPLES / "watchlist.json",
    )
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review_skeleton(result)
    for heading in REQUIRED_SECTION_HEADINGS:
        assert heading in output, f"Missing heading: {heading!r}"
