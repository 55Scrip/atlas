"""Security Identity Evidence (Sprint 23) -- the narrow boundary
between investor-authored `ConfirmedSecuritySelection` (Sprint 20/22)
and a future, still-unbuilt canonical `SecurityIdentity`.

Genesis: Sprint 20-22 gave Atlas an honest way to record "the investor
asserts ticker X for Decision Y," with a full append-only correction/
revocation lifecycle. What remained missing was any representation of
*externally observed* evidence about that assertion -- Atlas could
record what the investor said, but had no way to record what an
independent, external source (a security-identifier provider) actually
returned when asked about that same ticker.

This package fills exactly that gap, and nothing more:

    "An external provider was asked about the confirmed ticker at a
    specific point in time, and this is what it returned."

`SecurityIdentityEvidence` does NOT prove, and this package never
claims:

- that the provider's data is objectively, canonically true (that
  would be `SecurityIdentity`, still unbuilt -- this package produces
  raw material a future `SecurityIdentity` system might someday
  consume, but is not that system itself);
- that a "verified" result means Atlas has confirmed the security's
  real-world identity -- it means "the provider's own ticker/name data
  was consistent with what the investor confirmed," nothing stronger;
- that evidence in any way overrides, supersedes, or invalidates the
  investor's own confirmation -- verification is purely informational
  and can never automatically confirm, correct, or revoke anything
  (Sprint 23 ground rules 8-9). A "not_verified" result does not revoke
  the confirmation it is about; the investor's assertion stands exactly
  as recorded until *they* explicitly change it.

Structural ontology (Sprint 23 Phase 3) -- four concepts, no overlap:

- `SecurityCandidate` (Sprint 19): an unconfirmed possibility surfaced
  from SEC's own data by matching free text. Ephemeral, never persisted.
- `ConfirmedSecuritySelection` (Sprint 20/22): the investor's own
  explicit, persisted, append-only assertion for one Decision.
- `SecurityIdentityEvidence` (this package): an externally-sourced,
  persisted, append-only *observation* about one specific confirmation
  event -- never user-authored, never mutates or overrides it.
- `SecurityIdentity` (future, unbuilt): would be Atlas's own canonical,
  resolved identity for a security. This package is explicitly not
  that, and does not attempt to become it.

Scope (Sprint 23 Phase 5): evidence is scoped to one specific
*confirmation event* (`confirmation_id`, the `id` of one
`ConfirmedSecuritySelection`/`SecurityConfirmationEvent` row) -- not to
the Decision, not to the provider. Correcting a confirmation (Sprint
22's `correct()`) produces a logically new confirmed ticker; any
evidence gathered about the earlier ticker remains permanently
associated with that earlier, now-historical confirmation event,
exactly mirroring how Sprint 22 already treats a revoked confirmation
as permanent history rather than something to migrate or discard.

Verification is always an explicit action (Sprint 23 ground rule 14) --
never triggered automatically by `confirm`, `correct`, or `revoke`.

Following the one-way boundary `test_core_does_not_import_atlas_alpha`
already enforces: this package imports
`atlas.alpha.security_confirmation` (to read, never write, the current
confirmation for a Decision -- the same kind of Alpha-to-Alpha read
already established by Daily Brief/History reading
`investment_case_change`'s persisted state) and
`atlas.alpha.security_discovery.canonicalize` (the same pure,
dependency-free name-comparison transform Sprint 19 already proved,
reused here rather than inventing a second fuzzy-matching approach).
Core never imports this package.
"""
from __future__ import annotations
