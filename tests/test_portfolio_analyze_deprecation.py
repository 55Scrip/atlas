"""Sprint 89: Tests confirming atlas portfolio analyze has been retired.

Sprint 79 deprecated the command; Sprint 89 removed the command body.
`atlas portfolio analyze` is no longer a registered CLI command.

Sprint 128: PortfolioIntelligenceEngine deleted — zero production callers as of Sprint 127.
Shared types (Portfolio, PortfolioAnalysis, PortfolioPosition, etc.) remain on disk.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from typer.testing import CliRunner

from atlas.cli.deprecations import all_deprecated_commands, all_retired_commands
from atlas.cli.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = REPO_ROOT / "atlas" / "cli" / "main.py"

runner = CliRunner()

PORTFOLIO_ENGINE_CALLERS = (
    # atlas/intelligence/engine.py migrated in Sprint 125 — removed from this list
    # atlas/conversation/engine.py migrated in Sprint 126 — removed from this list
    # atlas/decision/decision_engine.py migrated in Sprint 124 — removed from this list
    # atlas/dashboard/engine.py migrated in Sprint 127 — removed from this list
    # atlas/reasoning/engine.py migrated in Sprint 131 — removed from this list
)


def _fake_portfolio_path(tmp_path: Path) -> Path:
    p = tmp_path / "portfolio.json"
    p.write_text(
        json.dumps({
            "positions": [{
                "ticker": "NVDA",
                "company": "NVIDIA",
                "sector": "Semiconductors",
                "country": "United States",
                "market_cap": 3_000_000_000_000,
                "weight": 0.5,
                "quality_score": 90,
                "risk_score": 70,
            }]
        }),
        encoding="utf-8",
    )
    return p


def test_portfolio_analyze_command_is_no_longer_registered(tmp_path) -> None:
    """atlas portfolio analyze must not be a recognized subcommand of atlas portfolio."""
    result = runner.invoke(app, ["portfolio", "analyze", str(_fake_portfolio_path(tmp_path)), "NVDA"])
    assert result.exit_code != 0


def test_portfolio_analyze_command_is_not_in_active_registry() -> None:
    assert "atlas portfolio analyze" not in all_deprecated_commands()


def test_portfolio_analyze_command_is_in_retired_registry() -> None:
    assert "atlas portfolio analyze" in all_retired_commands()


def test_portfolio_analyze_command_function_removed_from_cli() -> None:
    """The portfolio_analyze_command function must not exist in the CLI source."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    func_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert "portfolio_analyze_command" not in func_names, (
        "portfolio_analyze_command function should have been removed in Sprint 89"
    )


def test_portfolio_summary_command_is_unaffected(tmp_path) -> None:
    """atlas portfolio summary must remain functional and not deprecated."""
    p = _fake_portfolio_path(tmp_path)
    result = runner.invoke(app, ["portfolio", "summary", str(p)])
    assert result.exit_code == 0
    assert "deprecated" not in result.output.lower()


def test_portfolio_review_command_is_retired(tmp_path) -> None:
    """Sprint 90: atlas portfolio review command body retired — no longer a valid command."""
    result = runner.invoke(app, ["portfolio", "review", str(tmp_path / "p.json")])
    assert result.exit_code != 0


def test_sprint135_portfolio_boundary_types_importable_from_adapter() -> None:
    """Sprint 135: Portfolio and PortfolioPosition now live in atlas.adapters.portfolio."""
    from atlas.adapters.portfolio import Portfolio, PortfolioPosition  # noqa: F401
    assert Portfolio is not None
    assert PortfolioPosition is not None


def test_portfolio_engine_active_callers_remain() -> None:
    """Sprint 136: PORTFOLIO_ENGINE_CALLERS is empty — all callers migrated by Sprint 135."""
    assert len(PORTFOLIO_ENGINE_CALLERS) == 0, (
        "All atlas.analysis.portfolio callers were migrated by Sprint 135; "
        "this list must remain empty"
    )


def test_sprint135_analysis_portfolio_module_deleted() -> None:
    """Sprint 135: atlas.analysis.portfolio deleted — must NOT be importable."""
    import importlib
    import pytest
    with pytest.raises((ImportError, ModuleNotFoundError)):
        importlib.import_module("atlas.analysis.portfolio")


# ── Confirm remaining deprecated commands still work ─────────────────────────

