# Judgment — Implementation Design

This document is an implementation-design artifact, not a normative document. It carries no Doctrine status (Draft/Final/Superseded/Historical) because those statuses apply to normative documents, and this is not one. Where anything here appears to conflict with the Architecture Doctrine, OE-002 through OE-006, or the Historical Decision Record, those documents govern and this one is wrong and must be corrected.

## 1. Executive Finding

**Judgment is a Final-adopted Domain Object (OE-002 §5.4), and a faithful minimal implementation is derivable: Outcome 1 — Fully Defined Domain Object.**

**One-sentence meaning**: A Judgment is a permanent, independently-identified, Case-owned Domain Object that records the Case's settled characterization of an identified subject — the subject being either content held internally within the Judgment or a reference to another same-Case, already-accepted Domain Object — without asserting that the characterization is objectively true.

**Minimal accepted fields**: `id`, `case_id`, a required characterization (free-text content, minimally — OE-002 does not mandate a discrete or structured vocabulary), an *optional* typed subject reference (`subject_target_type`/`subject_target_id`, present only when the referential form is used), and `recorded_at`. The characterization field is not a convenience — it is canonically **forced**: a Judgment consisting only of a bare subject reference, with no characterization content, would be structurally and semantically indistinguishable from a Knowledge Reference, contradicting the already-settled, Final-adopted distinctness of the six closed-set types (Historical Decision Record). This is the load-bearing finding of this investigation.

One genuine, non-blocking open question is preserved rather than resolved: whether a single Judgment instance may combine both the internal-content and referential forms simultaneously is explicitly left open by OE-002 itself (§5.4, Ownership boundary), exactly as it is for Reasoning Trace's own supported-claim question and Decision's and Outcome's own analogous questions — this design does not resolve it, and does not need to, per Doctrine §7. Judgment does not require, and this design does not add, any Agent/actor, confidence, polarity, status, or Candidate reference — each was tested and rejected on precise canonical grounds, not by default. **Judgment is not related to the rejected "Reasoning Act" concept**, and this design does not reintroduce it.

## 2. Scope

This document designs Judgment's implementation within `docs/atlas_domain_object_architecture/`. It does not redesign Case, identity, or the validation/acceptance model, all reused directly from the Case Representation Strategy and the Complete Validation and Acceptance Redesign. It does not alter the completed Knowledge Reference, Reasoning Trace, or Reasoning Act designs. It does not design Decision, Observation, or Outcome beyond citing their already-published OE-002 definitions where directly relevant to Judgment's own relationships.

## 3. Source Authority and Canonical Sources Reviewed

**Authoritative**: Architecture Doctrine (§7, open questions inside settled decisions; §9, single source of truth); OE-002 §4 (closed type set), §5.4 (Judgment, quoted in full in Section 5), §5.5 (Decision, for its explicit Judgment-reference permission), §6 (relationship topology); OE-003 §4.4 (JudgmentAccepted); OE-004 (INV-002 through INV-006, INV-012); OE-005; OE-006; the Historical Decision Record (for provenance only).

