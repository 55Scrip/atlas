"""Dimensional evidence is stored and read by nothing yet.

Sprint 11 preserves evidence Atlas was discarding. It does not reason
from it. The four decision-intelligence layers -- Strategy Intelligence,
Salience, Corroboration, Attribution -- must not consume dimensional
facts until a sprint has argued for how, because the first consumer will
set the semantics for every one after it, and the hardest question is
still unanswered: a segment is not an initiative.

The consolidated path is the other boundary. Financial Risk, valuation
and the Investment Case read consolidated facts today, and a dimensioned
fact reaching them would put a business unit's number where a company's
belongs.
"""
from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_PRODUCTION_ROOT = _REPO_ROOT / "atlas"
_READER = "atlas.business_data_providers.esef.dimensions"
_STORE = "atlas.core.infrastructure.persistence.dimensional_fact"


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add(node.module or "")
    return modules


def _is_or_under(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(prefix + ".")


def test_no_decision_intelligence_layer_consumes_dimensional_evidence():
    layers = (
        "analysis_engine/strategy",
        "analysis_engine/strategy_salience",
        "analysis_engine/strategy_corroboration",
        "analysis_engine/strategy_attribution",
    )
    for layer in layers:
        for path in sorted((_PRODUCTION_ROOT / layer).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            for module in _imported_modules(path):
                assert not _is_or_under(module, _READER), f"{layer} reads the dimensional reader"
                assert not _is_or_under(module, _STORE), f"{layer} reads the dimensional store"


def test_no_deciding_module_consumes_dimensional_evidence():
    protected = (
        "analysis_engine/recommendation.py",
        "analysis_engine/recommendation_conviction.py",
        "analysis_engine/direction_selector.py",
        "analysis_engine/conviction.py",
        "analysis_engine/business.py",
        "analysis_engine/pipeline.py",
        "analysis_engine/valuation",
        "analysis_engine/risk",
        "analysis_engine/business_facts",
        "alpha/portfolio_fit",
    )
    for relative in protected:
        target = _PRODUCTION_ROOT / relative
        files = sorted(target.rglob("*.py")) if target.is_dir() else [target]
        for path in files:
            if not path.exists() or "__pycache__" in path.parts:
                continue
            for module in _imported_modules(path):
                assert not _is_or_under(module, _READER), f"{relative} reads dimensional facts"
                assert not _is_or_under(module, _STORE), f"{relative} reads the dimensional store"


def test_the_consolidated_normalizer_does_not_import_the_dimensional_reader():
    """The two readers are complements and stay independent: the
    consolidated one must keep working exactly as it did, and it does
    that by not knowing this module exists."""
    normalization = _PRODUCTION_ROOT / "business_data_providers" / "esef" / "normalization.py"
    for module in _imported_modules(normalization):
        assert not _is_or_under(module, _READER)


def test_the_dimensional_reader_fetches_nothing():
    """It reads a parsed document. No provider, no network, no cache
    path -- the facts were downloaded once, by the pipeline that already
    exists, and this module only stops throwing them away."""
    reader = _PRODUCTION_ROOT / "business_data_providers" / "esef" / "dimensions.py"
    forbidden = ("requests", "urllib", "httpx", "atlas.business_data_providers.esef.source")
    for module in _imported_modules(reader):
        assert not any(_is_or_under(module, prefix) for prefix in forbidden), module
