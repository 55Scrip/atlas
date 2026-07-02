"""Sprint 163: Release candidate checkpoint guardrails after 10 cleanup tracks closed.

Verifies:
- All deleted modules/packages remain absent (not importable)
- All retired symbols remain absent from active packages
- All five recently-closed-track packages remain importable
- Retired CLI commands remain in _RETIRED_REGISTRY and not in _REGISTRY
- Provider-coupled packages do not import YahooFinanceProvider directly
- atlas/domains/decision/ ReasoningEngine is distinct from the deleted atlas.reasoning
"""

import importlib

import pytest


# ── Deleted module guard ──────────────────────────────────────────────────────

DELETED_MODULES = [
    "atlas.reasoning",
    "atlas.analysis.portfolio",
    "atlas.analysis.growth",
    "atlas.analysis.macro",
    "atlas.analysis.moat",
    "atlas.analysis.quality",
    "atlas.analysis.sentiment",
    "atlas.analysis.technicals",
    "atlas.analysis.valuation",
]


@pytest.mark.parametrize("module", DELETED_MODULES)
def test_sprint163_deleted_module_remains_absent(module: str) -> None:
    """Sprint 163: deleted modules must not be importable."""
    try:
        importlib.import_module(module)
        pytest.fail(f"{module} must not be importable — deleted in cleanup tracks")
    except ModuleNotFoundError:
        pass


# ── Retired symbol guard ──────────────────────────────────────────────────────

def test_sprint163_retired_principles_symbols_absent() -> None:
    """Sprint 163: removed principles checks must remain absent."""
    import atlas.principles as pkg

    for removed in ("check_reasoning_report", "check_intelligence_report", "check_suitability_assessment"):
        assert not hasattr(pkg, removed), (
            f"{removed} must not be in atlas.principles after Sprint 152/157 removal"
        )


# ── Active package smoke imports ──────────────────────────────────────────────

ACTIVE_PACKAGES = [
    "atlas.evidence",
    "atlas.risk",
    "atlas.principles",
    "atlas.comparison",
    "atlas.home",
]


@pytest.mark.parametrize("package", ACTIVE_PACKAGES)
def test_sprint163_active_package_importable(package: str) -> None:
    """Sprint 163: recently-closed-track packages must remain importable."""
    mod = importlib.import_module(package)
    assert hasattr(mod, "__all__"), f"{package} must have __all__"
    assert len(mod.__all__) > 0, f"{package}.__all__ must not be empty"


# ── CLI retired/active registry ───────────────────────────────────────────────

def test_sprint163_deprecated_registry_is_empty() -> None:
    """Sprint 163: active deprecated registry must be empty — all deprecated commands retired Sprint 91."""
    from atlas.cli.deprecations import all_deprecated_commands

    assert all_deprecated_commands() == (), (
        "atlas/cli/deprecations._REGISTRY must be empty — all deprecated commands were retired"
    )


def test_sprint163_retired_commands_present() -> None:
    """Sprint 163: retired command registry must contain the expected retired commands."""
    from atlas.cli.deprecations import all_retired_commands

    retired = set(all_retired_commands())
    expected_retired = {
        "atlas reason analyze",
        "atlas risk size",
        "atlas evidence assess",
        "atlas daily brief",
        "atlas portfolio analyze",
        "atlas portfolio review",
        "atlas watchlist analyze",
    }
    missing = expected_retired - retired
    assert not missing, f"Expected retired commands missing from _RETIRED_REGISTRY: {missing}"


# ── Provider boundary ─────────────────────────────────────────────────────────

from pathlib import Path


def test_sprint163_comparison_does_not_import_yahoo() -> None:
    """Sprint 163: atlas/comparison/ must not import YahooFinanceProvider directly."""
    for py_file in Path("atlas/comparison").glob("*.py"):
        assert "YahooFinanceProvider" not in py_file.read_text(encoding="utf-8"), (
            f"{py_file}: YahooFinanceProvider must remain CLI-opt-in only"
        )


def test_sprint163_home_does_not_import_yahoo() -> None:
    """Sprint 163: atlas/home/ must not import YahooFinanceProvider directly."""
    for py_file in Path("atlas/home").glob("*.py"):
        assert "YahooFinanceProvider" not in py_file.read_text(encoding="utf-8"), (
            f"{py_file}: YahooFinanceProvider must remain CLI-opt-in only"
        )


# ── Blueprint-layer ReasoningEngine is distinct ───────────────────────────────

def test_sprint163_domains_decision_reasoning_engine_is_blueprint_class() -> None:
    """Sprint 163: atlas.domains.decision.ReasoningEngine is a Blueprint-layer class distinct
    from the deleted atlas.reasoning package. Both must not be confused."""
    from atlas.domains.decision import ReasoningEngine

    assert callable(ReasoningEngine), "atlas.domains.decision.ReasoningEngine must be callable"
    # Confirm the deleted package is still absent
    try:
        importlib.import_module("atlas.reasoning")
        pytest.fail("atlas.reasoning must not be importable — deleted Sprint 153")
    except ModuleNotFoundError:
        pass
