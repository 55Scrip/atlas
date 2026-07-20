"""Structural isolation tests for atlas.core.domain.shared (DO-IMP-002).

Reuses this codebase's own AST-import-graph precedent
(tests/unit/application/reflection_understanding_formation/
test_module_isolation.py) rather than a brittle source-text search.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
MODULE_DIR = REPO_ROOT / "atlas" / "core" / "domain" / "shared"

# The shared module must be usable by every future owning Domain Object
# without ever depending on one of them, or on any legacy/non-adopted
# concept, or on any infrastructure/API-layer technology.
_FORBIDDEN_MODULE_PREFIXES = (
    "atlas.core.domain.case",
    "atlas.core.domain.decision",
    "atlas.core.domain.outcome",
    "atlas.core.domain.hypothesis",
    "atlas.core.domain.evaluation",
    "atlas.core.domain.learning",
    "atlas.core.domain.evidence",
    "atlas.core.domain.observation",
    "atlas.core.domain.question",
    "atlas.core.domain.interpretation",
    "atlas.core.domain.conclusion",
    "atlas.core.domain.reasoning_link",
    "fastapi",
    "pydantic",
    "sqlalchemy",
    "atlas.core.infrastructure",
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


def test_shared_domain_module_never_imports_concrete_aggregates_or_infrastructure() -> None:
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


def test_shared_domain_module_files_are_present() -> None:
    filenames = {p.name for p in MODULE_DIR.glob("*.py")}
    assert filenames == {
        "__init__.py",
        "domain_object_type.py",
        "typed_reference.py",
        "exceptions.py",
    }
