"""Atlas Alpha — explicitly provisional application-layer modules.

Everything under `atlas/alpha/` supports Atlas Alpha's own internal
usable vertical slice. It is not Atlas Core (`atlas/core/`), not a
canonical Product Architecture surface, and not a resolution of any open
Product Architecture question (see `atlas/alpha/portfolio/__init__.py`
for the specific boundary this establishes for Portfolio).

`atlas/core/` MUST NOT import from `atlas/alpha/` — enforced by
`tests/test_architecture_boundaries.py::test_core_does_not_import_atlas_alpha`.
Modules under `atlas/alpha/` MAY import read-only from `atlas/core/` and
from the pre-existing `atlas.domains`/`atlas.adapters`/`atlas.shared`
layers — that is the only authorized direction.
"""