def test_daily_brief_is_retired() -> None:
    result = runner.invoke(app, ["daily", "brief"])
    assert result.exit_code != 0


def test_evidence_assess_is_retired() -> None:
    result = runner.invoke(app, ["evidence", "assess"])
    assert result.exit_code != 0


def test_reason_analyze_is_retired() -> None:
    result = runner.invoke(app, ["reason", "analyze"])
    assert result.exit_code != 0


def test_risk_size_is_retired(tmp_path) -> None:
    p = tmp_path / "r.json"
    p.write_text(json.dumps({"ticker": "NVDA"}), encoding="utf-8")
    result = runner.invoke(app, ["risk", "size", str(p)])
    assert result.exit_code != 0


def test_watchlist_analyze_is_retired(tmp_path) -> None:
    p = tmp_path / "w.json"
    p.write_text(json.dumps({"name": "Test", "tickers": ["NVDA"]}), encoding="utf-8")
    result = runner.invoke(app, ["watchlist", "analyze", str(p)])
    assert result.exit_code != 0


def test_portfolio_review_is_retired(tmp_path) -> None:
    # Sprint 90: atlas portfolio review command body retired — no longer a valid command
    p = _fake_portfolio_path(tmp_path)
    result = runner.invoke(app, ["portfolio", "review", str(p)])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Sprint 128: PortfolioIntelligenceEngine deletion guardrails
# ---------------------------------------------------------------------------

def test_sprint128_portfolio_intelligence_engine_not_importable_from_module() -> None:
    """Sprint 128: PortfolioIntelligenceEngine deleted — must NOT be importable from atlas.analysis.portfolio."""
    import pytest
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import PortfolioIntelligenceEngine  # noqa: F401


def test_sprint128_portfolio_intelligence_engine_not_in_atlas_analysis() -> None:
    """Sprint 128: PortfolioIntelligenceEngine removed from atlas.analysis __all__ and namespace."""
    import importlib
    mod = importlib.import_module("atlas.analysis")
    assert not hasattr(mod, "PortfolioIntelligenceEngine"), (
        "PortfolioIntelligenceEngine was deleted in Sprint 128 — must not appear in atlas.analysis"
    )


def test_sprint128_shared_types_still_importable() -> None:
    """Sprint 128/132/135: active boundary types remain importable — now from atlas.adapters.portfolio."""
    from atlas.adapters.portfolio import (  # noqa: F401
        Portfolio,
        PortfolioPosition,
    )
    assert True


# ---------------------------------------------------------------------------
# Sprint 129: Remaining symbol audit guardrails
# ---------------------------------------------------------------------------

def test_sprint129_deleted_modules_remain_gone() -> None:
    """Sprint 129: modules deleted in prior sprints must remain deleted."""
    import importlib
    import pytest
    for mod_name in (
        "atlas.analysis.watchlist",
        "atlas.analysis.comparison",
        "atlas.analysis.memory",
        "atlas.analysis.scoring",
    ):
        with pytest.raises((ImportError, ModuleNotFoundError)):
            importlib.import_module(mod_name)


def test_sprint129_portfolio_intelligence_capability_importable() -> None:
    """Sprint 129: PortfolioIntelligenceCapability must remain importable from atlas.capabilities."""
    from atlas.capabilities.portfolio_intelligence import (  # noqa: F401
        PortfolioIntelligenceCapability,
        PortfolioFitResult,
        PortfolioFitInput,
    )
    assert True


def test_sprint129_capability_engine_free_of_legacy_portfolio_import() -> None:
    """Sprint 129: capability engine must not import from atlas.analysis.portfolio at any level."""
    import pathlib
    source = pathlib.Path("atlas/capabilities/portfolio_intelligence/engine.py").read_text()
    assert "atlas.analysis.portfolio" not in source


def test_sprint129_portfolio_module_remaining_public_symbols() -> None:
    """Sprint 135: Portfolio, PortfolioPosition moved to atlas.adapters.portfolio."""
    from atlas.adapters.portfolio import (  # noqa: F401
        Portfolio,
        PortfolioPosition,
    )
    assert True


