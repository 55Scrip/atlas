# ADR-003 — The Nature of Knowledge

**Status: Final.** The candidate categories examined for Knowledge's own intrinsic kind (representational content, fact/state of affairs, the strongest available relational account) were tested and falsified, among the candidates considered; none is adopted, and the category is deliberately left open as a stated boundary rather than resolved by default. Established standing is characterized by two jointly necessary conditions — candidacy for Reasoning's examination, and freedom from current active revision — neither sufficient alone. This characterization currently depends on Reasoning, already independently settled (ADR-001 §1–2); whether that dependence is essential or provisional is recorded as an open boundary, not settled here. An identity criterion for subject matter is adopted, stated neutrally between a whole-state and a decomposable-portion reading; whether Knowledge in fact decomposes into determinate portions is likewise recorded as an open boundary. Knowledge's relationship to Evidence, Observation, and Reality remains untouched except at the one point where Knowledge's own boundary required acknowledging that such a relationship exists.

## Question

What is Knowledge?

## Motivation

ADR-001 (Final) characterizes Reasoning almost entirely in terms of its relationship to Knowledge, without settling what Knowledge itself is. ADR-002 (Final) inherits this gap directly: its Equivalence Criterion requires "identical subject matter" and names Knowledge's own identity criterion as the one dependency it references without resolving. This document exists to give Knowledge the treatment both ADRs presuppose but neither supplies.

## First Principles

- Knowledge has standing independent of, and prior to, any Reasoning Act (ADR-001 §3).
- Reasoning neither constitutes nor modifies Knowledge, directly or indirectly, regardless of the confidence carried by any resulting Judgment — Conservatism (ADR-001 §3).
- Knowledge is not Judgment and cannot become it: no Judgment may ever cross back into Knowledge's standing (ADR-001 §3–4).
- Reasoning's own ontological category — a standing capability, individuated by numerical distinctness of its own occurrences — is settled independently of Knowledge (ADR-001 §1–2); ADR-001 itself tested and rejected a candidate that would have tied Reasoning's identity to a knower-and-Knowledge relation.
- ADR-002's Equivalence Criterion depends on Knowledge's own identity criterion for its "identical subject matter" conjunct and does not supply it.

## Candidate Definitions

Among the candidate categories examined here, three were tested and rejected; a fourth, deliberately non-committal candidate survives. No claim is made that these exhaust every possible categorization of Knowledge.

**(a) Representational content.** Knowledge as established informational or representational material — claims, descriptions — standing for something beyond itself.

**(b) Fact or state of affairs.** Knowledge as the established facts themselves, not representations of them.

**(c) Relation, strongest form.** Knowledge as a relation between a knower and a known item, with "a body of Knowledge" naming the set of items some knower stands toward.

**(d) Established material, category left open.** Knowledge as whatever examinable material possesses established standing, prior to and independent of Reasoning, without commitment to whether that material is representational, factual, or of another kind.

## Falsification Attempts

**Against (a):** Representational content is, by definition, a representation *of* something, forcing either naming what that is (Reality, not licensed here) or leaving "aboutness" dangling with no relatum. Tested directly against "can Knowledge exist unrepresented?" — this candidate forecloses the answer by definition, not by argument.

**Against (b):** Cannot be false — a "false fact" is a contradiction in terms. Cannot conflict internally — two genuinely obtaining states of affairs cannot be logically inconsistent. Most decisively: Conservatism's own argument (forbidding endorsement, correction, reweighting) presupposes Knowledge has an adjustable standing capable of being reinforced or doubted. Bare facts have no such standing. If Knowledge were simply facts, Conservatism would guard against a risk that does not exist.

**Against (c), even in its strongest form:** Introduces an unearned first-class "knower" entity nowhere posited by ADR-001. Creates a live risk that a Reasoning Act's mere engagement with a known item generates a new relation-instance — a new instance of Knowledge — precisely the constitution-risk Conservatism forbids. Forces a second, unrequired identity question (sameness of relation-instance vs. sameness of known item) that ADR-002 never asked for. Even at its strongest, it still requires a positive account of the known item's own category, so it eliminates none of the work (a) and (b) were tried for.

**(d) survives every test applied:** permits falsity, permits internal conflict, is available to more than one reasoner without an indexing problem, and requires no representer, fact-hood, or knower.

## Contradictions Found

