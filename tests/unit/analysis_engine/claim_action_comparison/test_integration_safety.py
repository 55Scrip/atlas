"""Claim-Action Comparison is a decision-shadow read model.

It consumes the two committed representations -- that is its whole purpose --
but the traffic is one-way: neither extractor may import it, no decision layer
may consume it, it reads no clock and persists nothing. Its rules also name no
company, so nothing is fitted to the benchmark.

Imports are read with the AST and joined: ``from atlas.x import y`` records
``atlas.x``, and only joining the name reveals ``atlas.x.y``.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "atlas" / "analysis_engine" / "claim_action_comparison"
TARGET = "atlas.analysis_engine.claim_action_comparison"
CLAIM = "atlas.analysis_engine.strategy_claim"
ACTION = "atlas.analysis_engine.action_evidence"


def _imports(path: Path) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.add(node.module)
            out |= {f"{node.module}.{a.name}" for a in node.names}
    return out


def _under(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(prefix + ".")


def test_it_imports_only_the_two_read_models_it_compares():
    allowed = (TARGET, CLAIM, ACTION)
    for path in PACKAGE.glob("*.py"):
        foreign = {m for m in _imports(path)
                   if _under(m, "atlas") and not any(_under(m, a) for a in allowed)}
        assert not foreign, f"{path.name} imports {sorted(foreign)}"


def test_neither_extractor_imports_the_comparator():
    for layer in (CLAIM, ACTION):
        pkg = ROOT / Path(layer.replace(".", "/"))
        for path in pkg.glob("*.py"):
            assert not any(_under(m, TARGET) for m in _imports(path)), path


def test_no_production_module_consumes_the_comparator():
    offenders = []
    for path in (ROOT / "atlas").rglob("*.py"):
        if path.parent == PACKAGE:
            continue
        if any(_under(m, TARGET) for m in _imports(path)):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, offenders


def test_no_decision_layer_imports_it():
    layers = ["strategy", "strategy_salience", "strategy_corroboration", "strategy_attribution",
              "strategy_claim", "action_evidence", "forward_claims", "entity_identity"]
    files = ["recommendation.py", "forward_context.py", "valuation"]
    paths = [p for layer in layers for p in (ROOT / "atlas" / "analysis_engine" / layer).rglob("*.py")]
    for f in files:
        target = ROOT / "atlas" / "analysis_engine" / f
        paths += list(target.rglob("*.py")) if target.is_dir() else [target]
    for path in paths:
        assert not any(_under(m, TARGET) for m in _imports(path)), path


def test_no_clock_is_read():
    for path in PACKAGE.glob("*.py"):
        mods = _imports(path)
        assert not any(_under(m, "datetime") or _under(m, "time") for m in mods), path.name


def test_nothing_is_persisted():
    for path in PACKAGE.glob("*.py"):
        mods = _imports(path)
        assert not any(_under(m, p) for m in mods
                       for p in ("sqlalchemy", "sqlite3", "atlas.database")), path.name


def test_the_vocabulary_states_no_causation_success_or_materiality():
    forbidden = ("caused", "because of", "confirms", "confirmed", "validates", "validated",
                 "successful", "success", "on track", "material", "conviction", "score",
                 "confidence")
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                body = getattr(node, "body", [])
                if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                    docstrings.add(id(body[0].value))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
                low = node.value.lower()
                for word in forbidden:
                    assert word not in low, f"{path.name}: {node.value[:50]!r} says {word!r}"


#: Issuers, counterparties, facilities and programmes the benchmark names.
_NAMES = ("vistra", "vst", "amazon", "aws", "meta", "comanche", "micron", "mu", "pjm", "singapore",
          "west texas", "arizona", "new york", "chips", "waymo", "google", "googl", "alphabet",
          "shopify", "shop", "deliverr", "lotus", "cogentrix", "energy harbor", "baldwin", "ppa",
          "ppas", "wiz", "vantage", "idaho", "nand", "tpu", "other bets")


def test_no_rule_names_a_company_place_or_programme():
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                body = getattr(node, "body", [])
                if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                    docstrings.add(id(body[0].value))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
                low = node.value.lower()
                for name in _NAMES:
                    assert not re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", low), (
                        f"{path.name}: executable string {node.value[:60]!r} names {name!r}")
