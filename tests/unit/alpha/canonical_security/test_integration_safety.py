"""Sprint M Phase 12 -- Integration Safety.

Verifies the structural claim this package's own `__init__.py` makes:
nothing outside `atlas/alpha/canonical_security/`, its own test
directory, Sprint N's `canonical_security_resolution` package, and
Sprint O's `canonical_security_gate` package imports it. Both
exclusions are deliberate, not a weakening of this guard: Sprint N's
package is explicitly "the orchestration layer over Sprint M's
foundation" and Sprint O's package is explicitly the one sanctioned
integration point that wires that orchestration into the live
enrichment pipeline (`atlas.alpha.business_data_refresh.service
.refresh_company_data`) -- both are *meant* to import this one. What
this test still forbids is anything else in the *production* pipeline
(Watchlist, Portfolio) importing `canonical_security` directly, or
`BusinessRecord`/Investment Case importing it at all. If this test ever
fails outside these two expected exclusions, some other change wired
this foundation into the live pipeline through an undocumented path --
exactly the kind of silent integration this guard exists to catch.
"""
from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_PACKAGE_DIR = _REPO_ROOT / "atlas" / "alpha" / "canonical_security"
_OWN_TEST_DIR = _REPO_ROOT / "tests" / "unit" / "alpha" / "canonical_security"
_RESOLUTION_PACKAGE_DIR = _REPO_ROOT / "atlas" / "alpha" / "canonical_security_resolution"
_RESOLUTION_TEST_DIR = _REPO_ROOT / "tests" / "unit" / "alpha" / "canonical_security_resolution"
_GATE_PACKAGE_DIR = _REPO_ROOT / "atlas" / "alpha" / "canonical_security_gate"
_GATE_TEST_DIR = _REPO_ROOT / "tests" / "unit" / "alpha" / "canonical_security_gate"
_TARGET_MODULE_PREFIX = "atlas.alpha.canonical_security"


def _is_or_is_under(module: str, prefix: str) -> bool:
    """Dot-boundary-safe prefix match. A plain `str.startswith(prefix)`
    would wrongly treat `atlas.alpha.canonical_security_gate` (a
    sibling package) as importing `atlas.alpha.canonical_security`,
    since the raw string `"canonical_security_gate"` itself starts
    with `"canonical_security"`. Every real caller of this module
    imports `canonical_security_gate`/`canonical_security_resolution`,
    never `canonical_security` directly, so this boundary check is
    what keeps this guard testing the right thing."""
    return module == prefix or module.startswith(prefix + ".")


def _imports_target(source_path: Path) -> bool:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(_is_or_is_under(alias.name, _TARGET_MODULE_PREFIX) for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if _is_or_is_under(module, _TARGET_MODULE_PREFIX):
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


_EXCLUDED_DIRS = (_PACKAGE_DIR, _OWN_TEST_DIR, _RESOLUTION_PACKAGE_DIR, _RESOLUTION_TEST_DIR, _GATE_PACKAGE_DIR, _GATE_TEST_DIR)


def test_no_file_outside_this_package_and_its_own_tests_imports_it() -> None:
    offending: list[str] = []
    for path in _all_python_files_outside(*_EXCLUDED_DIRS):
        if _imports_target(path):
            offending.append(str(path.relative_to(_REPO_ROOT)))

    assert offending == [], (
        "The following files import atlas.alpha.canonical_security directly, but this "
        "foundation is only meant to be imported directly by its own package/tests, the "
        "Sprint N Resolution Service, and the Sprint O Identity Gate -- everything else "
        "(Watchlist, Portfolio, business_data_refresh) must go through the Gate, never "
        "this package directly: " + ", ".join(offending)
    )


def test_watchlist_business_data_and_investment_case_packages_are_among_the_files_scanned() -> None:
    """A sanity check on the scan itself -- if these known, relevant
    packages weren't even being walked, the assertion above would pass
    for the wrong reason (finding nothing because it looked nowhere)."""
    scanned = {str(p.relative_to(_REPO_ROOT)) for p in _all_python_files_outside(*_EXCLUDED_DIRS)}
    assert "atlas/alpha/watchlist/service.py" in scanned
    assert "atlas/alpha/portfolio/service.py" in scanned
    assert "atlas/analysis_engine/business_data/models.py" in scanned
    assert "atlas/alpha/investment_case/service.py" in scanned


def test_watchlist_and_portfolio_import_the_gate_not_canonical_security_directly() -> None:
    """Sprint O's own positive check: `watchlist/service.py` and
    `portfolio/service.py` now legitimately depend on identity
    resolution (via the Gate), but must reach it exclusively through
    `canonical_security_gate` -- never a direct import of this
    package. This is the fact that makes the boundary check above
    (dot-safe prefix matching) load-bearing rather than incidental."""
    watchlist = _REPO_ROOT / "atlas" / "alpha" / "watchlist" / "service.py"
    portfolio = _REPO_ROOT / "atlas" / "alpha" / "portfolio" / "service.py"
    assert not _imports_target(watchlist), "watchlist/service.py must not import canonical_security directly"
    assert not _imports_target(portfolio), "portfolio/service.py must not import canonical_security directly"
