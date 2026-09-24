"""Structural Scope reads filing paragraphs and nothing reads it.

    Held source ──> StructuralScope ──> NOTHING

It imports nothing from Atlas at all. Scope is a fact about a document's
layout, so it needs no representation of what the document is about -- and
needing none is the evidence that it is not quietly classifying anything.

Imports are read with the AST and joined -- ``from atlas.x import y`` records
``atlas.x`` as the module, and only joining the name reveals ``atlas.x.y``.
A prefix check without the join once let a real import through (Sprint 14).
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "atlas" / "analysis_engine" / "structural_scope"
TARGET = "atlas.analysis_engine.structural_scope"


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


def test_nothing_in_production_imports_it():
    offenders = [str(p.relative_to(ROOT)) for p in (ROOT / "atlas").rglob("*.py")
                 if PACKAGE not in p.parents and p.parent != PACKAGE
                 and any(_under(m, TARGET) for m in _imports(p))]
    assert not offenders, offenders


def test_the_evidence_layers_do_not_consume_it():
    """Scope is representation, and integrating it is a separate question from
    whether it can be represented at all."""
    for neighbour in ("project_relationship", "project_enumeration", "project_reference",
                      "action_evidence", "strategy_claim", "claim_action_comparison"):
        for path in (ROOT / "atlas" / "analysis_engine" / neighbour).rglob("*.py"):
            assert not any(_under(m, TARGET) for m in _imports(path)), path


def test_the_named_decision_layers_do_not_import_it():
    layers = ["strategy", "strategy_salience", "strategy_corroboration", "strategy_attribution",
              "forward_claims", "entity_identity", "valuation", "portfolio", "risk", "business_data"]
    paths = [p for layer in layers for p in (ROOT / "atlas" / "analysis_engine" / layer).rglob("*.py")]
    paths += [ROOT / "atlas" / "analysis_engine" / f
              for f in ("recommendation.py", "forward_context.py")]
    paths += list((ROOT / "atlas" / "alpha" / "investment_case").rglob("*.py"))
    paths += list((ROOT / "atlas" / "alpha" / "portfolio").rglob("*.py"))
    for path in paths:
        assert not any(_under(m, TARGET) for m in _imports(path)), path


def test_no_clock_is_read():
    for path in PACKAGE.glob("*.py"):
        mods = _imports(path)
        assert not any(_under(m, "datetime") or _under(m, "time") for m in mods), path.name


def test_no_similarity_machinery_is_present():
    banned = ("difflib", "Levenshtein", "editdistance", "numpy", "sklearn", "scipy",
              "sentence_transformers", "openai", "anthropic")
    for path in PACKAGE.glob("*.py"):
        assert not (_imports(path) & set(banned)), path.name
        text = path.read_text(encoding="utf-8")
        for word in ("similarity", "cosine", "embedding", "edit_distance", "token_overlap",
                     "SequenceMatcher", "fuzz"):
            assert word not in text, f"{path.name} mentions {word!r}"


#: Issuers and places the falsification set puts in front of the rules, plus the
#: words a geographic or topical reading would need. Scope is layout: the rules
#: must work as well on "Region Foo" and "Site Bar".
_NAMES = ("micron", "mu", "vistra", "vst", "salesforce", "crm", "google", "googl", "mastercard",
          "applied materials", "amat", "shopify", "shop", "tesla", "tsla", "nvidia", "nvda",
          "verizon", "vz", "singapore", "boise", "idaho", "new york", "clay", "japan", "taiwan",
          "india", "gujarat", "hiroshima", "united states", "u.s.", "outside", "domestic",
          "international", "foreign", "country", "region", "fab", "plant", "facility", "project")


def _executable_strings(path: Path) -> list[str]:
    """Every string the module could act on. A string standing alone as a
    statement is documentation; ``__all__`` lists the package's own exports."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    documentation = {id(node.value) for node in ast.walk(tree)
                     if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                     and isinstance(node.value.value, str)}
    exported = {id(v) for node in ast.walk(tree) if isinstance(node, ast.Assign)
                for t in node.targets if isinstance(t, ast.Name) and t.id == "__all__"
                for v in ast.walk(node.value) if isinstance(v, ast.Constant)}
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and id(node) not in documentation and id(node) not in exported]


def test_no_rule_names_an_issuer_a_place_or_a_topic():
    import re
    for path in PACKAGE.glob("*.py"):
        for s in _executable_strings(path):
            low = s.lower()
            for name in _NAMES:
                assert not re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", low), (
                    f"{path.name}: executable string {s[:60]!r} names {name!r}")


def test_nothing_in_the_package_is_named_for_meaning():
    banned = ("same", "not_same", "identi", "equal", "match", "resolve", "alias", "canonical",
              "project", "geograph", "country", "semantic", "topic", "outside", "domestic")
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = [n.name for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        names += [t.id for n in ast.walk(tree) if isinstance(n, ast.Assign)
                  for t in n.targets if isinstance(t, ast.Name)]
        assert not [n for n in names if any(w in n.lower() for w in banned)], (path.name, names)
