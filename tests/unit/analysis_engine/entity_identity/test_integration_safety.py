"""Identity claims are read by nothing.

Proving that two references denote one object is a precondition for a
join, not the join. Attribution keeps its own measure, period and
resolution rules; salience must not count a resolved name as extra
attention; and nothing that decides may see any of it.
"""
from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_PRODUCTION_ROOT = _REPO_ROOT / "atlas"
_IDENTITY = "atlas.analysis_engine.entity_identity"


def _imported_modules(path: Path) -> set[str]:
    """Both import forms. `from atlas.analysis_engine import entity_identity`
    records only the parent, which is how a consumer slips past a naive
    prefix check -- the lesson from the previous sprint's own firewall."""
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


def test_nothing_consumes_identity_resolution():
    offenders = []
    for path in sorted(_PRODUCTION_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts or "entity_identity" in path.parts:
            continue
        if any(_is_or_under(module, _IDENTITY) for module in _imported_modules(path)):
            offenders.append(str(path.relative_to(_REPO_ROOT)))
    assert not offenders, offenders


def test_no_named_layer_consumes_it():
    for relative in (
        "analysis_engine/strategy",
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
                assert not _is_or_under(module, _IDENTITY), f"{relative} consumes identity claims"


def test_identity_resolution_reaches_for_nothing():
    """It is handed references and declared labels. It must not fetch a
    filing, read a store, or reach the network to decide."""
    allowed_roots = {"", "__future__", "re", "dataclasses", "enum"}
    for name in ("contracts.py", "resolution.py"):
        module = _PRODUCTION_ROOT / "analysis_engine" / "entity_identity" / name
        for imported in _imported_modules(module):
            root = imported.split(".")[0]
            assert root in allowed_roots or imported.startswith(_IDENTITY), imported
