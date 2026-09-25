"""Table Introduction reads the parsed filing and nothing reads it.

    FilingContent + source_event_index ──> TableIntroduction ──> NOTHING

The relation is that a paragraph presents the table after it. The moment a
semantic layer consumes that, presentation starts being read as support: "this
sentence introduces this table, therefore the table is evidence for the
sentence." Sprint 39 measured presentation and refused to measure support, and
these tests are what keeps the two apart.

Imports are read with the AST and joined -- ``from atlas.x import y`` records
``atlas.x`` as the module, and only joining the name reveals ``atlas.x.y``.
A prefix check without the join once let a real import through (Sprint 14).
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "atlas" / "analysis_engine" / "table_introduction"
TARGET = "atlas.analysis_engine.table_introduction"

#: The only Atlas module it is allowed to name: the parsed filing it reads.
PERMITTED = "atlas.alpha.investment_case.filing_content_intelligence"


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
        foreign = {m for m in _imports(path) if _under(m, "atlas")
                   and not _under(m, TARGET) and not _under(m, PERMITTED)}
        assert not foreign, f"{path.name} imports {sorted(foreign)}"


def test_it_reads_no_other_evidence_layer():
    """Its input is the parsed document. An input of ActionEvidence or
    StrategyClaim would make a table's introduction depend on what someone
    decided the surrounding prose meant."""
    for path in PACKAGE.glob("*.py"):
        for neighbour in ("structural_scope", "project_enumeration", "project_relationship",
                          "project_reference", "action_evidence", "strategy_claim",
                          "claim_action_comparison", "strategy", "entity_identity"):
            assert not any(_under(m, f"atlas.analysis_engine.{neighbour}") for m in _imports(path)), \
                (path.name, neighbour)


def test_nothing_in_production_imports_it():
    offenders = [str(p.relative_to(ROOT)) for p in (ROOT / "atlas").rglob("*.py")
                 if PACKAGE not in p.parents and p.parent != PACKAGE
                 and any(_under(m, TARGET) for m in _imports(p))]
    assert not offenders, offenders


def test_no_shadow_read_model_consumes_it():
    for neighbour in ("structural_scope", "project_enumeration", "project_relationship",
                      "project_reference", "action_evidence", "strategy_claim",
                      "claim_action_comparison"):
        for path in (ROOT / "atlas" / "analysis_engine" / neighbour).rglob("*.py"):
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
    """The seam runs one way. A cycle here would let the meaning of a relation
    change what the parser produced in the first place."""
    parser = ROOT / Path(PERMITTED.replace(".", "/") + ".py")
    assert not any(_under(m, TARGET) for m in _imports(parser))


def test_no_clock_is_read():
    for path in PACKAGE.glob("*.py"):
        mods = _imports(path)
        assert not any(_under(m, "datetime") or _under(m, "time") for m in mods), path.name
        text = path.read_text(encoding="utf-8")
        for word in ("datetime.now", "time.time", "utcnow", "today()"):
            assert word not in text, f"{path.name} mentions {word!r}"


def test_no_similarity_machinery_is_present():
    banned = ("difflib", "Levenshtein", "editdistance", "numpy", "sklearn", "scipy",
              "sentence_transformers", "openai", "anthropic")
    for path in PACKAGE.glob("*.py"):
        assert not (_imports(path) & set(banned)), path.name
        text = path.read_text(encoding="utf-8")
        for word in ("similarity", "cosine", "embedding", "edit_distance", "token_overlap",
                     "SequenceMatcher", "fuzz"):
            assert word not in text, f"{path.name} mentions {word!r}"


def test_no_identity_or_scope_vocabulary_is_defined():
    banned = ("same", "not_same", "identi", "equal", "match", "resolve", "alias", "canonical",
              "scope", "govern", "support", "evidence_for", "materiality", "causal")
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = [n.name for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        names += [t.id for n in ast.walk(tree) if isinstance(n, ast.Assign)
                  for t in n.targets if isinstance(t, ast.Name)]
        offenders = [n for n in names if any(w in n.lower() for w in banned)]
        assert not offenders, (path.name, offenders)


#: Issuers, places and named plants the benchmark puts in front of the rules.
_NAMES = ("micron", "mu", "vistra", "vst", "verizon", "vz", "tesla", "tsla", "mastercard",
          "nand", "hbm", "dram", "singapore", "boise", "idaho", "new york", "clay", "japan",
          "taiwan", "india", "gujarat", "hiroshima", "facilities", "chips")


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
    import re

    for path in PACKAGE.glob("*.py"):
        for s in _executable_strings(path):
            low = s.lower()
            for name in _NAMES:
                assert not re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", low), (
                    f"{path.name}: executable string {s[:60]!r} names {name!r}")
