"""The boundary that makes Strategy Intelligence safe to keep.

Strategy Intelligence reads management's stated intentions. Those are the
most persuasive and least verified sentences a company produces: an
executive describing what they are trying to build is, by construction,
making a case. Letting that reach anything that decides would give
Atlas's recommendation a channel through which a company could talk its
way to a better rating -- the precise failure `forward_claims` was
firewalled against, arriving through a different door.

So this package is inert. Unlike `forward_claims` it has **no sanctioned
seam at all**: there is no strategy equivalent of `forward_context`,
because the sprint that built this layer was decision-shadow only.

Three *consumers* are sanctioned, each added by a deliberate edit here:

- `strategy_salience` reads this graph to say which parts of it a
  company's calls appear to be organised around;
- `strategy_corroboration` reads it to ask what the company's reported
  figures did about those parts;
- `strategy_attribution` reads it to ask whether any evidence ties an
  action to one part rather than to the company as a whole.

All three are allowed because none is a seam: they decide nothing, and
each is inert under its own firewall. The shape is deliberately a fan,
not a chain. Corroboration does not consume salience, so a node need not
be emphasised before Atlas looks for evidence about it; attribution
consumes neither, because whether an action *happened* and what it was
*for* are separate questions and making one a precondition of the other
would answer neither. Emphasis is management's to control; eligibility
for the other two must not be.

The exemption is narrowed by `test_the_sanctioned_consumers_are_inert`
below, which asserts that nothing in production imports either consumer.
Without it they would be routes rather than readers, and this rule would
have been softened rather than extended.

Scanned over `atlas/` only, deliberately: this asks a question about
production source, and the repository root also contains unrelated
physical worktree copies from other sessions whose files would answer it
wrongly.
"""
from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_PRODUCTION_ROOT = _REPO_ROOT / "atlas"
_PACKAGE_DIR = _PRODUCTION_ROOT / "analysis_engine" / "strategy"
_TARGET = "atlas.analysis_engine.strategy"

#: The sanctioned consumers -- readers, never seams. Each decides
#: nothing and each is itself inert; see the module docstring.
_SANCTIONED_CONSUMERS = (
    "atlas/analysis_engine/strategy_salience",
    "atlas/analysis_engine/strategy_corroboration",
    "atlas/analysis_engine/strategy_attribution",
)
_SANCTIONED_CONSUMER_MODULES = (
    "atlas.analysis_engine.strategy_salience",
    "atlas.analysis_engine.strategy_corroboration",
    "atlas.analysis_engine.strategy_attribution",
)


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


def test_no_production_module_imports_strategy_intelligence():
    offenders = [
        str(path.relative_to(_REPO_ROOT))
        for path in _production_files_outside_the_package()
        if any(_is_or_is_under(module, _TARGET) for module in _imported_modules(path))
        and not str(path.relative_to(_REPO_ROOT)).startswith(_SANCTIONED_CONSUMERS)
    ]
    assert offenders == [], (
        "Strategy Intelligence is decision-shadow only. A production importer means "
        f"management's stated intentions can now reach something in Atlas: {offenders}"
    )


def test_the_sanctioned_consumers_are_inert():
    """The sanctioned consumers may read the strategy graph. Nothing may
    read them.

    This is what keeps the exemptions above extensions of the rule
    rather than holes in it: a deciding module able to import either
    consumer would reach the strategy graph through it, and the firewall
    would have been satisfied on a technicality."""
    for consumer, module_name in zip(_SANCTIONED_CONSUMERS, _SANCTIONED_CONSUMER_MODULES):
        offenders = [
            str(path.relative_to(_REPO_ROOT))
            for path in _PRODUCTION_ROOT.rglob("*.py")
            if "__pycache__" not in path.parts
            and not str(path.relative_to(_REPO_ROOT)).startswith(consumer)
            and any(_is_or_is_under(module, module_name) for module in _imported_modules(path))
        ]
        assert offenders == [], (
            f"{module_name} is a reader of the strategy graph, not a route into it: {offenders}"
        )


