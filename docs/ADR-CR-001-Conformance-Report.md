# ADR-CR-001 Conformance Report — Decision Review and Supersession

**Sprint 7 — Architecture Conformance Review.** Audits `docs/ADR-CR-001-Decision-Review-and-Supersession.md` (Accepted) against `atlas/core/domain/decision/entity.py`, `atlas/core/domain/evaluation/entity.py`, and related application/persistence code.

**Overall Conformance: Fully Implemented**

---

## Finding 1 — `Decision` carries no status, review, or supersession field of any kind

- **Conformance:** Fully Implemented.
- **Evidence:** `atlas/core/domain/decision/entity.py`'s full field list is `id, case_id, user_id, decision_type, subject, investment_case, confidence, decided_at, recorded_at, source, observation_id` — no `status`, `superseded_by`, `reviewed`, or equivalent field exists anywhere on the dataclass or in `decision/value_objects.py`. `Decision.register()` is the only construction path; no update/mutate method exists on the class. This is Decision §2's own invariant ("No field or flag... may ever store that a Decision has been superseded") holding exactly, verified directly against the entity rather than assumed.
- **Severity:** Informational.
- **Recommendation:** No action.
- **Ownership:** Backend.
- **Dependencies:** None.

## Finding 2 — `Evaluation` matches the ADR's own description exactly and requires no change

- **Conformance:** Fully Implemented.
- **Evidence:** `atlas/core/domain/evaluation/entity.py`'s own docstring: "the investor's assessment of an Outcome: did it confirm or contradict what was expected, and why? It is immutable and references Outcome only by id, read-only." Matches Decision §1's citation verbatim. `outcome_id` is a required field; no `decision_id` reference exists, confirming the ADR's own Outcome-scoped-only characterization (relevant to this ADR's own Open Questions item about extending `Evaluation` for Outcome-less decisions — still genuinely unextended, not silently worked around).
- **Severity:** Informational.
- **Recommendation:** No action.
- **Ownership:** Backend.
- **Dependencies:** None.

## Finding 3 — Review/Reconsideration resolves into `Decision.register()` exactly as the ADR requires — but no named workflow exists yet at the application or API layer

- **Conformance:** Partially Implemented — the domain-layer requirement (§1: "no new domain object... resolves into `Decision.register()`") is trivially and correctly satisfied, since nothing new was added; a product-level Reconsideration *workflow* (distinguishing a fresh Decision from a reconsideration of an earlier one) does not exist as its own named concept anywhere in `atlas/alpha/` or the API layer.
- **Evidence:** `atlas/core/application/decision/capture_decision.py` and its API router contain a single, undifferentiated Decision-capture path — no "reconsideration" flag, no reference back to a prior Decision on the same subject beyond what `case_id`-based Decision Timeline queries can already derive. This is exactly what the ADR itself calls for (§2: supersession always computed from ordering, never stored) — the absence of a workflow layer is conformance, not a gap, for this ADR's own domain-layer scope.
- **Severity:** Informational.
- **Recommendation:** No action for this ADR. A future, separately-scoped product effort to give Reconsideration a named UI/API shape would be legitimate but is not something this ADR requires or blocks.
- **Ownership:** Product (for any future named workflow — not a current gap).
- **Dependencies:** None.

## Finding 4 — Amendment (Monitoring/Invalidation Conditions) remains correctly unbuilt, matching this ADR's own explicit deferral

- **Conformance:** Fully Implemented (as a deferral, not a build).
- **Evidence:** No Monitoring/Invalidation Condition object exists (see `ADR-CC-001` Conformance Report) — exactly consistent with this ADR's own §3, which explicitly places Amendment out of scope and defers it to Investigations 005/006's own conversion Wave.
- **Severity:** Informational.
- **Recommendation:** No action — tracked instead under `ADR-CC-001`.
- **Ownership:** Architecture.
- **Dependencies:** Cross-references `ADR-CC-001`, which remains Not Implemented (see that report).

---

## Synthesis

`ADR-CR-001` is the cleanest conformance result in this Sprint: the ADR's own decision was that nothing new needed to be built, and the audit confirms nothing new was built, incorrectly or otherwise. `Decision`'s immutability invariant, the specific thing this whole ADR series treats as most load-bearing, holds exactly as written, verified against the entity's actual field list rather than taken on faith.
