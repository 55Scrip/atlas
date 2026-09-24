"""Project Enumeration reads ActionEvidence and filing text, and nothing reads it.

    ActionEvidence ────────┐
                           ├──> ProjectEnumeration ──> NOTHING
    Held source paragraphs ┘

The one-way seam is the point: ActionEvidence decides what counts as an observed
action without knowing that lists exist, which is what makes it independent
evidence here. If it ever imported this layer the independence would be gone.

Imports are read with the AST and joined -- ``from atlas.x import y`` records
``atlas.x`` as the module, and only joining the name reveals ``atlas.x.y``.
A prefix check without the join once let a real import through (Sprint 14).
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "atlas" / "analysis_engine" / "project_enumeration"
TARGET = "atlas.analysis_engine.project_enumeration"
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


def test_it_reads_action_evidence_and_nothing_else_from_atlas():
    for path in PACKAGE.glob("*.py"):
        foreign = {m for m in _imports(path)
                   if _under(m, "atlas") and not _under(m, TARGET) and not _under(m, ACTION)}
        assert not foreign, f"{path.name} imports {sorted(foreign)}"


#: The one permitted consumer: Project Relationship (Sprint 35), which restates a
#: validated enumeration as evidence about its own entries and is itself consumed
#: by nothing. A closed list of named modules, never a prefix.
PERMITTED_CONSUMERS = ("atlas.analysis_engine.project_relationship",)


def test_only_the_named_consumer_imports_it():
    offenders = []
    for path in (ROOT / "atlas").rglob("*.py"):
        if PACKAGE in path.parents or path.parent == PACKAGE:
            continue
        module = str(path.relative_to(ROOT)).replace("/", ".").removesuffix(".py")
        if any(_under(module, c) for c in PERMITTED_CONSUMERS):
            continue
        if any(_under(m, TARGET) for m in _imports(path)):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, offenders


def test_the_seam_runs_one_way():
    """ActionEvidence must not learn about enumerations. Its independence is the
    whole reason it can tell a list of projects from a list of risks."""
    for path in (ROOT / "atlas" / Path(ACTION.removeprefix("atlas.").replace(".", "/"))).rglob("*.py"):
        assert not any(_under(m, TARGET) for m in _imports(path)), path


def test_the_other_neighbouring_shadow_models_do_not_consume_it():
    for neighbour in ("project_reference", "claim_action_comparison", "strategy_claim"):
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


#: Issuers, places and plants the benchmark puts in front of the rules, plus the
#: topical words a list classifier would reach for. A list is read by structure
#: and by independent action evidence, never by what it appears to be about.
_NAMES = ("micron", "mu", "vistra", "vst", "verizon", "vz", "salesforce", "crm", "google", "googl",
          "nvidia", "nvda", "applied materials", "amat", "shopify", "shop", "tesla", "tsla",
          "singapore", "boise", "idaho", "new york", "clay", "japan", "taiwan", "india",
          "gujarat", "hiroshima", "west texas", "comanche", "baldwin", "coffeen", "coleto creek",
          "miami fort", "energy harbor", "lotus", "cogentrix", "pjm", "ercot", "nand", "hbm",
          "risk", "risks", "factor", "factors", "financing", "audit", "forward-looking",
          "capital expenditures", "project", "projects", "acquisition")


def _executable_strings(path: Path) -> list[str]:
    """Every string the module could act on. A string standing alone as a
    statement is documentation: it is never evaluated into behaviour."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    documentation = {id(node.value) for node in ast.walk(tree)
                     if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                     and isinstance(node.value.value, str)}
    # ``__all__`` lists the package's own exported names. They are identifiers
    # written as strings, not words any rule matches against.
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


def test_no_identity_or_distinctness_is_defined_anywhere():
    banned = ("same", "not_same", "identi", "equal", "match", "resolve", "alias", "canonical",
              "distinct_project", "different", "transitive", "closure")
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = [n.name for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        names += [t.id for n in ast.walk(tree) if isinstance(n, ast.Assign)
                  for t in n.targets if isinstance(t, ast.Name)]
        assert not [n for n in names if any(w in n.lower() for w in banned)], (path.name, names)
