# ADR-002 — The Nature of Judgment

**Status: Final.** This document's account of Judgment is now settled, per the Doctrine's Definition of Done. It follows the Standard ADR Structure fixed by the [Atlas Reasoning Foundations Development Doctrine](Doctrine.md). Resolution Sessions 1 and 2 have settled Judgment's fundamental ontological category (an object, not a process) and its identity and equivalence criteria; Resolution Session 3 settled that antecedent uncertainty is not a precondition of Judgment; Resolution Session 4 settled the minimal criterion for identical Judgment content required by the Equivalence Criterion. Those conclusions are incorporated below and are no longer open. Candidate, Confidence, and Agent were terms introduced only by the rejected process-based candidate and are not carried forward as dependencies or blockers (Revision 2). Knowledge's own identity criterion remains unresolved and is an explicit external dependency, owned by a future ADR concerning Knowledge — it is not a blocker to this ADR's Final status and must not be read as settled by it (Revision 4).

## Question

What is Judgment?

## Motivation

ADR-001 established that a completed Reasoning Act produces an explicit Judgment, and that Judgment is its own ontological object — distinct from the Reasoning Act that produced it and from the Knowledge that Act concerned. ADR-001 deliberately did not settle what Judgment itself is, reserving that question for a document whose sole concern is Judgment (ADR-001, §5). Downstream architecture cannot proceed — how a Judgment is represented, compared, or related to the confidence it expresses — until this question has a stable answer. This document is that reserved document. It now reaches a stable answer for Judgment's ontological category, its identity and equivalence criteria (Resolution Sessions 1–2), whether Judgment presupposes antecedent uncertainty (Resolution Session 3), and the minimal criterion for identical Judgment content (Resolution Session 4). Knowledge's own identity criterion remains outside this document's scope: it is a fact about a different, already-established primitive, referenced here as an explicit external dependency rather than settled by this document.

## First Principles

The following are already fixed by ADR-001 (Final) and are treated here as constraints this document must remain consistent with, or explicitly flag tension against rather than silently violate:

- Reasoning is a standing capability; a Reasoning Act is one bounded, numerically distinct exercise of it.
- A completed Reasoning Act produces a Judgment. Production is unconditional: every completed Act produces one.
- Judgment is its own ontological object — distinct from the Act that produced it and from the Knowledge that Act concerned.
- Judgment is not necessarily an answer or a recommendation; an acknowledgment of uncertainty is itself a complete, legitimate Judgment.
- Reasoning is conservative with respect to Knowledge: no Judgment may be fed back to alter Knowledge's standing, directly or indirectly, regardless of the confidence it carries.

## Candidate Definitions

Three candidates were originally considered.

**(a) Judgment as a static conclusion or verdict.** A fixed determination reached by a completed Reasoning Act — an object in the plainest sense, consistent with ADR-001's characterization of Judgment as "its own ontological object." This candidate accommodates "acknowledgment of uncertainty" comfortably: a verdict can itself be a verdict of insufficiency. **Resolution Session 1 tested this candidate further and adopted it, refined, as the current best definition (see below); it is the only one of the three that survives.**

**(b) Judgment as the process by which an agent updates confidence in candidates generated through reasoning under conditions of uncertainty.** This was originally recorded as the current best working definition. **Resolution Session 1 falsified this candidate: characterizing Judgment as a process directly contradicts ADR-001's own characterization of Judgment as "its own ontological object," distinct from the Act, which ADR-001 itself characterizes as the process/event. This candidate is rejected — see Contradictions Found and Current Best Definition below.**

**(c) Judgment as a disposition.** A standing readiness of an agent to respond in a certain way, rather than either a fixed object produced at a point or a process unfolding over an interval. Not pursued further, as originally recorded below; unaffected by Resolution Sessions 1–2.

## Falsification Attempts

**Against (a), static conclusion or verdict:** this candidate sits comfortably with ADR-001's "ontological object" language but was originally judged not to, by itself, explain the dynamic character candidate (b) was meant to capture — a Judgment arrived at by weighing several possibilities against each other and revising an initial estimate. **Resolution Session 1 addressed this directly: (a) is not obligated to narrate its own genesis. That is the Reasoning Act's job, already fully handled by ADR-001. (a) only needs to *be* what results, not explain how it came about — exactly mirroring how ADR-001 never asks the Act to explain the Judgment either. This objection is answered, not a surviving weakness; (a) is adopted.**

**Against (c), disposition:** ADR-001 states that a completed Reasoning Act *produces* a Judgment — language of production, at a point, following completion of a bounded Act. A disposition, by contrast, is ordinarily a standing property of an agent, already present before and after any particular Act, not something brought into being by one. This sits poorly with "produces." (c) is not pursued further, though it is not conclusively ruled out.

**Against (b), the originally-proposed working definition — now rejected:**

