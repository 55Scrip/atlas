"""Lightweight static guardrails for Sprint 44 architecture consolidation.

These tests scan source files rather than importing modules, so they stay
fast and do not require network access.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ATLAS_ROOT = REPO_ROOT / "atlas"

DOMAINS_DIR = ATLAS_ROOT / "domains"
CAPABILITIES_DIR = ATLAS_ROOT / "capabilities"

FORBIDDEN_EDGE_PATTERNS = (
    "atlas edge",
    "atlas_edge",
    "atlasedge",
)

IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([\w\.]+)", re.MULTILINE)


def _python_files(directory: Path) -> list[Path]:
    return [
        path
        for path in directory.rglob("*.py")
        if "__pycache__" not in path.parts
    ]


def _imported_modules(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return set(IMPORT_RE.findall(text))


def test_domains_do_not_import_capabilities_or_providers_or_legacy() -> None:
    forbidden_prefixes = (
        "atlas.capabilities",
        "atlas.providers",
        "atlas.cli",
        "atlas.frontend",
        "atlas.backend",
        "atlas.database",
        "atlas.services",
        "atlas.adapters",
        # Legacy engine modules — domains must not import these (Sprint 75)
        "atlas.daily",
        "atlas.daily_brief",
        "atlas.analysis",
        "atlas.portfolio_review",
        "atlas.watchlist_review",
        "atlas.home",
        "atlas.dashboard",
        "atlas.intelligence",
    )

    violations = []
    for path in _python_files(DOMAINS_DIR):
        for module in _imported_modules(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "Domain layer boundary violations:\n" + "\n".join(violations)


def test_capabilities_do_not_import_providers_or_call_network_directly() -> None:
    forbidden_prefixes = ("atlas.providers",)
    forbidden_network_modules = {"urllib", "urllib.request", "requests", "httpx"}

    violations = []
    for path in _python_files(CAPABILITIES_DIR):
        modules = _imported_modules(path)
        for module in modules:
            if module.startswith(forbidden_prefixes) or module in forbidden_network_modules:
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "Capability layer boundary violations:\n" + "\n".join(violations)


def test_no_atlas_edge_naming_in_active_code_paths() -> None:
    """Atlas Edge naming must not appear in code or filenames.

    Documentation may legitimately reference "Atlas Edge" by name when
    clarifying repository identity (see docs/ArchitectureConsolidation.md),
    so only atlas/ and tests/ are scanned here.
    """
    search_dirs = [ATLAS_ROOT, REPO_ROOT / "tests"]
    violations = []

    for directory in search_dirs:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_dir() or "__pycache__" in path.parts:
                continue
            if path.suffix not in {".py", ".md"}:
                continue

            lowered_name = path.name.lower()
            for pattern in FORBIDDEN_EDGE_PATTERNS:
                if pattern.replace(" ", "_") in lowered_name or pattern.replace(" ", "") in lowered_name:
                    violations.append(f"filename: {path.relative_to(REPO_ROOT)}")

            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for pattern in FORBIDDEN_EDGE_PATTERNS:
                if pattern in text:
                    violations.append(f"content: {path.relative_to(REPO_ROOT)} contains '{pattern}'")

    # This file intentionally documents the forbidden patterns; exclude it.
    self_path = str(Path(__file__).relative_to(REPO_ROOT))
    violations = [v for v in violations if self_path not in v]

    assert not violations, "Atlas Edge naming found in active code paths:\n" + "\n".join(violations)


def test_adapters_may_bridge_legacy_and_domain_layers() -> None:
    """Sprint 45: atlas.adapters is the one layer allowed to import both
    legacy modules and atlas.domains/atlas.shared. Domains must not import
    adapters back (see test_domains_do_not_import_capabilities_or_providers_or_legacy)."""
    adapters_dir = ATLAS_ROOT / "adapters"
    assert adapters_dir.exists()

    portfolio_adapter = adapters_dir / "portfolio.py"
    modules = _imported_modules(portfolio_adapter)
    assert any(m.startswith("atlas.analysis") for m in modules)
    assert any(m.startswith("atlas.shared") or m.startswith("atlas.domains") for m in modules)


def test_default_provider_import_has_no_top_level_network_call() -> None:
    """The mock provider must not make network calls at module scope.

    We check this via source inspection rather than live import because
    atlas.providers.mock imports atlas.analysis, and atlas.analysis.__init__
    imports atlas.providers, creating a circular dependency that raises
    ImportError when either is the very first module loaded in a fresh
    process. Source scanning avoids that ordering issue while still verifying
    the intent: no top-level urlopen/requests/httpx calls in the mock file.
    """
    mock_path = ATLAS_ROOT / "providers" / "mock.py"
    text = mock_path.read_text(encoding="utf-8")
    assert "urlopen" not in text
    assert "requests." not in text
    assert "httpx" not in text


def test_mock_provider_is_the_documented_default() -> None:
    # Source check only -- see test_default_provider_import_has_no_top_level_network_call
    # for the explanation of why we avoid live import here.
    providers_init = ATLAS_ROOT / "providers" / "__init__.py"
    text = providers_init.read_text(encoding="utf-8")
    assert "MockCompanyAnalysisProvider" in text


# ── Sprint 74: legacy consolidation plan guardrails ───────────────────────────

DOCS_DIR = REPO_ROOT / "docs"


def test_legacy_consolidation_plan_exists() -> None:
    plan = DOCS_DIR / "LegacyConsolidationPlan.md"
    assert plan.exists(), "docs/LegacyConsolidationPlan.md not found"


def test_legacy_consolidation_plan_documents_sprint_75_target() -> None:
    plan = (DOCS_DIR / "LegacyConsolidationPlan.md").read_text()
    assert "Sprint 75" in plan
    assert "atlas/daily/" in plan


def test_providers_not_imported_by_demo_script() -> None:
    demo_script = REPO_ROOT / "scripts" / "run_daily_brief_demo.sh"
    text = demo_script.read_text()
    assert "yahoo" not in text.lower()
    assert "provider" not in text.lower()


def test_providers_not_imported_by_verify_script() -> None:
    verify_script = REPO_ROOT / "scripts" / "verify_release_candidate.sh"
    text = verify_script.read_text()
    assert "yahoo" not in text.lower()
    assert "provider" not in text.lower()


def test_atlas_daily_shim_is_removed() -> None:
    """Sprint 75: atlas/daily/ shim was deleted — the directory must not exist."""
    assert not (ATLAS_ROOT / "daily").exists(), "atlas/daily/ shim should have been removed in Sprint 75"


def test_domains_daily_brief_does_not_import_legacy() -> None:
    """Sprint 75: atlas/domains/daily_brief/ must not import from legacy modules."""
    domain_daily_brief = ATLAS_ROOT / "domains" / "daily_brief" / "__init__.py"
    text = domain_daily_brief.read_text()
    forbidden = ("atlas.daily_brief", "atlas.daily", "atlas.analysis")
    for mod in forbidden:
        assert mod not in text, f"atlas/domains/daily_brief/__init__.py still imports {mod}"


def test_legacy_shim_atlas_daily_is_documented_as_migration_target() -> None:
    plan = (DOCS_DIR / "LegacyConsolidationPlan.md").read_text()
    assert "atlas/daily/" in plan
    assert "re-export" in plan or "shim" in plan


def test_readme_links_to_consolidation_plan() -> None:
    readme = (REPO_ROOT / "README.md").read_text()
    assert "LegacyConsolidationPlan.md" in readme


# ── Sprint 77: legacy daily_brief engine removal guardrails ──────────────────


def test_atlas_daily_brief_engine_is_removed() -> None:
    """Sprint 77: atlas/daily_brief/ was deleted — the directory must not exist."""
    assert not (ATLAS_ROOT / "daily_brief").exists(), (
        "atlas/daily_brief/ legacy engine should have been removed in Sprint 77"
    )


def test_atlas_daily_brief_is_not_importable() -> None:
    """Sprint 77: atlas.daily_brief must not be importable."""
    import importlib
    import sys

    # Ensure no cached module from a prior import
    sys.modules.pop("atlas.daily_brief", None)

    try:
        importlib.import_module("atlas.daily_brief")
        raise AssertionError("atlas.daily_brief should not be importable after Sprint 77 deletion")
    except ModuleNotFoundError:
        pass  # expected


def test_no_active_code_imports_atlas_daily_brief() -> None:
    """Sprint 77: no source file outside atlas/daily_brief/ should import atlas.daily_brief."""
    violations = []
    search_dirs = [ATLAS_ROOT, REPO_ROOT / "tests", REPO_ROOT / "scripts"]
    for directory in search_dirs:
        if not directory.exists():
            continue
        for path in directory.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for module in IMPORT_RE.findall(text):
                if module.startswith("atlas.daily_brief"):
                    violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "Active imports of atlas.daily_brief found:\n" + "\n".join(violations)
