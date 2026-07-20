# Decision — Implementation Design

This document is an implementation-design artifact, not a normative document. It carries no Doctrine status (Draft/Final/Superseded/Historical) because those statuses apply to normative documents, and this is not one. Where anything here appears to conflict with the Architecture Doctrine, OE-002 through OE-006, or the Historical Decision Record, those documents govern and this one is wrong and must be corrected.

## 1. Executive Finding

**Decision is a Final-adopted Domain Object (OE-002 §5.5). Its committed-to matter is a single, unified slot realized as internal content, a typed reference, or — unresolved and therefore currently unadmitted — both at once. Selected outcome: Outcome 3 — Ready With Alternative Content Forms, corrected by the Committed-To Matter Completeness Review (appended at the end of this document) to Storage-Permissive, Admission-Restricted.**

**Correction notice**: the version of this Executive Finding, and of Sections 12, 29, 30, 31, 34, 35, 36, 37, 39, and 41 below, originally stated or implied a hard XOR constraint — "exactly one form, never both" — enforced at both the validation and persistence layers. On review, this was found to silently resolve, in the negative, the very question OE-002 itself leaves open ("this document does not establish that both forms may coexist... this is an open question"). A constraint that makes the combined form *structurally impossible* is not the same as *preserving* an open question — it is a specific, unstated answer to it. This has been corrected throughout, as detailed in the appended review. The corrected position: **at least one form must be present (this remains fully forced, not open); whether both may be present together remains genuinely open; the combined form is, today, representable at the storage layer but not admitted by domain validation, since no interpretation of its meaning has been adopted.**

**One-sentence meaning**: A Decision is a permanent, independently-identified, Case-owned Domain Object that records the Case's settled practical commitment regarding what is to be done — its committed-to matter being content held internally within the Decision, a reference to another same-Case, already-accepted Domain Object, or (unresolved, and not currently admitted) both — without itself executing behaviour, without requiring an Agent, and without asserting that the referenced matter, if any, is true, correct, or will ever be carried out.