**Prior implementation-design evidence, same track, reused directly**: the completed Knowledge Reference Implementation Design (typed-reference pattern, no-foreign-key policy); the completed and twice-revised Reasoning Trace Implementation Design (the primitive-relation method, the type-tag-carries-semantics analysis, the general reference-validation algorithm); the completed Reasoning Act Implementation Design (confirming that concept's non-adoption, and that no relationship to it should be introduced here); the second investigation in this series, the Legacy CoreLoop Semantic Correspondence & Reducibility Investigation (for its finding that Interpretation, Hypothesis, Conclusion's claim content, Evaluation, and Learning all reduce to Judgment — used here strictly as illustrative, corroborating evidence of what Judgment's two forms look like in existing, pre-migration shapes, never as independent normative authority); the Case Representation Strategy; the Complete Validation and Acceptance Redesign (for the Candidate/accepted-object distinction, directly relevant to Section 16 below).

**Inspected and confirmed non-authoritative**: `docs/atlas_reasoning_foundations/ADR-002-The-Nature-of-Judgment.md` was not re-read in full for this task (its content was already summarized, accurately, in the prior Reasoning Trace and Reasoning Act investigations); its own README is quoted again here for one specific, decisive fact: "*Candidate*, *Confidence*, and *Agent* were terms introduced only by an earlier, rejected candidate definition and were explicitly removed as dependencies" from that ADR — cited only as corroborating, non-authoritative background for Sections 20–21 below, never as governing material.

**Named in prior task briefs but confirmed absent from this repository** (re-confirmed, not re-litigated): "BETA-001," "DFS-001," a "Domain Object registry" distinct from OE-002 itself, "ontology-edge material," "foundation reviews," "mechanics observations." None appears anywhere in this repository.

**Existing code**: a repository-wide, case-insensitive search for "judgment" returned matches only as an ordinary English word in docstrings and comments across the unrelated legacy investment-app tree and in two CoreLoop-adjacent files (`reflection_understanding_formation/understanding.py` and `formation.py`, "whose interpretive judgment..."; `decision_timeline/timeline.py`, "forms a judgment"). **No class, schema, field, table, or test named `Judgment`, `JudgmentId`, or equivalent exists anywhere in `atlas/` or `tests/`.** This confirms, again, the first investigation's own finding: Judgment has no existing implementation.

## 4. Repository Existence and Adoption Check

Judgment is unambiguously **Final-adopted**: it is one of the six named types in OE-002 §4's closed Domain Object Set, with its own dedicated definition in §5.4, its own event (`JudgmentAccepted`, OE-003 §4.4), and no open question about its *existence* — only about one specific internal edge (Section 9, below), exactly as the Historical Decision Record records.

## 5. Explicit Canonical Claims

OE-002 §5.4, quoted in full, since this entire design turns on its exact wording:

> **Definition.** Judgment is a permanent Domain Object that records the Case's settled, Case-relative characterization of an identified subject, without asserting that the characterization is objectively true.
>
> **Identity.** Judgment has stable identity independent of its content and independent of the identity of any subject it references.
>
> **Responsibility.** Judgment is responsible for recording a settled assessment, status, or position that the Case holds regarding its subject. Judgment does not require multiple alternatives, does not assign a mandatory discrete status vocabulary, and does not require prior epistemic support from a Reasoning Trace.
>
> **Ownership boundary.** Judgment's subject MAY be content held internally by the Judgment itself, or a reference to another Domain Object belonging to the same Case. Both forms are independently valid. This document does not establish that both forms may coexist within one undifferentiated Judgment; this is an open question under Section 7 of the Architecture Doctrine. Judgment's root-eligibility depends on which form a given instance uses: an instance whose subject is internal content MAY be the first Domain Object accepted into a Case; an instance whose subject references another Domain Object is not root-eligible.
>
> **Relationships.** Where Judgment's subject is a reference, it MUST be to another same-Case Domain Object; no specific Domain Object type is required. Judgment does not require a Reasoning Trace, a Decision, an Observation, or a Knowledge Reference. Judgment MAY be referenced by other Domain Objects defined in this document; nothing in Judgment's own definition requires this.

Additional directly relevant claims: OE-002 §5.5 (Decision) — "a Judgment, a Reasoning Trace, or an Outcome MAY each serve as this reference [Decision's committed-to matter], but none is required." OE-004 INV-012 — Judgment's root eligibility is conditional on its chosen form, exactly mirroring OE-002 §5.4's own statement. OE-003 §4.4 — "Fact established: that a specific Judgment has been accepted, recording the Case's settled characterization of its subject. Not established: that the characterization is objectively true; anything about which of the two subject-forms was used beyond what OE-002 itself permits."

## 6. Required Distinctions

- **Judgment** — as defined above: a characterization of a subject, not itself the process that produced it, not the subject it concerns, and not an endorsement of truth.
- **Observation** (OE-002 §5.1) — preserves informational content without characterizing it; Judgment characterizes, Observation merely preserves.
- **Hypothesis** — not an adopted type; per the Legacy Correspondence investigation, reduces entirely to Judgment (internal-content form). There is no separate "Hypothesis" for Judgment to relate to (Section 17).
- **Candidate** — not an adopted Domain Object at all; a pre-acceptance construct of the Complete Validation and Acceptance Redesign, categorically ineligible as a reference target for any accepted object, Judgment included (Section 16).
- **Knowledge Reference** (OE-002 §5.2) — a bare reference to a target, asserting reliance without characterization content. Judgment's referential form differs precisely by requiring characterization content *in addition to* its reference — this distinction is the load-bearing argument of this whole design (Section 11).
- **Reasoning Trace** (OE-002 §5.3, as finalized) — a primitive support relation directed at itself; does not characterize anything and is not characterized by anything, as such — though it, like any of the six types, may be cited as another object's reference target where permitted (Section 18).
- **Decision** (OE-002 §5.5) — a practical commitment, not a characterization; may optionally reference a Judgment (Section 19), but is not the same kind of fact.
- **Evaluation, Learning** (legacy) — both reduce to Judgment (Legacy Correspondence investigation); not independently adopted.
- **Ordinary natural-language statements** — many things colloquially called "judgments" (opinions, scores, recommendations) are not automatically this Domain Object; only an accepted instance conforming to OE-002 §5.4's contract is.

## 7. Candidate Designs

**Candidate A — Free-Text Judgment.** Strongest argument: OE-002 explicitly declines to mandate "a discrete status vocabulary," leaving free text as the most conformant, least-inventive minimal representation. Canonical evidence: the Responsibility clause's own silence on structure, combined with the corroborating legacy shape of Hypothesis's and Interpretation's own `Statement` fields. Contradiction: none. **Disposition: Adopted as the minimal default realization of the canonically *required* characterization content** (Section 11) — not merely as documentation, and not as the only conformant format (Test 10, Section 34).

**Candidate B — Structured Proposition.** Canonical evidence: none — OE-002 defines no formal proposition language (subject–predicate–object, logical form, etc.). **Disposition: Rejected** as a requirement; not forbidden as a future implementation choice, but nothing forces it, and inventing one now would exceed canonical text.

**Candidate C — Target Plus Determination.** Tested precisely: the "target" half is adopted (the optional referential subject); the "determination" half, if read as a *discrete, typed* value (e.g., an enum), is directly contradicted by "does not assign a mandatory discrete status vocabulary." **Disposition: Adopted only for its target-reference half; rejected for any mandatory discrete determination vocabulary.** Free-text characterization (Candidate A) fills the role a rigid "determination" value would have played.

**Candidate D — Candidate Selection.** Contradiction: direct — "Judgment does not require multiple alternatives" explicitly rejects any requirement to record or compare multiple candidate options. Additionally, "Candidate" (validation-layer, pre-acceptance) cannot be a valid reference target under INV-005 in any case. **Disposition: Rejected outright, on two independent grounds.**

**Candidate E — Primitive Accepted Judgment.** Tested and found insufficiently minimal: unlike Reasoning Trace, Judgment's type contract is *not* exhausted by admission/exclusion criteria alone — it also forces genuine characterization content (Section 11's non-collapse argument). **Disposition: Rejected as the final characterization** of Judgment, though its underlying method (type-defined semantics, primitivism where forced) is reused for the parts of Judgment that *are* primitive (the alternate-form rule itself).

