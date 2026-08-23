# ADR-GOV-002 — Reconciliation Process

**Status:** Accepted.
**Type:** Repository-level governance record — establishes the general process by which disagreement between architectural tracks, or between a track and implementation, is reconciled. Produced by the ADR Adoption Program, Sprint 3, converting recommendations approved in `Atlas-Governance-Adoption-Review.md` (Sprint 2). Depends on `ADR-GOV-001-Governance-Authority.md`.

---

## Problem

`ADR-GOV-001` establishes that Atlas Core's architectural tracks are independently governed and that none currently governs another. This leaves open a real, practical question: when two tracks — or a track and implementation — genuinely disagree, what happens next? Before this ADR, exactly one precedent existed (`ADR-005`, a single pairwise resolution) and no general, repeatable process for reaching one.

## Context

The ADR Investigation Series tested this question directly (`docs/ADR-Investigation-010`) and found: (1) Domain Object Architecture's own Doctrine already contains well-designed elements usable for exactly this purpose — a forcing-function requirement for reopening settled decisions (§8), a formal supersession/historical-status vocabulary (§14), and historical-integrity guarantees (§11) — each separable from, and adoptable independent of, that Doctrine's own specific ontological content. This ADR reuses those three elements specifically; it does not adopt the full nine-step Change Protocol (§13) that document also defines, since that Protocol's remaining steps (upstream/downstream document amendment, navigational alignment, repository inspection, migration planning, implementation) presuppose a single governing chain this cross-track process does not have; (2) `ADR-005` itself is a real, working example of a complete reconciliation whose only output was a declared-authority relationship, with neither side's content changing at all; (3) most apparent cross-track disagreement, on close inspection, is omission or an alternative model, not a genuine contradiction — a precise distinction worth fixing before any reconciliation process is invoked, to avoid treating ordinary gaps in coverage as urgent conflicts.

This ADR converts the reconciliation-process recommendations approved in Sprint 2 (`INV10-R1` through `INV10-R6`, five marked Adopt and one — `INV10-R1` itself — marked Adopt with Modification) into normative architecture. The modification Sprint 2 required — concrete forcing-function criteria and a named initiation mechanism, rather than an abstract principle and an unassigned "someone, eventually" — is resolved directly in the Decision below, not left as a further open question.

## Decision

1. **Reconciliation between two architectural tracks, or between a track and implementation, MAY be undertaken only upon a genuine forcing function.** A forcing function is one of:
   - a newly identified domain fact that the current, disagreeing models cannot jointly represent;
   - an unavoidable, demonstrated contradiction between two claims both currently claiming settled status about the same fact (see Interpretive Guidance, below, for the precise test);
   - a downstream task — an implementation effort, a new ontology proposal, or a further investigation — that exposes a real, demonstrated expressive gap traceable to the disagreement;
   - evidence that an original investigation or decision omitted a materially distinct candidate, or misapplied its own governing method.
2. **The following do NOT, by themselves, constitute a forcing function:** documentary convenience; implementation inconvenience; naming preference; ordinary-language familiarity; a desire for structural symmetry; speculative future usefulness; the mere existence of legacy code or a legacy document; disagreement unaccompanied by new evidence.
3. **Reconciliation MAY be initiated by any contributor who identifies a satisfied forcing function and states it explicitly**, naming the forcing function invoked, the specific claim being challenged, and the narrowest scope of reconsideration required to address it. Initiation is not restricted to a designated role or standing office — none currently exists in Atlas Core's governance, and this ADR does not create one. This directly resolves Sprint 2's own flagged gap: the process is self-triggering by evidence, not gated on an unnamed owner.
4. **A reconciliation's minimum sufficient output is a documented decision** — a historical decision record stating what was decided, which tracks or documents were involved, the alternatives considered, and the grounds for the outcome. Reconciliation does NOT require either side's actual content to change. A mutual, explicit "these remain separately governed, by declared agreement" outcome — exactly what `ADR-005` already demonstrates — is a complete and sufficient result on its own.
5. **Supersession of a normative claim requires an identified replacing decision and an explicit status change** on the superseded document or claim (to Superseded, per the vocabulary in §6). A superseded document is never deleted, never edited to remove its original content, and never silently treated as though it had not existed. Supersession is never triggered by recency alone — a newer document existing is not, by itself, evidence that it supersedes an older one.
6. **Status vocabulary for any document produced or affected under this process:** Draft (under active work, not yet a stable basis for dependent work), Final (normatively adopted within its own stated scope — not a claim that every internal question is resolved), Superseded (no longer the current norm, replaced by an identified later decision, but remaining a true historical record of what was once adopted), Historical (preserved as a record of a past decision, not currently normative, never cited as a statement of current architecture). This is a *document*-level vocabulary, distinct from `ADR-GOV-003` §2's own Investigation-*lifecycle* vocabulary (Open/Complete/Converted/Superseded) — the two share the "Superseded" value because both describe the same underlying event (an identified later decision replacing an earlier one), but are not otherwise interchangeable: an Investigation's own status is governed by `ADR-GOV-003`, not by this section directly.
7. **Every document produced under this process, and every alternative it considered and rejected, must remain permanently recoverable.** A historical record is never a competing source of current truth, and it is never erased.

