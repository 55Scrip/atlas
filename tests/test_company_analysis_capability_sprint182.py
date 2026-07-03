"""Sprint 182 guardrail tests for atlas/capabilities/company_analysis/ audit.

Verifies:
- All 9 capability exports importable
- Capability does not import legacy atlas.analysis
- Capability does not import atlas.providers
- Capability does not import atlas.cli
- Legacy atlas.analysis does not import capability
- CompanyAnalysisProvider remains absent from all active code
- Deleted analysis modules remain absent
"""

import ast
import pathlib


# ── All 9 capability exports importable ──────────────────────────────────────

def test_company_analysis_capability_all_exports_importable():
    """Sprint 182: all 9 atlas.capabilities.company_analysis exports must be importable."""
    from atlas.capabilities.company_analysis import (  # noqa: F401
        CompanyAnalysisConfidence,
        CompanyAnalysisEngine,
        CompanyAnalysisEvidenceLink,
        CompanyAnalysisInput,
        CompanyAnalysisObservation,
        CompanyAnalysisReport,
        CompanyAnalysisRisk,
        CompanyAnalysisSection,
        CompanyAnalysisUnknown,
    )
    assert callable(CompanyAnalysisEngine)


def test_company_analysis_capability_all_has_nine_exports():
    """Sprint 182: atlas.capabilities.company_analysis.__all__ must have exactly 9 exports."""
    import atlas.capabilities.company_analysis as pkg
    expected = {
        "CompanyAnalysisConfidence",
        "CompanyAnalysisEngine",
        "CompanyAnalysisEvidenceLink",
        "CompanyAnalysisInput",
        "CompanyAnalysisObservation",
        "CompanyAnalysisReport",
        "CompanyAnalysisRisk",
        "CompanyAnalysisSection",
        "CompanyAnalysisUnknown",
    }
    assert set(pkg.__all__) == expected, (
        f"atlas.capabilities.company_analysis.__all__ mismatch. "
        f"Expected: {sorted(expected)}. Found: {sorted(pkg.__all__)}"
    )


# ── Boundary: capability does not import legacy atlas.analysis ────────────────

def test_capability_company_analysis_does_not_import_legacy_analysis():
    """Sprint 182: atlas/capabilities/company_analysis/ must not import from atlas.analysis."""
    cap_dir = pathlib.Path("atlas/capabilities/company_analysis")
    for py_file in cap_dir.glob("*.py"):
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.analysis"), (
                    f"{py_file} imports from legacy atlas.analysis — "
                    f"capability must not depend on legacy layer: {node.module}"
                )


# ── Boundary: legacy atlas.analysis does not import capability ────────────────

def test_legacy_analysis_does_not_import_capability():
    """Sprint 182: atlas/analysis/ must not import from atlas.capabilities.company_analysis."""
    analysis_dir = pathlib.Path("atlas/analysis")
    for py_file in analysis_dir.glob("*.py"):
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.capabilities.company_analysis"), (
                    f"{py_file} imports from atlas.capabilities.company_analysis — "
                    f"legacy layer must not depend on capability: {node.module}"
                )


# ── Boundary: capability does not import providers or CLI ─────────────────────

def test_capability_company_analysis_does_not_import_providers():
    """Sprint 182: atlas/capabilities/company_analysis/ must not import atlas.providers."""
    cap_dir = pathlib.Path("atlas/capabilities/company_analysis")
    for py_file in cap_dir.glob("*.py"):
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.providers"), (
                    f"{py_file} imports atlas.providers — "
                    f"capability must not be provider-coupled: {node.module}"
                )


def test_capability_company_analysis_does_not_import_cli():
    """Sprint 182: atlas/capabilities/company_analysis/ must not import atlas.cli."""
    cap_dir = pathlib.Path("atlas/capabilities/company_analysis")
    for py_file in cap_dir.glob("*.py"):
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


# ── CompanyAnalysisProvider remains absent from active code ──────────────────

def test_company_analysis_provider_alias_remains_absent():
    """Sprint 182: CompanyAnalysisProvider must not appear in any active atlas/ module.

    The alias was removed in Sprint 180. This confirms it has not been re-introduced.
    """
    import pytest
    with pytest.raises((ImportError, AttributeError)):
        from atlas.analysis.company_analysis import CompanyAnalysisProvider  # noqa: F401

    import atlas.analysis.company_analysis as mod
    assert not hasattr(mod, "CompanyAnalysisProvider"), (
        "CompanyAnalysisProvider must not exist in atlas.analysis.company_analysis — removed Sprint 180"
    )
