"""Action Evidence is a decision-shadow read model: it imports nothing from
Atlas beyond itself, nothing in the decision path imports it, and its
rules name no company.

Imports are read with the AST and joined -- ``from atlas.x import y``
records ``atlas.x`` as the module, and only joining the name reveals
``atlas.x.y``. A prefix check without the join once let a real import
through (Sprint 14)."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "atlas" / "analysis_engine" / "action_evidence"
TARGET = "atlas.analysis_engine.action_evidence"


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


#: The permitted consumers: three decision-shadow read models, each of which
#: nothing consumes in turn -- Claim-Action Comparison (Sprint 25), Project
#: Reference (Sprint 31) and Project Enumeration (Sprint 34). The last reads
#: actions to tell a filing's list of projects from its list of risks, and the
#: seam runs one way: this package must never learn that lists exist. The
#: guarantee that matters -- no decision layer reads this -- is enforced
#: unchanged below.
SHADOW_CONSUMERS = ("atlas.analysis_engine.claim_action_comparison",
                    "atlas.analysis_engine.project_reference",
                    "atlas.analysis_engine.project_enumeration")


def test_no_production_module_imports_action_evidence():
    offenders = []
    for path in (ROOT / "atlas").rglob("*.py"):
        if PACKAGE in path.parents or path.parent == PACKAGE:
            continue
        module = str(path.relative_to(ROOT)).replace('/', '.').removesuffix('.py')
        if any(_under(module, consumer) for consumer in SHADOW_CONSUMERS):
            continue
        if any(_under(m, TARGET) for m in _imports(path)):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, offenders


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


#: Issuers, counterparties, facilities and products the benchmark names. A rule
#: that mentions any of them is a rule fitted to a passage.
_NAMES = ("vistra", "vst", "amazon", "aws", "meta", "comanche", "micron", "mu", "crm", "ma",
          "singapore", "boise", "idaho", "new york", "hbm", "nand",
          "shop", "tesla", "tsla", "waymo",
          "lotus", "google", "googl", "alphabet", "mastercard", "salesforce", "shopify", "optimus",
          "gemini", "applied materials", "amat", "department of commerce", "energy harbor", "cogentrix")


def _executable_strings(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                docstrings.add(id(body[0].value))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            # a bare string used as an attribute docstring is also documentation
            out.append(node.value)
    return out


def test_no_rule_names_a_company_facility_or_product():
    import re
    for path in PACKAGE.glob("*.py"):
        for s in _executable_strings(path):
            low = s.lower()
            for name in _NAMES:
                assert not re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", low), (
                    f"{path.name}: executable string {s[:60]!r} names {name!r}")
