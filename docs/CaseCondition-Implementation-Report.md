# CaseCondition Implementation Report

**Sprint 10 — Production implementation.** Implementation notes only. `docs/ADR-CC-001-CaseCondition.md` remains the authoritative architecture. Unlike Sprint 9 (`ADR-DD-001`), no separate implementation-design document preceded this sprint — Sprint 10's own brief goes directly to production, so the design choices below were made during implementation, directly against the ADR's own text and `DecisionDraft`'s already-shipped conventions (Sprint 9), and are disclosed here rather than in a prior design artifact.

---

## 1. Execution Report

The complete `CaseCondition` aggregate was implemented: domain, persistence, application service, a dedicated evaluation engine, REST API, and router registration, plus a full test suite across all layers and an end-to-end test. Every design choice either (a) is dictated directly by `ADR-CC-001`'s own Decision section, or (b) mirrors an established `DecisionDraft` (Sprint 9) convention, or (c) is a small, disclosed implementation-level resolution of something the ADR's own text leaves open (§6, Implementation Findings) — the same discipline `DecisionDraft-Implementation-Design.md` §3.6 already modeled once for "abandon vs. delete."

No ADR conflict was found. `ADR-CC-001` was implementable in full.

## 2. Files Created

**Domain** (`atlas/core/domain/case_condition/`): `__init__.py`, `value_objects.py` (`CaseConditionId`), `entity.py` (`CaseConditionEvent`, `CaseConditionEventType`, `CaseConditionRole`, `CaseConditionAuthorship`, `CaseConditionView`, `is_terminal`, `reconstruct_current_state`), `evaluation.py` (the evaluation engine: `evaluate_date_condition`, `evaluate_threshold_condition`, `evaluate`), `exceptions.py`, `repository.py` (`CaseConditionEventRepository` Protocol).

**Application** (`atlas/core/application/case_condition/`): `__init__.py`, `case_condition_service.py` (`CaseConditionContent`, `CaseConditionEvaluationResult`, `CaseConditionService` with `create`, `revise`, `evaluate`, `retire`, `supersede`, `read`, `list_events`, `list_for_case`, `list_for_decision`).

**Persistence** (`atlas/core/infrastructure/persistence/case_condition/`): `__init__.py`, `table.py` (`case_condition_events_table`, `create_case_condition_events_table`), `sqlalchemy_repository.py` (`SqlAlchemyCaseConditionEventRepository`).

**API** (`atlas/core/infrastructure/api/case_condition/`): `__init__.py`, `schemas.py`, `router.py` (9 routes — see §4), `errors.py`, `dependencies.py`.

**Tests**: `tests/unit/domain/case_condition/{__init__.py,test_entity.py,test_value_objects.py,test_evaluation.py}`, `tests/unit/application/case_condition/{__init__.py,test_case_condition_service.py,test_end_to_end.py}`, `tests/unit/infrastructure/persistence/case_condition/{__init__.py,test_sqlalchemy_repository.py}`, `tests/unit/infrastructure/api/case_condition/{__init__.py,test_router.py}`.

No Alpha frontend deliverable was produced — Sprint 10's own brief, unlike Sprint 9's, does not list one.

## 3. Files Modified

**`atlas/core/infrastructure/api/app.py`** — the same two-addition pattern as Sprint 9: import lines plus `app.include_router(case_condition_router)` and `register_case_condition_error_handlers(app)`, inserted at the correct alphabetical position among the existing imports. 19 insertions, 0 deletions, one file — the only tracked file this sprint touches.

No other existing file was modified. Confirmed directly: `git diff --stat` against `Decision`, `DecisionContext`, `Case`, `DecisionDraft`, `security_confirmation`, and their persistence/API counterparts returns empty.

