# DecisionDraft Implementation Report

**Sprint 9 — Production implementation.** Implementation notes only, per this sprint's own instruction ("update only documentation required by implementation... no architecture rewriting, no ADR edits"). This is a record of what was built and verified, not a new design document — `docs/ADR-DD-001-Decision-Draft.md` and `docs/DecisionDraft-Implementation-Design.md` remain the authoritative architecture and design.

---

## 1. Execution Report

The complete `DecisionDraft` aggregate was implemented exactly as `DecisionDraft-Implementation-Design.md` specifies: domain, persistence, application service, REST API, router registration, a full test suite across all four backend layers plus an end-to-end test, and the Alpha frontend's typed API client. Every file matches the Migration Plan's own §8.1 list precisely, with one disclosed, mechanical addition (a repository method, §6 below). The design document was read in full before implementation began and re-consulted at each layer while building; no section of it was reinterpreted.

Two small implementation-detail corrections were made against the design document itself, where the design's own prose conflicted with the actual, already-registered conventions in this codebase (§6, Implementation Findings). Both are HTTP-transport-level choices (a status code, a query-parameter alias), not ontology, not aggregate boundaries, not repository contracts — squarely inside this sprint's own "Allowed Decisions."

No ADR conflict was found. `ADR-DD-001` was implementable exactly as written; nothing encountered during implementation required stopping to document an architectural contradiction.

## 2. Files Created

**Domain** (`atlas/core/domain/decision_draft/`): `__init__.py`, `value_objects.py` (`DraftId`), `entity.py` (`DecisionDraftEvent`, `DecisionDraftEventType`, `DecisionDraftView`, `reconstruct_current_state`), `exceptions.py` (`DecisionDraftError`, `DecisionDraftNotFoundError`, `DecisionDraftAlreadyAbandonedError`, `DecisionDraftAlreadyCommittedError`, `DecisionDraftConflictError`), `repository.py` (`DecisionDraftEventRepository` Protocol).

**Application** (`atlas/core/application/decision_draft/`): `__init__.py`, `decision_draft_service.py` (`DecisionDraftContent`, `DecisionDraftCommitResult`, `DecisionDraftSummary`, `DecisionDraftService` with exactly the eight methods the design names: `create`, `revise`, `abandon`, `commit`, `get`, `list_active_for_case`, `list_events`, `daily_brief_summary`).

**Persistence** (`atlas/core/infrastructure/persistence/decision_draft/`): `__init__.py`, `table.py` (`decision_draft_events_table`, `create_decision_draft_events_table`), `sqlalchemy_repository.py` (`SqlAlchemyDecisionDraftEventRepository`).

**API** (`atlas/core/infrastructure/api/decision_draft/`): `__init__.py`, `schemas.py`, `router.py`, `errors.py`, `dependencies.py`.

**Frontend**: `frontend/src/decisionWorkspace/decisionDraftApi.ts`.

**Tests**: `tests/unit/domain/decision_draft/{__init__.py,test_entity.py,test_value_objects.py}`, `tests/unit/application/decision_draft/{__init__.py,test_decision_draft_service.py,test_end_to_end.py}`, `tests/unit/infrastructure/persistence/decision_draft/{__init__.py,test_sqlalchemy_repository.py}`, `tests/unit/infrastructure/api/decision_draft/{__init__.py,test_router.py}`.

`test_end_to_end.py` is one file beyond the design's own §8.3 list (which named five files); the design's own §9 separately specifies an end-to-end test as its own testing category, so it is given its own file rather than folded into `test_decision_draft_service.py` — a file-organization choice, not a scope change.

## 3. Files Modified

**`atlas/core/infrastructure/api/app.py`** — exactly the two functional additions §8.2 specifies (`app.include_router(decision_draft_router)`, `register_decision_draft_error_handlers(app)`), plus their corresponding import lines and one explanatory comment, in the same style as every other entry in that file. `git diff --stat` confirms this is the only tracked file touched by this sprint: 10 insertions, 0 deletions, one file.

