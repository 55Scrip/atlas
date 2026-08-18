"""Sprint N Phase 16/20 -- Shadow Integration Safety.

Same AST-based repository scan Sprint M's own `test_integration_safety.py`
established, applied to this new package: nothing outside
`atlas/alpha/canonical_security_resolution/`, this test directory, and
(Sprint O) `canonical_security_gate` and its own test directory may
import it. The Sprint O exclusion is deliberate, not a weakening --
that package is explicitly the one sanctioned integration point wiring
this shadow-mode service into the live enrichment pipeline; this guard
still forbids anything else (Watchlist, Portfolio, business_data_refresh
directly) from importing this package, and this service must still
never itself import `BusinessRecord`- or `Case`-producing code.
"""
from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_PACKAGE_DIR = _REPO_ROOT / "atlas" / "alpha" / "canonical_security_resolution"
_OWN_TEST_DIR = _REPO_ROOT / "tests" / "unit" / "alpha" / "canonical_security_resolution"
_GATE_PACKAGE_DIR = _REPO_ROOT / "atlas" / "alpha" / "canonical_security_gate"
_GATE_TEST_DIR = _REPO_ROOT / "tests" / "unit" / "alpha" / "canonical_security_gate"
_TARGET_MODULE_PREFIX = "atlas.alpha.canonical_security_resolution"

_FORBIDDEN_IMPORT_PREFIXES = (
    "atlas.analysis_engine.business_data",
    "atlas.alpha.business_data_refresh",
    "atlas.core.domain.case",
    "atlas.alpha.case_generation",
)


def _imported_module_prefixes(source_path: Path) -> set[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _all_python_files_outside(*excluded_dirs: Path) -> list[Path]:
    files = []
    for path in _REPO_ROOT.rglob("*.py"):
        if any(part in {".venv", "node_modules", "__pycache__"} for part in path.parts):
            continue
        if any(excluded in path.parents or excluded == path for excluded in excluded_dirs):
            continue
        files.append(path)
    return files


def test_no_file_outside_this_package_and_its_own_tests_imports_it() -> None:
    offending: list[str] = []
    for path in _all_python_files_outside(_PACKAGE_DIR, _OWN_TEST_DIR, _GATE_PACKAGE_DIR, _GATE_TEST_DIR):
        modules = _imported_module_prefixes(path)
        if any(module.startswith(_TARGET_MODULE_PREFIX) for module in modules):
            offending.append(str(path.relative_to(_REPO_ROOT)))

    assert offending == [], (
        "The following files import atlas.alpha.canonical_security_resolution directly, but "
        "this shadow-mode service is only meant to be imported directly by its own package/tests "
        "and the Sprint O Identity Gate: " + ", ".join(offending)
    )


def test_package_never_imports_business_record_or_case_producing_code() -> None:
    """Structural guarantee for Sprint N's entire scope boundary --
    checked against every module in the package, not only `service.py`
    (Sprint N's own Phase 20 final-review checklist item)."""
    offending: list[str] = []
    for path in _PACKAGE_DIR.glob("*.py"):
        modules = _imported_module_prefixes(path)
        for forbidden in _FORBIDDEN_IMPORT_PREFIXES:
            if any(module.startswith(forbidden) for module in modules):
                offending.append(f"{path.name} imports {forbidden}")

    assert offending == [], "; ".join(offending)


def test_watchlist_business_data_and_investment_case_packages_are_among_the_files_scanned() -> None:
    scanned = {
        str(p.relative_to(_REPO_ROOT))
        for p in _all_python_files_outside(_PACKAGE_DIR, _OWN_TEST_DIR, _GATE_PACKAGE_DIR, _GATE_TEST_DIR)
    }
    assert "atlas/alpha/watchlist/service.py" in scanned
    assert "atlas/alpha/portfolio/service.py" in scanned
    assert "atlas/analysis_engine/business_data/models.py" in scanned
    assert "atlas/alpha/investment_case/service.py" in scanned
    # Sprint O: canonical_security/models.py is now wired into production, but only
    # indirectly (through the Gate) -- this assertion is a scan sanity check, not a
    # claim that this file is unreached by production code.
    assert "atlas/alpha/canonical_security/models.py" in scanned
