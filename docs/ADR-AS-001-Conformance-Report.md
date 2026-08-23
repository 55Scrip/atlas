# ADR-AS-001 Conformance Report — Assumption

**Sprint 7 — Architecture Conformance Review.** Audits `docs/ADR-AS-001-Assumption.md` (Accepted) against the repository, including the five neighboring epistemic objects (`Hypothesis`, `Evidence`, `Conclusion`, `Judgment`) and the disclosed `OutlookAssumption` naming collision.

**Overall Conformance: Not Implemented**

---

## Finding 1 — No `Assumption` object exists anywhere

- **Conformance:** Not Implemented.
- **Evidence:** A repository-wide, case-sensitive grep for `class Assumption\b` returns zero matches under `atlas/core/domain/`. No directory for it exists alongside `hypothesis`, `evidence`, `conclusion`, `judgment` in `atlas/core/domain/`.
- **Severity:** High. `Assumption` is the second of the two largest new domain concepts adopted this program, and it is the only member of the epistemic family with a genuinely strong, already-anticipated `DE-005` integration point (per the ADR's own Consequences) — currently unrealized.
- **Recommendation:** Larger implementation project.
- **Ownership:** Backend, API, UI.
- **Dependencies:** Soft dependency on `ADR-CC-001` — Decision §10 requires reusing "the identical event-stream pattern established for `CaseCondition`," and `CaseCondition` is itself Not Implemented (see that report). This is not strictly blocking: the underlying template (`SecurityConfirmationEvent`, confirmed present and unchanged) is directly available regardless of whether `CaseCondition` itself has been built, so `Assumption` could be implemented first if prioritized differently, at the cost of not having a literal, already-built sibling to copy.

## Finding 2 — The `OutlookAssumption` naming collision persists exactly as disclosed — not a new finding, but confirmed current

- **Conformance:** Conflicts With Implementation (a disclosed, accepted conflict, not a silent one).
- **Evidence:** `atlas/analysis_engine/outlook.py` still defines `OutlookAssumptionKind` and `OutlookAssumption` (lines 310, 331, and used throughout the file's valuation-model computation), unrenamed, exactly as `Investigation-007` found it. Since `Assumption` itself does not yet exist (Finding 1), the two names cannot yet collide in an actual import statement — but the ADR's own §11 and Open Questions correctly anticipate this as a live risk for whoever implements Finding 1.
- **Severity:** Medium (currently latent; becomes High the moment `Assumption` is implemented without also addressing this).
- **Recommendation:** ADR clarification is already sufficient (the ADR already discloses this); no code action needed until Finding 1's own implementation project begins, at which point renaming `OutlookAssumption` or choosing a visibly distinct name for the new object becomes a hard prerequisite, not optional.
- **Ownership:** Backend.
- **Dependencies:** Depends on Finding 1's own implementation timing.

## Finding 3 — The `ADR-002` C-02 authorship-transfer model is not implemented for any object in this family — confirms the disclosed gap is real, not theoretical

- **Conformance:** Not Implemented.
- **Evidence:** A repository-wide grep for `AtlasSuggested`, `UserAccepted`, `Atlas Suggested`, `User Accepted`, `AtlasProposed`, and any `class *Authorship*` finds no such enum, field, or model anywhere in `atlas/`. `Hypothesis`, `Evidence`, `Conclusion`, and `Judgment` each carry only a single-party authorship shape (investor-authored, no Atlas-suggestion/acceptance mechanic), exactly as `Investigation-008` Phase 15 found. Since `Assumption` also does not yet exist, this ADR's own §11's authorship claim (Assumption should follow C-02 "precisely") is currently unimplemented for the same reason as Finding 1, not a separate defect.
- **Severity:** Low (correctly disclosed as a genuinely open question by the ADR itself, not a violation of anything the ADR requires today).
- **Recommendation:** No action now — track alongside Finding 1's own implementation project, since building `Assumption` is the first opportunity to actually implement C-02 for any object in this family.
- **Ownership:** Backend.
- **Dependencies:** Depends on Finding 1.

## Finding 4 — `Hypothesis`, `Evidence`, `Conclusion`, `Judgment` remain unmodified, matching this ADR's own Migration clause

- **Conformance:** Fully Implemented.
- **Evidence:** All four entities remain present and, per this Sprint's own `git status` verification, untouched by this program's own documentation-only work. `Evidence.direction` (`SUPPORTS`/`CHALLENGES`, required) is confirmed present, matching Decision §4/Invariants exactly.
- **Severity:** Informational.
- **Recommendation:** No action.
- **Ownership:** Backend.
- **Dependencies:** None.

---

## Synthesis

`ADR-AS-001`, like `ADR-CC-001` and `ADR-DD-001`, is unimplemented architecture rather than drifted architecture. The one point requiring active attention at implementation time, not before, is the `OutlookAssumption` collision — currently harmless only because the new object does not yet exist to collide with it.
