"""Project Reference is a derived read model at the end of the chain: it reads
the two accepted representations and nothing reads it.

    StrategyClaim  ─┐
                    ├──> ProjectReference ──> NOTHING
    ActionEvidence ─┘

Imports are read with the AST and joined -- ``from atlas.x import y`` records
``atlas.x`` as the module, and only joining the name reveals ``atlas.x.y``.
A prefix check without the join once let a real import through (Sprint 14).
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "atlas" / "analysis_engine" / "project_reference"
TARGET = "atlas.analysis_engine.project_reference"
CLAIM = "atlas.analysis_engine.strategy_claim"
ACTION = "atlas.analysis_engine.action_evidence"
COMPARATOR = "atlas.analysis_engine.claim_action_comparison"


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


def test_it_reads_only_the_two_representations_it_is_derived_from():
    allowed = (TARGET, CLAIM, ACTION)
    for path in PACKAGE.glob("*.py"):
        foreign = {m for m in _imports(path)
                   if _under(m, "atlas") and not any(_under(m, a) for a in allowed)}
        assert not foreign, f"{path.name} imports {sorted(foreign)}"


def test_nothing_in_production_imports_it():
    offenders = []
    for path in (ROOT / "atlas").rglob("*.py"):
        if PACKAGE in path.parents or path.parent == PACKAGE:
            continue
        if any(_under(m, TARGET) for m in _imports(path)):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, offenders


def test_the_dependency_runs_one_way_only():
    for upstream in (CLAIM, ACTION):
        package = ROOT / Path(upstream.replace(".", "/"))
        for path in package.rglob("*.py"):
            assert not any(_under(m, TARGET) for m in _imports(path)), (
                f"{path} imports the layer derived from it")


def test_the_comparator_does_not_consume_it_yet():
    """Sprint 31 establishes representation only. Project compatibility is a
    later question, and only if the evidence earns it."""
    package = ROOT / Path(COMPARATOR.replace(".", "/"))
    for path in package.rglob("*.py"):
        assert not any(_under(m, TARGET) for m in _imports(path)), path


def test_the_named_decision_layers_do_not_import_it():
    layers = ["strategy", "strategy_salience", "strategy_corroboration", "strategy_attribution",
              "forward_claims", "entity_identity"]
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


#: Issuers, places, products and process names the corpus puts in front of the
#: rules. A rule that mentions any of them is a rule fitted to one passage --
#: and knowing that NAND and HBM are different things is knowledge the source
#: has to supply, not knowledge we are allowed to hold.
_NAMES = ("micron", "mu", "vistra", "vst", "nand", "hbm", "dram",
          "singapore", "boise", "idaho", "new york", "arizona", "japan", "west texas",
          "permian", "comanche", "baldwin", "pjm", "iso-ne", "nyiso", "delaware",
          "pennsylvania", "rhode island", "energy harbor", "lotus", "chips",
          "amat", "applied materials", "crm", "salesforce", "googl", "google", "shop",
          "shopify", "tsla", "tesla", "ma", "mastercard", "meta", "amazon", "aws")


def _executable_strings(path: Path) -> list[str]:
    """Every string the module could act on. A string that stands alone as a
    statement -- a module, class, function or attribute docstring -- is
    documentation: it is never evaluated into behaviour, so a rule cannot hide
    there, and quoting the corpus while explaining a field is not fitting to it."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    documentation = {id(node.value) for node in ast.walk(tree)
                     if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                     and isinstance(node.value.value, str)}
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and id(node) not in documentation]


def test_no_rule_names_an_issuer_a_place_or_a_process():
    import re
    for path in PACKAGE.glob("*.py"):
        for s in _executable_strings(path):
            low = s.lower()
            for name in _NAMES:
                assert not re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", low), (
                    f"{path.name}: executable string {s[:60]!r} names {name!r}")


def test_the_package_offers_no_way_to_ask_whether_two_references_are_the_same():
    """No identity API exists, because no true pair exists to falsify one."""
    import atlas.analysis_engine.project_reference as pkg
    banned = ("same", "match", "identi", "equal", "compare", "resolve", "link", "alias", "canonical")
    offered = [n for n in dir(pkg) if not n.startswith("_")]
    assert not [n for n in offered if any(w in n.lower() for w in banned)], offered
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = [n.name for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        assert not [n for n in names if any(w in n.lower() for w in banned)], (path.name, names)
