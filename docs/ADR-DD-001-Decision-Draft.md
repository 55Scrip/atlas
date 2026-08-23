# ADR-DD-001 — Decision Draft

**Status:** Accepted. Validated per `docs/ADR-DD-001-Validation-Report.md` (Accept with Changes; changes incorporated).
**Type:** Ontology ADR — Atlas Core, Decision Workspace domain. Produced by the ADR Adoption Program, Sprint 5 (Wave 1), converting recommendations from `docs/ADR-Investigation-003-Decision-Drafts-vs-Immutable-Decision.md`, following the process established by `ADR-GOV-001`, `ADR-GOV-002`, `ADR-GOV-003`. Depends on `ADR-DC-001-Decision-Context.md`.

---

## Problem

UX-009 requires a Save-as-Draft capability with cross-session persistence — a draft must survive panel collapse, page navigation, browser refresh, and be surfaced days later in Daily Brief. `Decision` is immutable and structurally cannot represent an incomplete commitment. No existing object in the implemented codebase can legitimately hold pre-Decision, editable, investor-authored content.

## Context

`Investigation-003` tested this question exhaustively: `Decision` itself cannot be incomplete (its constructor requires every field already populated); `DecisionContext` and `ReflectionResponse` (both `ADR-DC-001`) each require an already-existing `Decision`, structurally precluding pre-Decision use, and are each immutable, precluding the repeated editing a draft requires; `Case` is doctrinally content-free and cannot legitimately hold draft state directly; every earlier Core Loop object (`Observation`, `Question`, `Conclusion`, `ReasoningTrace`, `Judgment`) is either immutable, wrong-shaped, or wrong-directioned. No existing object survived this test.

Separately, `atlas/alpha/security_confirmation` already implements a real, shipped, tested pattern for exactly this shape of problem: `SecurityConfirmationEvent`, an append-only event stream (`confirmed`/`revoked`), with `ConfirmedSecuritySelection` as a derived, always-recomputable "current state" projection — never itself mutated. `Investigation-003` found this pattern directly reusable for Decision Drafts, without inventing a new persistence philosophy.

## Decision

**Naming note:** `DecisionDraft` (the domain object adopted below) and "Draft" (the document-status value defined in `ADR-GOV-002` §6, describing an ADR or OE not yet a stable basis for dependent work) are unrelated uses of the same word. This ADR's own `Status:` header uses the latter sense; every other use of "draft"/"Draft" in this document refers to `DecisionDraft`, the domain object.

