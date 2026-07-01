"""Sprint 50: Daily Brief CLI input flag tests.

Tests cover all new --research, --watchlist, --discovery, --company-analysis
flags on `atlas daily summary`, plus error handling and safety constraints.
All tests are local-only, deterministic, and make no network calls.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from atlas.cli.main import app

runner = CliRunner()

FORBIDDEN_LANGUAGE = (
    "buy",
    "sell",
    "strong buy",
    "strong sell",
    "urgent",
    "must act",
    "guaranteed",
    "risk-free",
    "price target",
    "outperform",
    "entry",
    "exit",
)


# ── JSON fixture builders ──────────────────────────────────────────────────────


def _portfolio_json(large_weight: float = 0.4) -> dict:
    return {
        "positions": [
            {
                "ticker": "NVDA", "company": "NVIDIA", "sector": "Semiconductors",
                "country": "USA", "market_cap": 1_000_000, "weight": large_weight,
                "quality_score": 90, "risk_score": 50,
            },
            {
                "ticker": "MSFT", "company": "Microsoft", "sector": "Software",
                "country": "USA", "market_cap": 2_500_000,
                "weight": round(1.0 - large_weight, 2),
                "quality_score": 88, "risk_score": 30,
            },
        ]
    }


def _research_json() -> dict:
    return {
        "notes": [
            {
                "id": "n1", "title": "NVDA deep dive",
                "body": "Initial thesis forming around GPU demand.",
                "created_at": "2026-07-01", "related_tickers": ["NVDA"],
            }
        ],
        "open_questions": ["What is the TAM for data centre GPU?", "Who owns the supply chain?"],
    }


def _watchlist_json() -> dict:
    return {
        "name": "My Watchlist",
        "open_questions": [
            {"id": "wq1", "question": "What is NVDA's competitive moat?", "status": "open"},
            {"id": "wq2", "question": "How durable is MSFT Azure growth?", "status": "open"},
        ],
        "suggested_next_research_steps": [
            "Research NVDA supply chain constraints.",
            "Review MSFT Azure pricing trends.",
        ],
    }


def _discovery_json() -> dict:
    return {
        "candidates": [
            {
                "identifier": "ASML",
                "title": "ASML Holding",
                "reasons": [
                    {"title": "Knowledge Fact", "detail": "Critical semiconductor equipment supplier."}
                ],
                "priority": "moderate",
            },
            {
                "identifier": "TSM",
                "title": "Taiwan Semiconductor",
                "reasons": [
                    {"title": "Research Link", "detail": "Appears in multiple research projects."}
                ],
                "priority": "moderate",
            },
        ]
    }


def _company_analysis_json() -> dict:
    return {
        "company": {
            "id": "nvda", "name": "NVIDIA Corporation",
            "ticker": "NVDA", "sector": "Semiconductors", "country": "USA",
        },
        "unknowns": [
            {"title": "Competitive moat durability", "detail": "Evidence on long-term moat is limited."},
            {"title": "Customer concentration", "detail": "Revenue concentration data is incomplete."},
        ],
        "evidence_links": [
            {"id": "ev1", "source": "10-K 2025", "description": "Revenue breakdown by segment."},
        ],
        "confidence": {
            "level": "medium",
            "explanation": "Moderate evidence base.",
            "drivers": ["Known revenue trajectory"],
            "limitations": ["Limited competitive intelligence"],
        },
    }


def _company_analysis_list_json() -> list:
    return [_company_analysis_json()]


def _write(tmp_path: Path, name: str, data: object) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ── no-input behavior ──────────────────────────────────────────────────────────


def test_no_flags_succeeds() -> None:
    result = runner.invoke(app, ["daily", "summary"])
    assert result.exit_code == 0
    assert "Atlas Daily Brief" in result.stdout


def test_no_flags_reports_no_developments() -> None:
    result = runner.invoke(app, ["daily", "summary"])
    assert result.exit_code == 0
    assert "No meaningful developments" in result.stdout


def test_no_flags_output_is_deterministic() -> None:
    first = runner.invoke(app, ["daily", "summary"])
    second = runner.invoke(app, ["daily", "summary"])
    assert first.exit_code == second.exit_code == 0
    assert first.stdout == second.stdout


# ── --portfolio flag ───────────────────────────────────────────────────────────


def test_portfolio_flag_succeeds(tmp_path: Path) -> None:
    path = _write(tmp_path, "portfolio.json", _portfolio_json())
    result = runner.invoke(app, ["daily", "summary", "--portfolio", str(path)])
    assert result.exit_code == 0
    assert "Portfolio Context" in result.stdout


def test_portfolio_missing_file_fails_cleanly(tmp_path: Path) -> None:
    result = runner.invoke(app, ["daily", "summary", "--portfolio", str(tmp_path / "nope.json")])
    assert result.exit_code == 1
    assert "Daily summary failed" in result.stdout
    assert "Traceback" not in result.stdout


# ── --research flag ────────────────────────────────────────────────────────────


def test_research_flag_succeeds(tmp_path: Path) -> None:
    path = _write(tmp_path, "research.json", _research_json())
    result = runner.invoke(app, ["daily", "summary", "--research", str(path)])
    assert result.exit_code == 0
    assert "Research Context" in result.stdout


def test_research_note_title_appears_in_output(tmp_path: Path) -> None:
    path = _write(tmp_path, "research.json", _research_json())
    result = runner.invoke(app, ["daily", "summary", "--research", str(path)])
    assert result.exit_code == 0
    assert "NVDA deep dive" in result.stdout


def test_research_open_questions_appear_as_unknowns(tmp_path: Path) -> None:
    path = _write(tmp_path, "research.json", _research_json())
    result = runner.invoke(app, ["daily", "summary", "--research", str(path)])
    assert result.exit_code == 0
    assert "Unresolved Questions" in result.stdout
    assert "TAM" in result.stdout


def test_research_missing_file_fails_cleanly(tmp_path: Path) -> None:
    result = runner.invoke(app, ["daily", "summary", "--research", str(tmp_path / "nope.json")])
    assert result.exit_code == 1
    assert "Daily summary failed" in result.stdout
    assert "Traceback" not in result.stdout


def test_research_invalid_json_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not valid json", encoding="utf-8")
    result = runner.invoke(app, ["daily", "summary", "--research", str(path)])
    assert result.exit_code == 1
    assert "Daily summary failed" in result.stdout
    assert "Traceback" not in result.stdout


def test_research_empty_notes_list_still_works(tmp_path: Path) -> None:
    path = _write(tmp_path, "research.json", {"notes": [], "open_questions": []})
    result = runner.invoke(app, ["daily", "summary", "--research", str(path)])
    assert result.exit_code == 0


def test_research_questions_only_no_notes(tmp_path: Path) -> None:
    path = _write(tmp_path, "research.json", {"notes": [], "open_questions": ["What is the moat?"]})
    result = runner.invoke(app, ["daily", "summary", "--research", str(path)])
    assert result.exit_code == 0
    assert "What is the moat?" in result.stdout


# ── --watchlist flag ───────────────────────────────────────────────────────────


def test_watchlist_flag_succeeds(tmp_path: Path) -> None:
    path = _write(tmp_path, "watchlist.json", _watchlist_json())
    result = runner.invoke(app, ["daily", "summary", "--watchlist", str(path)])
    assert result.exit_code == 0
    assert "Watchlist Context" in result.stdout


def test_watchlist_open_question_count_in_output(tmp_path: Path) -> None:
    path = _write(tmp_path, "watchlist.json", _watchlist_json())
    result = runner.invoke(app, ["daily", "summary", "--watchlist", str(path)])
    assert result.exit_code == 0
    assert "2" in result.stdout


def test_watchlist_suggested_steps_in_output(tmp_path: Path) -> None:
    path = _write(tmp_path, "watchlist.json", _watchlist_json())
    result = runner.invoke(app, ["daily", "summary", "--watchlist", str(path)])
    assert result.exit_code == 0
    assert "Suggested Next Research Steps" in result.stdout


def test_watchlist_missing_file_fails_cleanly(tmp_path: Path) -> None:
    result = runner.invoke(app, ["daily", "summary", "--watchlist", str(Path("/nope/watchlist.json"))])
    assert result.exit_code == 1
    assert "Daily summary failed" in result.stdout
    assert "Traceback" not in result.stdout


def test_watchlist_invalid_json_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("[invalid", encoding="utf-8")
    result = runner.invoke(app, ["daily", "summary", "--watchlist", str(path)])
    assert result.exit_code == 1
    assert "Daily summary failed" in result.stdout


def test_watchlist_empty_object_succeeds(tmp_path: Path) -> None:
    path = _write(tmp_path, "watchlist.json", {"name": "Empty"})
    result = runner.invoke(app, ["daily", "summary", "--watchlist", str(path)])
    assert result.exit_code == 0


def test_watchlist_questions_as_plain_strings(tmp_path: Path) -> None:
    path = _write(tmp_path, "watchlist.json", {
        "name": "Simple",
        "open_questions": ["Plain string question"],
        "suggested_next_research_steps": [],
    })
    result = runner.invoke(app, ["daily", "summary", "--watchlist", str(path)])
    assert result.exit_code == 0


# ── --discovery flag ───────────────────────────────────────────────────────────


def test_discovery_flag_succeeds(tmp_path: Path) -> None:
    path = _write(tmp_path, "discovery.json", _discovery_json())
    result = runner.invoke(app, ["daily", "summary", "--discovery", str(path)])
    assert result.exit_code == 0
    assert "Discovery Context" in result.stdout


def test_discovery_candidates_appear_in_output(tmp_path: Path) -> None:
    path = _write(tmp_path, "discovery.json", _discovery_json())
    result = runner.invoke(app, ["daily", "summary", "--discovery", str(path)])
    assert result.exit_code == 0
    assert "ASML" in result.stdout


def test_discovery_candidate_reason_appears_in_output(tmp_path: Path) -> None:
    path = _write(tmp_path, "discovery.json", _discovery_json())
    result = runner.invoke(app, ["daily", "summary", "--discovery", str(path)])
    assert result.exit_code == 0
    assert "semiconductor equipment" in result.stdout.lower() or "Critical" in result.stdout


def test_discovery_missing_file_fails_cleanly(tmp_path: Path) -> None:
    result = runner.invoke(app, ["daily", "summary", "--discovery", str(Path("/nope/disc.json"))])
    assert result.exit_code == 1
    assert "Daily summary failed" in result.stdout
    assert "Traceback" not in result.stdout


def test_discovery_invalid_json_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{bad", encoding="utf-8")
    result = runner.invoke(app, ["daily", "summary", "--discovery", str(path)])
    assert result.exit_code == 1
    assert "Daily summary failed" in result.stdout


def test_discovery_empty_candidates_list_succeeds(tmp_path: Path) -> None:
    path = _write(tmp_path, "discovery.json", {"candidates": []})
    result = runner.invoke(app, ["daily", "summary", "--discovery", str(path)])
    assert result.exit_code == 0


def test_discovery_candidate_without_reasons_uses_fallback(tmp_path: Path) -> None:
    path = _write(tmp_path, "discovery.json", {
        "candidates": [{"identifier": "XYZ", "title": "XYZ Corp"}]
    })
    result = runner.invoke(app, ["daily", "summary", "--discovery", str(path)])
    assert result.exit_code == 0
    assert "XYZ" in result.stdout


# ── --company-analysis flag ────────────────────────────────────────────────────


def test_company_analysis_flag_succeeds(tmp_path: Path) -> None:
    path = _write(tmp_path, "company.json", _company_analysis_json())
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(path)])
    assert result.exit_code == 0
    assert "Company Analysis Context" in result.stdout


def test_company_analysis_ticker_appears_in_output(tmp_path: Path) -> None:
    path = _write(tmp_path, "company.json", _company_analysis_json())
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(path)])
    assert result.exit_code == 0
    assert "NVDA" in result.stdout


def test_company_analysis_unknowns_in_output(tmp_path: Path) -> None:
    path = _write(tmp_path, "company.json", _company_analysis_json())
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(path)])
    assert result.exit_code == 0
    assert "2" in result.stdout


def test_company_analysis_evidence_gaps_in_output(tmp_path: Path) -> None:
    path = _write(tmp_path, "company.json", _company_analysis_json())
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(path)])
    assert result.exit_code == 0
    assert "Evidence Gaps" in result.stdout
    assert "Revenue" in result.stdout


def test_company_analysis_list_format_succeeds(tmp_path: Path) -> None:
    path = _write(tmp_path, "company.json", _company_analysis_list_json())
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(path)])
    assert result.exit_code == 0
    assert "NVDA" in result.stdout


def test_company_analysis_missing_file_fails_cleanly(tmp_path: Path) -> None:
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(Path("/nope/ca.json"))])
    assert result.exit_code == 1
    assert "Daily summary failed" in result.stdout
    assert "Traceback" not in result.stdout


def test_company_analysis_invalid_json_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("not json at all", encoding="utf-8")
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(path)])
    assert result.exit_code == 1
    assert "Daily summary failed" in result.stdout


def test_company_analysis_empty_unknowns_succeeds(tmp_path: Path) -> None:
    data = _company_analysis_json()
    data["unknowns"] = []
    data["evidence_links"] = []
    path = _write(tmp_path, "company.json", data)
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(path)])
    assert result.exit_code == 0


# ── multi-flag composition ─────────────────────────────────────────────────────


def test_all_flags_together_produce_all_sections(tmp_path: Path) -> None:
    portfolio_path = _write(tmp_path, "portfolio.json", _portfolio_json())
    research_path = _write(tmp_path, "research.json", _research_json())
    watchlist_path = _write(tmp_path, "watchlist.json", _watchlist_json())
    discovery_path = _write(tmp_path, "discovery.json", _discovery_json())
    company_path = _write(tmp_path, "company.json", _company_analysis_json())

    result = runner.invoke(app, [
        "daily", "summary",
        "--portfolio", str(portfolio_path),
        "--research", str(research_path),
        "--watchlist", str(watchlist_path),
        "--discovery", str(discovery_path),
        "--company-analysis", str(company_path),
    ])
    assert result.exit_code == 0
    assert "Portfolio Context" in result.stdout
    assert "Research Context" in result.stdout
    assert "Watchlist Context" in result.stdout
    assert "Discovery Context" in result.stdout
    assert "Company Analysis Context" in result.stdout


def test_portfolio_and_research_together(tmp_path: Path) -> None:
    portfolio_path = _write(tmp_path, "portfolio.json", _portfolio_json())
    research_path = _write(tmp_path, "research.json", _research_json())
    result = runner.invoke(app, [
        "daily", "summary",
        "--portfolio", str(portfolio_path),
        "--research", str(research_path),
    ])
    assert result.exit_code == 0
    assert "Portfolio Context" in result.stdout
    assert "Research Context" in result.stdout


def test_multi_flag_output_is_deterministic(tmp_path: Path) -> None:
    research_path = _write(tmp_path, "research.json", _research_json())
    watchlist_path = _write(tmp_path, "watchlist.json", _watchlist_json())
    first = runner.invoke(app, [
        "daily", "summary",
        "--research", str(research_path),
        "--watchlist", str(watchlist_path),
    ])
    second = runner.invoke(app, [
        "daily", "summary",
        "--research", str(research_path),
        "--watchlist", str(watchlist_path),
    ])
    assert first.exit_code == second.exit_code == 0
    assert first.stdout == second.stdout


def test_one_bad_flag_does_not_silently_skip(tmp_path: Path) -> None:
    research_path = _write(tmp_path, "research.json", _research_json())
    result = runner.invoke(app, [
        "daily", "summary",
        "--research", str(research_path),
        "--watchlist", str(tmp_path / "missing.json"),
    ])
    assert result.exit_code == 1
    assert "Daily summary failed" in result.stdout


# ── safety and language constraints ───────────────────────────────────────────


def test_no_forbidden_language_with_all_inputs(tmp_path: Path) -> None:
    portfolio_path = _write(tmp_path, "portfolio.json", _portfolio_json(large_weight=0.7))
    research_path = _write(tmp_path, "research.json", _research_json())
    watchlist_path = _write(tmp_path, "watchlist.json", _watchlist_json())
    discovery_path = _write(tmp_path, "discovery.json", _discovery_json())
    company_path = _write(tmp_path, "company.json", _company_analysis_json())

    result = runner.invoke(app, [
        "daily", "summary",
        "--portfolio", str(portfolio_path),
        "--research", str(research_path),
        "--watchlist", str(watchlist_path),
        "--discovery", str(discovery_path),
        "--company-analysis", str(company_path),
    ])
    assert result.exit_code == 0
    output_lower = result.stdout.lower()
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output_lower, f"Forbidden term found in output: {term!r}"


def test_no_network_calls_with_all_flags(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module

    def _fail(*args, **kwargs):
        raise AssertionError("urlopen must not be called during daily summary")

    monkeypatch.setattr(yahoo_module, "urlopen", _fail)

    research_path = _write(tmp_path, "research.json", _research_json())
    watchlist_path = _write(tmp_path, "watchlist.json", _watchlist_json())
    result = runner.invoke(app, [
        "daily", "summary",
        "--research", str(research_path),
        "--watchlist", str(watchlist_path),
    ])
    assert result.exit_code == 0


def test_legacy_daily_brief_command_still_works() -> None:
    result = runner.invoke(app, ["daily", "brief"])
    assert result.exit_code == 0
    assert "Atlas Daily Brief" in result.stdout
    assert "Bottom Line" in result.stdout
