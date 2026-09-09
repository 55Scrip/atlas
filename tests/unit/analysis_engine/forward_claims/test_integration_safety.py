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


def test_no_production_module_imports_forward_claims() -> None:
    """Stage 1's whole point: claims exist, and nothing consumes them."""
    offending = [
        str(path.relative_to(_REPO_ROOT))
        for path in _production_files_outside_the_package()
        if any(_is_or_is_under(module, _TARGET) for module in _imported_modules(path))
    ]
    assert offending == [], (
        "Forward claims are not connected to any analysis in Stage 1, but these production "
        "modules import them: " + ", ".join(offending)
    )


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