**Committed-to matter forms**: at least one of (a) internal commitment content (free text, minimally), or (b) a typed reference to another same-Case, already-accepted Domain Object of any adopted type (OE-002 names Judgment, Reasoning Trace, and Outcome as illustrative examples, explicitly stating "no specific Domain Object type is required" — these are examples, not an exhaustive restriction). Whether both may be present simultaneously is explicitly left open by OE-002 itself; this design neither forbids nor permits that combination at the persistence layer, but does not currently admit it through ordinary domain validation, since no adopted interpretation exists for what a combined instance would mean (Section 12; the appended review). Neither form is textually paired with a *separate*, forced characterization field the way Judgment's referential form is — this remains a genuine, precise structural difference from Judgment, driven directly by OE-002's own grammar: Judgment is defined as a "characterization *of* an identified subject" (two named parts); Decision is defined by a single "committed-to matter" (one part, mirroring Outcome's own "realized matter").

**Minimal accepted fields**: `id`, `case_id`, `commitment_content` (free text, nullable) and/or `matter_target_type` + `matter_target_id` (typed reference, nullable pair) with at least one realization required and their simultaneous presence structurally representable but not currently domain-admitted, and `recorded_at`. No Agent, Candidate, execution, status, finality, or supersession field is included — each was tested against explicit canonical text and rejected on precise, stated grounds, most directly OE-002 §5.5's own closing sentence: "Decision remains a valid record regardless of whether it is later executed, remains executable, produces a recorded Outcome, or is superseded by a later Decision."

This investigation also confirms that Decision, unlike every other type in this series so far, **already has a substantial existing implementation** in this repository. Its relationship to that existing code — specifically the already-flagged, still-unresolved status of `decision_type`, `confidence`, and `source` as possible extra content — is reported precisely in Section 38, reusing and not re-litigating the second and third investigations' own established findings.

## 2. Scope

This document designs Decision's implementation within `docs/atlas_domain_object_architecture/`. It does not redesign Case, identity, or the validation/acceptance model. It does not alter the completed Knowledge Reference, Reasoning Trace, Reasoning Act, or Judgment designs. It does not re-resolve the already-flagged, already-scoped-elsewhere questions about Decision's legacy `decision_type`/`confidence`/`source` fields or the Outcome-reference-direction question — both are cited from the second and third investigations, not re-derived here.

## 3. Source Authority and Canonical Sources Reviewed

**Authoritative**: Architecture Doctrine (§7, §9, §14); OE-002 §4 (closed type set), §5.5 (Decision, quoted in full in Section 5), §5.4 (Judgment, for comparison), §5.2 (Knowledge Reference, for comparison), §5.3 (Reasoning Trace, for comparison), §5.6 (Outcome, for its own reciprocal reference statement), §6 (relationship topology); OE-003 §4.5 (DecisionAccepted); OE-004 (INV-002 through INV-006, INV-012); OE-005; OE-006; the Historical Decision Record (provenance only).

**Prior implementation-design evidence, same track, reused directly**: the completed Knowledge Reference Implementation Design (typed-reference, no-FK pattern); the completed and twice-revised Reasoning Trace Implementation Design (primitive-relation and type-tag method); the completed Reasoning Act Implementation Design (confirming that concept remains unintroduced here); the completed Judgment Implementation Design (its own minimal-field structure is used here as a direct point of *contrast*, not a template, given the genuine grammatical difference identified in Section 12); the Legacy CoreLoop Semantic Correspondence & Reducibility Investigation (Decision's direct legacy correspondence, no migration needed); the Decision/Outcome Reference Semantics Investigation (the still-unresolved `decision_type`/`confidence`/`source` question, and the resolved `decision_id`-on-Outcome finding, both reused by citation, not re-derived); the Investor Identity and Accepted-State Permanence Resolution (`user_id`'s demotion to non-semantic compatibility metadata, reused by citation); the Case Representation Strategy; the Complete Validation and Acceptance Redesign.

**Inspected and confirmed non-authoritative**: no new inspection of `docs/atlas_reasoning_foundations/` was needed for this task; nothing in that track discusses "Decision" as a primitive, and its established non-governing status (confirmed in every prior investigation of this series) is unchanged.

**Named in prior task briefs but confirmed absent from this repository** (not re-litigated): "BETA-001," "DFS-001," a "Domain Object registry" distinct from OE-002, "ontology-edge material," "foundation reviews," "mechanics observations."

**Existing code**: unlike every other type investigated in this series, **Decision already has a substantial existing implementation**: `atlas/core/domain/decision/{entity.py,value_objects.py,exceptions.py,repository.py}`, `atlas/core/application/decision/capture_decision.py`, `atlas/core/infrastructure/persistence/decision/{table.py,sqlalchemy_repository.py}`, `atlas/core/infrastructure/api/decision/{router.py,schemas.py,dependencies.py,errors.py}`, and a full test suite — all previously inspected in depth across the first, second, third, and fourth investigations of this series. This document does not re-inspect these files line-by-line again; it cites the already-established findings precisely (Section 38).

## 4. Repository Existence and Adoption Check

Decision is unambiguously **Final-adopted**: one of the six named types in OE-002 §4's closed Domain Object Set, with its own dedicated definition in §5.5, its own event (`DecisionAccepted`, OE-003 §4.5), and no open question about its *existence* — only about one specific internal edge (Section 9), exactly parallel in kind to Judgment's, Reasoning Trace's, and Outcome's own analogous open questions.

## 5. Explicit Canonical Claims

OE-002 §5.5, quoted in full:

> **Definition.** Decision is a permanent Domain Object that records the Case's settled practical commitment regarding what is to be done, without itself executing behaviour.
>
> **Identity.** Decision has stable identity independent of its content and independent of the identity of any object it references.
>
> **Responsibility.** Decision is responsible for recording that the Case has settled on a determinate practical commitment. Decision does not require multiple alternatives, does not require an Agent, and does not itself constitute or perform execution of any kind.
>
> **Ownership boundary.** Decision's committed-to matter MAY be content held internally by the Decision itself, or a reference to another Domain Object belonging to the same Case. Both forms are independently valid. This document does not establish that both forms may coexist within one undifferentiated Decision; this is an open question under Section 7 of the Architecture Doctrine. Decision's root-eligibility depends on which form a given instance uses, following the same pattern as Judgment.
>
> **Relationships.** Where Decision's committed-to matter is a reference, it MUST be to another same-Case Domain Object. No specific Domain Object type is required; a Judgment, a Reasoning Trace, or an Outcome MAY each serve as this reference, but none is required. Decision does not require a prior Judgment, Reasoning Trace, or Outcome. Decision remains a valid record regardless of whether it is later executed, remains executable, produces a recorded Outcome, or is superseded by a later Decision.

Additional directly relevant claims: OE-002 §5.6 (Outcome) — "Outcome MAY be referenced by a Decision or by a Reasoning Trace as one permissible target among others" (the reciprocal statement, already analyzed in the Decision/Outcome investigation). OE-004 INV-012 — Decision's root eligibility is conditional on its chosen form, exactly mirroring Judgment's own text. OE-003 §4.5 — "Not established: that the Decision has been, will be, or can be executed; any consequence of the commitment."

## 6. Required Distinctions

- **Decision** — as defined above: a practical commitment, not a characterization (contrast Judgment), not a reliance-on-knowledge (contrast Knowledge Reference), not a support relation (contrast Reasoning Trace), not a realized state of affairs (contrast Outcome).
- **Action, execution, command, plan, authorization** — none of these is asserted or required by Decision's existence; OE-002 §5.5 explicitly and repeatedly disclaims execution content (Section 16).
- **Recommendation** — a recommendation is typically addressed to someone else for their own choice; a Decision records that the Case *itself* has already settled the matter, not that it is recommending anything to a further decision-maker.
- **Judgment with stronger finality** — tested directly in Section 8 (Candidate H) and rejected: Decision and Judgment are independently adopted, differently-shaped types with different definitional grammar (Section 12), not one type with an extra flag.
- **Candidate** — as established for Judgment, a pre-acceptance validation construct, categorically ineligible as a reference target (Section 15).
- **Outcome** — a realized state of affairs; Decision may optionally reference an Outcome (as one example among others), but Decision itself asserts nothing about realization.

## 7. Candidate Designs

**Candidate A — Internal Commitment Content.** Strongest argument: matches OE-002's own permitted internal-content form directly. Canonical evidence: "committed-to matter MAY be content held internally by the Decision itself." **Disposition: Adopted, as one of the two alternative realizations of the single committed-to-matter slot** (Section 12) — not as the sole or mandatory form.

**Candidate B — Judgment Commitment.** Tested precisely: is a Judgment reference *mandatory*? No — OE-002 states "none is required," and additionally names Reasoning Trace and Outcome as equally permitted examples, with "no specific Domain Object type is required" beyond that. **Disposition: Rejected as mandatory or as the exclusive referential target**; adopted only as one example among an otherwise-unrestricted reference form.

**Candidate C — Alternative Content Forms.** Directly and precisely adopted: the two forms are alternatives realizing one slot, exactly as OE-002's own Ownership Boundary clause states, with their possible coexistence explicitly and deliberately left open (Section 9). **Disposition: Adopted as the selected structure** (Section 9, Section 12).

**Candidate D — Internal Content Plus Optional Judgment.** Tested directly against Judgment's own two-part grammar ("characterization *of* a subject") versus Decision's one-part grammar ("committed-to matter," mirroring Outcome). Decision's own text never names a separate, additional content field alongside a reference the way Judgment's does. **Disposition: Rejected** as textually unsupported for Decision specifically — this is the single most important structural distinction this investigation establishes, and is not assumed by analogy to Judgment.

**Candidate E — Generic Target Relation.** Tested against the exact wording: "No specific Domain Object type is required" is itself the canonical basis for *not* restricting the referential form to Judgment alone. **Disposition: Adopted, precisely bounded** — any of the six adopted types is a permitted reference target when the referential form is used, per OE-002's own explicit disclaimer of type restriction, not merely "generalized" beyond what the text supports.

**Candidate F — Action Instruction.** Contradiction: directly and repeatedly excluded — "without itself executing behaviour," "does not itself constitute or perform execution of any kind." **Disposition: Rejected outright.**

**Candidate G — Workflow State.** Contradiction: no canonical text names or requires any status vocabulary for Decision; OE-002's own closing sentence ("remains a valid record regardless of whether it is... superseded") directly forecloses a mutable current/superseded status distinction. **Disposition: Rejected.**

**Candidate H — Judgment With Finality.** Tested for semantic collapse: Decision and Judgment have textually distinct definitions (practical commitment vs. characterization), distinct grammar (one-part matter vs. two-part characterization-of-subject), and are each independently Final-adopted, closed-set members. **Disposition: Rejected** — no collapse is warranted or supported.

**Candidate I — Commitment Primitive.** Tested: is "commitment" itself best understood as a primitive, stipulated architectural term (Doctrine §14), analogous to Reasoning Trace's "support" and Knowledge Reference's "reliance"? **Disposition: Adopted, as the correct general characterization of the relation's own nature** (Section 8) — while still recognizing the internal-content form carries genuine, substantive content of its own, not merely a bare relation.

**Candidate J — Identity Shell.** Tested directly (Test 1, Section 37): removing all committed-to-matter content leaves no complete Decision — OE-002's own Definition requires "regarding what is to be done" to be identifiable, which an empty shell cannot supply. **Disposition: Rejected** as insufficient alone.

**Candidate K — Adopted but Structurally Deferred.** Tested and found not to apply: sufficient content and relation semantics *are* derivable (Sections 9–15), so full deferral is unwarranted; only the already-acknowledged, narrower open question (both-forms-coexisting) remains open, exactly as Doctrine §7 permits without blocking. **Disposition: Rejected** as the final outcome.

## 8. Contradiction Analysis

No contradiction exists within the governing track regarding Decision. The one internally-acknowledged open question (both-forms-coexisting) is explicitly disclosed by OE-002 itself, not a contradiction, and is structurally identical in kind to Judgment's, Reasoning Trace's, and Outcome's own analogous deferrals.

## 9. Selected Ontological Meaning

**A Decision is a permanent, independently-identified, Case-owned Domain Object that records the Case's settled practical commitment regarding what is to be done — its committed-to matter being either content held internally within the Decision or a reference to another same-Case, already-accepted Domain Object of any adopted type — without itself executing behaviour, without requiring an Agent, and without asserting that the referenced or described matter is true, correct, or will ever be carried out.** This is Candidate C (alternative content forms), informed by Candidate I's primitivist framing of "commitment" itself, rejecting Candidates B (as mandatory or exclusive), D (as textually unsupported for Decision), F, G, H, and J.

## 10. Domain Object Status

Final-adopted (Section 4); member of OE-002 §4's closed set; independently identified (OE-002 §5.5 Identity clause); permanent (INV-009); belongs to exactly one Case (INV-002); referenceable by other Domain Objects (implicit — nothing forbids it, and Section 28 identifies the generic mechanisms by which it could be); subject to acceptance under the general OE-005/OE-006 model; governed directly by INV-002 through INV-006 and INV-012, and conditionally by INV-004/INV-005 when the referential form is used.

## 11. Commitment Semantics

"Commitment" is treated as a primitive, stipulated architectural term (Doctrine §14), not imported from legal, psychological, organizational, or workflow usage. Precisely: **the Case is the committing entity**, not an Agent — this follows directly from the Definition clause's own grammar ("the Case's settled practical commitment") and is independently, doubly confirmed by the Responsibility clause's explicit "does not require an Agent." The Decision is the *record* of that commitment, not a separate act distinct from the record — there is no adopted notion of "the commitment" existing independently of the accepted Decision object itself. The object of commitment is "what is to be done" — practically, not epistemically, oriented, distinguishing it from Judgment's characterizing orientation. Commitment does **not** imply that future action will actually occur (Section 16), does not imply endorsement of any referenced object's truth (Section 14), and does not imply exclusivity or irrevocability (Sections 22–23) — only permanent retention of the settled fact that this commitment was made. Commitment *can* later be practically superseded by a further Decision, without the original Decision ever being deleted, mutated, or invalidated (Section 23).

## 12. Committed-To Matter

**The committed-to matter is one unified slot, not two separate fields.** This is the single most important structural finding of this investigation, and it depends on a precise comparison of grammar across OE-002's own object definitions:

- **Judgment** (§5.4): "records... a **characterization** *of* an identified **subject**" — two named concepts (characterization, subject), with the Ownership Boundary clause describing only the *subject's* form as internal-or-referential, while the characterization is separately, always present as internal content (per the Judgment Implementation Design's own Section 11 finding).
- **Decision** (§5.5) and **Outcome** (§5.6): each is defined around a single named concept — "committed-to matter" and "realized matter" respectively — with the Ownership Boundary clause describing *that one concept's own* form as internal-or-referential. Neither definition names a second, separate content component alongside it.

