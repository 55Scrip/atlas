# Decision Case Context — Implementation Design

## Status

Implementation-design artifact, not a normative document. Carries no Doctrine status. Where anything here appears to conflict with the Architecture Doctrine, OE-002 through OE-006, the Historical Decision Record, or `Decision-Implementation-Design.md`, those documents govern and this one is wrong and must be corrected.

## Package Identifier

The Decision-integration package following Package R2 (`Core-Loop-Observation-Case-Context-Implementation-Design.md`, implemented in commits `3fecb0e`/`b41f0ff`). Design only. No code, test, or existing document is modified by this package.

## 1. Executive Finding

**Decision integration work is required, and its correct scope is narrow: add Case ownership (`case_id`) to the existing Decision aggregate, mirroring exactly the precedent already established for Observation (DO-IMP-006, Package R2).** Decision is a Final-adopted Domain Object (OE-002 §5.5, §4 item 5) and is therefore bound by INV-002 ("every Domain Object MUST belong to exactly one Case") — yet the current, fully-implemented, production-serving `Decision` entity has no `case_id` field anywhere: not in the domain entity, the application request, the persistence table, or the REST API. This is a genuine, unambiguous gap, not an invented one.

**This design deliberately does not attempt a second, much larger, and genuinely unsettled question: whether Decision's existing field set (`user_id`, `decision_type`, `subject`, `investment_case`, `confidence`, `source`) is a conforming realization of the OE-002-adopted minimal Decision shape (`commitment_content` and/or `matter_target_type`/`matter_target_id`) described in `Decision-Implementation-Design.md`.** That document's own Section 38 and Section 41 explicitly decline to resolve this, deferring it to "that same future migration effort" performed by a "Case Representation Strategy" document — which does not exist anywhere in this repository (already established as a historical inconsistency in `Core-Loop-Case-Context-Reconciliation-Investigation.md`, Section 40). Resolving it now would be exactly the kind of "ontology change hidden inside implementation details" this task forbids, and would require touching or reasoning about roughly a dozen unrelated downstream packages that consume Decision's current shape directly (Section 5, Gap G2).

The problem is **mixed**: a genuine, in-scope **domain + application + persistence + interface** gap (missing `case_id`), plus a real but **out-of-scope ontology question** (field-set reconciliation) that must be reported, not silently resolved, plus a **mechanical, disclosed test-fixture consequence** spanning nine unrelated files that construct `Decision.register(...)` directly.

## 2. Repository Evidence

**Governing documents read fresh for this task**: `Decision-Implementation-Design.md` (in full, including its appended Committed-To Matter Completeness Review); `OE-002-Domain-Object-Model.md` §3, §3.1, §4, §5.5, §6; `OE-004-Domain-Invariants.md` INV-002 through INV-006, INV-012; `OE-006-Domain-Acceptance-Model.md` (in full); `Core-Loop-Case-Context-Reconciliation-Investigation.md` (commit `a4e9c42`); `Core-Loop-Observation-Case-Context-Implementation-Design.md` (commit `8861ffa`). **Implementation paths inspected**: `atlas/core/domain/decision/{entity,value_objects,exceptions,repository}.py`; `atlas/core/application/decision/capture_decision.py`; `atlas/core/infrastructure/persistence/decision/{table,sqlalchemy_repository}.py`; `atlas/core/infrastructure/api/decision/{router,schemas,dependencies,errors}.py`; `atlas/core/application/reasoning_link/commit_decision_from_conclusion.py`; `atlas/core/application/conversation/orchestrator.py` (`_handle_decision`); `atlas/core/infrastructure/api/app.py` (confirms the Decision router is mounted). **Tests inspected**: every file listed in Section 5, Gap G1/G2/G3 below, read for its exact fixture and assertion shape.

## 3. Current Architecture

**Domain**: `atlas/core/domain/decision/entity.py` — `Decision(id: DecisionId, user_id: UserId, decision_type: DecisionType, subject: Subject, investment_case: InvestmentCase, confidence: Confidence, decided_at: datetime, recorded_at: datetime, source: DecisionSource = MANUAL)`, `@dataclass(frozen=True)`, `Decision.register(*, user_id, decision_type, subject, investment_case, confidence, decided_at=None, source=MANUAL, clock=_utc_now)`. No `case_id` anywhere.

