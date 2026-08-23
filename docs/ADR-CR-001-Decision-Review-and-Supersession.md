# ADR-CR-001 — Decision Review and Supersession

**Status:** Accepted. Validated per `docs/ADR-CR-001-Validation-Report.md` (Accept with Changes; changes incorporated).
**Type:** Ontology ADR — Atlas Core, Decision Workspace domain. Produced by the ADR Adoption Program, Sprint 5 (Wave 1), converting recommendations from `docs/ADR-Investigation-004-Decision-Review-vs-Amendment-vs-Supersession.md`, following the process established by `ADR-GOV-001`, `ADR-GOV-002`, `ADR-GOV-003`. Depends on `ADR-DD-001-Decision-Draft.md`.

---

## Problem

UX-008 and UX-009 describe Review, Amendment, and Supersession as things that happen to a Decision after it is recorded. `Decision` is immutable — "there is no update; a changed opinion is a new Decision." Whether Atlas therefore needs separate objects for Review, Amendment, and Supersession, or whether existing mechanisms already suffice, has never been formally settled.

## Context

`Investigation-004` found that `Evaluation` (`atlas/core/domain/evaluation/entity.py`) — an existing, already-implemented Core Loop object — already is a real review mechanism: "the investor's assessment of an Outcome: did it confirm or contradict what was expected, and why." UX-009's own text, independently, resolves the review *act* into the existing Decision-recording mechanism directly: "the user completes the review by recording a new decision." Testing every candidate object and model against this evidence, `Investigation-004` found supersession is fully computable from `decided_at`/`recorded_at` ordering across Decisions sharing a subject, requiring no stored field; and that "Amendment," as UX-009 actually uses the word, refers specifically to Monitoring/Invalidation Conditions — content with no object to attach to as of this ADR, explicitly out of this Wave's own scope.

## Decision

**Naming note:** "Supersession" is used in this document in a sense distinct from `ADR-GOV-002` §5's own document-level supersession. `ADR-GOV-002` §5 supersession is explicit — it requires an identified replacing decision and an explicit status change on the superseded document. The Decision-level supersession defined below (§2) is the opposite in mechanism — implicit and fully derived from timestamp ordering, with an explicit status field or flag forbidden outright. The two share a name and a general shape (a later thing displacing an earlier one for the same subject) but are deliberately different mechanisms governing different kinds of objects; neither is inconsistent with the other.

1. **No new domain object is adopted for Review, Amendment, or Supersession.** Review and Reconsideration resolve into the existing `Decision.register()` mechanism — optionally by way of a `DecisionDraft` (`ADR-DD-001`) — or, specifically for assessing whether an `Outcome` confirmed or contradicted expectation, the existing `Evaluation` object.
2. **No field or flag on `Decision`, or on any other object, may ever store that a Decision has been "superseded."** Whether a later Decision supersedes an earlier one, for the same subject, is always computed by comparing `decided_at`/`recorded_at` ordering — never persisted as a status.
3. **Amendment, as UX-009 uses the term, is deferred entirely by this ADR.** It refers specifically to versioned changes to Monitoring and Invalidation Conditions, neither of which has an adopted object as of this Wave — Investigations 005 and 006 address this directly and are explicitly out of this ADR's own scope. Nothing in this ADR authorizes attaching amendment semantics to `Decision` itself.
4. **The following models are rejected:** `Decision` gaining a mutable status field for review/supersession tracking (the single most severe failure considered — directly breaks `Decision`'s core invariant and everything downstream that relies on it, including `ReflectionResponse`'s own stated safety claim); a dedicated Review object distinct from both `Evaluation` and a plain new `Decision` (not supported by UX-009's own text, which already resolves review into recording a new Decision); a general Amendment object built now (premature — nothing yet exists for it to amend); a `Decision` lifecycle object separately tracking superseded-by/reviewed-by relationships (an unrequired materialized view of a relationship §2 already establishes is freely derivable); full event-sourcing of `Decision` itself (solves a problem the existing table-of-immutable-rows, queried by ordering, already solves without additional machinery).

## Rationale

The evidence converges on a genuinely economical conclusion, in contrast to `ADR-DD-001`: reviewing and reconsidering resolve into mechanisms that already exist (`Decision.register()`, `Evaluation`), so no new object is justified. This is not a default position — `Investigation-004` tested each candidate model directly, including several that would have introduced new ontology, and found none of them survives against the evidence that `Decision`'s own immutability, combined with a derived-supersession relationship, already accounts for everything UX-008/UX-009 describe except Amendment specifically, which this ADR deliberately does not attempt to resolve out of its own proper scope.

## Alternatives Considered

See Decision §4, above, for the specific rejected models and their individual grounds.

## Consequences

- `Decision`'s immutability, and everything downstream that relies on it, remains completely untouched.
- Decision Timeline (the existing chronological read model over Decision/Outcome/Evaluation/Learning) already supports everything this ADR concludes, today, with zero new work required.
- `DE-005`'s own existing Decision Memory synthesis — "the accumulated set of `reason` statements... read together in order," computed fresh, never stored — is independently validated, not contradicted, by this ADR.
- Amendment remains explicitly unresolved and is not silently claimed as solved by this ADR; whoever converts the relevant recommendations from Investigations 005/006 in a future Wave inherits this open boundary directly.

## Invariants

- No field or flag anywhere ever marks a Decision "superseded," "reviewed," or "amended" — these facts are always computed, never persisted as status.
- `Decision`'s own immutability is never weakened to accommodate Review, Reconsideration, or Supersession.
- Amendment-shaped behavior, if and when it is designed for a future Monitoring/Invalidation object, follows the already-proven append-only-revision pattern established in `ADR-DD-001` — not invented fresh at that time.

## Migration

None. No existing object is modified by this ADR; it confirms that current mechanisms already suffice for everything within its own stated scope.

## Open Questions

- Whether Daily Brief needs its own explicit "superseded/stale" computed signal, or whether surfacing the ordered Decision Timeline is sufficient — not resolved.
- How Reconsideration should compose with `DecisionDraft` (`ADR-DD-001`) in product terms, given the architectural relationship between them is already clean — a product-design question, not decided here.
- Whether `Evaluation` should ever be extended to cover reasoning-quality review for decisions that never produce an `Outcome` (for example, a Maintain/Hold decision) — not resolved; `Evaluation`'s own anchor is strictly Outcome-scoped today.
- The still-missing home for the review-*trigger* (as distinct from the review act, which this ADR resolves) remains open and is explicitly out of this ADR's own scope — Investigation 005 addresses it directly and belongs to a later conversion Wave.

## Related

`docs/ADR-Investigation-004-Decision-Review-vs-Amendment-vs-Supersession.md` (source investigation). `ADR-DD-001-Decision-Draft.md` (Reconsideration may begin as a Draft). `ADR-GOV-001`, `ADR-GOV-002`, `ADR-GOV-003` (governing process). `docs/ADR-Investigation-005-Review-Trigger-vs-Monitoring-vs-Invalidation.md` and `docs/ADR-Investigation-006-CaseCondition-Definition-Predicate-Lifecycle-Evaluation.md` (own the Amendment/Monitoring/Invalidation questions this ADR explicitly defers, out of scope for a future conversion Wave).
