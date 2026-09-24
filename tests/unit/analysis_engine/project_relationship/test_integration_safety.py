"""Project Relationship sits at the end of the chain and reads filing text
directly, so it imports nothing from Atlas and nothing in Atlas imports it.

    Held source ──> ProjectRelationship ──> NOTHING

Reading paragraphs rather than other read models is deliberate: Sprint 32
showed the relationships a filing declares attach to phrases that never become
a ProjectReference, so an input of ProjectReferences would have missed them.

Imports are read with the AST and joined -- ``from atlas.x import y`` records
``atlas.x`` as the module, and only joining the name reveals ``atlas.x.y``.
A prefix check without the join once let a real import through (Sprint 14).
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "atlas" / "analysis_engine" / "project_relationship"
TARGET = "atlas.analysis_engine.project_relationship"


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


#: The one thing it reads besides itself: Project Enumeration (Sprint 34), which
#: settles whether a list enumerates projects before this layer says anything
#: about its entries. The seam runs one way, and the tests below hold it there.
ENUMERATION = "atlas.analysis_engine.project_enumeration"


def test_the_package_imports_only_itself_and_the_enumeration_seam():
    for path in PACKAGE.glob("*.py"):
        foreign = {m for m in _imports(path) if _under(m, "atlas")
                   and not _under(m, TARGET) and not _under(m, ENUMERATION)}
        assert not foreign, f"{path.name} imports {sorted(foreign)}"


def test_it_does_not_read_what_the_enumeration_seam_reads():
    """Reading ActionEvidence directly would mean re-deciding upstream whether a
    list is about projects. The enumeration record is the answer, and this layer
    consumes the answer rather than the inputs."""
    for path in PACKAGE.glob("*.py"):
        assert not any(_under(m, "atlas.analysis_engine.action_evidence")
                       for m in _imports(path)), path.name


def test_nothing_in_production_imports_it():
    offenders = [str(p.relative_to(ROOT)) for p in (ROOT / "atlas").rglob("*.py")
                 if PACKAGE not in p.parents and p.parent != PACKAGE
                 and any(_under(m, TARGET) for m in _imports(p))]
    assert not offenders, offenders


def test_the_other_shadow_read_models_do_not_consume_it():
    """Project identity is a later question. Until it is answered, neither the
    comparator nor the reference layer may reach for this evidence."""
    for neighbour in ("claim_action_comparison", "project_reference", "strategy_claim",
                      "action_evidence"):
        for path in (ROOT / "atlas" / "analysis_engine" / neighbour).rglob("*.py"):
            assert not any(_under(m, TARGET) for m in _imports(path)), path


def test_the_named_decision_layers_do_not_import_it():
    layers = ["strategy", "strategy_salience", "strategy_corroboration", "strategy_attribution",
              "forward_claims", "entity_identity", "valuation", "portfolio", "risk"]
    files = ["recommendation.py", "forward_context.py"]
    paths = [p for layer in layers for p in (ROOT / "atlas" / "analysis_engine" / layer).rglob("*.py")]
    paths += [ROOT / "atlas" / "analysis_engine" / f for f in files]
    paths += list((ROOT / "atlas" / "alpha" / "investment_case").rglob("*.py"))
    for path in paths:
        assert not any(_under(m, TARGET) for m in _imports(path)), path


def test_no_clock_is_read():
    for path in PACKAGE.glob("*.py"):
        mods = _imports(path)
        assert not any(_under(m, "datetime") or _under(m, "time") for m in mods), path.name


def test_no_similarity_machinery_is_present():
    """Lexical patterns may recognise the source's own syntax. Nothing may
    score how alike two phrases are."""
    banned = ("difflib", "Levenshtein", "editdistance", "numpy", "sklearn", "scipy",
              "sentence_transformers", "openai", "anthropic")
    for path in PACKAGE.glob("*.py"):
        assert not (_imports(path) & set(banned)), path.name
        text = path.read_text(encoding="utf-8")
        for word in ("similarity", "cosine", "embedding", "edit_distance", "token_overlap",
                     "SequenceMatcher", "fuzz"):
            assert word not in text, f"{path.name} mentions {word!r}"


#: Issuers, places and named plants the benchmark puts in front of the rules.
_NAMES = ("micron", "mu", "vistra", "vst", "verizon", "vz", "tesla", "tsla", "mastercard",
          "nand", "hbm", "dram", "singapore", "boise", "idaho", "new york", "clay", "japan",
          "taiwan", "india", "gujarat", "hiroshima", "west texas", "permian", "comanche",
          "baldwin", "coffeen", "kincaid", "martin lake", "moss landing", "miami fort", "perry",
          "davis-besse", "beaver valley", "energy harbor", "pjm", "ercot", "chips")


def _executable_strings(path: Path) -> list[str]:
    """Every string the module could act on. A string standing alone as a
    statement is documentation: it is never evaluated into behaviour."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    documentation = {id(node.value) for node in ast.walk(tree)
                     if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                     and isinstance(node.value.value, str)}
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


def test_no_identity_or_closure_is_defined_anywhere_in_the_package():
    banned = ("same", "not_same", "identi", "equal", "match", "resolve", "alias", "canonical",
              "transitive", "closure")
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = [n.name for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        names += [t.id for n in ast.walk(tree) if isinstance(n, ast.Assign)
                  for t in n.targets if isinstance(t, ast.Name)]
        assert not [n for n in names if any(w in n.lower() for w in banned)], (path.name, names)


def test_the_enumeration_seam_has_no_return_path():
    """The dependency must not close into a cycle. Project Enumeration decides
    whether a list is about projects; this layer reads that decision, and the
    decision must never depend on what is read from it."""
    for path in (ROOT / Path(ENUMERATION.replace(".", "/"))).rglob("*.py"):
        assert not any(_under(m, TARGET) for m in _imports(path)), path
