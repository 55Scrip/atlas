# ADR-GOV-003 — Investigation Lifecycle

**Status:** Accepted.
**Type:** Repository-level governance record — establishes the status, role, and conversion path of the ADR Investigation Series. Produced by the ADR Adoption Program, Sprint 3, converting recommendations approved in `Atlas-Governance-Adoption-Review.md` (Sprint 2). Depends on `ADR-GOV-001-Governance-Authority.md` and `ADR-GOV-002-Reconciliation-Process.md`.

---

## Problem

The ADR Investigation Series (`docs/ADR-Investigation-001` through `011`) has produced eleven substantive documents of real, evidence-grounded architectural reasoning, including proposed new ontology (Draft, `CaseCondition`, Assumption) and a detailed self-examination of its own nature. No prior document established what an Investigation actually is, what it is allowed to do, when it is complete, whether it is permanent, or how — if at all — its findings become architecture.

## Context

`Investigation-010` first identified that the Series had, in practice, become a fourth architectural track without ever having been named as one. `Investigation-011` tested this directly against the Series' own actual, empirically-verified behavior (confirmed by direct inspection of all ten prior documents, not assumption) and found: every Investigation uniformly declares itself "Investigation only"; none has ever claimed Final, binding, or normative status for itself; every ADR Candidate section is labeled "Outline Only"; no Investigation has ever been deleted, only refined by a later one; and every genuine contradiction found is documented, never silently resolved by the Investigation that finds it. This ADR converts the investigation-lifecycle recommendations approved in Sprint 2 (`INV11-R1` through `INV11-R6`, `INV11-R8`, `INV11-R9`, all marked Adopt, and the paired `INV10-R7`/`INV11-R8` resolution, marked Adopt with Modification) into normative architecture.

The status model in Decision §2, specifically, is new operational structure produced during this conversion, not a verbatim restatement of a single approved recommendation — it synthesizes `INV11-R1`'s general claim that the Series has its own lifecycle with `Investigation-011`'s own Phase 10 completion criterion (a central question answered, alternatives tested, contradictions disclosed, an outline produced). Recorded here explicitly, consistent with this program's own principle that a recommendation's conversion into followable architecture is legitimate drafting work, but must be disclosed as such rather than presented as if directly approved verbatim. §7's traceability requirement is, similarly, a codification of already-uniform practice documented in `Investigation-011` Phase 6 and in `Atlas-Recommendation-Register.md`'s own "Method note," rather than a separately-numbered `INV11-R` item.

## Decision

1. **An Investigation is a research-grade recommendation document.** It is argued with the same evidentiary rigor architecture requires — evidence tested, alternatives rejected with stated reasons, contradictions disclosed rather than hidden — but it never itself claims Final, binding, or normative status. This is not a limitation imposed on Investigations from outside; it is what distinguishes an Investigation from an ADR.
2. **At any point in time, an Investigation is described by the applicable subset of the following tags** — these are independently-trackable facts about a document's own history, not a single, mutually-exclusive value a document holds one of at a time:
   - **Open** — under active investigation; applies only before the document reaches its own stated central question's answer, and no longer applies once it does.
   - **Complete** — its own central question has been answered with a single, justified verdict; every tested alternative carries a stated reason for rejection; every genuine contradiction or open question found is named explicitly; an ADR-candidate outline has been produced. An Investigation is Complete or Open, never both, and every Investigation transitions from Open to Complete at most once.
   - **Converted** — at least one of its recommendations has been formally adopted through the conversion process in §4, below. This tag applies *in addition to* Complete (an Investigation must be Complete before any of its recommendations can be converted) and does not remove the Complete tag when it is added.
   - **Superseded** — a later Investigation or ADR reached a different, better-evidenced conclusion on the same narrow question. This tag applies *in addition to* whichever of Complete/Converted already held, and does not remove them — it records that a later document now governs the specific question, not that this document ceased to be what it always was.

   Concretely: a document is always exactly one of Open or Complete; independently, once Complete, it may additionally be Converted (in whole or in part); independently again, it may additionally, later, be marked Superseded on the specific point a later document addresses. The document's own content is never rewritten to reflect any of these transitions — only its recorded status changes.