None. One pre-existing, external tension is inherited rather than created here: Dependency-Graph.md already records that ADR-001's "Knowledge" and the illustrative chain's "Evidence" stand in an undetermined relationship. This document does not resolve it (see Remaining Open Questions).

## Current Working Characterization

> Knowledge is established material: whatever stands, prior to and independent of any Reasoning Act, in a condition of established standing — without commitment to whether that material is representational, factual, or of some other kind.

"Material" is used here only as a neutral placeholder noun, permitting Knowledge to be spoken of at all; it asserts nothing about substance, quantity, or any other intrinsic ontological category beyond what is stated explicitly here.

Established standing consists of two jointly necessary conditions, neither sufficient alone:

1. The material stands as a candidate Reasoning could examine — ruling out material that has simply never been considered.
2. The material is not currently the subject of active revision or dispute — ruling out material presently in flux.

Neither truth, acceptance, authority, nor recognition is required: established material may later be found mistaken, may stand in tension with other established material, and its establishment is not constituted by, or relative to, any accepting or recognizing subject.

Condition 1 is stated in terms of Reasoning, which is already independently characterized without reference to Knowledge (ADR-001 §1–2). This is the strongest characterization of established standing demonstrated so far. Whether Knowledge could, in principle, be characterized without reference to Reasoning — and whether the present dependence is therefore essential or merely an artifact of this track's own sequencing — has not been settled and is not asserted either way here (see Remaining Open Questions).

## Identity Criterion

> Two instances of subject matter are identical if and only if they consist of the same established material, regardless of which Act examined it, when, or how many times.

This criterion is stated without commitment to whether "subject matter" names the entire body of established Knowledge at a given time or a determinate part of it — see Remaining Open Questions.

A consequence resembling locality — that material established elsewhere does not affect this identity — is not asserted here. Whether such a consequence holds depends on whether subject matter decomposes into determinate, independently identifiable portions or must instead be read at the level of the whole established body; that question is recorded as open, not resolved by this criterion.

One consequence follows under either reading: if established material is replaced or altered through revision, the established material available before and after that revision is not identical, even where both concern the same matter in a looser sense — identity tracks the material itself, not the matter it happens to concern.

## Dependency Graph

**Depends on (settled, Final):**
- ADR-001 — Knowledge's independent standing, non-modifiability, categorical distinctness from Judgment; and Reasoning's own independent characterization (§1–2), which the Current Working Characterization's first condition relies on.
- ADR-002 — the specific gap this document addresses: "identical subject matter" in the Equivalence Criterion.

**Introduces as open dependencies for later work:**
- Knowledge's relationship to Evidence, Observation, and Reality.
- Whether Knowledge's dependence on Reasoning (Current Working Characterization, condition 1) is essential to what Knowledge is, or merely provisional pending a future characterization via Reality or Evidence.
- The process, if any, by which material gains or loses established standing over time.

No new primitive is introduced. "Subject matter," as used above, names whatever established material a Judgment concerns — whether the whole body or a part of it — not a further entity in its own right; tested directly against the Primitive Discovery Test, as in ADR-002's treatment of "Judgment type."

## Architectural Consequences

Tentative, per the current state of this document: ADR-002's Equivalence Criterion becomes operational once both conjuncts are read together — "identical content" (settled, ADR-002 Revision 4) and "identical subject matter" (this document's Identity Criterion). No implementation or mechanism is specified.

## Remaining Open Questions

- Knowledge's relationship to Evidence, Observation, and Reality — genuinely open.
- Whether Knowledge's intrinsic category is representational, factual, or of another kind — among the candidates tested, none survived; this reflects the candidates examined, not an exhaustive elimination of every possible category, and is deliberately left open rather than resolved by default.
- Whether Knowledge's dependence on Reasoning for its characterization is essential or merely provisional — a distinct, separately-surfaced question, not to be conflated with the category question above.
- Whether Knowledge has determinate, independently identifiable portions, or whether subject matter must instead be understood at the level of the whole established body — newly identified; not inherited from ADR-001 or ADR-002, and not resolved here. No boundary criterion for portions is proposed, and the Evidence/Knowledge relationship is not drawn on to resolve it.
- The process, if any, by which material acquires or loses established standing over time.

These are carried forward as explicitly stated, knowingly-accepted boundaries of this document, not as omissions.