Given this precise textual difference, Decision's committed-to matter must be read as **at least one of** {internal content, a typed reference} — never a required content field *plus* an independently optional reference, unlike Judgment. **Whether the two forms may coexist within a single instance is explicitly, deliberately left open by OE-002 itself** ("This document does not establish that both forms may coexist within one undifferentiated Decision; this is an open question under Section 7 of the Architecture Doctrine") — this design does not resolve it, and does not need to, per Doctrine §7, since the minimum contract (at least one form present) is fully statable without resolving it. **Corrected by the appended Committed-To Matter Completeness Review**: a hard XOR (forbidding both) would itself resolve this open question, in the negative, exactly as much as an inclusive-OR-with-assigned-meaning would resolve it in the positive. The faithful position is that the *minimum-presence* requirement (at least one) is forced and settled, while the *combined-presence* question is neither forced to be forbidden nor forced to be permitted — it is genuinely undecided, and is treated here as representable-but-not-currently-admitted (Section 34, and the appended review).

When the internal-content form is used: the content is free-form text describing the commitment (e.g., what is to be done), with no separate "target" field. When the referential form is used: the reference alone constitutes the complete committed-to matter — OE-002's text does not require any additional free-text content alongside it, and none is added here without canonical basis (directly contrasting with the Judgment design's own forced, separate characterization field).

## 13. Internal Content

When used, internal commitment content is free-form text (a `Statement`-like, non-empty-string value object, matching the established codebase convention), sufficient on its own to constitute the complete committed-to matter — not documentary, but genuinely semantic, since it *is* the practical matter the Case has settled on, per OE-002's own Definition clause. No structured action language, instruction schema, or formal commitment grammar is canonically required; OE-002 imposes no structure beyond requiring that *some* determinate matter be identifiable.

## 14. Relationship to Judgment

**No mandatory relationship; one explicit, optional permission.** A Decision may, but need not, use a Judgment as its committed-to matter's referential target — one of three explicitly named examples, alongside Reasoning Trace and Outcome, under an otherwise unrestricted reference rule. This is not a special "Decision–Judgment" relationship distinct from Decision's general referential mechanism; it is simply that ordinary mechanism applied to one particular, textually-illustrated target type. Multiple Decisions may reference the same Judgment (no uniqueness constraint is justified, per the same reasoning already established three times in this series). A Decision may commit to internal content *or* a Judgment reference, never both required together, with their simultaneous coexistence left open exactly as Section 12 states. The Judgment Implementation Design's own finding — that Judgment has no mandatory Decision relation — is fully preserved and not contradicted here: the relationship, where it exists at all, is optional and stated entirely on Decision's own side.

## 15. Judgment Truth Versus Decision Commitment

