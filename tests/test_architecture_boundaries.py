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
CORE_DIR = ATLAS_ROOT / "core"
ALPHA_DIR = ATLAS_ROOT / "alpha"
DECISION_ENGINE_DIR = ATLAS_ROOT / "decision_engine"
ANALYSIS_ENGINE_DIR = ATLAS_ROOT / "analysis_engine"
AI_DIR = ATLAS_ROOT / "ai"

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


def test_core_does_not_import_atlas_alpha() -> None:
    """Alpha Sprint 1A: `atlas/alpha/` is explicitly provisional Alpha
    application state (see atlas/alpha/portfolio/__init__.py) and MAY
    read from `atlas/core/`, but `atlas/core/` MUST NOT depend on it in
    return -- that is the one direction the Alpha Sprint 1 Phase 4 plan
    (Decision A) authorizes. `atlas/core/infrastructure/api/app.py`'s own
    one composition-point import of the Alpha portfolio router is the
    sole, deliberate exception, called out in its own module comment."""
    violations = []
    for path in _python_files(CORE_DIR):
        for module in _imported_modules(path):
            if module.startswith("atlas.alpha") and "infrastructure/api/app.py" not in str(path):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "atlas/core importing atlas/alpha:\n" + "\n".join(violations)


def test_alpha_does_not_write_to_outcome() -> None:
    """Alpha Sprint 1B: "The Alpha layer may reference Outcome. Outcome
    must never reference Alpha." `atlas/alpha` is authorized to read
    Outcome (via `OutcomeRepository.get` and `OutcomeId`, both plain
    interfaces/value objects with no write behavior) but must never
    import Outcome's own write path -- its entity constructor or its
    application-layer capture service -- since doing so would let Alpha
    originate or mutate a Core object. Forbidding those two specific
    imports enforces this directly rather than relying on convention."""
    forbidden_prefixes = (
        "atlas.core.application.outcome",
        "atlas.core.domain.outcome.entity",
    )
    violations = []
    for path in _python_files(ALPHA_DIR):
        for module in _imported_modules(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "atlas/alpha writing to Outcome:\n" + "\n".join(violations)


def test_core_does_not_import_atlas_decision_engine() -> None:
    """Decision Engine Implementation Sprint 1: `atlas/decision_engine/`
    is explicitly provisional pipeline scaffolding (see
    atlas/decision_engine/__init__.py) and MAY read from `atlas/core/`,
    but `atlas/core/` MUST NOT depend on it in return -- the same
    one-way relationship `test_core_does_not_import_atlas_alpha` already
    enforces for `atlas/alpha/`, applied here to a second, structurally
    identical sibling package. No exception is authorized for this one:
    unlike Alpha, no composition point currently wires the Decision
    Engine into the API at all."""
    violations = []
    for path in _python_files(CORE_DIR):
        for module in _imported_modules(path):
            if module.startswith("atlas.decision_engine"):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "atlas/core importing atlas/decision_engine:\n" + "\n".join(
        violations
    )


def test_decision_engine_only_reads_core_domain_entities() -> None:
    """Decision Engine Implementation Sprint 1: the engine's own locked
    scope is "only one-way reading from Core" -- read-only Domain
    entities and value objects, never a repository, an application
    service, or infrastructure. Forbidding those imports enforces the
    read-only boundary directly rather than relying on convention, the
    same technique `test_alpha_does_not_write_to_outcome` already uses
    for Alpha's own read-only relationship to Outcome. Also forbidden:
    `atlas.alpha` (this sprint does not authorize that coupling; see
    `ReconciliationState` in `atlas/decision_engine/contracts.py`) and
    any legacy `atlas.decision`/`atlas.domains.decision` module (a
    different, non-superseding "Decision" track; see
    `docs/DecisionEngine.md`'s own supersession notice)."""
    forbidden_prefixes = (
        "atlas.core.application",
        "atlas.core.infrastructure",
        "atlas.alpha",
        "atlas.decision.",
        "atlas.decision_engine.decision",  # guards against a future misnamed module
        "atlas.domains.decision",
        "atlas.providers",
        "atlas.cli",
    )
    # atlas.core.domain.<feature>.repository defines an interface only
    # (no I/O implementation lives there), but this sprint's engine does
    # not need even a repository interface yet -- forbid it too, so a
    # future sprint must add this permission deliberately rather than by
    # accident.
    forbidden_suffixes = (".repository",)

    violations = []
    for path in _python_files(DECISION_ENGINE_DIR):
        for module in _imported_modules(path):
            if module.startswith(forbidden_prefixes) or module.endswith(
                forbidden_suffixes
            ):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "atlas/decision_engine boundary violation:\n" + "\n".join(
        violations
    )


def test_core_does_not_import_atlas_analysis_engine() -> None:
    """ATLAS-020 Phase 2: `atlas/analysis_engine/` mirrors
    `atlas/decision_engine/`'s own one-way relationship with Core (see
    `test_core_does_not_import_atlas_decision_engine`) — it MAY read
    from `atlas/core/`, but `atlas/core/` MUST NOT depend on it in
    return. No composition point wires the Analysis Engine into the API
    yet, so no exception is authorized."""
    violations = []
    for path in _python_files(CORE_DIR):
        for module in _imported_modules(path):
            if module.startswith("atlas.analysis_engine"):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "atlas/core importing atlas/analysis_engine:\n" + "\n".join(
        violations
    )


def test_analysis_engine_only_reads_core_and_decision_engine() -> None:
    """ATLAS-020 Phase 2: this sprint's own locked scope, stated in
    `atlas/analysis_engine/__init__.py` — the package reads only
    `atlas.core.domain` and `atlas.decision_engine`. It never imports
    `atlas.alpha` (real Alpha portfolio/trade data stays a future
    composition-layer concern, the same boundary
    `test_decision_engine_only_reads_core_domain_entities` already
    enforces for its sibling package), never `atlas.core.application`
    or `atlas.core.infrastructure` (this package is read-only; see
    `lifecycle.py`'s own Phase 11 verdict against building a write
    path here), and never a bare `.repository` module (no repository
    interface is needed yet — forbidding it now means a future sprint
    must add that permission deliberately, not by accident, mirroring
    the Decision Engine's own identical guard)."""
    forbidden_prefixes = (
        "atlas.core.application",
        "atlas.core.infrastructure",
        "atlas.alpha",
        "atlas.providers",
        "atlas.cli",
    )
    forbidden_suffixes = (".repository",)

    violations = []
    for path in _python_files(ANALYSIS_ENGINE_DIR):
        for module in _imported_modules(path):
            if module.startswith(forbidden_prefixes) or module.endswith(
                forbidden_suffixes
            ):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "atlas/analysis_engine boundary violation:\n" + "\n".join(
        violations
    )


def test_ai_discovery_chat_does_not_import_atlas_alpha() -> None:
    """Discovery Intelligence v1: `atlas/ai/discovery_chat.py` (and
    every other file in `atlas/ai/` except its own composition point,
    `atlas/ai/api/router.py`) MUST NOT import `atlas.alpha` -- the same
    one-way discipline `test_core_does_not_import_atlas_alpha` and
    `test_decision_engine_only_reads_core_domain_entities` already
    enforce for their own provider-agnostic cores. `atlas/ai/api/router.py`
    is `atlas/ai/`'s own single deliberate composition point with real
    Alpha portfolio state, exempted here exactly as
    `atlas/core/infrastructure/api/app.py` is exempted from the Core
    equivalent of this rule."""
    violations = []
    for path in _python_files(AI_DIR):
        if "ai/api/router.py" in str(path):
            continue
        for module in _imported_modules(path):
            if module.startswith("atlas.alpha"):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "atlas/ai importing atlas/alpha outside its composition point:\n" + "\n".join(
        violations
    )


def test_discovery_context_does_not_import_case_intelligence() -> None:
    """ATLAS-030: Discovery's canonical composition (`atlas/alpha
    /discovery_context/case_projection.py`, `service.py`,
    `dependencies.py`, `models.py`) must never depend on the legacy
    `atlas.alpha.case_intelligence` path it was migrated off of.
    `diff.py` is the one documented exception: `diff_case_intelligence`
    is pre-existing dead code (no live caller anywhere in `atlas/`,
    confirmed by this sprint's own audit) that independently type-hints
    against the legacy report shape for its own unused function
    signature -- harmless, and deliberately left untouched rather than
    deleted (Phase 16's own "the safer default is to keep, not delete"
    rule)."""
    discovery_context_dir = ALPHA_DIR / "discovery_context"
    violations = []
    for path in _python_files(discovery_context_dir):
        if path.name == "diff.py":
            continue
        for module in _imported_modules(path):
            if module.startswith("atlas.alpha.case_intelligence"):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "discovery_context depending on legacy case_intelligence:\n" + "\n".join(violations)


def test_discovery_context_never_imports_individual_evaluators() -> None:
    """ATLAS-030 Phase 17: Discovery may consume canonical result types
    (`CanonicalAnalysis`, `ConvictionAssessment`, ...) and composition
    services (`InvestmentCaseCompositionService`), but must never import
    an individual analytical evaluator or recomputation function
    directly -- it must not become a second reasoning engine."""
    forbidden_prefixes = (
        "atlas.analysis_engine.growth",
        "atlas.analysis_engine.capital_allocation",
        "atlas.analysis_engine.business_data",
        "atlas.analysis_engine.business_facts",
        "atlas.analysis_engine.valuation.cash_flow",
        "atlas.analysis_engine.risk.business_risk",
        "atlas.analysis_engine.risk.financial_risk",
        "atlas.analysis_engine.risk.valuation_risk",
        "atlas.analysis_engine.risk.thesis_risk",
        "atlas.decision_engine.pipeline",
        "atlas.decision_engine.stages",
    )
    forbidden_calls = ("calculate_conviction(", "assemble_analysis(", "run_pipeline(")

    discovery_context_dir = ALPHA_DIR / "discovery_context"
    violations = []
    for path in _python_files(discovery_context_dir):
        text = path.read_text(encoding="utf-8")
        for module in _imported_modules(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")
        for call in forbidden_calls:
            if call in text:
                violations.append(f"{path.relative_to(REPO_ROOT)} calls {call}")

    assert not violations, "discovery_context reasoning-engine leakage:\n" + "\n".join(violations)


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


# ── ATLAS-023: legacy company-analysis/scoring tree stays unreachable ────────


def test_analysis_engine_never_imports_the_legacy_company_analysis_tree() -> None:
    """ATLAS-023's own audit found `atlas/analysis/company_analysis.py`
    and `atlas/providers/{yahoo,base,mock}.py` still exist, still return
    hardcoded fake scores, and are still confirmed unreachable from the
    live app. This test makes that confirmation permanent: the real
    `atlas.analysis_engine` package (Growth and Capital Allocation
    included) must never import either legacy tree, ever."""
    forbidden_prefixes = ("atlas.analysis.company_analysis", "atlas.analysis.engine", "atlas.providers")
    violations = []
    for path in _python_files(ATLAS_ROOT / "analysis_engine"):
        for module in _imported_modules(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "atlas.analysis_engine importing legacy scoring code:\n" + "\n".join(violations)


# ── ATLAS-024: legacy value_scenario tree stays unreachable, studied not reused ──


def test_analysis_engine_never_imports_the_legacy_value_scenario_tree() -> None:
    """ATLAS-024's own audit studied `atlas/value_scenario/schema.py` as
    prior art (confirmed unreachable from the live app, same legacy
    tree) for `atlas.analysis_engine.valuation.scenarios`'s own
    BEAR/BASE/BULL structure -- but never imported any of it. This test
    makes that confirmation permanent."""
    violations = []
    for path in _python_files(ATLAS_ROOT / "analysis_engine"):
        for module in _imported_modules(path):
            if module.startswith("atlas.value_scenario"):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "atlas.analysis_engine importing legacy value_scenario code:\n" + "\n".join(violations)


# ── ATLAS-031: real provider boundary -- network stays at the boundary,
#    read-side composition never calls out, evaluators never see a provider ──


def test_analysis_engine_never_imports_business_data_providers() -> None:
    """The real, network-calling `atlas.business_data_providers` package
    must never be imported anywhere under `atlas.analysis_engine` --
    the Analysis Engine consumes already-ingested `BusinessRecord`s
    (via `assemble_analysis(business_records=...)`), never a provider
    directly. Mirrors the identical rule this file already enforces for
    the legacy `atlas.providers` tree."""
    violations = []
    for path in _python_files(ANALYSIS_ENGINE_DIR):
        for module in _imported_modules(path):
            if module.startswith("atlas.business_data_providers"):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "atlas.analysis_engine importing atlas.business_data_providers:\n" + "\n".join(
        violations
    )


def test_portfolio_cockpit_investment_case_discovery_never_import_business_data_providers() -> None:
    """Portfolio Cockpit, the canonical Investment Case package, and
    Discovery all consume `BusinessRecord`s exclusively through
    `InvestmentCaseCompositionService` -- none of them may import the
    real provider package directly. Only `atlas.alpha.business_data_refresh`
    (the one explicit, operator-triggered write path) is allowed to."""
    scoped_dirs = (
        ALPHA_DIR / "portfolio_cockpit",
        ALPHA_DIR / "investment_case",
        ALPHA_DIR / "discovery_context",
    )
    violations = []
    for directory in scoped_dirs:
        for path in _python_files(directory):
            for module in _imported_modules(path):
                if module.startswith("atlas.business_data_providers"):
                    violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, (
        "Portfolio Cockpit/Investment Case/Discovery importing atlas.business_data_providers directly:\n"
        + "\n".join(violations)
    )


def test_only_business_data_refresh_imports_business_data_providers() -> None:
    """The real provider package is meant to have exactly one caller in
    the whole application: `atlas.alpha.business_data_refresh` (Phase
    15/17 -- the one explicit refresh use case). Any other importer
    would mean a second, undisclosed path to a real network call."""
    allowed_prefixes = ("atlas.alpha.business_data_refresh", "atlas.business_data_providers")
    violations = []
    for path in _python_files(ATLAS_ROOT):
        if any(str(path.relative_to(REPO_ROOT)).startswith(prefix.replace(".", "/")) for prefix in allowed_prefixes):
            continue
        for module in _imported_modules(path):
            if module.startswith("atlas.business_data_providers"):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "Unexpected importer of atlas.business_data_providers:\n" + "\n".join(violations)


def test_business_data_providers_never_imports_evaluators_or_decision_engine() -> None:
    """The real provider package must return only `RawBusinessDocument`
    tuples -- it must never import an evaluator, the Decision Engine,
    or the Analysis Engine's own orchestration/business-conclusion
    modules. Provider-specific parsing stays entirely structural."""
    #: deliberately excludes "atlas.analysis_engine.business_data" and
    #: "atlas.analysis_engine.business_facts" -- both are legitimate,
    #: purely structural imports a provider needs (`RawBusinessDocument`,
    #: `SourceKind`) to construct valid input for the pipeline; neither
    #: is an evaluator or a reasoning module.
    forbidden_prefixes = (
        "atlas.decision_engine",
        "atlas.analysis_engine.growth",
        "atlas.analysis_engine.capital_allocation",
        "atlas.analysis_engine.valuation.cash_flow",
        "atlas.analysis_engine.valuation.pipeline",
        "atlas.analysis_engine.risk",
        "atlas.analysis_engine.conviction",
        "atlas.analysis_engine.recommendation",
        "atlas.analysis_engine.pipeline",
    )
    forbidden_call_text = (
        "calculate_conviction(",
        "assemble_analysis(",
        "run_pipeline(",
        "evaluate_growth(",
        "evaluate_business_analysis(",
    )
    violations = []
    provider_dir = ATLAS_ROOT / "business_data_providers"
    for path in _python_files(provider_dir):
        for module in _imported_modules(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")
        text = path.read_text(encoding="utf-8")
        for needle in forbidden_call_text:
            if needle in text:
                violations.append(f"{path.relative_to(REPO_ROOT)} contains call text {needle!r}")

    assert not violations, "atlas.business_data_providers reasoning leakage found:\n" + "\n".join(violations)


def test_business_facts_and_valuation_facts_extraction_stay_provider_agnostic() -> None:
    """Confirms the ATLAS-023/024 extraction modules were not made
    provider-aware by this sprint -- they must still only read
    `BusinessRecord.metadata`'s canonical keys, never import or branch
    on `atlas.business_data_providers`."""
    scoped_files = (
        ANALYSIS_ENGINE_DIR / "business_facts" / "extraction.py",
        ANALYSIS_ENGINE_DIR / "valuation" / "facts.py",
    )
    violations = []
    for path in scoped_files:
        for module in _imported_modules(path):
            if module.startswith("atlas.business_data_providers"):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "Fact extraction became provider-aware:\n" + "\n".join(violations)


def test_investment_case_composition_read_paths_never_import_network_libraries() -> None:
    """`InvestmentCaseCompositionService.build`/`build_many` (and
    Portfolio Cockpit's/Discovery's own composition modules) must stay
    pure reads -- no `httpx`/`requests`/`urlopen` import anywhere in
    those packages. Only `atlas.business_data_providers` (which this
    file's own boundary tests keep isolated to
    `atlas.alpha.business_data_refresh`) may make a real network call."""
    scoped_dirs = (
        ALPHA_DIR / "investment_case",
        ALPHA_DIR / "portfolio_cockpit",
        ALPHA_DIR / "discovery_context",
    )
    forbidden_anywhere = ("import httpx", "import requests", "import aiohttp", "urlopen(")
    violations = []
    for directory in scoped_dirs:
        for path in _python_files(directory):
            text = path.read_text(encoding="utf-8")
            for needle in forbidden_anywhere:
                if needle in text:
                    violations.append(f"{path.relative_to(REPO_ROOT)} contains {needle!r}")

    assert not violations, "Network capability found in a read-side composition package:\n" + "\n".join(violations)


def test_investment_case_history_never_imports_composition_or_providers() -> None:
    """History v1 (Scenario 25/26): `atlas.alpha.investment_case_history`
    must stay strictly read-only over already-persisted snapshots -- it
    must never import `InvestmentCaseCompositionService` (which *would*
    have the side effect of persisting a new snapshot via `.build`/
    `.build_many`), and never `atlas.business_data_providers` (a real
    network call). Opening History can only read; it can never trigger
    the analysis this file's own composition service performs."""
    package_dir = ALPHA_DIR / "investment_case_history"
    #: `atlas.alpha.investment_case.service` is where
    #: `InvestmentCaseCompositionService` (the one thing that persists a
    #: new snapshot) is defined -- forbidding the *module* import, not
    #: just the symbol name, since every file in this package legitimately
    #: mentions the class name in prose explaining why it is not used.
    forbidden_prefixes = ("atlas.business_data_providers", "atlas.alpha.investment_case.service")
    violations = []
    for path in _python_files(package_dir):
        for module in _imported_modules(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "History v1 read-only boundary violated:\n" + "\n".join(violations)
