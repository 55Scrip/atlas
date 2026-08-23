# Atlas Core — ADR Adoption Program

## Sprint 2 — Governance Adoption Review

**Status:** Architectural adoption review only. No ADR, OE document, doctrine, ontology decision, implementation, or reconciliation is created, modified, or authorized by this document. This review evaluates readiness; it does not itself confer architectural status on anything.

**Scope:** Every recommendation whose Source Investigation is `ADR-Investigation-009`, `010`, or `011`, as recorded in `Atlas-Recommendation-Register.md` — 20 recommendations in total (4 from Investigation 9, 7 from Investigation 10, 9 from Investigation 11). This is a broader set than the Register's own "Governance" category tag alone (14 entries): six additional entries tagged Architecture or Process in the Register are included here because they originate from investigations whose own stated subject was governance itself, and excluding them on a prior classification technicality would understate what these three investigations actually produced. Ontology recommendations from Investigations 001–008 are explicitly out of scope and not reviewed here.

---

## 1. Executive Summary

**Total governance recommendations reviewed:** 20.

**Overall maturity:** High, with one significant caveat. Every recommendation traces to specific, evidence-cited reasoning in its source investigation; none was found to rest on unstated assumption. The central recommendation of the set — `INV10-R1`, "Disclosed Pluralism with an Explicit Reconciliation Process" — is unusually well-tested (it survives its own 14-phase governance-model comparison and an 18-phase consistency check against the entire named architecture) and is not a novel invention: it is directly modeled on `ADR-005`, an already-accepted, already-working precedent. This materially de-risks the whole set, since the core model being proposed for formal adoption is not hypothetical.

**The caveat:** maturity of *reasoning* is not the same as maturity of *operational readiness*. Three recommendations in this set (`INV9-R2`, `INV10-R7`, `INV11-R7`) are well-argued but explicitly incomplete by their own sources' own admission — no owner, no timeline, or no practical test exists yet. These are flagged Defer below, not because the reasoning is weak, but because an ADR cannot responsibly be drafted around an unassigned "someone should eventually."

**Major themes:**
1. **Borrowing over inventing.** A strong majority of the set (11 of 20) explicitly reuses existing, already-accepted vocabulary — `atlas_domain_object_architecture/Doctrine.md` §8/§11/§14's own status, supersession, and historical-integrity language — rather than proposing anything new. This is a genuine strength: the adoption cost for these is close to zero, since nothing about Atlas's existing governance apparatus needs to change, only be explicitly extended in scope.
2. **A single critical-path spine.** `INV9-R1` → `INV10-R1` → `INV11-R1` → `INV11-R6` forms one continuous dependency chain that essentially *is* the governance model being proposed; nearly every other recommendation in the set either supports, refines, or is a corollary of this chain.
3. **Self-application.** The set includes recommendations that govern how this very review, and the sprint that produced it, must itself behave (`INV11-R6` in particular) — a genuinely unusual but coherent property, tested directly in Section 4 below.

**Primary risks:** (1) adopting the central model (`INV10-R1`) as one monolithic ADR risks conflating a sound governance *principle* with still-unresolved *operational* questions (who reconciles what, on what timeline); (2) three recommendations remain genuinely immature and risk being rushed into an ADR if the set is adopted as an undifferentiated block; (3) no existing doctrine track has yet been asked whether it accepts being described the way `Investigation-009`/`010` describe it — this review cannot resolve that, only flag it (Section 7).

---

## 2. Recommendation Review

### From Investigation 009 — Ontology Authority and Reconciliation

#### INV9-R1
- **Summary:** Treat the implemented `atlas/core/domain/*` objects as primary authority for this series and its own future continuations; treat Reasoning Foundations and Domain Object Architecture as informative but not currently binding.
- **Benefits:** Matches what the entire investigation series has already, consistently practiced; requires no change to anything; resolves the practical question of "which source do I trust" for every future investigation.
- **Risks:** Formalizing this could be read, if worded carelessly in a future ADR, as permanently demoting Domain Object Architecture's own real, rigorous work — `Investigation-009`'s own Phase 18 already flags this as a real, disclosed cost, not a hidden one.
- **Dependencies:** None upstream; everything else in this set downstream depends on it.
- **Existing doctrine compatibility:** Compatible — matches `ADR-005`'s own precedent for the Reasoning Foundations relationship exactly; extends the same posture to Domain Object Architecture, which `ADR-005` never addressed.
- **Existing implementation impact:** None.
- **Adoption readiness:** High.