1. *Process versus object.* **RESOLVED (Resolution Session 1).** The definition characterized Judgment as "the process by which..." ADR-001, however, characterizes the Reasoning Act itself as properly describable as a bounded process or event, and characterizes Judgment as "its own ontological object," produced by that Act and distinct from it. Resolution Session 1 tested this tension directly and rejected the process-based candidate on exactly this ground: a process cannot be Judgment without collapsing the very distinction ADR-001 argued for in rejecting "Judgment as identical to the Act." See Contradictions Found.

2. *Unconditional production versus conditional update.* **RESOLVED, by reframing (Resolution Session 1).** This tension arose only because (b) characterized Judgment as an *update* to confidence, leaving unclear whether a Reasoning Act with no change in confidence had produced a Judgment at all. Since Judgment is now an object rather than an update-process, this question no longer arises in its original form — every completed Act produces exactly one Judgment-object, unconditionally, regardless of how its content compares to any other Judgment.

3. *"Candidates generated through reasoning."* This term was introduced only by rejected candidate (b) and is not carried forward as a dependency of Judgment's settled ontology (Revision 2). It does not appear in the adopted definition, the identity criterion, or the equivalence criterion.

4. *"Conditions of uncertainty."* No longer part of the adopted definition, which does not invoke uncertainty as a precondition in this form. The narrower question about antecedent uncertainty that survived independently of (b)'s own wording is now settled — see Current Best Definition (Resolution Session 3).

5. *"An agent."* This term was introduced only by rejected candidate (b) and is not carried forward as a dependency of Judgment's settled ontology (Revision 2). It does not appear in the adopted definition, the identity criterion, or the equivalence criterion.

## Contradictions Found

- **Process versus object — RESOLVED (Resolution Session 1).** The prior working definition described Judgment as a process; ADR-001 (Final) describes Judgment as an ontological object distinct from the Act, and separately characterizes an Act as the thing properly describable as a process or event. Resolution Session 1 tested this directly and rejected the process-based candidate: Judgment is an ontological object, produced by, and never identical to, the Reasoning Act. No unresolved contradiction remains on this point.
- **Unconditional production versus conditional update — RESOLVED, by reframing (Resolution Session 1).** This tension arose only because the prior working definition characterized Judgment as an *update* to confidence. Since Judgment is now an object rather than an update-process, the question of whether a "null update" counts no longer arises in its original form: every completed Reasoning Act produces exactly one Judgment-object, unconditionally, regardless of how that determination compares to any other. No unresolved contradiction remains on this point.

## Current Best Definition

*(Judgment's ontological category, identity, and equivalence are now settled, per Resolution Sessions 1–2, and are no longer working/unresolved; whether Judgment presupposes antecedent uncertainty is likewise settled, per Resolution Session 3 (see below); the minimal criterion for identical Judgment content is likewise settled, per Resolution Session 4 (see Equivalence Criterion below). Knowledge's own identity criterion remains open, but as an external dependency owned by a future ADR, not as an open question of this definition (Revision 4). Candidate, Confidence, and Agent were introduced only by the rejected process-based candidate and are not dependencies of this definition — see Candidate Definitions and Falsification Attempts for the historical record.)*

> Judgment is the ontological object produced by a completed Reasoning Act: the specific, complete determination that Act reaches concerning the Knowledge it operated over — a determination that may itself consist in the honest conclusion that the available Knowledge does not settle the matter. Judgment is not the activity of reaching it; that activity is the Reasoning Act, already established in ADR-001.

This definition settles Judgment's fundamental ontological category. It does not depend on Candidate, Confidence, or Agent, and introduces no new primitive. The identity and equivalence criteria below are stated separately and are part of this same settled position.

**Antecedent uncertainty is not a precondition of Judgment (Resolution Session 3).** Every completed Reasoning Act produces exactly one Judgment regardless of whether the matter it concerned was uncertain before the Act. Uncertainty remains a possible content of a Judgment, including a determination that the available Knowledge does not settle the matter — this was already established by ADR-001 §7 and is unchanged here. Producing a Judgment does not itself alter whether the relevant Knowledge settles the matter: because Reasoning is conservative with respect to Knowledge (ADR-001 §3), a Judgment neither makes an already-settled matter more settled nor makes an unsettled matter settled. A later Reasoning Act concerning the same subject matter remains a distinct Act (per the Identity Criterion in this ADR), but its mere possibility does not imply that the matter was, or remains, uncertain.

> Before the Act: uncertainty is not required.
> Within the Judgment: uncertainty is possible content.
> After the Act: the Judgment does not modify the epistemic standing of the Knowledge concerned.

These are three distinct roles of one concept, not three instances of the same state — none is entailed by the others.

## Identity Criterion (Numerical)

> Numerical identity: two Judgments are numerically identical if and only if they were produced by the same Reasoning Act.

Since Reasoning Acts are individuated by numerical distinctness of occurrence alone (ADR-001), no two distinct Acts ever produce a numerically identical Judgment. Every Judgment has exactly one producing Act, and every completed Act produces exactly one Judgment. No Reasoning Act produces more than one Judgment, and no Judgment is produced by more than one Reasoning Act.

## Equivalence Criterion

> Equivalence: two numerically distinct Judgments are equivalent if and only if they express identical content concerning identical subject matter.

