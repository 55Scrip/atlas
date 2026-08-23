# Assumption Implementation Report

**Sprint 11 — Production implementation.** Implementation notes only. `docs/ADR-AS-001-Assumption.md` remains the authoritative architecture. As with Sprint 10 (`ADR-CC-001`), no separate implementation-design document preceded this sprint — design choices were made during implementation, directly against the ADR's own text and `CaseCondition`'s already-shipped conventions (Sprint 10, itself built on `DecisionDraft`, Sprint 9), and are disclosed here.

---

## 1. Execution Report

The complete `Assumption` aggregate was implemented: domain, persistence, application service, REST API (including its two integration relationships — Decision ↔ Assumption and CaseCondition ↔ Assumption — using existing IDs only, exactly as scoped), and router registration, plus a full test suite across all layers and an end-to-end integration test. Every design choice either (a) is dictated directly by `ADR-AS-001`'s own Decision/Invariants sections, (b) mirrors an established `CaseCondition`/`DecisionDraft` convention, or (c) is a small, disclosed implementation-level resolution of something the ADR's own text leaves open (§6, Implementation Findings).

No ADR conflict was found. `ADR-AS-001` was implementable in full.

## 2. Files Created

**Domain** (`atlas/core/domain/assumption/`): `__init__.py`, `value_objects.py` (`AssumptionId`), `entity.py` (`AssumptionEvent`, `AssumptionEventType`, `AssumptionAuthorship`, `AssumptionChallengeSeverity`, `AssumptionView`, `is_terminal`, `reconstruct_current_state`), `exceptions.py`, `repository.py` (`AssumptionEventRepository` Protocol).

**Application** (`atlas/core/application/assumption/`): `__init__.py`, `assumption_service.py` (`AssumptionContent`, `AssumptionService` with `create`, `revise`, `challenge`, `attach_case_condition`, `detach_case_condition`, `retire`, `supersede`, `read`, `list_events`, `list_for_decision`, `list_for_case`).

**Persistence** (`atlas/core/infrastructure/persistence/assumption/`): `__init__.py`, `table.py` (`assumption_events_table`, `create_assumption_events_table`), `sqlalchemy_repository.py` (`SqlAlchemyAssumptionEventRepository`).

**API** (`atlas/core/infrastructure/api/assumption/`): `__init__.py`, `schemas.py`, `router.py` (11 routes — see §4), `errors.py`, `dependencies.py`.

**Tests**: `tests/unit/domain/assumption/{__init__.py,test_entity.py,test_value_objects.py}`, `tests/unit/application/assumption/{__init__.py,test_assumption_service.py,test_end_to_end.py}`, `tests/unit/infrastructure/persistence/assumption/{__init__.py,test_sqlalchemy_repository.py}`, `tests/unit/infrastructure/api/assumption/{__init__.py,test_router.py}`.

## 3. Files Modified

**`atlas/core/infrastructure/api/app.py`** — the same two-addition pattern as Sprints 9 and 10: import lines plus `app.include_router(assumption_router)` and `register_assumption_error_handlers(app)`, inserted at the correct alphabetical position. 28 insertions, 0 deletions, one file — the only tracked file this sprint touches.

No other existing file was modified. Confirmed directly: `git diff --stat` against `Decision`, `DecisionContext`, `Case`, `DecisionDraft`, `CaseCondition`, `security_confirmation`, and their persistence/API counterparts returns empty — `Hypothesis`, `Evidence`, `Conclusion`, and `Judgment` were never even imported by any new file, consistent with `ADR-AS-001`'s own Consequences ("no existing object in the epistemic family... requires modification").

