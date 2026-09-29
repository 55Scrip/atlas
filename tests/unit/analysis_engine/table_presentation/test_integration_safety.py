"""Table Presentation reads a parsed table and nothing reads it.

    FilingTable ──> TablePresentation ──> NOTHING

The evidence is that a table's shape shows it presents no data. A consumer would
turn that into "so skip it", which is a different and unearned claim: a cover page
and a page header are part of the filing, and 12 of the tables a human reads as
layout get no evidence at all because the measured residue holds both classes.

Imports are read with the AST and joined -- ``from atlas.x import y`` records
``atlas.x`` as the module, and only joining the name reveals ``atlas.x.y``.
A prefix check without the join once let a real import through (Sprint 14).
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "atlas" / "analysis_engine" / "table_presentation"
TARGET = "atlas.analysis_engine.table_presentation"

#: Its sibling from Sprint 40, which must stay independent in BOTH directions.
TABLE_INTRODUCTION = "atlas.analysis_engine.table_introduction"


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


def test_the_package_imports_only_itself():
    for path in PACKAGE.glob("*.py"):
        foreign = {m for m in _imports(path) if _under(m, "atlas") and not _under(m, TARGET)}
        assert not foreign, f"{path.name} imports {sorted(foreign)}"


def test_nothing_in_production_imports_it():
    offenders = [str(p.relative_to(ROOT)) for p in (ROOT / "atlas").rglob("*.py")
                 if PACKAGE not in p.parents and p.parent != PACKAGE
                 and any(_under(m, TARGET) for m in _imports(p))]
    assert not offenders, offenders


def test_it_and_table_introduction_stay_independent():
    """Sprint 40 emitted 3 ambiguous introductions whose targets this layer now
    reaches. Joining them up would decide, in passing, that an introduction to a
    non-data table means something different -- which nothing has measured."""
    for path in PACKAGE.glob("*.py"):
        assert not any(_under(m, TABLE_INTRODUCTION) for m in _imports(path)), path.name
    for path in (ROOT / Path(TABLE_INTRODUCTION.replace(".", "/"))).rglob("*.py"):
        assert not any(_under(m, TARGET) for m in _imports(path)), path


def test_no_shadow_read_model_consumes_it():
    for neighbour in ("structural_scope", "project_enumeration", "project_relationship",
                      "project_reference", "action_evidence", "strategy_claim",
                      "claim_action_comparison", "table_introduction"):
        base = ROOT / "atlas" / "analysis_engine" / neighbour
        for path in base.rglob("*.py"):
            assert not any(_under(m, TARGET) for m in _imports(path)), path


def test_no_decision_layer_consumes_it():
    layers = ["strategy", "strategy_salience", "strategy_corroboration", "strategy_attribution",
              "forward_claims", "entity_identity", "valuation", "portfolio", "risk"]
    files = ["recommendation.py", "forward_context.py"]
    paths = [p for layer in layers for p in (ROOT / "atlas" / "analysis_engine" / layer).rglob("*.py")]
    paths += [ROOT / "atlas" / "analysis_engine" / f for f in files]
    paths += list((ROOT / "atlas" / "alpha" / "investment_case").rglob("*.py"))
    paths += list((ROOT / "atlas" / "alpha" / "portfolio").rglob("*.py"))
    for path in paths:
        if not path.exists():
            continue
        assert not any(_under(m, TARGET) for m in _imports(path)), path


def test_the_filing_parser_does_not_depend_back_on_it():
    parser = ROOT / "atlas/alpha/investment_case/filing_content_intelligence.py"
    assert not any(_under(m, TARGET) for m in _imports(parser))


def test_no_clock_is_read():
    for path in PACKAGE.glob("*.py"):
        mods = _imports(path)
        assert not any(_under(m, "datetime") or _under(m, "time") for m in mods), path.name
        text = path.read_text(encoding="utf-8")
        for word in ("datetime.now", "time.time", "utcnow", "today()"):
            assert word not in text, f"{path.name} mentions {word!r}"


def test_no_similarity_or_model_machinery_is_present():
    banned = ("difflib", "Levenshtein", "editdistance", "numpy", "sklearn", "scipy",
              "sentence_transformers", "openai", "anthropic", "re")
    for path in PACKAGE.glob("*.py"):
        assert not (_imports(path) & set(banned)), path.name
        text = path.read_text(encoding="utf-8")
        for word in ("similarity", "cosine", "embedding", "edit_distance", "token_overlap",
                     "SequenceMatcher", "fuzz"):
            assert word not in text, f"{path.name} mentions {word!r}"


def test_no_second_kind_and_no_continuation_vocabulary():
    """One-sided by construction. A DATA_PRESENTATION member, or a fragment or
    continuation member, would each assert something Sprint 41 refused."""
    from atlas.analysis_engine.table_presentation import TablePresentationKind

    assert [k.value for k in TablePresentationKind] == ["not_a_data_presentation"]
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = [n.name for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        names += [t.id for n in ast.walk(tree) if isinstance(n, ast.Assign)
                  for t in n.targets if isinstance(t, ast.Name)]
        for banned in ("layout", "fragment", "continuation", "merge", "same", "not_same",
                       "identi", "canonical", "confidence", "probability"):
            offenders = [n for n in names if banned in n.lower()]
            assert not offenders, (path.name, banned, offenders)
        #: the affirmative kind, specifically: NOT_A_DATA_PRESENTATION is the one
        #: member and must not be joined by the claim it was measured to refuse.
        affirmative = [n for n in names
                       if "data_presentation" in n.lower() and "not_a_data" not in n.lower()]
        assert not affirmative, (path.name, affirmative)


#: Issuers, places and named plants the benchmark puts in front of the rules.
_NAMES = ("micron", "mu", "vistra", "vst", "verizon", "vz", "tesla", "tsla", "mastercard", "ma",
          "alphabet", "googl", "salesforce", "crm", "shopify", "shop", "nvidia", "nvda",
          "nand", "hbm", "dram", "singapore", "boise", "idaho", "facilities")


def _executable_strings(path: Path) -> list[str]:
    """Every string the module could act on. A string standing alone as a
    statement is documentation: it is never evaluated into behaviour."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    documentation = {id(node.value) for node in ast.walk(tree)
                     if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                     and isinstance(node.value.value, str)}
    documentation |= {id(v) for node in ast.walk(tree)
                      if isinstance(node, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets)
                      for v in ast.walk(node.value) if isinstance(v, ast.Constant)}
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and id(node) not in documentation]


def test_no_rule_names_an_issuer_a_place_or_a_plant():
    import re as _re

    for path in PACKAGE.glob("*.py"):
        for s in _executable_strings(path):
            low = s.lower()
            for name in _NAMES:
                assert not _re.search(r"(?<![a-z])" + _re.escape(name) + r"(?![a-z])", low), (
                    f"{path.name}: executable string {s[:60]!r} names {name!r}")


def test_no_section_or_topic_literal_drives_behaviour():
    for path in PACKAGE.glob("*.py"):
        for s in _executable_strings(path):
            for banned in ("FINANCIAL_STATEMENTS", "BUSINESS", "MDA", "EXHIBITS", "PROPERTIES",
                           "RISK_FACTORS", "revenue", "debt", "asset", "maturit", "segment"):
                assert banned.lower() not in s.lower(), (path.name, s[:60], banned)
