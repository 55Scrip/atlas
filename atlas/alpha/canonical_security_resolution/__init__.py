"""Canonical Security Resolution Service (Sprint N) -- the deterministic
resolution/orchestration layer over Sprint M's inert `CanonicalSecurity`
foundation.

**Shadow mode only.** This package proves Atlas can deterministically
resolve securities into `CanonicalSecurity` aggregates, persist the
complete reasoning process, and safely operate without affecting any
existing production behavior -- it does not itself become the identity
gate. `CanonicalSecurityResolutionService.resolve()` never creates a
`BusinessRecord` (no import of `atlas.analysis_engine.business_data` or
`atlas.alpha.business_data_refresh` anywhere in this package) and never
creates a `Case` (no import of `atlas.core.domain.case` or
`atlas.alpha.case_generation`) -- see `service.py`'s own docstring for
the complete list of what this service structurally cannot do. Every
resolution it produces stops at `CanonicalSecurity.resolution_status ==
"CANONICAL"`, never `"ACTIVE"` (Sprint L's own definition: `ACTIVE`
means a `BusinessRecord` actually exists referencing this security,
which never happens here).

Nothing outside this package (and its own tests) imports it yet --
enforced by `tests/unit/alpha/canonical_security_resolution/
test_integration_safety.py`, the same AST-based repository scan Sprint
M's own `test_integration_safety.py` established. `Watchlist`,
`Portfolio`, `BusinessRecord`, and `Investment Case` all continue to
operate exactly as they did before this package existed.

Module map:
- `candidates.py` -- `ProviderCandidate`, the provider-neutral raw
  identity claim (Phase 4).
- `normalization.py` -- resolution algorithm steps 1-2 (Phase 5).
- `comparison.py` -- resolution algorithm steps 3-10 (Phase 5).
- `provider_agreement.py` -- the Provider Agreement Engine (Phase 8).
- `confidence.py` -- the Confidence Engine (Phase 7).
- `outcomes.py` -- the six `ResolutionOutcome` values and
  `determine_outcome` (Phase 6).
- `service.py` -- `CanonicalSecurityResolutionService`, the
  orchestrator (Phase 3), plus `confirm_manually` (Phase 11).
- `expiration.py` -- resolution/confidence aging, pure domain logic,
  no scheduler (Phase 13).
- `table.py` / `repository.py` -- shadow persistence (Phase 9/10/14).
- `serialization.py` -- JSON round-tripping (Phase 15).
- `replay.py` -- the Replay Engine (Phase 12).

See `docs/canonical_security_resolution_service.md` for the full
algorithm write-up, confidence rules, provider-agreement rules, and
architecture diagrams this package implements.
"""
from __future__ import annotations
