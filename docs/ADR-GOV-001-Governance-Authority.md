# ADR-GOV-001 — Governance Authority

**Status:** Accepted.
**Type:** Repository-level governance record — establishes cross-track architectural authority. Produced by the ADR Adoption Program, Sprint 3, converting recommendations approved in `Atlas-Governance-Adoption-Review.md` (Sprint 2). Follows the precedent of `ADR-005-Atlas-Reasoning-Foundations-Naming-and-Authority.md`.

---

## Problem

Atlas Core currently contains three independently-governed architectural tracks — the implemented Core Loop (`atlas/core/`), Atlas Reasoning Foundations (`docs/atlas_reasoning_foundations/`), and Atlas Domain Object Architecture (`docs/atlas_domain_object_architecture/`) — plus a research program, the ADR Investigation Series, that has produced substantial architectural reasoning of its own. No prior document establishes which of these is authoritative for what, whether any governs the others, or how new architectural input may legitimately acquire normative status. One of the three tracks (Domain Object Architecture) explicitly claims authority over implementation in its own governing Doctrine; that claim has never been examined, accepted, or rejected anywhere.

## Context

`ADR-005` (Accepted) previously resolved a naming collision between `atlas/core/` and the original `docs/atlas_core/` (now Reasoning Foundations), and established that neither track governs, supersedes, or is presumed to converge with the other. It did not address Domain Object Architecture, which was not named in it and is not part of the track `ADR-005` renamed.

The ADR Investigation Series (`docs/ADR-Investigation-001` through `011`) subsequently found, and tested directly:

- The implemented `atlas/core/domain/*` object set is a strict superset of Domain Object Architecture's own closed, normative six-object set (`OE-002` §4), containing ten additional objects (Question, Interpretation, Hypothesis, Evidence, Conclusion, Evaluation, Learning, plus provisional bridge entities) with no counterpart in that closed set.
- Domain Object Architecture's own governing Doctrine states directly that it "governs the relationship between architecture and implementation," that "Repository facts MUST NOT be used to establish, confirm, or deny an ontological claim," and that "implementation planning MUST NOT silently introduce new ontology" — an explicit, assertive authority claim over implementation that no implementation-side document has ever accepted or rejected.
- A candidate three-layer hierarchy (Reasoning Foundations → Domain Object Model → Implementation) was tested directly against the evidence and does not survive contradiction: Domain Object Architecture's own definitions do not derive from, or cite, Reasoning Foundations' work, and neither track's authority claim over implementation has been shown to be accepted by implementation.

This ADR converts the governance-authority recommendations approved in Sprint 2 (`INV9-R1`, `INV9-R3`, `INV9-R4`, all marked Adopt) into normative architecture. Decision §4, specifically, additionally draws on `INV11-R6` (Adopt) — a recommendation about the Investigation Series specifically, generalized here into the cross-cutting authority-acquisition principle every other governance ADR in this program, including `ADR-GOV-003`, depends on.

## Decision