**Candidate F — Relation Object.** Tested: Judgment's entire content is *not* reducible to relations alone, for the same non-collapse reason. **Disposition: Rejected** as the sole characterization, though the optional subject-reference *is* a relation, correctly captured as one part of a larger design.

**Candidate G — Result of Reasoning.** Directly excluded by this task's own governing instruction and by the completed Reasoning Act finding: no governing source independently forces "result of reasoning" semantics for Judgment; OE-002 §5.4 never mentions a producing act. **Disposition: Rejected.**

**Candidate H — Decision Precursor.** Contradiction: OE-002 §5.4 never states Judgment exists "primarily" for Decision's benefit; OE-002 §5.5 states the reverse relationship as optional, not mandatory, and in Decision's own terms, not Judgment's. **Disposition: Rejected** as ontology; at most a workflow intuition, explicitly excluded from Domain Object content.

**Candidate I — Identity Shell.** Tested directly against Test 4 (Section 34): a shell with only `id`/`case_id`/`recorded_at` and no characterization would be indistinguishable from a bare, contentless association — and, unlike Reasoning Trace's own shell (which had INV-013 to give it content), no invariant here would give a contentless Judgment shell any determinate meaning at all; worse, if it retained a bare subject reference with no characterization, it would collapse into Knowledge Reference. **Disposition: Rejected** — an identity shell alone is not a faithful Judgment.

**Candidate J — Adopted but Structurally Deferred.** Tested and found not to apply: sufficient content and relation semantics *are* derivable (Sections 11, 16–19), so full deferral is not warranted. **Disposition: Rejected** as the final outcome, though the one genuinely open sub-question (both-forms-coexisting) is preserved exactly as OE-002 itself preserves it.

**Candidate K — No Distinct Judgment Needed.** Tested against the explicit Final-adoption bar: no contradiction was found, and no reopening condition is met (Doctrine §8). **Disposition: Rejected**, correctly, per the task's own instruction not to select this without a genuine contradiction.

## 8. Contradiction Analysis

No contradiction exists within the governing track regarding Judgment. The one internally-acknowledged open question (both-forms-coexisting) is explicitly disclosed by OE-002 itself as an open question, not a contradiction, exactly parallel in kind to Reasoning Trace's own deferred supported-claim question and to Decision's and Outcome's own analogous internal/referential deferrals — all four share the identical open-question structure, none blocking its own Final adoption.

## 9. Selected Ontological Meaning

**A Judgment is a permanent, independently-identified, Case-owned Domain Object that records the Case's settled characterization of an identified subject — the subject being either content held internally within the Judgment or a reference to another same-Case, already-accepted Domain Object — without asserting that the characterization is objectively true.** This is Candidate A (for the required characterization content) combined with the adopted, conditional portion of Candidate C (the optional typed subject reference), rejecting Candidates B, D, E (as sole characterizations), F (as sole characterization), G, H, I, and K.

## 10. Domain Object Status

Final-adopted (Section 4); member of OE-002 §4's closed set; independently identified (OE-002 §5.4 Identity clause); permanent (general Domain Object contract, INV-009); belongs to exactly one Case (INV-002); referenceable by other Domain Objects ("Judgment MAY be referenced by other Domain Objects... nothing in Judgment's own definition requires this"); subject to acceptance under the general OE-005/OE-006 model; governed directly by INV-002 through INV-006 and INV-012, and conditionally by INV-004/INV-005 when the referential form is used.

## 11. Judgment Content

**The characterization is canonically forced, not optional, and not merely a documentation convenience.** The argument: OE-002 §5.4's Definition clause states Judgment "records the Case's settled... characterization of an identified subject" — two components are named, a characterization and a subject. If the characterization component were dropped, leaving only a subject reference, the resulting object would be structurally and semantically identical to Knowledge Reference (OE-002 §5.2: a bare reference to a target, asserting reliance without further content). Since the Historical Decision Record confirms Knowledge Reference and Judgment were each independently justified as *distinct* semantic operations during the original ontology investigation (Judgment's operation being "characterization," Knowledge Reference's being "reference to knowledge"), a Judgment with no characterization content would collapse into Knowledge Reference — directly contradicting that already-settled distinctness. Therefore, characterization content is **forced by non-collapse**, not chosen for convenience.

