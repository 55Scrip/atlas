# ADR-DC-001 — Decision Context

**Status:** Accepted. Validated per `docs/ADR-DC-001-Validation-Report.md` (Accept with Changes; changes incorporated).
**Type:** Ontology ADR — Atlas Core, Decision Workspace domain. Produced by the ADR Adoption Program, Sprint 5 (Wave 1), converting recommendations from `docs/ADR-Investigation-001-Decision-vs-DecisionContext.md` and `docs/ADR-Investigation-002-DecisionContext-vs-ReflectionResponse.md`, following the process established by `ADR-GOV-001`, `ADR-GOV-002`, `ADR-GOV-003`.

---

## Problem

UX-009 requires the Decision Workspace to capture richer decision-time context — the circumstances an investor believed mattered, alternatives they weighed, and uncertainties they held — than the minimal, immutable `Decision` aggregate is designed to hold. A separate object, `DecisionContext`, already exists in the implemented codebase for exactly this purpose, but is unwired to Alpha, and its relationship to a second, structurally similar object, `ReflectionResponse`, has never been formally settled.

## Context

`Decision` (`atlas/core/domain/decision/entity.py`) is deliberately minimal — five required fields, no narrative beyond a single `reason` string — so that every source of a Decision (manual entry, import, broker sync, API) remains valid regardless of whether richer context is ever supplied. `DecisionContext` (`atlas/core/domain/decision_context/entity.py`) already exists as a separate, fully persisted, application-layer-supported aggregate — `situation`, `portfolio_relevance`, `capital_considerations`, `alternatives_considered`, `uncertainties` — capped at one per `Decision`, both by application-layer check and SQL `unique` constraint. `ReflectionResponse` (`atlas/core/domain/reflection_response/entity.py`) is a second, structurally similar object — also `decision_id`-anchored, also investor-authored-only, also immutable — but occasioned by a specific, prior Atlas computation (a recognized behavioral pattern and coaching question), unlike `DecisionContext`, which requires no such occasion.

`Investigation-001` tested whether `DecisionContext` is already the correct home for UX-009's richer content and found `PARTIAL_REUSE`: correct for investor-authored qualitative context, never for Atlas-generated content or anything with a post-recording lifecycle. `Investigation-002` tested `DecisionContext` against `ReflectionResponse` directly — attempting to merge them in both directions and finding the merge fails each way — and established the precise, load-bearing distinction between them: whether an Atlas computation occasioned the content.

## Decision

1. **`DecisionContext`'s current field set is confirmed correct and sufficient.** No field is added or removed by this ADR. Its five existing fields remain the complete, correct home for investor-authored, decision-time circumstantial narrative.
2. **`DecisionContext` MUST NOT absorb Atlas-generated content, per-item acknowledgment records, or anything with a lifecycle after Decision recording.** These require separate objects, outside this ADR's own scope.
3. **The governing test for routing any future Decision Workspace content between `DecisionContext` and `ReflectionResponse` is whether an Atlas computation occasioned it:** `DecisionContext` holds content requiring no prior Atlas computation (investor-initiated); `ReflectionResponse` holds content that exists only because Atlas first computed something specific to react to (Atlas-occasioned). This test governs, and is not limited to, these two objects specifically — any future object proposed for similar content must be tested against it first.
4. **`DecisionContext` and `ReflectionResponse` MUST NOT be merged, in either direction.** A direct merge attempt fails both ways: forcing `ReflectionResponse`'s content into `DecisionContext`'s shape produces a permanently-null provenance field on unoccasioned rows; forcing `DecisionContext`'s content into `ReflectionResponse`'s shape requires fabricating an occasion (a coaching question and pattern) that never existed.
5. **A common-parent object unifying `DecisionContext`, `ReflectionResponse`, and any future similarly-shaped object is not adopted by this ADR.** It is recorded as a legitimate idea for a future, separately-scoped ADR, to be revisited only once a third occasioned-or-spontaneous object is itself adopted (see `ADR-DD-001`, which references this possibility).

### Implementation Note (non-binding)

`DecisionContext` could be exposed to Alpha via a new API endpoint over the existing, unmodified `capture_decision_context.py` application service — wiring only, no domain change. This note names a direction consistent with §1's own conclusion; it is not itself a Decision point of this ADR, is not required for this ADR's own adoption, and is not performed by this ADR. Whether and when to build it is an implementation-planning question for a future, separately-scoped effort.

