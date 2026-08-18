"""Canonical Security Foundation (Sprint M) -- the inert, unwired domain
model for `CanonicalSecurity` designed across Sprints J, K, and L.

This package exists to answer, once implemented, "which real-world
company does this ticker actually refer to" with an auditable, provider-
independent identity -- see `docs/canonical_security_identity_design.md`,
`docs/identity_integration_architecture.md`, and
`docs/canonical_security_foundation_implementation_design.md` for the
full design history this implementation follows.

**This package is deliberately not wired into anything yet.** No file
outside this package and its own tests imports it (verified by
`tests/unit/alpha/canonical_security/test_integration_safety.py`).
`atlas.alpha.watchlist`, `atlas.alpha.portfolio`,
`atlas.analysis_engine.business_data` (`BusinessRecord`), and
`atlas.alpha.investment_case` all continue to operate exactly as they did
before this package existed -- Sprint M's own scope is "gain a complete
subsystem without changing existing runtime behaviour," restated here as
a structural fact this package's own test suite enforces, not just a
sprint-note claim.

What this package does NOT reuse, and why: `atlas.alpha.security_
discovery`, `atlas.alpha.security_confirmation`, and `atlas.alpha.
security_identity_evidence` are untouched by this package (per Sprint K's
own finding, restated in Sprint L Phase 12/13: those packages are scoped
to `decision_id` and structurally cannot serve as the identity gate this
foundation exists to eventually become). This package reimplements the
*pattern* those packages already proved (append-only event history,
idempotent/rejecting write semantics, `sync_table_schema`-based
persistence, own `MetaData`, no SQL foreign keys) at the correct scope --
a resolvable security identity, not a Decision's confirmed selection.

Scope narrowing versus Sprint L's own design, documented explicitly here
per Sprint M Phase 15's own instruction to justify or revert deviations:
Sprint L's Phase 7 "Resolution Session" (a separate, persisted audit
object holding the candidate/scoring trail between `DISCOVERED` and
`CONFIRMED`) is not built in this sprint. Sprint M's own Phase 5 (Resolution
Lifecycle) treats `DISCOVERED`/`CANDIDATES_FOUND`/`IDENTITY_VERIFIED` as
states of `CanonicalSecurity.resolution_status` itself, and Sprint M's own
Phase 8 (Domain Events) lists a narrower 7-event set than Sprint L's
Phase 12 candidate-level event list. This package follows Sprint M's own,
narrower brief exactly: `ResolutionStatus` lives directly on the aggregate
(`models.py`), and the 7 events Sprint M's brief names are implemented in
`events.py`, with Sprint L's fuller candidate-level audit trail
(`SecurityDiscovered`, `CandidateFound`, `CandidateAccepted`,
`CandidateRejected`, `SecurityConfirmed`, `SecurityRejectedByInvestor`)
deferred to whichever future sprint actually builds the Resolver/
Verification pipeline these events would describe -- there is nothing yet
in this codebase that would produce them, so building them now would be
speculative, not foundational.
"""
from __future__ import annotations