No other existing file was modified. Confirmed directly: `git diff --stat` against `atlas/core/domain/decision/`, `atlas/core/domain/decision_context/`, `atlas/core/domain/case/`, `atlas/alpha/security_confirmation/`, and their persistence/API counterparts returns empty — byte-for-byte unchanged, as the design's own Definition of Done requires.

## 4. Test Results

| Layer | File(s) | Result |
|---|---|---|
| Domain | `test_entity.py`, `test_value_objects.py` | 14 passed |
| Application | `test_decision_draft_service.py` | 31 passed |
| End-to-end | `test_end_to_end.py` | 1 passed |
| Persistence | `test_sqlalchemy_repository.py` | 10 passed |
| API | `test_router.py` | 21 passed |
| **New tests, total** | | **77 passed, 0 failed** |
| Regression | `decision`, `decision_context`, `case` (domain/application/persistence/API), `security_confirmation`, `test_architecture_boundaries.py` | 327 passed, 0 failed |
| **Combined (new + regression)** | | **404 passed, 0 failed** |

Every row in the design's own Conformance Matrix (§11) has a passing, named test behind it — none rest on "trust the design" alone. In particular: `test_propagates_missing_subject_unmodified`/`_missing_reason_unmodified`/`_invalid_confidence_unmodified` are the executable proof that `commit()` never reimplements `Decision`'s own validation (§3 of the ADR); `test_returns_only_narrow_fields`/`test_returns_only_narrow_fields_for_active_drafts` are the executable proof of the Daily Brief narrow-projection invariant (§4); `test_full_create_revise_commit_flow_produces_a_real_decision_and_context` is the end-to-end proof of the commit boundary as a whole.

**Full-suite context.** A full `pytest tests/` run was also performed. Beyond the 404 tests this sprint owns, 210+ pre-existing failures were observed in unrelated files (`test_weekly_review_*`, `test_value_scenario_*`, `test_temporary_workspace_validation_cli_*`, `test_unsupported_locale_regression_*`). These are confirmed unrelated to this sprint: `git status` shows zero modification to any of them or anything they import; their failures are CLI-subprocess invocations of the installed `atlas` entry point failing with `ModuleNotFoundError: No module named 'atlas'`, and their own tracebacks resolve to a `/Users/axelgreitz/Downloads/atlas_v0_1_0/` path — a different directory than this checkout — indicating a pre-existing local environment/packaging artifact, not a code defect this sprint introduced. This is reported for transparency, not swept aside; it was investigated, not assumed.

## 5. Build Results

- **Backend import/composition:** `create_app()` builds successfully; the app now exposes routes for `case`, `decision`, `decision_context`, `decision_draft`, and every other existing router — 29 top-level routes total (including the new eight from this sprint).
- **Frontend typecheck:** `npm run typecheck` (`tsc --noEmit`) — clean, zero errors, across the whole frontend including the new `decisionDraftApi.ts`.
- **Frontend production build:** `npm run build` (`vite build`) — succeeds, 109 modules transformed, only a pre-existing chunk-size advisory warning unrelated to this change.

## 6. Implementation Findings

Three small, disclosed findings surfaced during implementation. None changes an aggregate boundary, the event model, a repository contract's own meaning, or API semantics — each is squarely within this sprint's own "Allowed Decisions" (helper functions, SQL query shape, component decomposition).

1. **HTTP status code for propagated `Decision`/`DecisionContext` validation errors.** The design's own §6.4 error table says commit-time validation failures from `Decision.register()` map to **400**. The actual, already-registered, app-wide convention (`atlas/core/infrastructure/api/decision/errors.py`, registered in `app.py` before this sprint) maps `DecisionValidationError` to **422**; `DecisionContextValidationError` (a different exception family) does map to 400. This is a citation error in the design document, not an architectural decision — the design's own governing principle is "follow existing API conventions exactly" and "let `Decision`'s own errors propagate unmodified." Implemented per the actual, existing convention (422 for `Decision`'s own errors; 400 remains correct for `DecisionContext`'s own errors, unaffected). Verified directly: `tests/unit/infrastructure/api/decision_draft/test_router.py::TestCommitDecisionDraft::test_returns_422_for_missing_subject` passes against the real, already-registered handler — no new handler was written for this case at all (see finding 3).

