# Atlas Architecture Conformance Register

**Sprint 7 — Architecture Conformance Review.** Consolidates the eight per-ADR Conformance Reports produced this sprint into a single implementation baseline. This is an audit artifact: every claim below traces to a specific per-ADR report, which itself traces to specific entities, services, repositories, APIs, tests, or migrations — not to the ADRs' own text taken on faith.

---

## 1. Overall Implementation Status

| ADR | Conformance | One-line reason |
|---|---|---|
| `ADR-GOV-001` | Partially Implemented | Track separation holds structurally, but the ADR's own account of cross-track interaction is out of date (Finding 2 below). |
| `ADR-GOV-002` | Partially Implemented | Process well-defined and unviolated; a large body of pre-existing reconciliation work sits entirely outside it. |
| `ADR-GOV-003` | Partially Implemented | Substantive rules (no self-conversion, traceability, no deletion) hold; the status bookkeeping and index the ADR itself anticipates were never done. |
| `ADR-DC-001` | Partially Implemented | Domain object and full REST API are built, tested, and correct; not yet consumed by Alpha; a real, previously undocumented naming collision exists. |
| `ADR-DD-001` | Not Implemented | No `DecisionDraft` object exists; the one required precedent (Security Confirmation event pattern) is ready and unchanged. |
| `ADR-CR-001` | Fully Implemented | The ADR required nothing new be built, and nothing new was built; `Decision`'s immutability invariant verified directly against the entity. |
| `ADR-CC-001` | Not Implemented | No `CaseCondition` object exists; `atlas/monitoring` is confirmed correctly untouched. |
| `ADR-AS-001` | Not Implemented | No `Assumption` object exists; the `OutlookAssumption` naming collision persists exactly as disclosed. |

**Read across the whole register:** one ADR is fully realized (`ADR-CR-001`, because it asked for nothing), one is substantially realized with real gaps (`ADR-DC-001`), three describe governance practice that is broadly honored but under-documented (`ADR-GOV-001/002/003`), and three are pure architecture-ahead-of-implementation (`ADR-DD-001`, `ADR-CC-001`, `ADR-AS-001`) with no drift or violation — only absence.

---

## 2. Implementation Gaps

Gaps are absences of required work, distinct from conflicts (Section 3).

| # | Gap | Severity | ADR(s) | Ownership |
|---|---|---|---|---|
| G1 | No `DecisionDraft` object, event stream, service, API, or UI | High | `ADR-DD-001` | Backend, API, UI |
| G2 | No `CaseCondition`/`CaseConditionEvent` object, service, API, or UI | High | `ADR-CC-001` | Backend, API, UI |
| G3 | No `Assumption` object, event stream, service, API, or UI | High | `ADR-AS-001` | Backend, API, UI |
| G4 | Alpha does not consume the already-built DecisionContext API | Medium | `ADR-DC-001` | API, UI |
| G5 | Investigations 001–011 never received the Complete/Converted status bookkeeping `ADR-GOV-003` §2 anticipates | Medium | `ADR-GOV-003` | Product |
| G6 | No central index of ADR/Investigation status exists | Medium | `ADR-GOV-003` | Product |
| G7 | `ADR-002` C-02 authorship-transfer model implemented for no object in the epistemic family (moot until G3 closes, but the four existing objects — `Hypothesis`/`Evidence`/`Conclusion`/`Judgment` — also lack it, a disclosed, unresolved gap in their own right) | Low | `ADR-AS-001` | Backend |
| G8 | No CI/lint mechanism enforces cross-track independence (`ADR-GOV-001`) | Low | `ADR-GOV-001` | Architecture |

## 3. Conflicts

Conflicts are places where current reality contradicts or is inconsistent with what an ADR states, as opposed to simply not yet existing.

| # | Conflict | Severity | ADR(s) | Ownership |
|---|---|---|---|---|
| C1 | A second, unrelated `DecisionContext` class (`atlas/decision/decision_context.py`, used by `atlas/decision/decision_engine.py`) predates and collides in name with the ADR's own `DecisionContext` — never disclosed by any prior Investigation | High | `ADR-DC-001` | Backend, Architecture |
| C2 | `ADR-GOV-001`'s Context understates how much cross-track (Domain Object Architecture ↔ implementation) reconciliation is already underway, evidenced by `Domain-Object-Implementation-Reconciliation-Plan.md` and five completed per-object Implementation Design documents | High | `ADR-GOV-001` | Architecture |
| C3 | That same reconciliation work was never expressed in, or routed through, `ADR-GOV-002`'s own forcing-function/reconciliation-record process — it predates GOV-002 and uses its own vocabulary | High | `ADR-GOV-002` | Architecture |
| C4 | `OutlookAssumption` (`atlas/analysis_engine/outlook.py`) remains unrenamed — a disclosed, not silent, conflict; becomes materially worse the moment `Assumption` (G3) is implemented | Medium (latent) | `ADR-AS-001` | Backend |

Both C2 and C3 describe the same underlying fact from each governance ADR's own vantage point — recorded once each because each ADR's own Conformance Report needs it independently, not because it is two separate problems.

## 4. Implementation Priorities

Ordered by a combination of severity, how many downstream ADRs depend on the gap, and how cheap the fix is relative to its value.

