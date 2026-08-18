"""Sprint M Phase 12 -- Integration Safety.

Verifies the structural claim this package's own `__init__.py` makes:
nothing outside `atlas/alpha/canonical_security/`, its own test
directory, and Sprint N's `canonical_security_resolution` package
imports it. The Sprint N exclusion is deliberate, not a weakening of
this guard: that package is explicitly designed as "the orchestration
layer over Sprint M's foundation" (its own `__init__.py`) -- it is
*meant* to import this one. What this test still forbids is the
*production* pipeline (Watchlist, Portfolio, BusinessRecord, Investment
Case) importing either package. If this test ever fails outside that
one expected exclusion, some other change wired this foundation into
the live pipeline without updating this guard -- exactly the kind of
silent, undocumented integration Sprint M's own scope forbids ("nothing
in the current enrichment pipeline should begin using it yet").
"""
from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_PACKAGE_DIR = _REPO_ROOT / "atlas" / "alpha" / "canonical_security"
_OWN_TEST_DIR = _REPO_ROOT / "tests" / "unit" / "alpha" / "canonical_security"
_RESOLUTION_PACKAGE_DIR = _REPO_ROOT / "atlas" / "alpha" / "canonical_security_resolution"
_RESOLUTION_TEST_DIR = _REPO_ROOT / "tests" / "unit" / "alpha" / "canonical_security_resolution"
_TARGET_MODULE_PREFIX = "atlas.alpha.canonical_security"


def _imports_target(source_path: Path) -> bool:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.startswith(_TARGET_MODULE_PREFIX) for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith(_TARGET_MODULE_PREFIX):
                return True
    return False


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
    for path in _all_python_files_outside(
        _PACKAGE_DIR, _OWN_TEST_DIR, _RESOLUTION_PACKAGE_DIR, _RESOLUTION_TEST_DIR
    ):
        if _imports_target(path):
            offending.append(str(path.relative_to(_REPO_ROOT)))

    assert offending == [], (
        "The following files import atlas.alpha.canonical_security, but this "
        "foundation is not yet meant to be wired into anything outside its own "
        "package, tests, and the Sprint N Resolution Service: " + ", ".join(offending)
    )


def test_watchlist_business_data_and_investment_case_packages_are_among_the_files_scanned() -> None:
    """A sanity check on the scan itself -- if these known, relevant
    packages weren't even being walked, the assertion above would pass
    for the wrong reason (finding nothing because it looked nowhere)."""
    scanned = {
        str(p.relative_to(_REPO_ROOT))
        for p in _all_python_files_outside(_PACKAGE_DIR, _OWN_TEST_DIR, _RESOLUTION_PACKAGE_DIR, _RESOLUTION_TEST_DIR)
    }
    assert "atlas/alpha/watchlist/service.py" in scanned
    assert "atlas/alpha/portfolio/service.py" in scanned
    assert "atlas/analysis_engine/business_data/models.py" in scanned
    assert "atlas/alpha/investment_case/service.py" in scanned