2. **Query-parameter casing for `GET /decision-drafts/daily-brief-summary`.** ADR-004 establishes camelCase as this app's wire format for JSON bodies; it does not by itself camelCase a bare FastAPI path/query function parameter, which defaults to its Python name. Implemented with an explicit `Query(alias="userId")`, consistent with ADR-004's own broader camelCase-wire-format intent, applied to the one query parameter this design introduces (no other endpoint in this codebase previously needed a named, camelCase query parameter, so there was no existing precedent to follow literally — this extends the same standard, not a new one).

3. **One additional repository method: `list_latest_by_user`.** The design's own §5.1 code block specifies four repository methods (`add`, `get_latest_event`, `list_events`, `list_latest_by_case`); its own §6.1 specifies a `GET .../daily-brief-summary?userId=...` route with no case scoping, and its own §5.3 already names a `user_id` index as "a low-cost forward-compatibility index for a future 'my drafts across every Case' query." No method in §5.1's own code block can serve that route without scanning every event in the table. `list_latest_by_user` was added, mirroring `list_latest_by_case` exactly, as the direct, mechanical completion of what §5.3 and §6.1 already specify together — not a new capability, a missing piece of an already-fully-specified one. Both the Protocol (`repository.py`) and its SQLAlchemy implementation carry an inline note pointing back to this report.

## 7. ADR Conflicts

None. `ADR-DD-001` was implementable in full, exactly as written, using `DecisionDraft-Implementation-Design.md` as the blueprint. No genuine architectural contradiction was encountered; nothing here required inventing new ontology, reopening a Decision point, or amending the ADR.

## 8. Final Conformance Statement

`ADR-DD-001` is now **Fully Implemented**. Every Decision point (§1–§6) has a working, tested implementation:

- **§1** — `DecisionDraft` is Case-scoped (`case_id`), investor-owned (`user_id`), never `decision_id`-keyed.
- **§2** — Built entirely on the append-only-events-plus-derived-projection pattern, reusing `SecurityConfirmationEvent`'s own shape; no update method exists anywhere in the repository Protocol or its implementation.
- **§3** — `commit()` calls `Decision.register()` and (conditionally) `DecisionContext.capture()` directly and unmodified; both aggregates' own repositories are called via their own unmodified `add()`; every validation exception either raises propagates through this codebase's own real, pre-existing error-handling chain, with zero new validation logic written for draft content.
- **§4** — `GET /decision-drafts/daily-brief-summary` and `DecisionDraftSummaryResponse` structurally cannot carry `reason`, `confidence`, `situation`, or any other full-content field — enforced by the type, not merely by convention, and verified by a dedicated test.
- **§5** — `committed_decision_id` is optional and additive, carried only on the terminal event, never a required field on `Decision` itself; `Decision`'s own `source`/value objects are untouched.
- **§6** — Every rejected model remains rejected: no mutable status field was added to `Decision`; `DecisionContext` was not repurposed; the aggregate is a real, typed object, not a generic bag; the event stream always has a derived projection, never bare events with no reconstruction.

This closes Sprint 9. `ADR-DD-001` moves, in Sprint 7's own Conformance Register terms, from "Not Implemented" to "Fully Implemented" — Wave B of the Architecture Conformance Register's own recommended implementation waves is complete.

## Related

`docs/ADR-DD-001-Decision-Draft.md` (the ADR this implementation realizes). `docs/DecisionDraft-Implementation-Design.md` (the authoritative blueprint this report confirms was followed). `docs/ADR-DD-001-Conformance-Report.md` (Sprint 7's own "Not Implemented" starting point this sprint closes out). `docs/Atlas-Architecture-Conformance-Register.md` (Wave B).
