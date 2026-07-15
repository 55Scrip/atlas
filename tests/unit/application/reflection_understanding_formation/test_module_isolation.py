"""Structural isolation tests for reflection_understanding_formation (ATLAS-013).

Reuses this codebase's own AST-import-graph precedent
(tests/test_config_sprint195.py::_config_imports()) rather than a
brittle source-text search.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
MODULE_DIR = REPO_ROOT / "atlas" / "core" / "application" / "reflection_understanding_formation"

_FORBIDDEN_MODULE_PREFIXES = (
    "atlas.core.application.pattern_recognition",
    "atlas.core.application.strategy_signature",
    "atlas.core.application.decision_reflection",
    "atlas.core.application.decision_coach",
    "atlas.core.application.decision_timeline",
    # ATLAS-013A-D Chapters 5–6: Formation must never construct, call,
    # or depend on Reflection Comparison or Reflection Exploration —
    # explicit selection may occur through any legitimate means, of
    # which those two are only current examples, not a dependency.
    "atlas.core.application.reflection_comparison",
    "atlas.core.application.reflection_exploration",
)

# understanding.py, formation.py, exceptions.py, and query.py never
# touch an Engine, a repository, or a table — cli.py is the only file
# in this module allowed to reach infrastructure at all, and it does so
# only through already-existing composition functions (ATLAS-009B/
# ATLAS-010), never by importing sqlalchemy itself.
_NO_SQLALCHEMY_AT_ALL_FILES = ("understanding.py", "formation.py", "exceptions.py", "query.py")


def _imports_of(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(a.name for a in node.names)
    return modules


def test_reflection_understanding_formation_never_imports_sibling_capabilities() -> None:
    for path in MODULE_DIR.glob("*.py"):
        imports = _imports_of(path)
        leaked = [
            m
            for m in imports
            if any(
                m == prefix or m.startswith(prefix + ".")
                for prefix in _FORBIDDEN_MODULE_PREFIXES
            )
        ]
        assert not leaked, f"{path.name} must not import: {leaked}"


def test_core_files_import_no_sqlalchemy_at_all() -> None:
    for filename in _NO_SQLALCHEMY_AT_ALL_FILES:
        imports = _imports_of(MODULE_DIR / filename)
        sqlalchemy_imports = [
            m for m in imports if m == "sqlalchemy" or m.startswith("sqlalchemy.")
        ]
        assert not sqlalchemy_imports, (
            f"reflection_understanding_formation/{filename} must not import "
            f"sqlalchemy at all (no Engine, no repository, no table is "
            f"reachable from this file): {sqlalchemy_imports}"
        )
