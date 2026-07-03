"""Sprint 219 — Per-ticker local evidence presence checks in Weekly Review.

Checks:
- evidence universe includes portfolio tickers (excluding cash)
- evidence universe includes watchlist tickers
- duplicate ticker across portfolio/watchlist appears once
- source field marks portfolio_and_watchlist when applicable
- company_facts/<TICKER>.json presence is detected
- financials/<TICKER>.csv presence is detected
- missing company facts file appears in Section 8
- missing financial history file appears in Section 8
- missing company facts creates follow-up question in Section 9
- missing financial history creates follow-up question in Section 9
- missing company facts creates reason to wait in Section 10
- missing financial history creates reason to wait in Section 10
- missing evidence directories remain non-blocking
- Section 10 remains non-empty
- output is deterministic
- output avoids forbidden language
- no provider/network imports are introduced
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.weekly_review.inputs import (
    WeeklyReviewInputPaths,
    WeeklyReviewTickerEvidence,
    load_weekly_review_inputs,
)
from atlas.weekly_review.render import render_weekly_review

REPO_ROOT = Path(__file__).parent.parent
REALISTIC_DIR = REPO_ROOT / "examples" / "weekly_review_realistic"

FORBIDDEN_TERMS = [
    "buy", "sell", "strong buy", "strong sell", "price target", "target price",
    "urgent", "act now", "must buy", "must sell", "guaranteed", "will outperform",
    "financial advice",
]

_PORTFOLIO_BOTH = {
    "as_of": "2026-01-01",
    "positions": [
        {"ticker": "ASML", "weight": 0.50, "company": "ASML Holding", "sector": "Technology"},
        {"ticker": "XYL", "weight": 0.30, "company": "Xylem", "sector": "Industrials"},
        {"ticker": "CASH", "weight": 0.20, "company": "Cash", "sector": "Cash"},
    ],
}
_WATCHLIST_BOTH = {
    "name": "Test",
    "as_of": "2026-01-01",
    "items": [
        {"ticker": "XYL", "name": "Xylem", "status": "Research"},   # overlap with portfolio
        {"ticker": "NOVO", "name": "Novo Nordisk", "status": "Needs More Evidence"},
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_bundle(
    tmp_dir: Path,
    suffix: str = "",
    facts_tickers: list[str] | None = None,
    fins_tickers: list[str] | None = None,
    include_facts_dir: bool = True,
    include_fins_dir: bool = True,
) -> WeeklyReviewInputPaths:
    port_path = tmp_dir / f"portfolio{suffix}.json"
    watch_path = tmp_dir / f"watchlist{suffix}.json"
    port_path.write_text(json.dumps(_PORTFOLIO_BOTH), encoding="utf-8")
    watch_path.write_text(json.dumps(_WATCHLIST_BOTH), encoding="utf-8")

    facts_dir = None
    if include_facts_dir:
        facts_dir = tmp_dir / f"company_facts{suffix}"
        facts_dir.mkdir(exist_ok=True)
        for t in (facts_tickers or []):
            (facts_dir / f"{t}.json").write_text("{}", encoding="utf-8")

    fins_dir = None
    if include_fins_dir:
        fins_dir = tmp_dir / f"financials{suffix}"
        fins_dir.mkdir(exist_ok=True)
        for t in (fins_tickers or []):
            (fins_dir / f"{t}.csv").write_text("ticker,fiscal_year\n", encoding="utf-8")

    return WeeklyReviewInputPaths(
        portfolio_path=port_path,
        watchlist_path=watch_path,
        company_facts_dir=facts_dir,
        financials_dir=fins_dir,
        as_of="2026-01-01",
    )


# ---------------------------------------------------------------------------
# Ticker universe
# ---------------------------------------------------------------------------


def test_evidence_universe_includes_portfolio_tickers(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_u1")
    result = load_weekly_review_inputs(paths)
    tickers = {ev.ticker for ev in result.ticker_evidence}
    assert "ASML" in tickers
    assert "XYL" in tickers


def test_evidence_universe_includes_watchlist_tickers(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_u2")
    result = load_weekly_review_inputs(paths)
    tickers = {ev.ticker for ev in result.ticker_evidence}
    assert "NOVO" in tickers


def test_evidence_universe_excludes_cash(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_u3")
    result = load_weekly_review_inputs(paths)
    tickers = {ev.ticker for ev in result.ticker_evidence}
    assert "CASH" not in tickers


def test_evidence_universe_deduplicates_overlap(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_u4")
    result = load_weekly_review_inputs(paths)
    tickers = [ev.ticker for ev in result.ticker_evidence]
    assert tickers.count("XYL") == 1


def test_evidence_universe_stable_sort(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_u5")
    result = load_weekly_review_inputs(paths)
    tickers = [ev.ticker for ev in result.ticker_evidence]
    assert tickers == sorted(tickers)


# ---------------------------------------------------------------------------
# Source field
# ---------------------------------------------------------------------------


def test_source_portfolio_only(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_src1")
    result = load_weekly_review_inputs(paths)
    asml = next(ev for ev in result.ticker_evidence if ev.ticker == "ASML")
    assert asml.source == "portfolio"


def test_source_watchlist_only(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_src2")
    result = load_weekly_review_inputs(paths)
    novo = next(ev for ev in result.ticker_evidence if ev.ticker == "NOVO")
    assert novo.source == "watchlist"


def test_source_portfolio_and_watchlist(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_src3")
    result = load_weekly_review_inputs(paths)
    xyl = next(ev for ev in result.ticker_evidence if ev.ticker == "XYL")
    assert xyl.source == "portfolio_and_watchlist"


# ---------------------------------------------------------------------------
# File presence detection
# ---------------------------------------------------------------------------


def test_company_facts_available_when_file_exists(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_fp1", facts_tickers=["ASML"])
    result = load_weekly_review_inputs(paths)
    asml = next(ev for ev in result.ticker_evidence if ev.ticker == "ASML")
    assert asml.company_facts_available is True


def test_company_facts_unavailable_when_file_missing(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_fp2", facts_tickers=[])
    result = load_weekly_review_inputs(paths)
    asml = next(ev for ev in result.ticker_evidence if ev.ticker == "ASML")
    assert asml.company_facts_available is False


def test_financials_available_when_file_exists(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_fp3", fins_tickers=["ASML"])
    result = load_weekly_review_inputs(paths)
    asml = next(ev for ev in result.ticker_evidence if ev.ticker == "ASML")
    assert asml.financials_available is True


def test_financials_unavailable_when_file_missing(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_fp4", fins_tickers=[])
    result = load_weekly_review_inputs(paths)
    asml = next(ev for ev in result.ticker_evidence if ev.ticker == "ASML")
    assert asml.financials_available is False


def test_tickers_missing_facts_preserved(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_fp5", facts_tickers=["ASML"])
    result = load_weekly_review_inputs(paths)
    # ASML has a file, XYL and NOVO do not
    assert "ASML" not in result.tickers_missing_facts
    assert "XYL" in result.tickers_missing_facts
    assert "NOVO" in result.tickers_missing_facts


def test_tickers_missing_financials_preserved(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_fp6", fins_tickers=["ASML"])
    result = load_weekly_review_inputs(paths)
    assert "ASML" not in result.tickers_missing_financials
    assert "XYL" in result.tickers_missing_financials


# ---------------------------------------------------------------------------
# Directory missing — non-blocking
# ---------------------------------------------------------------------------


def test_missing_facts_dir_is_non_blocking(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_md1", include_facts_dir=False)
    result = load_weekly_review_inputs(paths)
    assert result.company_facts_available is False
    # ticker_evidence still built, but facts marked unavailable
    assert len(result.ticker_evidence) > 0


def test_missing_fins_dir_is_non_blocking(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_md2", include_fins_dir=False)
    result = load_weekly_review_inputs(paths)
    assert result.financials_available is False
    assert len(result.ticker_evidence) > 0


def test_missing_both_dirs_ticker_evidence_still_built(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_md3", include_facts_dir=False, include_fins_dir=False)
    result = load_weekly_review_inputs(paths)
    assert len(result.ticker_evidence) == 3  # ASML, NOVO, XYL


def test_missing_both_dirs_facts_unavailable_in_evidence(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_md4", include_facts_dir=False, include_fins_dir=False)
    result = load_weekly_review_inputs(paths)
    for ev in result.ticker_evidence:
        assert ev.company_facts_available is False
        assert ev.financials_available is False


# ---------------------------------------------------------------------------
# Section 8: per-ticker evidence gaps
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def output_s8_partial(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("s8")
    paths = _write_bundle(tmp, suffix="_s8", facts_tickers=["ASML"], fins_tickers=["ASML"])
    result = load_weekly_review_inputs(paths)
    return render_weekly_review(result)


def test_section8_present(output_s8_partial):
    assert "8. Missing Evidence" in output_s8_partial


def test_section8_evidence_gap_missing_facts(output_s8_partial):
    # Sprint 220: when both facts and financials are missing, one combined line per ticker
    assert "Evidence Gap [XYL]: no local company facts file or financial history file." in output_s8_partial
    assert "Evidence Gap [NOVO]: no local company facts file or financial history file." in output_s8_partial


def test_section8_no_gap_for_ticker_with_facts(output_s8_partial):
    assert "Evidence Gap [ASML]" not in output_s8_partial


def test_section8_evidence_gap_missing_financials(output_s8_partial):
    # Combined message covers both; assert the combined line is present
    assert "no local company facts file or financial history file" in output_s8_partial


def test_section8_no_gap_for_ticker_with_financials(output_s8_partial):
    assert "Evidence Gap [ASML]: local financial history file is missing." not in output_s8_partial


# ---------------------------------------------------------------------------
# Section 9: per-ticker follow-up questions
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def output_s9_partial(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("s9")
    paths = _write_bundle(tmp, suffix="_s9", facts_tickers=["ASML"], fins_tickers=["ASML"])
    result = load_weekly_review_inputs(paths)
    return render_weekly_review(result)


def test_section9_present(output_s9_partial):
    assert "9. Follow-Up Questions" in output_s9_partial


def test_section9_follow_up_for_missing_facts(output_s9_partial):
    # Sprint 220: grouped list instead of per-ticker identical questions
    assert "Tickers without local company facts" in output_s9_partial
    assert "XYL" in output_s9_partial


def test_section9_no_follow_up_for_available_facts(output_s9_partial):
    # ASML has facts, so it should NOT appear in the missing-facts group
    missing_line = next(
        (l for l in output_s9_partial.splitlines() if "Tickers without local company facts" in l),
        ""
    )
    assert "ASML" not in missing_line


def test_section9_follow_up_for_missing_financials(output_s9_partial):
    # Sprint 220: grouped list
    assert "Tickers without local financial history" in output_s9_partial
    assert "XYL" in output_s9_partial


def test_section9_no_follow_up_for_available_financials(output_s9_partial):
    missing_line = next(
        (l for l in output_s9_partial.splitlines() if "Tickers without local financial history" in l),
        ""
    )
    assert "ASML" not in missing_line


# ---------------------------------------------------------------------------
# Section 10: per-ticker reasons to wait
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def output_s10_partial(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("s10")
    paths = _write_bundle(tmp, suffix="_s10", facts_tickers=["ASML"], fins_tickers=["ASML"])
    result = load_weekly_review_inputs(paths)
    return render_weekly_review(result)


def test_section10_present(output_s10_partial):
    assert "10. Non-Actions / Reasons to Wait" in output_s10_partial


def test_section10_reason_to_wait_missing_facts(output_s10_partial):
    # Sprint 220: consolidated summary line listing tickers
    section = output_s10_partial.split("10. Non-Actions")[1]
    assert "Local company facts missing for" in section
    assert "XYL" in section
    assert "NOVO" in section


def test_section10_no_reason_for_available_facts(output_s10_partial):
    section = output_s10_partial.split("10. Non-Actions")[1]
    # ASML has facts, should not appear in the missing-facts summary
    missing_line = next(
        (l for l in section.splitlines() if "Local company facts missing for" in l), ""
    )
    assert "ASML" not in missing_line


def test_section10_reason_to_wait_missing_financials(output_s10_partial):
    section = output_s10_partial.split("10. Non-Actions")[1]
    assert "Local financial history missing for" in section
    assert "XYL" in section


def test_section10_non_empty_without_evidence_dirs(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_s10_nd", include_facts_dir=False, include_fins_dir=False)
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    section = output.split("10. Non-Actions")[1]
    assert section.strip()


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_output_deterministic(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_det", facts_tickers=["ASML"], fins_tickers=["ASML"])
    result1 = load_weekly_review_inputs(paths)
    result2 = load_weekly_review_inputs(paths)
    assert render_weekly_review(result1) == render_weekly_review(result2)


# ---------------------------------------------------------------------------
# Language guardrails
# ---------------------------------------------------------------------------


def test_output_no_forbidden_language(tmp_path):
    paths = _write_bundle(tmp_path, suffix="_lang", facts_tickers=["ASML"], fins_tickers=["ASML"])
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result).lower()
    for term in FORBIDDEN_TERMS:
        assert term not in output, f"Forbidden term {term!r} found in output"


# ---------------------------------------------------------------------------
# Provider / network boundary
# ---------------------------------------------------------------------------


def test_inputs_has_no_provider_dependency():
    import ast
    import inspect
    import atlas.weekly_review.inputs as mod
    source = inspect.getsource(mod)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else ([node.module] if node.module else [])
            )
            for name in names:
                assert "providers" not in (name or ""), f"Provider import in inputs.py: {name}"


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


def test_realistic_ticker_evidence_built(realistic_result):
    assert len(realistic_result.ticker_evidence) > 0


def test_realistic_evidence_sorted(realistic_result):
    tickers = [ev.ticker for ev in realistic_result.ticker_evidence]
    assert tickers == sorted(tickers)


def test_realistic_cash_excluded_from_evidence(realistic_result):
    tickers = {ev.ticker for ev in realistic_result.ticker_evidence}
    assert "CASHEUR" not in tickers


def test_realistic_asml_has_facts(realistic_result):
    asml = next((ev for ev in realistic_result.ticker_evidence if ev.ticker == "ASML"), None)
    assert asml is not None
    assert asml.company_facts_available is True


def test_realistic_section8_has_per_ticker_gaps(realistic_result):
    output = render_weekly_review(realistic_result)
    # Some tickers should be missing facts/financials (most are, only 3 have them)
    assert "Evidence Gap" in output


def test_realistic_no_forbidden_language(realistic_result):
    output = render_weekly_review(realistic_result).lower()
    for term in FORBIDDEN_TERMS:
        assert term not in output, f"Forbidden term {term!r} in realistic output"