Representation: OE-002 explicitly declines to mandate "a discrete status vocabulary," so the characterization's *internal format* is left open — free text (a `Statement`-like, non-empty-string value object, matching the established, minimal, non-transformation-discipline convention used throughout this codebase) is the smallest, safest, most directly conformant realization, but is not asserted to be the *only* conformant one (Test 10, Section 34); a future, richer structured representation would not contradict OE-002, provided it still carries genuine characterization content and does not impose a *mandatory* discrete vocabulary as a normative requirement on other implementations.

**Corroborating (non-normative) evidence**: the Legacy Correspondence investigation's own findings show exactly this two-part shape already realized twice in this codebase's pre-migration structures — Interpretation (`observation_id` reference + `statement` characterization) for the referential form, and Hypothesis (`statement` characterization alone, no reference) for the internal-content form. This is cited only as illustrative corroboration, never as independent normative authority.

## 12. Truth-Aptness

The characterization content is plausibly truth-apt in the ordinary sense (a natural-language assessment that could, informally, be true or false) — but **acceptance of the Judgment Domain Object does not assert, endorse, or require that this content is objectively true**, per OE-002 §5.4's own explicit disclaimer, mirrored again in OE-003 §4.4 ("Not established: that the characterization is objectively true"). Distinguishing precisely: the Judgment Domain Object's own existence is not itself a truth-bearer — it is a permanent record that a characterization was settled and held; the *content* of that characterization may be true, false, or indeterminate, entirely independent of the object's own valid, permanent existence. Accepting a Judgment does not endorse its truth. An accepted Judgment may later be shown wrong (informally) without this affecting its validity or identity as a Domain Object (Test 6, Section 34). Contradictory Judgments may coexist (Section 25) — nothing in OE-002 requires cross-Judgment consistency, and since no Judgment's truth is asserted by Atlas in the first place, two Judgments asserting incompatible characterizations create no architectural conflict.

## 13. Identity

`JudgmentId`, independently assigned, stable, and — per OE-002 §5.4's own Identity clause — independent both of the Judgment's own content and of the identity of any subject it references. Two Judgments may have identical characterization content and, if referential, identical subject references, and remain two distinct, independently accepted Domain Objects — exactly the same conclusion already reached, on parallel textual grounds, for Knowledge Reference and Reasoning Trace. A revised assessment is represented by accepting a **new**, separate Judgment; the earlier one is never mutated or replaced in place (INV-009/011) — no "supersedes" reference is canonically forced (OE-002 §5.4 never mentions one), though nothing forbids adding an optional, non-constitutive one later if a genuine future need is demonstrated. Presentation or serialization changes never affect identity, consistent with every other type in this series.

## 14. Case Ownership

Exactly one Case per Judgment (INV-002), assigned independently before validation and acceptance, never derived from the subject reference (directly per the Case Representation Strategy's own established rule, reused here without modification), immutable once accepted. Where the referential form is used, the subject MUST belong to the same Case (OE-002 §5.4's own explicit "another same-Case Domain Object"); cross-Case subject references are forbidden (INV-004).

## 15. Subject or Target Semantics

A subject is **not unconditionally mandatory as a separate reference** — it is mandatory as a *concept* (every Judgment characterizes *some* identified subject), but that subject may be realized either as content embedded directly within the characterization itself (internal-content form, no separate reference field populated) or as an explicit reference to another Domain Object (referential form). When referential: exactly one target (OE-002's singular framing throughout — "an identified subject," "a reference," never "one or more"), no specific type restriction, must be same-Case, must already be accepted (INV-005). Duplicate subject references across *different* Judgments are permitted (no uniqueness constraint is justified, per the same reasoning already established for Knowledge Reference's duplicate-target policy). Self-reference is structurally impossible (a candidate is not yet accepted at validation time). Cycles are structurally impossible for the identical prior-acceptance-plus-permanence reason already established twice in this series. The subject is not part of Judgment's own *identity* (per §5.4's Identity clause), but it is part of its *content* when the referential form is used.

## 16. Candidate Relationship

**No relationship is adopted, and none can be, categorically.** "Candidate" (as used in the validation/acceptance model) names a pre-acceptance construct, never itself an accepted Domain Object. INV-005 requires every reference target to already be accepted. A Candidate, by definition, is not yet accepted. Therefore a Judgment cannot reference, select, accept, rank, or reject a Candidate as a stored, accepted relation — this is not merely undemonstrated, it is structurally excluded by the adopted validation model itself. This directly and independently confirms OE-002 §5.4's own explicit statement that "Judgment does not require multiple alternatives": there is no canonical mechanism, and none should be invented, for a Judgment to record which candidate characterizations were considered and rejected before one was accepted — that process, if it occurs at all, belongs entirely to the application/authoring layer, never to the accepted Judgment's own content.

## 17. Hypothesis Relationship

