# ADR-CC-001 — CaseCondition

**Status:** Accepted. Validated per `docs/ADR-CC-001-Validation-Report.md` (Accept with Changes; changes incorporated).
**Type:** Ontology ADR — Atlas Core, Decision Workspace domain. Produced by the ADR Adoption Program, Sprint 6 (Wave 2), converting recommendations from `docs/ADR-Investigation-005-Review-Trigger-vs-Monitoring-vs-Invalidation.md` and `docs/ADR-Investigation-006-CaseCondition-Definition-Predicate-Lifecycle-Evaluation.md`, following the process established by `ADR-GOV-001`, `ADR-GOV-002`, `ADR-GOV-003`. Depends on `ADR-DC-001-Decision-Context.md` and `ADR-DD-001-Decision-Draft.md`.

---

## Problem

UX-008 and UX-009 require Monitoring Conditions, Invalidation Conditions, and a Review Plan attached to a recorded investment Decision. No existing object can represent any of them: `Decision` is immutable and cannot hold a growing, editable condition list, and the existing `atlas/monitoring` package — despite its name — is a stateless, Decision/Case-unaware legacy scoring utility whose own historical comparison is synthetically fabricated, not a working-but-dormant system.

## Context

`Investigation-005` tested six named "Review Trigger" examples (scheduled date, thesis-assumption invalidation, new evidence, valuation threshold, portfolio concentration, manual entry) and found they span at least four structurally different mechanisms — "Review Trigger" is not one domain object, but a product-level label for several different things that can lead an investor back into the Decision Workspace. It further found Decision-scoping alone too narrow: Watchlist securities have `Case`s but no `Decision`s, and Portfolio-wide conditions have neither. `Investigation-006`, building tightly on that evidence, converged independently across four separate phases (3, 4, 10, 12) on a single, economical shape: exactly two objects — a stable `CaseCondition` identity (the definition) and one unified `CaseConditionEvent` stream, covering both revisions and meaningful evaluation transitions as different event types — materially leaner than the eight-state lifecycle a naive reading of UX-009 might suggest. `atlas/alpha/security_confirmation`'s already-shipped `SecurityConfirmationEvent`/`ConfirmedSecuritySelection` pattern is the direct structural template, reused for a third time in this document series.

