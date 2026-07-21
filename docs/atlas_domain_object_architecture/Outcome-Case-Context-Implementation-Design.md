# Outcome Case Context — Implementation Design

## Status

Implementation-design artifact, not a normative document. Carries no Doctrine status. Where anything here appears to conflict with the Architecture Doctrine, OE-002 through OE-006, the Historical Decision Record, `Outcome-Implementation-Design.md`, or `Outcome-Implementation-Scope-Audit.md`, those documents govern and this one is wrong and must be corrected.

## Package Identifier

The Outcome-integration package following Package R3 (`Decision-Case-Context-Implementation-Design.md`, implemented in commit `4eb16b4`) — already anticipated, under this exact identifier, by that document's own "Next Genuine Integration Boundary" section as "Package R4." Design only. No code, test, or existing document is modified by this package. This document uses `Decision-Case-Context-Implementation-Design.md` as its governing structural precedent, per direct instruction, and follows its section structure exactly.

## 1. Executive Finding

**Outcome integration work is required, and its correct scope — per explicit instruction — is narrow: add Case ownership (`case_id`) to the existing Outcome aggregate, and nothing else.** Outcome is a Final-adopted Domain Object (OE-002 §5.6, §4 item 6) and is therefore bound by INV-002 ("every Domain Object MUST belong to exactly one Case") — yet the current, fully-implemented `Outcome` entity has no `case_id` field anywhere: not in the domain entity, the application request, or the persistence table. This is the identical shape of gap already corrected for Observation (Package R2) and Decision (Package R3).

**This design deliberately does not attempt the much larger, already-identified, and already-out-of-scope migration** that `Outcome-Implementation-Design.md` itself (Sections 42, 45) and `Outcome-Implementation-Scope-Audit.md` (Sections 6–8) both describe: making `decision_id`/`statement` nullable, introducing a generic `matter_target_type`/`matter_target_id` reference pair, replacing the current unconditional-AND constraint with minimum-presence semantics, building a new REST API, or adopting any data-migration policy (including Alembic). That work is explicitly excluded (Section 4 below) per direct instruction, mirroring exactly how `Decision-Case-Context-Implementation-Design.md` excluded Decision's own field-set reconciliation (its Gap G2) — with one difference worth stating precisely: for Decision, the exclusion was this document's own judgment call, checked against the governing design's silence; for Outcome, the exclusion is the user's own explicit, itemized instruction, and this document does not re-derive or re-justify it — it only confirms each excluded item is, in fact, the item the source documents describe, and implements around it.

**A correction to the prior document's own record.** `Decision-Case-Context-Implementation-Design.md`'s "Next Genuine Integration Boundary" section stated Outcome "has no current Core Loop integration to break, since `OutcomeService` is not wired into any orchestrator." A fresh repository-wide search performed for this document (Section 2) found this to be **incorrect**: `OutcomeService` is wired into `DecisionReviewOrchestrator` (`atlas/core/application/decision_review/orchestrator.py`, `_handle_outcome`), a real, standalone, CLI-exposed composite service (ATLAS-003, `decision_review/cli.py`). This does not block the package — it changes what "composite-service propagation" means for Outcome, and is treated as a genuine finding, not silently folded into the file list without comment (Section 5, Gap G5).

## 2. Repository Evidence

**Governing documents read fresh for this task**: `Outcome-Implementation-Design.md` (in full, all 45 sections, re-confirmed against the copy already read for `Outcome-Implementation-Scope-Audit.md`); `Outcome-Implementation-Scope-Audit.md` (in full); `Decision-Case-Context-Implementation-Design.md` (in full, as the governing structural precedent); `OE-002-Domain-Object-Model.md` §3, §3.1, §4, §5.6, §6; `OE-004-Domain-Invariants.md` INV-002 through INV-006, INV-012.

**Implementation paths inspected, read in full**: `atlas/core/domain/outcome/{entity,value_objects,exceptions,repository}.py`; `atlas/core/application/outcome/capture_outcome.py`; `atlas/core/infrastructure/persistence/outcome/{table,sqlalchemy_repository}.py`; `atlas/core/application/decision_review/{orchestrator,composition,session,cli}.py`; `atlas/core/infrastructure/api/app.py` (confirmed: no Outcome router mounted, no Outcome API directory exists).

**Tests inspected, read in full**: `tests/unit/domain/outcome/test_entity.py`; `tests/unit/application/outcome/test_capture_outcome.py`; `tests/unit/infrastructure/persistence/outcome/test_sqlalchemy_repository.py`; `tests/unit/application/decision_timeline/test_query.py`; `tests/unit/application/evaluation/test_capture_evaluation.py`; `tests/unit/application/reasoning_link/test_core_loop_end_to_end.py`; `tests/unit/application/decision_review/{test_orchestrator,test_review_end_to_end}.py` (read to confirm they do not construct `Outcome`/`CaptureOutcomeRequest` directly and therefore need no change); `tests/unit/infrastructure/persistence/case/test_sqlalchemy_repository.py`; `tests/unit/infrastructure/persistence/knowledge_reference/test_sqlalchemy_repository.py`.

