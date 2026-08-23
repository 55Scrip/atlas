# ADR-CR-001 Validation Report

**Subject:** `docs/ADR-CR-001-Decision-Review-and-Supersession.md`
**Method:** Adversarial re-review against the seven-part framework used in Sprint 4 (Scope, Normative, Consistency, Minimality, Boundary, Alternative, Implementation Validation), followed by a Final Decision.

---

## 1. Scope Validation

The ADR's stated Problem — whether Review, Amendment, and Supersession require new objects given `Decision`'s immutability — is single and well-bounded. All six topics Sprint 5's brief specified (Review, Reconsideration, Supersession, Amendment, Derived state, Existing ontology reuse) are covered by the four Decision points. No scope drift found; Amendment is correctly and explicitly deferred rather than silently addressed.

## 2. Normative Validation

Every Decision point traces to a Register recommendation: §1→`INV4-R1`, §2→`INV4-R2`, §3→`INV4-R3`, §4→`INV4-R4`. No fabricated claim found.

## 3. Consistency Validation

No conflict against `ADR-DC-001` or `ADR-DD-001` (both correctly cited and consistent with this ADR's own treatment).

**Finding (resolved during this review):** "supersession" is used for two substantively different mechanisms across this program. `ADR-GOV-002` §5 defines document-level supersession as **explicit** — it requires an identified replacing decision and an explicit status change on the superseded document. This ADR's own §2 defines Decision-level supersession as the mechanism's near opposite — **implicit and fully derived** from `decided_at`/`recorded_at` ordering, with an explicit stored field or flag forbidden outright ("no field or flag... may ever store that a Decision has been superseded"). This is not a superficial naming coincidence like the `Draft`/`DecisionDraft` case in `ADR-DD-001` — it is two contrary mechanisms sharing one word, which is a materially higher risk of misreading (a reader could wrongly assume Decision supersession requires the same explicit status change `ADR-GOV-002` mandates, which §2 of this ADR specifically forbids). **Fix applied:** a "Naming note" was added at the top of the Decision section, stating the distinction explicitly and confirming the two mechanisms are deliberately different, not inconsistent.

## 4. Minimality Validation

All four Decision points are load-bearing. §4's list of five rejected models is not padding — each is independently plausible and independently tested in `Investigation-004`.

## 5. Boundary Validation

The ADR is explicit about what it does not resolve: Amendment (deferred to Investigations 005/006), the review-trigger's own home (deferred to Investigation 005), and several product-design questions in Open Questions. This is a clean, well-disclosed boundary.

## 6. Alternative Validation

The five rejected models in Decision §4 match `Investigation-004`'s own tested set. The severity ranking given to the mutable-status model ("the single most severe failure considered") is supported directly by the stated reasoning (breaks `Decision`'s core invariant and `ReflectionResponse`'s own downstream safety claim), not asserted without grounds.

## 7. Implementation Validation

This ADR requires zero new implementation — it confirms existing mechanisms (`Decision.register()`, `Evaluation`) already suffice. This is the strongest possible implementation-validation outcome: there is no new mechanism whose followability needs to be checked. No ambiguity found.

---

## Final Decision: **Accept with Changes**

Changes required and applied in this review:
1. Added a "Naming note" at the top of the Decision section disambiguating this ADR's own derived, implicit Decision-supersession (§2) from `ADR-GOV-002` §5's explicit, document-level supersession — the two are contrary in mechanism despite sharing a name.

No other revision required. `ADR-CR-001`'s `Status` is updated to `Accepted` following this review.