**Referencing a Judgment as committed-to matter does not endorse that Judgment's truth.** This directly follows both from Judgment's own truth-disclaimer (OE-002 §5.4, "without asserting that the characterization is objectively true") and from Decision's own silence on the matter — nothing in OE-002 §5.5 adds a new truth-assertion on top of whatever the referenced Judgment already does or does not assert. Constructed case: an accepted Judgment whose content is false; a Decision references it as committed-to matter; no execution ever occurs. What remains true in the ontology: the Judgment remains a valid, permanent accepted fact (its falsity does not affect its validity, per the Judgment design's own Section 12); the Decision remains an equally valid, permanent accepted fact (its validity depends only on the referenced Judgment being an already-accepted, same-Case object — not on that Judgment's content being true); and nothing about the absence of execution affects either object's validity (Section 16). The Decision asserts only that the Case settled on committing to that specific, already-accepted Judgment as its practical matter — nothing stronger.

## 16. Choice and Alternatives

**No Candidate relationship; none is possible.** Directly, textually confirmed twice over: "Decision does not require multiple alternatives" (explicit disclaimer), and, independently, "Candidate" (the validation-layer, pre-acceptance construct) cannot satisfy INV-005's already-accepted-target requirement, categorically excluding it as a reference target regardless of the explicit disclaimer. Decision records only the matter ultimately settled on; the existence of any unselected alternatives, if such a process ever occurred at the application/authoring layer, is not semantically relevant to, and is not recorded by, the accepted Decision object.

## 17. Action and Execution

**No action or execution content is adopted; none is added.** Directly and repeatedly confirmed by OE-002 §5.5's own text: "without itself executing behaviour"; "does not itself constitute or perform execution of any kind"; and, most decisively, "Decision remains a valid record regardless of whether it is later executed, remains executable, produces a recorded Outcome, or is superseded by a later Decision." A Decision may exist permanently even if nothing is ever carried out (Test 6); execution may fail entirely without invalidating the Decision (Test 7) — OE-003 §4.5 independently confirms: "Not established: that the Decision has been, will be, or can be executed; any consequence of the commitment." Execution, if it occurs, may produce a *separate*, independently-accepted Outcome — but this is never required, and Decision's own validity never depends on it. No `executed`, `completed`, or `failed` field is added; action tracking is deliberately, explicitly outside this ontology.

## 18. Authority and Actor

**No actor/author field is adopted, and none is added.** OE-002 §5.5 states directly: "does not require an Agent." "Agent" is not an adopted Domain Object anywhere in OE-002 through OE-006. The semantic committing entity is the Case itself (Section 11), not any actor. This directly reinforces, rather than reopens, the fourth investigation's own already-settled finding that Decision's legacy `user_id` field has no future semantic role and must not participate in Decision's accepted content going forward (Section 38). No `agent_id`, `authority_id`, `approved_by`, or `created_by` field is included.

## 19. Identity

`DecisionId`, independently assigned, stable, and — per OE-002 §5.5's own Identity clause — independent both of the Decision's own content and of the identity of any object it references. Two Decisions may commit to identical content, or reference the identical Judgment, and remain two distinct, independently accepted Domain Objects — the same conclusion already reached, on parallel textual grounds, for Knowledge Reference, Reasoning Trace, and Judgment. Repeated commitment to the same matter, and reversal via a contrary later commitment, each create a **new**, separate Decision; the earlier one is never mutated, replaced, or deleted (INV-009/011; and explicitly, "remains a valid record regardless of whether it is... superseded"). Since no Agent field exists, there is no actor-identity dimension to Decision's own identity criterion at all.

## 20. Case Ownership

Exactly one Case per Decision (INV-002), assigned independently before validation and acceptance, never derived from any referenced object, immutable once accepted — the identical, already-established discipline reused here without modification. Where the referential form is used, the referenced object MUST belong to the same Case (INV-004, explicit in OE-002 §5.5's own text: "MUST be to another same-Case Domain Object").

## 21. Truth-Aptness

The Decision object itself is not straightforwardly truth-apt in the way a characterization is — a practical commitment is not, in ordinary usage, the kind of thing assessed as simply "true" or "false," though its internal content (if free text) may describe a matter that could informally be judged wise or unwise, and its referential target's own content (if a Judgment) carries whatever truth-aptness *that* object independently has. A Decision remains ontologically valid even when its referenced Judgment is later shown wrong (Section 15), and remains valid even if the practical commitment itself later proves to have been a poor one — existence and quality are kept strictly distinct; acceptance never endorses correctness, wisdom, or eventual success.

## 22. Finality

**Permanent retention, not exclusivity or irrevocability.** "Settled" refers to the *record's* own permanence (INV-009/011), not to the practical matter being forever fixed or beyond future reconsideration. A later, contrary Decision does not retroactively unsettle or invalidate the earlier one — both remain permanently valid historical facts, directly and explicitly confirmed by OE-002's own closing sentence. No `final`, `active`, or `current` field is added; the architecture draws no distinction between a "currently operative" and a "historical" Decision — that would be an invented status concept with no canonical basis.

## 23. Supersession and Reversal

**No supersession mechanism, status flag, or deletion is adopted.** A later Decision addressing the same or a contrary matter is simply a new, independent, additionally-accepted Decision (Section 19); the earlier Decision is never mutated, superseded-in-the-sense-of-altered, withdrawn, revoked, or deleted — it remains, permanently, exactly as accepted. Supersession, where it occurs at all, is a purely extrinsic, informal fact about a later Decision's mere existence — never an intrinsic, stored property of either Decision. This directly follows OE-002's own closing sentence and mirrors the identical "new fact, not a mutation" discipline already established for Knowledge Reference, Reasoning Trace, and Judgment alike.

## 24. Temporal Semantics

Only `recorded_at` is forced by the general contract (acceptance/event time, INV-015). Unlike the newly-analyzed Judgment (which OE-002 is silent about regarding a second timestamp), **Decision's existing implementation already carries its own investor-supplied `decided_at` timestamp**, and this is well-grounded: OE-002's own Definition frames Decision around "what is to be done," a practically-oriented commitment with a natural "moment of deciding" distinct from Atlas's own acceptance clock — directly paralleling Observation's `observed_at` and Outcome's `occurred_at`. This design confirms `decided_at` (or an equivalently-named investor-supplied timestamp) as a well-corroborated, permitted field, consistent with — and not disturbing — the existing implementation's own established shape; it is not, however, separately re-derived as canonically *forced* by OE-002's own abstract text alone, which (like Judgment) does not explicitly name a second timestamp requirement. No `effective_at` or `expires_at` field is adopted — nothing in OE-002 supports a distinct "when this commitment takes effect" or "when it lapses" concept; both would import unadopted temporal/finality semantics (Section 22).

## 25. Lifecycle and Mutability

Immutable from acceptance (INV-009/011): no proposed/pending/active/executed/failed/withdrawn/superseded/expired state exists for an accepted Decision — it either is accepted (permanent) or does not yet exist as a Domain Object. No `status` field is added (Section 17, Section 23). A changed commitment is represented by accepting a new, separate Decision, never an update to the existing one.

## 26. Relationship to Reasoning Trace

**No mandatory relationship in either direction; two independent, generic possibilities, one of them explicitly disclaimed as required.** OE-002 §5.5 states directly: "Decision does not require a prior Judgment, Reasoning Trace, or Outcome" — explicitly optional. A Decision may, in its own referential form, use a Reasoning Trace as its committed-to matter (one of the three named examples). Separately and independently, a Decision may generically be cited as one of a Reasoning Trace's supporting objects, since Reasoning Trace places no type restriction on its supporters. Neither is mandatory; neither creates a special Decision–Trace relationship beyond the ordinary, already-established generic mechanisms. The finalized Reasoning Trace design is not altered, and this design does not turn it into a justification, explanation, provenance chain, or process record to accommodate Decision.

## 27. Relationship to Knowledge Reference

**No mandatory or special relationship.** Knowledge Reference's own text ("MAY reference any other Domain Object... No specific Domain Object type is required as its target") permits a Knowledge Reference to target a Decision, exactly as it would permit targeting any of the six adopted types — a generic possibility, not a Decision-specific rule. Symmetrically, Decision's own referential committed-to-matter form could, in principle, reference a Knowledge Reference (since Decision's own "no specific Domain Object type is required" disclaimer excludes no type), though this is not named as one of OE-002's three illustrative examples. Decision does not "contain" Knowledge References in any special structural sense; any such relationship is exactly an ordinary instance of each type's own already-established generic reference rule.

## 28. Other Domain Object Relationships

| Type | Direction | Optional/Mandatory | Cardinality | Same-Case | Prior Acceptance | Storage |
|---|---|---|---|---|---|---|
| Observation | Decision → Observation (generic, unnamed example) | Optional | Zero or one | Required if used | Required if used | On Decision, if referential form used |
| Knowledge Reference | Either direction (generic) | Optional | Zero or one/more, on the referencing side | Required if used | Required if used | On whichever side references the other |
| Reasoning Trace | Decision → Trace (named example); Decision as a Trace's supporter (generic) | Optional, both directions | Zero or one (as Decision's matter); unbounded (as a cited supporter) | Required if used | Required if used | On Decision (as matter) or on the Trace (as supporter) |
| Judgment | Decision → Judgment (named example) | Optional | Zero or one | Required if used | Required if used | On Decision |
| Decision → Decision | Generic, unnamed example | Optional | Zero or one | Required if used | Required if used | On the referencing Decision |
| Outcome | Decision → Outcome (named example); Outcome → Decision (per OE-002 §5.6, separately, non-constitutively — see the Decision/Outcome investigation) | Optional, both directions, but semantically distinct (see below) | Zero or one each | Required if used | Required if used | On whichever side references the other |

No workflow graph is inferred from the mere ordering of OE-002's own type definitions; every relationship listed above is stated or directly implied by explicit text, not by sequence. The Outcome relationship specifically is *not* symmetric in meaning: Decision-to-Outcome (Decision's own committed-to matter referencing an Outcome) is Decision choosing to commit around an already-realized state of affairs; Outcome-to-Decision (the already-resolved `Outcome.decision_id` design) is a separate, non-constitutive, optional association, per the Decision/Outcome Reference Semantics Investigation's own final resolution — not re-derived here.

## 29. Acceptance

Acceptance of a Decision means exactly what the general OE-006 contract states: the object is admitted into permanent, accepted Case state, and its corresponding `DecisionAccepted` event has occurred, atomically. **Acceptance does not assert** that the committed-to matter is true, that execution is authorized or has begun, that alternatives were evaluated, or that the Decision is final in any exclusivity sense — only that the specified commitment, in the specified Case, is now a permanent, settled fact of record. The committed-to matter must be fully complete and determinate at acceptance time — **corrected**: at least one of the two forms must be present and well-formed (this is forced); a candidate presenting *both* forms is not accepted today, not because it violates a forced invariant, but because no interpretation of simultaneous presence has been adopted (Section 12; the appended review) — such a candidate is classified Invalid, with a distinctly-labeled, non-numbered finding, never silently accepted and never treated as an ordinary INV-nnn violation. An incomplete or absent committed-to matter cannot be accepted (Test 1, Section 37).

## 30. Minimal Accepted Fields

| Field | Type | Nullable | Meaning | Necessity | Semantic/Technical | Source | Invariant |
|---|---|---|---|---|---|---|---|
| `id` | `DecisionId` (UUID) | No | Identity | OE-002 §5.5 Identity clause | Semantic | OE-002 §5.5 | INV-003/006 |
| `case_id` | `CaseId` | No | Ownership boundary | INV-002 | Semantic | INV-002 | INV-002 |
| `commitment_content` | `Statement`-like text | Yes — present only when the internal-content form is used | The committed-to matter itself, in internal-content form | Required when this form is chosen (Section 12) | Semantic | OE-002 §5.5 Ownership boundary | — |
| `matter_target_type` | Enum of six adopted types | Yes — present only when the referential form is used | Routing/dereferencing for the committed-to-matter reference | Required when this form is chosen | Technical (routing) | OE-002 §5.5 Relationships | INV-004/005 |
| `matter_target_id` | Typed target identifier | Yes — present only when the referential form is used | The referenced committed-to matter itself | Required when this form is chosen | Semantic | OE-002 §5.5 | INV-004/005/012 |
| `recorded_at` | `datetime` | No | Acceptance/event time | INV-015 | Technical | INV-015 | INV-015 |

**At least one** of `commitment_content` or the `matter_target_type`/`matter_target_id` pair must be present — a minimum-presence rule, **not an XOR** (corrected from the original version of this document, which had imposed a hard XOR and thereby silently forbidden the combined form rather than preserving it as open; see the appended Committed-To Matter Completeness Review). The persistence schema permits both to be populated simultaneously (no CHECK constraint forbids it, preserving forward compatibility, Test 1 of the appended review); ordinary domain-layer capture and acceptance, however, currently construct and admit only the content-only and reference-only cases, since no adopted interpretation exists for the combined case (Section 12; Section 34). This is a genuine, load-bearing distinction between what the *schema* can represent and what the *domain* currently admits — contrast Judgment's design, where the content field is always required and the reference is independently, unconditionally optional, a different structure entirely.

## 31. Rejected and Deferred Fields

| Field | Disposition | Reason |
|---|---|---|
| `agent_id`/`user_id`/`authority_id`/`approved_by`/`created_by` | Forbidden | No canonical basis; directly contradicts "does not require an Agent"; reinforces, does not reopen, the already-settled Investor Identity finding. |
| Candidate reference | Forbidden | Categorically excluded (INV-005) and directly contradicted by "does not require multiple alternatives." |
| `status` (pending/active/executed/failed/withdrawn/superseded/expired) | Forbidden | Directly contradicted by "remains a valid record regardless of whether it is later executed... or is superseded." |
| `executed_at`/`completed_at` | Forbidden | Execution is explicitly, repeatedly excluded from Decision's ontology (Section 17). |
| `effective_at`/`expires_at` | Forbidden | No canonical basis; would import unadopted finality/temporal-scope semantics (Section 22, Section 24). |
| `supersedes_id` | Deferred | Not canonically forced; OE-002 §5.5 never mentions a supersession reference. Permitted as a future, optional, non-constitutive addition if a genuine need is demonstrated, per the same discipline applied to Outcome's own `decision_id`. |
| `rationale` (free-standing, beyond `commitment_content`) | Rejected as a separate field | Would duplicate the committed-to-matter content itself; nothing in OE-002 §5.5 names a distinct rationale concept separate from the matter itself. |
| `kind` (a decision-type discriminator) | Deferred, not resolved here | This corresponds to legacy `decision_type`; its status as permissible internal-content structure versus extra, unresolved semantics was already flagged, and left open, by the Decision/Outcome Reference Semantics Investigation — not re-resolved in this document. |
| Action or instruction payload | Forbidden | Directly excluded — "without itself executing behaviour." |
| Confidence | Deferred, not resolved here | Corresponds to legacy `confidence`; same already-flagged, still-open status as `decision_type` (Section 38); not independently re-derived or resolved by this investigation, and — separately — no basis exists for treating it as *forced* Decision content the way `commitment_content` is. |
| Generic/arbitrary JSON payload | Rejected | Would postpone rather than satisfy the forced minimum-presence content requirement, smuggling in unbounded, unvalidated structure with no canonical basis. |
| A hard database XOR constraint (both fields mutually exclusive at the schema level) | Rejected (corrected) | Would silently decide, in the negative, OE-002's own explicitly preserved open question about combined-form coexistence — a constraint is not "preserving an open question" merely because it is convenient; see the appended review. |

## 32. Cardinality

| Relation | Cardinality | Classification |
|---|---|---|
| Cases per Decision | Exactly one | Adopted (INV-002) |
| Committed-to-matter realizations per Decision | At least one of {internal content, reference}; both simultaneously present is representable but not currently domain-admitted (corrected; see the appended review) | Adopted (OE-002 §5.5, by the grammar comparison in Section 12) |
| Referenced Judgments (or any single reference target) per Decision | Zero or one | Adopted, conditional on form chosen |
| Candidates per Decision | Not applicable — categorically excluded | Logically derived (INV-005) |
| Agents per Decision | Zero (no field) | Adopted by exclusion (Section 18) |
| Reasoning Traces per Decision | Zero or one, only if chosen as the referential matter; never required | Adopted, permissive |
| Superseded Decisions per Decision | Zero, in the minimal design (no stored relation) | Proposed/deferred |
| Actions/executions per Decision | Zero, by design — not modeled at all | Adopted by exclusion (Section 17) |
| Alternatives considered per Decision | Not recorded; not applicable | Adopted by exclusion (Section 16) |

## 33. Reference Semantics

Reused directly from the established Knowledge Reference/Reasoning Trace/Judgment pattern: **typed** (`matter_target_type`/`matter_target_id`); **no type restriction beyond OE-002's own three illustrative examples** (Judgment, Reasoning Trace, Outcome are named, but "no specific Domain Object type is required" extends this to all six — this design does not narrow the reference to only the three named examples, since the text itself does not); **same-Case required** (INV-004); **prior-acceptance required** (INV-005); **duplicate references** — not applicable, since there is at most one committed-to-matter reference per Decision; **role** — a single, fixed role ("committed-to matter"); **order** — not applicable, singular; **self-reference** — structurally impossible; **cycles** — structurally impossible (identical DAG argument, established repeatedly in this series); **deletion behavior** — not applicable, permanence forbids it.

## 34. Persistence Design

One table, `decisions_v2` (or an eventual migration of the existing `decisions` table, per Section 38): `id` (PK, `String`), `case_id` (indexed `String`), `commitment_content` (nullable `String`), `matter_target_type` (nullable, indexed `String`, CHECK-constrained to the six adopted type names when present), `matter_target_id` (nullable, indexed `String`), `recorded_at` (`String`).

**Corrected constraint (Committed-To Matter Completeness Review)**: a single CHECK constraint enforcing only **minimum presence** — `commitment_content IS NOT NULL OR (matter_target_type IS NOT NULL AND matter_target_id IS NOT NULL)` — ruling out only the genuinely forbidden empty case (neither form present). **No constraint forbids both being non-null simultaneously.** This is a deliberate choice, not an oversight: a hard XOR CHECK constraint (as originally proposed, and as would be conventional for a tagged union) would make the combined form *structurally impossible* to store, which is not preserving OE-002's open question but silently deciding it in the negative. Leaving the schema permissive means that if a future OE amendment resolves the question in either direction, no schema migration is required — only the domain-layer validation rule (Section 35) would need to change. The domain constructor and acceptance path, not the database schema, are where the "not currently admitted" boundary is enforced (Test 3 of the appended review). No foreign key across the polymorphic reference, for the same reasons established throughout this series. No deletion, no update method, append-only. camelCase API serialization follows the established shared convention.

## 35. API Consequences

**Create/capture**: required — accepts (or resolves) a `case_id` and at least one realization of the committed-to matter. **Corrected validation rule**: (1) reject as `Incomplete` if neither realization is present at all; (2) reject as `Invalid`, carrying a distinctly-labeled, non-numbered "combined form not currently admitted" finding, if *both* realizations are present — this is a genuine validation-time rejection, not a silent acceptance and not an ordinary INV-nnn violation, per Test 2 of the appended review; (3) if exactly one realization is present, validate it via the same generic algorithm already established for Knowledge Reference, Reasoning Trace, and Judgment (INV-004/INV-005 when the referential form is used). **Read**: required — get by `case_id` + `id`. **Update, supersede-as-mutation, revoke, execute**: none is meaningful or adopted — permanence and the explicit non-execution disclaimer forbid all of them as domain operations; a "later Decision" is simply a new capture, not an operation on the earlier one. **Attach Judgment (or any reference) after the fact**: not permitted — the committed-to matter is fixed entirely at capture time, per OE-006 §4's "no candidate element may be replaced" rule; a different reference is a different candidate requiring its own acceptance. **Delete**: forbidden.

## 36. Invariants

**Adopted**: INV-002 (single Case ownership); INV-003/INV-006 (distinct identity); INV-004 (same-Case reference, when the referential form is used); INV-005 (prior acceptance of the referenced matter, when present); INV-007 (exactly one `DecisionAccepted` event, structurally trivial); INV-008 (atomic acceptance); INV-009/010/011 (permanence, non-erasure — including the explicit non-invalidation-by-supersession rule); INV-012 (conditional root eligibility, depending on chosen form).

**Logically derived**: a Decision lacking any committed-to matter (neither form present) is incomplete/Invalid, by direct analogy to Knowledge Reference's own zero-target resolution under OE-005 §15 and to Judgment's own analogous completeness rule; self-reference and cycles are structurally impossible; no separate Domain Event artifact is required (OE-003 §3, INV-007). **Corrected**: the two forms are *not* logically derived to be mutually exclusive — only their *minimum presence* (at least one) is forced; their potential simultaneous coexistence remains a genuinely open, unresolved question (per OE-002 §5.5's own explicit text), and is treated as **currently unadmitted, not invariantly forbidden** — a distinction with real consequences (Section 34, Section 35, the appended review).

**Proposed implementation constraints**: a minimum-presence CHECK constraint across the content/reference field groups (not an XOR); a domain-layer validation rule rejecting the combined form as Invalid-with-a-distinct-finding, separate from and not itself one of the fifteen numbered invariants; no foreign key across the polymorphic reference; no `update`/`delete` repository method; no "supersede" or "execute" operation.

**Unresolved candidates**: whether both committed-to-matter forms may ever coexist within one Decision instance, and be admitted as such — explicitly, permanently open per OE-002 §5.5 itself, not resolved here, and not blocking, precisely because the corrected design (Storage-Permissive, Admission-Restricted) requires no schema change to accommodate whichever way it is eventually resolved.

## 37. Edge-Case Analysis

**Two Decisions with identical internal content** — permitted; distinct accepted objects with identical semantic content (Section 19). **Two Decisions referencing the same Judgment** — permitted; no uniqueness constraint. **A Decision with internal content and no reference** — the ordinary internal-content-form case; fully valid, root-eligible. **A Decision with a reference and no internal content** — the ordinary referential-form case; fully valid, not root-eligible. **A Decision with both forms** — representable at the storage layer (Section 34), but **not currently admitted** by domain validation (Section 29, Section 35): rejected as Invalid with a distinctly-labeled "combined form not currently admitted" finding, not silently accepted and not treated as an ordinary numbered-invariant violation — the explicitly open OE-002 question (Section 9) is preserved, not decided, by this treatment. **A Decision with neither form** — incomplete/Invalid (Section 29, Section 36); not a valid accepted Decision; this remains fully, unambiguously forced regardless of the combined-form question. **A Decision referencing a false Judgment** — remains fully valid (Section 15). **A Decision never executed** — remains fully valid, permanently (Section 17). **A Decision whose execution fails** — remains fully valid; execution is not modeled at all. **A Decision later reversed** — the original remains permanently valid; the reversal is a separate, new Decision (Section 23). **Contradictory Decisions in the same Case** — permitted, by the same reasoning as contradictory Judgments (no consistency requirement is adopted). **Repeated commitment to the same matter** — creates a new, distinct Decision each time. **An anonymous or imported Decision** — fully representable, since no actor field exists to be unknown. **Cross-Case Judgment reference** — forbidden (INV-004); yields an Invalid candidate if attempted. **A Decision referencing another Decision** — permitted; an ordinary instance of the generic, unrestricted reference rule. **Self-reference** — structurally impossible. **Cycles** — structurally impossible. **Deletion of the referenced Judgment** — impossible under permanence; nothing is ever deleted. **Serialization changes without semantic changes** — fully compatible; identity and content are independent of presentation. **Duplicated semantic Decisions under different IDs** — permitted, per Section 19.

**Test-by-test resolution**: **Test 1** — removing all committed-to-matter content leaves no complete Decision; the minimum content requirement is exactly one of {internal content, reference}, forced by OE-002's own Definition (a Decision must be "regarding what is to be done," which requires *some* identifiable matter). **Test 2** — a Judgment-reference-only Decision expresses exactly: "the Case has settled a practical commitment regarding [the referenced Judgment], without asserting that Judgment's truth, without requiring execution." **Test 3** — internal-content-only is canonically complete, per Section 12. **Test 4** — both forms together: coexistence remains an open question; **corrected** — this design implements neither the permission nor a structural prohibition; it enforces only the independently-forced minimum-presence rule (at least one), while treating the combined case as currently unadmitted at the domain-validation layer (Invalid, distinctly labeled) without foreclosing it at the storage layer, per the appended review's own resolution. **Test 5** — a false-Judgment-referencing Decision remains fully ontologically valid (Section 15). **Test 6** — a never-executed Decision violates no invariant (Section 17). **Test 7** — failed execution neither changes the Decision nor requires a new Domain Object; Decision and execution are wholly independent (Section 17). **Test 8** — reversal leaves the earlier Decision permanently valid as a historical commitment (Section 23). **Test 9** — two Decisions committing to identical content may both exist, distinguished only by identity (Section 19). **Test 10** — without the type label, the machine-verifiable distinction is the *combination* of a minimum-presence-constrained (not XOR-constrained) committed-to-matter slot, with no separate, additional forced content field and no domain-layer admission of the combined case — a shape distinct from Judgment (mandatory content, independently optional reference), Knowledge Reference (mandatory single reference, no content), and a generic empty Case-owned record (no forced content at all). **Test 11** — replacing AI with human reasoning changes nothing about any proposed field; none of them references execution, models, or authorship, so all survive unchanged, confirming none was smuggled in from the execution layer. **Test 12** — an accepted Decision referencing a Judgment later shown false, with no action ever occurring, still means exactly: the Case settled a practical commitment regarding that Judgment, at the time of acceptance, permanently — nothing more and nothing less.

## 38. Existing-Code Impact

Decision already has a substantial existing implementation, previously inspected in depth across the first four investigations of this series. This document does not re-inspect it line-by-line; it reports the already-established, relevant conclusions precisely:

- `atlas/core/domain/decision/entity.py` implements `Decision` with fields `id`, `user_id`, `decision_type`, `subject`, `investment_case`, `confidence`, `decided_at`, `recorded_at`, `source`.
- **`user_id`**: per the Investor Identity and Accepted-State Permanence Resolution, this field has **no future semantic role**, is to be retained temporarily as compatibility-only metadata, and must not participate in Decision's accepted content, completeness, or validity going forward — fully consistent with, and reinforced by, this investigation's own independent finding that Decision "does not require an Agent" (Section 18).
- **`subject` and `investment_case`**: plausibly correspond to this design's minimal `commitment_content` in its internal-content-form realization (a subject plus reasoning text together constituting the committed-to matter) — this correspondence is noted as *plausible* but not independently re-derived or finalized here.
- **`decision_type` and `confidence`**: their status as permissible internal-content structure versus extra, unresolved semantics was explicitly flagged, and explicitly left open, by the Decision/Outcome Reference Semantics Investigation ("whether `decision_type`/`confidence`/`source` are permissible internal content or extra semantics requiring their own justification"). This document does not resolve that question; it is reported here, precisely, as still open.
- **`source`**: same still-open status as `decision_type`/`confidence`.
- **`decided_at`**: well-corroborated as an investor-supplied timestamp distinct from `recorded_at` (Section 24); consistent with, not disturbed by, this design.
- **No Case field exists yet** on the existing `decisions` table — its introduction is the responsibility of the Case Representation Strategy's own migration track, not this document.
- Existing tests, API schemas, and CLI flows are not modified here, per this task's own restrictions; none is touched.

**No new file was created for implementation, and none was modified** — this document is itself the only artifact produced.

## 39. Unresolved Questions

**Q1 — May both committed-to-matter forms coexist within a single Decision instance?** Explicitly and permanently open per OE-002 §5.5 itself; not resolved here, and not resolvable without a genuine forcing function under Doctrine §8. **Corrected smallest safe placeholder**: enforce only minimum presence (at least one) at the schema level, with no CHECK constraint forbidding both; enforce non-admission of the combined case at the domain-validation layer (Invalid, distinctly labeled, not a numbered-invariant violation) (Section 30, Section 34, Section 35). This genuinely preserves the open question — a future resolution in either direction requires only a validation-layer change, never a schema migration — whereas the originally-proposed hard XOR would have required a destructive schema change to ever permit the combined form, and would have silently asserted a negative answer in the meantime.

**Q2 — Are `decision_type`, `confidence`, and `source` permissible internal-content structure, or unadopted extra semantics?** Already flagged as open by the Decision/Outcome Reference Semantics Investigation; not re-resolved here. Competing interpretations: (a) they are legitimate, product-specific internal content within the committed-to-matter slot, no different in kind from any other free-text elaboration; (b) they assert additional, independently-structured semantic content beyond what OE-002's own minimal contract requires, and would need their own justification or removal. No canonical text in OE-002 §5.5 resolves this either way. Implementation consequence of deciding prematurely: could either strip meaningful, already-functioning product content, or entrench unexamined scope creep. Smallest safe placeholder: retain as-is, unresolved, exactly as the third investigation left it. Forcing function: a dedicated, future, bounded investigation into these three fields specifically — not attempted here, consistent with this document's own scope restriction.

**Q3 — Should a `supersedes` reference be added?** Deferred (Section 31); no canonical basis exists today, and none is invented.

None of these questions blocks the minimal design in Section 30 from faithfully preserving OE-002 §5.5's adopted meaning.

## 40. Reopening Conditions

Governed entirely by Architecture Doctrine §8, applied identically to every prior investigation in this series: a genuine forcing function requires a newly identified domain fact inexpressible by the current architecture, an unavoidable contradiction, a downstream normative task exposing a real, demonstrated expressive gap, or evidence the original OE-002 investigation omitted a materially distinct candidate or misapplied the Doctrine's method. Convenience, symmetry with Judgment's own richer structure, or a desire to resolve the both-forms-coexisting question preemptively do not qualify.

## 41. Final Implementation Recommendation

Adopt the four-slot minimal design of Section 30: `id`, `case_id`, a minimum-presence-constrained committed-to-matter realization (`commitment_content` free text, and/or `matter_target_type`/`matter_target_id` typed reference), and `recorded_at`. **Corrected**: persist as one table with a single CHECK constraint enforcing only that at least one realization is present — *not* an XOR — so that the schema can, without future migration, represent a combined-form row whenever the ontology question is eventually resolved. Enforce, at the domain-validation layer only, that ordinary capture and acceptance admit exclusively the content-only and reference-only cases today, rejecting the combined case as Invalid with a distinctly-labeled, non-numbered finding — never silently accepting it, and never treating its rejection as an ordinary invariant violation. Reuse the generic reference-validation algorithm already established for Knowledge Reference, Reasoning Trace, and Judgment where the referential form is used. Introduce no Agent, Candidate, execution, status, finality, or supersession field — each was tested and rejected on precise, stated canonical grounds. This design genuinely preserves, rather than silently resolves, the both-forms-coexisting question OE-002 itself leaves open — see the appended Committed-To Matter Completeness Review for the full analysis and correction. Do not resolve the already-flagged `decision_type`/`confidence`/`source` question here; it remains a separate, bounded, future task. Reconcile the existing `atlas/core/domain/decision/` implementation with this minimal design only as part of that same future migration effort, not as part of this document.

---

## Committed-To Matter Completeness Review

*Appended after initial completion, as a focused corrective review. This section re-examines the committed-to-matter constraint above rather than assuming the original design was correct merely because it had already been written. Sections 1, 12, 29, 30, 31, 34, 35, 36, 37, 39, and 41 above were edited in place to reflect the correction reached here; all other sections are unchanged, since nothing else in the original design depended on the error identified below.*

### Review Question

If OE-002 leaves coexistence of internal commitment content and a typed committed-to-matter reference unresolved, what schema and validation contract may Atlas implement without deciding that unresolved ontology question?

### The Exact Canonical Wording

OE-002 §5.5, Ownership boundary, quoted again because this review turns on its precise reading:

> Decision's committed-to matter MAY be content held internally by the Decision itself, or a reference to another Domain Object belonging to the same Case. Both forms are independently valid. This document does not establish that both forms may coexist within one undifferentiated Decision; this is an open question under Section 7 of the Architecture Doctrine.

Three distinct claims are packed into this passage, and the original design conflated the first two with the third:

1. "MAY be... or..." — an ordinary grammatical alternative, establishing that *either* form is a legitimate way to realize the committed-to matter.
2. "Both forms are independently valid" — a minimum-sufficiency claim: each form, alone, is enough to constitute a complete Decision. This does **not** say "and no other combination is valid" — it only affirms that neither form needs the other to be sufficient.
3. "This document does not establish that both forms may coexist... this is an open question" — an explicit, direct statement that the *combination* question is **undecided**, not that it is decided in the negative. OE-002 does not say "both forms MUST NOT coexist"; it says it does not settle whether they may.

The original design's error was treating (1) and (2) as if they logically forced exclusivity ("either... or..." read as XOR), when in fact only a minimum-presence claim is directly supported, and (3) explicitly forecloses treating exclusivity as settled.

### 1. Alternative Meaning Versus Exclusive Representation

Ordinary grammatical "or," standing alone, does not establish exclusive-OR — it is compatible with inclusive-OR, with an examples-list reading, or with genuine underdetermination, depending on context. Here, OE-002's own immediately-following sentence resolves the ambiguity explicitly, in the direction of **underdetermination**, not exclusivity: the authors evidently recognized the "or" alone did not settle the coexistence question, which is precisely why they added a dedicated sentence flagging it as open. Converting this into an XOR — as the original design did — is not licensed by the grammar and directly contradicts the explicit flagging sentence. The correct reading combines minimum-sufficiency ("either form alone suffices") with genuine, stated underdetermination ("whether together is also valid remains unsettled").

### 2. Ontology Versus Schema Capacity

Four layers were tested for independent permissiveness, per the review's own required distinction:

- **Database representation**: may, and should, be capable of storing both fields populated — restricting this would presuppose an answer to the open question in the negative.
- **Domain constructor / candidate construction**: may accept a candidate presenting both fields as *structurally well-formed input* (parseable, not malformed) — construction failure is reserved for malformed primitives, not for this semantic question.
- **Acceptance boundary (domain validation)**: today, does **not** admit a candidate presenting both fields as a *valid* Decision — this is where the "not yet admitted" line is actually drawn, and it is drawn here specifically because no interpretation of the combined case has been adopted (Section 4 below), not because the database or constructor forbid it.
- **Public API**: mirrors the acceptance boundary — a request presenting both would be rejected at the same validation stage, with a response indicating the combined form is not currently supported, not a generic malformed-request error.

These four layers need not, and here do not, share identical permissiveness — this is the central technical mechanism by which the open question is preserved without inventing a decision.

### 3. Minimum Valid Decision

| Form present | Classification |
|---|---|
| Internal content only | Explicitly valid (OE-002: "both forms are independently valid") |
| Typed reference only | Explicitly valid (same) |
| Both | Unresolved at the ontology level; **representable but not currently admissible** at the implementation level (this review's own precise classification, distinct from "explicitly invalid") |
| Neither | Explicitly invalid — logically forced by OE-002's own Definition, which requires committed-to matter to be identifiable at all; this is independent of, and unaffected by, the combined-form question |

### 4. Combined Form Semantics

Every offered interpretation was tested honestly: both independently constitute committed-to matter; internal content describes the referenced matter; internal content qualifies or narrows it; internal content duplicates it; internal content is documentary only; the two must be semantically equivalent. **None is adopted by any canonical text.** OE-002 states no rule for resolving conflict, priority, or redundancy between the two forms when both are present. This absence of any adopted interpretation is itself the reason the combined form must not be silently admitted with an invented meaning (which would violate the Decision Standard's prohibition on adding unsupported semantics) and must not be silently forbidden either (which would violate the same standard from the opposite direction, by asserting a negative answer OE-002 does not give).

### 5. Persistence Constraint — Candidate Evaluation

- **Candidate A — Strict XOR**: rejected. Directly forbids the combined form at the schema level, prematurely deciding the open question in the negative, and would require a destructive migration if a future resolution permitted combination (Test 1).
- **Candidate B — Inclusive OR (both permitted with assigned meaning)**: rejected. Would require inventing a specific combined-form interpretation with no canonical basis (Section 4), violating the Decision Standard from the opposite direction.
- **Candidate C — Storage-Permissive, Domain-Restrictive**: **adopted.** The schema stores either or both forms without a forbidding constraint; domain validation and acceptance admit only the two independently-established forms today; the combined form is reserved, representable, and currently unadmitted. This is the only candidate that adds no unsupported semantics in either direction (Test 7) while remaining forward-compatible (Test 1) and honest about present validation behavior (Test 2).
- **Candidate D — Separate Representation Variants (an explicit discriminator)**: tested and found unnecessary — introducing a formal "internal-content Decision / referenced-matter Decision / combined-reserved Decision" discriminator would itself assert a taxonomy of Decision *sub-kinds* that OE-002 never establishes; the same distinction is already fully and more simply captured by which of the two nullable field-groups is populated, with no additional ontology invented.
- **Candidate E — Structurally Deferred**: rejected as too strong — the ambiguity does not block a faithful schema or API design; it only requires that schema permissiveness and domain admission be kept distinct, which Candidate C already achieves without deferral.

### 6. API Contract

The create/capture API should, today: accept content-only; accept reference-only; **reject both together**, returning a validation response distinctly indicating the combined form is not currently supported (not a generic malformed-input error, and not silently accepted "without assigning additional semantics" — accepting it silently would itself assign it the tacit, unadopted meaning of "harmless," which is exactly the invention this review forbids). Generic storage acceptance (the schema's own capacity) is explicitly not treated as domain acceptance (the API's own gate) — this is the direct application of Section 2's layered-permissiveness finding.

### 7. Existing Implementation

The existing `atlas/core/domain/decision/entity.py` implementation was inspected (already reported in Section 38 above) and confirmed to have **no committed-to-matter reference field at all today** — `subject`/`investment_case` are its only content-bearing fields, with no `matter_target_type`/`matter_target_id` equivalent yet implemented. It therefore currently assumes, by omission, only the internal-content form — neither an XOR, an inclusive-OR, nor a combined form is currently encoded, because the referential form does not yet exist in code. The corrected design is **additive compatibility**, not a migration requirement: introducing the nullable reference-field pair and the minimum-presence CHECK constraint can be done without touching any existing row, and the domain-validation rule described above can be implemented without altering the existing table's current columns. No production code was modified in the course of this review.

### Required Contradiction Tests

**Test 1 (Future canonical approval of the combined form)** — Under the corrected design, no destructive migration is required: the schema already permits both fields populated; only the application-layer validation rule need be relaxed. Under the original hard-XOR design, a genuine schema migration (dropping or altering the CHECK constraint) would have been required — this is the single most decisive point in favor of the correction.

**Test 2 (Current admission of the combined form)** — No: Atlas cannot today state a complete, determinate semantic proposition for a Decision presenting both forms (Section 4), and therefore it must not be accepted as a valid Decision today. It is rejected, not silently passed through.

**Test 3 (Database row versus accepted Domain Object)** — Yes, in principle, a row could be structurally stored (e.g., during a future migration or bulk import) without that row constituting an *accepted* Decision under the ordinary domain-validation path — this mirrors the general Candidate/accepted-object distinction already established in the Complete Validation and Acceptance Redesign. The corrected design's schema permissiveness exists precisely to support this distinction; it is not, however, currently exercised by the ordinary capture/acceptance flow, which continues to gate on the validation rule described above.

**Test 4 (Remove XOR — do empty Decisions become possible?)** — Yes, if the XOR were simply deleted with nothing put in its place. This is why the corrected design retains a **separate, independently-justified minimum-presence constraint** (at least one realization required) — this constraint is not part of the open question at all; it is fully forced by OE-002's own Definition and is retained without qualification.

**Test 5 (Combined form with conflict)** — No adopted rule defines which of the two, if both were present and disagreed, would control. This absence of a tie-breaking rule is itself part of why the combined form cannot yet be honestly constructed or accepted — there is nothing for an implementation to fall back on.

**Test 6 (Combined form with redundancy)** — Even where the two forms happen to agree or one merely repeats the other, no adopted rule assigns this redundancy any defined semantic or documentary status; the absence of an adopted interpretation applies uniformly regardless of whether the two inputs happen to cohere, so redundancy does not create a special permitted case.

**Test 7 (Canonical silence — which response adds the least unsupported semantics?)** — Reserving representational capacity while rejecting domain admission adds the least unsupported semantics. Forbidding the combined form outright asserts an unstated negative answer; permitting it with an invented meaning asserts both an unstated positive answer and a specific, unadopted interpretation. Reserving-while-rejecting asserts neither — it only declines to construct an interpretation for an input whose meaning is genuinely undefined, which is the position with the smallest semantic footprint of the three.

### Selected Outcome

**Outcome 3 — Storage-Permissive, Admission-Restricted.** The persistence schema preserves capacity for both forms (no forbidding CHECK constraint beyond minimum presence); current domain creation and acceptance permit only content-only and reference-only Decisions; the combined form remains unresolved, structurally representable, and currently unadmitted, rejected at validation time with a distinctly-labeled, non-numbered finding rather than silently accepted or invariantly forbidden.

### Final Determination on This Review

The original design's central error was treating a hard XOR as a way of "choosing not to decide" the coexistence question, when a hard XOR *is* a decision — specifically, a negative one, enforced irreversibly at the schema level. The corrected design separates two genuinely different constraints that the original conflated into one: an independently-forced **minimum-presence** rule (at least one form; never both absent) and a genuinely **open admission question** (whether both together is ever valid), the latter now handled by restricting domain-layer admission rather than schema-layer representation. Decision remains fully implementation-ready under this correction — nothing about the fix required narrowing or deferring any other part of the design (Sections 1–11, 13–28 remain entirely unaffected and are not revised).