**Repository-wide searches performed** (excluding `.claude/worktrees/**`, a separate git worktree, not part of this branch):
- `Outcome\.capture\(` — 16 non-worktree call sites across 5 files, recounted directly via `grep -c` during this audit (an earlier draft of this document undercounted `test_entity.py`'s own call sites as 9; the correct count, re-verified twice, is 12 — corrected throughout this document): 1 production (`capture_outcome.py`); 4 test files — own-suite `test_entity.py` (12 individual call sites within that one file), `test_sqlalchemy_repository.py`'s `_new_outcome()` helper (1 call site), `decision_timeline/test_query.py`'s `_make_outcome()` helper (1 call site), `evaluation/test_capture_evaluation.py`'s `existing_outcome` fixture (1 call site).
- `\bOutcome\(` (direct, non-factory construction) — 1 hit: `atlas/core/infrastructure/persistence/outcome/sqlalchemy_repository.py`'s `_to_outcome()` — production, already in scope as the persistence-layer change.
- `CaptureOutcomeRequest\(` — 3 hits: `decision_review/orchestrator.py` (production, `_handle_outcome`); `test_core_loop_end_to_end.py` (2 call sites); `test_capture_outcome.py`'s `_request()` helper.
- `insert\(outcomes_table` — 1 hit: `sqlalchemy_repository.py`'s own `add()` method (production, already in scope).
- `outcomes_table\.columns\.keys\(\)` (hardcoded schema assertions) — 3 hits: `outcome/test_sqlalchemy_repository.py` (own-suite), `case/test_sqlalchemy_repository.py`, `knowledge_reference/test_sqlalchemy_repository.py` — the latter two are cross-package "existing core tables are unchanged" regression assertions.
- `OutcomeService\(` — 3 hits: `decision_review/composition.py` (production); `test_core_loop_end_to_end.py`; `test_capture_outcome.py`.
- Composite-service and Core Loop construction paths — confirmed exactly two: `decision_review/orchestrator.py._handle_outcome` (Gap G5) and the Core Loop end-to-end test's own step 8 (no production composite service beyond `OutcomeService` itself touches Outcome; `evaluation`/`learning` only ever read Outcome by id, never construct one).

No additional, previously-undisclosed construction site was found beyond what this section lists.

## 3. Current Architecture

**Domain**: `atlas/core/domain/outcome/entity.py` — `Outcome(id: OutcomeId, decision_id: DecisionId, statement: Statement, occurred_at: datetime, recorded_at: datetime, note: str | None = None)`, `@dataclass(frozen=True)`, `Outcome.capture(*, decision_id, statement, occurred_at, note=None, clock=_utc_now)`. No `case_id` anywhere.

**Application**: `atlas/core/application/outcome/capture_outcome.py` — `CaptureOutcomeRequest(decision_id, statement, occurred_at, note=None)`; `OutcomeService(decision_repository: DecisionRepository, outcome_repository: OutcomeRepository)` — two dependencies; `.capture()` verifies the referenced Decision exists (`self._decisions.get(decision_id) is None` → `DecisionNotFoundError`), discards the fetched Decision otherwise, and translates the request into `Outcome.capture(...)`. No `CaseRepository` anywhere.

**Composite (Decision Review, ATLAS-003)**: `atlas/core/application/decision_review/orchestrator.py` — `DecisionReviewOrchestrator._handle_outcome` constructs `CaptureOutcomeRequest(decision_id=session.decision_id, statement=answer, occurred_at=_now())` and calls `self._outcome_service.capture(...)`. `DecisionReviewSession` (`decision_review/session.py`) carries `decision_id`, `session_id`, `current_step`, `outcome_id`/`evaluation_id`/`learning_id`, `pending` — **no `case_id` field, and no Case-resolution mechanism of any kind anywhere in this module** (`decision_review/composition.py`'s `create_decision_review_tables` creates `decisions`, `outcomes`, `evaluations`, `learnings` — never `cases`). This is structurally unlike `ConversationSession`, which already gained `case_id` in Package R2; Decision Review has never had a Case-context concept to begin with.

**Persistence**: `atlas/core/infrastructure/persistence/outcome/table.py` — `outcomes_table(outcome_id, decision_id, statement, note, occurred_at, recorded_at)`, no `case_id` column. `sqlalchemy_repository.py` — `add`/`get`/`list_all`/`list_by_decision_id`, insert-only.

**API**: none. Confirmed via `app.py` and via absence of any `atlas/core/infrastructure/api/outcome/` directory. Not part of this package (Section 4).

**Downstream consumers** (read-only, via `OutcomeRepository.get()`/`.list_all()`/`.list_by_decision_id()`): `decision_timeline` (production code only reads Outcome; its own test module's fixture, `_make_outcome`, constructs one directly — Section 5, Gap G3); `evaluation` (production code only reads Outcome by id via `OutcomeRepository.get()` to verify existence before capturing an `Evaluation`; its own test module's fixture, `existing_outcome`, constructs an `Outcome` directly — Gap G3). Neither `decision_timeline`'s nor `evaluation`'s own production code constructs an `Outcome`.

## 4. Accepted Outcome Semantics, Narrowly Scoped to This Package

**Settled** (OE-002 §5.6, quoted in full in `Outcome-Implementation-Design.md` Section 5): Outcome is a permanent, independently-identified, Case-owned Domain Object recording a determinate state of affairs the Case treats as having become actual — without asserting objective truth, causal attribution, success, failure, or measurement. Outcome belongs to exactly one Case (INV-002), assigned independently, never derived from any referenced object, immutable once accepted. Its identity (`OutcomeId`) is independent of its content and of any object it references (OE-002 §5.6 Identity clause).

**Explicitly excluded from this package** (per direct instruction; each item's own deferred status is already established by `Outcome-Implementation-Design.md` Sections 42/45 and confirmed as a genuine scope boundary by `Outcome-Implementation-Scope-Audit.md` Sections 6–8):

| Excluded item | Why it is excluded here |
|---|---|
| Making `decision_id` nullable | Part of the separately-deferred field-set migration (`Outcome-Implementation-Design.md` §42 point 2); changes an existing `NOT NULL` constraint, not additive. |
| Making `statement` nullable | Same migration (§42 point 1); changes an existing `NOT NULL` constraint. |
| Introducing `matter_target_type` | Same migration (§42 point 3); a new reference mechanism replacing the current hardcoded one. |
| Introducing `matter_target_id` | Same migration (§42 point 3). |
| Replacing the current constraint with minimum-presence semantics | Same migration (§39, §42); today's schema enforces an unconditional AND (content and a Decision reference both mandatory), which this package does not touch in either direction. |
| Creating a new Outcome REST API | §39/§42 state this design "does not currently exist as a REST API... these are specifications the future API layer must satisfy, not a description of code already present"; building one is a separate, undesigned effort (Scope Audit §8.3). |
| Adopting Alembic or defining a data-migration policy | Not raised by the source design at all; flagged only by the Scope Audit (§8.3) as a consequence of Category B, which this package does not enter. |
| Reconciling or redesigning Outcome's broader field model | The migration itself (§42/§45's own "genuine future migration effort... not as part of this document"). |

**This package's only semantic change**: Outcome gains a required `case_id: CaseId`, and that identifier is propagated, unchanged, through every existing Outcome construction, application, persistence, and composite-service path. No other field, constraint, or relationship changes.

## 5. Gap Analysis

**G1 — Missing Case ownership (in scope).** Observed: `Outcome` has no `case_id` anywhere (domain, application, persistence). Expected: INV-002 requires exactly one Case per Domain Object, unconditionally. Evidence: `entity.py`, `capture_outcome.py`, `table.py` (Section 3). Classification: missing Case propagation / domain-application-persistence gap. Impact: Outcome, a Final-adopted Domain Object, is not architecturally compliant. **In scope.**

**G2 — Field-set/API/migration reconciliation (out of scope).** Observed and disposed of in full in Section 4's table above. **Out of scope**, per direct instruction — reported, not resolved.

**G3 — Four test files construct `Outcome`/`Outcome.capture(...)` directly (in scope, as mechanical fixture corrections only).** Observed: `tests/unit/domain/outcome/test_entity.py` (12 call sites, own-suite, confirmed by direct `grep -c` recount during audit), `tests/unit/infrastructure/persistence/outcome/test_sqlalchemy_repository.py`'s `_new_outcome()` (own-suite), `tests/unit/application/decision_timeline/test_query.py`'s `_make_outcome()`, `tests/unit/application/evaluation/test_capture_evaluation.py`'s `existing_outcome` fixture. Expected: once `case_id` becomes a required, no-default field on `Outcome.capture()`, every one of these calls raises `TypeError`, mirroring exactly what happened for `Decision.register(...)` in Package R3. Evidence: Section 2's repository-wide search. Classification: mechanical, disclosed, unavoidable consequence of G1. Impact: four fixture edits (two own-suite, two cross-package), zero behavioral change to `decision_timeline`'s or `evaluation`'s own functionality. **In scope, as fixture corrections only.**

**G4 — Two cross-package "existing core tables are unchanged" tests hardcode `outcomes_table`'s column set (in scope, as mechanical assertion corrections only).** Observed: `tests/unit/infrastructure/persistence/case/test_sqlalchemy_repository.py` and `tests/unit/infrastructure/persistence/knowledge_reference/test_sqlalchemy_repository.py` each assert `set(outcomes_table.columns.keys()) == {...}` without `case_id`; the `case/` file additionally carries a comment stating "outcomes_table has not [gained case_id] — Outcome's own Case-integration remains a separate, later, not-yet-authorized package" (written during Package R3, now stale the moment this package lands). Expected: both assertions must include `case_id`; the stale comment must be corrected to state the current fact. Classification: mechanical, disclosed, identical in kind to the comment correction already performed once, for the same file, during Package R3. **In scope, as assertion/comment corrections only** — no behavioral change to Case's or Knowledge Reference's own test suites.

**G5 — `DecisionReviewOrchestrator._handle_outcome` has no Case-context source of its own (in scope; resolved by internal derivation, not by request-shape change — see Section 6 for the reasoning).** Observed: unlike `ConversationSession` (which gained `case_id` in Package R2) or the API caller (Decision's own path), `DecisionReviewSession` has no `case_id` and no Case-resolution flow. This is a genuinely different situation from Decision's own G5 (Core Loop `_handle_decision`), where `session.case_id` already existed and only needed one more relay hop. Here, no existing value exists to relay. Classification: missing Case-context source, not missing propagation of an already-resolved one. Impact and resolution: Section 6 explains why the chosen resolution requires **zero changes** to `decision_review/orchestrator.py` or `decision_review/composition.py`. **In scope**, resolved entirely inside `OutcomeService.capture()`.

## 6. Selected Implementation

**Production files:**

1. `atlas/core/domain/outcome/entity.py` — add `case_id: CaseId` as a required field on `Outcome` (positioned immediately after `id`, before `decision_id`, mirroring `Decision`'s own field order), import `CaseId` from `atlas.core.domain.case.value_objects`; add `case_id: CaseId` as `Outcome.capture`'s first keyword-only parameter, passed straight through into the constructed instance with no re-validation. *Why here*: Outcome's own aggregate boundary; Case ownership is intrinsic to the entity, exactly as it is for Decision and Observation.

2. `atlas/core/application/outcome/capture_outcome.py` — **`CaptureOutcomeRequest` gains no new field.** `OutcomeService.capture()` is changed to retain the Decision it already must fetch (`decision = self._decisions.get(decision_id)`, instead of discarding the result after the `is None` check) and to pass `case_id=decision.case_id` into `Outcome.capture(...)`. *Why here, and why this diverges from Decision's own request-shape convention*: every other Domain Object's Capture-request DTO in this codebase (`CaptureDecisionRequest.case_id`, `CaptureObservationRequest.case_id`) carries `case_id` as an explicit, caller-supplied field, because each has an existing, already-resolved upstream source (`ConversationSession.case_id`, or the API caller) to supply it from. Outcome's only production call site, `DecisionReviewOrchestrator._handle_outcome`, has no such source (Section 3, Section 5 G5) — `DecisionReviewSession` carries no `case_id`. The only Case-context fact available anywhere in Outcome's current call graph is the `case_id` already carried by the very Decision every Outcome capture is unconditionally required to reference and verify exists. Reading it from that already-fetched Decision is not an inference or a fabrication — it is the one, single, uniquely-determined source of truth for the Outcome's own Case ownership, obtained via a lookup the service already performs for an unrelated reason (the existing `DecisionNotFoundError` check). This is evaluated against, and preferred over, the alternative of adding an explicit `case_id` field to `CaptureOutcomeRequest` (Section 7).

3. `atlas/core/infrastructure/persistence/outcome/table.py` — add `Column("case_id", String, nullable=False, index=True)` immediately after `outcome_id`; no foreign key, no server default.

4. `atlas/core/infrastructure/persistence/outcome/sqlalchemy_repository.py` — `_to_row` gains `"case_id": str(outcome.case_id)`; `_to_outcome` gains `case_id=CaseId(uuid.UUID(row["case_id"]))`, read unconditionally (no fallback), fails loudly on a genuinely missing legacy row — identical discipline to Decision's and Observation's own repository corrections.

**No change** to `OutcomeRepository`'s Protocol (`add`/`get`/`list_all`/`list_by_decision_id` remain exactly as they are — no `list_by_case_id` is added; nothing in this package's own scope requires it, and adding one would be an unrequested extension). **No change** to `OutcomeService.__init__`'s constructor signature — it remains exactly `(decision_repository: DecisionRepository, outcome_repository: OutcomeRepository)`; no `CaseRepository` is added, mirroring `CaptureDecisionService`'s own precedent of never adding a `CaseRepository` dependency. **No change** to `atlas/core/application/decision_review/orchestrator.py`, `composition.py`, or `session.py` — the derivation in item 2 above makes `case_id` propagation entirely internal to `OutcomeService`, invisible to every caller, including `DecisionReviewOrchestrator`. **No change** to `Evaluation`, `Learning`, or any `reasoning_link` bridge entity — neither is a Domain Object under OE-002 §4's closed set, and neither gains `case_id` anywhere in this package. **No change** to `Case`, `CaseService`, `CaseRepository`, or `composition.py`'s Case-resolution helpers.

**Explicit non-substitution.** `case_id` originates from exactly one place in this package: the `case_id` already carried by the Decision that `OutcomeService.capture()` already fetches and verifies exists. Neither `DecisionReviewSession.session_id`, `DecisionReviewSession.decision_id` (used only to look up the Decision, never itself treated as a Case identifier), `user_id`, nor any investor identity is ever reused, cast, converted, or interpreted as `case_id` anywhere in this design — each remains the distinct identifier it already was, exactly as established in `Core-Loop-Case-Context-Reconciliation-Investigation.md` and reaffirmed, not reopened, by `Decision-Case-Context-Implementation-Design.md` Section 4, and reaffirmed identically here.

## 6a. Soundness of the Internal-Derivation Propagation Design

This section directly addresses the central design question this package turns on: is deriving Outcome's `case_id` from the already-fetched Decision, rather than adding an explicit `case_id` field to `CaptureOutcomeRequest`, the narrowest correct solution under the existing architecture?

- **The Decision is always the authoritative same-Case source for this path, and this is stronger than a design preference — it is what INV-004 requires.** OE-004's INV-004 ("Same-Case Reference") states: "Every semantic reference from one Domain Object to another MUST connect Domain Objects belonging to the same Case." Outcome's `decision_id` is exactly such a semantic reference (the pre-reconciliation stand-in for the referential committed-to/realized-matter form `Outcome-Implementation-Design.md` describes, Section 42). Once both `Outcome` and `Decision` carry `case_id`, INV-004 does not merely permit deriving Outcome's `case_id` from the referenced Decision — it **forbids** the alternative of an independently-supplied `case_id` that could ever disagree with the Decision's own. An explicit `case_id` field on `CaptureOutcomeRequest`, supplied by a caller, would create exactly the possibility INV-004 exists to foreclose (a cross-Case reference) unless independently re-validated against the Decision's own `case_id` — at which point the "independent" field would be redundant with, not an alternative to, the derivation this design already performs. Internal derivation does not merely avoid inconvenience; it is the only mechanism that makes an INV-004 violation structurally impossible rather than something a validation branch must catch.
- **The Decision lookup occurs before Outcome construction.** Confirmed directly in `capture_outcome.py`: `self._decisions.get(decision_id)` is called, and the `DecisionNotFoundError` check completes, before `Outcome.capture(...)` is ever invoked. There is no ordering question to resolve.
- **The stored `case_id` is copied verbatim, never inferred or substituted.** `case_id=decision.case_id` is a direct field read, not a computation, cast, or lookup against any other identifier.
- **No Case identity is fabricated.** The Decision's own `case_id` was itself independently assigned at Decision-capture time (Package R3); this package never generates a new `CaseId` anywhere.
- **The caller cannot currently provide a valid independent Case identity without adding broader Case-resolution machinery.** Confirmed by Section 3: `DecisionReviewSession` carries no `case_id`, and `decision_review/composition.py` creates no `cases` table and holds no `CaseRepository`. The only alternative to internal derivation is building a Case-resolution flow for Decision Review from scratch — considered and rejected in Section 7.
- **Keeping the lookup inside `OutcomeService` avoids duplicated validation and orchestration responsibility.** Were `case_id` instead an explicit request field, `DecisionReviewOrchestrator._handle_outcome` would need its own Decision lookup solely to populate it, duplicating the lookup `OutcomeService.capture()` already performs (Section 7).
- **This does not make `case_id` optional on the `Outcome` entity itself.** `Outcome.capture`'s `case_id` parameter remains required, keyword-only, with no default (Section 6, item 1) — the derivation choice concerns only *where the application layer obtains the value it must supply*, never whether the domain layer may accept its absence.
- **This does not establish a general rule that Domain Objects may derive Case identity arbitrarily from related objects.** This design is justified entirely by facts specific to Outcome's own current call graph: Outcome has exactly one production construction path, that path already mandatorily fetches a same-Case-bound Decision for an unrelated existence check, and no independent Case-context source exists anywhere else in that path. It does not follow, and this document does not claim, that any other Domain Object may derive its own `case_id` from an object it references merely because a reference exists — Decision's and Observation's own `case_id` fields, for instance, are supplied explicitly by their callers precisely because each already has its own independent, already-resolved Case-context source (`ConversationSession.case_id`, or the API caller), and neither should be changed to derive `case_id` from anything else on the strength of this document.
- **This design remains specific to the existing Outcome-from-Decision construction path.** If Outcome ever gains an additional, independent construction path with its own Case-context source (e.g., a future REST API, explicitly out of scope here — Section 4), that path would supply `case_id` explicitly, exactly as Decision's and Observation's APIs do; this derivation is not a substitute for that and does not need to be reconciled with it now.

## 7. Rejected Alternatives

- **Adding an explicit `case_id: uuid.UUID` field to `CaptureOutcomeRequest`, populated by the caller (mirroring Decision's DTO shape exactly).** Considered directly, since "mirror Decision's precedent" is this document's own governing instruction. Rejected: doing so would require `DecisionReviewOrchestrator._handle_outcome` to independently look up the Decision itself (duplicating the lookup `OutcomeService.capture()` already performs internally) solely to populate one field, and would then force a choice between (a) trusting the caller-supplied value with no verification — a latent, unnecessary correctness gap — or (b) adding new same-Case validation logic comparing `request.case_id` to the fetched Decision's own `case_id`, which is new invariant-enforcement logic beyond "strictly additive... only semantic change is [that] `case_id`... is propagated unchanged." Internal derivation (Section 6, item 2) achieves the identical guarantee — the Outcome's `case_id` is always, by construction, exactly the reviewed Decision's own `case_id` — with no duplication and no new validation branch.
- **Adding `case_id` to `DecisionReviewSession` and building a Case-resolution flow for Decision Review, mirroring Package R2's `resolve_new_case`/`resolve_existing_case`.** Rejected: Decision Review has never had a Case-context concept (Section 3); introducing one would be a disproportionate, separate integration effort in its own right, not a mechanical consequence of adding `case_id` to Outcome.
- **Making `case_id` optional.** Rejected outright, per explicit instruction and INV-002; also inconsistent with every other `case_id` field's already-settled required-no-default precedent in this codebase.
- **Introducing `matter_target_type`/`matter_target_id`, making `decision_id`/`statement` nullable, replacing the current constraint, building a REST API, or adopting Alembic.** Rejected: each is explicitly excluded by direct instruction (Section 4); none is touched, invented, or partially started here.
- **Adding a `list_by_case_id` query method to `OutcomeRepository`.** Rejected: no current caller needs it; nothing in this package's own scope requires a new access pattern, and adding one would be an unrequested extension beyond the stated single semantic change.
- **Modifying `decision_timeline`'s or `evaluation`'s own production code to accommodate the new `case_id` requirement.** Rejected: neither's production code constructs an `Outcome`; only their test fixtures do, and only those fixtures are touched (Section 5, Gap G3), never their own logic.

## 8. Test Design

**Existing tests to update, own Outcome suite:**
- `tests/unit/domain/outcome/test_entity.py` — add a module-level `_CASE_ID = CaseId()` constant (mirroring the established pattern; new import `from atlas.core.domain.case.value_objects import CaseId`); add `case_id=_CASE_ID` to all 12 existing `Outcome.capture(...)` calls; add `test_requires_a_case_id` (mirrors `test_requires_a_decision_id`/`test_requires_a_statement` exactly — omits only `case_id`); add a `TestCaseOwnership` class (two Outcomes in the same Case remain distinct; Outcomes in different Cases are independent) — mirrors `test_entity.py` for Decision exactly.
- `tests/unit/infrastructure/persistence/outcome/test_sqlalchemy_repository.py` — `_new_outcome()` helper gains `case_id=CaseId()` default; `TestEqualsOriginal` gains `assert reloaded.case_id == original.case_id`; `test_outcome_table_has_no_sql_foreign_key`'s expected column set gains `"case_id"`; add a `TestCaseOwnership` class with a `case_id`-not-null enforcement test via a direct `IntegrityError`-raising raw insert, mirroring Decision's own persistence test addition.

**Existing test to update, application suite (propagation confirmation only — `CaptureOutcomeRequest`'s own shape does not change, so no new-field fixtures are needed here):**
- `tests/unit/application/outcome/test_capture_outcome.py` — add one assertion to `test_captures_an_outcome_of_an_existing_decision`: `assert outcome.case_id == existing_decision.case_id`. No `test_rejects_missing_case_id`/`test_rejects_malformed_case_id` is added — there is no such field to omit or malform, a deliberate and disclosed difference from Decision's own API-layer test additions, since Outcome has no API and `CaptureOutcomeRequest` carries no `case_id` field (Section 6).

**Existing test to update, Core Loop suite (propagation confirmation only, no fixture change — `CaptureOutcomeRequest`'s call sites are untouched):**
- `tests/unit/application/reasoning_link/test_core_loop_end_to_end.py` — add one assertion after step 8 (Outcome capture): `assert outcome.case_id == decision.case_id`, alongside the existing round-trip/FK assertions. The negative-case test `test_capture_outcome_of_unknown_decision_writes_nothing` needs no change: the referenced Decision does not exist, so `DecisionNotFoundError` is still raised before any `case_id` derivation is attempted.

**Fixture-only corrections (Gap G3, one line each, no assertion or behavior change beyond a new import where absent):**
- `tests/unit/application/decision_timeline/test_query.py` — `_make_outcome()` gains `case_id=CaseId()`; new import `from atlas.core.domain.case.value_objects import CaseId`.
- `tests/unit/application/evaluation/test_capture_evaluation.py` — `existing_outcome` fixture's `Outcome.capture(...)` call gains `case_id=CaseId()`; new import `from atlas.core.domain.case.value_objects import CaseId`.

**Schema-assertion corrections (Gap G4, one file each):**
- `tests/unit/infrastructure/persistence/case/test_sqlalchemy_repository.py` — `test_existing_core_tables_are_unchanged_by_this_package`'s `outcomes_table.columns.keys()` assertion gains `"case_id"`; the preceding comment ("outcomes_table has not — Outcome's own Case-integration remains a separate, later, not-yet-authorized package") is corrected to state that Outcome's own Case Context package has since added `case_id` to `outcomes_table` as well.
- `tests/unit/infrastructure/persistence/knowledge_reference/test_sqlalchemy_repository.py` — `TestExistingCoreTablesAreUnchanged`'s `outcomes_table.columns.keys()` assertion gains `"case_id"`.

**No new, dedicated own-suite application-layer test file is added** — unlike Decision's Package R3 (which addressed a pre-existing coverage gap, Gap G4 in that document, by adding `tests/unit/application/decision/test_capture_decision.py`), Outcome already has a direct, dedicated application-layer test file (`test_capture_outcome.py`); no equivalent coverage gap exists here.

**Narrow test commands:**
```
.venv/bin/python -m pytest -q tests/unit/domain/outcome tests/unit/application/outcome \
  tests/unit/infrastructure/persistence/outcome
```

**Adjacent regression commands:**
```
.venv/bin/python -m pytest -q tests/unit/application/decision_review tests/unit/application/decision_timeline \
  tests/unit/application/evaluation tests/unit/application/reasoning_link/test_core_loop_end_to_end.py \
  tests/unit/infrastructure/persistence/case tests/unit/infrastructure/persistence/knowledge_reference
```

**Final full-suite command:** `.venv/bin/python -m pytest`.

## 9. Implementation Sequence

1. `atlas/core/domain/outcome/entity.py` (add `case_id`).
2. `atlas/core/application/outcome/capture_outcome.py` (internal derivation from the already-fetched Decision).
3. `atlas/core/infrastructure/persistence/outcome/table.py` + `sqlalchemy_repository.py` (persist).
4. Own-suite test updates (Section 8, first two groups).
5. Application-suite propagation assertion (`test_capture_outcome.py`).
6. Core Loop propagation assertion (`test_core_loop_end_to_end.py`).
7. Four fixture-only corrections (Gap G3).
8. Two schema-assertion/comment corrections (Gap G4).
9. Full-suite verification.

No step touches `decision_review/orchestrator.py`, `composition.py`, or `session.py` — confirmed by Section 6's derivation choice.

## 10. Verification and Acceptance Criteria

- Narrow Outcome tests (Section 8 command 1) green.
- Adjacent regression command (Section 8 command 2) green.
- Full suite green: baseline recorded below, plus new tests added in step 4 (`test_requires_a_case_id`, `TestCaseOwnership` ×2 in `test_entity.py`, `TestCaseOwnership` ×2 in the persistence test), plus zero net change from the two propagation assertions (existing tests gain one assertion each, not new test functions), minus zero (no test removed), skipped count unchanged, failures and errors at 0.
- `.venv/bin/ruff check` clean on every changed file.
- No file outside Section 11's list changed.
- Clean working tree after commit; nothing staged beyond the intended files; no push.

## 11. Expected File Set

**Production (4):** `atlas/core/domain/outcome/entity.py`; `atlas/core/application/outcome/capture_outcome.py`; `atlas/core/infrastructure/persistence/outcome/table.py`; `atlas/core/infrastructure/persistence/outcome/sqlalchemy_repository.py`.

**Tests, own-suite (2 modified):** `tests/unit/domain/outcome/test_entity.py`; `tests/unit/infrastructure/persistence/outcome/test_sqlalchemy_repository.py`.

**Tests, propagation confirmation (2 modified, one assertion each):** `tests/unit/application/outcome/test_capture_outcome.py`; `tests/unit/application/reasoning_link/test_core_loop_end_to_end.py`.

**Tests, fixture-only (2 modified):** `tests/unit/application/decision_timeline/test_query.py`; `tests/unit/application/evaluation/test_capture_evaluation.py`.

**Tests, schema-assertion/comment corrections (2 modified):** `tests/unit/infrastructure/persistence/case/test_sqlalchemy_repository.py`; `tests/unit/infrastructure/persistence/knowledge_reference/test_sqlalchemy_repository.py`.

**Documentation:** none.

**Not touched, and confirmed by this design not to require any change:** `atlas/core/application/decision_review/{orchestrator,composition,session,cli}.py`; `atlas/core/domain/{evaluation,learning}/**`; any `reasoning_link` module; `atlas/core/infrastructure/api/app.py`.

## 12. Commit Plan

One atomic commit, if and when a separate, explicit implementation task is authorized. Recommended message: `Implement Outcome Case Context` (mirroring commit `4eb16b4`'s "Implement Decision Case Context"). **No commit is made during this design task, and none is made without a separate, explicit implementation authorization per Section 14.**

## 13. Stop Conditions

**Checked, do not apply to the in-scope `case_id` addition**: no governing-document conflict blocks it (INV-002 is unconditional and settled); Outcome's Case-ownership semantics are fully settled (OE-002 §5.6, §3.1); narrow tests are not already green with no gap — the gap is real and confirmed by direct inspection (Section 5, G1); the architecture does not contradict this specific integration — Package R3's own document already anticipated it by name ("Package R4").

**Applies, and this design deliberately stops here**: Gap G2 (the field-set/API/migration reconciliation, Section 4) is exactly the case where implementing further "would require unrelated ontology or architecture work" — this design does not touch it, invents no resolution, and reports it exactly as already reported by `Outcome-Implementation-Scope-Audit.md`.

## 14. Permission or Prohibition for Implementation

**No implementation may begin from this document.** This document is itself design-only and is not self-authorizing: producing or committing it does not constitute approval to modify any production or test file listed in Sections 6, 8, or 11. The next authorized step is a separate, explicitly-approved implementation package (recommended commit per Section 12), reviewed on its own terms before any code changes. This package remains strictly bounded to the single semantic change stated in Section 4; it does not, and may not, be read as authorizing any item in Section 4's exclusion table, regardless of how mechanically adjacent that item might appear once `case_id` lands.

## Baseline Execution Record

`git status --short` at the start of this design task: one untracked file, `docs/atlas_domain_object_architecture/Outcome-Implementation-Scope-Audit.md` (produced by the immediately preceding audit task; not part of this package). HEAD: `4eb16b4d005f213d7b2792d5760d76ce911a64a9`, branch `main`. Combined current-state test selection (`tests/unit/domain/outcome`, `tests/unit/application/outcome`, `tests/unit/infrastructure/persistence/outcome`, `tests/unit/application/decision_review`, `tests/unit/application/decision_timeline`, `tests/unit/application/evaluation`, `tests/unit/application/reasoning_link/test_core_loop_end_to_end.py`, `tests/unit/infrastructure/persistence/case`, `tests/unit/infrastructure/persistence/knowledge_reference`): **102 passed, 0 failed, 0 errors** — Outcome's current, `case_id`-less implementation is internally consistent and fully green today; the gap is one of absence (INV-002 non-compliance), not of any failing behavior.

**Independently re-verified during the later audit of this document**: the same combined selection re-run, HEAD unchanged at `4eb16b4`, working tree unchanged apart from this document and the Scope Audit document — **102 passed, 0 failed, 0 errors**, identical to the figure above. `tests/unit/domain/outcome/test_entity.py` run in isolation collects and passes exactly 12 items, confirming both the test-count baseline and the corrected `Outcome.capture(...)` call-site count (Section 2) independently.

## Next Genuine Integration Boundary

After this package, per `Core-Loop-Case-Context-Reconciliation-Investigation.md`'s own sequencing, the next unintegrated boundary is **Reasoning Trace** (Package R5 — approved design, zero existing code). Independently of that sequencing, Outcome's own separately-deferred migration (Section 4's exclusion table) remains open and unscoped by any implementable document; per the Scope Audit's own final statement, that migration requires its own future design work — a data-migration policy, an Alembic decision, and an actual API design — none of which this package performs or brings closer to being decided.