This ADR converts `INV5-R1` (superseded in detail, not in substance, by `INV6-R1`'s leaner refinement), `INV6-R1` through `INV6-R7`, `INV5-R2` through `INV5-R5`, and `INV6-R6`, consistent with `Atlas-Recommendation-Register.md`'s own dependency graph. `INV5-R6`/`INV6-R5` (Portfolio-scoped conditions) are a disclosed gap, not an adoption candidate — carried into Open Questions, not converted here.

Decision §3's predicate-content shape (free text by default, with an optional structured sub-field) is drawn directly from `Investigation-006` Phase 2's own analysis, which was not independently extracted as its own numbered Register recommendation — Sprint 1's own register pass folded it into `INV6-R1`'s general "definition" scope rather than giving it a separate ID. Recorded here explicitly, consistent with this program's own principle (`ADR-GOV-003` Context) that a recommendation's conversion into followable architecture is legitimate drafting work, but must be disclosed as such rather than presented as if directly approved verbatim under its own ID.

## Decision

1. **Adopt `CaseCondition`** — a stable, Case-scoped identity, with an optional `decision_id` back-reference for the common case where a condition originates from a specific Decision Workspace recording. This ADR adopts `INV6-R1`'s refined shape directly; `INV5-R1`'s own original proposal is treated as superseded in detail, not in substance, per `Atlas-Recommendation-Register.md`'s own note.
2. **`CaseCondition`'s lifecycle MUST be expressed entirely through a single, unified `CaseConditionEvent` stream, never through mutation.** The condition's own definition is created once and never mutated; every subsequent change — a revision, a meaningful evaluation transition, a supersession, a retirement — is a new, immutable event (`revised`, `evaluated_satisfied`, `superseded`, `retired`) in that one stream, directly generalizing `SecurityConfirmationEvent`'s own `confirmed`/`revoked` shape. "Satisfied condition" and "detected event" are the same underlying transition described from two angles, not two objects. Only meaningful transitions are ever persisted — routine "still not met, checked again today" re-checks are never stored.
3. **A `CaseCondition`'s stored content is free text by default**, with an optional structured sub-field for the subset of conditions mechanically evaluable today (a specific date; a metric-operator-threshold triple). It is boolean only as an evaluation outcome, never as a storage type — qualitative, date-based, and event-based conditions all coexist and share no single formal schema.
4. **Monitoring and Invalidation Conditions are the same object type, differentiated by a role field, never separate aggregates.** The distinction is functional, not structural: a Monitoring Condition is passive watch with no inherent consequence; an Invalidation Condition is a watch specifically designated to warrant re-entry into the Decision Workspace when met.
5. **Time-based and state-based conditions share one object shape (`CaseCondition`) but never one evaluation mechanism.** Calendar comparison (a trivial `today >= date` check, needing no live data) and live-data threshold comparison (genuinely needing infrastructure that does not currently exist in any Decision-anchored, persisted form) remain structurally distinct processes — the already-shipped `_is_thesis_stale` fixed 90-day threshold is existing precedent that this split already holds elsewhere in this codebase.
6. **`CaseCondition` references `case_id` always and `decision_id` optionally**, following the same optional-additive-reference precedent `ADR-DD-001` §5 establishes for `Decision.observation_id`. No field or flag on `Decision` — or on any other object — may ever mark a Decision "monitored" or "invalidated"; that state lives entirely on `CaseCondition`, consistent with `ADR-CR-001` §2's own derived-state principle applied to a different relationship.
7. **`CaseCondition` content may originate as `DecisionDraft` content and be captured as a real `CaseCondition` only at Decision-commit time**, mirroring exactly how `ADR-DD-001` §3 already describes `DecisionContext` being captured from draft content. `DecisionDraft` itself has no predicate/evaluation shape of its own and is not a substitute for `CaseCondition`.
8. **Daily Brief MUST consume only a narrow, derived projection over `CaseCondition` — never raw condition definitions, never raw per-check evaluations.** The projection unions several sources into a single "Review Trigger" surface: unified Satisfied/Invalidated transitions (at higher priority for the Invalidation role), overdue time-based conditions, and recommendation-shift signals sourced from the already-existing, already-shipped Change Intelligence computation — no new ontology is needed to source the last of these.
9. **The existing `atlas/monitoring` package is kept fully separate — not reused, not extended, not wrapped, not replaced.** It remains a legitimate, narrow, deterministic scoring/snapshot utility for Company/Theme/Market Health/Market Regime display, unrelated to `Decision`/`Case`, with a synthetically fabricated comparison baseline that must never be presented as a genuine longitudinal signal for `CaseCondition` purposes.
10. **The following models are rejected:** Monitoring owning everything (really means building something new under a misleading legacy name); a separate `MonitoringCondition`/`ReviewSchedule` structural split (unjustified given the role-not-kind finding in §4); a fully generic Watch Condition spanning Security/Case/Portfolio in one shape (under-differentiates genuinely different-scoped concerns); no new ontology at all, fully derived from `Decision.reason` (a real, viable minimal option, but permanently forecloses automated detection); a mutable condition row (the first mutable-row precedent break this series has found, directly contradicting Security Confirmation's own deliberate move away from it).

## Rationale

The evidence converges from two independent investigations onto one economical shape, not by assumption but by four separate phases in `Investigation-006` (3, 4, 10, 12) each independently arriving at the same two-object structure. Adopting `INV6-R1`'s refinement over `INV5-R1`'s original proposal follows this program's own established practice of tracking supersession-in-detail explicitly (`ADR-GOV-002` §5) rather than silently discarding the earlier, less-specified finding. Keeping Monitoring and Invalidation as one object differentiated by role (§4), rather than two aggregates, avoids an unjustified structural split the evidence does not support. Reusing the Security Confirmation event pattern for a third time (§2) is deliberate, not incidental — it is now an established, reusable architectural template for exactly this family of "editable-over-time but historically-honest" concepts.

## Alternatives Considered

See Decision §11, above, for the specific rejected models and their individual grounds.

## Consequences

- `Decision`'s immutability, and everything downstream that relies on it (`ReflectionResponse`, `ADR-DD-001`'s `DecisionDraft`, `ADR-CR-001`'s derived-supersession model), remains completely untouched.
- `atlas/monitoring` requires no change and is not implicated by this ADR.
- Daily Brief gains one more source to union into its existing narrow-projection boundary (already established by `ADR-DD-001` §4 for drafts), not a new content type designed from scratch.
- Portfolio-scoped conditions (concentration limits, sector exposure) remain explicitly unsolved and out of scope for this ADR — a genuine, disclosed gap, not silently claimed as solved.
- A real naming-collision risk is inherited and must be actively managed by any future implementation: "Condition Evaluation" (this ADR's own term) and the Core Loop's own `Evaluation` aggregate (the investor's assessment of an `Outcome`) are different concepts sharing one English word.
- Decision Timeline and Decision Memory (`DE-005`) each gain a disclosed, but not yet designed, future integration point for `CaseCondition`'s own Satisfied/Invalidated events.

## Invariants

- `CaseCondition` itself is created once and never mutated; every subsequent change is a new `CaseConditionEvent`.
- One event stream, one condition identity, multiple event types (`revised`, `evaluated_satisfied`, `superseded`, `retired`) — never a mutated row.
- Only meaningful evaluation transitions are ever persisted as events; routine non-transition checks are never stored.
- Scope is Case-first, never Portfolio — a distinct, unsolved sibling concept.
- No field anywhere marks a `Decision` "monitored" or "invalidated"; that state lives entirely on `CaseCondition`.
- Unedited acceptance of an Atlas-proposed condition follows `ADR-002` C-02's authorship model exactly.

## Migration

None to existing code — no `CaseCondition` object exists yet, and nothing currently implemented is altered by this ADR. `atlas/monitoring` is explicitly untouched. A future implementation effort would build the object and its event stream against this ADR's own shape.

## Open Questions

- How Portfolio-scoped conditions (concentration limits, sector exposure) should be represented, given they explicitly do not fit `CaseCondition`'s own Case-anchored shape — not resolved here, restated unchanged from `Investigation-005`/`006`.
- Whether `CaseCondition` content is always captured via a `DecisionDraft` first, or direct Decision-time capture is also legitimate — not resolved.
- What the actual scheduling/evaluation mechanism for state-based conditions is, given `atlas/monitoring` cannot currently serve this role — a real, unavoidable next question, explicitly out of this ADR's own ontology-only scope.
- Whether Daily Brief's union-of-sources projection should be its own read-model service or computed ad hoc per request — an implementation question, not decided here.
- Whether a future formal cross-reference between `CaseCondition` and `Assumption` (`ADR-AS-001`) should be enforced or left entirely loose — named in `ADR-AS-001`'s own Open Questions, not resolved by either ADR.
- The same conversion-path question raised in `ADR-DC-001`'s own Open Questions applies identically here.

## Related

`docs/ADR-Investigation-005-Review-Trigger-vs-Monitoring-vs-Invalidation.md`, `docs/ADR-Investigation-006-CaseCondition-Definition-Predicate-Lifecycle-Evaluation.md` (source investigations). `ADR-DC-001-Decision-Context.md`, `ADR-DD-001-Decision-Draft.md`, `ADR-CR-001-Decision-Review-and-Supersession.md` (Wave 1 ADRs this document builds on). `ADR-AS-001-Assumption.md` (the loose, optional cross-reference relationship, §7 of that document). `atlas/alpha/security_confirmation` (the direct, already-shipped precedent for §2's own persistence pattern). `ADR-002-Critical-UX-Architecture-Resolutions.md` C-02 (authorship model, §10). `ADR-GOV-001`, `ADR-GOV-002`, `ADR-GOV-003` (governing process). `Atlas-Recommendation-Register.md` (source of every cited `INV5-R`/`INV6-R` recommendation ID).
