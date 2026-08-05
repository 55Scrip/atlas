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

Sprint 1A: establishing state via manual existing-portfolio entry or the
from-scratch path, reading the derived view, and linking a holding to
its Investment Case.

Sprint 1B adds `AlphaTradeLogEntry` (`trade_log_table.py`,
`trade_log_store.py`) and portfolio reconciliation. Recording a
confirmed external trade *reads* the existing, immutable Core Outcome
by id via `OutcomeRepository` -- the one authorized direction this
sprint states explicitly: "The Alpha layer may reference Outcome.
Outcome must never reference Alpha." No Core object is ever written to,
modified, or originated by this module; `Outcome`'s own entity,
persistence, API schemas, and application service remain byte-for-byte
unchanged.

See `tests/test_architecture_boundaries.py::test_core_does_not_import_atlas_alpha`
and `::test_alpha_does_not_write_to_outcome` for the enforced halves of
this boundary, and `tests/unit/alpha/portfolio/` for tests asserting
this module's own restraint.
"""
