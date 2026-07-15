# ADR-002 — The Nature of Judgment

**Status: Draft.** This is a working document, not a settled account. It follows the Standard ADR Structure fixed by the [Atlas Core Development Doctrine](Doctrine.md). Contradictions and open questions recorded below are left open deliberately, per that doctrine's own discipline — none are resolved in this draft.

## Question

What is Judgment?

## Motivation

ADR-001 established that a completed Reasoning Act produces an explicit Judgment, and that Judgment is its own ontological object — distinct from the Reasoning Act that produced it and from the Knowledge that Act concerned. ADR-001 deliberately did not settle what Judgment itself is, reserving that question for a document whose sole concern is Judgment (ADR-001, §5). Downstream architecture cannot proceed — how a Judgment is represented, compared, or related to the confidence it expresses — until this question has a stable answer. This document is that reserved document, and it does not yet reach a stable answer.

## First Principles

The following are already fixed by ADR-001 (Final) and are treated here as constraints this document must remain consistent with, or explicitly flag tension against rather than silently violate:

- Reasoning is a standing capability; a Reasoning Act is one bounded, numerically distinct exercise of it.
- A completed Reasoning Act produces a Judgment. Production is unconditional: every completed Act produces one.
- Judgment is its own ontological object — distinct from the Act that produced it and from the Knowledge that Act concerned.
- Judgment is not necessarily an answer or a recommendation; an acknowledgment of uncertainty is itself a complete, legitimate Judgment.
- Reasoning is conservative with respect to Knowledge: no Judgment may be fed back to alter Knowledge's standing, directly or indirectly, regardless of the confidence it carries.

## Candidate Definitions

Three candidates are considered.

**(a) Judgment as a static conclusion or verdict.** A fixed determination reached by a completed Reasoning Act — an object in the plainest sense, consistent with ADR-001's characterization of Judgment as "its own ontological object." This candidate accommodates "acknowledgment of uncertainty" comfortably: a verdict can itself be a verdict of insufficiency.

**(b) Judgment as the process by which an agent updates confidence in candidates generated through reasoning under conditions of uncertainty.** This is the current best working definition (see below). It emphasizes movement — a transition from a prior state of confidence to a posterior one — rather than a static determination.

**(c) Judgment as a disposition.** A standing readiness of an agent to respond in a certain way, rather than either a fixed object produced at a point or a process unfolding over an interval.

## Falsification Attempts

**Against (a), static conclusion or verdict:** this candidate sits comfortably with ADR-001's "ontological object" language but does not, by itself, explain the dynamic character candidate (b) is meant to capture — a Judgment arrived at by weighing several possibilities against each other and revising an initial estimate. A bare "verdict" account is silent on this movement. Not falsified outright, but incomplete relative to what (b) is trying to capture.

**Against (c), disposition:** ADR-001 states that a completed Reasoning Act *produces* a Judgment — language of production, at a point, following completion of a bounded Act. A disposition, by contrast, is ordinarily a standing property of an agent, already present before and after any particular Act, not something brought into being by one. This sits poorly with "produces." (c) is not pursued further, though it is not conclusively ruled out.

**Against (b), the current best working definition, examined closely:**

1. *Process versus object.* The definition characterizes Judgment as "the process by which..." ADR-001, however, characterizes the Reasoning Act itself as properly describable as a bounded process or event, and characterizes Judgment as "its own ontological object," produced by that Act and distinct from it. If Judgment is now defined as a process, it is not obvious how it remains distinct from the Act — the very distinction ADR-001 argued for in rejecting "Judgment as identical to the Act." This is a direct tension, not falsified away here — see Contradictions Found.

2. *Unconditional production versus conditional update.* ADR-001 requires that every completed Reasoning Act produce a Judgment, without qualification. If Judgment is defined specifically as an *update* to confidence, it is unclear whether a Reasoning Act whose honest result is "the prior confidence level stands, unchanged" has produced a Judgment at all under this definition, or has produced nothing, since no update occurred. Whether a null update counts as an update is not addressed by the definition as given.

3. *"Candidates generated through reasoning."* The definition presupposes that Reasoning generates "candidates" prior to Judgment being formed. Nothing in ADR-001 establishes "candidates," in this sense, as part of Atlas Core's ontology, nor addresses how they relate to Knowledge or to the Reasoning Act. This may be an implicit further primitive that has not yet passed the Primitive Discovery Test, or it may be reducible to existing vocabulary — this draft does not attempt to decide which.

