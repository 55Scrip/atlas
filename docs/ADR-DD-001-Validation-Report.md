# ADR-DD-001 Validation Report

**Subject:** `docs/ADR-DD-001-Decision-Draft.md`
**Method:** Adversarial re-review against the seven-part framework used in Sprint 4 (Scope, Normative, Consistency, Minimality, Boundary, Alternative, Implementation Validation), followed by a Final Decision.

---

## 1. Scope Validation

The ADR's stated Problem — whether any existing object can hold pre-Decision, editable, cross-session content — is single and well-bounded. All six topics Sprint 5's brief specified for `ADR-DD-001` (DecisionDraft ontology, append-only event model, relationship to Decision, lifecycle, provenance, rejected models) are covered, and none of the six Decision points reaches beyond them. No scope drift found.

## 2. Normative Validation

Every Decision point traces cleanly to a Register recommendation: §1→`INV3-R1`, §2→`INV3-R2`, §3→`INV3-R3`, §4→`INV3-R4`, §5→`INV3-R5`, §6→`INV3-R6`. No fabricated claim found.

## 3. Consistency Validation

No conflict against `ADR-GOV-001`/`002`/`003`, `ADR-DC-001`, or `ADR-CR-001`.

**Finding (resolved during this review):** the word "Draft" is used in this program for two unrelated things — a document-status value (`ADR-GOV-002` §6: "Draft — under active work, not yet a stable basis for dependent work") and, informally, the domain object this very ADR adopts (`DecisionDraft`, frequently shortened to "a draft" in the prose). This is the same category of naming collision the Investigation Series itself repeatedly found and flagged elsewhere (`Reflection`, `Evaluation`, `Assumption`/`OutlookAssumption`) — a real risk that a future reader skimming this ADR's own `Status: Draft` header alongside its `DecisionDraft` content could conflate the two senses. **Fix applied:** a "Naming note" was added at the top of the Decision section, stating explicitly that the `Status:` header uses `ADR-GOV-002`'s document-status sense and every other use of "draft" refers to the `DecisionDraft` domain object.

## 4. Minimality Validation

All six Decision points are load-bearing; none duplicates another. §5's `DecisionSource` taxonomy reference (`IMPORT`/`API`/`BROKER_SYNC` never pass through a draft) is a genuine hard constraint, not an illustrative example dressed as a rule.

## 5. Boundary Validation

The Open Questions section is unusually thorough (eight items) and explicitly discloses what remains unresolved — provenance retention, abandon-vs-delete, expiration, cardinality, collaboration, storage-retention-vs-privacy tension, offline/mobile sync, and the conversion-path question. This is a genuine strength: the boundary of what this ADR does and does not settle is unusually well-disclosed compared to a typical ADR in this program.

## 6. Alternative Validation

The five rejected models in Decision §6 match `Investigation-003`'s own tested set, including the correct reasoning for why the event-only model (no derived projection) is dominated rather than merely different.

## 7. Implementation Validation

The ADR requires no new infrastructure design — it explicitly reuses an already-shipped, already-tested pattern (`SecurityConfirmationEvent`/`ConfirmedSecuritySelection`). A future implementer has a concrete precedent to build against, not an abstract description. No blocking ambiguity found.

---

## Final Decision: **Accept with Changes**

Changes required and applied in this review:
1. Added a "Naming note" at the top of the Decision section disambiguating "Draft" (ADR document status, `ADR-GOV-002` §6) from `DecisionDraft` (the domain object this ADR adopts).

No other revision required. `ADR-DD-001`'s `Status` is updated to `Accepted` following this review.