**Application**: `atlas/core/application/decision/capture_decision.py` — `CaptureDecisionRequest(user_id, decision_type, subject, reason, confidence, decided_at=None, source="Manual")`; `CaptureDecisionService(repository: DecisionRepository)` — one dependency, `.capture()` translates the request into `Decision.register(...)` and calls `repository.add()`. No `CaseRepository` anywhere — matches the already-established Observation pattern exactly.

**Composite (Core Loop)**: `atlas/core/application/reasoning_link/commit_decision_from_conclusion.py` — `CommitDecisionFromConclusionRequest(conclusion_id, user_id, decision_type, subject, reason, confidence, decided_at=None, source=MANUAL)`; `CommitDecisionFromConclusionService(conclusion_repository, decision_service, link_repository)` — verifies the Conclusion exists, delegates to `CaptureDecisionService`, records a `ConclusionDecisionLink`. No `case_id` anywhere.

**Orchestrator**: `ConversationOrchestrator._handle_decision` (`orchestrator.py`) already has `session.case_id` available (added by Package R2) but does not yet pass it into `CommitDecisionFromConclusionRequest(...)`.

**Persistence**: `atlas/core/infrastructure/persistence/decision/table.py` — `decisions_table(id, user_id, decision_type, subject, reason, confidence, decided_at, recorded_at, source)`, no `case_id` column. `sqlalchemy_repository.py` — `add`/`get`/`list_all`, insert-only.

**API**: `atlas/core/infrastructure/api/decision/router.py` — `POST /decisions`, `GET /decisions`, `GET /decisions/{id}`, mounted in `atlas/core/infrastructure/api/app.py` (confirmed a real, live, currently-tested surface, not dead code). `schemas.py` — `CreateDecisionRequest`/`DecisionSummary`/`DecisionCreatedResponse` (camelCase via `CamelModel`, per ADR-004), no `case_id` field.

**Downstream consumers** (read-only, via `DecisionRepository.list_all()`/`.get()`, or via direct `Decision.register()` fixture construction): `decision_review`, `decision_reflection`, `decision_coach`, `decision_timeline`, `decision_context`, `pattern_recognition`, `strategy_signature`, `outcome`, and the `reflection_*` family (`reflection_comparison`, `reflection_exploration`, `reflection_history`, `reflection_understanding_formation`, `reflection_response`). None of these packages' own production code constructs a `Decision`; several of their **tests** do, directly (Section 5, Gap G3).

## 4. Accepted Decision Semantics

**Settled** (OE-002 §5.5, quoted in `Decision-Implementation-Design.md` Section 5): Decision is a permanent, independently-identified, Case-owned Domain Object recording the Case's settled practical commitment regarding what is to be done — a **commitment**, not an act, a recorded result, a selected alternative, an intention, an instruction, or a conclusion in the OE-002 sense. It does **not** assert: execution ("without itself executing behaviour"); that it requires an Agent; that multiple alternatives were considered; that any referenced matter is true, correct, or will be carried out; finality in the sense of exclusivity or irrevocability (a later, contrary Decision does not invalidate an earlier one — both remain permanent). Decision belongs to exactly one Case (INV-002), assigned independently, never derived from any referenced object, immutable once accepted. Its identity (`DecisionId`) is independent of its content and of any object it references (OE-002 §5.5 Identity clause). Root-eligibility is conditional on which committed-to-matter form is used (INV-012) — moot today since no referential form exists in code.

**Upstream relations** (task item 3): the approved design permits Decision's committed-to matter to be internal content or a typed reference to **any of the six adopted Domain Objects** (Observation, Knowledge Reference, Reasoning Trace, Judgment, Decision, Outcome) — never Interpretation, Hypothesis, Evidence, or Conclusion, none of which is a Domain Object under OE-002 §4's closed set. **This referential form does not exist in the current codebase at all** — no `matter_target_type`/`matter_target_id` field exists on `Decision` today. Decision's only connection to the legacy Core Loop is the external `ConclusionDecisionLink` bridge (`reasoning_link` module), which is explicitly provisional and not part of Decision's own domain model. Cardinality/ordering/duplicate/self-reference/cycle questions are therefore **not yet applicable** — there is nothing to constrain until the reference field itself is introduced, which this design does not do (Gap G2).

