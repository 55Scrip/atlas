"""Sprint 213 trial tests — realistic Weekly Investment Review input bundle.

Covers:
- realistic trial bundle loads without error
- trial CLI command succeeds
- all 10 sections present
- realistic portfolio context (11 holdings, multiple sectors)
- profile principles/constraints rendered
- per-ticker company facts presence check
- per-ticker financials presence check
- combined concentration note
- watchlist varied statuses
- journal entries render with follow-up triggers
- Section 10 non-empty
- no forbidden language on realistic inputs
- no provider/network imports
- determinism on realistic inputs
- scope notes preview (not raw markdown dump)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.weekly_review import (
    WeeklyReviewInputPaths,
    WeeklyReviewLoadResult,
    load_weekly_review_inputs,
    render_weekly_review,
)

REALISTIC = Path(__file__).parent.parent / "examples" / "weekly_review_realistic"

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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def realistic_paths() -> WeeklyReviewInputPaths:
    scope_notes_text = (REALISTIC / "scope_notes.md").read_text(encoding="utf-8")
    return WeeklyReviewInputPaths(
        portfolio_path=REALISTIC / "portfolio.json",
        watchlist_path=REALISTIC / "watchlist.json",
        profile_path=REALISTIC / "investor_profile.json",
        journal_path=REALISTIC / "decision_journal.json",
        company_facts_dir=REALISTIC / "company_facts",
        financials_dir=REALISTIC / "financials",
        as_of="2026-01-03",
        scope_notes=scope_notes_text,
    )


@pytest.fixture
def realistic_result(realistic_paths: WeeklyReviewInputPaths) -> WeeklyReviewLoadResult:
    return load_weekly_review_inputs(realistic_paths)


@pytest.fixture
def realistic_output(realistic_result: WeeklyReviewLoadResult) -> str:
    return render_weekly_review(realistic_result)


# ---------------------------------------------------------------------------
# Trial bundle loads without error
# ---------------------------------------------------------------------------


def test_realistic_bundle_loads(realistic_result):
    assert realistic_result is not None


def test_realistic_portfolio_11_holdings(realistic_result):
    assert len(realistic_result.portfolio.all_holdings) == 11


def test_realistic_watchlist_5_items(realistic_result):
    assert len(realistic_result.watchlist.items) == 5


def test_realistic_journal_4_entries(realistic_result):
    assert realistic_result.journal_entry_count == 4
    assert len(realistic_result.journal_entries) == 4


def test_realistic_profile_available(realistic_result):
    assert realistic_result.profile_available is True


def test_realistic_company_facts_available(realistic_result):
    assert realistic_result.company_facts_available is True


def test_realistic_financials_available(realistic_result):
    assert realistic_result.financials_available is True


# ---------------------------------------------------------------------------
# Profile principles and constraints loaded
# ---------------------------------------------------------------------------


def test_profile_principles_loaded(realistic_result):
    assert len(realistic_result.profile_principles) >= 5


def test_profile_constraints_loaded(realistic_result):
    assert len(realistic_result.profile_constraints) >= 3


def test_profile_risk_tolerance_loaded(realistic_result):
    assert realistic_result.profile_risk_tolerance != ""
    assert "balanced" in realistic_result.profile_risk_tolerance.lower()


def test_profile_time_horizon_loaded(realistic_result):
    assert realistic_result.profile_time_horizon != ""
    assert "year" in realistic_result.profile_time_horizon.lower()


def test_profile_principles_no_forbidden_language(realistic_result):
    for principle in realistic_result.profile_principles:
        for term in FORBIDDEN_TERMS:
            assert term not in principle.lower(), (
                f"Forbidden term {term!r} in principle: {principle!r}"
            )


def test_profile_constraints_no_forbidden_language(realistic_result):
    for constraint in realistic_result.profile_constraints:
        for term in FORBIDDEN_TERMS:
            assert term not in constraint.lower(), (
                f"Forbidden term {term!r} in constraint: {constraint!r}"
            )


# ---------------------------------------------------------------------------
# Per-ticker company facts presence check
# ---------------------------------------------------------------------------


def test_tickers_missing_facts_populated(realistic_result):
    # ASML, NOVO, MSFT have facts; others don't
    assert len(realistic_result.tickers_missing_facts) > 0


def test_tickers_present_in_facts_not_in_missing(realistic_result):
    # ASML, NOVO, MSFT have company_facts files
    for ticker in ("ASML", "NOVO", "MSFT"):
        assert ticker not in realistic_result.tickers_missing_facts


def test_tickers_without_facts_listed(realistic_result):
    # LVMH does not have a company_facts file
    assert "LVMH" in realistic_result.tickers_missing_facts


def test_casheur_excluded_from_missing_facts(realistic_result):
    # Cash holdings should be excluded from the check
    assert "CASHEUR" not in realistic_result.tickers_missing_facts


# ---------------------------------------------------------------------------
# Per-ticker financials presence check
# ---------------------------------------------------------------------------


def test_tickers_missing_financials_populated(realistic_result):
    # ASML, NOVO, MSFT have financials; others don't
    assert len(realistic_result.tickers_missing_financials) > 0


def test_tickers_present_in_financials_not_in_missing(realistic_result):
    for ticker in ("ASML", "NOVO", "MSFT"):
        assert ticker not in realistic_result.tickers_missing_financials


def test_tickers_without_financials_listed(realistic_result):
    assert "LVMH" in realistic_result.tickers_missing_financials


def test_casheur_excluded_from_missing_financials(realistic_result):
    assert "CASHEUR" not in realistic_result.tickers_missing_financials


# ---------------------------------------------------------------------------
# Renderer: all 10 sections
# ---------------------------------------------------------------------------


def test_all_10_sections_present(realistic_output):
    for heading in REQUIRED_SECTION_HEADINGS:
        assert heading in realistic_output, f"Missing section: {heading!r}"


# ---------------------------------------------------------------------------
# Renderer: Section 2 — Portfolio Context
# ---------------------------------------------------------------------------


def test_section2_shows_asml_weight(realistic_output):
    assert "ASML" in realistic_output
    assert "24.0%" in realistic_output


def test_section2_shows_multiple_sectors(realistic_output):
    for sector in ("Semiconductors", "Healthcare", "Technology", "Consumer Discretionary"):
        assert sector in realistic_output


def test_section2_combined_concentration_note(realistic_output):
    assert "Combined concentration" in realistic_output
    assert "ASML + NOVO" in realistic_output
    assert "45.0%" in realistic_output


def test_section2_unclassified_neste(realistic_output):
    assert "Unclassified" in realistic_output
    assert "NESTE" in realistic_output


# ---------------------------------------------------------------------------
# Renderer: Section 3 — Watchlist Review
# ---------------------------------------------------------------------------


def test_section3_all_5_watchlist_tickers(realistic_output):
    for ticker in ("XYL", "ADYEN", "RCKWB", "VEEV", "DXCM"):
        assert ticker in realistic_output


def test_section3_varied_statuses(realistic_output):
    assert "Research" in realistic_output
    assert "Needs More Evidence" in realistic_output
    assert "Watchlist" in realistic_output
    assert "Suitable for Further Review" in realistic_output
    assert "Decision Deferred" in realistic_output


def test_section3_evidence_gaps(realistic_output):
    assert "[XYL] Evidence Gap" in realistic_output
    assert "[ADYEN] Evidence Gap" in realistic_output


# ---------------------------------------------------------------------------
# Renderer: Section 5 — Suitability (profile fields)
# ---------------------------------------------------------------------------


def test_section5_risk_tolerance_rendered(realistic_output):
    assert "Risk tolerance" in realistic_output
    assert "Balanced" in realistic_output


def test_section5_time_horizon_rendered(realistic_output):
    assert "Time horizon" in realistic_output
    assert "7-10 years" in realistic_output


def test_section5_constraints_rendered(realistic_output):
    assert "Stated constraints" in realistic_output
    assert "Constraint:" in realistic_output


# ---------------------------------------------------------------------------
# Renderer: Section 6 — Guardrails (principles)
# ---------------------------------------------------------------------------


def test_section6_principles_rendered(realistic_output):
    assert "Stated principles" in realistic_output
    assert "Principle:" in realistic_output


def test_section6_at_least_one_principle_text(realistic_output):
    # Check that a key principle text appears
    assert "Evidence before opinion" in realistic_output


# ---------------------------------------------------------------------------
# Renderer: Section 7 — Open Decisions
# ---------------------------------------------------------------------------


def test_section7_4_journal_entries(realistic_output):
    assert "4 entry/entries reviewed" in realistic_output


def test_section7_lvmh_entry(realistic_output):
    assert "LVMH" in realistic_output


def test_section7_msft_no_action(realistic_output):
    assert "No Action Warranted" in realistic_output


def test_section7_adyen_deferred(realistic_output):
    assert "Needs More Evidence" in realistic_output


def test_section7_follow_up_triggers(realistic_output):
    assert "[Follow-up]" in realistic_output


# ---------------------------------------------------------------------------
# Renderer: Section 8 — Missing Evidence
# ---------------------------------------------------------------------------


def test_section8_watchlist_gaps(realistic_output):
    assert "Evidence Gap [XYL]" in realistic_output
    assert "Evidence Gap [ADYEN]" in realistic_output


def test_section8_missing_company_facts_compact(realistic_output):
    assert "Missing company facts for:" in realistic_output
    assert "LVMH" in realistic_output  # LVMH is in the missing list


def test_section8_missing_financials_compact(realistic_output):
    assert "Missing financial history for:" in realistic_output


# ---------------------------------------------------------------------------
# Renderer: Section 10 — Non-Actions
# ---------------------------------------------------------------------------


def test_section10_non_empty(realistic_output):
    idx = realistic_output.index("10. Non-Actions / Reasons to Wait")
    tail = realistic_output[idx:]
    assert "No Action Warranted" in tail or "Reason to Wait" in tail or "Decision Deferred" in tail


def test_section10_evidence_gap_count(realistic_output):
    assert "Reason to Wait" in realistic_output
    assert "evidence gap" in realistic_output.lower()


def test_section10_missing_facts_reason(realistic_output):
    assert "Company facts missing" in realistic_output or "Reason to Wait" in realistic_output


def test_section10_atlas_reminder(realistic_output):
    assert "Atlas supports better judgment" in realistic_output


# ---------------------------------------------------------------------------
# Scope notes preview
# ---------------------------------------------------------------------------


def test_scope_notes_preview_no_raw_markdown(realistic_output):
    # Raw markdown headers like "# Title" or "## Section" should not appear
    assert "## Focus areas" not in realistic_output
    assert "## What would change" not in realistic_output


def test_scope_notes_preview_contains_line_count(realistic_output):
    # Preview should show line count when truncated
    assert "lines]" in realistic_output or "line]" in realistic_output


# ---------------------------------------------------------------------------
# Forbidden language
# ---------------------------------------------------------------------------


def test_no_forbidden_language_realistic(realistic_output):
    text = realistic_output.lower()
    for term in FORBIDDEN_TERMS:
        assert term not in text, f"Forbidden term {term!r} found in realistic trial output"


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_realistic_output_is_deterministic(realistic_result):
    out1 = render_weekly_review(realistic_result)
    out2 = render_weekly_review(realistic_result)
    assert out1 == out2


# ---------------------------------------------------------------------------
# Provider boundary
# ---------------------------------------------------------------------------


def test_render_module_no_provider_imports():
    import atlas.weekly_review.render as m
    source = Path(m.__file__).read_text(encoding="utf-8")
    for term in ["atlas.providers", "import requests", "import urllib", "import httpx", "import aiohttp"]:
        assert term not in source


def test_inputs_module_no_provider_imports():
    import atlas.weekly_review.inputs as m
    source = Path(m.__file__).read_text(encoding="utf-8")
    for term in ["atlas.providers", "import requests", "import urllib", "import httpx", "import aiohttp"]:
        assert term not in source


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


def test_realistic_cli_command_succeeds():
    from typer.testing import CliRunner
    from atlas.cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, [
        "weekly-review",
        "--portfolio", str(REALISTIC / "portfolio.json"),
        "--watchlist", str(REALISTIC / "watchlist.json"),
        "--profile", str(REALISTIC / "investor_profile.json"),
        "--journal", str(REALISTIC / "decision_journal.json"),
        "--company-facts", str(REALISTIC / "company_facts"),
        "--financials", str(REALISTIC / "financials"),
        "--as-of", "2026-01-03",
    ])
    assert result.exit_code == 0, f"CLI failed:\n{result.output}"


def test_realistic_cli_output_all_sections():
    from typer.testing import CliRunner
    from atlas.cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, [
        "weekly-review",
        "--portfolio", str(REALISTIC / "portfolio.json"),
        "--watchlist", str(REALISTIC / "watchlist.json"),
        "--as-of", "2026-01-03",
    ])
    assert result.exit_code == 0
    for heading in REQUIRED_SECTION_HEADINGS:
        assert heading in result.output