3. **The Investigation Series is not a fourth peer-authority architectural track** alongside implementation, Reasoning Foundations, and Domain Object Architecture (as those three are established in `ADR-GOV-001`). It is advisory ADR-precursor input to those tracks and to implementation. This directly resolves the open question `Investigation-010` raised and `Investigation-011` answered: the Series observes and advises; it does not govern, replace, or reconcile on its own authority.
4. **An Investigation's findings become architecture only through conversion** — a separate, later act performed under an authorized track's own governing process: an engineering effort for implementation; Reasoning Foundations' own Draft/Final ADR discipline for that track; Domain Object Architecture's own OE-series and Change Protocol for that track; or, for governance itself, an `ADR-GOV-NNN` document such as this one. An Investigation never self-converts. Its continued existence as a committed, readable file never itself confers normative status, exactly as `ADR-GOV-001` §4 already establishes generally, applied here specifically to Investigations.
5. **Every ADR Candidate section within an Investigation MUST remain labeled an outline** — a handoff artifact prepared for whoever eventually performs conversion, never presented, and never to be mistaken for, the ADR itself.
6. **No Investigation is ever deleted.** A later Investigation or ADR that reaches a different, better-evidenced conclusion on the same narrow question supersedes the earlier one explicitly, per `ADR-GOV-002` §5 — the earlier document's status is marked Superseded, the superseding document is named, and the original text remains fully intact and readable. §2's Superseded *tag*, above, is the Investigation-specific application of this same rule; it is not a second, independent supersession mechanism. It is distinct from `ADR-GOV-002` §6's own Draft/Final/Superseded/Historical vocabulary, which describes documents generally (including ADRs and OEs) rather than Investigations specifically — the two vocabularies share the "Superseded" value because both describe the same underlying event, but an Investigation is never itself "Final" in `ADR-GOV-002` §6's sense, since §1, above, already establishes that no Investigation claims that status.
7. **Every Investigation, and every recommendation extracted from it, must remain traceable** — citing the specific document, phase, and evidence relied upon, and stating explicitly what it depends on and what depends on it, exactly as the Series has already, consistently practiced across Investigations 001–011 and as recorded in `Atlas-Recommendation-Register.md`.

## Rationale

Every provision above states, formally, what the Series was already doing — `Investigation-011`'s own empirical verification (direct inspection, not recollection) found zero deviation from this model across all ten prior documents. This ADR does not impose a new constraint on the Series' own working method; it converts an already-uniform practice into a citable, normative reference, so future Investigations and future adopters no longer need to re-derive the Series' own authority from first principles each time, as `Investigation-011` itself had to.

## Alternatives Considered

- **Research only.** Rejected — undersells the decisive, single-verdict structure every Investigation actually reaches, and the ADR-candidate outlines every one actually produces; a purely exploratory characterization does not match the observed practice.
- **Architecture authority.** Rejected — directly falsified by the empirical record: zero of eleven Investigations has ever claimed binding status for itself.
- **Independent reconciliation track.** Rejected — overstates what Investigations have ever actually completed; `Investigation-009`/`010` could name and analyze cross-track disagreement, but neither could or did complete an actual reconciliation on its own authority.
- **Living archive alone.** Rejected as incomplete, not wrong — correctly captures that Investigations are permanent and never deleted, but says nothing about their forward-looking, decision-directed function, which every Investigation also demonstrably has.
- **Temporary working documents.** Rejected — directly contradicted by the Series' own practice: nothing in the Series has ever been deleted, even where later work substantially refined an earlier finding.

## Consequences

- Investigations 001–011 remain exactly as valid, and exactly as written, as before this ADR — nothing is rewritten. Their status should be recorded as Complete going forward, as a matter of bookkeeping, not as a change to their content.
- Future ontology proposals already produced by the Series — Draft (`Investigation-003`), `CaseCondition` (`Investigation-005`/`006`), and Assumption (`Investigation-007`/`008`) — may now be formally converted via §4's own process, referencing this ADR for how conversion works, rather than each requiring its own justification for why an Investigation's conclusion may be relied upon at all.
- Any future Investigation, from this point forward, is understood by default to carry the status model in §2 and the conversion path in §4, without needing to restate either.
- Future governance work may cite this ADR directly for "what is an Investigation allowed to do," in place of re-deriving the answer from the Series' own self-examination each time.

## Invariants

- No Investigation claims Final, binding, or normative status for itself.
- Every ADR Candidate section remains labeled an outline, never presented as the ADR itself.
- No Investigation is ever deleted; supersession is always explicit, per `ADR-GOV-002` §5.
- Conversion into architecture always requires a separate, authorized track's own process — never self-conversion, never mere continued existence as a file.
- Every Investigation and every extracted recommendation remains traceable to its specific source and evidence.

## Migration

None required to the content of the existing eleven Investigation documents. Their status should be recorded as Complete under §2's model as a bookkeeping matter; this ADR does not perform that recording itself, and no existing file requires editing to comply.

## Open Questions

How a genuine future contradiction *between two Investigations* (as opposed to between a track and implementation, which `ADR-GOV-002` already covers) would be adjudicated remains open. `Investigation-011`'s own proposed mechanism — a third, later Investigation that directly re-tests the disputed claim — was not adopted in Sprint 2 (it was marked Defer, as explicitly untested in practice, since no genuine Investigation-to-Investigation contradiction has yet occurred) and is accordingly out of this ADR's own scope. Who specifically initiates conversion for any given Investigation's recommendation is likewise not assigned by this ADR, consistent with `ADR-GOV-002` §3's own open, non-office-bound initiation model.

## Related

`ADR-GOV-001-Governance-Authority.md` (establishes the general no-self-conversion principle this ADR applies specifically to Investigations). `ADR-GOV-002-Reconciliation-Process.md` (supersession, §5, and historical-status vocabulary, §6, both referenced directly in this document's §2 and §6). `docs/ADR-Investigation-010-Ontology-Reconciliation-Process.md` and `docs/ADR-Investigation-011-Authority-of-the-ADR-Investigation-Series.md` (source investigations). `Atlas-Recommendation-Register.md` and `Atlas-Governance-Adoption-Review.md` (the Sprint 1/2 documents this ADR's own recommendations were drawn from).