def test_sprint130_dead_private_helpers_deleted() -> None:
    """Sprint 130/135: 16 dead private helpers deleted — must not exist in atlas.adapters.portfolio."""
    import atlas.adapters.portfolio as mod
    deleted_helpers = [
        "_diversification_impact",
        "_sector_concentration",
        "_country_concentration",
        "_market_cap_concentration",
        "_overlap_with_existing_holdings",
        "_expected_quality_impact",
        "_expected_risk_impact",
        "_aggregate_portfolio_score",
        "_recommend",
        "_final_reasoning",
        "_weight_by_attribute",
        "_mega_cap_weight",
        "_weighted_average",
        "_pro_forma_average",
        "_concentration_score",
        "_is_mega_cap",
    ]
    for name in deleted_helpers:
        assert not hasattr(mod, name), (
            f"{name} was deleted in Sprint 130 — must not be present in atlas.adapters.portfolio"
        )


def test_sprint130_get_mock_company_portfolio_profile_deleted() -> None:
    """Sprint 130: get_mock_company_portfolio_profile deleted — must NOT be importable."""
    import pytest
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import get_mock_company_portfolio_profile  # noqa: F401


def test_sprint130_active_portfolio_helpers_still_present() -> None:
    """Sprint 130/135: active private helpers remain in atlas.adapters.portfolio."""
    import atlas.adapters.portfolio as mod
    assert hasattr(mod, "_position_from_mapping")
    assert hasattr(mod, "_normalize_weight")


# ---------------------------------------------------------------------------
# Sprint 132: PortfolioAnalysis, PortfolioSignal, PortfolioRecommendation deleted
# ---------------------------------------------------------------------------

def test_sprint132_portfolio_analysis_not_importable() -> None:
    """Sprint 132: PortfolioAnalysis deleted — must NOT be importable from atlas.analysis.portfolio."""
    import pytest
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import PortfolioAnalysis  # noqa: F401


def test_sprint132_portfolio_signal_not_importable() -> None:
    """Sprint 132: PortfolioSignal deleted — must NOT be importable from atlas.analysis.portfolio."""
    import pytest
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import PortfolioSignal  # noqa: F401


def test_sprint132_portfolio_recommendation_not_importable() -> None:
    """Sprint 132: PortfolioRecommendation deleted — must NOT be importable from atlas.analysis.portfolio."""
    import pytest
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import PortfolioRecommendation  # noqa: F401


def test_sprint132_deleted_types_not_in_atlas_analysis_namespace() -> None:
    """Sprint 132: deleted types must not appear in atlas.analysis namespace."""
    import importlib
    mod = importlib.import_module("atlas.analysis")
    assert not hasattr(mod, "PortfolioAnalysis"), "PortfolioAnalysis was deleted Sprint 132"
    assert not hasattr(mod, "PortfolioSignal"), "PortfolioSignal was deleted Sprint 132"
    assert not hasattr(mod, "PortfolioRecommendation"), "PortfolioRecommendation was deleted Sprint 132"


def test_sprint132_active_boundary_types_remain() -> None:
    """Sprint 135: Portfolio, PortfolioPosition importable from atlas.adapters.portfolio."""
    from atlas.adapters.portfolio import (  # noqa: F401
        Portfolio,
        PortfolioPosition,
    )
    assert True


def test_sprint132_no_production_code_imports_portfolio_analysis() -> None:
    """Sprint 132: no production source file imports PortfolioAnalysis from atlas.analysis.portfolio."""
    import ast
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    for py_file in (repo_root / "atlas").rglob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        if "PortfolioAnalysis" not in source:
            continue
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                names = [alias.name for alias in node.names]
                if "PortfolioAnalysis" in names:
                    assert False, (
                        f"{py_file}: runtime import of PortfolioAnalysis found — "
                        "should have been deleted in Sprint 132"
                    )


def test_sprint132_portfolio_intelligence_capability_still_importable() -> None:
    """Sprint 132: capability layer must remain importable and intact."""
    from atlas.capabilities.portfolio_intelligence import (  # noqa: F401
        PortfolioIntelligenceCapability,
        PortfolioFitResult,
        PortfolioFitDimension,
        PortfolioFitInput,
    )
    assert True


# ---------------------------------------------------------------------------
# Sprint 133: CompanyPortfolioProfile deleted; providers return PortfolioFitInput
# ---------------------------------------------------------------------------

def test_sprint133_company_portfolio_profile_not_importable() -> None:
    """Sprint 133: CompanyPortfolioProfile deleted — must NOT be importable."""
    import pytest
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import CompanyPortfolioProfile  # noqa: F401