### Interpretive Guidance — Distinguishing a Contradiction from an Omission or Alternative Model

The following is guidance for applying §1's forcing-function test, not an independent obligation of its own. A **contradiction**, for the purpose of triggering reconciliation, is precisely defined: two claims that both currently claim settled status about the same fact and cannot both be true. This is distinguished from:

- an **omission** — a track simply never having addressed a concept, asserting nothing that conflicts;
- an **alternative model** — two tracks addressing the same question with different, internally coherent, non-merged accounts, neither shown false;
- **incomplete work** — a Draft-status or equivalently provisional document, which discloses its own non-bindingness by its own status;
- **implementation lag** — a settled decision published before implementation catches up, which every track's own governing material already anticipates as ordinary, not exceptional.

Only a genuine contradiction, in this precise sense, satisfies the "unavoidable, demonstrated contradiction" branch of §1's own forcing-function test. Omissions and alternative models may be documented and left as disclosed, coexisting differences without triggering this process — treating every such difference as requiring reconciliation would invoke this ADR's own process far more often than genuinely necessary.

## Rationale

The forcing-function requirement (§1–2) exists to prevent reconciliation from being triggered by preference, convenience, or mere disagreement — consistent with Atlas Core's own repeated, cross-track principle that complexity and change must be discovered through demonstrated necessity, never introduced speculatively. Making initiation open rather than office-bound (§3) resolves the concrete gap Sprint 2 identified without inventing a new governance role this ADR has no independent justification for creating. Setting the minimum viable output at a documented decision, not a content merge (§4), is directly evidenced by `ADR-005` already having worked exactly this way — this ADR generalizes a proven pattern rather than proposing an untested one. The precise contradiction/omission/alternative-model distinction (Interpretive Guidance, below) exists because the Investigation Series found most apparent cross-track disagreement is not, on close inspection, a true contradiction — without this distinction, the process risks being invoked far more often than genuinely necessary.

## Alternatives Considered

- **Implementation wins unconditionally.** Rejected — permanently devalues real, rigorous work in the other tracks and forecloses any future value from Domain Object Architecture's or Reasoning Foundations' own reasoning, including for future automated-reasoning capability where that reasoning may become more, not less, relevant.
- **Ontology wins unconditionally.** Rejected — would retroactively invalidate ten real, running implemented objects with no reconciliation ever having occurred, violating the same historical-integrity principle this ADR itself adopts (§7).
- **Newest document wins.** Rejected — directly contrary to the single-source-of-truth principle already established in Domain Object Architecture's own Doctrine, which this ADR's §5 makes generally applicable: authority is never a function of recency.
- **Living architecture with no reconciliation discipline.** Rejected — this is close to how implementation has actually evolved, but alone, with no process, it is exactly the condition that let the implementation/Domain-Object-Architecture disagreement go unnamed for nine prior investigations before being surfaced.
- **Independent parallel tracks with no reconciliation process at all.** Rejected as a permanent posture — legitimate only when disclosed, which requires a process to disclose it through; this ADR is that process.

## Consequences

- Any future reconciliation between implementation and Domain Object Architecture — named but not performed by `Investigation-009`/`010` — would use this exact process once a forcing function is identified and stated.
- No existing document needs to change to comply with this ADR, since none currently claims a completed reconciliation this process would invalidate.
- Future investigations, ADRs, or implementation efforts that discover a genuine cross-track disagreement now have a named, concrete procedure to invoke, rather than needing to design one from scratch each time.
- The contradiction/omission/alternative-model distinction (Interpretive Guidance) becomes the standard test any future governance work should apply before escalating a disagreement.

## Invariants

- Reconciliation requires a stated, genuine forcing function; the excluded categories in §2 never qualify on their own.
- Reconciliation's minimum output is always a historical decision record; content change on either side is a possible, not a required, outcome.
- Supersession always requires an identified replacing decision and an explicit status change — never silent, never by recency alone.
- No document produced or superseded under this process is ever deleted; historical recoverability is permanent.
- The contradiction/omission/alternative-model distinction (Interpretive Guidance) governs whether this process is invoked at all.

## Migration

None. No existing document requires modification under this ADR.

## Open Questions

Whether, and when, any specific reconciliation (for example, between implementation and Domain Object Architecture, per `ADR-GOV-001`'s own Open Question) is actually undertaken remains genuinely open and is explicitly outside this ADR's own scope — this ADR defines the process by which such a reconciliation would proceed if and when it is initiated; it does not itself initiate one.

## Related

`ADR-GOV-001-Governance-Authority.md` (the authority relationship this process would be invoked to reconcile). `ADR-005-Atlas-Reasoning-Foundations-Naming-and-Authority.md` (the direct working precedent for §4). `atlas_domain_object_architecture/Doctrine.md` §8, §11, §14 (the specific elements this ADR adapts, without adopting that Doctrine's own content authority or its full nine-step Change Protocol). `docs/ADR-Investigation-010-Ontology-Reconciliation-Process.md` (source investigation).
