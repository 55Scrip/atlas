# Core Loop Observation Case Context — Implementation Design

## 2. Status

Implementation-design artifact, not a normative document. Carries no Doctrine status (Draft/Final/Superseded/Historical) because those statuses apply to normative documents, and this is not one. Where anything here appears to conflict with the Architecture Doctrine, OE-002 through OE-006, the Historical Decision Record, or the committed Core-Loop-Case-Context-Reconciliation-Investigation, those documents govern and this one is wrong and must be corrected.

## 3. Package Identifier

Package R2 — ObserveFromQuestionService Case Integration Design, per `Core-Loop-Case-Context-Reconciliation-Investigation.md` Sections 33–34. Design only. No code, test, or existing document is modified by this package.

## 4. Executive Finding

The smallest semantically complete design threads a single, already-resolved `CaseId` from one explicit CLI-level choice — "start a new investigation" or "continue an existing one by id" — through exactly four points: a new `build_conversation_orchestrator(engine, case_id)` parameter, a new `ConversationOrchestrator.__init__` field (mirroring the already-accepted `investor_id` pattern exactly), a new required `ConversationSession.case_id` field (mirroring `DecisionReviewSession.decision_id`'s already-accepted, already-tested "externally resolved, required, no default" shape), and a new required `ObserveFromQuestionRequest.case_id` field relayed unchanged into the already-approved `CaptureObservationRequest.case_id`. Case resolution itself uses only the existing, unmodified `CaseService.create()`/`.get()` — no new Case field, no new persistence, no enumeration capability is required, because Case's own minimal shape (`id`, `recorded_at` only) makes direct CaseId entry sufficient and makes a list-and-select UX add no real value it would not already have from typing the id back in. Two closely analogous, already-accepted precedents exist in this exact codebase for every non-trivial part of this design — `investor_id`'s resolve-once-outside-the-orchestrator pattern and `DecisionReviewSession.decision_id`'s externally-resolved-required-field pattern — so nothing here is invented from scratch.

## 5. Selected Outcome

**Outcome 1 — Deterministic implementation design complete.** The explicit new-or-existing Case contract, Case creation authority, existing-Case validation authority, `ConversationSession` propagation, and `ObserveFromQuestionService` propagation are each fully determined below, with exact file changes and exact tests specified, and no decision is left blocking a subsequent implementation package. Not Outcome 2: no further public-entry contract decision remains open — Section 19 selects one contract, precisely. Not Outcome 3: Section 8's inspection confirms Case creation requires no data the conversation boundary cannot supply (it requires none at all). Not Outcome 4: no restructuring of the orchestrator's step sequence or Observation's own construction semantics is required. Not Outcome 5: no further unresolved authority question blocks this design — the one authority question the reconciliation investigation left open (the exact public contract) is resolved here.

## 6. Scope

This design determines the exact code shape required to supply a genuine `CaseId` to `ObserveFromQuestionService` through the existing legacy Core Loop, consistent with the create-or-continue model already selected and committed in `Core-Loop-Case-Context-Reconciliation-Investigation.md` Section 19. It resolves the Observation integration boundary only.

## 7. Explicit Exclusions

Does not implement anything — design only. Does not begin Decision integration (`CommitDecisionFromConclusionService`/`CommitDecisionFromConclusionRequest`) — explicitly out of scope per the governing task and per the reconciliation investigation's own Package R3. Does not begin Outcome integration — out of scope per Package R4; no current integration exists to fix. Does not begin Reasoning Trace, Knowledge Reference, or Judgment work — unaffected by this design. Does not add `case_id` to Question, Interpretation, Hypothesis, Evidence, Conclusion, Evaluation, Learning, or any `reasoning_link` bridge entity — each remains a non-Domain-Object under OE-002 §4's closed set, per the reconciliation investigation's own Section 8. Does not reopen Observation's own approved entity, request, service, persistence, or API shape (commit `d1fb901`) — Observation's construction semantics (`Observation.capture(case_id=..., subject=..., statement=..., observed_at=..., source=..., note=...)`) are treated as fixed, correct input this design must reach, never redesigned. Does not add a Case title, purpose, subject, status, or investor-ownership field — Case's own entity remains exactly `id`, `recorded_at`. Does not stage, commit, tag, or push anything.

## 8. Governing Sources

**Authoritative**: Architecture Doctrine; OE-002 §3.1, §4 (Case's ownership-boundary role; the closed six-member Domain Object Set); OE-004 INV-002/003/004/005/006. **Binding, already-committed**: `Core-Loop-Case-Context-Reconciliation-Investigation.md` (commit `a4e9c42`) — every one of its twelve binding facts and its Section 19 selected model are treated here as fixed inputs, not reopened; `Observation-Implementation-Design.md`, `Observation-Implementation-Integration-Blocker-Resolution.md`, `Observation-Implementation-Pre-Commit-Review.md` (commits `8585089`, `ccb9426`, `1d9e896`) — Observation's own approved shape, cited, not re-derived. **Existing code inspected fresh for this design**: `atlas/core/domain/case/{entity,value_objects,repository,exceptions}.py`; `atlas/core/application/case/create_case.py`; `atlas/core/infrastructure/persistence/case/{table,sqlalchemy_repository}.py`; `atlas/core/infrastructure/api/case/{router,dependencies,schemas}.py`; `atlas/core/domain/observation/entity.py`; `atlas/core/application/observation/capture_observation.py`; `atlas/core/application/reasoning_link/observe_from_question.py`; `atlas/core/application/conversation/{session,orchestrator,composition,cli}.py`; `atlas/core/application/decision_review/{session,orchestrator,lookup}.py` (inspected specifically for precedent); `tests/unit/application/conversation/test_orchestrator.py`.

## 9. Repository State Inspected

`git status --short` was clean at task start; branch `main`; HEAD `a4e9c42ca44a85e898e25cd6dcb464b9040e965a`, whose history includes both `d1fb901` (Implement Observation Case Ownership) and `a4e9c42` (Investigate Core Loop Case Context) as required. `Case` has exactly two fields (`id: CaseId`, `recorded_at: datetime`); `CaseService` has exactly `create()` (zero arguments beyond an injectable clock) and `get(case_id) -> Case`, raising `CaseNotFoundError` if absent; `CaseRepository` has exactly `add`/`get`, deliberately no `list_all` ("nothing within DO-IMP-001's approved scope needs to enumerate every Case yet"). `Observation` already has `case_id: CaseId` as a required field (DO-IMP-006, `d1fb901`); `CaptureObservationRequest` already has `case_id: uuid.UUID` as its first, required field. `ObserveFromQuestionRequest` (`observe_from_question.py`) has no `case_id` field. `ConversationSession` (`session.py`) has `session_id`, `current_step`, seven step-result ids, two carried-forward values, and `pending` — no `case_id`. `ConversationOrchestrator.__init__` (`orchestrator.py`) takes exactly the seven step services plus `investor_id: UserId`; `start()` takes zero arguments and returns a bare `ConversationSession()`; `_handle_observation` constructs `ObserveFromQuestionRequest(question_id=..., subject=..., statement=..., observed_at=...)` with no `case_id`. `build_conversation_orchestrator(engine)` (`composition.py`) resolves `investor_id = resolve_investor_identity(engine)` once and passes it into the orchestrator's constructor — the exact precedent this design reuses for `case_id`. `DecisionReviewSession` (`decision_review/session.py`) has `decision_id: uuid.UUID` as a required, no-default field, populated by `DecisionReviewOrchestrator.select()` after looking the Decision up via `DecisionRepository` and returning `None` on no match — the exact precedent this design reuses for Case continuation's not-found behavior. `DecisionRepository.list_all()` backs `list_decisions_for_selection()`/`select_decision()` in `decision_review/lookup.py` — inspected and found inapplicable to Case (Section 17) because Case has no displayable content beyond its own id.

## 10. Binding Decisions Inherited from Reconciliation

From `Core-Loop-Case-Context-Reconciliation-Investigation.md`, treated as fixed, not reopened: (1) OE-002's six-member closed Domain Object Set and INV-002's scope to it (Sections 6, 8 there). (2) The selected model — explicit new-or-continue choice, made once per conversation, propagated as plain data (Section 19 there). (3) `CaptureObservationService`/`CaptureObservationRequest` must not gain a `CaseRepository` dependency and must not fabricate or repair Case context (Section 20 there). (4) `ConversationOrchestrator` gains no new constructor dependency on `CaseService`/`CaseRepository` — Case resolution happens at the composition/CLI layer, before the orchestrator is built, and the orchestrator receives only an already-resolved value (Section 25 there — this is Candidate D from that document, already selected, not re-decided here). (5) Package R2 is design-only (Section 33/43 there, corrected).

## 11. Current Integration Failure

`ObserveFromQuestionService.observe()` constructs `CaptureObservationRequest(subject=..., statement=..., observed_at=..., source=..., note=...)` with no `case_id` — `CaptureObservationRequest.__init__()` raises `TypeError` on every call, since `case_id` is a required field with no default. `ConversationOrchestrator._handle_observation` wraps this in a bare `try/except Exception:`, so the failure manifests in the full suite as 22 assertion failures/timeouts and 4 errors in conversation-level tests, not a visible crash.

## 12. Current Core Loop Path

`atlas/core/application/conversation/cli.py:run()` → `build_conversation_orchestrator(engine)` (`composition.py`) → `ConversationOrchestrator.start()` returns `ConversationSession()` → CLI loop calls `orchestrator.respond(session, answer)` → `_handle_question` → `_handle_observation` constructs `ObserveFromQuestionRequest(...)` → `ObserveFromQuestionService.observe()` constructs `CaptureObservationRequest(...)` → `CaptureObservationService.capture()` constructs `Observation.capture(case_id=..., ...)`. This design modifies exactly the six points on this path listed in Section 4; every other point on the path (`_handle_question` onward past observation, `InterpretationService`, and beyond) is unaffected.

## 13. Current Case Implementation

`atlas/core/domain/case/entity.py`: `Case(id: CaseId, recorded_at: datetime)`, `Case.create(*, clock=_utc_now)` — zero semantic input. `atlas/core/domain/case/value_objects.py`: `CaseId(value: uuid.UUID = field(default_factory=uuid.uuid4))`. `atlas/core/domain/case/repository.py`: `CaseRepository` Protocol with `add`/`get` only. `atlas/core/domain/case/exceptions.py`: `CaseError`, `CaseNotFoundError` (no `CaseValidationError` — Case has no field that can ever fail validation). `atlas/core/application/case/create_case.py`: `CaseService(repository)`, `.create() -> Case`, `.get(case_id) -> Case` raising `CaseNotFoundError`. `atlas/core/infrastructure/persistence/case/table.py`: `cases_table(case_id PK, recorded_at)`, no foreign keys, own `MetaData`. `atlas/core/infrastructure/persistence/case/sqlalchemy_repository.py`: `add`/`get` only, insert-only. `atlas/core/infrastructure/api/case/{router,dependencies,schemas}.py`: `POST /cases` (no body), `GET /cases/{id}`; no list route.

## 14. Current ConversationSession Model

`session_id: uuid.UUID` (default-generated, in-memory correlation only, never `CaseId`); `current_step`; seven step-result ids; `observation_subject`/`conclusion_statement` (carried-forward answers); `pending: dict`. Not persisted, mutable, exempt from the immutability convention, per its own module docstring, which additionally states: "a First Decision Conversation is a single sitting, and is not designed to be resumed after a gap" — meaning a `ConversationSession` itself is never resumed; only a Case may be continued, via a brand-new `ConversationSession` in a brand-new sitting. This is independent confirmation, from the codebase's own stated design intent, that the reconciliation investigation's selected model (continuation happens at the Case level, not the session level) is already consistent with how this codebase understands "a sitting" — no contradiction was found, and this finding strengthens Outcome 1 rather than raising a new question.

## 15. Current ObserveFromQuestionService Model

`ObserveFromQuestionRequest(question_id, subject, statement, observed_at, source=None, note=None)`; `ObserveFromQuestionService(question_repository, observation_service, link_repository)`; `.observe()` verifies the Question exists (`QuestionNotFoundError` if not), delegates to `CaptureObservationService.capture()`, records a `QuestionObservationLink`. No `case_id` anywhere in this service or its request today.

## 16. Current CaptureObservationService Model

`CaptureObservationRequest(case_id: uuid.UUID, subject, statement, observed_at, source=None, note=None)` — `case_id` already required, first field, no default (DO-IMP-006). `CaptureObservationService(repository)` — exactly one dependency, no `CaseRepository`. `.capture()` calls `Observation.capture(case_id=CaseId(request.case_id), ...)` with no existence check against `CaseRepository` — Case existence is never verified at this layer, by design (binding fact 15/inherited decision 3, Section 10 above). This design's own propagation must reach exactly this already-fixed shape; nothing here changes.

## 17. Candidate Public Case-Context Contracts

**A — two separate public operations** (e.g., "start with a new Case" / "start with an existing CaseId"). Directly mirrors `DecisionReviewOrchestrator`'s own `list_decisions()`/`select()` two-operation shape. Explicit; no ambiguous state possible; no hidden-creation risk. **Retained in spirit** (Section 19) as two distinctly named composition-layer functions, not as two formal REST endpoints, since no HTTP surface exists for conversations today — introducing one now would be inventing API structure beyond what any existing accepted contract requires (binding constraint 15).

**B — one request containing a discriminated Case-context union** (`CreateNewCase` / `ContinueExistingCase(case_id)`). Fully explicit and impossible-to-conflate in principle. **Rejected in its literal, formal-type form**: the only current conversation entry point is a bare `input()`/`print()` CLI loop with no schema-validated request object anywhere in its path (`cli.py`'s own `run()` calls `orchestrator.start()` with zero arguments) — introducing a discriminated Python union type here would add structure the current surface has no accepted contract to receive it through. B's *essence* (mutual exclusivity, no ambiguous absence) is preserved by adopting two distinctly named functions instead (effectively A), which give identical guarantees without inventing a type the CLI cannot yet express.

**C — one request with optional `case_id`, absence means create.** **Rejected**: this is exactly the "collapsing creation intent into missing data" and "optional-field ambiguity" the governing task explicitly warns against — a blank or mistyped `case_id` would silently mean "create new" rather than being rejected as invalid input, which is indistinguishable from a hidden-creation risk in practice even though no field is technically defaulted at the domain layer.

**D — Case is always resolved before entering the conversation layer; the orchestrator receives only a resolved CaseId.** **Selected as the internal propagation mechanism** — already binding per the reconciliation investigation's own Section 25 (Section 10 above), not re-decided here, only implemented in design form: `build_conversation_orchestrator(engine, case_id)` resolves nothing itself; the CLI resolves `case_id` before calling it, exactly mirroring how `investor_id` is already resolved before the orchestrator is built.

**E — a higher-level application service owns both Case resolution and conversation startup.** **Rejected as unnecessary machinery**: two small, plain composition functions (`resolve_new_case`, `resolve_existing_case`), living beside `resolve_investor_identity` in the same architectural role, achieve everything a new coordinating service class would, without introducing a new class whose only job is to call two already-existing operations in sequence — Doctrine's minimality discipline counsels against the extra layer.

**F — conversation entry directly depends on CaseService.** **Rejected**: this would mean `ConversationOrchestrator` (or `cli.py`'s `run()` treated as "entry") carries a live `CaseService`/`CaseRepository` dependency for its entire lifetime merely to perform a resolution that happens exactly once, before the orchestrator's own work begins — contradicts inherited decision 4 (Section 10), which already rejected giving the orchestrator this dependency.

**G — any repository-supported contract already present.** None found beyond A/D's own composition, `CaseService.create()`/`.get()`, and `DecisionRepository`'s `list_all()`-backed selection pattern (inspected in Section 9, found inapplicable here per Section 19).

## 18. Candidate Rejection Analysis

Rejected by contradiction with an explicit binding constraint: C (optional-field ambiguity, directly named as forbidden), F (contradicts inherited decision 4). Rejected as unsupported by any existing accepted contract: B in its literal, formal-type form (no schema-validated conversation-entry boundary exists to carry it). Rejected as unnecessary additional machinery, not by contradiction: E (two plain functions suffice). Retained: A (in composition-function form) and D (internal mechanism, already binding) — combined as the selected contract.

## 19. Selected Case-Context Contract

**Two distinctly named, unambiguous composition-layer operations, resolved once, before the conversation orchestrator is built, exposed to the investor as one explicit CLI choice before the Question prompt:**

- `resolve_new_case(engine) -> uuid.UUID` — constructs `CaseService(SqlAlchemyCaseRepository(engine))` (creating the `cases` table if needed, mirroring every other composition function in this module), calls `.create()`, returns `case.id.value`.
- `resolve_existing_case(engine, case_id: uuid.UUID) -> uuid.UUID | None` — constructs the identical `CaseService`, calls `.get(CaseId(case_id))`, catches `CaseNotFoundError` and returns `None` so the caller can re-prompt (mirroring `DecisionReviewOrchestrator.select()`'s own "return `None` so the caller can re-ask" idiom, Section 9), otherwise returns `case.id.value`.

The CLI (`cli.py:run()`) asks exactly one explicit question before printing `QUESTION_PROMPT`: "Start a new investigation, or continue an existing one? (new/continue)." "new" calls `resolve_new_case` and prints the resulting id (so it can be reused later — Section 31). "continue" prompts for a CaseId string, calls `resolve_existing_case`, and re-prompts for the id (not the new/continue choice again) if `None` is returned. Neither branch is reachable without an explicit answer; there is no blank-input default. The resolved `uuid.UUID` is passed once into `build_conversation_orchestrator(engine, case_id=resolved_id)`.

## 20. Case Creation Authority

Unchanged: only `CaseService.create()` creates a Case, exactly as DO-IMP-001 established. The caller under this design is the new `resolve_new_case` composition function, itself called only from `cli.py:run()`'s explicit "new" branch — never from `ObserveFromQuestionService`, never from `CaptureObservationService`, never from `ConversationSession` or `ConversationOrchestrator`. No new creation path, no new Case field, no new persistence.

## 21. Existing-Case Validation Authority

Unchanged: only `CaseService.get()` verifies existence, exactly as DO-IMP-001 established. The caller is the new `resolve_existing_case` composition function, called once, at the single resolution boundary, before the orchestrator is built. `ObserveFromQuestionService` and `CaptureObservationService` never verify Case existence — satisfying "existence validation must occur at the correct authority boundary, not redundantly in every downstream service" directly. Case has no ownership/investor-association field, so no such check exists to invent, and none is invented; nothing in Case's own model distinguishes "absent" from "belongs to another owner" or "inaccessible" — only "absent" (`CaseNotFoundError`) is a concept here at all. Case has no status field, so no stale/closed state can ever affect continuation — a Case, once created, is validly continuable forever under current architecture.

## 22. Exact Case-Origin Design

A genuine `CaseId` originates at exactly one of two points, chosen explicitly by the investor before a conversation's Question is even asked: `CaseService.create()` (new) or `CaseService.get()` (continue, following successful validation). Never from `session_id`, never from `investor_id`, never from a default, sentinel, or inferred value — no code path in this design permits any of those substitutions.

## 23. Exact ConversationSession Design

`atlas/core/application/conversation/session.py` — `ConversationSession` gains one new field: `case_id: uuid.UUID` (no default, positioned before `session_id` in the dataclass — mirroring `DecisionReviewSession`'s own `decision_id` positioned before its `session_id`). Required at construction: yes, no default value, exactly like `DecisionReviewSession.decision_id`. Immutable in practice: no method ever reassigns it (identical discipline to `session_id`, which is also never reassigned despite the dataclass not being frozen). It may never change during a session's lifetime — no code path in this design writes to `session.case_id` after construction. Existing sessions before this change do not need migration, since `ConversationSession` is never persisted or serialized anywhere — every session is freshly constructed in-memory each run. No session equality or identity semantics exist to change (the dataclass has no custom `__eq__`). `session_id` remains generated independently via its own `default_factory`, wholly unrelated to `case_id`. `case_id` does not participate in any session lookup (none exists — sessions are never looked up by any key). One Case may have multiple sessions (each conversation that continues the same Case constructs a fresh session carrying the same `case_id` value) — this is expected and not a distinct violation. One session may never change Case, structurally, since nothing ever reassigns the field. Failure behavior for a missing `CaseId`: a `TypeError` at construction, identical in kind to how `DecisionReviewSession(decision_id=...)` already behaves if omitted — no default is introduced to soften this. **Explicit clarification, carried forward from the reconciliation investigation's own Section 15**: carrying `case_id` does not make `ConversationSession` a Case, a Domain Object, or Case-owned in any sense — it remains exactly what its own module docstring already establishes: a non-domain, unpersisted, application-boundary construct, now carrying one additional piece of resolved context alongside `session_id`.

## 24. Exact Orchestrator Design

`atlas/core/application/conversation/orchestrator.py` — `ConversationOrchestrator.__init__` gains one new required parameter, `case_id: uuid.UUID`, stored as `self._case_id`, positioned immediately after `investor_id` — mirroring exactly how `investor_id` itself is already accepted and stored, since both are plain, already-resolved values carried for the orchestrator's lifetime, not services. `start()`'s own signature does not change (remains zero arguments); its body changes from `return ConversationSession()` to `return ConversationSession(case_id=self._case_id)`. `_handle_observation` changes its `ObserveFromQuestionRequest(...)` construction to add `case_id=session.case_id` as the first keyword argument. No other of the six `_handle_*` methods changes. `CaseId` enters through the constructor (a resolved value), not through any method request and not read fresh from `ConversationSession` at construction time — `ConversationSession` receives it from the orchestrator, not the reverse; `_handle_observation` then reads it back from `session.case_id` purely because that is where the value already lives once the session exists, not because `ConversationSession` is itself authoritative for it. The orchestrator needs no `CaseRepository`/`CaseService` (inherited decision 4). Case existence is already resolved, by the CLI, before the orchestrator is constructed. The orchestrator may never create or change the active Case — no such method exists in this design. Only the observation-producing step receives `CaseId` in this package; no other step is touched, since Decision/Outcome integration is explicitly out of scope (Section 7) — a future package (R3) will add the identical one-line propagation to `_handle_decision`'s own `CommitDecisionFromConclusionRequest(...)` construction, reusing `session.case_id` unchanged, requiring no further orchestrator-level redesign. No generic global context object is introduced — repository evidence (the `investor_id` precedent) shows a single, named, resolved-value constructor parameter is the established, sufficient pattern; inventing a broader context abstraction is not supported by anything found in this codebase.

## 25. Exact ObserveFromQuestionRequest Design

`atlas/core/application/reasoning_link/observe_from_question.py` — `ObserveFromQuestionRequest` gains `case_id: uuid.UUID` as its first field, required, no default (mirroring `CaptureObservationRequest`'s own field ordering exactly).

## 26. Exact ObserveFromQuestionService Design

`ObserveFromQuestionService.observe()`'s `CaptureObservationRequest(...)` construction gains `case_id=request.case_id` as its first keyword argument. `case_id` is required (inherited from the request), passed straight through with no re-validation, no lookup, no `CaseRepository` dependency added to `ObserveFromQuestionService.__init__` (unchanged: `question_repository`, `observation_service`, `link_repository` only). The service creates no Case, changes no other output, and its domain responsibility (verify Question, delegate capture, record link) remains entirely legitimate — this is a pure mechanical propagation, identical in kind to the one-line change DO-IMP-006 itself already made inside `CaptureObservationService.capture()`. Interpretation's input is unaffected and irrelevant to this change.

## 27. Exact CaptureObservationRequest Propagation

No change to `CaptureObservationRequest` or `CaptureObservationService` — both already have exactly the required shape (Section 16). This design's entire purpose is to ensure a genuine value reaches the `case_id` argument `ObserveFromQuestionService` already needs to supply once Section 26's one-line change exists.

## 28. Domain Object Ownership Boundaries

`case_id` is Domain Object ownership content only on `Observation` itself (already true) and, by direct relay, on `CaptureObservationRequest`/`ObserveFromQuestionRequest` as the input that becomes that ownership fact. Nowhere else in this design does `case_id` constitute Domain Object ownership.

## 29. Non-Domain Object Context Boundaries

`ConversationSession.case_id` and `ConversationOrchestrator._case_id` are application context only — resolved data carried across a conversation's lifetime, never an ownership assertion by `ConversationSession` or `ConversationOrchestrator` themselves, neither of which is or becomes a Domain Object. Question, Interpretation, Hypothesis, Evidence, Conclusion, Evaluation, Learning, and the four `reasoning_link` bridges receive no `case_id` field anywhere in this design.

## 30. Public API Design

No REST API change: no HTTP surface fronts the conversation flow today (`cli.py` is the only entry point), so there is no API schema to add a field to. The `/cases` router (`POST /cases`, `GET /cases/{id}`) is unchanged and already sufficient for this design's two composition functions, which call the same underlying `CaseService` the router itself calls, not the router.

## 31. CLI Design

`atlas/core/application/conversation/cli.py:run()` gains, before the existing `print(prompts.QUESTION_PROMPT)` line: one explicit new/continue prompt (re-asked on any unrecognized answer, mirroring the existing `parse_direction`/`parse_decision_type` re-ask idiom already used later in the same loop); on "new," a call to `resolve_new_case(engine)` followed by printing the resulting id with a short note that it may be reused to continue this investigation later (without this, "continue" would be practically unreachable, since Case has no other way to be recalled); on "continue," a prompt for a CaseId string, a call to `resolve_existing_case(engine, parsed_uuid)`, and a re-prompt (for the id only, not the whole new/continue choice) if `None` is returned or the string fails to parse as a UUID. The resolved id is passed to `build_conversation_orchestrator(engine, case_id=resolved_id)` in place of today's `build_conversation_orchestrator(engine)`.

## 32. Application-Layer Design

New composition functions `resolve_new_case`/`resolve_existing_case` are added to `atlas/core/application/conversation/composition.py`, beside the existing `create_conversation_tables`/`build_conversation_orchestrator`, reusing `create_case_table` (already defined in `atlas/core/infrastructure/persistence/case/table.py`) and constructing `SqlAlchemyCaseRepository(engine)`/`CaseService(repository)` directly, exactly mirroring how every other repository in this same module is already constructed inline. `build_conversation_orchestrator` gains one new required parameter, `case_id: uuid.UUID`, threaded straight into the `ConversationOrchestrator(...)` call.

## 33. Domain-Model Implications

None. `Case`, `Observation`, `Question`, and every other domain entity are untouched by this design.

## 34. Persistence Implications

None beyond what already exists. No new table, no new column, no migration — `case_id` is threaded as plain application/request data; the only place it is ever persisted is `Observation`'s own `case_id` column, already added by DO-IMP-006.

## 35. Dependency-Injection Design

`composition.py` gains two new small functions with no new class dependency graph — they construct `CaseRepository`/`CaseService` locally and return a plain value, exactly like `resolve_investor_identity` already does for `UserId`. `build_conversation_orchestrator`'s signature changes to accept `case_id`. `ConversationOrchestrator.__init__` gains one new parameter. No repository is shared across services beyond what already exists (Case's own repository is constructed and discarded within each composition function call, never held open). No transaction boundary changes: Case resolution and Observation capture already occur as separate, sequential engine transactions, exactly like every other cross-aggregate call in this codebase. In-memory test fakes for `CaseRepository`, if introduced by the later implementation package, follow the identical `Protocol`-based pattern every other repository in this codebase already uses.

## 36. Transaction and Failure Design

Creating a new Case failing: the underlying exception propagates from `resolve_new_case` to the CLI, which reports the failure honestly and does not proceed to build the orchestrator — no retry, no silent fallback. An existing CaseId not found: `resolve_existing_case` returns `None`; the CLI re-prompts for the id only, exactly like every other re-ask idiom already in this codebase — this is not treated as a fatal error. Session construction cannot fail after Case resolution: `ConversationSession(...)` is a pure, in-memory dataclass construction with no I/O. Observation creation failing after Case resolution is handled exactly as today — the orchestrator's existing per-step exception handling re-prompts; the already-resolved, already-persisted Case is entirely unaffected and remains a valid, permanent record regardless. No cross-repository transaction ties Case resolution to Observation capture — none is promised, and none is required: Case's own model has no invariant requiring it to ever have an attached Domain Object. **Orphan Cases are possible and are acceptable under current architecture**: nothing in OE-002 or OE-004 requires a Case to contain any Domain Object; a Case created and never used (e.g., the investor abandons the conversation before Observation) remains a permanently valid, empty ownership boundary, exactly consistent with Case's own "ownership boundary" definition, which asserts nothing about what, if anything, it must eventually own.

## 37. Migration and Compatibility Design

No database migration is required — `ConversationSession` is never persisted, and `Observation`'s own schema already has `case_id` (DO-IMP-006). No compatibility layer is introduced for pre-existing sessions, since sessions never outlive a single process run. No compatibility default fabricates Case context anywhere in this design — every path either resolves a genuine `CaseId` or fails/re-prompts honestly.

## 38. Test Design

**Case choice**: explicit new-Case path resolves and returns a fresh id; explicit existing-Case path with a valid id resolves and returns that same id; an existing-Case path with an unknown id returns `None` and the CLI re-prompts; a malformed CaseId string is rejected and re-prompted, never silently treated as "new"; an unrecognized new/continue answer re-prompts the same question, never defaults to either branch. **ConversationSession**: constructing without `case_id` raises `TypeError`; `session_id` and `case_id` are independently generated/assigned and never conflated; `investor_id` (held by the orchestrator, not the session) remains untouched by any of this; nothing in this design provides a way to reassign `case_id` after construction, so no test can observe it changing; two sessions constructed with the same `case_id` are permitted and independent, mirroring the "one Case, multiple sessions" finding (Section 23). **Propagation**: the same `case_id` is traced end to end — `ConversationSession.case_id` (as resolved and passed in by `ConversationOrchestrator` at `start()`) reaches `_handle_observation`'s constructed `ObserveFromQuestionRequest` unchanged; `ObserveFromQuestionService.observe()` passes that identical value into `CaptureObservationRequest`; the persisted `Observation` contains exactly that `case_id`; no intermediate step alters, defaults, or fabricates it. **Authority**: a new Case is created only by calling `resolve_new_case`, never inside `ConversationSession`, `ConversationOrchestrator`, `ObserveFromQuestionService`, `CaptureObservationService`, any repository adapter, or any test fixture; an existing Case is validated only inside `resolve_existing_case`, never redundantly re-validated downstream; `ObserveFromQuestionService`/`CaptureObservationService` are asserted, by inspection of their constructors, to have no `CaseRepository` dependency. **Regression**: the current 22/4 failures are mapped in Section 39; existing Observation tests (already passing since `d1fb901`) remain valid and untouched; Question/Interpretation/Hypothesis/Evidence/Conclusion/Evaluation/Learning tests remain untouched, confirming no `case_id` leaked into them. None of these tests is written or modified during R2 itself (Section 7).

## 39. Current 22-Failure/4-Error Mapping

All 22 failures and 4 errors originate from the single `TypeError` in `ObserveFromQuestionService.observe()` (Section 11), surfacing across conversation-level tests (`test_orchestrator.py`, `test_conversation_end_to_end.py`, `test_conversation_engine.py`, `test_conversation_package_sprint166.py`, and the tests layered on top of the conversation flow — decision reflection/coach/investor-identity integration tests) that all drive the orchestrator through the observation step. Once the subsequent implementation package executes this design (Sections 23–27), every one of these is expected to pass again, since the fix is a pure input-completion at exactly the point they all share; no failure in this set is attributable to any other cause. This design does not itself resolve any of them (Section 7).

## 40. Exact File-Change Plan

**Definitely requiring change, next package (dependency order)**: (1) `atlas/core/application/conversation/session.py` — add `case_id: uuid.UUID` to `ConversationSession`. (2) `atlas/core/application/reasoning_link/observe_from_question.py` — add `case_id: uuid.UUID` to `ObserveFromQuestionRequest`; add `case_id=request.case_id` to the `CaptureObservationRequest(...)` call in `ObserveFromQuestionService.observe()`. (3) `atlas/core/application/conversation/orchestrator.py` — add `case_id: uuid.UUID` to `ConversationOrchestrator.__init__`; change `start()`'s body to pass it into `ConversationSession(...)`; add `case_id=session.case_id` to `_handle_observation`'s `ObserveFromQuestionRequest(...)` call. (4) `atlas/core/application/conversation/composition.py` — add `resolve_new_case`/`resolve_existing_case`; add a `case_id` parameter to `build_conversation_orchestrator`. (5) `atlas/core/application/conversation/cli.py` — add the explicit new/continue prompt and pass the resolved id through. **Conditionally requiring change** (test-only, to keep the existing suite passing against the above): `tests/unit/application/conversation/test_orchestrator.py`, `tests/unit/application/conversation/test_conversation_end_to_end.py`, `tests/test_conversation_engine.py`, `tests/test_conversation_package_sprint166.py`, `tests/unit/application/conversation/test_decision_reflection_integration.py`, `tests/unit/application/conversation/test_investor_identity_integration.py`, `tests/unit/application/conversation/test_reflection_response_integration.py`, `tests/unit/application/reasoning_link/test_observe_from_question.py`, `tests/unit/application/reasoning_link/test_core_loop_end_to_end.py` — each constructs an orchestrator, a session, or an `ObserveFromQuestionRequest` directly and will need a `case_id` fixture value added, mirroring exactly how Observation's own tests were updated in `d1fb901`. **Explicitly prohibited from change, in this package and the next**: every file listed in Section 41.

## 41. Files Prohibited from Change

`atlas/core/domain/observation/entity.py`; `atlas/core/application/observation/capture_observation.py`; `atlas/core/infrastructure/persistence/observation/*`; `atlas/core/infrastructure/api/observation/*` — Observation's approved shape (Section 7). `atlas/core/domain/case/*`; `atlas/core/application/case/create_case.py`; `atlas/core/infrastructure/persistence/case/*`; `atlas/core/infrastructure/api/case/*` — Case's own approved shape and creation authority (Section 20). `atlas/core/domain/{question,interpretation,hypothesis,evidence,conclusion,evaluation,learning}/*`; `atlas/core/domain/reasoning_link/*` — non-Domain Objects, must never gain `case_id` (Section 29). `atlas/core/domain/decision/*`, `atlas/core/application/decision/*`, `atlas/core/application/reasoning_link/commit_decision_from_conclusion.py`; `atlas/core/domain/outcome/*`, `atlas/core/application/outcome/*` — Decision/Outcome integration, out of scope (Section 7). `atlas/core/application/conversation/prompts.py` — no change is required; the new/continue question is a distinct, one-time bootstrap prompt, not a Core Loop step prompt, and does not require a new constant in this module (though the implementation package may reasonably choose to add one there — not required by this design).

## 42. Implementation Dependency Order

Per Section 40's numbering: `session.py` → `observe_from_question.py` → `orchestrator.py` → `composition.py` → `cli.py`, followed by the conditionally-required test updates. Each step is independently compilable once its predecessor lands, mirroring the exact order DO-IMP-006 itself already used (entity/request → service → composition/orchestration → tests).

## 43. Subsequent Implementation Package

**Package name**: R2-Implementation — ObserveFromQuestionService Case Integration (Implementation). **Scope**: execute exactly Sections 23–27, 31–32, and 40 of this design; no broader change. **Prerequisites**: this document, reviewed and approved. **Included**: the five production-file changes in Section 40, plus the conditionally-listed test-file updates. **Excluded**: Decision integration, Outcome integration, any other Domain Object package, any change to Observation's own approved shape, any change to Case's own approved shape. **Required verification**: scoped Ruff, direct unit tests for every changed file, targeted regression across the conversation and reasoning_link test suites, and a full-suite run expected to resolve all 22 failures/4 errors mapped in Section 39. **Failures expected to remain for unrelated reasons**: none identified — Section 39 attributes the entire current failure set to this one gap; if the full suite still shows failures after that package lands, they would be a new, separately investigated finding, not something this design anticipates.

## 44. Architecture Compliance Matrix

| Requirement | Status under this design |
|---|---|
| Observation belongs to exactly one Case | Preserved — unchanged since `d1fb901` |
| `Observation.case_id` remains required | Preserved — untouched |
| No fabricated CaseId | Preserved — Section 22, always one of two explicit resolutions |
| No hidden Case creation | Preserved — Section 20, only `resolve_new_case`, only from the CLI's explicit branch |
| `session_id` is not CaseId | Preserved — Section 23, independently generated, never conflated |
| `investor_id` is not CaseId | Preserved — orchestrator holds both as two separate, independently resolved values |
| `ConversationSession` is not a Domain Object | Preserved — Section 23, explicit clarification carried forward |
| Non-Domain Object Core Loop entities do not gain Case ownership | Preserved — Section 29, none touched |
| Explicit create-versus-continue choice | Preserved — Section 19/31, one CLI question, no default |
| Resolved CaseId remains stable for the session | Preserved — Section 23/24, never reassigned |
| `CaptureObservationService` remains free of Case resolution | Preserved — Section 16/27, unchanged |
| `ObserveFromQuestionService` performs propagation only | Preserved — Section 26, one relayed field, no lookup |
| Case creation uses authorized Case machinery | Preserved — Section 20, only `CaseService.create()` |
| Continuing a Case validates existence at the selected boundary | Preserved — Section 21, only `resolve_existing_case` |
| Package R2 performs no implementation | Preserved — this entire document is design only |
| Decision and Outcome integration remain out of scope | Preserved — Section 7, Section 41 |

## 45. Contradiction Search

No `ConversationSession` constructor lacks a legitimate future `CaseId` source (Section 23 gives it one). No second conversation entry path bypasses Case resolution — `cli.py:run()` is the only entry point found (Section 9). No direct `ObserveFromQuestionService`/`CaptureObservationService` call site outside the orchestrator and its own tests was found by the construction-site grep already performed for the reconciliation investigation and re-confirmed here. No fixture in this design fabricates an identity — `resolve_existing_case`'s `None`-on-absence path is the only "not found" behavior, never a fabricated substitute. No service creates a hidden Case. Case creation occurs only inside `resolve_new_case`. No optional `case_id` field is introduced anywhere (Section 18 rejects Candidate C outright). No conversion between `session_id`, `investor_id`, and `CaseId` exists anywhere in this design. No request in this design ever carries more than one `CaseId`. No mutable "active Case" state exists beyond the one, never-reassigned `ConversationSession.case_id`/`ConversationOrchestrator._case_id` pair. The one current public interface (the CLI) can express create-versus-continue, per Section 31. Case creation fields are fully available at conversation entry (Section 20 — none are required at all). No ownership/authorization assumption unsupported by the Case model is introduced (Section 21 states plainly that none exists to check). No transaction assumption unsupported by infrastructure is made (Section 36 promises no atomicity). No overlap with Decision or Outcome implementation exists — Sections 7/41 exclude both explicitly. No historical document conflicts with the committed reconciliation decision — the citation-only documents flagged as a historical inconsistency in the reconciliation investigation (Section 40 there) are not relied upon anywhere in this design.

## 46. Blockers

None.

## 47. Required Design Decisions

None remaining. Section 19 resolves the one decision the reconciliation investigation left open (its own Section 42, Q1).

## 48. Required Implementation Corrections

The five production-file changes and associated test-file updates listed in Section 40 — to be performed only by the subsequent, separately authorized implementation package (Section 43), not by this design document.

## 49. Historical Inconsistencies

None newly found. The reconciliation investigation's own Section 40 finding (six Implementation Design documents citing prior investigations that do not exist as files in this repository) is unchanged and not relied upon by this design.

## 50. Non-Blocking Risks

(1) Because Case carries no displayable content, an investor who loses the printed CaseId after a "new" resolution has no way to recover it later under this design (no enumeration exists) — acceptable for this minimal package, but worth a future, separate consideration if repeated loss proves a real usability problem; not a defect in this design, since nothing in the reconciliation investigation or OE-002 requires Case to be recoverable by any means other than the id itself. (2) The orchestrator's uniform bare `try/except Exception:` per step (already flagged as a non-blocking risk in the reconciliation investigation) will continue to mask a malformed `case_id` at the observation step as a silent re-prompt rather than a distinguishable error — unchanged by this design, not required to be fixed for R2's own scope. (3) `prompts.py` is not modified by this design (Section 41); the implementation package may choose to add a named constant for the new/continue prompt text there for consistency with every other prompt string, a stylistic choice with no architectural consequence either way.

## 51. Open Questions

None block this design's own completeness. One deferred, non-blocking product question: whether a future package should add `CaseRepository.list_all()` and a list-and-select CLI flow (mirroring Decision Review) once Cases plausibly accumulate enough that direct-id entry becomes inconvenient — explicitly not needed for this minimal design (Section 19), and not decided here either way.

## 52. Final Conclusion

Outcome 1 — deterministic implementation design complete. The smallest semantically complete path threads a CLI-resolved `CaseId` through five points (Section 40), reusing only already-existing, already-accepted machinery (`CaseService.create()`/`.get()`, the `investor_id` resolve-once pattern, the `DecisionReviewSession.decision_id` required-field pattern, the `select()`-returns-`None`-to-reprompt idiom) with no new Case field, no new persistence, and no enumeration capability required. The next authorized package is **R2-Implementation** (Section 43), which may proceed only once this document is reviewed and approved.

## 53. Permission or Prohibition for Implementation

**No implementation may begin from this document.** This document authorizes only that R2-Implementation may next be undertaken as its own, separately authorized package. No production code, test, Decision integration, or Outcome integration may begin as a consequence of this document alone.

## 54. Working-Tree Report

Before this task: `git status --short` was clean; branch `main`; HEAD `a4e9c42ca44a85e898e25cd6dcb464b9040e965a`, including both `d1fb901` and `a4e9c42` in its history. During this task, no production file, test file, or existing document was modified. Exactly one new file was created: `docs/atlas_domain_object_architecture/Core-Loop-Observation-Case-Context-Implementation-Design.md` (this document). Nothing was staged, committed, tagged, or pushed.