**No relationship is adopted, because "Hypothesis" does not exist as an independent type to relate to.** Per the Legacy Correspondence investigation's own finding, Hypothesis reduces entirely to Judgment (internal-content form) — what was formerly called a Hypothesis simply *is* a Judgment, of a certain use, not a separate category a Judgment could confirm, reject, or reference. The only relationship a Judgment could have "to a Hypothesis" under the adopted six-type architecture is the ordinary, generic case of one Judgment referencing another Judgment as its subject (permitted, since OE-002 places no type restriction on the referential form) — which is not a special "Hypothesis relationship" at all, merely an unremarkable instance of the general rule.

## 18. Reasoning Trace Relationship

**No mandatory relationship in either direction; two independent, generic possibilities exist.** OE-002 §5.4 states directly: "Judgment does not require... prior epistemic support from a Reasoning Trace" — explicitly optional, and phrased as Judgment potentially being informed by a Trace, never the reverse. Separately, and independently, Reasoning Trace's own §5.3 places no type restriction on its supporting objects, so a Judgment **may generically** be cited as one of a Reasoning Trace's supporting objects, exactly like any other of the six types — this is not a special Judgment–Trace relationship, only an ordinary instance of Reasoning Trace's own general rule. The finalized Reasoning Trace design is not altered by this observation, and this design does not turn Reasoning Trace into a provenance record, process record, explanation, or genealogy link to accommodate Judgment — no such accommodation is needed, since the existing generic mechanisms already suffice for whatever incidental relationship might arise.

## 19. Decision Relationship

**No mandatory relationship; one explicit, optional permission, stated on Decision's side.** OE-002 §5.5 states directly: "a Judgment, a Reasoning Trace, or an Outcome MAY each serve as this reference [Decision's committed-to matter], but none is required." This is the only adopted textual connection between Judgment and Decision, and it runs from Decision to Judgment, not the reverse; nothing in Judgment's own §5.4 text mentions Decision at all. Distinguishing precisely: this is **ontology** (an explicitly stated, optional referential permission), not dependency (Decision does not need a Judgment to exist validly), not workflow order (nothing requires Judgments to precede Decisions procedurally), and not a database foreign key stored on Judgment itself (any such reference, if used, is stored on the Decision row, not on the Judgment). A Judgment may exist permanently with no Decision ever referencing it (Test 8, Section 34) — nothing requires otherwise.

## 20. Agent and Authorship

**No actor/author field is adopted, and none is added.** OE-002 §5.4 never mentions an author, holder, or Agent. "Agent" is not an adopted Domain Object anywhere in OE-002 through OE-006. This is directly reinforced by the fourth investigation's own established conclusion (actor identity excluded from Domain Object content generally) and, as non-authoritative corroboration only, by the separate, non-governing track's own README, which records that "Agent" was considered and *explicitly removed* as a dependency from its own Judgment ADR. No `agent_id`, `user_id`, `model_id`, or `created_by` field is included.

## 21. Confidence

**Not adopted; rejected.** No canonical text in OE-002 §5.4 mentions confidence for Judgment. As non-authoritative corroboration only, the separate track's own README records that "Confidence" was likewise considered and explicitly removed as a dependency from its own Judgment ADR. Legacy Decision's own `Confidence` field (0–100) is a separate, already-flagged, unresolved question specific to Decision (from the Decision/Outcome Reference Semantics Investigation) and does not transfer to Judgment; nothing forces or suggests it should. No `confidence` field is included.

## 22. Polarity, Status, and Kind

**None is adopted; all are directly, textually rejected.** OE-002 §5.4 states plainly: Judgment "does not assign a mandatory discrete status vocabulary." No accepted/rejected, positive/negative, true/false, supported/unsupported, pass/fail, selected/not-selected, valid/invalid, kind, category, or polarity field is canonically required, and none is added here.

## 23. Temporal Semantics

Only `recorded_at` is forced by the general Domain Object contract (acceptance/event time, INV-015). Unlike Observation, Decision, and Outcome — each of which OE-002 explicitly discusses in terms of its own investor-supplied "when this happened" timing (`observed_at`, `decided_at`, realization timing) — OE-002 §5.4 is **silent** on any second timestamp for Judgment. This silence is treated precisely: a second, investor-supplied "when this characterization was settled" timestamp is **permitted** (well-corroborated by Interpretation's `interpreted_at` and Hypothesis's `formulated_at`, both pre-migration analogs) but **not canonically forced**, since OE-002 does not name or require it the way it explicitly does for the other three types. This genuine, minor underdetermination is preserved rather than resolved by preference; `recorded_at` alone is the minimal forced field, with a second timestamp left as an open, non-blocking implementation choice.

## 24. Lifecycle and Mutability

Immutable from acceptance, exactly like every other adopted type (INV-009/011): no proposed/in-progress/accepted-pending state exists for an accepted Judgment — it either is accepted (permanent) or does not yet exist as a Domain Object. No `status` field is added (Section 22). A "revised" assessment is a **new**, separately-accepted Judgment (Section 13), never an in-place update. Withdrawal, invalidation, correction, and expiry are not represented by any field; if a Judgment is later considered mistaken, that fact, if ever recorded at all, would itself be recorded as a further, separate accepted fact (e.g., another Judgment characterizing the first one), never as a mutation of the original.

## 25. Contradictory Judgments

