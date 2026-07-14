"""Structural isolation tests for reflection_comparison (ATLAS-011).

Reuses this codebase's own AST-import-graph precedent
(tests/test_config_sprint195.py::_config_imports()) rather than a
brittle source-text search.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
MODULE_DIR = REPO_ROOT / "atlas" / "core" / "application" / "reflection_comparison"

_FORBIDDEN_MODULE_PREFIXES = (
    "atlas.core.application.pattern_recognition",
    "atlas.core.application.strategy_signature",
    "atlas.core.application.decision_reflection",
    "atlas.core.application.decision_coach",
    "atlas.core.application.decision_timeline",
)

# comparison.py, exceptions.py, and query.py never touch an Engine, a
# repository, or a table — cli.py is the only file in this module
# allowed to reach infrastructure at all, and it does so only through
# already-existing composition functions (ATLAS-009B/ATLAS-010), never
# by importing sqlalchemy itself.
_NO_SQLALCHEMY_AT_ALL_FILES = ("comparison.py", "exceptions.py", "query.py")


def _imports_of(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(a.name for a in node.names)
    return modules


def test_reflection_comparison_never_imports_other_understanding_capabilities() -> None:
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


def test_comparison_exceptions_and_query_import_no_sqlalchemy_at_all() -> None:
    for filename in _NO_SQLALCHEMY_AT_ALL_FILES:
        imports = _imports_of(MODULE_DIR / filename)
        sqlalchemy_imports = [
            m for m in imports if m == "sqlalchemy" or m.startswith("sqlalchemy.")
        ]
        assert not sqlalchemy_imports, (
            f"reflection_comparison/{filename} must not import sqlalchemy at all "
            f"(no Engine, no repository, no table is reachable from this file): "
            f"{sqlalchemy_imports}"
        )
