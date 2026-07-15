# Atlas Core Development Doctrine

**Status:** Normative. This document governs *how* Atlas Core is developed. It does not define what Atlas Core's concepts are — that is the province of individual ADRs — but it fixes the discipline every ADR must follow, and the discipline that governs the transition from ontology to architecture to implementation.

---

## Purpose

Atlas Core is built by first establishing what things *are* before deciding how they are structured, and by deciding how they are structured before writing any code that implements them. This document exists to make that discipline explicit, permanent, and binding, so that Atlas Core's foundations remain sound as the system grows in scope and complexity. Every contributor to Atlas Core — human or otherwise — is bound by this doctrine when authoring an ADR, designing an architecture, or writing implementation code.

## Core Philosophy

Rigor precedes speed. Complexity must be discovered through argument, never introduced for convenience or anticipated future need. Every concept admitted into Atlas Core's ontology must earn its place by surviving deliberate attempts to falsify it — it does not earn its place merely by being plausible, useful, or easy to implement. Where a genuine contradiction or a genuinely open question is found, it is recorded and left open rather than papered over. An honest, incomplete doctrine is preferable to a complete one that conceals an unresolved tension.

## First Principles

Every ontological question addressed in Atlas Core is reasoned from first principles: from the nature of the thing itself, not from analogy to an existing system, from precedent, or from implementation convenience. Reasoning by analogy may suggest a candidate worth testing, but a candidate is never accepted merely because something similar worked elsewhere — it must be independently argued for on its own terms, against the specific concepts it is meant to relate to.

## Falsification

No candidate definition, principle, or architectural claim is accepted on its initial plausibility. Each must be subjected to genuine attempts to break it: alternative candidates must be considered, contradictions with already-established doctrine must be actively sought, and edge cases must be examined rather than assumed away. A definition earns acceptance by surviving falsification attempts, not by being the first idea proposed. Where falsification succeeds, the candidate is rejected or revised; where it is inconclusive, the resulting uncertainty is recorded, not hidden.

## Ontology Before Architecture

What a thing *is* must be settled before any decision is made about how it is structured, represented, related to other things, or organized into components. Architecture built atop an unsettled ontology risks encoding confusion into structure that is far more costly to unwind later than an unresolved question is to leave open now. No ADR may be treated as a basis for architectural work while it contains a contradiction presented as resolved.

## Architecture Before Implementation

Once ontology is settled, architecture — the shape of components, their responsibilities, and their relationships — must be decided before implementation begins. No code is written against an ontological question that has not yet reached a stable answer, and no architecture is implemented before it has itself been reasoned through and recorded. This mirrors, at the level of engineering process, the same discipline applied to individual concepts: understand fully, then commit.

## One Primitive per ADR

Each ADR introduces and settles exactly one new ontological primitive. An ADR that attempts to settle several primitives at once makes it impossible to test any one of them properly — falsification attempts against one candidate become entangled with unrelated candidates, and contradictions become harder to locate and attribute. Where a document surfaces the need for an additional primitive in the course of answering its own question, that further primitive is named as an open dependency and deferred to its own, later ADR — never resolved inline.

## Primitive Discovery Test

Before a new primitive is admitted into Atlas Core's ontology, it must pass a discovery test: is this genuinely a distinct kind of thing, not reducible to, and not already covered by, an existing primitive? A primitive that fails this test — that turns out to be an existing concept restated under a new name, or a property of an existing concept rather than a concept of its own — is not admitted, regardless of how convenient a separate name for it might be. This test is applied the same way falsification is applied to definitions: by attempting to reduce the candidate primitive to what already exists, and admitting it only if that attempt genuinely fails.

## Complexity Must Be Discovered, Never Introduced

Complexity is added to Atlas Core's ontology, architecture, or implementation only when a specific, demonstrated contradiction or necessity forces it. It is never introduced speculatively, for a need that is merely anticipated, for symmetry with an unrelated part of the system, or for convenience. Where a simpler account is sufficient to avoid contradiction, the simpler account is preferred, even if a more elaborate one seems more complete or more future-proof.

## Explicit Dependency Graph

Every ADR states explicitly what it depends on — which prior ADRs and primitives it presupposes and builds upon — and, as later ADRs are written, what depends on it. No dependency is left implicit or assumed from context. Where an ADR relies on a concept that has not yet been the subject of its own ADR, that reliance is named explicitly as an open, unresolved dependency, not silently used as though it were already settled.

## Traceability

Every architectural decision and every implementation choice must be traceable back to the specific ADR — and within it, the specific argument — that justifies it. A decision with no documented lineage back to first-principles reasoning has no standing in Atlas Core, regardless of how reasonable it may appear in isolation.

## Every Layer Should Make the Next Layer Inevitable

Ontology, architecture, and implementation are developed as successive layers, each resting on the one before it. A layer is not yet complete if the layer above it still requires arbitrary choices that do not follow from what has already been established — if the next layer does not feel inevitable given the current one, the current one has not yet been reasoned through with sufficient rigor, and work should return to it rather than proceed past it.

## Standard ADR Structure

Every ADR — whether Draft or Final — follows the same structure:

- **Question** — the single question this ADR exists to answer.
- **Motivation** — why this question must be answered now, and what depends on the answer.
- **First Principles** — what is already established and fixed, which this ADR must remain consistent with or explicitly flag tension against.
- **Candidate Definitions** — the alternative accounts considered.
- **Falsification Attempts** — the deliberate attempts made to break each candidate.
- **Contradictions Found** — any genuine tension surfaced, whether within this ADR or against prior ADRs, recorded rather than resolved if resolution is not yet earned.
- **Current Best Definition** — the definition currently adopted, marked according to the ADR's status.
- **Dependency Graph** — what this ADR depends on, and what it introduces as a dependency for later work.
- **Architectural Consequences** — what would follow, architecturally, if the current best definition is retained; held tentatively while the ADR remains a Draft.
- **Remaining Open Questions** — what this ADR does not settle, stated explicitly rather than left to be inferred from silence.

An ADR carries a status of **Draft** or **Final**. A Draft may contain unresolved contradictions and open questions; a Final ADR may not, and its promotion from Draft to Final is itself governed by the Acceptance Criteria and Definition of Done below.

## Acceptance Criteria

An ADR — of any status — is acceptable for inclusion in Atlas Core's doctrine only if:

- every candidate definition it considers was genuinely tested by falsification, not merely listed;
- every contradiction it surfaces, against itself or against a prior ADR, is stated explicitly rather than silently resolved or omitted;
- it introduces at most one new primitive, per One Primitive per ADR;
- its dependencies — settled and open — are stated explicitly;
- it contains no implementation detail, and no claim about mechanism;
- its status (Draft or Final) is stated and accurately reflects whether open questions or contradictions remain.

## Definition of Done

An ADR is Done — eligible for Final status — only when:

- it contains no unresolved contradiction with itself;
- it contains no unresolved contradiction with any other Final ADR (a contradiction with a Draft ADR is recorded, not treated as blocking, since the Draft itself remains open to revision);
- every open question it once carried has either been genuinely resolved by argument or been explicitly and knowingly carried forward as a stated, permanent boundary rather than a mere omission;
- its dependency graph is confirmed consistent with the dependency graphs of every ADR it depends on or is depended upon by;
- it has been reviewed and approved against this doctrine.

A Draft ADR is never treated as Done merely because it is well-written or currently the best available account — it is Done only when the above criteria are actually met.