1. **The implemented `atlas/core/domain/*` object set, and the working system built upon it, is the operative authority for what currently exists and how it currently behaves.** This is a statement of practical fact, not a claim that implementation is ontologically self-justifying — see Invariants, below.
2. **Atlas Reasoning Foundations and Atlas Domain Object Architecture are each authoritative within their own, self-governed chains**, under their own respective Doctrines. Neither is, by this ADR, treated as automatically binding on implementation. This extends `ADR-005`'s own established treatment of Reasoning Foundations to Domain Object Architecture as well, which `ADR-005` never addressed.
3. **No hierarchy is adopted among these three tracks.** The candidate three-layer model (Reasoning Foundations above Domain Object Architecture above Implementation) is rejected outright — it does not describe how these tracks actually relate, and no document establishes a derivation relationship between any two of them.
4. **No document, investigation, or informal artifact acquires architectural authority merely by existing, being well-reasoned, being repeatedly cited, or being more recent than another.** Authority is conferred only by an authorized track's own governing process producing a document that explicitly claims normative status under that process's own rules. What counts, concretely, as such a process for each track, and how the Investigation Series specifically relates to it, is stated in `ADR-GOV-002` (the reconciliation process) and `ADR-GOV-003` (the Investigation Series' own conversion path) respectively — this ADR states the general principle; it does not itself enumerate every track's own procedure.
5. **This ADR does not alter any track's internal authority over its own domain** — Reasoning Foundations remains sole authority over its own ADR series; Domain Object Architecture remains sole authority over its own OE series, Doctrine, and Change Protocol. This ADR states only how the three tracks, and implementation, relate to one another from the outside.

## Rationale

Domain Object Architecture's own Doctrine makes a genuine, assertive authority claim implementation has never engaged with. Two responses were available: accept the claim (Domain Object Architecture becomes binding, and ten real, running, load-bearing implemented objects become unaccounted-for pending a reconciliation that does not yet exist), or decline it for now while leaving the door open (implementation continues as the practical authority for its own behavior, and any future claim of governance requires its own explicit act, following `ADR-GOV-002`). The second was chosen because the first would retroactively destabilize working architecture without the Change Protocol Domain Object Architecture's own Doctrine requires for exactly this kind of change ever having been run. `ADR-005`'s own precedent — declining Reasoning Foundations' potential claim over implementation without rejecting Reasoning Foundations' work — is the direct model for this decision, extended here to a second track making a stronger claim.

## Alternatives Considered

- **Domain Object Architecture is unilaterally normative over implementation.** Rejected — implementation impact is severe (ten objects with no accounting), and Domain Object Architecture's own Change Protocol (`Doctrine.md` §13) was never run to reach this outcome; adopting it by ADR fiat rather than by that Protocol would itself violate the Doctrine it claims to follow.
- **Reasoning Foundations governs all ontology, including implementation.** Rejected — explicitly foreclosed by `ADR-005`, and Reasoning Foundations has no counterpart for the majority of implemented objects.
- **A three-layer hierarchy, each track owning a distinct abstraction level.** Rejected — tested directly and does not survive contradiction; the tracks do not in fact derive from one another.
- **Leave the current, undisclosed state as it was.** Rejected — leaves a live, real contradiction (Domain Object Architecture's own closure claim vs. implementation's actual object set) unacknowledged, which this ADR exists specifically to avoid.

## Consequences

- Implementation continues, unimpeded, exactly as it currently operates.
- Reasoning Foundations and Domain Object Architecture continue their own internal work, unimpeded, under their own Doctrines.
- Any future desire to make either track's ontology binding over implementation requires a dedicated reconciliation under `ADR-GOV-002`, producing its own historical decision record — this ADR neither authorizes nor forecloses that outcome; it states only that it has not yet happened.
- Future architectural work — ontology proposals, implementation designs, or further governance work — may cite this ADR directly for "which track governs what," rather than re-deriving the three-track relationship from the Investigation Series each time.

## Invariants

- No track's authority extends beyond its own defined governing chain without an explicit ADR stating otherwise.
- Architectural authority is never conferred by mere existence, repetition, or persuasiveness of a document, nor by its recency or its location in the repository.
- Implementation facts may inform architectural and migration planning; they do not, by themselves, establish or deny an ontological claim.
- Any future claim that one track governs another, or that implementation must conform to a specific track's ontology, requires its own dedicated ADR under `ADR-GOV-002`'s reconciliation process.

## Migration

None. No existing tracked document requires modification. This ADR is purely additive; it formalizes a relationship the Investigation Series had already, in practice, been operating under.

## Open Questions

Whether Reasoning Foundations and Domain Object Architecture themselves accept the relationship this ADR describes has not been, and cannot unilaterally be, confirmed by this document. This ADR states Atlas Core's own operating posture; it does not, and cannot, bind another track's own independent governance to agree with it. This remains open pending any future, separate response from either track.

## Related

`ADR-005-Atlas-Reasoning-Foundations-Naming-and-Authority.md` (direct precedent). `ADR-GOV-002-Reconciliation-Process.md` (the process by which any future change to the relationship stated here would be reached). `ADR-GOV-003-Investigation-Lifecycle.md` (applies this ADR's §4 principle specifically to the Investigation Series). `docs/ADR-Investigation-009-Ontology-Authority-and-Reconciliation.md` (source investigation).
