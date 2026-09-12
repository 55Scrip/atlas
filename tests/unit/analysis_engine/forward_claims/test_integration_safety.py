"""Forward-Looking Evidence, Stage 1 -- the boundary that makes the rest
of this package safe.

A `ForwardClaim` is what management *said it expects*. A `BusinessFact`
is what a company *did*. They differ by a single word in English and by
everything in arithmetic: fed to a growth calculation, the first is a
data point and the second is a hope. Nothing in Atlas's analysis or
decision path may import this package, so a management expectation
cannot reach Growth, Capital Allocation, Valuation, FCF Yield, Financial
Risk, Outlook, Conviction or Recommendation -- not by accident, and not
by a future edit that looks harmless.

One deliberate seam exists (Recommendation Reasoning Forward-Context
Integration): `atlas.analysis_engine.forward_context` restates forward
evidence as non-directional reasoning context, only the pipeline calls
it, and the gate carries it without handing it to anything that decides.
Every one of those limits is pinned below.

Scanned over `atlas/` only, deliberately: this asks a question about
production source, and the repository root also contains unrelated
physical worktree copies from other sessions whose files would answer
it wrongly.
"""
from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_PRODUCTION_ROOT = _REPO_ROOT / "atlas"
_PACKAGE_DIR = _PRODUCTION_ROOT / "analysis_engine" / "forward_claims"
_TARGET = "atlas.analysis_engine.forward_claims"


