"""Guardrail tests for atlas.weekly_review input loading (Sprint 210).

Covers:
- Sample input bundle loads cleanly
- V1 extended portfolio format (accounts[].holdings[])
- Existing positions[] portfolio format
- Missing required portfolio file raises ValueError
- Missing required watchlist file raises ValueError
- Rich watchlist item fields are parsed correctly
- Missing watchlist status defaults to Watchlist with warning
- Missing sector defaults to Unclassified with warning
- Missing profile produces warning, not failure
- Missing optional journal / company_facts / financials produce warnings
- No provider or network imports in the weekly_review package
- Sample input files do not contain forbidden language
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.weekly_review import (
    WeeklyReviewInputPaths,
    WeeklyReviewPortfolioInput,
    WeeklyReviewWatchlistInput,
    WeeklyReviewWatchlistStatus,
    load_weekly_review_inputs,
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


# ---------------------------------------------------------------------------
# Sample file loading
# ---------------------------------------------------------------------------


def test_sample_portfolio_loads():
    portfolio, warnings = WeeklyReviewPortfolioInput.from_json_file(
        EXAMPLES / "portfolio.json"
    )
    assert len(portfolio.accounts) == 1
    holdings = portfolio.all_holdings
    tickers = {h.ticker for h in holdings}
    assert "ASML" in tickers
    assert "MSFT" in tickers
    assert "CASH" in tickers


def test_sample_watchlist_loads():
    watchlist, warnings = WeeklyReviewWatchlistInput.from_json_file(
        EXAMPLES / "watchlist.json"
    )
    assert watchlist.name == "Core Research Watchlist"
    tickers = {item.ticker for item in watchlist.items}
    assert "XYL" in tickers
    assert "NOVO" in tickers


def test_sample_input_bundle_loads():
    paths = WeeklyReviewInputPaths(
        portfolio_path=EXAMPLES / "portfolio.json",
        watchlist_path=EXAMPLES / "watchlist.json",
        profile_path=EXAMPLES / "investor_profile.json",
        journal_path=EXAMPLES / "decision_journal.json",
        company_facts_dir=EXAMPLES / "company_facts",
        financials_dir=EXAMPLES / "financials",
        as_of="2026-01-05",
        scope_notes="Q1 2026 review",
    )
    result = load_weekly_review_inputs(paths)
    assert result.portfolio is not None
    assert result.watchlist is not None
    assert result.profile_available is True
    assert result.journal_entry_count == 1
    assert result.company_facts_available is True
    assert result.financials_available is True
    assert result.as_of == "2026-01-05"
    assert result.scope_notes == "Q1 2026 review"
    # No unexpected errors in warnings (warnings are non-blocking only)
    assert all(w.code != "missing_optional_profile" for w in result.warnings)


# ---------------------------------------------------------------------------
# V1 extended portfolio format
# ---------------------------------------------------------------------------


def test_v1_extended_portfolio_accounts_format():
    payload = {
        "as_of": "2026-01-01",
        "accounts": [
            {
                "name": "Private",
                "holdings": [
                    {
                        "ticker": "ASML",
                        "name": "ASML Holding",
                        "sector": "Semiconductors",
                        "country": "Netherlands",
                        "currency": "EUR",
                        "market_value": 95000,
                        "cost_basis": 82000,
                        "quality_score": 85,
                        "risk_score": 40,
                        "role": "Core holding",
                    },
                    {
                        "ticker": "CASH",
                        "name": "Cash Reserve",
                        "sector": "Cash",
                        "market_value": 270000,
                        "quality_score": 100,
                        "risk_score": 0,
                    },
                ],
            }
        ],
    }
    portfolio, warnings = WeeklyReviewPortfolioInput.from_mapping(payload)
    assert len(portfolio.accounts) == 1
    assert portfolio.accounts[0].name == "Private"
    holdings = portfolio.all_holdings
    assert len(holdings) == 2
    asml = next(h for h in holdings if h.ticker == "ASML")
    assert asml.sector == "Semiconductors"
    assert asml.market_value == 95000
    # Weights should be derived from market_value proportionally
    total = 95000 + 270000
    assert abs(asml.weight - 95000 / total) < 1e-9


def test_v1_extended_portfolio_multiple_accounts():
    payload = {
        "accounts": [
            {
                "name": "ISK",
                "holdings": [
                    {
                        "ticker": "MSFT",
                        "name": "Microsoft",
                        "sector": "Technology",
                        "market_value": 50000,
                    }
                ],
            },
            {
                "name": "Private",
                "holdings": [
                    {
                        "ticker": "ASML",
                        "name": "ASML Holding",
                        "sector": "Semiconductors",
                        "market_value": 50000,
                    }
                ],
            },
        ]
    }
    portfolio, warnings = WeeklyReviewPortfolioInput.from_mapping(payload)
    assert len(portfolio.accounts) == 2
    all_tickers = {h.ticker for h in portfolio.all_holdings}
    assert all_tickers == {"MSFT", "ASML"}


# ---------------------------------------------------------------------------
# Existing positions[] format
# ---------------------------------------------------------------------------


def test_existing_positions_format_supported():
    payload = {
        "positions": [
            {
                "ticker": "NVDA",
                "company": "NVIDIA Corporation",
                "sector": "Semiconductors",
                "country": "USA",
                "market_cap": 2000000,
                "weight": 0.55,
                "quality_score": 88,
                "risk_score": 55,
            },
            {
                "ticker": "CASH",
                "company": "Cash",
                "sector": "Cash",
                "country": "USA",
                "market_cap": 0,
                "weight": 0.45,
                "quality_score": 100,
                "risk_score": 0,
            },
        ]
    }
    portfolio, warnings = WeeklyReviewPortfolioInput.from_mapping(payload)
    assert len(portfolio.accounts) == 1
    assert portfolio.accounts[0].name == "Portfolio"
    holdings = portfolio.all_holdings
    tickers = {h.ticker for h in holdings}
    assert tickers == {"NVDA", "CASH"}
    nvda = next(h for h in holdings if h.ticker == "NVDA")
    assert abs(nvda.weight - 0.55) < 1e-9


def test_positions_format_100_percent_weight_normalized():
    payload = {
        "positions": [
            {
                "ticker": "AAPL",
                "company": "Apple",
                "sector": "Technology",
                "weight": 60,  # provided as percentage
                "quality_score": 90,
                "risk_score": 30,
            }
        ]
    }
    portfolio, warnings = WeeklyReviewPortfolioInput.from_mapping(payload)
    aapl = portfolio.all_holdings[0]
    assert abs(aapl.weight - 0.60) < 1e-9


# ---------------------------------------------------------------------------
# Required file validation
# ---------------------------------------------------------------------------


def test_missing_required_portfolio_raises(tmp_path):
    paths = WeeklyReviewInputPaths(
        portfolio_path=tmp_path / "nonexistent_portfolio.json",
        watchlist_path=EXAMPLES / "watchlist.json",
    )
    with pytest.raises(ValueError, match="Required portfolio file not found"):
        load_weekly_review_inputs(paths)


def test_missing_required_watchlist_raises(tmp_path):
    paths = WeeklyReviewInputPaths(
        portfolio_path=EXAMPLES / "portfolio.json",
        watchlist_path=tmp_path / "nonexistent_watchlist.json",
    )
    with pytest.raises(ValueError, match="Required watchlist file not found"):
        load_weekly_review_inputs(paths)


def test_invalid_portfolio_structure_raises(tmp_path):
    bad_portfolio = tmp_path / "bad_portfolio.json"
    bad_portfolio.write_text(json.dumps({"name": "empty"}), encoding="utf-8")
    paths = WeeklyReviewInputPaths(
        portfolio_path=bad_portfolio,
        watchlist_path=EXAMPLES / "watchlist.json",
    )
    with pytest.raises(ValueError):
        load_weekly_review_inputs(paths)


def test_invalid_watchlist_structure_raises(tmp_path):
    bad_watchlist = tmp_path / "bad_watchlist.json"
    bad_watchlist.write_text(json.dumps({"name": "empty", "items": []}), encoding="utf-8")
    paths = WeeklyReviewInputPaths(
        portfolio_path=EXAMPLES / "portfolio.json",
        watchlist_path=bad_watchlist,
    )
    with pytest.raises(ValueError):
        load_weekly_review_inputs(paths)


# ---------------------------------------------------------------------------
# Rich watchlist parsing
# ---------------------------------------------------------------------------


def test_watchlist_rich_item_fields_parsed():
    payload = {
        "name": "My Watchlist",
        "items": [
            {
                "ticker": "XYL",
                "name": "Xylem",
                "status": "Research",
                "reason": "Water infrastructure theme",
                "evidence_needed": ["Margin durability", "Valuation context"],
                "open_questions": ["How durable is replacement demand?"],
                "manual_observations": ["No position currently."],
                "notes": "Reason to wait: evidence gap.",
            }
        ],
    }
    watchlist, warnings = WeeklyReviewWatchlistInput.from_mapping(payload)
    assert len(watchlist.items) == 1
    item = watchlist.items[0]
    assert item.ticker == "XYL"
    assert item.name == "Xylem"
    assert item.status == WeeklyReviewWatchlistStatus.RESEARCH
    assert "Margin durability" in item.evidence_needed
    assert "Valuation context" in item.evidence_needed
    assert len(item.open_questions) == 1
    assert len(item.manual_observations) == 1
    assert "Reason to wait" in item.notes


def test_watchlist_missing_status_defaults_to_watchlist_with_warning():
    payload = {
        "items": [
            {"ticker": "AAPL", "name": "Apple"}
        ]
    }
    watchlist, warnings = WeeklyReviewWatchlistInput.from_mapping(payload)
    assert watchlist.items[0].status == WeeklyReviewWatchlistStatus.WATCHLIST
    assert any(w.code == "missing_watchlist_status" for w in warnings)


def test_watchlist_unknown_status_defaults_with_warning():
    payload = {
        "items": [
            {"ticker": "AAPL", "name": "Apple", "status": "UnknownStatus"}
        ]
    }
    watchlist, warnings = WeeklyReviewWatchlistInput.from_mapping(payload)
    assert watchlist.items[0].status == WeeklyReviewWatchlistStatus.WATCHLIST
    assert any(w.code == "unknown_watchlist_status" for w in warnings)


def test_watchlist_legacy_status_aliases_accepted():
    for legacy, expected in [
        ("researching", WeeklyReviewWatchlistStatus.RESEARCH),
        ("observing", WeeklyReviewWatchlistStatus.WATCHLIST),
        ("needs_more_evidence", WeeklyReviewWatchlistStatus.NEEDS_MORE_EVIDENCE),
        ("ready_for_review", WeeklyReviewWatchlistStatus.SUITABLE_FOR_FURTHER_REVIEW),
    ]:
        payload = {"items": [{"ticker": "AAA", "name": "AAA Corp", "status": legacy}]}
        watchlist, warnings = WeeklyReviewWatchlistInput.from_mapping(payload)
        assert watchlist.items[0].status == expected, f"Failed for {legacy!r}"


def test_watchlist_missing_ticker_raises():
    payload = {"items": [{"name": "No Ticker Corp"}]}
    with pytest.raises(ValueError, match="missing required field 'ticker'"):
        WeeklyReviewWatchlistInput.from_mapping(payload)


def test_watchlist_empty_evidence_fields_default_empty():
    payload = {"items": [{"ticker": "AAPL", "name": "Apple"}]}
    watchlist, _ = WeeklyReviewWatchlistInput.from_mapping(payload)
    item = watchlist.items[0]
    assert item.evidence_needed == ()
    assert item.open_questions == ()
    assert item.manual_observations == ()
    assert item.notes == ""


# ---------------------------------------------------------------------------
# Sector defaulting
# ---------------------------------------------------------------------------


def test_missing_sector_defaults_to_unclassified_with_warning():
    payload = {
        "accounts": [
            {
                "name": "Main",
                "holdings": [
                    {"ticker": "XYZ", "name": "XYZ Corp", "market_value": 10000}
                ],
            }
        ]
    }
    portfolio, warnings = WeeklyReviewPortfolioInput.from_mapping(payload)
    holding = portfolio.all_holdings[0]
    assert holding.sector == "Unclassified"
    assert any(w.code == "missing_sector" for w in warnings)


# ---------------------------------------------------------------------------
# Optional inputs
# ---------------------------------------------------------------------------


def test_missing_profile_path_produces_warning_not_failure(tmp_path):
    paths = WeeklyReviewInputPaths(
        portfolio_path=EXAMPLES / "portfolio.json",
        watchlist_path=EXAMPLES / "watchlist.json",
        profile_path=tmp_path / "no_profile.json",
    )
    result = load_weekly_review_inputs(paths)
    assert result.profile_available is False
    assert any(w.code == "missing_optional_profile" for w in result.warnings)


def test_no_profile_path_produces_warning_not_failure():
    paths = WeeklyReviewInputPaths(
        portfolio_path=EXAMPLES / "portfolio.json",
        watchlist_path=EXAMPLES / "watchlist.json",
    )
    result = load_weekly_review_inputs(paths)
    assert result.profile_available is False
    assert any(w.code == "missing_optional_profile" for w in result.warnings)


def test_missing_journal_produces_warning_not_failure():
    paths = WeeklyReviewInputPaths(
        portfolio_path=EXAMPLES / "portfolio.json",
        watchlist_path=EXAMPLES / "watchlist.json",
        journal_path=Path("nonexistent_journal.json"),
    )
    result = load_weekly_review_inputs(paths)
    assert result.journal_entry_count == 0
    assert any(w.code == "missing_optional_journal" for w in result.warnings)


def test_journal_entry_count_loaded_when_present():
    paths = WeeklyReviewInputPaths(
        portfolio_path=EXAMPLES / "portfolio.json",
        watchlist_path=EXAMPLES / "watchlist.json",
        journal_path=EXAMPLES / "decision_journal.json",
    )
    result = load_weekly_review_inputs(paths)
    assert result.journal_entry_count == 1


def test_missing_company_facts_dir_produces_warning():
    paths = WeeklyReviewInputPaths(
        portfolio_path=EXAMPLES / "portfolio.json",
        watchlist_path=EXAMPLES / "watchlist.json",
        company_facts_dir=Path("nonexistent_dir"),
    )
    result = load_weekly_review_inputs(paths)
    assert result.company_facts_available is False
    assert any(w.code == "missing_optional_company_facts" for w in result.warnings)


def test_missing_financials_dir_produces_warning():
    paths = WeeklyReviewInputPaths(
        portfolio_path=EXAMPLES / "portfolio.json",
        watchlist_path=EXAMPLES / "watchlist.json",
        financials_dir=Path("nonexistent_dir"),
    )
    result = load_weekly_review_inputs(paths)
    assert result.financials_available is False
    assert any(w.code == "missing_optional_financials" for w in result.warnings)


def test_existing_company_facts_dir_recognized(tmp_path):
    facts_dir = tmp_path / "company_facts"
    facts_dir.mkdir()
    paths = WeeklyReviewInputPaths(
        portfolio_path=EXAMPLES / "portfolio.json",
        watchlist_path=EXAMPLES / "watchlist.json",
        company_facts_dir=facts_dir,
    )
    result = load_weekly_review_inputs(paths)
    assert result.company_facts_available is True


# ---------------------------------------------------------------------------
# Provider / network boundary
# ---------------------------------------------------------------------------


def test_weekly_review_package_no_provider_imports():
    import importlib
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


def test_weekly_review_init_no_provider_imports():
    import atlas.weekly_review as pkg

    source = Path(pkg.__file__).read_text(encoding="utf-8")
    assert "atlas.providers" not in source
    assert "import requests" not in source


# ---------------------------------------------------------------------------
# Language guardrail — sample files
# ---------------------------------------------------------------------------


def _scan_file_for_forbidden(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8").lower()
    return [term for term in FORBIDDEN_TERMS if term in text]


def test_sample_portfolio_no_forbidden_language():
    hits = _scan_file_for_forbidden(EXAMPLES / "portfolio.json")
    assert not hits, f"Forbidden terms in portfolio.json: {hits}"


def test_sample_watchlist_no_forbidden_language():
    hits = _scan_file_for_forbidden(EXAMPLES / "watchlist.json")
    assert not hits, f"Forbidden terms in watchlist.json: {hits}"


def test_sample_investor_profile_no_forbidden_language():
    hits = _scan_file_for_forbidden(EXAMPLES / "investor_profile.json")
    assert not hits, f"Forbidden terms in investor_profile.json: {hits}"


def test_sample_decision_journal_no_forbidden_language():
    hits = _scan_file_for_forbidden(EXAMPLES / "decision_journal.json")
    assert not hits, f"Forbidden terms in decision_journal.json: {hits}"


def test_sample_company_facts_no_forbidden_language():
    hits = _scan_file_for_forbidden(EXAMPLES / "company_facts" / "ASML.json")
    assert not hits, f"Forbidden terms in company_facts/ASML.json: {hits}"


def test_sample_scope_notes_no_forbidden_language():
    hits = _scan_file_for_forbidden(EXAMPLES / "scope_notes.md")
    assert not hits, f"Forbidden terms in scope_notes.md: {hits}"


def test_loader_warning_messages_no_forbidden_language():
    paths = WeeklyReviewInputPaths(
        portfolio_path=EXAMPLES / "portfolio.json",
        watchlist_path=EXAMPLES / "watchlist.json",
    )
    result = load_weekly_review_inputs(paths)
    for w in result.warnings:
        text = w.message.lower()
        for term in FORBIDDEN_TERMS:
            assert term not in text, (
                f"Warning code={w.code!r} contains forbidden term {term!r}: {w.message!r}"
            )


# ---------------------------------------------------------------------------
# __all__ integrity
# ---------------------------------------------------------------------------


def test_weekly_review_all_exports_importable():
    import atlas.weekly_review as pkg

    for name in pkg.__all__:
        assert hasattr(pkg, name), f"atlas.weekly_review missing export: {name!r}"
