"""Atlas Alpha's provisional portfolio state.

This module is explicitly provisional Alpha application state. It is:

- NOT a Core Domain Object (`OE-002` §4's Domain Object Set is closed —
  Observation, Knowledge Reference, Reasoning Trace, Judgment, Decision,
  Outcome — and includes no owned-position or Portfolio primitive).
- NOT a canonical Product aggregate (`APS-006` PF-R-002, PF-R-006, and
  PFINV-001 forbid treating Portfolio as, or introducing, a Core Domain
  Object; this module lives outside `atlas/core/` entirely, so those
  rules are respected by construction, not by exception).
- NOT a permanent Portfolio architecture. It may be replaced, migrated,
  or deleted once a formal Portfolio/Holding architecture is authorized.
- NOT a resolution of `APS-006` §24's open question ("whether 'Holding'
  or 'owned position' requires later formal Product Concept treatment").
  That question remains open; this module answers only "what does Atlas
  Alpha need today to run one honest vertical slice."

Its purpose is narrow: hold investor-supplied Alpha portfolio input
(`AlphaPortfolioState`, `models.py`) and expose a derived, read-only
portfolio representation by calling the existing, unmodified
`atlas.domains.portfolio.calculations` engine (`projection.py`). It
originates no Core Domain Object and mutates nothing in `atlas/core/`.

Sprint 1A scope only (Alpha Sprint 1, Phase 4 revised plan, Decision 3):
establishing state via manual existing-portfolio entry or the
from-scratch path, and reading the derived view. No trade recording, no
`AlphaTradeLogEntry`, no reconciliation — that is Sprint 1B, added only
after Sprint 1A is independently verified.

See `tests/test_architecture_boundaries.py::test_core_does_not_import_atlas_alpha`
for the enforced half of this boundary, and `tests/unit/alpha/portfolio/`
for tests asserting this module's own restraint.
"""