**Permitted, without qualification.** OE-002 imposes no consistency requirement across Judgments, and since no Judgment's content is asserted true by Atlas (Section 12), two Judgments reaching opposite conclusions about the same or related subjects create no invariant violation and no uniqueness conflict. No consistency-enforcing constraint is added.

## 26. Acceptance and Authority

Acceptance of a Judgment means exactly what the general OE-006 contract states: the object is admitted into permanent, accepted Case state, and its corresponding `JudgmentAccepted` event has occurred, atomically. **Acceptance does not assert, and must not be read to assert**, that Atlas endorses the characterization's content, that the content is true, reliable, or final, or that the subject (if referenced) has been definitively evaluated in any objective sense — only that the specified characterization, of the specified subject, in the specified Case, is now a permanent, settled fact of record.

## 27. Minimal Accepted Fields

| Field | Type | Nullable | Meaning | Necessity | Semantic/Technical | Source | Invariant |
|---|---|---|---|---|---|---|---|
| `id` | `JudgmentId` (UUID) | No | Identity | OE-002 §5.4 Identity clause | Semantic | OE-002 §5.4 | INV-003/006 |
| `case_id` | `CaseId` | No | Ownership boundary | INV-002 | Semantic | INV-002 | INV-002 |
| `characterization` | `Statement`-like non-empty text (minimal default; see Section 11) | No | The settled assessment/position itself | Forced by non-collapse into Knowledge Reference (Section 11) | Semantic | OE-002 §5.4 Definition/Responsibility | — |
| `subject_target_type` | Enum of six adopted types | Yes (present only for referential form) | Routing/dereferencing for the subject reference | Required only when the referential form is used | Technical (routing) | OE-002 §5.4 Ownership boundary/Relationships | INV-004/005 |
| `subject_target_id` | Typed target identifier | Yes (present only for referential form) | The referenced subject itself | Required only when the referential form is used | Semantic (part of content when present) | OE-002 §5.4 | INV-004/005/012 |
| `recorded_at` | `datetime` | No | Acceptance/event time | INV-015; uniform contract | Technical | INV-015 | INV-015 |

## 28. Rejected and Deferred Fields

| Field | Disposition | Reason |
|---|---|---|
| Discrete status/kind/polarity vocabulary | Forbidden | Directly contradicts "does not assign a mandatory discrete status vocabulary" (OE-002 §5.4). |
| Candidate reference | Forbidden | Categorically excluded — Candidates are pre-acceptance and cannot satisfy INV-005; also directly contradicted by "does not require multiple alternatives." |
| Hypothesis reference | Unresolved as stated, resolved on inspection | No separate Hypothesis type exists to reference; reduces to an ordinary Judgment-to-Judgment reference if ever used. |
| Reasoning Trace reference (mandatory) | Rejected as mandatory | Directly contradicted by "does not require... prior epistemic support from a Reasoning Trace"; permitted only as an ordinary, optional instance of the general referential form. |
| Decision reference | Rejected as a field on Judgment | The adopted relationship runs from Decision to Judgment (OE-002 §5.5), not the reverse; nothing is stored on Judgment for this. |
| Agent/`user_id`/`model_id`/`created_by` | Forbidden | No canonical basis; conflates ontology with authorship/execution (Section 20). |
| Confidence | Rejected | No canonical basis for Judgment specifically (Section 21); Decision's own unresolved Confidence question does not transfer. |
| `supersedes` reference | Deferred | Not canonically forced (OE-002 §5.4 never mentions supersession); permitted as a future, optional, non-constitutive addition if a genuine need is demonstrated, per the same discipline applied to Outcome.decision_id. |
| `status` (proposed/accepted/withdrawn/etc.) | Forbidden | No genuine ontological distinction requires it; conflates Domain Object acceptance with a mutable application-level lifecycle. |
| Rationale / narrative explanation | Forbidden | Would duplicate or exceed the characterization field itself, and risks importing the "narrative rationale" content explicitly excluded for Reasoning Trace by analogy — nothing in OE-002 §5.4 separately requires or permits an additional explanatory field beyond the characterization. |
| Execution metadata (model, prompt, tool, latency) | Forbidden | Platform-observability content, never Domain Object content, per the identical exclusion already established for Reasoning Trace. |
| A structured proposition language (subject–predicate–object tuple) | Deferred | Permitted as a future, richer implementation choice (Section 11), not forced or defined by any canonical source today. |
| Generic/arbitrary JSON payload | Rejected | Would postpone rather than satisfy the forced characterization requirement, and would smuggle in unbounded, unvalidated structure with no canonical basis (Test 11, Section 34). |

## 29. Cardinality

