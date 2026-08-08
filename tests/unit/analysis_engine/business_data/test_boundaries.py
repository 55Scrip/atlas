"""Boundary tests scoped to `atlas.analysis_engine.business_data`
itself (ATLAS-022). Complements the repository-wide static guardrail
`tests/test_architecture_boundaries.py
::test_analysis_engine_only_reads_core_and_decision_engine`, which
already covers this subpackage since it recursively scans all of
`atlas/analysis_engine/` -- this file checks the sprint's own named
constraints (no Alpha imports, no provider-specific dependencies, no
database writes, no external API calls this sprint) so a reviewer can
see them enumerated in one place, mirroring
`tests/unit/analysis_engine/test_boundaries.py`'s identical pattern for
its parent package.
"""
from __future__ import annotations

from pathlib import Path

_PACKAGE_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "atlas"
    / "analysis_engine"
    / "business_data"
)

#: Checked against the whole file -- unlikely to appear in this
#: package's own prose, so a full-text scan is safe.
_FORBIDDEN_ANYWHERE = (
    "import requests",
    "import httpx",
    "import aiohttp",
    "urlopen(",
    "import sqlalchemy",
    "import sqlite3",
    "import psycopg",
)

#: Checked only against actual `import`/`from` lines -- this package's
#: own module docstrings *deliberately* name these (explaining why
#: `atlas.providers.yahoo.YahooFinanceProvider` and
#: `CompanyDataProvider` are not reused, and that `atlas.alpha` stays
#: out of this boundary), so a full-text scan would flag its own
#: documentation. An actual import is what the boundary forbids.
_FORBIDDEN_IN_IMPORTS = (
    "atlas.alpha",
    "atlas.providers",
    "CompanyDataProvider",
    "YahooFinanceProvider",
)


def _source_files() -> list[Path]:
    return [p for p in _PACKAGE_DIR.rglob("*.py") if "__pycache__" not in p.parts]


def _import_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip().startswith(("import ", "from "))]


class TestNoForbiddenDependencies:
    def test_no_forbidden_substrings_anywhere_in_the_package(self):
        violations: list[str] = []
        for path in _source_files():
            text = path.read_text(encoding="utf-8")
            for needle in _FORBIDDEN_ANYWHERE:
                if needle in text:
                    violations.append(f"{path.name} contains {needle!r}")
        assert not violations, "Forbidden dependency found:\n" + "\n".join(violations)

    def test_no_forbidden_imports_anywhere_in_the_package(self):
        violations: list[str] = []
        for path in _source_files():
            for line in _import_lines(path.read_text(encoding="utf-8")):
                for needle in _FORBIDDEN_IN_IMPORTS:
                    if needle in line:
                        violations.append(f"{path.name}: {line.strip()!r}")
        assert not violations, "Forbidden import found:\n" + "\n".join(violations)

    def test_no_wall_clock_calls_inside_the_package(self):
        violations: list[str] = []
        for path in _source_files():
            text = path.read_text(encoding="utf-8")
            if "datetime.now(" in text or "datetime.utcnow(" in text or "time.time(" in text:
                violations.append(path.name)
        assert not violations, "Wall-clock call found in:\n" + "\n".join(violations)

    def test_package_contains_the_expected_modules(self):
        names = {p.name for p in _source_files()}
        for expected in (
            "__init__.py",
            "contracts.py",
            "models.py",
            "providers.py",
            "sources.py",
            "normalization.py",
            "pipeline.py",
            "versioning.py",
            "validation.py",
            "exceptions.py",
        ):
            assert expected in names, f"{expected} missing from atlas/analysis_engine/business_data/"


class TestNoExternalSourceKindDuplication:
    def test_business_py_no_longer_defines_its_own_source_taxonomy(self):
        """ATLAS-022's own audit decision: exactly one SourceKind-shaped
        document taxonomy in the repository."""
        business_module = _PACKAGE_DIR.parent / "business.py"
        text = business_module.read_text(encoding="utf-8")
        assert "class ExternalSourceKind" not in text
