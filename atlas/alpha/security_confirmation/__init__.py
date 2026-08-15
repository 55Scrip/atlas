"""Explicit Security Confirmation (Sprint 20) -- the narrow boundary
between Sprint 19's read-only `SecurityCandidate` discovery and a
future, not-yet-built canonical `SecurityIdentity`.

Genesis: Sprint 19 proved candidate discovery is viable but explicitly
non-authoritative (`SecurityCandidate.status` is always
`"candidate_only"`). Sprint 20 investigated what an explicit investor
confirmation can actually prove, and found the honest answer narrower
than it might first appear:

    "The investor asserts that, for this specific Decision, the
    intended referent was this specific ticker."

This is what `ConfirmedSecuritySelection` records -- nothing more. It
does NOT prove, and this package never claims:

- that the ticker is the security's objective canonical identity
  (that is `SecurityIdentity`, still unbuilt, still Sprint 17/18
  territory -- external identity evidence, not investor intent);
- that any *other* Decision sharing the same recorded subject text
  means the same thing (Sprint 20's own scope investigation: Case
  carries no single-security invariant, `case_id` alone did not unify
  NVDA/NVIDIA in Sprint 16's real data, and nothing rules out the same
  free-text subject legitimately meaning different securities across
  different Decisions -- ticker reuse, share classes, generic names,
  re-entry after exit). Confirmation is therefore **decision-scoped
  only** -- there is no case-level, subject-level, or investor-global
  alias concept anywhere in this package;
- that the candidate the investor is confirming was genuinely the one
  a UI rendered -- Sprint 19's discovery results are not persisted, so
  this package cannot independently verify what a caller previously
  showed a human. The write contract is honest about this: it records
  "the investor asserts ticker X for Decision Y," carrying through
  whatever candidate provenance the caller supplies, not "Atlas
  verified this candidate was actually displayed."

Ground rules preserved structurally, not just by convention:

- `Decision.subject`/`Decision.case_id`/every other Decision field is
  never written by this package -- `service.py` only ever calls
  `DecisionRepository.get` (a read), never anything that mutates
  Decision;
- no field, method, or class anywhere in this package is named in a
  way that implies external identity verification (`resolved_security`,
  `canonical_security`, `verified_identity` do not exist here --
  see `models.py`'s own naming);
- Pattern Recognition, Observed Decision Properties, Strategy
  Signature, and History are not imported by, and do not import,
  anything in this package;
- confirmations are insert-only at the table level (see `table.py`) --
  a resubmission of the *same* ticker for the *same* Decision is
  idempotent (returns the existing row, no duplicate insert); a
  *different* ticker for a Decision that already has a confirmation is
  rejected outright (409), never silently overwritten -- correction/
  revocation semantics remain a deliberately unbuilt future decision
  (Sprint 20 Phase 36/37), and this table's shape (no unique
  constraint on `decision_id` alone, enforced only at the service
  layer) does not foreclose a future append-only supersession model.

Following the one-way boundary `test_core_does_not_import_atlas_alpha`
already enforces: this package (`atlas.alpha`) imports
`atlas.core.domain.decision` (to reference `DecisionId` and read via
`DecisionRepository`) and `atlas.core.infrastructure.persistence.shared`
(for the same `sync_table_schema` helper every other Alpha persistence
package already uses); nothing in Core ever imports this package.
"""
from __future__ import annotations
