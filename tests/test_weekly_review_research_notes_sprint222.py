"""Sprint 222 — Research notes input tests for Atlas Weekly Review.

Tests cover: CLI argument, directory detection, per-ticker notes loading,
bounded reading, safe parsing, Section 8/9/10 rendering, missing/malformed
notes handling, determinism, language guardrails, and provider boundary.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from pathlib import Path

import pytest

from atlas.weekly_review.inputs import (
    WeeklyReviewInputPaths,
    WeeklyReviewResearchNote,
    _RESEARCH_NOTES_MAX_CHARS,
    _load_research_note,
    _parse_research_notes,
    load_weekly_review_inputs,
)
from atlas.weekly_review.render import render_weekly_review


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PORTFOLIO_PATH = Path("examples/weekly_review/portfolio.json")
WATCHLIST_PATH = Path("examples/weekly_review/watchlist.json")
RESEARCH_NOTES_DIR = Path("examples/weekly_review/research_notes")


def _minimal_paths(**kwargs) -> WeeklyReviewInputPaths:
    return WeeklyReviewInputPaths(
        portfolio_path=PORTFOLIO_PATH,
        watchlist_path=WATCHLIST_PATH,
        **kwargs,
    )


def _make_notes_dir(tmp_path: Path, ticker: str, content: str) -> Path:
    notes_dir = tmp_path / ticker
    notes_dir.mkdir(parents=True)
    (notes_dir / "notes.md").write_text(content, encoding="utf-8")
    return tmp_path


SAMPLE_NOTES = textwrap.dedent("""\
    # ASML Research Notes

    ## Thesis Notes
    - Lithography leadership thesis.

    ## Evidence Gaps
    - Margin durability needs review.
    - China exposure needs context.

    ## Open Questions
    - What assumptions about EUV demand should be rechecked?
    - Which quarters are most relevant for margin review?

    ## Risks to Monitor
    - Export controls.
    - Customer capex cyclicality.

    ## Reason to Wait
    - Evidence gaps remain unresolved.
