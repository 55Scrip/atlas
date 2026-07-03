"""Sprint 177 guardrail tests for atlas/domains/ package inventory.

Verifies:
- All domain subpackages importable
- Domains do not import deleted atlas.reasoning
- Domains do not import deleted atlas.analysis.* modules
- Domains do not import atlas.capabilities (no upward coupling)
- Domains do not import atlas.cli or atlas.providers
- atlas.domains.decision.ReasoningEngine is the active Blueprint-layer class
  (distinct from deleted atlas.reasoning.ReasoningEngine)
- Domain boundaries correct from domain side
"""

import ast
import pathlib


# ── Subpackage importability ──────────────────────────────────────────────────

def test_domains_package_importable():
    import atlas.domains  # noqa: F401


def test_domains_decision_importable():
    from atlas.domains.decision import (  # noqa: F401
        Confidence,
        Decision,
        DecisionCard,
        DecisionContext,
        DecisionEngine,
        DecisionResult,
        Evidence,
        EvidenceCategory,
        EvidenceEngine,
        EvidenceStrength,
        Observation,
        ReasoningEngine,
        ReasoningStep,
        Unknown,
    )


def test_domains_knowledge_importable():
    from atlas.domains.knowledge import (  # noqa: F401
        KnowledgeCollection,
        KnowledgeEdge,
        KnowledgeFact,
        KnowledgeNode,
        KnowledgeNodeType,
        KnowledgeQueryService,
        KnowledgeReference,
        KnowledgeRelationship,
        KnowledgeRelationshipEngine,
        KnowledgeSource,
    )


def test_domains_portfolio_importable():
    from atlas.domains.portfolio import (  # noqa: F401
        Allocation,
        Concentration,
        ConcentrationLevel,
        Holding,
        Portfolio,
        PortfolioDomainReview,
        PortfolioIssueSeverity,
        PortfolioObservation,
        PortfolioReviewEngine,
        PortfolioSnapshot,
        PortfolioSummary,
        PortfolioValidationIssue,
        PortfolioValidationResult,
        cash_weight,
        concentration_level,
        country_allocation,
        holding_market_value,
        holding_weight,
        largest_position,
        portfolio_summary,
        sector_allocation,
        top_holdings,
        total_portfolio_value,
        validate_portfolio,
    )


def test_domains_research_importable():
    from atlas.domains.research import (  # noqa: F401
        ResearchAssumption,
        ResearchEvidenceReference,
        ResearchIssueSeverity,
        ResearchNote,
        ResearchProject,
        ResearchQuestion,
        ResearchQuestionStatus,
        ResearchStatus,
        ResearchSummary,
        ResearchValidationIssue,
        ResearchValidationResult,
        ThesisFragment,
        is_valid_status_transition,
        summarize_research,
        validate_research_project,
    )


def test_domains_authentication_importable():
    from atlas.domains.authentication import User  # noqa: F401


def test_domains_decision_journal_importable():
    from atlas.domains.decision_journal import JournalEntry  # noqa: F401


def test_domains_watchlist_importable():
    from atlas.domains.watchlist import Watchlist  # noqa: F401


def test_domains_daily_brief_importable():
    import atlas.domains.daily_brief  # noqa: F401


def test_domains_ai_importable():
    from atlas.domains.ai import (  # noqa: F401
        DecisionEngine,
        DiscoveryService,
        KnowledgeService,
        ReasoningService,
        SummaryService,
    )


# ── ReasoningEngine identity guardrail ────────────────────────────────────────

def test_domains_decision_reasoning_engine_is_active_blueprint_class():
    """atlas.domains.decision.ReasoningEngine is the active Blueprint-layer class.

    It is distinct from deleted atlas.reasoning.ReasoningEngine.
    It must be callable and have a .reason() method.
    """
    from atlas.domains.decision import ReasoningEngine
    assert callable(ReasoningEngine), "ReasoningEngine must be callable"
    assert callable(getattr(ReasoningEngine, "reason", None)), (
        "ReasoningEngine must have a callable .reason() method"
    )


def test_deleted_atlas_reasoning_remains_deleted():
    """atlas.reasoning package remains deleted (distinct from atlas.domains.decision)."""
    import importlib
    import pytest
    with pytest.raises((ImportError, ModuleNotFoundError)):
        importlib.import_module("atlas.reasoning")


# ── Boundary: domains must not import upward ──────────────────────────────────

def test_domains_do_not_import_capabilities():
    """No domain module imports atlas.capabilities (no upward coupling)."""
    dom_dir = pathlib.Path("atlas/domains")
    for py_file in dom_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.capabilities"), (
                    f"{py_file} imports atlas.capabilities (upward coupling): {node.module}"
                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("atlas.capabilities"), (
                        f"{py_file} imports atlas.capabilities (upward coupling): {alias.name}"
                    )


def test_domains_do_not_import_cli():
    """No domain module imports atlas.cli."""
    dom_dir = pathlib.Path("atlas/domains")
    for py_file in dom_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
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


def test_domains_do_not_import_providers():
    """No domain module imports atlas.providers."""
    dom_dir = pathlib.Path("atlas/domains")
    for py_file in dom_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
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


def test_domains_do_not_import_deleted_reasoning():
    """No domain module imports deleted atlas.reasoning."""
    dom_dir = pathlib.Path("atlas/domains")
    for py_file in dom_dir.rglob("*.py"):
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


def test_domains_do_not_import_deleted_analysis_modules():
    """No domain module imports deleted atlas.analysis.* submodules."""
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
    dom_dir = pathlib.Path("atlas/domains")
    for py_file in dom_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
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


# ── Top-level __all__ ─────────────────────────────────────────────────────────

def test_domains_top_level_all():
    """atlas/domains/__init__.py.__all__ lists expected domain namespaces."""
    import atlas.domains as pkg
    assert hasattr(pkg, "__all__")
    expected = {
        "ai", "authentication", "decision", "daily_brief",
        "decision_journal", "knowledge", "portfolio", "research", "watchlist",
    }
    actual = set(pkg.__all__)
    assert actual == expected, (
        f"atlas.domains.__all__ mismatch. Expected {expected}, got {actual}"
    )