1. **C1 — Rename the legacy `atlas/decision/decision_context.py` `DecisionContext` class.** Small, cheap, high-value fix; removes a live, currently-exploitable-by-accident naming collision in production code. No dependency on anything else in this register.
2. **C2/C3 — Reconcile `ADR-GOV-001`/`ADR-GOV-002` with the actual state of Domain-Object-Architecture-↔-implementation reconciliation.** Documentation-only, but blocks confident reasoning about the governance ADRs' own accuracy until resolved.
3. **G5/G6 — Investigation status bookkeeping and a central ADR index.** Cheap, Product-owned, meaningfully improves navigability of an already-large document set.
4. **G1 — Implement `DecisionDraft`.** The highest-leverage single implementation project: it is a named dependency (soft or hard) for both `ADR-CC-001` and `ADR-CR-001`'s own Reconsideration story, and closes a real, named UX-009 product gap (Save-as-Draft).
5. **G2 — Implement `CaseCondition`.** Second-highest leverage: unblocks Monitoring/Invalidation Conditions and Review Plan (UX-008/UX-009), and is `ADR-AS-001`'s own soft dependency.
6. **G3 — Implement `Assumption`.** Third: benefits from G2 existing first (a literal, already-built sibling to copy) but does not strictly require it.
7. **G4 — Wire the existing DecisionContext API into Alpha's UI.** Independent of 4–6; can proceed in parallel at any time, since the backend is complete.
8. **C4 — Rename or disambiguate `OutlookAssumption`.** Deferred until immediately before or during G3's own implementation — no value in doing it earlier, real cost in doing it later.
9. **G7/G8 — Low-urgency disclosed gaps.** No action recommended until their triggering conditions arrive (G7: `Assumption` implementation; G8: only if track-boundary violations start actually occurring).

## 5. Dependency Graph

```
ADR-DC-001 (domain+API: DONE)
     │
     ├──(commit boundary; already satisfied)──▶ ADR-DD-001 (DecisionDraft: NOT BUILT)
     │                                                │
     │                                                │ (soft — §7 "may originate", not required)
     │                                                ▼
     └──(no dependency)                        ADR-CC-001 (CaseCondition: NOT BUILT)
                                                        │
                                                        │ (soft — event-stream pattern reuse; template
                                                        │  itself is independently available)
                                                        ▼
                                                 ADR-AS-001 (Assumption: NOT BUILT)

ADR-CR-001 (Review/Supersession: DONE — required nothing new)
     └── cross-references ADR-CC-001 for Amendment (explicitly deferred, not blocking)

ADR-GOV-001 ──governs──▶ ADR-GOV-002 ──governs──▶ ADR-GOV-003
     │                         │
     └── C2/C3: both reference a pre-existing, out-of-process
         reconciliation effort in docs/atlas_domain_object_architecture/
```

No hard (build-blocking) dependency was found anywhere in this graph. Every "depends on" relationship among `ADR-DD-001`/`ADR-CC-001`/`ADR-AS-001` is soft: each names the prior ADR's own shape as the pattern to reuse, but the underlying template (`SecurityConfirmationEvent`) is already independently available to all three, so none is literally blocked from starting before its named predecessor is built — sequencing them in the order above is a leverage choice (Section 4), not a hard requirement.

## 6. Recommended Implementation Waves

**Wave A — Hygiene (no code, low risk, do first):** C1 (rename legacy `DecisionContext`), G5 (Investigation status bookkeeping), G6 (ADR index), C2/C3 (governance ADR clarifications).

**Wave B — Decision Draft:** G1, full stack. Closes the Save-as-Draft product gap and removes the soft dependency both `ADR-CC-001` and `ADR-CR-001`'s own Reconsideration story name.

**Wave C — CaseCondition:** G2, full stack, plus C4 addressed concurrently if `Assumption` (Wave D) is scheduled soon after — otherwise C4 can wait. Closes Monitoring/Invalidation Conditions and the Review Plan.

**Wave D — Assumption:** G3, full stack, with C4 (rename `OutlookAssumption` or the new object's own disambiguating name) as a hard prerequisite of this wave specifically, not before it. G7 (C-02 authorship extension) is addressed for `Assumption` itself as part of this wave; extending it to `Hypothesis`/`Evidence`/`Conclusion`/`Judgment` remains explicitly out of scope, per `ADR-AS-001`'s own disclosed gap.

**Wave E — Alpha integration:** G4 (wire DecisionContext into the UI), plus equivalent UI wiring for whatever of Waves B–D has landed by the time this wave is scheduled. Independent of Waves B–D's own internal ordering; can be pulled forward for any single ADR whose backend is already complete.

---

## 7. Success Criteria — Status

- **A complete architectural implementation baseline:** Established — Section 1's table and the eight per-ADR reports it summarizes.
- **A verified list of implementation gaps:** Established — Section 2, each gap traced to a specific absence in a specific location, not inferred from the ADR text alone.
- **A prioritized implementation roadmap derived from Accepted ADRs:** Established — Sections 4–6.
- **A clear distinction between architecture that exists, architecture that is partially implemented, and architecture that remains to be built:** Established — Section 1's Conformance column, cross-checked against Sections 2–3 for the specific reasons behind every "Partially" or "Not" verdict.

## Related

`docs/ADR-GOV-001-Conformance-Report.md`, `docs/ADR-GOV-002-Conformance-Report.md`, `docs/ADR-GOV-003-Conformance-Report.md`, `docs/ADR-DC-001-Conformance-Report.md`, `docs/ADR-DD-001-Conformance-Report.md`, `docs/ADR-CR-001-Conformance-Report.md`, `docs/ADR-CC-001-Conformance-Report.md`, `docs/ADR-AS-001-Conformance-Report.md` (the eight source reports this register consolidates). `docs/atlas_domain_object_architecture/Domain-Object-Implementation-Reconciliation-Plan.md` (the pre-existing reconciliation effort named in C2/C3). `Atlas-Recommendation-Register.md`, `Atlas-Governance-Adoption-Review.md` (prior-sprint documents this review builds on for traceability).
