"""Entity representation is read by nothing outside Strategy.

It is additive by construction: the module imports nothing from
`atlas`, nothing imports it, and no node contract changed. That is what
makes "Strategy semantics unchanged" a fact rather than a hope.

The layers below matter for different reasons. Salience counts where
attention goes, and a name repeated in five quarters must not become
five reasons to think it important. Corroboration asks whether an
action happened independently, and preserving what management named is
still management's own account. Attribution has its own standard, and
Sprint 13's channel must keep rejecting what it rejected.
"""
from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_PRODUCTION_ROOT = _REPO_ROOT / "atlas"
_ENTITIES = "atlas.analysis_engine.strategy.entities"


def _imported_modules(path: Path) -> set[str]:
    """Every module this file imports, including the submodule form.

    `from atlas.analysis_engine.strategy import entities` records the
    *parent* as `node.module`, so a check against the full dotted name
    alone misses it -- which is exactly how a consumer would slip in.
    The imported name is joined on so both forms are visible."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            parent = node.module or ""
            modules.add(parent)
            modules.update(f"{parent}.{alias.name}" if parent else alias.name
                           for alias in node.names)
    return modules


def _is_or_under(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(prefix + ".")


def test_no_layer_outside_strategy_consumes_entity_representation():
    for relative in (
        "analysis_engine/strategy_salience",
        "analysis_engine/strategy_corroboration",
        "analysis_engine/strategy_attribution",
        "analysis_engine/recommendation.py",
        "analysis_engine/conviction.py",
        "analysis_engine/business.py",
        "analysis_engine/pipeline.py",
        "analysis_engine/valuation",
        "analysis_engine/risk",
        "alpha/portfolio_fit",
    ):
        target = _PRODUCTION_ROOT / relative
        files = sorted(target.rglob("*.py")) if target.is_dir() else [target]
        for path in files:
            if not path.exists() or "__pycache__" in path.parts:
                continue
            for module in _imported_modules(path):
                assert not _is_or_under(module, _ENTITIES), f"{relative} consumes entity mentions"


def test_entity_representation_reaches_for_nothing():
    """It reads passages it is handed. No filing, no dimensional
    evidence, no store, no provider, no network."""
    module = _PRODUCTION_ROOT / "analysis_engine" / "strategy" / "entities.py"
    for imported in _imported_modules(module):
        assert not imported.startswith("atlas"), imported
        assert imported not in {"httpx", "requests", "urllib"}


def test_the_strategy_node_contract_did_not_change():
    """Entity mentions live beside the node, not inside it. A field on
    `StrategyNode` would change every consumer's serialization and make
    "additive" untrue."""
    from atlas.analysis_engine.strategy.models import StrategyNode

    fields = {f.name for f in StrategyNode.__dataclass_fields__.values()}
    assert not any("entity" in name or "mention" in name for name in fields)


def test_composition_does_not_call_entity_extraction():
    """Nothing in the Strategy package's own pipeline invokes it either,
    so composing a strategy produces byte-identical output."""
    composition = _PRODUCTION_ROOT / "analysis_engine" / "strategy" / "composition.py"
    extraction = _PRODUCTION_ROOT / "analysis_engine" / "strategy" / "extraction.py"
    for path in (composition, extraction):
        for module in _imported_modules(path):
            assert not _is_or_under(module, _ENTITIES), f"{path.name} calls entity extraction"
