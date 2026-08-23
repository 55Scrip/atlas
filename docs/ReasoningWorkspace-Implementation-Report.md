# Reasoning Workspace Implementation Report

**Sprint 12 — Orchestration implementation.** Implementation notes only. No ADR was written or modified this sprint, and none needed to be — this sprint introduces no new domain concept, only a workflow layer over five already-Accepted, already-Fully-Implemented aggregates (`ADR-DC-001`, `ADR-DD-001`, `ADR-CR-001`, `ADR-CC-001`, `ADR-AS-001`).

---

## 1. Execution Report

Implemented `ReasoningWorkspaceService` (the two orchestration workflows named in Sprint 12 §1/§2), a `read_models.py` module (§3), and a REST API surface over both (§4). Every write in this sprint is a call to `DecisionDraftService.commit()`, `AssumptionService.create()`/`.attach_case_condition()`, or `CaseConditionService.create()` — all four already-shipped, unmodified. Every read is a call to one of those services' own existing listing/read methods, or, where no existing method provides the exact shape needed (finding the draft that became a given Decision), a read-only call directly against a sibling repository — the identical pattern `AssumptionService` itself already established for reading `CaseConditionEventRepository` in Sprint 11.

No ADR conflict was found. No aggregate boundary was crossed, merged, or reinterpreted.

## 2. Files Created

**Application** (`atlas/core/application/reasoning_workspace/`): `__init__.py`, `reasoning_workspace_service.py` (`DecisionReasoningWorkspace`, `AssumptionWithLinkedConditions`, `DraftCommitWithReasoningResult`, `ReasoningWorkspaceService` with `load_workspace` and `commit_draft_with_reasoning`), `read_models.py` (`ActiveAssumptionRow`, `ActiveCaseConditionRow`, `OpenDecisionDraftRow`, and their three list functions).

**API** (`atlas/core/infrastructure/api/reasoning_workspace/`): `__init__.py`, `schemas.py`, `router.py` (5 routes — see §4), `dependencies.py`. No `errors.py` — see §4's own note on why none is needed.

**Tests**: `tests/unit/application/reasoning_workspace/{__init__.py,test_reasoning_workspace_service.py,test_read_models.py}`, `tests/unit/infrastructure/api/reasoning_workspace/{__init__.py,test_router.py}`.

No new domain package, no new persistence package, no new table, no new event type, no new exception type — a direct, deliberate consequence of "no ontology redesign / no new primitive concepts."

## 3. Files Modified

**`atlas/core/infrastructure/api/app.py`** — the same addition pattern as Sprints 9–11: one import block plus `app.include_router(reasoning_workspace_router)`. No `register_*_error_handlers` call was added, because this package registers none (§4). 37 insertions, 0 deletions, one file — the only tracked file this sprint touches.

No other existing file was modified. Confirmed directly: `git diff --stat` against every domain, application, persistence, and API package built across Sprints 9–11 (`decision`, `decision_context`, `case`, `decision_draft`, `case_condition`, `assumption`, `security_confirmation`) returns empty.