Equivalence is not numerical identity: two equivalent Judgments remain two. ADR-001's phrase that separate Acts "might yield what is recognizably the same Judgment" is interpreted, per Resolution Session 2, as a claim about equivalence, not numerical identity — a reading adopted by argument, since ADR-001's own phrasing does not itself unambiguously specify which was meant (see Remaining Open Questions). "Judgment type," where the term is used at all, refers only to this equivalence relation over Judgment tokens — it is not introduced as a further ontological primitive.

**Identical content (Resolution Session 4).** Two Judgment contents are identical if and only if they constitute the same determination concerning the same subject matter — the same resolution, at the same scope, qualification, and directional commitment, including, where applicable, the same acknowledgment that the matter remains unsettled — regardless of wording, logical form, evidential history, or reasoning path. In particular:

- Identical wording is neither necessary nor sufficient for identical content: two Judgments may use the same words while committing to different determinations, and may use different words while committing to the same determination.
- Differences in scope, qualification, or directional commitment are differences in what is determined, not merely in how it is expressed, and therefore produce different content.
- The reasoning path and evidential history through which a Reasoning Act reached its determination are not part of Judgment's content: Judgment is not the activity of reaching it (Current Best Definition; Resolution Session 1), and this holds for content-identity exactly as it already holds for Judgment's ontological category.

**Identical subject matter** depends on Knowledge's own identity criterion, which this document does not supply and does not need to supply before reaching Final — see Dependency Graph and Remaining Open Questions.

## Dependency Graph

**Depends on (settled, Final):**
- ADR-001 — The Nature of Reasoning: Reasoning, Reasoning Act, Knowledge, and the prior conclusion that Judgment is an ontological object produced by a completed Act.

This is the only dependency the Current Best Definition, Identity Criterion, and Equivalence Criterion actually use. Candidate, Confidence, and Agent were introduced only by the rejected process-based candidate (b) — see Candidate Definitions and Falsification Attempts for the historical record of why (b) was rejected. They are not dependencies of the settled ontology, and are not relocated elsewhere in this document as open Judgment primitives (Revision 2).

*Judgment type* was considered directly (Resolution Session 2) and explicitly **not** introduced as a new primitive: where "type" language is used, it names only the equivalence relation over Judgment tokens defined above, not a further kind of entity.

**External dependency (not owned by this ADR):**
- Knowledge's own identity criterion — what makes two bodies of Knowledge, or two instances of subject matter, "the same." The Equivalence Criterion's "identical subject matter" conjunct relies on this, but it is a fact about Knowledge, a primitive already established independently in ADR-001, not about Judgment. This ADR names the dependency explicitly rather than resolving it, and does not require it to be resolved before reaching Final. When a future ADR settles Knowledge's own identity criterion, that ADR's dependency graph must be checked for consistency with this reliance, per the Doctrine's Definition of Done.

This dependency graph now reflects everything the settled ontology requires or explicitly references. It carries no unresolved dependency that is this ADR's own to settle.

## Architectural Consequences

The adopted ontology of Judgment yields one settled consequence:

- Judgment, being an object rather than a process, captures the *result* a Reasoning Act reaches — not the activity of reaching it, and not any ongoing or unbounded state. Its own boundaries are fixed by, and only by, the boundedness of the Act that produced it (ADR-001); no further clarification of Judgment's own boundaries as a bounded, terminating thing is needed, since Judgment is not itself process-like.

This is a settled consequence, not a contingency. No representation obligation for Candidate, Confidence, or Agent is recorded here: none of the three is a dependency of the settled ontology (Revision 2), so there is nothing about them for this section to hold even tentatively.

## Remaining Open Questions

- **Resolved by Resolution Session 1:** Judgment is an ontological object, not a process; this is no longer an open question. **Resolved by Resolution Sessions 1–2, by reframing:** since Judgment is not an update-process, the null-update question no longer arises in its original form; every completed Reasoning Act produces exactly one Judgment, unconditionally. **Removed (Revision 2):** Candidate, Confidence, and Agent are no longer listed as open questions of ADR-002 — each was introduced only by rejected candidate (b) and is not a dependency, blocker, or open question of the settled ontology (see Candidate Definitions and Falsification Attempts for the historical record). **Resolved by Resolution Session 3 (Revision 3):** antecedent uncertainty is not a precondition of Judgment; this is no longer an open question — see Current Best Definition for the settled principle. **Resolved by Resolution Session 4 (Revision 4):** the minimal criterion for identical Judgment content is settled — see Equivalence Criterion. **Reclassified (Revision 4):** Knowledge's own identity criterion was previously listed here as an open question of this ADR. It is not: it is a fact about Knowledge, a primitive already established independently in ADR-001, and is recorded as an explicit external dependency in the Dependency Graph above rather than as an open question this ADR must itself resolve.

This ADR carries no remaining open question of its own. It carries one explicit external dependency — Knowledge's own identity criterion, recorded in the Dependency Graph above — owned by a future ADR, unresolved, and not a blocker to this document's Final status.
