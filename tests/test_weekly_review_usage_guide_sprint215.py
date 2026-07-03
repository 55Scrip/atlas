"""Sprint 215 — Usage guide existence and content guardrail tests.

Checks:
- docs/AtlasWeeklyReviewUsageGuide.md exists
- guide references atlas weekly-review command
- guide references required files (portfolio.json, watchlist.json)
- guide references all 10 section headings
- guide avoids forbidden language
- referenced example files exist in the repository
- README points to usage guide
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
GUIDE = REPO_ROOT / "docs" / "AtlasWeeklyReviewUsageGuide.md"
README = REPO_ROOT / "README.md"

FORBIDDEN_TERMS = [
    "buy", "sell", "strong buy", "strong sell", "price target", "target price",
    "urgent", "act now", "must buy", "must sell", "guaranteed", "will outperform",
    "financial advice",
]

REQUIRED_SECTION_HEADINGS = [
    "Review Scope",
    "Portfolio Context",
    "Watchlist Review",
    "Company Reviews Needing Attention",
    "Portfolio Fit and Suitability Notes",
    "Risk and Principle Guardrails",
    "Open Decisions",
    "Missing Evidence",
    "Follow-Up Questions",
    "Non-Actions / Reasons to Wait",
]


@pytest.fixture(scope="module")
def guide_text() -> str:
    return GUIDE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def guide_lower(guide_text) -> str:
    return guide_text.lower()


# ---------------------------------------------------------------------------
# File existence
# ---------------------------------------------------------------------------


def test_usage_guide_exists():
    assert GUIDE.exists(), f"Usage guide not found at {GUIDE}"


def test_readme_exists():
    assert README.exists()


# ---------------------------------------------------------------------------
# Guide content
# ---------------------------------------------------------------------------


def test_guide_references_weekly_review_command(guide_text):
    assert "atlas weekly-review" in guide_text


def test_guide_references_portfolio_json(guide_text):
    assert "portfolio.json" in guide_text


def test_guide_references_watchlist_json(guide_text):
    assert "watchlist.json" in guide_text


def test_guide_references_investor_profile(guide_text):
    assert "investor_profile.json" in guide_text


def test_guide_references_decision_journal(guide_text):
    assert "decision_journal.json" in guide_text


def test_guide_references_company_facts(guide_text):
    assert "company_facts" in guide_text


def test_guide_references_financials(guide_text):
    assert "financials" in guide_text


def test_guide_references_all_10_sections(guide_text):
    for heading in REQUIRED_SECTION_HEADINGS:
        assert heading in guide_text, f"Usage guide missing section reference: {heading!r}"


def test_guide_references_as_of(guide_text):
    assert "--as-of" in guide_text


def test_guide_references_scope_notes(guide_text):
    assert "scope-notes" in guide_text or "scope_notes" in guide_text


def test_guide_references_aging(guide_text):
    assert "aging" in guide_text.lower() or "Aging" in guide_text


def test_guide_references_section10_philosophy(guide_text):
    assert "No action" in guide_text or "no action" in guide_text


def test_guide_references_limitations(guide_text):
    assert "limitation" in guide_text.lower()


def test_guide_references_no_live_data(guide_lower):
    assert "live" in guide_lower


def test_guide_references_no_recommendations(guide_lower):
    assert "recommendation" in guide_lower


# ---------------------------------------------------------------------------
# Forbidden language in guide
# ---------------------------------------------------------------------------


def test_guide_no_forbidden_language(guide_lower):
    for term in FORBIDDEN_TERMS:
        assert term not in guide_lower, f"Forbidden term {term!r} found in usage guide"


# ---------------------------------------------------------------------------
# Referenced example files exist
# ---------------------------------------------------------------------------


def test_example_weekly_review_portfolio_exists():
    assert (REPO_ROOT / "examples" / "weekly_review" / "portfolio.json").exists()


def test_example_weekly_review_watchlist_exists():
    assert (REPO_ROOT / "examples" / "weekly_review" / "watchlist.json").exists()


def test_example_weekly_review_realistic_portfolio_exists():
    assert (REPO_ROOT / "examples" / "weekly_review_realistic" / "portfolio.json").exists()


def test_example_weekly_review_realistic_watchlist_exists():
    assert (REPO_ROOT / "examples" / "weekly_review_realistic" / "watchlist.json").exists()


def test_example_weekly_review_realistic_company_facts_dir_exists():
    assert (REPO_ROOT / "examples" / "weekly_review_realistic" / "company_facts").is_dir()


def test_example_weekly_review_realistic_financials_dir_exists():
    assert (REPO_ROOT / "examples" / "weekly_review_realistic" / "financials").is_dir()


# ---------------------------------------------------------------------------
# README pointer
# ---------------------------------------------------------------------------


def test_readme_references_usage_guide():
    readme = README.read_text(encoding="utf-8")
    assert "AtlasWeeklyReviewUsageGuide" in readme


def test_readme_references_weekly_review():
    readme = README.read_text(encoding="utf-8")
    assert "weekly-review" in readme or "Weekly Review" in readme
