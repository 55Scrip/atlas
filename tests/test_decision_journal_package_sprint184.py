"""Sprint 184 guardrail tests for atlas/decision_journal/ audit.

Verifies:
- All 11 decision_journal exports importable
- decision_journal does not import atlas.providers
- decision_journal does not import atlas.cli
- decision_journal does not import deleted atlas.reasoning
- decision_journal does not import deleted atlas.analysis submodules
- decision_journal does not import atlas.capabilities
- decision_journal does not import atlas.adapters
- CompanyAnalysisProvider remains absent
"""

import ast
import pathlib


# ── All 11 exports importable ─────────────────────────────────────────────────

def test_decision_journal_all_exports_importable():
    """Sprint 184: all 11 atlas.decision_journal exports must be importable."""
    from atlas.decision_journal import (  # noqa: F401
        DecisionJournalEngine,
        DecisionJournalEntry,
        DecisionJournalInput,
        DecisionJournalLesson,
        DecisionJournalReview,
        DecisionJournalStatus,
        DecisionJournalTrigger,
        DecisionType,
        render_decision_journal_entries,
        render_decision_journal_entry,
        render_decision_journal_review,
    )
    assert callable(DecisionJournalEngine)


def test_decision_journal_all_has_eleven_exports():
    """Sprint 184: atlas.decision_journal.__all__ must have exactly 11 exports."""
    import atlas.decision_journal as pkg
    expected = {
        "DecisionJournalEngine",
        "DecisionJournalEntry",
        "DecisionJournalInput",
        "DecisionJournalLesson",
        "DecisionJournalReview",
        "DecisionJournalStatus",
        "DecisionJournalTrigger",
        "DecisionType",
        "render_decision_journal_entries",
        "render_decision_journal_entry",
        "render_decision_journal_review",
    }
    assert set(pkg.__all__) == expected, (
        f"atlas.decision_journal.__all__ mismatch. "
        f"Expected: {sorted(expected)}. Found: {sorted(pkg.__all__)}"
    )


# ── Boundary: no providers, no CLI ───────────────────────────────────────────

def test_decision_journal_does_not_import_providers():
    """Sprint 184: atlas/decision_journal/ must not import atlas.providers."""
    dj_dir = pathlib.Path("atlas/decision_journal")
    for py_file in dj_dir.glob("*.py"):
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.providers"), (
                    f"{py_file} imports atlas.providers — "
                    f"decision_journal must not be provider-coupled: {node.module}"
                )


def test_decision_journal_does_not_import_cli():
    """Sprint 184: atlas/decision_journal/ must not import atlas.cli."""
    dj_dir = pathlib.Path("atlas/decision_journal")
    for py_file in dj_dir.glob("*.py"):
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


# ── Boundary: no stale closed-track imports ──────────────────────────────────

def test_decision_journal_does_not_import_deleted_reasoning():
    """Sprint 184: atlas/decision_journal/ must not import deleted atlas.reasoning."""
    dj_dir = pathlib.Path("atlas/decision_journal")
    for py_file in dj_dir.glob("*.py"):
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


def test_decision_journal_does_not_import_deleted_analysis_submodules():
    """Sprint 184: atlas/decision_journal/ must not import deleted atlas.analysis submodules."""
    deleted_prefixes = (
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
    )
    dj_dir = pathlib.Path("atlas/decision_journal")
    for py_file in dj_dir.glob("*.py"):
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in deleted_prefixes:
                    assert not node.module.startswith(prefix), (
                        f"{py_file} imports deleted module {prefix}: {node.module}"
                    )


def test_decision_journal_does_not_import_capabilities():
    """Sprint 184: atlas/decision_journal/ must not import atlas.capabilities."""
    dj_dir = pathlib.Path("atlas/decision_journal")
    for py_file in dj_dir.glob("*.py"):
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


def test_decision_journal_does_not_import_adapters():
    """Sprint 184: atlas/decision_journal/ must not import atlas.adapters."""
    dj_dir = pathlib.Path("atlas/decision_journal")
    for py_file in dj_dir.glob("*.py"):
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.adapters"), (
                    f"{py_file} imports atlas.adapters (upward coupling): {node.module}"
                )


# ── CompanyAnalysisProvider remains absent ───────────────────────────────────

def test_company_analysis_provider_alias_remains_absent_sprint184():
    """Sprint 184: CompanyAnalysisProvider must not appear in any active atlas/ module.

    The alias was removed in Sprint 180. This confirms it has not been re-introduced.
    """
    import pytest
    with pytest.raises((ImportError, AttributeError)):
        from atlas.analysis.company_analysis import CompanyAnalysisProvider  # noqa: F401

    import atlas.analysis.company_analysis as mod
    assert not hasattr(mod, "CompanyAnalysisProvider"), (
        "CompanyAnalysisProvider must not exist in atlas.analysis.company_analysis — removed Sprint 180"
    )