## 4. API Routes

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/cases/{case_id}/case-conditions` | Create |
| `GET` | `/cases/{case_id}/case-conditions` | List for a Case (`includeTerminal` query param, default `false`) |
| `GET` | `/decisions/{decision_id}/case-conditions` | List for a Decision |
| `GET` | `/case-conditions/{condition_id}` | Read current state |
| `GET` | `/case-conditions/{condition_id}/events` | Full event history |
| `PATCH` | `/case-conditions/{condition_id}` | Revise |
| `POST` | `/case-conditions/{condition_id}/evaluate` | Mechanical or human-asserted evaluation |
| `POST` | `/case-conditions/{condition_id}/retire` | Retire (idempotent, 204) |
| `POST` | `/case-conditions/{condition_id}/supersede` | Supersede (with optional replacement reference) |

## 5. Tests

| Layer | File(s) | Result |
|---|---|---|
| Domain | `test_entity.py`, `test_value_objects.py`, `test_evaluation.py` | 32 passed |
| Application | `test_case_condition_service.py` | 30 passed |
| End-to-end | `test_end_to_end.py` | 1 passed |
| Persistence | `test_sqlalchemy_repository.py` | 8 passed |
| API | `test_router.py` | 20 passed |
| **New tests, total** | | **91 passed, 0 failed** |
| Regression | `decision`, `decision_context`, `case`, `decision_draft` (all layers), `security_confirmation`, `test_architecture_boundaries.py` | 404 passed, 0 failed |
| **Combined** | | **495 passed, 0 failed** |

The evaluation engine has dedicated, isolated tests (`test_evaluation.py`) proving both mechanisms independently of the service layer — date comparison, all six threshold operators, the dispatcher's routing by `structured_kind`, and both its own error conditions (`MissingObservedValueError`, `ConditionNotMechanicallyEvaluableError`). `test_case_condition_service.py::TestEvaluateRepeatedSatisfaction` is the executable proof that re-evaluating an already-satisfied condition writes no new event — the direct test of this sprint's own "only meaningful transitions" implementation finding (§6). `test_end_to_end.py` exercises the full create → revise → evaluate → supersede flow against real repositories and confirms `Decision`/`Case` are read but never written by any of it.

## 6. Build Results

Backend composition builds successfully: `create_app()` succeeds, and all 9 new routes are present and dispatchable (confirmed via the live OpenAPI schema, not merely `len(app.routes)` — Starlette's `include_router` now wraps sub-routers as `_IncludedRouter` objects that don't flatten into `app.routes` directly at this FastAPI/Starlette version, so an `openapi.json` check was used instead; this is a diagnostic-method note, not a defect). No frontend changes were made this sprint, so no frontend build was run.

## 7. Implementation Findings

Four findings, none changing an aggregate boundary, the event model's own four required types, a repository contract's meaning, or API semantics beyond what those four types require to be usable at all.

1. **Terminal vs. non-terminal event types.** ADR-CC-001 §2 names four event types but does not state which close a condition's own stream. Implemented: `superseded` and `retired` are terminal; `revised` and `evaluated_satisfied` are not — a condition may be revised again after being satisfied (an investor reviewing a triggered condition and choosing to keep watching is a legitimate case the ADR never forecloses). Mirrors `DecisionDraft`'s own identical `abandoned`/`committed`-terminal, `revised`-not split.

2. **"Superseded" carries an optional forward reference.** Modeled directly on `DecisionDraftEvent.committed`'s own `committed_decision_id` back-reference: a `superseded` event may carry `superseded_by_condition_id`. This is the concrete, structural difference from `retired` ("stop watching, no replacement," per `Investigation-006` Phase 10) that the ADR's own four-type list otherwise leaves implicit.

3. **Repeated-`True` evaluation is also a "routine, non-transition" check.** ADR-CC-001 §2 explicitly protects the not-met case ("routine 'still not met, checked again today' re-checks are never stored") but does not explicitly say whether re-checking an *already-satisfied* condition and finding it still true should write a second `evaluated_satisfied` event. Implemented: no — only a genuine not-met→met transition is ever persisted; a repeat-true evaluation is a no-op, generalizing the ADR's own stated principle rather than contradicting it. Directly tested (`TestEvaluateRepeatedSatisfaction`).

4. **`supersede` and `list_for_decision` were added beyond Sprint 10's own six named application methods.** `supersede` because ADR-CC-001 §2 requires `superseded` as one of exactly four event types, and no method in Sprint 10's own brief (`CreateCondition`, `ReviseCondition`, `RetireCondition`, `EvaluateCondition`, `ListConditions`, `ReadCurrentState`) can ever produce one — the same class of gap `DecisionDraft-Implementation-Design.md` §5.1 already had once for a missing repository method (Sprint 9's own disclosed finding #3), resolved the same way: a direct, mechanical completion, not a new capability. `list_for_decision` because ADR-CC-001 §6 establishes `decision_id` as a first-class optional back-reference, and "ListConditions" naturally includes listing by that reference alongside listing by Case — a minor scope-filling decision, not a new concept.

The C-02 authorship model (ADR-CC-001's own Invariants: "Unedited acceptance of an Atlas-proposed condition follows `ADR-002` C-02's authorship model exactly") is implemented as a single `authorship: "atlas" | "user" | "mixed"` field on the condition's own content, matching C-02's own canonical API property exactly (`docs/atlas_ux/governance/ADR-002-Critical-UX-Architecture-Resolutions.md` line 56). C-02's fuller, transient UI-state properties (`hasAtlasOrigin`, `originalAtlasText`, `acceptedAt`, `editedAt`) are not implemented — those describe live form-editing state for a React component that does not exist yet (no Decision Workspace UI has been built, confirmed again this sprint), not the backend aggregate's own persisted record. This is a minimal, correct application of the invariant to what actually exists to apply it to, not a partial implementation of it.

## 8. ADR Conflicts

None. `ADR-CC-001` was implementable exactly as written, using `DecisionDraft`'s own conventions as the structural template it explicitly is (§2: "directly generalizing `SecurityConfirmationEvent`'s own... shape"; Rationale: "an established, reusable architectural template").

## 9. Final Conformance Statement

`ADR-CC-001` is now **Fully Implemented**. Every Decision point (§1–§10) has a working, tested implementation:

- **§1** — `CaseCondition` is Case-scoped (`case_id`, always required) with an optional `decision_id` back-reference, enforced same-Case at creation (`CrossCaseDecisionError`).
- **§2** — Entirely event-sourced; no update method exists anywhere in the repository Protocol or its implementation; all four named event types (`revised`, `evaluated_satisfied`, `superseded`, `retired`) are implemented; only meaningful transitions are ever persisted, verified for both the not-met and repeat-met cases.
- **§3** — Predicate content is free text by default (`predicate_text`), with an optional structured sub-field (`structured_kind: "date" | "threshold"`) for the mechanically-evaluable subset; the evaluation engine treats the mechanical result as boolean-only-as-an-outcome, never as storage.
- **§4** — Monitoring and Invalidation are the same object type, differentiated by `role: "monitoring" | "invalidation"`, never separate aggregates.
- **§5** — Time-based (`evaluate_date_condition`) and state-based (`evaluate_threshold_condition`) conditions share one object shape but are dispatched to two genuinely distinct evaluation mechanisms; the date mechanism reuses the exact comparison idiom already established by `_is_thesis_stale`.
- **§6** — `decision_id` is optional; no field exists anywhere on `Decision` marking it "monitored" or "invalidated" — confirmed by `Decision`'s own entity being byte-for-byte unmodified this sprint.
- **§7** — No code path constructs a `CaseCondition` from `DecisionDraft` content this sprint (that integration is a future product-flow concern, not required by this sprint's own brief), but nothing here forecloses it — `create()`'s own content shape is a direct structural match for what a committed draft could supply.
- **§8** — Not built this sprint (no Daily Brief deliverable was in scope), but `list_for_case`/`list_for_decision` return the full `CaseConditionView`, and a narrower Daily Brief-specific projection remains a straightforward addition when that integration is scheduled, following the exact precedent `DecisionDraftService.daily_brief_summary` already set.
- **§9** — `atlas/monitoring` was not touched, imported, or referenced anywhere in this sprint's own code; confirmed via `git diff --stat`.
- **§10** — Every rejected model remains rejected: no separate `MonitoringCondition`/`ReviewSchedule` split was built; no generic cross-scope Watch Condition; the aggregate is a real, typed object with a derived projection, not bare events or a mutable row.

This closes Sprint 10. `ADR-CC-001` moves from "Not Implemented" (Sprint 7's own Conformance Register) to "Fully Implemented." Per this sprint's own closing note, `ADR-AS-001` (Assumption) is now unblocked: its own event-stream pattern (`ADR-AS-001` §10) can reuse `CaseConditionEvent`'s own now-shipped shape directly, the same way this sprint reused `DecisionDraftEvent`'s.

## Related

`docs/ADR-CC-001-CaseCondition.md` (the ADR this implementation realizes). `docs/DecisionDraft-Implementation-Design.md`, `docs/DecisionDraft-Implementation-Report.md` (the Sprint 9 precedent this sprint's own conventions are drawn from). `docs/ADR-CC-001-Conformance-Report.md` (Sprint 7's own "Not Implemented" starting point this sprint closes out). `docs/Atlas-Architecture-Conformance-Register.md` (Wave C).
