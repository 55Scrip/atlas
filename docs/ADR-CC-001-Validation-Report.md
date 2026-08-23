# ADR-CC-001 Validation Report

**Subject:** `docs/ADR-CC-001-CaseCondition.md`
**Method:** Adversarial re-review against the seven-part framework used in Sprints 4/5 (Scope, Normative, Consistency, Minimality, Boundary, Alternative, Implementation Validation), followed by a Final Decision.

---

## 1. Scope Validation

Sprint 6's own brief names eleven topics for `ADR-CC-001`: Purpose, Identity and event model, Predicate semantics, Monitoring vs. Invalidation, Lifecycle, Evaluation model, Relationship to Decision, Relationship to DecisionDraft, Relationship to Daily Brief, Existing ontology reuse, Rejected alternatives.

**Finding (resolved during this review):** the original Decision list carried eleven numbered points, but one of them — former §10, an Authorship rule requiring Atlas-proposed condition text to be labeled "Atlas Suggested / User Accepted" per `ADR-002` C-02 — is not among the eleven specified topics. This is the same category of scope creep found and fixed in `ADR-DC-001`'s own validation (Sprint 5): real, evidenced content, but outside what this specific ADR's own brief asked for. **Fix applied:** former §10 was removed from the numbered Decision list; its content survives unchanged in the Invariants section (where it already duplicated the same rule), so no substantive content is lost. The remaining rejected-alternatives point renumbered from §11 to §10.

No other scope drift found — the remaining ten Decision points map cleanly onto the ten remaining topics (Predicate semantics and Evaluation model are addressed jointly across §3 and §5, a reasonable grouping given the investigations' own findings treat them as related).

## 2. Normative Validation

Traceability checked against `Atlas-Recommendation-Register.md`:

| Decision point | Source |
|---|---|
| §1 (Adopt CaseCondition) | `INV5-R1` (superseded in detail) / `INV6-R1` |
| §2 (event stream, only meaningful transitions) | `INV6-R1`, `INV6-R2`, `INV6-R4` |
| §3 (predicate content shape) | `Investigation-006` Phase 2 — see below |
| §4 (Monitoring/Invalidation same object) | `INV6-R3` |
| §5 (time/state evaluation split) | `INV5-R5` |
| §6 (Decision relationship) | `INV5-R1`/`INV6-R1`, consistent with `ADR-DD-001` §5 |
| §7 (DecisionDraft relationship) | `Investigation-006` Phase 9 |
| §8 (Daily Brief relationship) | `INV6-R7`, `INV5-R3`, `INV5-R4` |
| §9 (atlas/monitoring kept separate) | `INV5-R2` |
| §10 (rejected models) | `INV5-R7`, `INV6-R8` |

**Finding (resolved during this review):** §3's predicate-content-shape finding (free text by default, optional structured sub-field) traces to `Investigation-006` Phase 2, which was never independently extracted as its own numbered `INV6-R` recommendation in Sprint 1's register pass — it was folded into `INV6-R1`'s general "definition" scope without its own ID. This is real, undisputed content from a Complete investigation, not fabrication, but presenting it without disclosure risks it being mistaken for a directly-approved, separately-numbered recommendation. **Fix applied:** a disclosure sentence was added to the Context section, naming the gap explicitly and citing the same disclosure principle `ADR-GOV-003`'s own Context section already established for exactly this situation.

No other traceability gap found; every other Decision point maps to an explicit Register ID.

## 3. Consistency Validation

Checked against `ADR-GOV-001`/`002`/`003` (no conflict) and against all three Wave 1 ADRs (`ADR-DC-001`, `ADR-DD-001`, `ADR-CR-001`). §6's "no field on Decision may mark it monitored/invalidated" is consistent with, and explicitly cross-references, `ADR-CR-001` §2's own derived-supersession principle applied to a different relationship — no contradiction. §7's DecisionDraft-origination claim is consistent with `ADR-DD-001` §3's own commit-boundary description.

## 4. Minimality Validation

With former §10 removed (§1, above), the remaining ten Decision points are each load-bearing and non-duplicative. No example is stated as if it were a rule.

## 5. Boundary Validation

Portfolio-scoped conditions are explicitly named as an unsolved, out-of-scope gap in both Context and Open Questions — a clean, well-disclosed boundary, consistent with how the source investigations themselves treated this gap.

## 6. Alternative Validation

The five rejected models in Decision §10 match `Investigation-005` Phase 18 and `Investigation-006` Phase 16's own tested sets precisely, with correct grounds stated for each.

## 7. Implementation Validation

The ADR requires no new infrastructure to be followed — it reuses an already-shipped persistence pattern (Security Confirmation) for a third time, and explicitly leaves `atlas/monitoring` untouched. No blocking ambiguity found for a future implementer.

---

## Final Decision: **Accept with Changes**

Changes required and applied in this review:
1. Removed former Decision §10 (Authorship) from the numbered Decision list — outside Sprint 6's own eleven-topic brief for this ADR — retaining its content, unchanged, in Invariants. Renumbered the rejected-models point from §11 to §10.
2. Added a disclosure sentence to Context naming §3's source as `Investigation-006` Phase 2, which was never given its own Register recommendation ID.

No other revision required. `ADR-CC-001`'s `Status` is updated to `Accepted` following this review.