**Open, not settled by this design** (task item 1, explicitly not resolved here): whether `decision_type`, `confidence`, `subject`, `source` are permissible internal-content structure or unadopted extra semantics (`Decision-Implementation-Design.md` Section 39, Q2 — already flagged there as open, not re-derived here); whether both committed-to-matter forms may ever coexist (Q1, immaterial today since neither form is implemented as such); `user_id`'s ultimate disposition, already resolved to "retained temporarily as compatibility-only metadata, must not participate in accepted content going forward" per that same document's Section 38, citing an "Investor Identity and Accepted-State Permanence Resolution" that — like "Case Representation Strategy" — does not exist as a file in this repository (a historical inconsistency, not a new one; already logged in `Core-Loop-Case-Context-Reconciliation-Investigation.md` Section 40).

**Explicit non-substitution.** `case_id` originates from exactly one place: the already-resolved `ConversationSession.case_id` for the Core Loop path (established by Package R2's `resolve_new_case`/`resolve_existing_case`), or the API caller's own supplied value for the standalone REST path. Neither `session_id`, `investor_id`, nor `user_id` is ever reused, cast, converted, or interpreted as `case_id` anywhere in this design — each remains the distinct identifier it already was, exactly as established in `Core-Loop-Case-Context-Reconciliation-Investigation.md` and reaffirmed, not reopened, here.

## 5. Gap Analysis

**G1 — Missing Case ownership (in scope).** Observed: `Decision` has no `case_id` anywhere (domain, application, persistence, API). Expected: INV-002 requires exactly one Case per Domain Object, unconditionally. Evidence: `entity.py`, `capture_decision.py`, `table.py`, `schemas.py` (Section 3). Classification: missing Case propagation / domain-application-persistence-interface gap. Impact: Decision, a Final-adopted Domain Object, is not architecturally compliant. **In scope.**

**G2 — Field-set reconciliation with the approved minimal Decision shape (out of scope).** Observed: the current entity's content fields (`user_id`, `decision_type`, `subject`, `investment_case`, `confidence`, `source`) do not correspond to the approved design's minimal fields (`commitment_content` and/or `matter_target_type`/`matter_target_id`). Expected: `Decision-Implementation-Design.md` itself defers this reconciliation to a future, separately-scoped migration effort and explicitly states "reconcile the existing... implementation with this minimal design only as part of that same future migration effort, not as part of this document" (Section 41). Evidence: Section 30 (minimal fields table omits every current content field except by inference), Section 38 (existing-code impact, "plausibly corresponds... not independently re-derived or finalized"), Section 39 Q2. Classification: ontology/design conflict, pre-existing, already disclosed by the governing design itself. Impact: real, but not created or worsened by adding `case_id`. **Out of scope** — reported, not resolved, per this task's own stop-condition instruction ("changes would require unrelated ontology or architecture work").

**G3 — Nine unrelated test files construct `Decision.register(...)` directly (in scope, as mechanical fixture corrections only).** Observed: `tests/unit/application/{reflection_understanding_formation,reflection_comparison,outcome,reflection_exploration,decision_context}/test_*.py`, `tests/unit/application/reflection_history/test_composition.py`, `tests/unit/infrastructure/persistence/reflection_response/test_list_all_for_owner.py`, `tests/unit/infrastructure/api/decision_context/test_router.py` each call `Decision.register(...)` directly as their own seed/fixture data, bypassing `CaptureDecisionService`. Expected: once `case_id` becomes a required, no-default field, every one of these calls raises `TypeError`, mirroring exactly what DO-IMP-006 caused for `test_capture_interpretation.py` (already corrected in commit `b41f0ff`). Evidence: `grep -rn "Decision\.register(" tests/`. Classification: mechanical, disclosed, unavoidable consequence of G1 — not a defect in this design, not scope creep, not a reason to make `case_id` optional. Impact: nine one-line fixture edits, zero behavioral change to those packages' own functionality. **In scope, as fixture corrections only** — no production or assertion change in any of these packages.

**G4 — No dedicated application-layer test for `CaptureDecisionService` (pre-existing, non-blocking).** Observed: no `tests/unit/application/decision/` directory exists at all; `CaptureDecisionService` is exercised only indirectly, through `CommitDecisionFromConclusionService` and the nine downstream consumers in G3. Expected: every other capture service in this codebase (Observation, Hypothesis, Evidence, Question, Interpretation) has its own direct application-layer test file. Evidence: `find tests -path "*decision*"` returns no such directory; confirmed by directory listing. Classification: pre-existing, unrelated test-coverage gap (task item 7) — not caused by this design. Impact: non-blocking; addressed minimally in Section 8 (a new, narrowly-scoped test file proving only the `case_id` behavior this package adds, not a general audit of the service).

**G5 — `CommitDecisionFromConclusionRequest`/`_handle_decision` lack `case_id` (in scope).** Observed: the Core Loop's own Decision-producing composite service and its sole orchestrator caller do not propagate `session.case_id`. Expected: `Core-Loop-Case-Context-Reconciliation-Investigation.md` Section 23 and `Core-Loop-Observation-Case-Context-Implementation-Design.md` Section 24 already specify this exact one-line propagation as the anticipated next step. Evidence: `orchestrator.py` `_handle_decision`; `commit_decision_from_conclusion.py`. Classification: missing Case propagation. Impact: once G1 lands, every call through this path breaks identically to how `ObserveFromQuestionService` broke before Package R2 — must land in the same commit as G1 to avoid reintroducing a disclosed-but-broken state. **In scope.**

**G6 — Decision REST API lacks `case_id` (in scope).** Observed: `CreateDecisionRequest`/`DecisionSummary` have no `case_id` field; the router constructs `CaptureDecisionRequest(...)` without one. Expected: mirrors Observation's own API update in DO-IMP-006 exactly — a real, live, mounted, currently-tested API surface, not a compatibility shim. Evidence: `app.py` mounts the router; `test_router.py` exercises it end-to-end today. Classification: missing serialization field. Impact: without this change, the API breaks identically to every other consumer once G1 lands. **In scope.**

## 6. Selected Implementation

**Production files:**

1. `atlas/core/domain/decision/entity.py` — add `case_id: CaseId` as a required field on `Decision` (positioned immediately after `id`, mirroring `Observation`'s own field order), import `CaseId` from `atlas.core.domain.case.value_objects`; add `case_id: CaseId` as `Decision.register`'s first keyword-only parameter, passed straight through with no re-validation. *Why here*: this is Decision's own aggregate boundary; Case ownership is intrinsic to the entity, exactly as it is for Observation.

2. `atlas/core/application/decision/capture_decision.py` — add `case_id: uuid.UUID` as `CaptureDecisionRequest`'s first, required field; `CaptureDecisionService.capture()` passes `case_id=CaseId(request.case_id)` into `Decision.register(...)`. No `CaseRepository` dependency added — `CaptureDecisionService.__init__` remains exactly one parameter. *Why here*: the one place raw input is translated into the aggregate; mirrors `CaptureObservationService` exactly.

3. `atlas/core/infrastructure/persistence/decision/table.py` — add `Column("case_id", String, nullable=False, index=True)` immediately after `id`; no foreign key, no server default. *Why here*: schema must persist the new required field.

4. `atlas/core/infrastructure/persistence/decision/sqlalchemy_repository.py` — `_to_row` gains `"case_id": str(decision.case_id)`; `_to_decision` gains `case_id=CaseId(uuid.UUID(row["case_id"]))`, read unconditionally (no fallback), fails loudly on a genuinely missing legacy row — identical discipline to Observation's own repository correction.

5. `atlas/core/infrastructure/api/decision/schemas.py` — `CreateDecisionRequest`/`DecisionSummary` gain `case_id: uuid.UUID` (serializes as `caseId` via `CamelModel`); `DecisionSummary.from_domain` gains `case_id=decision.case_id.value`.

6. `atlas/core/infrastructure/api/decision/router.py` — `create_decision` gains `case_id=payload.case_id` inside its existing `CaptureDecisionRequest(...)` construction. No other route changes.

7. `atlas/core/application/reasoning_link/commit_decision_from_conclusion.py` — `CommitDecisionFromConclusionRequest` gains `case_id: uuid.UUID` as its first field; `.commit()` passes `case_id=request.case_id` into `CaptureDecisionRequest(...)`. No `CaseRepository` added to `CommitDecisionFromConclusionService`.

8. `atlas/core/application/conversation/orchestrator.py` — `_handle_decision`'s `CommitDecisionFromConclusionRequest(...)` construction gains `case_id=session.case_id` as its first keyword argument. No other line in this file changes.

**No change** to `Case`, `CaseService`, `CaseRepository`, `composition.py`'s `resolve_new_case`/`resolve_existing_case`, or `cli.py` — the Case-context resolution and propagation mechanism is already complete (Package R2); this package only extends the already-designed relay one step further, exactly as anticipated. **No change** to Question, Interpretation, Hypothesis, Evidence, Conclusion, Evaluation, Learning, or any `reasoning_link` bridge entity — none is a Domain Object under OE-002 §4's closed set, none gains `case_id` anywhere in this package.

## 7. Rejected Alternatives

- **Inferring Case from the Conclusion the Decision is committed from.** Rejected: Conclusion is not a Domain Object (OE-002 §4's closed set excludes it) and carries no `case_id` of its own to infer from; this would also violate the already-established "no hidden Case creation/inference" binding fact.
- **Allowing mixed-Case inputs and validating later.** Rejected: `case_id` arrives as a single, already-resolved value from `ConversationSession`/the API caller; there is no second Case-bearing input to mix with, and introducing a later validation step would duplicate the existence check outside its one authorized boundary.
- **Duplicating Case validation in the entity and the application service.** Rejected: mirrors Observation's own settled discipline — the entity performs only structural (non-None, correct-type) validation via its dataclass field; existence validation of the Case itself happens once, only at the conversation/API resolution boundary, never inside `CaptureDecisionService` or `Decision` itself.
- **Introducing a generic Decision dependency resolver for `matter_target_type`/`matter_target_id`.** Rejected: no referential form exists in code today (Section 4); inventing a resolver for a field that does not exist would be pure speculation, unsupported by any current requirement.
- **Making `case_id` optional.** Rejected outright, per explicit task instruction and INV-002; also inconsistent with `CaptureObservationRequest.case_id`'s own already-settled required-no-default precedent.
- **Modifying `decision_context`, `pattern_recognition`, `outcome`, or any `reflection_*` package's own production code to accommodate the new `case_id` requirement.** Rejected: none of their production code constructs a `Decision`; only their test fixtures do, and only those fixtures are touched (Section 6, Gap G3), never their own logic.
- **Introducing `commitment_content`/`matter_target_type` now, or resolving `decision_type`/`confidence`/`subject`/`user_id`'s ultimate status.** Rejected: this is Gap G2, explicitly out of scope, already deferred by the governing design itself to an undefined future effort; resolving it here would be an unrelated, much larger architecture change smuggled into a Case-integration package.
- **Broad migration of `decision_context`, `outcome`, or any other adjacent package to add their own `case_id`.** Rejected: each is a separate, future, independently-scoped integration question (mirroring how Outcome's own Case-integration was already identified, in `Core-Loop-Case-Context-Reconciliation-Investigation.md`, as Package R4 — a distinct package, not this one).

## 8. Test Design

**Existing tests to update, own Decision suite:**
- `tests/unit/domain/decision/test_entity.py` — add a module-level `_CASE_ID = CaseId()` constant (mirroring the established pattern); add `case_id=_CASE_ID` to every `Decision.register(...)` call; add `test_requires_a_case_id`; add a `TestCaseOwnership` class (two Decisions in the same Case remain distinct; Decisions in different Cases are independent) — mirrors `test_entity.py` for Observation exactly.
- `tests/unit/infrastructure/persistence/decision/test_sqlalchemy_repository.py` — `_new_decision()` helper gains `case_id=CaseId()` default; `TestEqualsOriginal` (or equivalent) asserts `case_id` round-trips; add `case_id`-not-null enforcement test if this file follows the Observation persistence test's `IntegrityError` pattern.
- `tests/unit/infrastructure/api/decision/test_router.py` — `_valid_payload()` gains `"caseId": str(uuid.uuid4())` default; add `test_rejects_missing_case_id`/`test_rejects_malformed_case_id` (422), mirroring Observation's router test additions.
- `tests/unit/application/reasoning_link/test_commit_decision_from_conclusion.py` — add `case_id=uuid.uuid4()` to the request construction; add a propagation test asserting `result.decision.case_id.value == request.case_id`.
- `tests/unit/application/reasoning_link/test_core_loop_end_to_end.py` — add `case_id=uuid.uuid4()` to its `CommitDecisionFromConclusionRequest(...)` call (already updated once for Observation's own request in Package R2; this is the analogous, second required edit in the same file).

**Existing tests to update, conversation suite (propagation confirmation only, no new fixtures needed since `session.case_id` already exists from Package R2):**
- `tests/unit/application/conversation/test_conversation_end_to_end.py` — add one assertion, `assert decision.case_id.value == resolved_case_id`, alongside the existing Observation assertion added in Package R2.

**New test file (addresses Gap G4 minimally, scoped to `case_id` only):**
- `tests/unit/application/decision/test_capture_decision.py` — proves: `case_id` is required (`TypeError` if omitted); the same `case_id` supplied in the request is the one persisted; `CaptureDecisionService.__init__` depends on exactly one repository (no `CaseRepository`). Does not attempt to backfill general coverage for `decision_type`/`confidence`/`subject` — out of scope (Gap G2).

**Fixture-only corrections (Gap G3, one line each, no assertion or behavior change):**
`tests/unit/application/reflection_understanding_formation/test_cli.py`, `tests/unit/application/reflection_comparison/test_cli.py`, `tests/unit/application/outcome/test_capture_outcome.py`, `tests/unit/application/reflection_exploration/test_cli.py` (two call sites), `tests/unit/application/decision_context/test_capture_decision_context.py`, `tests/unit/application/reflection_history/test_composition.py`, `tests/unit/infrastructure/persistence/reflection_response/test_list_all_for_owner.py`, `tests/unit/infrastructure/api/decision_context/test_router.py` — each `Decision.register(...)` call gains a `case_id=` argument (a fresh `uuid.uuid4()`/`CaseId()`, following whichever convention that specific file already uses elsewhere), and nothing else in any of these files changes.

**Narrow test commands:**
```
.venv/bin/python -m pytest -q tests/unit/domain/decision tests/unit/application/decision \
  tests/unit/infrastructure/persistence/decision tests/unit/infrastructure/api/decision \
  tests/unit/application/reasoning_link/test_commit_decision_from_conclusion.py \
  tests/unit/application/reasoning_link/test_core_loop_end_to_end.py
```

**Adjacent regression commands:**
```
.venv/bin/python -m pytest -q tests/unit/application/conversation tests/unit/application/decision_review \
  tests/unit/application/decision_reflection tests/unit/application/decision_timeline \
  tests/unit/application/decision_context tests/unit/application/pattern_recognition \
  tests/unit/application/strategy_signature tests/unit/application/outcome \
  tests/unit/application/reflection_comparison tests/unit/application/reflection_exploration \
  tests/unit/application/reflection_history tests/unit/application/reflection_understanding_formation \
  tests/unit/infrastructure/persistence/reflection_response tests/unit/infrastructure/api/decision_context
```

**Final full-suite command:** `.venv/bin/python -m pytest`.

## 9. Implementation Sequence

1. `atlas/core/domain/decision/entity.py` (add `case_id`).
2. `atlas/core/application/decision/capture_decision.py` (relay).
3. `atlas/core/infrastructure/persistence/decision/table.py` + `sqlalchemy_repository.py` (persist).
4. `atlas/core/infrastructure/api/decision/schemas.py` + `router.py` (serialize).
5. `atlas/core/application/reasoning_link/commit_decision_from_conclusion.py` (composite relay).
6. `atlas/core/application/conversation/orchestrator.py` (`_handle_decision` relay) — must land in the same change as step 5, never separately, to avoid a disclosed-but-broken intermediate state.
7. Own-suite test updates (Section 8, first two groups).
8. New `test_capture_decision.py`.
9. Nine fixture-only corrections (Gap G3).
10. Full-suite verification.

## 10. Verification and Acceptance Criteria

- Narrow Decision tests (Section 8 command 1) green.
- Adjacent regression command green.
- Full suite green: exact pass count will be baseline (8080) plus new tests added in steps 7–8 (own-suite additions: `test_requires_a_case_id`, `TestCaseOwnership` ×2, router `caseId` tests ×2, propagation test ×1, new `test_capture_decision.py` file ×3 tests, conversation-end-to-end assertion is not a new test) minus zero (no test removed), skipped count unchanged at 3, failures and errors at 0.
- `.venv/bin/ruff check` clean on every changed file.
- No file outside Section 11's list changed.
- Clean working tree after commit; nothing staged; no push.

## 11. Expected File Set

**Production (8):** `atlas/core/domain/decision/entity.py`; `atlas/core/application/decision/capture_decision.py`; `atlas/core/infrastructure/persistence/decision/table.py`; `atlas/core/infrastructure/persistence/decision/sqlalchemy_repository.py`; `atlas/core/infrastructure/api/decision/schemas.py`; `atlas/core/infrastructure/api/decision/router.py`; `atlas/core/application/reasoning_link/commit_decision_from_conclusion.py`; `atlas/core/application/conversation/orchestrator.py`.

**Tests, own-suite (5 modified + 1 new):** `tests/unit/domain/decision/test_entity.py`; `tests/unit/infrastructure/persistence/decision/test_sqlalchemy_repository.py`; `tests/unit/infrastructure/api/decision/test_router.py`; `tests/unit/application/reasoning_link/test_commit_decision_from_conclusion.py`; `tests/unit/application/reasoning_link/test_core_loop_end_to_end.py`; new `tests/unit/application/decision/test_capture_decision.py`.

**Tests, conversation (1 modified):** `tests/unit/application/conversation/test_conversation_end_to_end.py`.

**Tests, fixture-only (9 modified):** `tests/unit/application/reflection_understanding_formation/test_cli.py`; `tests/unit/application/reflection_comparison/test_cli.py`; `tests/unit/application/outcome/test_capture_outcome.py`; `tests/unit/application/reflection_exploration/test_cli.py`; `tests/unit/application/decision_context/test_capture_decision_context.py`; `tests/unit/application/reflection_history/test_composition.py`; `tests/unit/infrastructure/persistence/reflection_response/test_list_all_for_owner.py`; `tests/unit/infrastructure/api/decision_context/test_router.py`.

**Documentation:** none.

## 12. Commit Plan

One atomic commit. Recommended message: `Implement Decision Case Ownership` (mirroring the naming convention of commit `d1fb901`, "Implement Observation Case Ownership"). No commit is made during this design task.

## 13. Stop Conditions

**Checked, do not apply to the in-scope `case_id` addition**: no governing-document conflict blocks it (INV-002 is unconditional and settled); Decision's Case-ownership semantics are fully settled (OE-002 §5.5, §3.1); the required upstream acceptance behavior for a Case reference is defined (INV-004/005, already implemented identically for Observation); narrow tests are not already green with no gap — the gap is real and confirmed by direct inspection (Section 5, G1); the architecture does not contradict this specific integration — it already anticipates it (`Core-Loop-Case-Context-Reconciliation-Investigation.md` Section 23, `Core-Loop-Observation-Case-Context-Implementation-Design.md` Section 24).

**Applies, and this design deliberately stops here**: Gap G2 (field-set reconciliation against the approved minimal Decision shape) is exactly the case where "governing documents... leave semantics not sufficiently settled" and "changes would require unrelated ontology or architecture work" — this design does not touch it, invents no resolution, and reports it as a required, separately-scoped future investigation (analogous in kind to how Package R1 preceded Package R2 for Observation).

## 14. Permission or Prohibition for Implementation

**No implementation may begin from this document.** This document is itself design-only and is not self-authorizing: producing or committing it does not constitute approval to modify any production or test file listed in Sections 6, 8, or 11. The next authorized step is a separate, explicitly-approved implementation package (recommended commit per Section 12), reviewed on its own terms before any code changes.

## Baseline Execution Record

`git status --short`: clean. HEAD: `b41f0ffc22f11aab3439bbf2441ea38d48f658be`. Narrow Decision test selection (`tests/unit/domain/decision`, `tests/unit/infrastructure/persistence/decision`, `tests/unit/infrastructure/api/decision`, `tests/unit/application/reasoning_link/test_commit_decision_from_conclusion.py`, `tests/unit/application/reasoning_link/test_core_loop_end_to_end.py`): **90 passed, 0 failed, 0 errors** — Decision's current, case_id-less implementation is internally consistent and fully green today; the gap is one of absence (INV-002 non-compliance), not of any failing behavior. Adjacent regression selection (`decision_review`, `decision_reflection`, `decision_timeline`, `pattern_recognition`, `strategy_signature`, `outcome`, `conversation`): **106 passed, 0 failed, 0 errors**. No failure required classification, since none occurred; the gap was established by direct code inspection (absence of `case_id`), not by a failing test.

## Next Genuine Integration Boundary

After this package (and independently of Gap G2's future resolution), the next unintegrated boundary per `Core-Loop-Case-Context-Reconciliation-Investigation.md`'s own sequencing is **Outcome** (Package R4 — approved design exists, `Decision-Implementation-Design.md`'s sibling `Outcome-Implementation-Design.md` already reviewed, but Outcome has no current Core Loop integration to break, since `OutcomeService` is not wired into any orchestrator), followed by **Reasoning Trace** (Package R5 — approved design, zero existing code).