4. *"Conditions of uncertainty."* ADR-001 establishes uncertainty as a legitimate *outcome* of a Reasoning Act. The working definition instead treats uncertainty as a *precondition* — something Judgment occurs "under." Whether these two roles for uncertainty (outcome versus precondition) are consistent, or whether the definition implicitly assumes a Reasoning Act cannot occur, or cannot produce genuine Judgment, in the absence of prior uncertainty, is not resolved here.

5. *"An agent."* The definition attributes the updating to "an agent." No prior ADR names an agent as a primitive, nor establishes whether "the agent" is identical to whatever exercises the Reasoning capability, or is a further, distinct concept. This term is used by the working definition without being grounded in anything settled so far.

## Contradictions Found

- **Process versus object.** The current best working definition describes Judgment as a process; ADR-001 (Final) describes Judgment as an ontological object distinct from the Act, and separately characterizes an Act as the thing properly describable as a process or event. These two characterizations are not currently reconciled. This is recorded as an open contradiction, not resolved in this draft.
- **Unconditional production versus conditional update.** ADR-001 requires every completed Act to produce a Judgment, unconditionally. The working definition's framing around "updating" confidence leaves it unclear whether a Reasoning Act that leaves confidence unchanged has produced a Judgment. This tension is recorded, not resolved.

## Current Best Definition

*(Working, unresolved — carried forward as-is, not endorsed as final.)*

> Judgment is the process by which an agent updates confidence in candidates generated through reasoning under conditions of uncertainty.

This definition is retained as the current best account despite the contradictions and open questions recorded above, per this document's Draft status. It is not to be treated as settled.

## Dependency Graph

**Depends on (settled, Final):**
- ADR-001 — The Nature of Reasoning: Reasoning, Reasoning Act, Knowledge, and the prior conclusion that Judgment is an ontological object produced by a completed Act.

**Introduces as open, unresolved dependencies (no ADR yet exists for these):**
- *Candidate* — whatever "candidates generated through reasoning" refers to.
- *Confidence* — whatever is being updated; its own structure (comparative? quantitative? something else) is undefined.
- *Agent* — whoever or whatever performs the updating; its relationship to the exerciser of the Reasoning capability is undefined.

This dependency graph is itself incomplete, and is recorded as incomplete rather than papered over: ADR-002 currently rests on primitives that have not themselves been through the Primitive Discovery Test required by the Doctrine.

## Architectural Consequences

Held tentatively, contingent on the current best definition and subject to revision once the contradictions above are addressed:

- If Judgment involves updating confidence, some representation of confidence — whether comparative or quantitative — would need to exist wherever a Judgment is represented.
- If Judgment concerns "candidates," a Judgment's representation would need some way of referring to the candidates it concerns, distinct from referring to the Knowledge a Reasoning Act operated over.
- If the process/object contradiction above is resolved in favor of "object," a Judgment would presumably need to capture the *result* of an update (a posterior confidence state) rather than the updating itself; if resolved in favor of "process," a Judgment's own boundaries as a bounded, terminating thing would need further clarification, echoing the same question already asked and answered for Reasoning Acts in ADR-001.

None of these consequences are committed to. They are recorded as *what would follow if* the current draft definition is retained, not as decisions.

## Remaining Open Questions

- Is Judgment fundamentally a process or an object? This draft's working definition and ADR-001's established conclusion point in different directions, and this contradiction is not resolved here.
- Does Judgment require an actual change in confidence to have occurred, or can a Reasoning Act that leaves confidence unchanged still produce a genuine Judgment?
- What is a "candidate," in "candidates generated through reasoning"? Is this a distinct primitive requiring its own ADR, or reducible to Knowledge and Reasoning as already defined?
- What is "confidence"? Does it require its own ADR and its own identity or comparison structure, or is it a simpler, derivative notion?
- What or who is "the agent" that updates confidence? Is this identical to whatever exercises the Reasoning capability defined in ADR-001, or a further, distinct concept not yet named anywhere in Atlas Core's doctrine?
- Is uncertainty, as invoked by "under conditions of uncertainty," the same uncertainty ADR-001 treats as a legitimate *outcome* of reasoning, or a distinct, precondition-like role uncertainty plays that has not yet been reconciled with ADR-001's treatment?

None of the above are resolved by this draft. They are carried forward exactly as open.