## 4. API Routes

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/decisions/{decision_id}/reasoning-workspace` | Assemble the full reasoning state for one Decision |
| `POST` | `/decision-drafts/{draft_id}/commit-with-reasoning` | Commit a draft, optionally creating Assumptions and (optionally-linked) CaseConditions |
| `GET` | `/cases/{case_id}/reasoning/active-assumptions` | Read model: active Assumptions for a Case |
| `GET` | `/cases/{case_id}/reasoning/active-case-conditions` | Read model: active CaseConditions for a Case |
| `GET` | `/reasoning/open-decision-drafts` | Read model: open DecisionDrafts for a user (`userId` query param) |

**No dedicated `errors.py`.** Every exception `ReasoningWorkspaceService` can raise (`DecisionNotFoundError`, `DecisionDraftAlreadyCommittedError`, `MissingSubjectError`, `CaseConditionNotFoundForLinkError`, `AssumptionTerminatedError`, etc.) originates from an existing service it calls, and each already has an app-wide handler registered from that service's own sprint. This is itself evidence the orchestration layer introduces no new failure mode of its own — every error a caller can hit is one the underlying aggregate already defined.

Every response schema reuses an existing one directly (`DecisionSummary`, `DecisionContextResponse`, `DecisionDraftResponse`, `AssumptionResponse`, `CaseConditionResponse`) — per Sprint 12's own "reuse existing DTO conventions" instruction, and the identical choice `CommitDecisionDraftResponse` already made in Sprint 9.

## 5. Tests

| Category | File(s) | Result |
|---|---|---|
| Orchestration | `test_reasoning_workspace_service.py` | 13 passed |
| Projection | `test_read_models.py` | 4 passed |
| API/integration | `test_router.py` | 9 passed |
| **New tests, total** | | **26 passed, 0 failed** |
| Regression | `decision`, `decision_context`, `case`, `decision_draft`, `case_condition`, `assumption` (all layers), `security_confirmation`, `test_architecture_boundaries.py` | 572 passed, 0 failed |
| **Combined** | | **598 passed, 0 failed** |

`test_commit_draft_with_reasoning.py`'s own `test_creates_and_links_case_conditions_to_their_assumption` is the definitive proof of Deliverable 1: it commits a draft, creates an Assumption and a linked CaseCondition, and independently re-reads the Assumption via the real, unmodified `AssumptionService.read()` to confirm the link was actually persisted through `attach_case_condition()` — not merely returned in the orchestration response. `test_load_workspace`'s own `test_does_not_mutate_any_underlying_aggregate` is the executable proof of "without merging ownership": it snapshots `Decision`/`DecisionContext` before calling `load_workspace`, then confirms both are byte-for-byte identical after — the workspace composition is read-only, with no side channel back into any aggregate it assembles.

## 6. Build Results

Backend composition builds successfully: `create_app()` succeeds, and all 5 new routes are present and dispatchable (verified via the live OpenAPI schema).

## 7. Implementation Findings

Two findings, both interpretive resolutions of language in Sprint 12's own brief, not architectural decisions.

1. **"DecisionDraft (if active)" is two things, not one.** Sprint 12 §2 asks the workspace to assemble "DecisionDraft (if active)" for a *Decision* — but a Decision's own originating draft, if any, is by definition no longer active once committed (its own status becomes `"committed"`, ADR-DD-001 §3/§4). Read literally, "if active" would make this field always empty for any Decision that has one. Implemented as two separate fields instead: `originating_draft` (the draft that became this Decision, if any — found by scanning `DecisionDraftEventRepository.list_latest_by_case` for a `"committed"` event naming this Decision, since no existing repository method answers "which draft became this Decision" directly) and `active_case_drafts` (any other currently-active, uncommitted drafts on the same Case — e.g., a reconsideration already in progress, consistent with `ADR-CR-001`'s own Related section: "Reconsideration may begin as a DecisionDraft"). This resolves the apparent contradiction in the brief's own wording without dropping either piece of information a reasonable reading of "DecisionDraft (if active)" could have wanted.

2. **"Assumptions [and] linked CaseConditions" (Sprint 12 §1) means CaseConditions linked *to the Assumptions being created*, not merely linked to the Decision.** `CaseCondition` already links to a Decision via its own optional `decision_id` (ADR-CC-001 §6) — that relationship needs no new orchestration to establish (`CaseConditionService.create()` already accepts `decision_id` directly). The one relationship worth automating at commit time is `Assumption` ↔ `CaseCondition` (ADR-AS-001 §8), which is why `commit_draft_with_reasoning` accepts `AssumptionWithLinkedConditions` (each assumption paired with the conditions to create and attach to it) plus a separate `standalone_case_condition_contents` list for conditions with no assumption to link to. Both paths are exercised by dedicated tests.

**No modification to `DecisionDraft`'s own schema.** A tempting alternative design would have stored proposed assumption/condition content directly on `DecisionDraftEvent`, so a single `commit()` call could read them back. This was deliberately rejected: it would change an already-shipped aggregate's own content shape (a real "aggregate ownership" change Sprint 12 §1 explicitly forbids), for a need the orchestration layer already satisfies by simply accepting that content as extra parameters to a new, additive method. `DecisionDraftEvent`'s own table and entity are confirmed byte-for-byte unmodified.

## 8. ADR Conflicts

None. No ADR was consulted for permission to build this layer beyond the five already-Accepted ontology ADRs whose own services this sprint calls; none of their own invariants were touched, reinterpreted, or worked around.

## 9. Final Conformance Statement

Sprint 12's own Definition of Done is met in full:

- **Decision, DecisionContext, DecisionDraft, Assumption, and CaseCondition work together through orchestration, not direct coupling** — `ReasoningWorkspaceService` and `read_models.py` are the only new code, and neither contains a domain-object constructor call, a repository write, or a validation rule of its own; every mutation and every non-trivial read is delegated to the aggregate's own existing service.
- **Aggregate ownership is unchanged** — zero new tables, zero new event types, zero modified entity/table/repository files across all five aggregates (confirmed by `git diff --stat`).
- **Existing ADRs remain valid without modification** — `ADR-DC-001`, `ADR-DD-001`, `ADR-CR-001`, `ADR-CC-001`, `ADR-AS-001` were not edited, and this sprint required no new ADR of its own (a workflow layer over an already-settled ontology, exactly as Sprint 12's own closing framing anticipated).
- **Full regression suite passes** — 598 passed, 0 failed, spanning every aggregate this sprint touches plus every one it deliberately leaves alone.

This closes Sprint 12. The project now has both a complete core ontology (Sprints 9–11) and a first orchestration layer over it (this sprint) — the two-part foundation Sprint 12's own closing note names as the basis for "higher-level reasoning workflows and product capabilities built on top."

## Related

`docs/DecisionDraft-Implementation-Report.md`, `docs/CaseCondition-Implementation-Report.md`, `docs/Assumption-Implementation-Report.md` (Sprints 9–11, the five services this sprint composes). `docs/ADR-DD-001-Decision-Draft.md`, `docs/ADR-CC-001-CaseCondition.md`, `docs/ADR-AS-001-Assumption.md` (the governing ADRs, none modified). `docs/Atlas-Architecture-Conformance-Register.md` (Wave E).