def test_attribution_depends_on_neither_salience_nor_corroboration():
    """Attribution reads the strategy graph and the records, and nothing
    else in this family.

    Whether an action happened and what it was for are separate
    questions. Making corroboration a precondition would mean Atlas only
    asks what spending was for once it has already seen spending move --
    and the most useful attribution in the corpus, a stated intent to
    invest in a named facility, has no observed action behind it at
    all."""
    attribution = _PRODUCTION_ROOT / "analysis_engine" / "strategy_attribution"
    for path in sorted(attribution.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        for sibling in ("atlas.analysis_engine.strategy_salience",
                        "atlas.analysis_engine.strategy_corroboration"):
            assert not any(
                _is_or_is_under(module, sibling) for module in _imported_modules(path)
            ), f"{path.name} imports {sibling}"


def test_corroboration_does_not_depend_on_salience():
    """A node does not have to be emphasised before Atlas will look for
    evidence about it.

    Salience measures what management chooses to stress. Making it a
    gate on corroboration would mean the company decided which of its
    own strategies Atlas would check -- the exact circularity this layer
    exists to break. The two consumers are a fan out of the strategy
    graph, not a chain."""
    corroboration = _PRODUCTION_ROOT / "analysis_engine" / "strategy_corroboration"
    for path in sorted(corroboration.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        assert not any(
            _is_or_is_under(module, "atlas.analysis_engine.strategy_salience")
            for module in _imported_modules(path)
        ), f"{path.name} imports salience"


def test_strategy_never_reaches_recommendation_conviction_or_the_engines():
    """Named individually as well as covered by the sweep above, so a
    failure says which decision this would have contaminated."""
    protected = (
        "atlas/analysis_engine/recommendation.py",
        "atlas/analysis_engine/recommendation_conviction.py",
        "atlas/analysis_engine/direction_selector.py",
        "atlas/analysis_engine/conviction.py",
        "atlas/analysis_engine/reasoning.py",
        "atlas/analysis_engine/business.py",
        "atlas/analysis_engine/valuation",
        "atlas/analysis_engine/risk",
        "atlas/analysis_engine/pipeline.py",
        "atlas/analysis_engine/forward_context.py",
        "atlas/alpha/portfolio_fit/engine.py",
    )
    for relative in protected:
        path = _REPO_ROOT / relative
        files = sorted(path.rglob("*.py")) if path.is_dir() else [path]
        for file in files:
            if not file.exists() or "__pycache__" in file.parts:
                continue
            assert not any(
                _is_or_is_under(module, _TARGET) for module in _imported_modules(file)
            ), f"{relative} must not be able to see a company's stated intentions"


def test_strategy_does_not_import_a_provider_or_a_database():
    """The layer is a read model over records Atlas already holds. It
    may not fetch, and it may not persist -- a strategy table would be a
    second truth about evidence that already has one."""
    forbidden = ("atlas.providers", "atlas.business_data_providers", "sqlalchemy", "atlas.database")
    for path in sorted(_PACKAGE_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        for module in _imported_modules(path):
            assert not any(_is_or_is_under(module, prefix) for prefix in forbidden), (
                f"{path.name} imports {module}: Strategy Intelligence neither fetches nor stores"
            )


def test_strategy_does_not_import_forward_claims_interpretation():
    """`forward_claims` owns guidance. The strategy layer may name a
    guidance-shaped sentence and refuse it, which needs no import; it
    may not build a second interpretation path into the same evidence.
    `forward_context` is the one seam that interprets forward evidence
    for anything downstream, and Strategy Intelligence is not a second
    one."""
    for path in sorted(_PACKAGE_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        for module in _imported_modules(path):
            assert not _is_or_is_under(module, "atlas.analysis_engine.forward_claims"), (
                f"{path.name} imports {module}"
            )
            assert not _is_or_is_under(module, "atlas.analysis_engine.forward_context"), (
                f"{path.name} imports {module}"
            )


def test_no_ticker_specific_rule_exists_in_the_package():
    """META and VST are benchmarks, not templates. A literal ticker in a
    production rule would mean Atlas learned one company rather than one
    method -- and would pass every benchmark while generalising to
    nothing."""
    tickers = (
        "META", "VST", "GOOGL", "AMAT", "NVDA", "AMZN", "MSFT", "TSLA",
        "MU", "AMD", "ASML", "CRM", "SHOP", "BRK.B",
    )
    for path in sorted(_PACKAGE_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert node.value not in tickers, (
                    f"{path.name} line {node.lineno} contains the literal ticker {node.value!r}"
                )
