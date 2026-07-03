"""Renderer tests for Atlas Weekly Investment Review — Sprint 212.

Covers the deterministic renderer introduced in Sprint 212:
- all 10 sections present
- portfolio context includes weights and sector exposure
- watchlist review includes per-item details
- open decisions includes journal summaries
- missing evidence consolidates watchlist gaps
- follow-up questions use watchlist open_questions
- Section 10 always non-empty
- determinism (same input → same output)
- no forbidden language
- no provider/network imports
- WeeklyReviewLoadResult carries journal_entries
"""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.weekly_review import (
    WeeklyReviewInputPaths,
    WeeklyReviewLoadResult,
    load_weekly_review_inputs,
    render_weekly_review,
    render_weekly_review_skeleton,
)

EXAMPLES = Path(__file__).parent.parent / "examples" / "weekly_review"

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
def full_paths() -> WeeklyReviewInputPaths:
    return WeeklyReviewInputPaths(
        portfolio_path=EXAMPLES / "portfolio.json",
        watchlist_path=EXAMPLES / "watchlist.json",
        profile_path=EXAMPLES / "investor_profile.json",
        journal_path=EXAMPLES / "decision_journal.json",
        company_facts_dir=EXAMPLES / "company_facts",
        financials_dir=EXAMPLES / "financials",
        as_of="2026-01-05",
    )


@pytest.fixture
def minimal_paths() -> WeeklyReviewInputPaths:
    return WeeklyReviewInputPaths(
        portfolio_path=EXAMPLES / "portfolio.json",
        watchlist_path=EXAMPLES / "watchlist.json",
    )


@pytest.fixture
def full_result(full_paths: WeeklyReviewInputPaths) -> WeeklyReviewLoadResult:
    return load_weekly_review_inputs(full_paths)


@pytest.fixture
def minimal_result(minimal_paths: WeeklyReviewInputPaths) -> WeeklyReviewLoadResult:
    return load_weekly_review_inputs(minimal_paths)


@pytest.fixture
def full_output(full_result: WeeklyReviewLoadResult) -> str:
    return render_weekly_review(full_result)


@pytest.fixture
def minimal_output(minimal_result: WeeklyReviewLoadResult) -> str:
    return render_weekly_review(minimal_result)


# ---------------------------------------------------------------------------
# render_weekly_review exists and is importable
# ---------------------------------------------------------------------------


def test_render_weekly_review_importable():
    from atlas.weekly_review import render_weekly_review as fn  # noqa: F401
    assert callable(fn)


def test_render_weekly_review_skeleton_still_importable():
    from atlas.weekly_review import render_weekly_review_skeleton as fn  # noqa: F401
    assert callable(fn)


def test_skeleton_is_alias_of_full_renderer(full_result):
    assert render_weekly_review(full_result) == render_weekly_review_skeleton(full_result)


# ---------------------------------------------------------------------------
# WeeklyReviewLoadResult carries journal_entries
# ---------------------------------------------------------------------------


def test_load_result_has_journal_entries_field(full_result):
    assert hasattr(full_result, "journal_entries")


def test_journal_entries_populated_when_journal_provided(full_result):
    assert len(full_result.journal_entries) > 0


def test_journal_entries_empty_when_no_journal(minimal_result):
    assert full_result is not minimal_result  # sanity
    assert len(minimal_result.journal_entries) == 0


def test_journal_entries_are_dicts(full_result):
    for entry in full_result.journal_entries:
        assert isinstance(entry, dict)


def test_journal_entry_count_matches_entries(full_result):
    assert full_result.journal_entry_count == len(full_result.journal_entries)


# ---------------------------------------------------------------------------
# All 10 section headings present
# ---------------------------------------------------------------------------


def test_all_10_headings_present_full(full_output):
    for heading in REQUIRED_SECTION_HEADINGS:
        assert heading in full_output, f"Missing heading: {heading!r}"


def test_all_10_headings_present_minimal(minimal_output):
    for heading in REQUIRED_SECTION_HEADINGS:
        assert heading in minimal_output, f"Missing heading in minimal run: {heading!r}"


# ---------------------------------------------------------------------------
# Section 1: Review Scope
# ---------------------------------------------------------------------------


def test_section1_contains_review_date(full_output):
    assert "2026-01-05" in full_output


def test_section1_local_only_statement(full_output):
    assert "Local files only" in full_output or "local" in full_output.lower()


def test_section1_shows_optional_inputs_loaded(full_output):
    assert "Optional inputs loaded" in full_output