def test_sprint133_portfolio_fit_input_from_profile_is_identity() -> None:
    """Sprint 133: portfolio_fit_input_from_profile must accept and return PortfolioFitInput unchanged."""
    from atlas.adapters.portfolio import portfolio_fit_input_from_profile
    from atlas.capabilities.portfolio_intelligence import PortfolioFitInput
    fit_input = PortfolioFitInput(
        ticker="TSM",
        company="TSMC",
        sector="Semiconductors",
        country="Taiwan",
        market_cap=600_000_000_000.0,
        quality_score=88,
        risk_score=55,
    )
    result = portfolio_fit_input_from_profile(fit_input)
    assert result is fit_input


def test_sprint133_providers_return_portfolio_fit_input() -> None:
    """Sprint 133: MockCompanyAnalysisProvider.get_portfolio_profile must return PortfolioFitInput."""
    from atlas.providers.mock import MockCompanyAnalysisProvider
    from atlas.capabilities.portfolio_intelligence import PortfolioFitInput
    provider = MockCompanyAnalysisProvider()
    profile = provider.get_portfolio_profile("NVDA")
    assert isinstance(profile, PortfolioFitInput)


def test_sprint133_portfolio_module_remaining_symbols() -> None:
    """Sprint 135: Portfolio and PortfolioPosition live in atlas.adapters.portfolio."""
    import atlas.adapters.portfolio as mod
    assert hasattr(mod, "Portfolio")
    assert hasattr(mod, "PortfolioPosition")
    assert not hasattr(mod, "CompanyPortfolioProfile"), (
        "CompanyPortfolioProfile deleted in Sprint 133"
    )


# ---------------------------------------------------------------------------
# Sprint 134: Caller audit guardrails — lock remaining import sites
# ---------------------------------------------------------------------------

def test_sprint134_portfolio_boundary_types_still_importable() -> None:
    """Sprint 135: Portfolio and PortfolioPosition importable from atlas.adapters.portfolio."""
    from atlas.adapters.portfolio import Portfolio, PortfolioPosition  # noqa: F401
    assert Portfolio is not None
    assert PortfolioPosition is not None


def test_sprint134_deleted_types_not_importable_individually() -> None:
    """Sprint 134: individual ImportError checks for each deleted legacy type."""
    import pytest
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import PortfolioIntelligenceEngine  # noqa: F401
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import PortfolioAnalysis  # noqa: F401
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import PortfolioSignal  # noqa: F401
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import PortfolioRecommendation  # noqa: F401
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import CompanyPortfolioProfile  # noqa: F401


def test_sprint134_portfolio_module_private_helpers_present() -> None:
    """Sprint 135: active private helpers live in atlas.adapters.portfolio."""
    import atlas.adapters.portfolio as mod
    assert hasattr(mod, "_position_from_mapping"), (
        "_position_from_mapping must be present in atlas.adapters.portfolio"
    )
    assert hasattr(mod, "_normalize_weight"), (
        "_normalize_weight must be present in atlas.adapters.portfolio"
    )


def test_sprint134_adapter_still_provides_legacy_conversion() -> None:
    """Sprint 134: adapter must still provide legacy_portfolio_to_domain_portfolio."""
    from atlas.adapters.portfolio import legacy_portfolio_to_domain_portfolio  # noqa: F401
    assert legacy_portfolio_to_domain_portfolio is not None


def test_sprint134_cli_still_imports_portfolio_from_analysis() -> None:
    """Sprint 135: CLI now imports Portfolio from atlas.adapters.portfolio."""
    import pathlib
    source = pathlib.Path("atlas/cli/main.py").read_text(encoding="utf-8")
    assert "atlas.adapters.portfolio" in source, (
        "CLI must import Portfolio from atlas.adapters.portfolio after Sprint 135"
    )
    assert "atlas.analysis.portfolio" not in source, (
        "CLI must not import from atlas.analysis.portfolio after Sprint 135"
    )


def test_sprint134_portfolio_fit_input_from_profile_is_identity() -> None:
    """Sprint 134: portfolio_fit_input_from_profile is now identity — PortfolioFitInput in, PortfolioFitInput out."""
    from atlas.adapters.portfolio import portfolio_fit_input_from_profile
    from atlas.capabilities.portfolio_intelligence import PortfolioFitInput
    fit = PortfolioFitInput(
        ticker="TSM", company="TSMC", sector="Semiconductors",
        country="Taiwan", market_cap=600_000_000_000.0,
        quality_score=88, risk_score=55,
    )
    assert portfolio_fit_input_from_profile(fit) is fit


