"""Structural isolation tests for reflection_history (ATLAS-010).

Reuses this codebase's own AST-import-graph precedent
(tests/test_config_sprint195.py::_config_imports()) rather than a
brittle source-text search.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
MODULE_DIR = REPO_ROOT / "atlas" / "core" / "application" / "reflection_history"

_FORBIDDEN_MODULE_PREFIXES = (
    "atlas.core.application.pattern_recognition",
    "atlas.core.application.strategy_signature",
    "atlas.core.application.decision_reflection",
    "atlas.core.application.decision_coach",
    "atlas.core.application.decision_timeline",
)


def _imports_of(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(a.name for a in node.names)
    return modules


def test_reflection_history_never_imports_other_understanding_capabilities() -> None:
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


def test_composition_does_not_import_sqlalchemy_core_directly() -> None:
    """`sqlalchemy.engine` (the Engine type) is fine; `sqlalchemy` Core
    (Table/insert/select/update) must never be imported here — those
    belong entirely to the infrastructure layer, mirroring the same
    layering test ATLAS-009B added for its own composition.py."""
    imports = _imports_of(MODULE_DIR / "composition.py")
    core_imports = [m for m in imports if m == "sqlalchemy"]
    assert not core_imports, (
        f"reflection_history/composition.py must not import sqlalchemy Core "
        f"directly: {core_imports}"
    )