#### INV9-R2
- **Summary:** A formal, `ADR-005`-equivalent reconciliation between the implemented Core Loop and Domain Object Architecture should eventually be produced.
- **Benefits:** Names a real, concrete gap (no such document exists) that would otherwise remain invisible.
- **Risks:** As stated, carries no owner, no timeline, and no defined scope — not yet shaped enough to become an ADR task; a premature ADR here risks becoming an unfulfillable placeholder.
- **Dependencies:** Depends on `INV9-R1` being adopted first.
- **Existing doctrine compatibility:** Compatible in principle — matches Domain Object Architecture Doctrine's own §13 Change Protocol shape, but that Protocol itself presupposes an initiator, which this recommendation does not supply.
- **Existing implementation impact:** None.
- **Adoption readiness:** Low (reasoning is sound; operational readiness is not).

#### INV9-R3
- **Summary:** Reject the candidate three-layer hierarchy model (Reasoning Foundations → Domain Object Model → Implementation) — it does not survive contradiction.
- **Benefits:** Forecloses a tempting but false simplification before it can be assumed by a future document.
- **Risks:** None identified — a negative finding, not a proposal.
- **Dependencies:** None; supports `INV10-R6`'s own identical rejection one level up.
- **Existing doctrine compatibility:** Compatible — no doctrine track claims this hierarchy exists.
- **Existing implementation impact:** None.
- **Adoption readiness:** High.

#### INV9-R4
- **Summary:** Reject unilateral OE-002 authority over implementation (Model B), Reasoning-Foundations-governs-all (Model C), and unacknowledged status quo (Model F).
- **Benefits:** Same as `INV9-R3` — closes off unsound alternatives explicitly.
- **Risks:** None identified.
- **Dependencies:** None.
- **Existing doctrine compatibility:** Compatible.
- **Existing implementation impact:** None.
- **Adoption readiness:** High.

---

### From Investigation 010 — Ontology Reconciliation Process