# ---------------------------------------------------------------------------
# Sprint 135: atlas.analysis.portfolio deleted; boundary types in atlas.adapters.portfolio
# ---------------------------------------------------------------------------

def test_sprint135_analysis_portfolio_module_deleted() -> None:
    """Sprint 135: atlas.analysis.portfolio must not exist — module was deleted."""
    import importlib
    import pytest
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("atlas.analysis.portfolio")


def test_sprint135_portfolio_importable_from_adapter() -> None:
    """Sprint 135: Portfolio and PortfolioPosition must be importable from atlas.adapters.portfolio."""
    from atlas.adapters.portfolio import Portfolio, PortfolioPosition  # noqa: F401
    assert Portfolio is not None
    assert PortfolioPosition is not None


def test_sprint135_portfolio_json_behavior_preserved() -> None:
    """Sprint 135: Portfolio.from_mapping still works identically after the move."""
    from atlas.adapters.portfolio import Portfolio
    portfolio = Portfolio.from_mapping({
        "positions": [{
            "ticker": "nvda",
            "company": "NVIDIA",
            "sector": "Semiconductors",
            "country": "United States",
            "market_cap": 3_300_000_000_000,
            "weight": 60,
            "quality_score": 92,
            "risk_score": 77,
        }]
    })
    assert len(portfolio.positions) == 1
    pos = portfolio.positions[0]
    assert pos.ticker == "NVDA"
    assert pos.weight == 0.60
    assert pos.quality_score == 92


def test_sprint135_no_production_code_imports_analysis_portfolio() -> None:
    """Sprint 135: zero production files may import from atlas.analysis.portfolio."""
    import ast
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    for py_file in (repo_root / "atlas").rglob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        if "atlas.analysis.portfolio" not in source:
            continue
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "atlas.analysis.portfolio":
                assert False, (
                    f"{py_file}: import from atlas.analysis.portfolio found — "
                    "module was deleted in Sprint 135"
                )


# ---------------------------------------------------------------------------
# Sprint 136: Post-portfolio migration architecture checkpoint
# ---------------------------------------------------------------------------

def test_sprint136_portfolio_not_in_atlas_analysis_namespace() -> None:
    """Sprint 136: atlas.analysis must not export Portfolio or PortfolioPosition."""
    import importlib
    mod = importlib.import_module("atlas.analysis")
    assert not hasattr(mod, "Portfolio"), (
        "Portfolio must not be exported from atlas.analysis after Sprint 135"
    )
    assert not hasattr(mod, "PortfolioPosition"), (
        "PortfolioPosition must not be exported from atlas.analysis after Sprint 135"
    )


def test_sprint136_adapter_boundary_is_self_contained() -> None:
    """Sprint 136: atlas.adapters.portfolio must not import from atlas.analysis.portfolio."""
    import pathlib
    source = pathlib.Path("atlas/adapters/portfolio.py").read_text(encoding="utf-8")
    import ast
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "atlas.analysis.portfolio":
            assert False, "atlas/adapters/portfolio.py must not import atlas.analysis.portfolio"


def test_sprint136_all_deleted_portfolio_symbols_unreachable() -> None:
    """Sprint 136: symbols deleted across portfolio migration sprints must not exist in adapter."""
    import atlas.adapters.portfolio as adapter_mod
    deleted = [
        "PortfolioIntelligenceEngine",
        "PortfolioAnalysis",
        "PortfolioSignal",
        "PortfolioRecommendation",
        "CompanyPortfolioProfile",
    ]
    for symbol in deleted:
        assert not hasattr(adapter_mod, symbol), (
            f"{symbol} must not exist in atlas.adapters.portfolio — deleted in prior sprints"
        )


def test_sprint136_analysis_package_has_no_portfolio_module() -> None:
    """Sprint 136: atlas/analysis/portfolio.py must not exist on disk."""
    import pathlib
    assert not pathlib.Path("atlas/analysis/portfolio.py").exists(), (
        "atlas/analysis/portfolio.py must remain deleted after Sprint 135"
    )