| Relation | Cardinality | Classification |
|---|---|---|
| Cases per Judgment | Exactly one | Adopted (INV-002) |
| Subject references per Judgment | Zero (internal-content form) or exactly one (referential form) — never more than one | Adopted (OE-002 §5.4's singular framing) |
| Candidates per Judgment | Not applicable — categorically excluded | Logically derived (INV-005) |
| Hypotheses per Judgment | Not applicable — no such independent type exists | Logically derived (Legacy Correspondence investigation) |
| Reasoning Traces per Judgment | Zero or one, only if the referential form is used and a Trace happens to be chosen as the subject; never required | Adopted, permissive (OE-002 §5.4, §5.3) |
| Decisions per Judgment | Zero or more, unbounded, but stored on the Decision side, never on the Judgment | Adopted (OE-002 §5.5), not a Judgment-side cardinality |
| Agents per Judgment | Zero (no field) | Adopted by exclusion (Section 20) |
| Confidence values per Judgment | Zero (no field) | Adopted by exclusion (Section 21) |
| Supersession relations per Judgment | Zero, in the minimal design | Proposed/deferred (Section 28) |

## 30. Reference Semantics

Reused directly from the established, twice-applied Knowledge Reference/Reasoning Trace pattern, since the underlying situation genuinely matches (a same-Case reference to an already-accepted object of any adopted type, when present): **typed** (`subject_target_type`/`subject_target_id`); **no type restriction**; **same-Case required** (INV-004, explicit in OE-002 §5.4's own text); **prior-acceptance required** (INV-005); **duplicate references** — not applicable, since there is only ever zero or one subject reference per Judgment, never a set; **role semantics** — a single, fixed role ("subject"), no further role vocabulary needed; **order** — not applicable, singular; **self-reference** — structurally impossible (not yet accepted at validation time); **cycles** — structurally impossible (prior-acceptance ordering plus permanence, the identical DAG argument established twice already); **deletion behavior** — not applicable, since nothing is ever deleted (permanence).

## 31. Persistence Design

One table, `judgments`: `id` (PK, `String`), `case_id` (indexed `String`), `characterization` (`String`, `NOT NULL`), `subject_target_type` (nullable, indexed `String`, CHECK-constrained to the six adopted type names when present), `subject_target_id` (nullable, indexed `String`), `recorded_at` (`String`). A CHECK constraint enforcing "`subject_target_type` and `subject_target_id` are both null or both non-null" is recommended — this enforces the already-established two-form structural rule, not an invented one. No foreign key across the polymorphic subject reference, for the identical reasons already established twice in this series (no precedent anywhere in this codebase, permanence eliminates the dangling-reference risk, and transactional, authoritative re-validation at acceptance is sufficient). No deletion, no update method, append-only. camelCase API serialization follows the established shared convention.

## 32. API Consequences

**Create/capture**: required — accepts (or resolves) a `case_id`, a required characterization, and an optional subject reference. **Read**: required — get by `case_id` + `id`. **Update**: not meaningful — permanence forbids it. **Supersede/withdraw**: not adopted as distinct operations; a revision is simply a new capture of a new Judgment (Section 24). **Delete**: forbidden. **Relate to another object**: not a Judgment-side operation — any Decision or Reasoning Trace choosing to reference a Judgment does so on its own side, via its own capture operation. **Validation**: the same complete-violation-set model established throughout this series, with the alternate-form rule (exactly one of internal/referential) checked as part of completeness, and the subject reference (when present) checked via the same generic algorithm already established for Knowledge Reference and Reasoning Trace.

## 33. Invariants

**Adopted**: INV-002 (single Case ownership); INV-003/INV-006 (distinct identity); INV-004 (same-Case reference, when the referential form is used); INV-005 (prior acceptance of the subject reference, when present); INV-007 (exactly one `JudgmentAccepted` event, structurally trivial, per the established no-separate-artifact conclusion); INV-008 (atomic acceptance); INV-009/010/011 (permanence, non-erasure); INV-012 (conditional root eligibility, depending on chosen form).

**Logically derived**: a Judgment lacking any characterization content collapses into Knowledge Reference and is therefore Invalid or, at minimum, non-conformant (Section 11) — this is not itself one of the fifteen numbered invariants, but follows necessarily from the Historical Decision Record's own settled distinctness finding; self-reference and cycles are structurally impossible (same DAG argument as established twice already); no separate Domain Event artifact is required (OE-003 §3, INV-007).

**Proposed implementation constraints**: a CHECK constraint enforcing the paired-nullability of the subject-reference columns; no foreign key across the polymorphic subject reference; no `update`/`delete` repository method.

**Unresolved candidates**: whether both forms (internal content and reference) may ever coexist within one Judgment instance — explicitly and permanently open per OE-002 §5.4 itself, not resolved here, and not blocking.

## 34. Edge-Case Analysis

**Two Judgments with identical content** — permitted; distinct accepted objects with identical semantic content, per Section 13. **Two contradictory Judgments in one Case** — permitted, per Section 25. **A Judgment with no target** — permitted; this is exactly the internal-content form, fully valid and, per INV-012, root-eligible. **A Judgment with no Candidate/no Hypothesis/no Reasoning Trace/no Decision** — all permitted; none is required (Sections 16–19). **A Judgment made by an unknown Agent** — trivially representable, since no Agent field exists to be unknown. **An imported historical Judgment** — representable under the same completeness/validation/Case-assignment rules as any other; no special import mechanism needed. **An accepted Judgment later shown wrong** — remains a fully valid Domain Object (Section 12; Test 6). **A revised assessment** — a new, separate Judgment (Section 24). **A Judgment about another Judgment** — permitted; an ordinary instance of the referential form with no type restriction. **Self-reference** — structurally impossible. **Cyclic Judgment relationships** — structurally impossible. **A target deleted after acceptance** — impossible under permanence; nothing is ever deleted. **Cross-Case targets** — forbidden (INV-004), yields an Invalid candidate if attempted. **Duplicate references** — not applicable, since there is at most one subject reference per instance. **Content-equivalent Judgments under different IDs** — permitted, per Section 13. **Serialization changes without semantic changes** — fully compatible; identity and content are independent of presentation.

**Test-by-test resolution** (per the task's required Contradiction Tests): **Test 1** — two Judgments may share identical content and remain distinct solely by numerical identity, exactly as for Knowledge Reference and Reasoning Trace. **Test 2** — opposite Judgments about the same subject are permitted; no invariant forbids it (Section 25). **Test 3** — removing the target (internal-content form) leaves a complete proposition, since the characterization is self-contained. **Test 4** — removing the characterization, leaving only a target, leaves *no* Judgment at all — it becomes a Knowledge Reference (Section 11); this is the decisive test that forces the characterization field. **Test 5** — without the type label, the machine-verifiable distinction is the *combination* of a mandatory non-empty characterization field with an *optional* (not mandatory, not a set) typed reference — a shape distinct from Knowledge Reference (mandatory single reference, no required free content) and from Reasoning Trace (mandatory non-empty *set* of references, no free content) alike. **Test 6** — an incorrect Judgment remains fully valid as a Domain Object (Section 12). **Test 7** — a Judgment may exist without any Reasoning Trace; no invariant is violated (Section 18). **Test 8** — a Judgment may exist permanently without any Decision ever referencing it (Section 19). **Test 9** — an unattributed Judgment is fully representable, since no actor field exists (Section 20). **Test 10** — a text-based and a structured-tuple implementation could both conform, provided each still carries genuine characterization content; OE-002 forces the presence of content, not its exact format (Section 11). **Test 11** — arbitrary, unvalidated JSON would not faithfully implement the ontology; it would merely relocate, not resolve, the forced-content requirement, and would smuggle in unbounded structure with no canonical basis. **Test 12** — an accepted-but-false Judgment is directly and explicitly permitted by the architecture (Section 12).

## 35. Existing-Code Impact

Confirmed by direct, repository-wide, case-insensitive search: no class, schema, field, table, migration, API, test, or fixture named `Judgment`, `JudgmentId`, or equivalent exists anywhere in `atlas/` or `tests/`. Every match for the plain word "judgment" is ordinary English prose in docstrings or comments, unrelated to any implemented Domain Object. This is a purely additive design; no existing file requires change, and none should be touched. Future implementation would add a new `atlas/core/domain/judgment/` module (entity, value objects, exceptions, repository), a matching persistence module, a capture/acceptance application service, and eventual API/CLI surfaces — all additive, mirroring Knowledge Reference's own established pattern.

## 36. Unresolved Questions

**Q1 — May both the internal-content and referential forms coexist within a single Judgment instance?** Explicitly and permanently open per OE-002 §5.4 itself; not resolved here, and not resolvable without a genuine forcing function under Doctrine §8. The minimal design (Section 27) does not require resolving this — a conforming implementation may simply enforce "exactly one form, never both, never neither" as its own structural constraint, consistent with every other type's identical, already-adopted open question.

**Q2 — Should a second, investor-supplied "characterization settled at" timestamp be added alongside `recorded_at`?** Genuinely underdetermined (Section 23): well-corroborated by legacy analogs, but not canonically forced by OE-002's own silence on this specific point for Judgment. Smallest safe placeholder: omit it from the minimal design; add it later only if a demonstrated product need arises, following the same discipline already applied to every other optional field in this series.

**Q3 — Should a `supersedes` reference be added?** Deferred (Section 28); no canonical basis exists today, and none is invented.

None of these questions blocks the minimal design in Section 27 from faithfully preserving OE-002 §5.4's adopted meaning.

## 37. Reopening Conditions

Governed entirely by Architecture Doctrine §8, applied identically to every prior investigation in this series: a genuine forcing function requires a newly identified domain fact inexpressible by the current architecture, an unavoidable contradiction, a downstream normative task exposing a real, demonstrated expressive gap, or evidence the original OE-002 investigation omitted a materially distinct candidate or misapplied the Doctrine's method. Convenience, symmetry, richer explanatory ambition, or a desire to resolve the both-forms-coexisting question preemptively do not qualify.

## 38. Final Implementation Recommendation

Adopt the six-field minimal design of Section 27: `id`, `case_id`, a required `characterization` (free text, minimally), an optional typed subject reference (`subject_target_type`/`subject_target_id`), and `recorded_at`. Persist as one table with a paired-nullability CHECK constraint on the subject-reference columns; no foreign key. Enforce the alternate-form rule (exactly one of internal/referential) at validation time, reusing the generic reference-validation algorithm already established for Knowledge Reference and Reasoning Trace where the referential form is used. Introduce no Agent, Candidate, confidence, status, polarity, kind, rationale, or execution-metadata field — each was tested and rejected on precise, stated canonical grounds. Leave the both-forms-coexisting question exactly as open as OE-002 itself leaves it. Touch no existing file in the course of this design, since none currently references Judgment in any implemented form.