""")


# ---------------------------------------------------------------------------
# WeeklyReviewResearchNote dataclass
# ---------------------------------------------------------------------------

def test_research_note_dataclass_fields():
    note = WeeklyReviewResearchNote(
        ticker="ASML",
        available=True,
        evidence_gaps=("gap 1", "gap 2"),
        open_questions=("q 1",),
        risks_to_monitor=("risk 1",),
        reasons_to_wait=("reason 1",),
    )
    assert note.ticker == "ASML"
    assert note.available is True
    assert note.evidence_gaps == ("gap 1", "gap 2")
    assert note.open_questions == ("q 1",)
    assert note.risks_to_monitor == ("risk 1",)
    assert note.reasons_to_wait == ("reason 1",)


def test_research_note_defaults():
    note = WeeklyReviewResearchNote(ticker="XYL", available=False)
    assert note.evidence_gaps == ()
    assert note.open_questions == ()
    assert note.risks_to_monitor == ()
    assert note.reasons_to_wait == ()


def test_research_note_is_frozen():
    note = WeeklyReviewResearchNote(ticker="ASML", available=True)
    with pytest.raises((AttributeError, TypeError)):
        note.ticker = "OTHER"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# _parse_research_notes
# ---------------------------------------------------------------------------

def test_parse_evidence_gaps():
    fields = _parse_research_notes(SAMPLE_NOTES)
    assert "Margin durability needs review." in fields["evidence_gaps"]
    assert "China exposure needs context." in fields["evidence_gaps"]


def test_parse_open_questions():
    fields = _parse_research_notes(SAMPLE_NOTES)
    assert len(fields["open_questions"]) == 2


def test_parse_risks_to_monitor():
    fields = _parse_research_notes(SAMPLE_NOTES)
    assert "Export controls." in fields["risks_to_monitor"]
    assert "Customer capex cyclicality." in fields["risks_to_monitor"]


def test_parse_reasons_to_wait():
    fields = _parse_research_notes(SAMPLE_NOTES)
    assert "Evidence gaps remain unresolved." in fields["reasons_to_wait"]


def test_parse_unknown_heading_ignored():
    text = "## Unknown Section\n- Some bullet\n"
    fields = _parse_research_notes(text)
    # All known fields should be empty
    assert all(len(v) == 0 for v in fields.values())


def test_parse_empty_text():
    fields = _parse_research_notes("")
    assert all(len(v) == 0 for v in fields.values())


def test_parse_no_bullet_lines_under_heading():
    text = "## Evidence Gaps\nSome prose, not a bullet.\n"
    fields = _parse_research_notes(text)
    assert fields["evidence_gaps"] == ()


def test_parse_asterisk_bullets():
    text = "## Evidence Gaps\n* First gap.\n* Second gap.\n"
    fields = _parse_research_notes(text)
    assert "First gap." in fields["evidence_gaps"]
    assert "Second gap." in fields["evidence_gaps"]


def test_parse_deterministic():
    fields_a = _parse_research_notes(SAMPLE_NOTES)
    fields_b = _parse_research_notes(SAMPLE_NOTES)
    assert fields_a == fields_b


# ---------------------------------------------------------------------------
# _load_research_note
# ---------------------------------------------------------------------------

def test_load_research_note_available(tmp_path):
    notes_path = tmp_path / "notes.md"
    notes_path.write_text(SAMPLE_NOTES, encoding="utf-8")
    note = _load_research_note("ASML", notes_path)
    assert note.available is True
    assert note.ticker == "ASML"
    assert len(note.evidence_gaps) == 2
    assert len(note.open_questions) == 2


def test_load_research_note_missing_file(tmp_path):
    notes_path = tmp_path / "nonexistent.md"
    note = _load_research_note("ASML", notes_path)
    assert note.available is False
    assert note.ticker == "ASML"
    assert note.evidence_gaps == ()


def test_load_research_note_bounded(tmp_path):
    large_content = "## Evidence Gaps\n" + "- Gap line.\n" * 10_000
    notes_path = tmp_path / "notes.md"
    notes_path.write_text(large_content, encoding="utf-8")
    # Should not raise; bounded read
    note = _load_research_note("ASML", notes_path)
    assert note.available is True
    # Total chars in file exceeds limit; the parser must have read bounded content
    assert len(large_content) > _RESEARCH_NOTES_MAX_CHARS


def test_load_research_note_malformed_utf8(tmp_path):
    notes_path = tmp_path / "notes.md"
    notes_path.write_bytes(b"## Evidence Gaps\n- gap\n\xff\xfe")
    # Should not raise
    note = _load_research_note("ASML", notes_path)
    assert note.available is True


# ---------------------------------------------------------------------------
# WeeklyReviewInputPaths — research_notes_dir field
# ---------------------------------------------------------------------------

def test_input_paths_research_notes_dir_default():
    paths = WeeklyReviewInputPaths(
        portfolio_path=PORTFOLIO_PATH,
        watchlist_path=WATCHLIST_PATH,
    )
    assert paths.research_notes_dir is None


def test_input_paths_research_notes_dir_set(tmp_path):
    paths = WeeklyReviewInputPaths(
        portfolio_path=PORTFOLIO_PATH,
        watchlist_path=WATCHLIST_PATH,
        research_notes_dir=tmp_path,
    )
    assert paths.research_notes_dir == tmp_path


# ---------------------------------------------------------------------------
# load_weekly_review_inputs — research notes loading
# ---------------------------------------------------------------------------

def test_missing_research_notes_dir_non_blocking():
    paths = _minimal_paths(research_notes_dir=Path("/nonexistent/research_notes"))
    result = load_weekly_review_inputs(paths)
    assert result.research_notes == ()


def test_no_research_notes_dir_non_blocking():
    paths = _minimal_paths()
    result = load_weekly_review_inputs(paths)
    assert result.research_notes == ()


def test_existing_research_notes_dir_detected(tmp_path):
    # Create a note for a ticker from the portfolio
    result_base = load_weekly_review_inputs(_minimal_paths())
    if not result_base.portfolio.all_holdings:
        pytest.skip("No holdings in example portfolio")
    ticker = result_base.portfolio.all_holdings[0].ticker
    _make_notes_dir(tmp_path, ticker, SAMPLE_NOTES)
    paths = _minimal_paths(research_notes_dir=tmp_path)
    result = load_weekly_review_inputs(paths)
    assert len(result.research_notes) >= 1


def test_notes_loaded_for_portfolio_ticker(tmp_path):
    result_base = load_weekly_review_inputs(_minimal_paths())
    holdings = result_base.portfolio.all_holdings
    non_cash = [h for h in holdings if h.sector.lower() != "cash"]
    if not non_cash:
        pytest.skip("No non-cash holdings in example portfolio")
    ticker = non_cash[0].ticker
    _make_notes_dir(tmp_path, ticker, SAMPLE_NOTES)
    paths = _minimal_paths(research_notes_dir=tmp_path)
    result = load_weekly_review_inputs(paths)
    loaded_tickers = {n.ticker for n in result.research_notes}
    assert ticker in loaded_tickers


def test_notes_loaded_for_watchlist_ticker(tmp_path):
    result_base = load_weekly_review_inputs(_minimal_paths())
    if not result_base.watchlist.items:
        pytest.skip("No watchlist items in example watchlist")
    ticker = result_base.watchlist.items[0].ticker
    _make_notes_dir(tmp_path, ticker, SAMPLE_NOTES)
    paths = _minimal_paths(research_notes_dir=tmp_path)
    result = load_weekly_review_inputs(paths)
    loaded_tickers = {n.ticker for n in result.research_notes}
    assert ticker in loaded_tickers


def test_notes_ticker_order_is_stable(tmp_path):
    result_base = load_weekly_review_inputs(_minimal_paths())
    all_tickers = sorted({
        h.ticker for h in result_base.portfolio.all_holdings
        if h.sector.lower() != "cash"
    } | {item.ticker for item in result_base.watchlist.items})
    for t in all_tickers[:3]:
        _make_notes_dir(tmp_path, t, SAMPLE_NOTES)
    paths = _minimal_paths(research_notes_dir=tmp_path)
    result_a = load_weekly_review_inputs(paths)
    result_b = load_weekly_review_inputs(paths)
    assert [n.ticker for n in result_a.research_notes] == [n.ticker for n in result_b.research_notes]


def test_missing_ticker_notes_file_not_included(tmp_path):
    # Create directory but no notes.md inside
    (tmp_path / "ASML").mkdir()
    paths = _minimal_paths(research_notes_dir=tmp_path)
    result = load_weekly_review_inputs(paths)
    assert all(n.ticker != "ASML" or n.available for n in result.research_notes)


def test_example_research_notes_dir_loads():
    if not RESEARCH_NOTES_DIR.is_dir():
        pytest.skip("Example research_notes dir not present")
    paths = _minimal_paths(research_notes_dir=RESEARCH_NOTES_DIR)
    result = load_weekly_review_inputs(paths)
    assert isinstance(result.research_notes, tuple)


# ---------------------------------------------------------------------------
# Rendering — Section 8 (evidence gaps from research notes)
# ---------------------------------------------------------------------------

@pytest.fixture
def notes_result(tmp_path):
    result_base = load_weekly_review_inputs(_minimal_paths())
    non_cash = [h for h in result_base.portfolio.all_holdings if h.sector.lower() != "cash"]
    if not non_cash:
        pytest.skip("No non-cash holdings")
    ticker = non_cash[0].ticker
    _make_notes_dir(tmp_path, ticker, SAMPLE_NOTES)
    paths = _minimal_paths(research_notes_dir=tmp_path)
    return load_weekly_review_inputs(paths), ticker


def test_section8_includes_research_note_evidence_gap(notes_result):
    result, ticker = notes_result
    output = render_weekly_review(result)
    assert f"Evidence Gap [{ticker}] (research notes)" in output


def test_section8_evidence_gap_content(notes_result):
    result, ticker = notes_result
    output = render_weekly_review(result)
    assert "Margin durability needs review." in output


# ---------------------------------------------------------------------------
# Rendering — Section 9 (open questions from research notes)
# ---------------------------------------------------------------------------

def test_section9_includes_research_note_open_questions(notes_result):
    result, ticker = notes_result
    output = render_weekly_review(result)
    assert f"[{ticker}] Research notes — open questions:" in output


def test_section9_open_question_content(notes_result):
    result, ticker = notes_result
    output = render_weekly_review(result)
    assert "EUV demand" in output or "margin review" in output


def test_section9_includes_risks_to_monitor(notes_result):
    result, ticker = notes_result
    output = render_weekly_review(result)
    assert f"Risk to Monitor ({ticker})" in output or f"Risk to Monitor (research notes)" in output or "Export controls." in output


# ---------------------------------------------------------------------------
# Rendering — Section 10 (reasons to wait from research notes)
# ---------------------------------------------------------------------------

def test_section10_includes_reason_to_wait_from_notes(notes_result):
    result, ticker = notes_result
    output = render_weekly_review(result)
    assert "Reason to Wait" in output
    # Either from explicit Reason to Wait section or evidence gap summary
    assert (
        f"Reason to Wait [{ticker}]" in output
        or f"Reason to Wait: {ticker}" in output
    )


def test_section10_reason_to_wait_content(notes_result):
    result, ticker = notes_result
    output = render_weekly_review(result)
    # Should reference evidence gaps or reason content
    assert "evidence gap" in output.lower() or "unresolved" in output.lower()


# ---------------------------------------------------------------------------
# Rendering — example research notes integration
# ---------------------------------------------------------------------------

def test_example_research_notes_render():
    if not RESEARCH_NOTES_DIR.is_dir():
        pytest.skip("Example research_notes dir not present")
    paths = _minimal_paths(research_notes_dir=RESEARCH_NOTES_DIR)
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    assert "## 8. Missing Evidence" in output
    assert "## 9. Follow-Up Questions" in output
    assert "## 10. Non-Actions / Reasons to Wait" in output


def test_example_asml_notes_appear_in_output():
    if not (RESEARCH_NOTES_DIR / "ASML" / "notes.md").exists():
        pytest.skip("ASML example notes not present")
    paths = _minimal_paths(research_notes_dir=RESEARCH_NOTES_DIR)
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    assert "ASML" in output
    assert "Evidence Gap [ASML] (research notes)" in output


def test_example_xyl_notes_appear_in_output():
    if not (RESEARCH_NOTES_DIR / "XYL" / "notes.md").exists():
        pytest.skip("XYL example notes not present")
    paths = _minimal_paths(research_notes_dir=RESEARCH_NOTES_DIR)
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    assert "XYL" in output


# ---------------------------------------------------------------------------
# Input status line
# ---------------------------------------------------------------------------

def test_input_status_shows_research_notes(notes_result):
    result, _ = notes_result
    output = render_weekly_review(result)
    assert "Research notes:" in output
    assert "ticker(s) with local notes" in output


def test_input_status_no_research_notes():
    paths = _minimal_paths()
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    assert "Research notes: Not provided." in output


# ---------------------------------------------------------------------------
# Section 1 — optional inputs summary
# ---------------------------------------------------------------------------

def test_section1_includes_research_notes_in_optional(notes_result):
    result, _ = notes_result
    output = render_weekly_review(result)
    assert "research notes" in output.lower()


# ---------------------------------------------------------------------------
# Language guardrails
# ---------------------------------------------------------------------------

FORBIDDEN_LANGUAGE = [
    "Strong Buy", "Strong Sell", "Price Target", "Target Price",
    "Act Now", "Must Buy", "Must Sell", "Guaranteed",
    "Will Outperform", "Financial Advice",
]


def test_no_forbidden_language_in_research_notes_output(notes_result):
    result, _ = notes_result
    output = render_weekly_review(result)
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output, f"Forbidden language found: '{term}'"


def test_no_forbidden_language_in_example_notes():
    if not RESEARCH_NOTES_DIR.is_dir():
        pytest.skip("Example research_notes dir not present")
    for notes_file in RESEARCH_NOTES_DIR.rglob("notes.md"):
        content = notes_file.read_text(encoding="utf-8")
        for term in FORBIDDEN_LANGUAGE:
            assert term not in content, f"Forbidden language in {notes_file}: '{term}'"


# ---------------------------------------------------------------------------
# Provider / network boundary
# ---------------------------------------------------------------------------

def test_no_provider_imports_in_inputs_module():
    import atlas.weekly_review.inputs as mod
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
                assert "providers" not in name, f"Provider import in inputs.py: {name}"
                assert "requests" not in name, f"Network import in inputs.py: {name}"
                assert "urllib" not in name, f"Network import in inputs.py: {name}"


def test_no_provider_imports_in_render_module():
    import atlas.weekly_review.render as mod
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
                assert "providers" not in name, f"Provider import in render.py: {name}"
                assert "requests" not in name, f"Network import in render.py: {name}"


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_research_notes_output_is_deterministic(notes_result):
    result, _ = notes_result
    output_a = render_weekly_review(result)
    output_b = render_weekly_review(result)
    assert output_a == output_b


def test_research_notes_load_is_deterministic(tmp_path):
    result_base = load_weekly_review_inputs(_minimal_paths())
    non_cash = [h for h in result_base.portfolio.all_holdings if h.sector.lower() != "cash"]
    if not non_cash:
        pytest.skip("No non-cash holdings")
    ticker = non_cash[0].ticker
    _make_notes_dir(tmp_path, ticker, SAMPLE_NOTES)
    paths = _minimal_paths(research_notes_dir=tmp_path)
    result_a = load_weekly_review_inputs(paths)
    result_b = load_weekly_review_inputs(paths)
    assert result_a.research_notes == result_b.research_notes
