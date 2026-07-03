"""Sprint 178 guardrail tests for atlas/adapters/ package inventory.

Verifies:
- All adapter modules importable and public symbols accessible
- Adapters do not import deleted atlas.reasoning
- Adapters do not import deleted atlas.analysis.* submodules
  (atlas.analysis.scores is NOT deleted — it is an active utility)
- Adapters do not import atlas.providers directly
- Adapters do not import atlas.cli
- Portfolio boundary cleanup remains closed:
  - Portfolio and PortfolioPosition importable from atlas.adapters.portfolio
  - Deleted legacy symbols absent from atlas.adapters.portfolio
  - legacy_portfolio_to_domain_portfolio importable and callable
"""

import ast
import pathlib


# ── Adapter module importability ──────────────────────────────────────────────

def test_adapters_company_analysis_importable():
    from atlas.adapters.company_analysis import company_reports_from_dict  # noqa: F401
    assert callable(company_reports_from_dict)


def test_adapters_knowledge_importable():
    from atlas.adapters.knowledge import knowledge_facts_from_dict  # noqa: F401
    assert callable(knowledge_facts_from_dict)


def test_adapters_portfolio_importable():
    from atlas.adapters.portfolio import (  # noqa: F401
        Portfolio,
        PortfolioPosition,
        legacy_portfolio_to_domain_portfolio,
    )
    assert callable(legacy_portfolio_to_domain_portfolio)


def test_adapters_research_input_importable():
    from atlas.adapters.research_input import research_projects_from_dict  # noqa: F401
    assert callable(research_projects_from_dict)


def test_adapters_watchlist_importable():
    from atlas.adapters.watchlist import (  # noqa: F401
        watchlist_input_from_dict,
        assign_knowledge_facts,
    )
    assert callable(watchlist_input_from_dict)
    assert callable(assign_knowledge_facts)


# ── Portfolio boundary cleanup remains closed ─────────────────────────────────

def test_portfolio_boundary_portfolio_importable():
    """Sprint 178: Portfolio must remain importable from atlas.adapters.portfolio."""
    from atlas.adapters.portfolio import Portfolio  # noqa: F401


def test_portfolio_boundary_portfolio_position_importable():
    """Sprint 178: PortfolioPosition must remain importable from atlas.adapters.portfolio."""
    from atlas.adapters.portfolio import PortfolioPosition  # noqa: F401


def test_portfolio_boundary_translation_fn_importable():
    """Sprint 178: legacy_portfolio_to_domain_portfolio must remain importable."""
    from atlas.adapters.portfolio import legacy_portfolio_to_domain_portfolio  # noqa: F401


def test_portfolio_boundary_deleted_legacy_symbols_absent():
    """Sprint 178: deleted legacy portfolio symbols must not exist in atlas.adapters.portfolio."""
    import atlas.adapters.portfolio as mod
    deleted = [
        "PortfolioAnalysis",
        "PortfolioSignal",
        "PortfolioRecommendation",
        "CompanyPortfolioProfile",
        "PortfolioIntelligenceEngine",
        "portfolio_fit_input_from_profile",
    ]
    for sym in deleted:
        assert not hasattr(mod, sym), (
            f"{sym} must not exist in atlas.adapters.portfolio — was deleted in prior sprints"
        )


# ── Stale import guardrails ───────────────────────────────────────────────────

def test_adapters_do_not_import_deleted_reasoning():
    """No adapter module imports deleted atlas.reasoning."""
    adap_dir = pathlib.Path("atlas/adapters")
    for py_file in adap_dir.glob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.reasoning"), (
                    f"{py_file} imports deleted atlas.reasoning: {node.module}"
                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("atlas.reasoning"), (
                        f"{py_file} imports deleted atlas.reasoning: {alias.name}"
                    )


def test_adapters_do_not_import_deleted_analysis_submodules():
    """No adapter imports deleted atlas.analysis.* submodules.

    NOTE: atlas.analysis.scores is NOT deleted (it is an active utility module
    intentionally kept as of Sprint 140). Only the deleted submodules are checked.
    """
    deleted_analysis = {
        "atlas.analysis.portfolio",
        "atlas.analysis.comparison",
        "atlas.analysis.memory",
        "atlas.analysis.scoring",
        "atlas.analysis.watchlist",
        "atlas.analysis.growth",
        "atlas.analysis.macro",
        "atlas.analysis.moat",
        "atlas.analysis.quality",
        "atlas.analysis.sentiment",
        "atlas.analysis.technicals",
        "atlas.analysis.valuation",
    }
    adap_dir = pathlib.Path("atlas/adapters")
    for py_file in adap_dir.glob("*.py"):
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module not in deleted_analysis, (
                    f"{py_file} imports deleted module: {node.module}"
                )


def test_adapters_do_not_import_providers():
    """No adapter module imports atlas.providers directly."""
    adap_dir = pathlib.Path("atlas/adapters")
    for py_file in adap_dir.glob("*.py"):
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.providers"), (
                    f"{py_file} imports atlas.providers: {node.module}"
                )


def test_adapters_do_not_import_cli():
    """No adapter module imports atlas.cli."""
    adap_dir = pathlib.Path("atlas/adapters")
    for py_file in adap_dir.glob("*.py"):
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.cli"), (
                    f"{py_file} imports atlas.cli (upward coupling): {node.module}"
                )


# ── atlas.analysis.scores active status ──────────────────────────────────────

def test_analysis_scores_clamp_score_active():
    """atlas.analysis.scores.clamp_score remains active (intentionally kept Sprint 140)."""
    from atlas.analysis.scores import clamp_score  # noqa: F401
    assert clamp_score(150) == 100
    assert clamp_score(-5) == 0
    assert clamp_score(72) == 72
