"""Strategy Claim is a decision-shadow read model: it imports nothing from
Atlas but itself -- not even Action Evidence, whose records it must never use
to decide what a claim says -- nothing in the decision path imports it, it
reads no clock, persists nothing, and its rules name no company.

Imports are read with the AST and joined: ``from atlas.x import y`` records
``atlas.x``, and only joining the name reveals ``atlas.x.y``. A prefix check
without the join once let a real import through (Sprint 14).
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "atlas" / "analysis_engine" / "strategy_claim"
TARGET = "atlas.analysis_engine.strategy_claim"
ACTION_EVIDENCE = "atlas.analysis_engine.action_evidence"


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


def test_the_package_imports_nothing_from_atlas_but_itself():
    for path in PACKAGE.glob("*.py"):
        foreign = {m for m in _imports(path) if _under(m, "atlas") and not _under(m, TARGET)}
        assert not foreign, f"{path.name} imports {sorted(foreign)}"


def test_a_claim_is_never_defined_by_the_action_evidence_that_would_test_it():
    # If the claim reader could see observed actions, a claim would be
    # confirmed by construction and the comparison would prove nothing.
    for path in PACKAGE.glob("*.py"):
        assert not any(_under(m, ACTION_EVIDENCE) for m in _imports(path)), path.name


def test_action_evidence_does_not_import_strategy_claim_either():
    for path in (ROOT / "atlas" / "analysis_engine" / "action_evidence").glob("*.py"):
        assert not any(_under(m, TARGET) for m in _imports(path)), path.name


#: The one permitted consumer: Claim-Action Comparison (Sprint 25), itself a
#: decision-shadow read model that nothing consumes in turn. The guarantee that
#: matters -- no decision layer reads this -- is enforced unchanged below.
COMPARATOR = "atlas.analysis_engine.claim_action_comparison"


def test_no_production_module_imports_strategy_claim():
    offenders = []
    for path in (ROOT / "atlas").rglob("*.py"):
        if path.parent == PACKAGE:
            continue
        if _under(str(path.relative_to(ROOT)).replace('/', '.').removesuffix('.py'), COMPARATOR):
            continue
        if any(_under(m, TARGET) for m in _imports(path)):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, offenders


def test_the_named_decision_layers_do_not_import_it():
    layers = ["strategy", "strategy_salience", "strategy_corroboration", "strategy_attribution",
              "forward_claims", "entity_identity", "action_evidence"]
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
        assert not any(_under(m, p) for m in mods for p in ("sqlalchemy", "sqlite3", "atlas.database")), path.name


#: Issuers, counterparties, facilities and programmes the benchmark names. A
#: rule mentioning any of them is a rule fitted to one passage.
_NAMES = ("vistra", "vst", "amazon", "aws", "meta", "comanche", "micron", "mu", "pjm", "singapore",
          "west texas", "arizona", "new york", "chips", "tesla", "tsla", "waymo", "google", "googl",
          "alphabet", "deepmind", "gemini", "salesforce", "shopify", "merchants", "applied materials",
          "amat", "nand", "tpu", "permian", "other bets")


def _executable_strings(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                docstrings.add(id(body[0].value))
    return [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings]


def test_no_rule_names_a_company_facility_or_programme():
    for path in PACKAGE.glob("*.py"):
        for s in _executable_strings(path):
            low = s.lower()
            for name in _NAMES:
                assert not re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", low), (
                    f"{path.name}: executable string {s[:60]!r} names {name!r}")