def _is_or_is_under(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(prefix + ".")


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add(node.module or "")
    return modules


def _production_files_outside_the_package() -> list[Path]:
    return [
        path
        for path in _PRODUCTION_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts and _PACKAGE_DIR not in path.parents
    ]


#: The one deliberate seam (Recommendation Reasoning Forward-Context
#: Integration): a builder that restates forward evidence as reasoning
#: *context*, carried by the recommendation gate and read by nothing that
#: decides anything. Everything else stays unable to see forward evidence.
_SANCTIONED_IMPORTER = "atlas/analysis_engine/forward_context.py"
_BUILDER = "atlas.analysis_engine.forward_context"
_SANCTIONED_BUILDER_CALLER = "atlas/analysis_engine/pipeline.py"

#: Modules that decide something -- direction, drivers, conviction, risk,
#: valuation, business analysis, decision support, reasoning vocabulary.
#: None may import forward evidence or its reasoning-context builder.
_DECIDING_MODULES = (
    "atlas/analysis_engine/direction_selector.py",
    "atlas/analysis_engine/recommendation.py",
    "atlas/analysis_engine/recommendation_conviction.py",
    "atlas/analysis_engine/conviction.py",
    "atlas/analysis_engine/reasoning.py",
    "atlas/analysis_engine/business.py",
    "atlas/analysis_engine/capital_allocation.py",
    "atlas/analysis_engine/growth.py",
    "atlas/analysis_engine/outlook.py",
    "atlas/alpha/decision_support.py",
)


def test_only_the_forward_context_builder_imports_forward_claims() -> None:
    """Stage 1's point, amended by exactly one seam: forward evidence
    exists, and the only production code that reads it is the builder
    that turns it into non-directional reasoning context."""
    offending = [
        str(path.relative_to(_REPO_ROOT))
        for path in _production_files_outside_the_package()
        if any(_is_or_is_under(module, _TARGET) for module in _imported_modules(path))
    ]
    assert offending == [_SANCTIONED_IMPORTER], (
        "Only the forward-context builder may read forward evidence, but these production "
        "modules import it: " + ", ".join(offending)
    )


def test_only_the_pipeline_calls_the_forward_context_builder() -> None:
    offending = [
        str(path.relative_to(_REPO_ROOT))
        for path in _production_files_outside_the_package()
        if _BUILDER in _imported_modules(path)
    ]
    assert offending == [_SANCTIONED_BUILDER_CALLER], ", ".join(offending)


def test_no_deciding_module_can_see_forward_evidence() -> None:
    for relative in (*_DECIDING_MODULES, *(str(p.relative_to(_REPO_ROOT)) for p in (_PRODUCTION_ROOT / "analysis_engine" / "risk").glob("*.py")),
                     *(str(p.relative_to(_REPO_ROOT)) for p in (_PRODUCTION_ROOT / "analysis_engine" / "valuation").glob("*.py"))):
        modules = _imported_modules(_REPO_ROOT / relative)
        leaked = [m for m in modules if _is_or_is_under(m, _TARGET) or _is_or_is_under(m, _BUILDER)]
        assert leaked == [], f"{relative} imports forward evidence: {leaked}"


def test_the_gate_hands_forward_context_to_no_deciding_call() -> None:
    """Structural: inside the recommendation gate, `forward_context`
    appears only as the value of `RecommendationReasoning(forward_context=...)`
    -- never as an argument to the calls that choose the direction,
    drivers, triggers, unknowns or conviction."""
    tree = ast.parse((_PRODUCTION_ROOT / "analysis_engine" / "recommendation.py").read_text(encoding="utf-8"))
    deciding = {"select_direction", "build_drivers", "build_signal_summary", "_derive_what_would_change",
                "build_key_unknowns", "calculate_recommendation_conviction", "build_conviction_reasoning",
                "has_company_fundamentals_evidence", "determine_recommendation"}
    uses, leaks = [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", getattr(node.func, "attr", None))
            direct = [*node.args, *(k.value for k in node.keywords)]
            if any(isinstance(arg, ast.Name) and arg.id == "forward_context" for arg in direct):
                uses.append(name)
            if name in deciding and any(
                isinstance(n, ast.Name) and n.id == "forward_context" for arg in direct for n in ast.walk(arg)
            ):
                leaks.append(name)  # e.g. `dampening or bool(forward_context)`
    assert uses and set(uses) == {"RecommendationReasoning"}, uses
    assert leaks == [], f"forward context reaches a deciding call: {leaks}"


def test_forward_claims_never_imports_the_historical_fact_layer() -> None:
    """The firewall holds in both directions. A ForwardClaim that could
    be built from a `BusinessFact`, or that reused its kinds, would blur
    exactly the line this package exists to draw."""
    forbidden = ("atlas.analysis_engine.business_facts", "atlas.decision_engine")
    offending: list[str] = []
    for path in _PACKAGE_DIR.rglob("*.py"):
        for module in _imported_modules(path):
            if any(_is_or_is_under(module, prefix) for prefix in forbidden):
                offending.append(f"{path.relative_to(_REPO_ROOT)} -> {module}")
    assert offending == [], "Forward claims must not depend on historical facts: " + ", ".join(offending)


def test_forward_claim_is_not_a_business_fact() -> None:
    """No shared base class, no structural substitutability. A
    `ForwardClaim` must never satisfy an `isinstance` check some future
    consumer writes against `BusinessFact`."""
    from atlas.analysis_engine.business_facts.models import BusinessFact
    from atlas.analysis_engine.forward_claims.models import ForwardClaim

    assert not issubclass(ForwardClaim, BusinessFact)
    assert not issubclass(BusinessFact, ForwardClaim)
    assert set(ForwardClaim.__mro__) & set(BusinessFact.__mro__) == {object}


def test_forward_claim_has_no_field_a_historical_evaluator_would_recognise() -> None:
    """`BusinessFact` consumers read `.kind`, `.value` and `.period`.
    A `ForwardClaim` deliberately has none of those names, so duck-typed
    code cannot consume one by accident -- it fails loudly instead."""
    from dataclasses import fields

    from atlas.analysis_engine.forward_claims.models import ForwardClaim

    names = {f.name for f in fields(ForwardClaim)}
    assert "kind" not in names, "a claim's subject is `subject`, never `kind`"
    assert "value" not in names, "a claim's value is bounded (`value_low`/`value_high`), never a bare `value`"
    assert "period" not in names, "a claim's period is `horizon_period` -- the future, not a realized period"