## Rationale

`DecisionContext` and `ReflectionResponse` were each independently tested against every other object in the codebase before being tested against each other, and both survived — the remaining question was only whether they should be treated as one thing or two. The occasioned/unoccasioned test (Decision §4) is adopted as the governing rule because it is the only distinction found that is structural, not merely stylistic: it tracks a real difference in what each object's own existence *depends on* (a prior Atlas computation, or nothing), not an accident of field naming. Declining the common-parent option (§6) follows this program's own established discipline against introducing structure before a demonstrated second instance exists — one confirmed pair does not yet justify a generalized abstraction.

## Alternatives Considered

- **Merge `DecisionContext` into `ReflectionResponse`.** Rejected — every unoccasioned row would carry a permanently-null provenance field, the textbook sign of two aggregates forced together.
- **Merge `ReflectionResponse` into `DecisionContext`.** Rejected, more severely — requires fabricating a coaching-question provenance record for content that was never prompted, a direct violation of this program's own no-fabrication principle.
- **Absorb Atlas-generated or lifecycle-bearing content into `DecisionContext` directly**, rather than routing it elsewhere. Rejected — contradicts `DecisionContext`'s own design rationale (investor-only, captured once, no lifecycle) and would require it to do work its own invariants were never built to support.
- **Adopt a common-parent object now.** Rejected as premature — no second occasioned-or-unoccasioned pair beyond this one currently exists to generalize from.

## Consequences

- Future Decision Workspace implementation work has a single, precise test (§4) for where new content belongs, rather than needing to re-derive the distinction case by case.
- `DecisionContext` remains unwired to Alpha until a future implementation effort (§2) adds the endpoint — this ADR does not change current behavior.
- `ADR-DD-001` (Decision Draft) may reference `DecisionContext` as the eventual destination for draft content that becomes real, per its own commit-boundary rule.

## Invariants

- `DecisionContext` content is always investor-authored; Atlas never originates its content, only proposes candidate text a la `ADR-002` C-02's own authorship model.
- At most one `DecisionContext` per `Decision`, enforced at both the application and schema layers.
- A `DecisionContext` requires an already-existing `Decision`; it can never precede or be orphaned from one.
- The occasioned/unoccasioned test (§4) governs all future routing decisions between `DecisionContext`-shaped and `ReflectionResponse`-shaped content, not only the two objects that motivated it.

## Migration

None to existing code — `DecisionContext` and `ReflectionResponse` are unmodified by this ADR. A future, separately-scoped implementation effort would add the API endpoint authorized in §2; this ADR does not perform that work.

## Open Questions

- Whether `DecisionContext`'s own `portfolio_relevance` field name should eventually be clarified or renamed, given its risk of being misread as Atlas-computed data — not resolved here.
- Future UI copy must keep `Decision.reason` visibly distinct from `DecisionContext.situation`/`capital_considerations`, and `DecisionContext.uncertainties` visibly distinct from any future `ReflectionResponse` surface — a design-discipline requirement this ADR names but does not itself enforce.
- Whether the ADR Adoption Program's own production process is itself one of the "authorized track" conversion paths `ADR-GOV-003` §4 names (implementation, Reasoning Foundations, Domain Object Architecture, or a governance ADR) is not settled by `ADR-GOV-003` itself for *ontology* ADRs specifically. This ADR is produced under that Program's own established discipline by direct instruction; whether that constitutes a fourth, ontology-specific conversion path, or should instead be understood as an implementation-track effort performed through this Program, is left open pending a future governance clarification.

## Related

`docs/ADR-Investigation-001-Decision-vs-DecisionContext.md`, `docs/ADR-Investigation-002-DecisionContext-vs-ReflectionResponse.md` (source investigations). `ADR-GOV-001`, `ADR-GOV-002`, `ADR-GOV-003` (governing process). `ADR-002-Critical-UX-Architecture-Resolutions.md` C-02 (authorship model reused in §2/Invariants). `ADR-DD-001-Decision-Draft.md` (references this ADR's own commit-boundary relationship to `DecisionContext`).