#### INV10-R1
- **Summary:** Adopt "Disclosed Pluralism with an Explicit Reconciliation Process" (Model G) as the general cross-track governance model: tracks remain independently governed by default; a demonstrated forcing function is required before reconciliation is undertaken; when undertaken, reconciliation follows the Domain Object Architecture Change Protocol as a method template, never a content mandate.
- **Benefits:** The central, load-bearing recommendation of the entire set — already validated by a real precedent (`ADR-005`), survives its own dedicated 18-phase consistency test, and requires no existing track's content to change.
- **Risks:** Its own source material discloses two live gaps that a bare adoption would leave unaddressed: no forcing-function criteria are concretely enumerated (only described abstractly, per Domain Object Architecture Doctrine §8's own borrowed vocabulary), and no reconciliation has an owner (`INV9-R2`). Adopting the *principle* without addressing these risks an ADR that is philosophically sound but operationally inert.
- **Dependencies:** Depends on `INV9-R1`. Is itself the direct dependency for `INV11-R1`.
- **Existing doctrine compatibility:** Compatible — explicitly, deliberately modeled on `ADR-005` and Domain Object Architecture Doctrine §13, without claiming either track's own content authority.
- **Existing implementation impact:** None.
- **Adoption readiness:** Medium-High — the model itself is ready; its operational surface is not.

#### INV10-R2
- **Summary:** Reconciliation's minimum required output is always at least a documented decision; content need not change on either side.
- **Benefits:** Low-cost, directly evidenced by `ADR-005` itself as a working example — removes any temptation to treat reconciliation as always requiring a costly content merge.
- **Risks:** None identified.
- **Dependencies:** Depends on `INV10-R1`.
- **Existing doctrine compatibility:** Compatible.
- **Existing implementation impact:** None.
- **Adoption readiness:** High.

#### INV10-R3
- **Summary:** Supersession requires an identified replacing decision and an explicit status change — never silent deletion, never mere recency.
- **Benefits:** Directly reuses Domain Object Architecture Doctrine §14's own already-accepted language; zero new concepts.
- **Risks:** None identified.
- **Dependencies:** None standalone; reused reflexively by `INV11-R5`.
- **Existing doctrine compatibility:** Fully compatible — a direct citation, not a paraphrase.
- **Existing implementation impact:** None.
- **Adoption readiness:** High.

#### INV10-R4
- **Summary:** Historical records, including every investigation document, must remain permanently recoverable regardless of any future reconciliation's outcome.
- **Benefits:** Same as `INV10-R3` — a direct reuse of §11's own already-accepted language.
- **Risks:** None identified.
- **Dependencies:** None standalone; reused reflexively by `INV11-R5`.
- **Existing doctrine compatibility:** Fully compatible.
- **Existing implementation impact:** None.
- **Adoption readiness:** High.

#### INV10-R5
- **Summary:** A contradiction (two claims both currently claiming settled status about the same fact) must be distinguished from an omission or alternative model; only the former requires urgent resolution.
- **Benefits:** A precise, reusable analytical distinction that prevents over-reacting to ordinary gaps in coverage.
- **Risks:** This is closer to methodological guidance than a formal architectural rule — worth confirming it is adopted as *guidance for future investigations and reviews*, not mistaken for a normative claim about any specific existing disagreement.
- **Dependencies:** Depends on `INV10-R1` for context; reused directly by `INV11-R7`.
- **Existing doctrine compatibility:** Compatible, no direct doctrine precedent but no conflict either.
- **Existing implementation impact:** None.
- **Adoption readiness:** High, with the framing caveat above.

#### INV10-R6
- **Summary:** Reject implementation-first-alone, ontology-first-alone (read retroactively), documentation-first, living-architecture-alone, and independent-parallel-tracks-alone as the general governance model.
- **Benefits:** Closes off five plausible-sounding alternatives with stated reasons each.
- **Risks:** None identified.
- **Dependencies:** None.
- **Existing doctrine compatibility:** Compatible.
- **Existing implementation impact:** None.
- **Adoption readiness:** High.

#### INV10-R7
- **Summary:** The investigation series itself should be recognized as a fourth, previously-unacknowledged quasi-track and its own authority status formally addressed.
- **Benefits:** Correctly identifies a real, previously-invisible gap.
- **Risks:** **This recommendation's own open question is already answered by `INV11-R8`** — adopting `INV10-R7` on its own, without `INV11-R8`'s specific answer, would recreate the ambiguity `INV11-R8` exists to close.
- **Dependencies:** Directly resolved by `INV11-R8` — should not be adopted independently of it.
- **Existing doctrine compatibility:** N/A on its own; compatible once paired with `INV11-R8`.
- **Existing implementation impact:** None.
- **Adoption readiness:** Medium — sound as a diagnosis, incomplete without its own resolution attached.

---

### From Investigation 011 — Authority of the ADR Investigation Series

#### INV11-R1
- **Summary:** Adopt "Permanent ADR-Precursor Record" as the investigation series' own governance model: the series observes and advises; it never governs, replaces, or self-converts into architecture.
- **Benefits:** Unusually strong evidentiary basis — verified by direct grep of all ten prior documents' actual behavior, not merely argued from principle. Describes existing, already-uniform practice rather than imposing something new.
- **Risks:** None substantive identified; the closest thing to a risk is that formalizing an already-informal practice could, if worded too rigidly, constrain a future investigation's own legitimate flexibility — not evidenced as an actual problem, only a theoretical one.
- **Dependencies:** Depends on `INV10-R1` and `INV10-R7`.
- **Existing doctrine compatibility:** Compatible by construction — built specifically to reuse existing vocabulary (`INV11-R2`).
- **Existing implementation impact:** None.
- **Adoption readiness:** High.

#### INV11-R2
- **Summary:** Investigation documents should borrow existing status/supersession/historical-integrity vocabulary rather than requiring a new, bespoke doctrine.
- **Benefits:** Directly disciplined by Domain Object Architecture Doctrine's own anti-inflation principle (§3); avoids duplicating governance machinery that already exists.
- **Risks:** None identified.
- **Dependencies:** Depends on `INV11-R1`.
- **Existing doctrine compatibility:** Fully compatible — this recommendation's entire premise is compatibility.
- **Existing implementation impact:** None.
- **Adoption readiness:** High.

#### INV11-R3
- **Summary:** No investigation document may claim Final, binding, or normative status for itself.
- **Benefits:** Zero-cost — already the uniform, verified practice across all ten prior documents.
- **Risks:** None identified.
- **Dependencies:** Depends on `INV11-R1`.
- **Existing doctrine compatibility:** Compatible.
- **Existing implementation impact:** None.
- **Adoption readiness:** High.

#### INV11-R4
- **Summary:** Every ADR Candidate section a future investigation produces must remain labeled an outline, never presented as the ADR itself.
- **Benefits:** Same as `INV11-R3` — already-verified uniform practice.
- **Risks:** None identified.
- **Dependencies:** Depends on `INV11-R1`.
- **Existing doctrine compatibility:** Compatible.
- **Existing implementation impact:** None.
- **Adoption readiness:** High.

#### INV11-R5
- **Summary:** No investigation is ever deleted; a later document supersedes an earlier one explicitly, leaving it fully readable.
- **Benefits:** Directly reuses `INV10-R3`/`R4`'s already-reviewed, high-readiness rules, applied reflexively to the series itself.
- **Risks:** None identified.
- **Dependencies:** Depends on `INV10-R3`, `INV10-R4`, `INV11-R1`.
- **Existing doctrine compatibility:** Fully compatible.
- **Existing implementation impact:** None.
- **Adoption readiness:** High.

#### INV11-R6
- **Summary:** Conversion of any investigation's findings into architecture always requires a separate, later act by an authorized track's own process — never self-conversion, never mere continued existence as a file.
- **Benefits:** The single most operationally important recommendation in the set — it is the rule that determines what this very Sprint 2 review is and is not allowed to do (see Section 4's own self-application test).
- **Risks:** If under-communicated, could be misread as making the entire investigation series pointless; the correct reading (input, not output) needs to travel with this rule wherever it is cited.
- **Dependencies:** Depends on `INV11-R1`.
- **Existing doctrine compatibility:** Compatible — consistent with every existing track's own change-protocol structure, none of which permits self-conversion either.
- **Existing implementation impact:** None.
- **Adoption readiness:** High.

#### INV11-R7
- **Summary:** A genuine future contradiction between two investigations should be resolved by a third, later investigation that directly re-tests the disputed claim.
- **Benefits:** A coherent, evidence-consistent contingency plan.
- **Risks:** **Explicitly untested** — no real contradiction between investigations has yet occurred (`Investigation-011`'s own Phase 12 finding: `Investigation-009`'s refinement of `Investigation-008` was an omission fix, not a contradiction). Adopting an untested conflict-resolution mechanism as formal architecture risks discovering it doesn't work only when it is actually needed.
- **Dependencies:** Depends on `INV11-R1`, `INV10-R5`.
- **Existing doctrine compatibility:** Compatible in principle, no precedent to confirm against.
- **Existing implementation impact:** None.
- **Adoption readiness:** Low (sound reasoning, zero practical validation).

#### INV11-R8
- **Summary:** The investigation series should be treated as advisory ADR-precursor input, not a peer-authority fourth track — the direct answer to `INV10-R7`'s own open question.
- **Benefits:** Resolves a real, named gap with a specific, well-reasoned answer rather than leaving it open indefinitely.
- **Risks:** None identified — explicitly framed by its own source as answering, not reversing, a genuinely open prior question.
- **Dependencies:** Depends on `INV10-R7`, `INV11-R1`.
- **Existing doctrine compatibility:** Compatible.
- **Existing implementation impact:** None.
- **Adoption readiness:** High.

#### INV11-R9
- **Summary:** Reject research-only, architecture-authority, independent-reconciliation-track, living-archive-alone, and temporary-working-documents as the series' own governance model.
- **Benefits:** Closes off five plausible alternatives with stated, empirically-grounded reasons.
- **Risks:** None identified.
- **Dependencies:** None.
- **Existing doctrine compatibility:** Compatible.
- **Existing implementation impact:** None.
- **Adoption readiness:** High.

---

## 3. Adoption Matrix

| ID | Status | Rationale |
|---|---|---|
| INV9-R1 | **Adopt** | Foundational, zero cost, already-practiced posture; nothing downstream can be adopted without it |
| INV9-R2 | **Defer** | Sound diagnosis, no owner or timeline — not yet ADR-shaped |
| INV9-R3 | **Adopt** | Negative finding, supports `INV10-R6`, no cost |
| INV9-R4 | **Adopt** | Negative finding, no cost |
| INV10-R1 | **Adopt with Modification** | The model itself is ready; adoption must require concrete forcing-function criteria and a named reconciliation-initiation process to be specified as part of the ADR, not left implicit |
| INV10-R2 | **Adopt** | Directly evidenced by `ADR-005`, zero new risk |
| INV10-R3 | **Adopt** | Direct reuse of existing, accepted doctrine language |
| INV10-R4 | **Adopt** | Direct reuse of existing, accepted doctrine language |
| INV10-R5 | **Adopt with Modification** | Adopt explicitly as analytical/methodological guidance, not as a standalone normative rule, to avoid overclaiming its status |
| INV10-R6 | **Adopt** | Negative findings, no cost |
| INV10-R7 | **Adopt with Modification** | Adopt only paired with `INV11-R8`'s own answer — never standalone |
| INV11-R1 | **Adopt** | Strongest evidentiary basis in the set (direct empirical verification); describes existing practice |
| INV11-R2 | **Adopt** | Directly disciplined by existing anti-inflation principle; zero new machinery |
| INV11-R3 | **Adopt** | Zero cost, already-uniform practice |
| INV11-R4 | **Adopt** | Zero cost, already-uniform practice |
| INV11-R5 | **Adopt** | Direct reuse of already-reviewed `INV10-R3`/`R4` |
| INV11-R6 | **Adopt** | Operationally critical; governs the legitimacy of this very review |
| INV11-R7 | **Defer** | Explicitly untested contingency mechanism; no urgency, no current instance requiring it |
| INV11-R8 | **Adopt** | Resolves `INV10-R7` cleanly, no identified cost |
| INV11-R9 | **Adopt** | Negative findings, no cost |

**Summary:** 15 Adopt, 3 Adopt with Modification, 2 Defer, 0 Reject.

**No recommendation in this set was found to warrant outright rejection** — the weakest entries (`INV9-R2`, `INV11-R7`) are deferred for operational immaturity, not because their reasoning is unsound.

---

## 4. Required Architectural Changes

| If adopted | Required formal work |
|---|---|
| INV9-R1, INV9-R3, INV9-R4 | New ADR (a single, short "governing-posture" ADR is sufficient for all three together — they are one finding and its two supporting rejections) |
| INV9-R2 | No architectural change required *yet* — first requires an owner and scope to be assigned by whatever process Wave 0 establishes; only then does it become ADR-ready |
| INV10-R1 (with modification) | New ADR — the set's central document; should explicitly incorporate the forcing-function and ownership detail identified as missing in Section 2 |
| INV10-R2, INV10-R3, INV10-R4, INV10-R6 | Documentation update only — these codify or cite already-accepted doctrine; at most a cross-reference needs adding to that doctrine's own navigational material |
| INV10-R5 | Documentation update — record as investigation/review methodology, not a new ADR |
| INV10-R7 + INV11-R8 (paired) | New ADR — the series' own status determination, naturally packaged with `INV11-R1` below |
| INV11-R1, INV11-R2, INV11-R3, INV11-R4, INV11-R5, INV11-R6, INV11-R9 | New ADR — the series' own governing document; these seven form one coherent package and should not be split across multiple ADRs |
| INV11-R7 | No architectural change required *yet* — revisit only if and when a genuine investigation-to-investigation contradiction actually occurs |

**No implementation work, OE amendment, or existing-doctrine amendment is required by any recommendation in this set.** Every adoptable item either produces a new ADR or merely documents/cites what already exists. This is consistent with the set's own repeatedly-stated principle of borrowing over inventing (Section 1).

---

## 5. Dependency Analysis

**Critical-path spine (must be adopted in this order; each is a prerequisite for the next):**

```
INV9-R1
   └─→ INV10-R1 (with modification)
          └─→ INV11-R1
                 └─→ INV11-R6
```

**Prerequisites for specific downstream items:**
- `INV10-R7` requires `INV11-R8` to be adopted in the same package (Section 2/3).
- `INV11-R5` requires `INV10-R3` and `INV10-R4` to already be accepted (it directly reuses their language).
- `INV11-R7` requires `INV10-R5`'s own contradiction/omission distinction to already exist.

**Blockers:**
- `INV9-R2` is blocked on an ownership assignment that no recommendation in this set actually performs — Section 7 names this as a remaining risk, not something this review can resolve.
- Nothing else in the set is blocked; every Defer item is deferred for its own internal immaturity, not because something else must happen first.

**Independent recommendations (no dependency relationship to anything else in the set):**
- `INV9-R3`, `INV9-R4`, `INV10-R2`, `INV10-R6`, `INV11-R9` — each is a self-contained finding (mostly negative/supporting) that could be adopted in any order, or omitted, without affecting anything else.

**Recommendations that should be adopted together, as a package, even though not strictly sequential:**
- `INV10-R7` + `INV11-R8` (Section 2/3 — adopting one without the other recreates an open question).
- `INV11-R1` through `INV11-R6` and `INV11-R9` — while `R1` is the technical prerequisite, in practice these seven describe one coherent governance model for the series and read poorly if split across separate ADRs (Section 4).

---

## 6. Adoption Waves

**Wave 0 — Governance Foundation**
`INV9-R1`, `INV9-R3`, `INV9-R4`.
*Purpose: establish that implementation is treated as primary authority for this series, with the rejected alternatives on record. Nothing else in this set can be meaningfully adopted before this wave lands.*

**Wave 1 — Authority Model**
`INV10-R1` (with modification — forcing-function criteria and reconciliation ownership must be concretely specified during drafting), `INV10-R2`, `INV10-R3`, `INV10-R4`, `INV10-R5` (as guidance), `INV10-R6`.
*Purpose: establish the general cross-track reconciliation model and its supporting vocabulary. This is the set's own center of gravity.*

**Wave 2 — Investigation Lifecycle**
`INV10-R7` + `INV11-R8` (paired), `INV11-R1`, `INV11-R2`, `INV11-R3`, `INV11-R4`, `INV11-R5`, `INV11-R6`, `INV11-R9`.
*Purpose: formally establish what the investigation series itself is and is not allowed to do — the most self-referential, but also most empirically well-grounded, wave.*

**Parked (not assigned to a wave):**
`INV9-R2`, `INV11-R7` — both Defer, both revisited only once their own named precondition (an owner; a real test case) actually arises.

---

## 7. Remaining Risks

Only genuine, unresolved governance questions — none of the settled investigations is reopened here.

1. **No owner exists for the Track 1 ↔ Track 3 reconciliation (`INV9-R2`), and no recommendation in this set assigns one.** This is the single most concrete, actionable gap surfaced by this review, exactly as it was by `Investigation-009` and `010` before it — restated, not newly discovered, but still unresolved.
2. **`INV10-R1`'s forcing-function criteria remain abstract.** Domain Object Architecture Doctrine §8 lists categories of legitimate forcing functions, but nothing in this set states, concretely, what would satisfy them *for this specific cross-track question*. Drafting the Wave 1 ADR without resolving this risks a model that is correct in principle but unusable in practice.
3. **Neither Reasoning Foundations nor Domain Object Architecture has been asked whether it accepts the posture `INV9-R1`/`INV10-R1` assign to it.** This review, like the investigations before it, can only observe and recommend — it cannot confirm the other tracks' own agreement, and no mechanism in this set produces that confirmation either.
4. **`INV11-R7`'s conflict-resolution mechanism is unvalidated.** A real, future contradiction between investigations, if one occurs before this mechanism is tested, would be the first real trial of a rule adopted on reasoning alone.
5. **The set's own internal packaging (`INV10-R7`+`INV11-R8`; the seven-item `INV11` bundle) is this review's own judgment, not something any source investigation itself specified.** A future ADR author may reasonably package these differently; this review's Section 4/6 groupings should be treated as a recommendation, not a constraint.

---

## 8. Final Recommendation

**Split governance into multiple ADRs first.**

Justification, drawn only from the findings above: the set's overall maturity is high (15 of 20 Adopt outright, zero Reject), which argues against deferring the whole program or launching another investigation — no genuine ontological or evidentiary gap remains that would justify either. But the set is not uniform: it contains one high-stakes recommendation needing concrete operational detail before it is truly ADR-ready (`INV10-R1`), two recommendations that are sound but genuinely premature (`INV9-R2`, `INV11-R7`), and a natural three-wave structure (Section 6) that maps cleanly onto three separately-scoped ADRs rather than one monolithic document. Producing a single governance ADR covering all twenty recommendations at once would either force the two immature items in prematurely, or require artificially holding back seventeen ready recommendations to wait for two that are not — both worse outcomes than proceeding wave by wave, each as its own ADR, in the order Section 6 already establishes.
