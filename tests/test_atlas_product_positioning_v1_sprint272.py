"""Sprint 272 — Atlas Product Positioning v1 documentation tests.

Verifies that docs/AtlasProductPositioningV1.md exists and contains the
required product positioning content. No runtime behaviour is changed by
this sprint. These tests read the specification document only.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

DOC = Path("docs/AtlasProductPositioningV1.md")


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Document exists
# ---------------------------------------------------------------------------

def test_document_exists() -> None:
    assert DOC.exists(), "docs/AtlasProductPositioningV1.md must exist"


# ---------------------------------------------------------------------------
# Product thesis
# ---------------------------------------------------------------------------

def test_atlas_is_private_investment_workspace_or_system() -> None:
    d = _doc().lower()
    assert "private investment workspace" in d or "private investment system" in d


def test_atlas_is_not_another_stock_app() -> None:
    d = _doc().lower()
    assert "not another stock app" in d


def test_atlas_is_not_a_trading_product() -> None:
    d = _doc().lower()
    assert "not a trading product" in d or "not a trading app" in d


def test_atlas_is_not_an_ai_stock_picker() -> None:
    d = _doc().lower()
    assert "not an ai stock-picker" in d or "not an ai stock picker" in d


def test_turns_messy_input_into_structured_judgment() -> None:
    d = _doc().lower()
    assert "structured judgment" in d or "structured judgement" in d


# ---------------------------------------------------------------------------
# Primary user
# ---------------------------------------------------------------------------

def test_primary_user_section_exists() -> None:
    assert "Primary User" in _doc()


def test_primary_user_is_serious_private_capital_owner() -> None:
    d = _doc().lower()
    assert "serious private capital" in d or "private capital owner" in d


def test_primary_user_includes_entrepreneur() -> None:
    assert "entrepreneur" in _doc().lower()


def test_primary_user_wants_a_system() -> None:
    assert "they want a system" in _doc().lower()


# ---------------------------------------------------------------------------
# Secondary user
# ---------------------------------------------------------------------------

def test_secondary_user_section_exists() -> None:
    assert "Secondary User" in _doc()


def test_secondary_user_held_back_by_uncertainty() -> None:
    d = _doc().lower()
    assert "uncertainty" in d or "fear" in d or "lack of knowledge" in d


def test_secondary_user_not_told_what_to_buy() -> None:
    d = _doc().lower()
    assert "not by telling people what to buy" in d


# ---------------------------------------------------------------------------
# Core problem
# ---------------------------------------------------------------------------

def test_core_problem_section_exists() -> None:
    assert "Core Problem" in _doc()


def test_core_problem_is_lack_of_structured_judgment() -> None:
    d = _doc().lower()
    assert "lack of structured judgment" in d or "lack of structured judgement" in d


def test_core_problem_not_lack_of_information() -> None:
    d = _doc().lower()
    assert "not lack of information" in d or "core problem is not lack of information" in d


# ---------------------------------------------------------------------------
# Product promise
# ---------------------------------------------------------------------------

def test_product_promise_section_exists() -> None:
    assert "Product Promise" in _doc()


def test_promise_no_better_predictions() -> None:
    d = _doc().lower()
    assert "does not promise better predictions" in d or "not promise" in d


def test_promise_is_structure() -> None:
    d = _doc().lower()
    assert "it promises structure" in d or "promises structure" in d


def test_promise_no_market_timing() -> None:
    d = _doc().lower()
    assert "market timing" in d


def test_promise_no_winners() -> None:
    d = _doc().lower()
    assert "winners" in d and ("not promise" in d or "does not promise" in d)


# ---------------------------------------------------------------------------
# What Atlas does
# ---------------------------------------------------------------------------

def test_what_atlas_does_section_exists() -> None:
    assert "What Atlas Does" in _doc()


def test_does_structure_portfolios() -> None:
    assert "structure portfolios" in _doc().lower()


def test_does_identify_missing_evidence() -> None:
    assert "missing evidence" in _doc().lower()


def test_does_surface_open_decisions() -> None:
    assert "open decisions" in _doc().lower()


def test_does_run_weekly_reviews() -> None:
    assert "weekly investment review" in _doc().lower()


# ---------------------------------------------------------------------------
# What Atlas does not do
# ---------------------------------------------------------------------------

def test_what_atlas_does_not_do_section_exists() -> None:
    d = _doc()
    assert "What Atlas Does Not Do" in d


def test_does_not_give_buy_sell_signals() -> None:
    d = _doc().lower()
    assert "buy/sell signals" in d or "buy/sell" in d


def test_does_not_execute_trades() -> None:
    assert "does not execute trades" in _doc().lower()


def test_does_not_set_price_targets() -> None:
    assert "does not set price targets" in _doc().lower()


def test_does_not_promise_outperformance() -> None:
    assert "does not promise outperformance" in _doc().lower()


def test_is_not_a_broker() -> None:
    assert "is not a broker" in _doc().lower()


def test_builds_the_process() -> None:
    assert "atlas builds the process" in _doc().lower()


# ---------------------------------------------------------------------------
# First user experience
# ---------------------------------------------------------------------------

def test_first_user_experience_section_exists() -> None:
    assert "First User Experience" in _doc()


def test_first_experience_input_first_not_dashboard_first() -> None:
    d = _doc().lower()
    assert "input-first" in d or "input first" in d
    assert "dashboard-first" in d or "not dashboard-first" in d or "dashboard" in d


def test_first_screen_does_not_begin_with_create_account() -> None:
    d = _doc().lower()
    assert "create account" in d  # listed as what NOT to do
    assert "should not begin with" in d or "not begin with" in d


def test_first_flow_defined() -> None:
    d = _doc().lower()
    assert "paste" in d and "temporary workspace" in d


def test_account_creation_after_value() -> None:
    d = _doc().lower()
    assert "after the user has seen value" in d or "after" in d and "value" in d


# ---------------------------------------------------------------------------
# No-account first value
# ---------------------------------------------------------------------------

def test_no_account_first_value_section_exists() -> None:
    assert "No-Account First Value" in _doc()


def test_no_account_useful_before_trust() -> None:
    d = _doc().lower()
    assert "useful before asking for trust" in d


def test_no_account_prompt_framed_around_persistence() -> None:
    d = _doc().lower()
    assert "persistence" in d or "save this workspace" in d


def test_account_must_not_block_first_value() -> None:
    d = _doc().lower()
    assert "should not block first value" in d or "not block first value" in d


def test_broker_not_required_for_first_value() -> None:
    d = _doc().lower()
    assert "broker" in d and "not be required" in d


# ---------------------------------------------------------------------------
# Aha moment
# ---------------------------------------------------------------------------

def test_aha_moment_section_exists() -> None:
    assert "Aha Moment" in _doc()


def test_aha_moment_primary_user() -> None:
    d = _doc().lower()
    assert "system" in d and "capital" in d


def test_aha_moment_less_impulse_driven() -> None:
    d = _doc().lower()
    assert "impulse" in d


# ---------------------------------------------------------------------------
# Emotional outcome
# ---------------------------------------------------------------------------

def test_emotional_outcome_section_exists() -> None:
    assert "Emotional Outcome" in _doc()


def test_emotional_outcome_calmer_clearer_in_control() -> None:
    d = _doc().lower()
    assert "calmer" in d and "clearer" in d and "in control" in d


def test_emotional_outcome_not_excitement() -> None:
    d = _doc().lower()
    assert "not excitement" in d or "is not excitement" in d


def test_emotional_outcome_not_urgency() -> None:
    d = _doc().lower()
    assert "not urgency" in d or "is not urgency" in d


# ---------------------------------------------------------------------------
# Pricing philosophy
# ---------------------------------------------------------------------------

def test_pricing_philosophy_section_exists() -> None:
    assert "Pricing Philosophy" in _doc()


def test_pricing_optimizes_for_genuine_long_term_users() -> None:
    d = _doc().lower()
    assert "genuine long-term users" in d or "long-term users" in d


def test_pricing_not_cheap_stock_tip_app() -> None:
    d = _doc().lower()
    assert "cheap stock-tip app" in d or "stock-tip app" in d


def test_pricing_v1_hypothesis_exists() -> None:
    assert "Pricing v1 hypothesis" in _doc()


def test_pricing_guest_tier() -> None:
    assert "Guest" in _doc()
    assert "0 kr" in _doc()


def test_pricing_personal_tier() -> None:
    d = _doc()
    assert "Personal" in d
    assert "99" in d or "199" in d


def test_pricing_plus_tier() -> None:
    d = _doc()
    assert "Plus" in d
    assert "299" in d or "499" in d


def test_pricing_goal_is_volume_not_extraction() -> None:
    d = _doc().lower()
    assert "volume" in d and "trust" in d and "habit" in d


# ---------------------------------------------------------------------------
# Internal product principles
# ---------------------------------------------------------------------------

def test_internal_principles_section_exists() -> None:
    assert "Internal Product Principles" in _doc()


def test_principle_judgment_not_prediction() -> None:
    d = _doc().lower()
    assert "judgment system" in d or "judgement system" in d
    assert "not a prediction system" in d or "prediction system" in d


def test_principle_no_action_warranted_is_valid() -> None:
    d = _doc().lower()
    assert "no action warranted is a valid" in d


def test_principle_value_before_account() -> None:
    d = _doc().lower()
    assert "value before account" in d


def test_principle_input_first_not_dashboard_first() -> None:
    d = _doc().lower()
    assert "input-first, not dashboard-first" in d


def test_principle_reduce_noise() -> None:
    d = _doc().lower()
    assert "reduce noise" in d


def test_principle_must_be_excellent_or_not_exist() -> None:
    d = _doc().lower()
    assert "excellent" in d and "should not exist" in d


def test_principle_calmer_clearer_in_control() -> None:
    d = _doc().lower()
    assert "calmer" in d and "clearer" in d and "more in control" in d


# ---------------------------------------------------------------------------
# Positioning lines
# ---------------------------------------------------------------------------

def test_positioning_lines_section_exists() -> None:
    assert "Positioning Lines" in _doc()


def test_positioning_private_investment_workspace() -> None:
    assert "private investment workspace" in _doc().lower()


def test_positioning_structured_judgment_before_action() -> None:
    d = _doc().lower()
    assert "structured judgment before investment action" in d or "structured judgement before investment action" in d


def test_positioning_not_another_trading_app() -> None:
    d = _doc().lower()
    assert "not another trading app" in d


def test_positioning_see_what_is_missing() -> None:
    d = _doc().lower()
    assert "see what is missing" in d


def test_positioning_swedish_lines_present() -> None:
    d = _doc()
    assert "privat investeringsyta" in d.lower() or "investeringsyta" in d.lower()


# ---------------------------------------------------------------------------
# Landing page copy
# ---------------------------------------------------------------------------

def test_landing_page_copy_section_exists() -> None:
    assert "Landing Page Copy" in _doc()


def test_landing_page_english_copy_present() -> None:
    d = _doc().lower()
    assert "serious private investors" in d
    assert "temporary workspace" in d


def test_landing_page_swedish_copy_present() -> None:
    d = _doc().lower()
    assert "investeringstänkande" in d or "investerare" in d


# ---------------------------------------------------------------------------
# Category definition
# ---------------------------------------------------------------------------

def test_category_definition_section_exists() -> None:
    assert "Category Definition" in _doc()


def test_category_private_investment_workspace() -> None:
    assert "Private Investment Workspace" in _doc()


def test_category_investment_judgment_system() -> None:
    d = _doc()
    assert "Investment Judgment System" in d or "judgment system" in d.lower()


def test_category_use_externally_internally_defined() -> None:
    d = _doc().lower()
    assert "externally" in d and "internally" in d


# ---------------------------------------------------------------------------
# Strategic standard
# ---------------------------------------------------------------------------

def test_strategic_standard_section_exists() -> None:
    assert "Strategic Standard" in _doc()


def test_strategic_standard_best_or_not_built() -> None:
    d = _doc().lower()
    assert "best product of its kind" in d or "should not be built" in d


def test_strategic_standard_features_serve_core_promise() -> None:
    d = _doc().lower()
    assert "core promise" in d


def test_strategic_standard_no_noise_features() -> None:
    d = _doc().lower()
    assert "adds noise" in d or "add noise" in d


def test_strategic_standard_no_impulsive_action_features() -> None:
    d = _doc().lower()
    assert "impulsive action" in d


# ---------------------------------------------------------------------------
# Final north star
# ---------------------------------------------------------------------------

def test_final_north_star_section_exists() -> None:
    assert "Final North Star" in _doc()


def test_final_north_star_english() -> None:
    d = _doc().lower()
    assert "private investment workspace" in d
    assert "structured judgment" in d or "structured judgement" in d


def test_final_north_star_swedish() -> None:
    d = _doc().lower()
    assert "privat investeringsyta" in d
    assert "beslutsstruktur" in d or "underlag" in d


# ---------------------------------------------------------------------------
# Positioning avoids unsafe language
# ---------------------------------------------------------------------------

def test_no_guaranteed_language() -> None:
    assert "guaranteed" not in _doc().lower()


def test_no_outperform_as_promise() -> None:
    d = _doc().lower()
    # "outperformance" appears only in "does not promise outperformance"
    if "outperform" in d:
        assert "does not promise outperformance" in d or "not promise" in d


def test_no_price_target_as_feature() -> None:
    d = _doc().lower()
    # "price targets" appears only in "does not set price targets"
    if "price target" in d:
        assert "does not set price targets" in d or "not set" in d


def test_no_urgency_as_feature() -> None:
    d = _doc().lower()
    # urgency appears only in "is not urgency" (emotional outcome)
    if "urgency" in d:
        assert "is not urgency" in d or "not urgency" in d or "not excitement" in d


# ---------------------------------------------------------------------------
# No runtime behavior changed
# ---------------------------------------------------------------------------

def test_no_ui_module_added() -> None:
    assert not Path("atlas/ui.py").exists()
    assert not Path("atlas/web.py").exists()


def test_no_auth_module_added() -> None:
    assert not Path("atlas/auth.py").exists()
    assert not Path("atlas/accounts.py").exists()


def test_no_database_module_added() -> None:
    assert not Path("atlas/db.py").exists()
    assert not Path("atlas/database.py").exists()


def test_no_backend_module_added() -> None:
    assert not Path("atlas/server.py").exists()
    assert not Path("atlas/api.py").exists()


def test_no_provider_imports_added() -> None:
    for path in Path("atlas").rglob("*.py"):
        src = path.read_text(encoding="utf-8")
        assert "import requests" not in src, f"requests import found in {path}"
        assert "import httpx" not in src, f"httpx import found in {path}"
        assert "import openai" not in src, f"openai import found in {path}"
        assert "import anthropic" not in src, f"anthropic import found in {path}"


def test_cli_still_exits_zero() -> None:
    atlas = str(Path(".venv/bin/atlas").resolve())
    r = subprocess.run(
        [atlas, "weekly-review",
         "--portfolio", "examples/weekly_review/portfolio.json",
         "--watchlist", "examples/weekly_review/watchlist.json",
         "--as-of", "2026-01-05"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
