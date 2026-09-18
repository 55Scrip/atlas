"""SEC filing evidence is read by nothing yet.

Sprint 12 fetches and preserves what Atlas already knew where to find.
It does not reason from it, and it does not change what CompanyFacts
gives the engines today. Three boundaries hold that:

The four decision-intelligence layers -- Strategy Intelligence,
Salience, Corroboration, Attribution -- must not consume filing
evidence until a sprint has argued for how. VST's 10-K names Comanche
Peak and Moss Landing 83 times between them, which is exactly the
evidence Strategic Action Attribution was starved of, and exactly why
the first consumer must be designed rather than discovered.

The deciding modules must not consume it either. Financial Risk,
valuation and the Investment Case read consolidated CompanyFacts
today, and a segment's number reaching them would be a company's
number that is wrong.

CompanyFacts itself must stay untouched. It remains the owner of the
consolidated figures production uses; this layer is additive.
"""
from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_PRODUCTION_ROOT = _REPO_ROOT / "atlas"
_READER = "atlas.business_data_providers.sec_filing"
_STORE = "atlas.core.infrastructure.persistence.sec_filing"
_DIMENSIONAL_STORE = "atlas.core.infrastructure.persistence.dimensional_fact"


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


def test_no_decision_intelligence_layer_consumes_filing_evidence():
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
                assert not _is_or_under(module, _READER), f"{layer} reads SEC filing facts"
                assert not _is_or_under(module, _STORE), f"{layer} reads the filing store"
                assert not _is_or_under(module, _DIMENSIONAL_STORE), f"{layer} reads the fact store"


def test_no_deciding_module_consumes_filing_evidence():
    protected = (
        "analysis_engine/recommendation.py",
        "analysis_engine/conviction.py",
        "analysis_engine/business.py",
        "analysis_engine/pipeline.py",
        "analysis_engine/valuation",
        "analysis_engine/risk",
        "analysis_engine/business_facts",
        "alpha/portfolio_fit",
        "alpha/investment_case/service.py",
    )
    for relative in protected:
        target = _PRODUCTION_ROOT / relative
        files = sorted(target.rglob("*.py")) if target.is_dir() else [target]
        for path in files:
            if not path.exists() or "__pycache__" in path.parts:
                continue
            for module in _imported_modules(path):
                assert not _is_or_under(module, _READER), f"{relative} reads SEC filing facts"
                assert not _is_or_under(module, _STORE), f"{relative} reads the filing store"


def test_the_companyfacts_provider_does_not_import_the_filing_reader():
    """CompanyFacts stays the owner of consolidated evidence, and it
    does that by not knowing this package exists."""
    for name in ("sec_edgar.py", "sec_edgar_identity.py", "http.py"):
        provider = _PRODUCTION_ROOT / "business_data_providers" / name
        for module in _imported_modules(provider):
            assert not _is_or_under(module, _READER), f"{name} imports the filing reader"
            assert not _is_or_under(module, _STORE), f"{name} imports the filing store"


def test_the_filing_reader_fetches_nothing_itself():
    """Parsing is separate from fetching on purpose. Acquisition is a
    background, batch operation with a fair-access budget; this module
    turns bytes into facts and must never be able to reach the network
    from a request path."""
    forbidden = ("requests", "urllib", "httpx", "atlas.business_data_providers.http")
    for path in sorted((_PRODUCTION_ROOT / "business_data_providers" / "sec_filings").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        for module in _imported_modules(path):
            assert not any(_is_or_under(module, prefix) for prefix in forbidden), f"{path.name}: {module}"


def test_the_dimensional_contract_is_provider_neutral():
    """The contract both readers share must not know about either
    taxonomy. If it grows an ESEF or SEC import, the next provider will
    inherit a dependency on the previous one's vocabulary."""
    contract = _PRODUCTION_ROOT / "business_data_providers" / "dimensional_evidence.py"
    for module in _imported_modules(contract):
        assert not module.startswith("atlas."), f"the shared contract imports {module}"