## 4. API Routes

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/decisions/{decision_id}/assumptions` | Create |
| `GET` | `/decisions/{decision_id}/assumptions` | List for a Decision |
| `GET` | `/cases/{case_id}/assumptions` | List for a Case (across Decisions) |
| `GET` | `/assumptions/{assumption_id}` | Read current state |
| `GET` | `/assumptions/{assumption_id}/events` | Full event history |
| `PATCH` | `/assumptions/{assumption_id}` | Revise |
| `POST` | `/assumptions/{assumption_id}/challenge` | Record a challenge (default) or invalidation (`severity`) |
| `POST` | `/assumptions/{assumption_id}/retire` | Retire (idempotent, 204) |
| `POST` | `/assumptions/{assumption_id}/supersede` | Supersede (with optional replacement reference) |
| `POST` | `/assumptions/{assumption_id}/case-conditions/{condition_id}/attach` | Link a CaseCondition (idempotent) |
| `POST` | `/assumptions/{assumption_id}/case-conditions/{condition_id}/detach` | Unlink a CaseCondition (idempotent) |

No `DELETE` verb anywhere — `detach` is a `POST`, matching the same, already-disclosed codebase convention `security_confirmation/api/router.py` states explicitly ("a DELETE verb would misdescribe what revoke really does").

## 5. Tests

| Layer | File(s) | Result |
|---|---|---|
| Domain | `test_entity.py`, `test_value_objects.py` | 20 passed |
| Application | `test_assumption_service.py` | 28 passed |
| Integration end-to-end | `test_end_to_end.py` | 1 passed |
| Persistence | `test_sqlalchemy_repository.py` | 9 passed |
| API | `test_router.py` | 19 passed |
| **New tests, total** | | **77 passed, 0 failed** |
| Regression | `decision`, `decision_context`, `case`, `decision_draft`, `case_condition` (all layers), `security_confirmation`, `test_architecture_boundaries.py` | 495 passed, 0 failed |
| **Combined** | | **572 passed, 0 failed** |

`test_end_to_end.py` is the definitive conformance check for the Integration deliverable: it creates an Assumption anchored to a real `Decision` (case_id derived transitively, never separately supplied — directly tested by `test_derives_case_id_transitively_from_the_decision`), attaches a real `CaseCondition` created via `CaseConditionService`, challenges the assumption, reaffirms it via a plain revision (proving the CaseCondition link survives a challenge-then-revise cycle, since `revise()` carries the current link set forward), and supersedes it — then asserts `Decision`, `Case`, and the `CaseCondition` it referenced were never mutated by any of it. `test_assumption_service.py::TestAttachDetachCaseCondition` covers the integration in isolation, including the required existence check (`test_attach_rejects_an_unknown_case_condition`) and idempotency in both directions.

## 6. Build Results

Backend composition builds successfully: `create_app()` succeeds, and all 11 new routes are present and dispatchable (verified via the live OpenAPI schema, the same diagnostic method Sprint 10's own report already established as necessary at this FastAPI/Starlette version). No frontend deliverable was in scope this sprint (matching Sprint 10's own precedent; Sprint 11's brief lists none), so no frontend build was run.

## 7. Implementation Findings

Five findings. None changes an aggregate boundary, the four required event types' own meaning, a repository contract, or API semantics beyond what those four types and the two named integration relationships require to be usable.

1. **Decision-anchored, not Case-scoped — `case_id` is never caller-supplied.** ADR-AS-001 §1 adopts Assumption as "a stable, Decision-anchored identity (with `case_id` reachable transitively...)" — the identical shape `DecisionContext` already has (no `case_id` field of its own). Implemented: `decision_id` is required on every event; `case_id` is derived from the referenced `Decision` at creation time and denormalized onto every event row for query efficiency, but is never an independently supplied parameter — `create()` takes only `decision_id`. This is a real, evidenced difference from `CaseCondition` (Case-scoped, optional `decision_id`), not a copy-paste of its shape; getting this backwards would have been a genuine ontology error, not a detail.

2. **Attach/detach append a `"revised"` event, not a new event type.** ADR-AS-001's own Invariants name exactly four event types (`revised`, `challenged`, `retired`, `superseded`) — no fifth type exists for the §8 cross-reference. Implemented: the loose, optional link to `CaseCondition` (`linked_case_condition_ids`) is ordinary content carried on the same full-snapshot `revised` event every other edit uses. `attach_case_condition`/`detach_case_condition` read the assumption's own current `statement`/`authorship` first and carry them forward unchanged, so the caller never has to resupply unrelated content just to attach or detach one reference. This uses "existing IDs only," per Sprint 11's own Integration instruction — no new join table, no field added to `CaseCondition` itself (confirmed: that package remains byte-for-byte unmodified).

3. **`challenge` and `supersede` were added beyond Sprint 11's own seven named application methods.** The same class of gap Sprint 10 already found once for `CaseCondition` (a missing `supersede` method): ADR-AS-001's own four required event types include two (`challenged`, `superseded`) that no method in Sprint 11's own brief (`CreateAssumption`, `ReviseAssumption`, `RetireAssumption`, `AttachCaseCondition`, `DetachCaseCondition`, `ListAssumptions`, `ReadCurrentState`) can ever produce. Resolved identically: direct, mechanical completions, not new capabilities.

4. **"Challenged"/"Invalidated" are one event type differentiated by a `severity` field**, per ADR-AS-001 §9's own explicit instruction ("collapse toward one event type, differentiated by degree, not a truth verdict") — `severity: "challenged" | "invalidated"`, defaulting to `"challenged"`. This is the direct, minimal reading of that sentence, not an invented distinction.

5. **Terminal vs. non-terminal, and "superseded" carries an optional forward reference** — both are the identical implementation-level resolutions already applied to `CaseCondition` (Sprint 10) and disclosed there: `superseded`/`retired` terminal, `revised`/`challenged` not (an assumption may be revised again after a challenge — directly tested: `test_can_revise_after_being_challenged`, `test_a_later_revision_resets_status_to_supported_after_a_challenge`); `superseded_by_assumption_id` modeled on `CaseConditionEvent.superseded`'s own `superseded_by_condition_id`.

The C-02 authorship model (ADR-AS-001's own Invariants) is implemented identically to `CaseCondition`'s own scope decision (Sprint 10, Implementation Finding): a single `authorship: "atlas" | "user" | "mixed"` field, matching C-02's canonical API property exactly, without the fuller transient UI-state properties that describe a live-editing form which does not exist yet.

## 8. ADR Conflicts

None. `ADR-AS-001` was implementable exactly as written, reusing `CaseCondition`'s own event-stream pattern precisely as §10 requires ("the fourth reuse of the Security-Confirmation-derived pattern in this document series" — now the fifth, counting `CaseCondition` itself).

## 9. Final Conformance Statement

`ADR-AS-001` is now **Fully Implemented**. Every Decision point (§1–§12) has a working, tested implementation:

- **§1** — `Assumption` is Decision-anchored (`decision_id`, required); `case_id` reachable transitively, never separately asserted; content is free text (`statement`), Atlas-proposable/investor-editable (`authorship`).
- **§2** — Truth is never a stored binary verdict; `status` (`supported`/`challenged`/`invalidated`) is entirely a derived projection over the event stream, never a stored field.
- **§3, §5, §6** — `Assumption` remains a wholly separate object from `Hypothesis`, `Conclusion`, and `Judgment`; none of the three is imported, referenced, or modified by any file in this sprint.
- **§4** — No direct coupling to `Evidence` beyond an optional `evidence_id` reference on a `challenged` event — never a required field, never a verdict.
- **§7** — No field exists on `Decision` for Assumptions; `Decision`'s own entity is confirmed byte-for-byte unmodified.
- **§8** — `Assumption` ↔ `CaseCondition` is a loose, optional, ID-only cross-reference (`linked_case_condition_ids`), attach/detach both idempotent, neither aggregate contains or is merged with the other; `CaseCondition`'s own entity, table, and repository are confirmed byte-for-byte unmodified.
- **§9** — Lifecycle implemented leaner than an eight-state model exactly as described: no `"Draft"` state, `"Accepted"` is the creation event, `"Supported"` is a projection, `"Challenged"`/`"Invalidated"` are one event type differentiated by `severity`, `"Retired"` is a distinct terminal event, `"Rejected"` has no event (an Atlas-proposed candidate never accepted is simply never created).
- **§10** — The identical event-stream pattern established for `CaseCondition` — no update method anywhere in the repository Protocol or its implementation; verified by the type system, not convention.
- **§11** — `OutlookAssumption` (`atlas/analysis_engine/outlook.py`) was not touched, imported, or referenced anywhere in this sprint's own code.
- **§12** — Every rejected model remains rejected: no free text on `Decision.reason`; no forced `CaseCondition` evaluation lifecycle on every Assumption; no `KnowledgeReference`-shaped reference object; no enforced pipeline ordering against `Hypothesis`.

This closes Sprint 11. Per this sprint's own closing note, completing it finishes the implementation of the core ontology defined by Investigations 1–8 and their adopted ADRs (`ADR-DC-001`, `ADR-DD-001`, `ADR-CR-001`, `ADR-CC-001`, `ADR-AS-001` — all now Fully Implemented). Remaining work moves to higher-level reasoning workflows and product capabilities built on top of these five foundations, not further core-ontology construction.

## Related

`docs/ADR-AS-001-Assumption.md` (the ADR this implementation realizes). `docs/CaseCondition-Implementation-Report.md`, `docs/DecisionDraft-Implementation-Report.md` (the Sprint 10/9 precedents this sprint's own conventions are drawn from). `docs/ADR-AS-001-Conformance-Report.md` (Sprint 7's own "Not Implemented" starting point this sprint closes out). `docs/Atlas-Architecture-Conformance-Register.md` (Wave D).
