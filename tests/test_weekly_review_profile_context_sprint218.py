"""Sprint 218 — Investor profile principles and constraints in Weekly Review.

Checks:
- principles and constraints are parsed from investor_profile.json
- risk_tolerance and time_horizon are parsed when present
- missing profile remains warning, not failure
- malformed principles field warns and renders safely
- malformed constraints field warns and renders safely
- Section 5 renders risk tolerance, time horizon, constraints, and deferred note
- Section 6 renders principles and constraints as guardrails
- Section 10 includes reasons to wait derived from principles and constraints
- Section 10 remains non-empty without profile
- output is deterministic for same profile input
- output avoids forbidden language
- no provider/network imports are introduced
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.weekly_review.inputs import (
    WeeklyReviewInputPaths,
    WeeklyReviewInputWarning,
    WeeklyReviewLoadResult,
    WeeklyReviewPortfolioInput,
    WeeklyReviewWatchlistInput,
    load_weekly_review_inputs,
)
from atlas.weekly_review.render import render_weekly_review

REPO_ROOT = Path(__file__).parent.parent
EXAMPLE_DIR = REPO_ROOT / "examples" / "weekly_review"
REALISTIC_DIR = REPO_ROOT / "examples" / "weekly_review_realistic"

FORBIDDEN_TERMS = [
    "buy", "sell", "strong buy", "strong sell", "price target", "target price",
    "urgent", "act now", "must buy", "must sell", "guaranteed", "will outperform",
    "financial advice",
]

_MINIMAL_PORTFOLIO = {
    "as_of": "2026-01-01",
    "positions": [
        {"ticker": "MSFT", "weight": 0.6, "company": "Microsoft", "sector": "Technology"},
        {"ticker": "CASH", "weight": 0.4, "company": "Cash", "sector": "Cash"},
    ],
}
_MINIMAL_WATCHLIST = {
    "name": "Test Watchlist",
    "as_of": "2026-01-01",
    "items": [{"ticker": "ADYEN", "name": "Adyen", "status": "Research"}],
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def tmp_dir(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("sprint218")


def _write_bundle(
    tmp_dir: Path,
    profile: dict | None,
    suffix: str = "",
) -> WeeklyReviewInputPaths:
    port_path = tmp_dir / f"portfolio{suffix}.json"
    watch_path = tmp_dir / f"watchlist{suffix}.json"
    port_path.write_text(json.dumps(_MINIMAL_PORTFOLIO), encoding="utf-8")
    watch_path.write_text(json.dumps(_MINIMAL_WATCHLIST), encoding="utf-8")

    profile_path = None
    if profile is not None:
        profile_path = tmp_dir / f"profile{suffix}.json"
        profile_path.write_text(json.dumps(profile), encoding="utf-8")

    return WeeklyReviewInputPaths(
        portfolio_path=port_path,
        watchlist_path=watch_path,
        profile_path=profile_path,
        as_of="2026-01-01",
    )


_FULL_PROFILE = {
    "risk_tolerance": "Balanced",
    "time_horizon": "10+ years",
    "principles": [
        "Evidence before opinion",
        "No action is an acceptable outcome",
        "Keep reserve capacity",
    ],
    "constraints": [
        "Avoid excessive concentration",
        "Avoid decisions based only on recent price movement",
    ],
}


# ---------------------------------------------------------------------------
# Parsing: principles and constraints
# ---------------------------------------------------------------------------


def test_principles_parsed_from_profile(tmp_dir):
    paths = _write_bundle(tmp_dir, _FULL_PROFILE, suffix="_p1")
    result = load_weekly_review_inputs(paths)
    assert result.profile_principles == (
        "Evidence before opinion",
        "No action is an acceptable outcome",
        "Keep reserve capacity",
    )


def test_constraints_parsed_from_profile(tmp_dir):
    paths = _write_bundle(tmp_dir, _FULL_PROFILE, suffix="_p2")
    result = load_weekly_review_inputs(paths)
    assert result.profile_constraints == (
        "Avoid excessive concentration",
        "Avoid decisions based only on recent price movement",
    )


def test_risk_tolerance_parsed(tmp_dir):
    paths = _write_bundle(tmp_dir, _FULL_PROFILE, suffix="_p3")
    result = load_weekly_review_inputs(paths)
    assert result.profile_risk_tolerance == "Balanced"


def test_time_horizon_parsed(tmp_dir):
    paths = _write_bundle(tmp_dir, _FULL_PROFILE, suffix="_p4")
    result = load_weekly_review_inputs(paths)
    assert result.profile_time_horizon == "10+ years"


def test_empty_principles_list_gives_empty_tuple(tmp_dir):
    profile = {**_FULL_PROFILE, "principles": []}
    paths = _write_bundle(tmp_dir, profile, suffix="_p5")
    result = load_weekly_review_inputs(paths)
    assert result.profile_principles == ()


def test_empty_constraints_list_gives_empty_tuple(tmp_dir):
    profile = {**_FULL_PROFILE, "constraints": []}
    paths = _write_bundle(tmp_dir, profile, suffix="_p6")
    result = load_weekly_review_inputs(paths)
    assert result.profile_constraints == ()


def test_missing_principles_field_gives_empty_tuple(tmp_dir):
    profile = {"risk_tolerance": "Balanced", "time_horizon": "5 years", "constraints": ["Avoid X"]}
    paths = _write_bundle(tmp_dir, profile, suffix="_p7")
    result = load_weekly_review_inputs(paths)
    assert result.profile_principles == ()


def test_missing_constraints_field_gives_empty_tuple(tmp_dir):
    profile = {"risk_tolerance": "Balanced", "time_horizon": "5 years", "principles": ["Evidence first"]}
    paths = _write_bundle(tmp_dir, profile, suffix="_p8")
    result = load_weekly_review_inputs(paths)
    assert result.profile_constraints == ()


# ---------------------------------------------------------------------------
# Parsing: malformed fields
# ---------------------------------------------------------------------------


def test_malformed_principles_warns(tmp_dir):
    profile = {**_FULL_PROFILE, "principles": "not a list"}
    paths = _write_bundle(tmp_dir, profile, suffix="_m1")
    result = load_weekly_review_inputs(paths)
    codes = [w.code for w in result.warnings]
    assert "invalid_profile_principles" in codes


def test_malformed_principles_gives_empty_tuple(tmp_dir):
    profile = {**_FULL_PROFILE, "principles": "not a list"}
    paths = _write_bundle(tmp_dir, profile, suffix="_m2")
    result = load_weekly_review_inputs(paths)
    assert result.profile_principles == ()


def test_malformed_constraints_warns(tmp_dir):
    profile = {**_FULL_PROFILE, "constraints": 42}
    paths = _write_bundle(tmp_dir, profile, suffix="_m3")
    result = load_weekly_review_inputs(paths)
    codes = [w.code for w in result.warnings]
    assert "invalid_profile_constraints" in codes


def test_malformed_constraints_gives_empty_tuple(tmp_dir):
    profile = {**_FULL_PROFILE, "constraints": 42}
    paths = _write_bundle(tmp_dir, profile, suffix="_m4")
    result = load_weekly_review_inputs(paths)
    assert result.profile_constraints == ()


def test_malformed_principles_does_not_fail_load(tmp_dir):
    profile = {**_FULL_PROFILE, "principles": {"not": "a list"}}
    paths = _write_bundle(tmp_dir, profile, suffix="_m5")
    result = load_weekly_review_inputs(paths)
    assert result.profile_available is True
    assert result.profile_principles == ()


def test_malformed_constraints_does_not_fail_load(tmp_dir):
    profile = {**_FULL_PROFILE, "constraints": True}
    paths = _write_bundle(tmp_dir, profile, suffix="_m6")
    result = load_weekly_review_inputs(paths)
    assert result.profile_available is True
    assert result.profile_constraints == ()


# ---------------------------------------------------------------------------
# Missing profile
# ---------------------------------------------------------------------------


def test_missing_profile_warns_not_fails(tmp_dir):
    paths = _write_bundle(tmp_dir, profile=None, suffix="_np1")
    result = load_weekly_review_inputs(paths)
    assert result.profile_available is False
    codes = [w.code for w in result.warnings]
    assert "missing_optional_profile" in codes


def test_missing_profile_gives_empty_principles(tmp_dir):
    paths = _write_bundle(tmp_dir, profile=None, suffix="_np2")
    result = load_weekly_review_inputs(paths)
    assert result.profile_principles == ()


def test_missing_profile_gives_empty_constraints(tmp_dir):
    paths = _write_bundle(tmp_dir, profile=None, suffix="_np3")
    result = load_weekly_review_inputs(paths)
    assert result.profile_constraints == ()


# ---------------------------------------------------------------------------
# Section 5: Portfolio Fit and Suitability Notes
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def output_with_profile(tmp_dir) -> str:
    paths = _write_bundle(tmp_dir, _FULL_PROFILE, suffix="_s5")
    result = load_weekly_review_inputs(paths)
    return render_weekly_review(result)


def test_section5_present(output_with_profile):
    assert "5. Portfolio Fit and Suitability Notes" in output_with_profile


def test_section5_renders_risk_tolerance(output_with_profile):
    assert "Balanced" in output_with_profile


def test_section5_renders_time_horizon(output_with_profile):
    assert "10+ years" in output_with_profile


def test_section5_renders_constraints(output_with_profile):
    assert "Avoid excessive concentration" in output_with_profile


def test_section5_notes_suitability_deferred(output_with_profile):
    assert "deferred" in output_with_profile.lower()


# ---------------------------------------------------------------------------
# Section 6: Risk and Principle Guardrails
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def output_s6(tmp_dir) -> str:
    paths = _write_bundle(tmp_dir, _FULL_PROFILE, suffix="_s6")
    result = load_weekly_review_inputs(paths)
    return render_weekly_review(result)


def test_section6_present(output_s6):
    assert "6. Risk and Principle Guardrails" in output_s6


def test_section6_renders_principles(output_s6):
    assert "Evidence before opinion" in output_s6


def test_section6_renders_all_principles(output_s6):
    for p in _FULL_PROFILE["principles"]:
        assert p in output_s6


def test_section6_renders_constraints(output_s6):
    assert "Avoid excessive concentration" in output_s6


def test_section6_labels_as_guardrail(output_s6):
    assert "Principle:" in output_s6


# ---------------------------------------------------------------------------
# Section 10: Non-Actions / Reasons to Wait
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def output_s10(tmp_dir) -> str:
    paths = _write_bundle(tmp_dir, _FULL_PROFILE, suffix="_s10")
    result = load_weekly_review_inputs(paths)
    return render_weekly_review(result)


def test_section10_present(output_s10):
    assert "10. Non-Actions / Reasons to Wait" in output_s10


def test_section10_includes_principle_reason_to_wait(output_s10):
    assert "Reason to Wait" in output_s10
    assert "Evidence before opinion" in output_s10


def test_section10_includes_constraint_no_action(output_s10):
    assert "No Action Warranted" in output_s10
    assert "Avoid excessive concentration" in output_s10


def test_section10_all_principles_in_s10(output_s10):
    section = output_s10.split("10. Non-Actions")[1]
    for p in _FULL_PROFILE["principles"]:
        assert p in section, f"Principle not found in Section 10: {p!r}"


def test_section10_all_constraints_in_s10(output_s10):
    section = output_s10.split("10. Non-Actions")[1]
    for c in _FULL_PROFILE["constraints"]:
        assert c in section, f"Constraint not found in Section 10: {c!r}"


def test_section10_non_empty_without_profile(tmp_dir):
    paths = _write_bundle(tmp_dir, profile=None, suffix="_s10_np")
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    section = output.split("10. Non-Actions")[1]
    assert section.strip()


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_output_deterministic_with_same_profile(tmp_dir):
    paths = _write_bundle(tmp_dir, _FULL_PROFILE, suffix="_det1")
    result1 = load_weekly_review_inputs(paths)
    result2 = load_weekly_review_inputs(paths)
    assert render_weekly_review(result1) == render_weekly_review(result2)


def test_principles_order_stable(tmp_dir):
    paths = _write_bundle(tmp_dir, _FULL_PROFILE, suffix="_ord")
    result = load_weekly_review_inputs(paths)
    assert list(result.profile_principles) == _FULL_PROFILE["principles"]


def test_constraints_order_stable(tmp_dir):
    paths = _write_bundle(tmp_dir, _FULL_PROFILE, suffix="_cord")
    result = load_weekly_review_inputs(paths)
    assert list(result.profile_constraints) == _FULL_PROFILE["constraints"]


# ---------------------------------------------------------------------------
# Language guardrails
# ---------------------------------------------------------------------------


def test_output_no_forbidden_language(tmp_dir):
    paths = _write_bundle(tmp_dir, _FULL_PROFILE, suffix="_lang")
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result).lower()
    for term in FORBIDDEN_TERMS:
        assert term not in output, f"Forbidden term {term!r} found in output"


# ---------------------------------------------------------------------------
# Provider / network boundary
# ---------------------------------------------------------------------------


def test_weekly_review_inputs_has_no_provider_dependency():
    """inputs.py must not import from atlas.providers."""
    import ast, inspect
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
                assert "providers" not in (name or ""), (
                    f"Provider import found in inputs.py: {name}"
                )


def test_weekly_review_render_has_no_provider_dependency():
    """render.py must not import from atlas.providers."""
    import ast, inspect
    import atlas.weekly_review.render as mod
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
                assert "providers" not in (name or ""), (
                    f"Provider import found in render.py: {name}"
                )


# ---------------------------------------------------------------------------
# Realistic example bundle integration
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


def test_realistic_profile_principles_loaded(realistic_result):
    assert len(realistic_result.profile_principles) > 0


def test_realistic_profile_constraints_loaded(realistic_result):
    assert len(realistic_result.profile_constraints) > 0


def test_realistic_risk_tolerance_loaded(realistic_result):
    assert realistic_result.profile_risk_tolerance


def test_realistic_time_horizon_loaded(realistic_result):
    assert realistic_result.profile_time_horizon


def test_realistic_section10_principles_present(realistic_result):
    output = render_weekly_review(realistic_result)
    section = output.split("10. Non-Actions")[1]
    # At least one principle should appear in section 10
    assert any(p in section for p in realistic_result.profile_principles)


def test_realistic_section10_constraints_present(realistic_result):
    output = render_weekly_review(realistic_result)
    section = output.split("10. Non-Actions")[1]
    assert any(c in section for c in realistic_result.profile_constraints)


def test_realistic_no_forbidden_language(realistic_result):
    output = render_weekly_review(realistic_result).lower()
    for term in FORBIDDEN_TERMS:
        assert term not in output, f"Forbidden term {term!r} found in realistic output"