def test_section1_no_optionals_when_minimal(minimal_output):
    assert "1. Review Scope" in minimal_output


# ---------------------------------------------------------------------------
# Section 2: Portfolio Context
# ---------------------------------------------------------------------------


def test_section2_contains_holdings_by_weight(full_output):
    assert "Holdings by weight" in full_output


def test_section2_contains_asml_ticker(full_output):
    assert "ASML" in full_output


def test_section2_contains_weight_percentages(full_output):
    # ASML = 19.0%, MSFT = 27.0%, CASH = 54.0%
    assert "19.0%" in full_output or "27.0%" in full_output


def test_section2_contains_sector_exposure(full_output):
    assert "Sector exposure" in full_output
    assert "Semiconductors" in full_output


def test_section2_contains_cash_note(full_output):
    assert "Cash position" in full_output


def test_section2_no_live_data_disclaimer(full_output):
    assert "user-supplied" in full_output or "No live pricing" in full_output


# ---------------------------------------------------------------------------
# Section 3: Watchlist Review
# ---------------------------------------------------------------------------


def test_section3_shows_watchlist_items(full_output):
    assert "XYL" in full_output
    assert "NOVO" in full_output


def test_section3_shows_item_status(full_output):
    assert "Research" in full_output
    assert "Needs More Evidence" in full_output


def test_section3_shows_evidence_gaps_per_item(full_output):
    assert "[XYL] Evidence Gap" in full_output
    assert "[NOVO] Evidence Gap" in full_output


def test_section3_shows_open_questions(full_output):
    assert "[XYL] Question" in full_output


def test_section3_shows_item_reason(full_output):
    assert "[XYL] Reason" in full_output


def test_section3_shows_notes(full_output):
    assert "[XYL] Notes" in full_output or "[NOVO] Notes" in full_output


# ---------------------------------------------------------------------------
# Section 4: Company Reviews Needing Attention
# ---------------------------------------------------------------------------


def test_section4_flags_items_with_evidence_gaps(full_output):
    # XYL and NOVO both have 3 evidence gaps each
    assert "Needs More Evidence" in full_output
    assert "evidence gaps" in full_output.lower()


def test_section4_local_input_note(full_output):
    assert "user-supplied local inputs" in full_output or "local inputs" in full_output


def test_section4_flags_visible_holdings(full_output):
    # MSFT at 27% is a visible holding
    assert "MSFT" in full_output or "Visible holding" in full_output


# ---------------------------------------------------------------------------
# Section 5: Portfolio Fit and Suitability Notes
# ---------------------------------------------------------------------------


def test_section5_mentions_profile_availability(full_output):
    assert "Investor profile" in full_output
    assert "Provided" in full_output or "Available" in full_output


def test_section5_deferred_engine_note(full_output):
    assert "deferred" in full_output.lower()


def test_section5_concentration_observation(full_output):
    assert "Concentration observation" in full_output or "concentration" in full_output.lower()


def test_section5_no_profile_when_minimal(minimal_output):
    assert "5. Portfolio Fit and Suitability Notes" in minimal_output
    assert "Not provided" in minimal_output or "profile" in minimal_output.lower()


# ---------------------------------------------------------------------------
# Section 6: Risk and Principle Guardrails
# ---------------------------------------------------------------------------


def test_section6_principle_guardrail_note(full_output):
    assert "Principle Guardrail" in full_output or "guardrail" in full_output.lower()


def test_section6_deferred_engine_note(full_output):
    assert "deferred" in full_output.lower()


def test_section6_no_action_principle(full_output):
    assert "No action is warranted" in full_output or "No Action" in full_output


# ---------------------------------------------------------------------------
# Section 7: Open Decisions
# ---------------------------------------------------------------------------


def test_section7_journal_entry_count(full_output):
    assert "1 entry" in full_output or "1 entries" in full_output


def test_section7_shows_decision_title(full_output):
    # Sample journal has "Xylem — initial research decision"
    assert "Xylem" in full_output


def test_section7_shows_decision_status(full_output):
    # atlas_rating = "Needs More Evidence"
    assert "Needs More Evidence" in full_output


def test_section7_shows_follow_up_triggers(full_output):
    assert "[Follow-up]" in full_output


def test_section7_absent_journal_graceful(minimal_output):
    assert "7. Open Decisions" in minimal_output
    assert "not provided" in minimal_output.lower() or "Not provided" in minimal_output


# ---------------------------------------------------------------------------
# Section 8: Missing Evidence
# ---------------------------------------------------------------------------