1. **Adopt `DecisionDraft`** — a stable, Case-scoped identity, referencing `case_id` directly (following `Decision`'s own precedent, not `DecisionContext`'s narrower one) and investor identity, never `decision_id` — since no `Decision` exists yet at the point a draft is created.
2. **`DecisionDraft`'s lifecycle MUST be built on the append-only-events-plus-derived-current-state pattern already proven by `SecurityConfirmationEvent`/`ConfirmedSecuritySelection`.** A `DecisionDraft`'s own definition is immutable once created; every subsequent edit is a new, immutable event in its own stream, never a mutation of a stored row. "Current state" is always a derived projection over the latest relevant event, never a separately, directly edited value.
3. **The commit boundary for a Draft becoming real MUST remain the existing, unmodified `Decision.register()` call, and, where applicable, `DecisionContext.capture()` (`ADR-DC-001`).** `DecisionDraft` never itself becomes a `Decision`. A new `Decision` (and, optionally, a new `DecisionContext`) is constructed fresh from whatever the draft held at the moment of commit; the draft object and the resulting `Decision` remain two separate, independently-identified things.
4. **Daily Brief MUST consume only a narrow summary projection of drafts** — existence, subject, and a resume link — **never full draft content** (rationale, confidence, or any other field an investor has not yet committed to).
5. **Any future provenance reference from `Decision` back to the `DecisionDraft` it originated from MUST be optional and additive**, following the `Decision.observation_id` precedent exactly — never a required field. `Decision.source` values `IMPORT`, `API`, and `BROKER_SYNC` never pass through a draft at all, and no future schema may require one.
6. **The following models are rejected:** a purely transient, non-persisted draft (fails the Daily Brief cross-session requirement directly); `Decision` gaining a mutable `DRAFT` status (destroys `Decision`'s own core immutability invariant, and breaks `ReflectionResponse`'s own stated reliance on Decisions never changing after being read); `DecisionContext` doubling as the draft object (fails on two independent structural grounds — temporal precedence and immutability); a generic, untyped "Case Workspace State" bag (collapses into a mislabeled version of §1 once examined, with a weaker contract); an event-only model with no derived current-state projection (works, but is strictly dominated by §2's own richer model, which the Security Confirmation precedent itself already chose over the leaner alternative).

## Rationale

Every existing candidate object was tested directly, not assumed unsuitable — the exhaustive rejection in `Investigation-003` is the evidentiary basis for concluding new ontology is genuinely required here, unlike the governance-track questions in `ADR-GOV-001`–`003`, where existing structure sufficed. Reusing the Security Confirmation event pattern (§2) rather than inventing a new persistence model is deliberate: this program's own governing discipline (`ADR-GOV-002`, borrowed from Domain Object Architecture Doctrine) treats complexity as something to be discovered through demonstrated necessity, never introduced speculatively — and a working, already-shipped precedent for this exact shape of problem already exists.

## Alternatives Considered

See Decision §6, above, for the specific rejected models and their individual grounds. No alternative was found that both satisfies the Daily Brief cross-session requirement and preserves `Decision`'s own immutability without introducing a new, dedicated object.

## Consequences

- `Decision`'s immutability, and every object that relies on it (`ReflectionResponse`, Security Confirmation, `ADR-CR-001`'s own supersession-by-derivation model), remains completely untouched.
- Imported, API-created, and broker-synced Decisions remain fully valid with zero draft involvement, per §5's own hard constraint.
- A future implementation effort may build `DecisionDraft` and its event stream directly against this ADR's own shape, without further ontology design being required first.
- `ADR-CR-001`'s own treatment of Reconsideration may reference `DecisionDraft` as one legitimate way a reconsideration begins, without requiring it.

## Invariants

- `DecisionDraft` itself is created once and never mutated; every change is a new event in its own stream.
- The commit boundary is always the existing, unmodified `Decision.register()`/`DecisionContext.capture()` calls; `DecisionDraft` never becomes a `Decision`.
- Any future `Decision`-side reference to a draft is optional and additive, never required.
- Daily Brief never receives full draft content, only the narrow projection in §4.

## Migration

None to existing code — no `DecisionDraft` object exists yet, and nothing currently implemented is altered by this ADR. A future implementation effort would build the object and its event stream against this ADR's own shape.

## Open Questions

- Whether a recorded-and-superseded draft is retained as provenance or discarded — not resolved.
- Whether "abandon" and "delete" are the same action for a `DecisionDraft`, or two distinct events — not resolved.
- Whether drafts should ever expire — not resolved.
- Whether multiple simultaneous drafts per Case should be permitted or capped at one — not resolved; evidence leans against a hard ontological cap, but this remains a product decision.
- Whether the Case-scoped-only model should be revisited before any future multi-user/collaboration capability is built — a disclosed, inherited limitation, not resolved here.
- Whether abandoned-draft events should be retained indefinitely at the storage layer even though never surfaced to the investor as part of their permanent memory — a genuine tension between auditability and the same privacy posture this codebase's own Companion design already chose (session continuity, not durable memory) — not resolved.
- Whether offline/mobile editing requires a local-first sync layer beyond this ADR's own synchronous shape — not resolved; no evidence was gathered on this question.
- The same conversion-path question raised in `ADR-DC-001`'s own Open Questions applies identically here.

## Related

`docs/ADR-Investigation-003-Decision-Drafts-vs-Immutable-Decision.md` (source investigation). `ADR-DC-001-Decision-Context.md` (the commit-boundary destination for draft content that becomes a real `DecisionContext`). `ADR-CR-001-Decision-Review-and-Supersession.md` (Reconsideration may begin as a `DecisionDraft`). `atlas/alpha/security_confirmation` (the direct, already-shipped precedent for §2's own persistence pattern). `ADR-GOV-001`, `ADR-GOV-002`, `ADR-GOV-003` (governing process).
