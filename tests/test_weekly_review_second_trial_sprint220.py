"""Sprint 220 — Second real portfolio trial validation tests.

Checks:
- realistic trial command exits 0
- Section 10 consolidated missing evidence summaries replace per-ticker lines
- Section 8 combined line per ticker when both facts and financials are missing
- Section 9 grouped ticker lists replace per-ticker identical questions
- Section 10 block format for principles and constraints
- output remains deterministic
- output avoids forbidden language
- no provider/network imports introduced
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
from atlas.weekly_review.render import render_weekly_review

REPO_ROOT = Path(__file__).parent.parent
REALISTIC_DIR = REPO_ROOT / "examples" / "weekly_review_realistic"

FORBIDDEN_TERMS = [
    "buy", "sell", "strong buy", "strong sell", "price target", "target price",
    "urgent", "act now", "must buy", "must sell", "guaranteed", "will outperform",
    "financial advice",
]

_PORTFOLIO = {
    "as_of": "2026-01-01",
    "positions": [
        {"ticker": "ASML", "weight": 0.50, "company": "ASML", "sector": "Technology"},
        {"ticker": "XYL", "weight": 0.30, "company": "Xylem", "sector": "Industrials"},
        {"ticker": "CASH", "weight": 0.20, "company": "Cash", "sector": "Cash"},
    ],
}
_WATCHLIST = {
    "name": "Test",
    "as_of": "2026-01-01",
    "items": [
        {"ticker": "XYL", "name": "Xylem", "status": "Research"},
        {"ticker": "NOVO", "name": "Novo Nordisk", "status": "Needs More Evidence"},
    ],
}
_PROFILE = {
    "risk_tolerance": "Balanced",
    "time_horizon": "10+ years",
    "principles": ["Evidence before opinion", "No action is an acceptable outcome"],
    "constraints": ["Avoid excessive concentration", "Avoid decisions on price alone"],
}


def _write_bundle(tmp_dir: Path, facts_tickers=None, fins_tickers=None, suffix="") -> WeeklyReviewInputPaths:
    port = tmp_dir / f"portfolio{suffix}.json"
    watch = tmp_dir / f"watchlist{suffix}.json"
    profile = tmp_dir / f"profile{suffix}.json"
    port.write_text(json.dumps(_PORTFOLIO), encoding="utf-8")
    watch.write_text(json.dumps(_WATCHLIST), encoding="utf-8")
    profile.write_text(json.dumps(_PROFILE), encoding="utf-8")

    facts_dir = tmp_dir / f"company_facts{suffix}"
    facts_dir.mkdir(exist_ok=True)
    for t in (facts_tickers or []):
        (facts_dir / f"{t}.json").write_text("{}", encoding="utf-8")

    fins_dir = tmp_dir / f"financials{suffix}"
    fins_dir.mkdir(exist_ok=True)
    for t in (fins_tickers or []):
        (fins_dir / f"{t}.csv").write_text("ticker,fiscal_year\n", encoding="utf-8")

    return WeeklyReviewInputPaths(
        portfolio_path=port,
        watchlist_path=watch,
        profile_path=profile,
        company_facts_dir=facts_dir,
        financials_dir=fins_dir,
        as_of="2026-01-01",
    )


# ---------------------------------------------------------------------------
# Section 8: combined line when both missing
# ---------------------------------------------------------------------------


def test_section8_combined_line_when_both_missing(tmp_path):
    paths = _write_bundle(tmp_path, facts_tickers=["ASML"], fins_tickers=["ASML"], suffix="_s8c")
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    # XYL and NOVO both missing facts and fins → combined line
    assert "Evidence Gap [NOVO]: no local company facts file or financial history file." in output
    assert "Evidence Gap [XYL]: no local company facts file or financial history file." in output


def test_section8_only_facts_missing_line(tmp_path):
    # Give fins to all tickers but facts only to ASML
    paths = _write_bundle(
        tmp_path,
        facts_tickers=["ASML"],
        fins_tickers=["ASML", "XYL", "NOVO"],
        suffix="_s8of",
    )
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    assert "Evidence Gap [XYL]: local company facts file is missing." in output
    assert "Evidence Gap [NOVO]: local company facts file is missing." in output
    # Should NOT use the combined message since only facts are missing
    assert "Evidence Gap [XYL]: no local company facts file or financial history file." not in output


def test_section8_only_fins_missing_line(tmp_path):
    paths = _write_bundle(
        tmp_path,
        facts_tickers=["ASML", "XYL", "NOVO"],
        fins_tickers=["ASML"],
        suffix="_s8ofi",
    )
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    assert "Evidence Gap [XYL]: local financial history file is missing." in output
    assert "Evidence Gap [XYL]: no local company facts file or financial history file." not in output


# ---------------------------------------------------------------------------
# Section 9: grouped ticker lists
# ---------------------------------------------------------------------------


def test_section9_grouped_missing_facts(tmp_path):
    paths = _write_bundle(tmp_path, facts_tickers=["ASML"], fins_tickers=["ASML"], suffix="_s9gf")
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    assert "Tickers without local company facts" in output
    assert "NOVO" in output
    assert "XYL" in output


def test_section9_grouped_missing_fins(tmp_path):
    paths = _write_bundle(tmp_path, facts_tickers=["ASML"], fins_tickers=["ASML"], suffix="_s9gfi")
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    assert "Tickers without local financial history" in output


def test_section9_no_per_ticker_generic_questions(tmp_path):
    paths = _write_bundle(tmp_path, facts_tickers=["ASML"], fins_tickers=["ASML"], suffix="_s9nq")
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    # The old per-ticker identical questions should be gone
    assert "[XYL] What local facts would help clarify the current thesis?" not in output
    assert "[NOVO] Which financial history should be reviewed before changing" not in output


def test_section9_available_tickers_not_in_grouped_list(tmp_path):
    paths = _write_bundle(tmp_path, facts_tickers=["ASML"], fins_tickers=["ASML"], suffix="_s9av")
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    facts_line = next(
        (l for l in output.splitlines() if "Tickers without local company facts" in l), ""
    )
    assert "ASML" not in facts_line


# ---------------------------------------------------------------------------
# Section 10: consolidated missing evidence + block format
# ---------------------------------------------------------------------------


def test_section10_consolidated_missing_facts_summary(tmp_path):
    paths = _write_bundle(tmp_path, facts_tickers=["ASML"], fins_tickers=["ASML"], suffix="_s10cf")
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    section = output.split("10. Non-Actions")[1]
    assert "Local company facts missing for" in section
    assert "NOVO" in section and "XYL" in section


def test_section10_consolidated_missing_fins_summary(tmp_path):
    paths = _write_bundle(tmp_path, facts_tickers=["ASML"], fins_tickers=["ASML"], suffix="_s10cfi")
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    section = output.split("10. Non-Actions")[1]
    assert "Local financial history missing for" in section


def test_section10_no_per_ticker_reason_lines(tmp_path):
    paths = _write_bundle(tmp_path, facts_tickers=["ASML"], fins_tickers=["ASML"], suffix="_s10np")
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    section = output.split("10. Non-Actions")[1]
    # Old per-ticker format should be gone
    assert "XYL is missing local company facts" not in section
    assert "NOVO is missing local financial history" not in section


def test_section10_principles_block_format(tmp_path):
    paths = _write_bundle(tmp_path, facts_tickers=["ASML"], fins_tickers=["ASML"], suffix="_s10pb")
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    section = output.split("10. Non-Actions")[1]
    assert "Stated principles support a measured approach" in section
    # Each principle still present in the block
    for p in _PROFILE["principles"]:
        assert p in section


def test_section10_constraints_block_format(tmp_path):
    paths = _write_bundle(tmp_path, facts_tickers=["ASML"], fins_tickers=["ASML"], suffix="_s10cb")
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    section = output.split("10. Non-Actions")[1]
    assert "Stated constraints apply to current portfolio" in section
    for c in _PROFILE["constraints"]:
        assert c in section


def test_section10_no_boilerplate_repetition(tmp_path):
    paths = _write_bundle(tmp_path, facts_tickers=["ASML"], fins_tickers=["ASML"], suffix="_s10br")
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    section = output.split("10. Non-Actions")[1]
    # Old boilerplate should be gone
    assert "supports gathering evidence before changing any decision status." not in section
    assert "applies when reviewing current portfolio and watchlist decisions." not in section


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_output_deterministic_after_improvements(tmp_path):
    paths = _write_bundle(tmp_path, facts_tickers=["ASML"], fins_tickers=["ASML"], suffix="_det")
    r1 = load_weekly_review_inputs(paths)
    r2 = load_weekly_review_inputs(paths)
    assert render_weekly_review(r1) == render_weekly_review(r2)


# ---------------------------------------------------------------------------
# Language guardrails
# ---------------------------------------------------------------------------


def test_no_forbidden_language(tmp_path):
    paths = _write_bundle(tmp_path, facts_tickers=["ASML"], fins_tickers=["ASML"], suffix="_lang")
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result).lower()
    for term in FORBIDDEN_TERMS:
        assert term not in output, f"Forbidden term {term!r} found"


# ---------------------------------------------------------------------------
# Realistic bundle integration
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def realistic_result():
    if not (REALISTIC_DIR / "investor_profile.json").exists():
        pytest.skip("Realistic example bundle not present")
    scope_notes = (REALISTIC_DIR / "scope_notes.md").read_text(encoding="utf-8")
    paths = WeeklyReviewInputPaths(
        portfolio_path=REALISTIC_DIR / "portfolio.json",
        watchlist_path=REALISTIC_DIR / "watchlist.json",
        profile_path=REALISTIC_DIR / "investor_profile.json",
        journal_path=REALISTIC_DIR / "decision_journal.json",
        company_facts_dir=REALISTIC_DIR / "company_facts",
        financials_dir=REALISTIC_DIR / "financials",
        as_of="2026-01-01",
        scope_notes=scope_notes,
    )
    return load_weekly_review_inputs(paths)


def test_realistic_trial_exits_cleanly(realistic_result):
    output = render_weekly_review(realistic_result)
    assert output.strip()


def test_realistic_section10_consolidated_not_per_ticker(realistic_result):
    output = render_weekly_review(realistic_result)
    section = output.split("10. Non-Actions")[1]
    assert "Local company facts missing for" in section
    # No per-ticker lines in old format
    assert "LVMH is missing local company facts" not in section


def test_realistic_section10_principles_block(realistic_result):
    output = render_weekly_review(realistic_result)
    section = output.split("10. Non-Actions")[1]
    assert "Stated principles support a measured approach" in section


def test_realistic_section9_grouped_tickers(realistic_result):
    output = render_weekly_review(realistic_result)
    assert "Tickers without local company facts (12)" in output or "Tickers without local company facts" in output


def test_realistic_no_forbidden_language(realistic_result):
    output = render_weekly_review(realistic_result).lower()
    for term in FORBIDDEN_TERMS:
        assert term not in output, f"Forbidden term {term!r} in realistic output"