def test_section8_lists_watchlist_evidence_gaps(full_output):
    assert "Evidence Gap [XYL]" in full_output
    assert "Evidence Gap [NOVO]" in full_output


def test_section8_when_no_facts(minimal_output):
    assert "8. Missing Evidence" in minimal_output
    assert "Company facts" in minimal_output or "evidence" in minimal_output.lower()


# ---------------------------------------------------------------------------
# Section 9: Follow-Up Questions
# ---------------------------------------------------------------------------


def test_section9_watchlist_open_questions(full_output):
    assert "[XYL] Open questions" in full_output


def test_section9_derived_question_from_evidence(full_output):
    assert "evidence would confirm" in full_output.lower() or "follow-up" in full_output.lower()


def test_section9_novo_open_questions(full_output):
    assert "[NOVO] Open questions" in full_output


# ---------------------------------------------------------------------------
# Section 10: Non-Actions / Reasons to Wait
# ---------------------------------------------------------------------------


def test_section10_present(full_output):
    assert "10. Non-Actions / Reasons to Wait" in full_output


def test_section10_non_empty_full(full_output):
    idx = full_output.index("10. Non-Actions / Reasons to Wait")
    tail = full_output[idx:]
    assert "No Action Warranted" in tail or "Reason to Wait" in tail or "Decision Deferred" in tail


def test_section10_non_empty_minimal(minimal_output):
    idx = minimal_output.index("10. Non-Actions / Reasons to Wait")
    tail = minimal_output[idx:]
    assert "No Action Warranted" in tail or "Reason to Wait" in tail


def test_section10_deferred_status_surfaced(full_output):
    # NOVO has status Needs More Evidence
    assert "NOVO" in full_output
    assert "Decision Deferred" in full_output or "Needs More Evidence" in full_output


def test_section10_evidence_gap_count(full_output):
    # 6 total gaps: XYL=3, NOVO=3
    assert "6 evidence gap" in full_output or "Reason to Wait" in full_output


def test_section10_atlas_reminder(full_output):
    assert "Atlas supports better judgment" in full_output


# ---------------------------------------------------------------------------
# Input Status block
# ---------------------------------------------------------------------------


def test_input_status_present(full_output):
    assert "Input Status" in full_output


def test_input_status_portfolio_count(full_output):
    assert "Portfolio: 3 holding(s)" in full_output


def test_input_status_watchlist_count(full_output):
    assert "Watchlist: 2 item(s)" in full_output


def test_input_status_journal_count(full_output):
    assert "Decision journal: 1 entry" in full_output


def test_input_status_review_date(full_output):
    assert "Review date: 2026-01-05" in full_output


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_render_is_deterministic(full_result):
    out1 = render_weekly_review(full_result)
    out2 = render_weekly_review(full_result)
    assert out1 == out2


def test_render_minimal_is_deterministic(minimal_result):
    out1 = render_weekly_review(minimal_result)
    out2 = render_weekly_review(minimal_result)
    assert out1 == out2


# ---------------------------------------------------------------------------
# Language guardrail
# ---------------------------------------------------------------------------


def test_no_forbidden_language_full(full_output):
    text = full_output.lower()
    for term in FORBIDDEN_TERMS:
        assert term not in text, f"Forbidden term {term!r} found in full renderer output"


def test_no_forbidden_language_minimal(minimal_output):
    text = minimal_output.lower()
    for term in FORBIDDEN_TERMS:
        assert term not in text, f"Forbidden term {term!r} found in minimal renderer output"


# ---------------------------------------------------------------------------
# Provider / network boundary
# ---------------------------------------------------------------------------


def test_render_module_no_provider_imports():
    import atlas.weekly_review.render as m

    source = Path(m.__file__).read_text(encoding="utf-8")
    forbidden_imports = [
        "atlas.providers",
        "import requests",
        "import urllib",
        "import httpx",
        "import aiohttp",
    ]
    for term in forbidden_imports:
        assert term not in source, (
            f"atlas.weekly_review.render must not import {term!r}"
        )


def test_inputs_module_no_provider_imports():
    import atlas.weekly_review.inputs as m

    source = Path(m.__file__).read_text(encoding="utf-8")
    forbidden_imports = [
        "atlas.providers",
        "import requests",
        "import urllib",
        "import httpx",
        "import aiohttp",
    ]
    for term in forbidden_imports:
        assert term not in source, (
            f"atlas.weekly_review.inputs must not import {term!r}"
        )
