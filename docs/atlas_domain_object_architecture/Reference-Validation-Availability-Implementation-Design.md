# Reference Validation Availability — Implementation Design

## Status

Implementation-design artifact, not a normative document. Carries no Doctrine status. Where anything here appears to conflict with the Architecture Doctrine, OE-002, OE-004, or OE-006, those documents govern and this one is wrong and must be corrected. This document does not amend architecture, does not resolve any ontological question, and does not implement any code.

## Package Identifier

The package following the completed Case Context initiative (Observation — Package R2, commit `3fecb0e`/`b41f0ff`; Decision — Package R3, commit `4eb16b4`; Outcome — Package R4, commit `60b681d`) and the "ATLAS CORE — Reference Validation Availability Audit" that identified this as the next correct package. Design only. No code, test, or existing document is modified by this package.

## 1. Executive Finding

**Knowledge Reference's and Judgment's own capture-availability gates can now be widened, because the prerequisite work they were each explicitly waiting on — `case_id` existing on Observation, Decision, and Outcome — has landed.** Both modules' own docstrings, written before that prerequisite existed, state directly: *"Capture against each becomes available, with no change to [this module's] own schema or API contract, once that type's own prerequisite work lands."* That prerequisite has now landed for three of the four previously-excluded types. Only Reasoning Trace remains genuinely blocked — not by a missing `case_id`, but because no repository, persistence table, or accepted-instance mechanism for it exists anywhere in this codebase, so INV-005 (prior acceptance) cannot be established against it under any circumstance.

**This is not new work invented by this document.** Both capture-availability gates were deliberately, narrowly scoped by their own original implementations (`Knowledge-Reference-Pre-Commit-Architecture-Review.md`, Outcome 2) to admit only what could be positively verified at the time. This design activates exactly what those same modules already anticipated, using the identical dispatch pattern, error types, and repository-based verification they already contain — nothing is redesigned.

## 2. Repository Verification (re-confirmed fresh for this document, not assumed from the audit)

**Current capture-enabled target types, verified directly:**
- Knowledge Reference: `_CURRENTLY_CAPTURE_ENABLED_TARGET_TYPES = frozenset({DomainObjectType.KNOWLEDGE_REFERENCE})` (`capture_knowledge_reference.py:63`).
- Judgment: `_CURRENTLY_CAPTURE_ENABLED_SUBJECT_TARGET_TYPES = frozenset({DomainObjectType.KNOWLEDGE_REFERENCE, DomainObjectType.JUDGMENT})` (`capture_judgment.py:57–59`).

**Currently rejected target types** (raise `TargetTypeUnavailableError` via `_verify_target`/`_verify_subject`): for Knowledge Reference — Observation, Reasoning Trace, Judgment, Decision, Outcome; for Judgment — Observation, Reasoning Trace, Decision, Outcome.

**Repository, retrieval, and Case-ownership verification, per type** (re-run fresh, not reused from the prior audit):

| Type | `.get(id) -> T \| None` on its repository | `case_id: CaseId` field count on its entity | Repository construction available |
|---|---|---|---|
| Observation | ✅ (`observation/repository.py:20`) | 1 | ✅ `SqlAlchemyObservationRepository` |
| Knowledge Reference | ✅ (`knowledge_reference/repository.py:20`) | 1 | ✅ `SqlAlchemyKnowledgeReferenceRepository` |
| Judgment | ✅ (`judgment/repository.py:20`) | 1 | ✅ `SqlAlchemyJudgmentRepository` |
| Decision | ✅ (`decision/repository.py:22`) | 1 | ✅ `SqlAlchemyDecisionRepository` |
| Outcome | ✅ (`outcome/repository.py:20`) | 1 | ✅ `SqlAlchemyOutcomeRepository` |
| Reasoning Trace | — | — (no module exists: `find atlas -iname "*reasoning_trace*"` → empty) | — |

No discrepancy was found between this fresh verification and the prior audit's findings. Proceeding.

## 3. Governing Sources

- **OE-002 §5.2** (Knowledge Reference): "MAY reference any other Domain Object defined in this document that belongs to the same Case. No specific Domain Object type is required as its target; the target's type is unrestricted by this document."
- **OE-002 §5.4** (Judgment): "Where Judgment's subject is a reference, it MUST be to another same-Case Domain Object; no specific Domain Object type is required."
- **OE-004 INV-004** (Same-Case Reference): "Every semantic reference from one Domain Object to another MUST connect Domain Objects belonging to the same Case." **Does not require** any particular type to be referenced.
- **OE-004 INV-005** (Prior Acceptance): "A Domain Object MUST NOT reference another Domain Object that has not already been accepted." **Does not require** any specific target type — "the target's type is unconstrained by this invariant."
- **OE-004 INV-006** (Distinct Identity), **INV-014** (Knowledge Reference Single Target — "exactly one other Domain Object already accepted in the same Case," with no type restriction stated or implied).
- **OE-006 §5, §9, §16**: acceptance requires every applicable invariant to be *positively established*, not merely assumed; no "accepted with a deferred invariant" status exists. This is the exact bar both modules' own docstrings already cite as the reason for their present narrowness — re-confirmed here directly against the normative text, not taken on the docstrings' authority alone.

All five sources confirm: canonical target-type eligibility for both Knowledge Reference and Judgment has always been unconditional across all six adopted types. Nothing in this design changes that eligibility — it was never narrowed. Only *present capture availability*, an application-layer, present-state fact never governed by OE-002/OE-004/OE-006, changes.

## 4. Design Decision — Knowledge Reference

**Exactly which `DomainObjectType`s become accepted:** `OBSERVATION`, `JUDGMENT`, `DECISION`, `OUTCOME` are added to the existing `KNOWLEDGE_REFERENCE`. `REASONING_TRACE` is not added and remains rejected.

`_CURRENTLY_CAPTURE_ENABLED_TARGET_TYPES` becomes:
```python
_CURRENTLY_CAPTURE_ENABLED_TARGET_TYPES = frozenset({
    DomainObjectType.KNOWLEDGE_REFERENCE,
    DomainObjectType.OBSERVATION,
    DomainObjectType.JUDGMENT,
    DomainObjectType.DECISION,
    DomainObjectType.OUTCOME,
})
```

**Exactly how `_verify_target()` dispatch changes:** the existing two-step shape (gate check → existence check via the correct repository → same-Case check) is unchanged in structure. Only the routing step, currently a single `self._knowledge_references.get(...)` call, becomes a dispatch across five repositories keyed by `target_type` — the identical `if/elif` shape `_verify_subject()` in `capture_judgment.py` already uses today for its two currently-enabled types, extended from two branches to five:
```python
def _verify_target(self, *, case_id, target_type, target_id) -> None:
    if target_type not in _CURRENTLY_CAPTURE_ENABLED_TARGET_TYPES:
        raise TargetTypeUnavailableError(...)

    existing = _REPOSITORY_BY_TARGET_TYPE[target_type](self).get(_ID_BY_TARGET_TYPE[target_type](target_id))
    # or an equivalent explicit if/elif — the exact dispatch mechanics (dict-of-lambdas
    # vs. if/elif) are an implementation-task decision, not a design decision; either
    # is a mechanical extension of the existing pattern and neither changes behavior.

    if existing is None:
        raise TargetNotFoundError(...)
    if existing.case_id != case_id:
        raise CrossCaseTargetError(...)
```

**Exactly which repositories become constructor dependencies:** `KnowledgeReferenceService.__init__` gains four new parameters — `observation_repository: ObservationRepository`, `judgment_repository: JudgmentRepository`, `decision_repository: DecisionRepository`, `outcome_repository: OutcomeRepository` — alongside its existing `repository: KnowledgeReferenceRepository`. `JudgmentRepository` is included here because Judgment becomes a newly-accepted target type for Knowledge Reference in this design (Judgment was previously excluded for Knowledge Reference specifically — Judgment's own capture-availability gate already accepted Knowledge Reference and itself, but Knowledge Reference's gate had not yet been widened to accept Judgment; verified in Section 2's "currently rejected" list). **Where the concrete `JudgmentRepository` implementation is obtained from at the API dependency layer is not the same as at the constructor-signature level — see Section 6's import-cycle finding, which this exact addition creates and which Section 6 resolves.**

## 5. Design Decision — Judgment

**Exactly which `DomainObjectType`s become accepted:** `OBSERVATION`, `DECISION`, `OUTCOME` are added to the existing `KNOWLEDGE_REFERENCE`, `JUDGMENT`. `REASONING_TRACE` is not added and remains rejected.

`_CURRENTLY_CAPTURE_ENABLED_SUBJECT_TARGET_TYPES` becomes:
```python
_CURRENTLY_CAPTURE_ENABLED_SUBJECT_TARGET_TYPES = frozenset({
    DomainObjectType.KNOWLEDGE_REFERENCE,
    DomainObjectType.JUDGMENT,
    DomainObjectType.OBSERVATION,
    DomainObjectType.DECISION,
    DomainObjectType.OUTCOME,
})
```

**Exactly how `_verify_subject()` dispatch changes:** identical in kind to Knowledge Reference's own change above — the existing two-branch `if subject.target_type is DomainObjectType.JUDGMENT: ... else: ...` dispatch (currently: Judgment or Knowledge Reference) is extended to a five-branch dispatch (Judgment, Knowledge Reference, Observation, Decision, Outcome), each routing to its own repository's `.get()`. The gate check, the `TargetNotFoundError` check, and the `existing.case_id != case_id` check are structurally unchanged.

**Exactly which repositories become constructor dependencies:** `JudgmentService.__init__` gains three new parameters — `observation_repository: ObservationRepository`, `decision_repository: DecisionRepository`, `outcome_repository: OutcomeRepository` — alongside its existing `repository: JudgmentRepository` and `knowledge_reference_repository: KnowledgeReferenceRepository`.

## 6. Dependency Wiring — `get_outcome_repository`, and a Verified Import-Cycle Correction

**Definitive location: `atlas/core/infrastructure/api/knowledge_reference/dependencies.py`.**

**Why this location is preferred, verified directly against the existing composition pattern:**
- No `atlas/core/infrastructure/api/outcome/` module exists at all (confirmed fresh, Section 2) — Outcome has no REST API and this design does not give it one (Section 8). There is therefore no natural "home" module analogous to `decision/dependencies.py` or `observation/dependencies.py` where `get_outcome_repository` would sit as that Domain Object's own API composition root.
- The existing precedent for a shared-but-homeless dependency is `get_knowledge_reference_repository` itself: `judgment/dependencies.py` does not redefine it — it imports and reuses it directly from `knowledge_reference/dependencies.py` (`from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_knowledge_reference_repository`). Placing `get_outcome_repository` in the same file that already plays this "first consumer, shared provider" role keeps exactly one precedent, not two.
- `knowledge_reference/dependencies.py` already imports `get_decision_engine` (the single shared physical-engine provider every module reuses) — adding `get_outcome_repository` there requires no new import root:
```python
def get_outcome_repository(engine: Engine = Depends(get_decision_engine)) -> OutcomeRepository:
    create_outcome_table(engine)
    return SqlAlchemyOutcomeRepository(engine)
```

**A verified import-cycle defect this design must NOT introduce, and its resolution.** Section 4 requires `KnowledgeReferenceService` to gain a `JudgmentRepository` dependency. The naive way to obtain it — `knowledge_reference/dependencies.py` importing `get_judgment_repository` from `judgment/dependencies.py` — was checked directly against the current import graph and found to create a genuine two-way circular import, not a hypothetical one: `judgment/dependencies.py` already contains, at module top level, `from atlas.core.infrastructure.api.knowledge_reference.dependencies import (get_knowledge_reference_repository,)` (verified fresh, `judgment/dependencies.py:24-26`). If `knowledge_reference/dependencies.py` were to add a module-top-level `from atlas.core.infrastructure.api.judgment.dependencies import get_judgment_repository`, then whichever of the two modules Python loads first would, partway through its own top-level execution, trigger loading the other — which would in turn try to import a name from the first module before that name's `def` statement has executed, raising `ImportError: cannot import name ... from partially initialized module`. This is not avoidable by moving the import inside a function body, because FastAPI's `Depends(get_judgment_repository)` must appear as a parameter *default value*, which Python evaluates at `def`-statement execution time (module-load time) — a deferred, function-body-local import does not help here, unlike the general circular-import workaround.

**Resolution, consistent with "no new module, no repository abstraction, narrowest correct fix":** `knowledge_reference/dependencies.py` defines its own private, module-local repository-construction helper for this one purpose — not imported from `judgment/dependencies.py`, and not intended for reuse elsewhere:
```python
def _get_judgment_repository(engine: Engine = Depends(get_decision_engine)) -> JudgmentRepository:
    create_judgment_table(engine)
    return SqlAlchemyJudgmentRepository(engine)
```
This is a two-line duplication of `judgment/dependencies.py`'s own `get_judgment_repository` body — an accepted, minimal cost, not a new abstraction: it reuses the exact same underlying `create_judgment_table`/`SqlAlchemyJudgmentRepository` calls every other provider in this codebase already calls directly, just without importing the *wrapper function* across the one boundary that would cycle. The leading underscore signals this is `knowledge_reference/dependencies.py`'s own private helper, not a shared provider — `judgment/dependencies.py` continues to define and own the canonical, public `get_judgment_repository` for its own use, unchanged. This keeps the dependency graph strictly one-directional: `judgment/dependencies.py` imports from `knowledge_reference/dependencies.py` (as it already does today, now for two names instead of one); `knowledge_reference/dependencies.py` imports nothing from `judgment/dependencies.py`, in either direction, at any point.

**How both services reuse the resulting providers:**
- `knowledge_reference/dependencies.py`'s own `get_knowledge_reference_service` gains `observation_repository: ObservationRepository = Depends(get_observation_repository)` (imported from `observation/dependencies.py`, one-directional, no cycle — verified: `observation/dependencies.py` imports nothing from `knowledge_reference/dependencies.py`), `decision_repository: DecisionRepository = Depends(get_decision_repository)` (imported from `decision/dependencies.py`, one-directional, no cycle — verified: `decision/dependencies.py` imports nothing from `knowledge_reference/dependencies.py`), `judgment_repository: JudgmentRepository = Depends(_get_judgment_repository)` (the new private, local helper above), and `outcome_repository: OutcomeRepository = Depends(get_outcome_repository)` (the new local public provider above).
- `judgment/dependencies.py`'s own `get_judgment_service` gains `observation_repository: ObservationRepository = Depends(get_observation_repository)`, `decision_repository: DecisionRepository = Depends(get_decision_repository)` (both imported directly from their own home modules, exactly as `knowledge_reference/dependencies.py` does — no new dependency direction), and `outcome_repository: OutcomeRepository = Depends(get_outcome_repository)`, imported from `knowledge_reference/dependencies.py` exactly as it already imports `get_knowledge_reference_repository` from there today.

This is **not a new API**: Outcome gains zero routes, zero endpoints, zero schemas. It is a repository-construction helper reused inside two already-existing, already-mounted routers' own dependency graphs — the identical category of plumbing `observation/dependencies.py` already performs by reusing `decision`'s shared engine.

## 7. Explicit Exclusions — Verified Against This Design

| Excluded | Confirmed not touched by this design |
|---|---|
| Entities | `KnowledgeReference.capture()`/`Judgment.capture()` already accept a generic `TypedDomainObjectReference` for any `DomainObjectType` — verified unchanged in Section 2; no entity file is listed in Section 8's production inventory. |
| Value objects | Not listed in Section 8; no new value object is introduced. |
| Persistence | No table, column, or migration — every repository and table already exists and is unchanged. |
| Repositories | `ObservationRepository`, `DecisionRepository`, `OutcomeRepository`, `JudgmentRepository`, `KnowledgeReferenceRepository` Protocols are consumed exactly as already defined; none gains a new method. |
| Routers | Neither router's route definitions, path operations, or request/response wiring changes — only the `Depends(...)` chain behind an unchanged endpoint signature. |
| Schemas | `TypedDomainObjectReferenceSchema` (DO-IMP-002) already accepts all six enum values; `CreateKnowledgeReferenceRequest`/`CreateJudgmentRequest` are unchanged. |
| Orchestrators | Neither `KnowledgeReferenceService` nor `JudgmentService` is wired into any composite service or orchestrator today (verified fresh: `grep -rln "JudgmentService\|KnowledgeReferenceService" atlas/core/application/` outside their own modules → empty); this design does not wire them into one. |
| Ontology | OE-002 §5.2/§5.4 already state unrestricted target-type eligibility (Section 3) — nothing here is newly permitted at the ontological level. |
| Invariants | INV-004/INV-005/INV-006/INV-014 are applied exactly as already written, to more cases — no new invariant, no altered invariant. |
| Reasoning Trace | Remains in neither frozenset. Remains rejected via the identical `TargetTypeUnavailableError` path, for the identical reason (no repository exists). |

## 8. Expected Implementation Scope

**Production files (6 — corrected during audit from an initial 4; see the two additions' justification below):**
1. `atlas/core/application/knowledge_reference/capture_knowledge_reference.py` — widen frozenset; add four repository constructor parameters; extend `_verify_target` dispatch.
2. `atlas/core/application/judgment/capture_judgment.py` — widen frozenset; add three repository constructor parameters; extend `_verify_subject` dispatch.
3. `atlas/core/infrastructure/api/knowledge_reference/dependencies.py` — add `get_outcome_repository` and the private `_get_judgment_repository` (Section 6); extend `get_knowledge_reference_service` to inject four new repositories.
4. `atlas/core/infrastructure/api/judgment/dependencies.py` — extend `get_judgment_service` to inject three new repositories (reusing `get_observation_repository`, `get_decision_repository` directly, and `get_outcome_repository` imported from item 3).
5. **`atlas/core/domain/knowledge_reference/exceptions.py`** — `TargetTypeUnavailableError`'s own docstring currently states, as the reason for the type's unavailability, facts this exact package makes false (e.g., implicitly, via the module docstring it mirrors, that Observation/Decision/Outcome lack `case_id`). This docstring must be corrected to describe the new, narrower unavailability reason (Reasoning Trace only). This is a directly-forced, mechanical consequence of this package's own change — not unrelated cleanup — exactly the same category of correction already established as in-scope by the completed Outcome Case Context package's own Gap G4 (correcting a comment that becomes self-contradictory the moment the change lands).
6. **`atlas/core/domain/judgment/exceptions.py`** — `TargetTypeUnavailableError`'s own docstring explicitly states, verbatim: "Observation, Decision, and Outcome each lack a `case_id` today, so INV-004 cannot currently be established against any of them" — a direct factual claim this package makes false. Must be corrected for the identical reason as item 5. The docstring's separate claim about Reasoning Trace ("has no accepted-instance repository at all, so INV-005 is determinately violated") remains true and needs no change.

**Test files (4):**
1. `tests/unit/application/knowledge_reference/test_capture_knowledge_reference.py`
2. `tests/unit/infrastructure/api/knowledge_reference/test_router.py`
3. `tests/unit/application/judgment/test_capture_judgment.py`
4. `tests/unit/infrastructure/api/judgment/test_router.py`

**Mechanical expectation updates (not new tests — existing tests corrected to match the new gate; expanded during audit, since fresh inspection found the constructor-signature change forces far more than the tuple shrink alone):**
- Each file's `_CURRENTLY_UNAVAILABLE_TARGET_TYPES` tuple shrinks: Knowledge Reference's own (currently `OBSERVATION, REASONING_TRACE, JUDGMENT, DECISION, OUTCOME`) and Judgment's own (currently `OBSERVATION, REASONING_TRACE, DECISION, OUTCOME`) both shrink to `(REASONING_TRACE,)`. The existing `TestCanonicalButCurrentlyUnavailableTargetTypes` classes in all four files continue to exist, parametrized over the shrunk tuple — they are not deleted, since Reasoning Trace remains a genuine member of that category.
- **Both application-test files' own `repository`/`service` fixtures are a forced, universal change, not an optional one.** `tests/unit/application/knowledge_reference/test_capture_knowledge_reference.py`'s `repository` fixture currently creates only the Knowledge Reference table on its in-memory engine, and its `service` fixture constructs `KnowledgeReferenceService(repository)` with exactly one argument; `tests/unit/application/judgment/test_capture_judgment.py`'s equivalent fixtures currently construct exactly two repositories and call `JudgmentService(judgment_repository, knowledge_reference_repository)`. Once each `__init__` gains new, non-default parameters, both fixtures must create the newly-needed tables on the same shared in-memory engine, construct the newly-needed repositories, and pass all of them into the service constructor — otherwise **every existing test in both files** fails with `TypeError: missing required positional argument`, not merely the newly-added ones.
- **Both API-test files' own `context` fixture requires the identical expansion, for a distinct and more serious reason: test isolation, not just a `TypeError`.** Verified directly: `tests/unit/infrastructure/api/knowledge_reference/test_router.py`'s `context` fixture creates one in-memory engine, creates only the Knowledge Reference table on it, and overrides only `get_knowledge_reference_repository` via `app.dependency_overrides`; `tests/unit/infrastructure/api/judgment/test_router.py`'s equivalent fixture does the same for exactly its two current repositories. Once `get_knowledge_reference_service`/`get_judgment_service` depend on additional repository providers, any provider left un-overridden falls through to its real implementation — which resolves through `get_decision_engine`, the actual shared, `lru_cache`-backed, real `atlas.db`-file engine used in production. Left uncorrected, the newly-enabled capture paths in the API tests would silently read and write against the real database file instead of the isolated in-memory test engine. Both `context` fixtures must therefore create every newly-needed table on their own existing in-memory engine and add a `dependency_overrides` entry for every newly-injected provider (`get_observation_repository`, `get_decision_repository`, `get_outcome_repository`, and — for Knowledge Reference's fixture only — `get_judgment_repository`).
- **`tests/unit/application/knowledge_reference/test_capture_knowledge_reference.py`'s existing `TestServiceDependencySimplification.test_service_depends_only_on_its_own_repository` requires deliberate, explicit handling, not a silent break or a thoughtless deletion.** This test asserts, via `inspect.signature(KnowledgeReferenceService.__init__)`, that the parameter list is exactly `["self", "repository"]` — a direct, load-bearing lock on the "dependency simplification" performed by the already-completed `Knowledge-Reference-Pre-Commit-Architecture-Review.md` Outcome 2 correction (referenced in the class's own name). This design necessarily and knowingly reverses that simplification: the widened service depends on five repositories, not one, because cross-type reference validation genuinely requires it. The implementation task must rewrite this test's assertion to reflect the new signature (or, if judged clearer, replace the assertion with one stating the new, complete parameter list) — it must not be left to fail silently, and must not be deleted without acknowledging that it is intentionally reversing a previously locked-in decision, for a verified, stated reason (this design's own Section 4/5). No equivalent test exists in `test_capture_judgment.py` (confirmed by fresh grep — Judgment's own dependency count was never asserted this way), so no analogous correction is needed there.

**Behavioral tests (new, per newly-enabled type × per service, mirroring the already-existing `TestPriorAcceptance`/`TestSameCase`/success-path classes verbatim):**
- For each of Observation, Judgment (Knowledge-Reference-side only, since Judgment already accepts itself), Decision, Outcome as a Knowledge Reference target: successful capture; `TargetNotFoundError` when the target does not exist; `CrossCaseTargetError` when it belongs to a different Case.
- For each of Observation, Decision, Outcome as a Judgment subject: the same three behaviors.
- At the API layer (both `test_router.py` files): the same three behaviors exercised through the live router/dependency chain, mirroring the existing `TestCreateKnowledgeReferenceRequest`/`TestCreateJudgmentReferentialFormAgainstKnowledgeReference`-style classes already present.

**Regression scope:** `tests/unit/application/knowledge_reference`, `tests/unit/application/judgment`, `tests/unit/infrastructure/api/knowledge_reference`, `tests/unit/infrastructure/api/judgment`, plus the full suite (current baseline: 8099 passed, 3 skipped, 0 failed, 0 errors). No other package's own tests construct `KnowledgeReferenceService`/`JudgmentService` (verified fresh, Section 7), so no other test file is expected to require any change.

**Documentation:** none.

## 9. Design Verification

- **No new ontology is introduced.** OE-002 §5.2/§5.4 already license every target type this design enables (Section 3); nothing is newly permitted that was not always canonically eligible.
- **No new API is introduced.** Zero new routes, endpoints, or schemas anywhere, including for Outcome (Section 6).
- **No persistence change.** Every table and repository already exists, unchanged, and already round-trips `case_id` correctly (established by the completed Case Context packages).
- **No migration.** Nothing about existing stored data changes.
- **No Case Context work.** This design consumes the completed Case Context work; it does not repeat, extend, or revisit it.
- **This design simply activates already-supported Domain Object types whose prerequisites now exist** — every mechanism used (the gate frozenset, the `_verify_target`/`_verify_subject` dispatch, `TargetNotFoundError`/`CrossCaseTargetError`/`TargetTypeUnavailableError`, the shared-engine dependency-provider pattern) already exists in the codebase today, applied to more cases than before.
- **No import cycle is introduced.** Verified directly against the current import graph (Section 6): the one genuine risk found (`knowledge_reference/dependencies.py` needing a `JudgmentRepository`, while `judgment/dependencies.py` already imports from `knowledge_reference/dependencies.py`) is resolved by a private, module-local helper rather than a cross-import, keeping the dependency direction strictly one-way exactly as it is today.

## 10. Implementation Boundary

**This document does not authorize implementation by existing.** Producing or committing this design does not constitute approval to modify any file listed in Section 8. A separate, explicit implementation task is required.

**This design explicitly prohibits, and any implementation task working from it must not perform:**
- Adding Reasoning Trace as an accepted target type in either frozenset, under any circumstance — it remains blocked by the absence of a repository, not by this design's choice, and nothing in this package changes that fact.
- Introducing any repository abstraction, base class, generic dispatcher class, or `Protocol`-level change beyond the five already-existing, already-typed repository Protocols consumed as-is.
- Any opportunistic cleanup: renaming existing fields, reordering existing tests, correcting unrelated stale comments (e.g., the Case entity's own mildly-dated phrasing noted in the prior audit), or touching any file not listed in Section 8.
- Expanding scope to wire `KnowledgeReferenceService` or `JudgmentService` into any orchestrator, conversation flow, or Core Loop step — no such wiring is requested, needed, or in scope here.
- Treating this document's own worked dispatch-code sketches (Section 4) as mandatory literal implementation — the exact dispatch mechanics (an `if/elif` chain vs. a dict keyed by `DomainObjectType`) are an implementation-task's own choice; only the *set of accepted types* and *which repository each type routes to* are design decisions fixed by this document.

## Baseline Execution Record

`git status --short` at the start of this design task: clean. HEAD: `60b681dba9f819b49e106075ab4de0698747666e`, branch `main`. Repository-fact verification (Section 2) used static inspection (`grep`, direct file reads), not test execution.

**Baseline test run, performed during the subsequent audit-and-commit pass over this document:** `tests/unit/application/knowledge_reference`, `tests/unit/infrastructure/api/knowledge_reference`, `tests/unit/application/judgment`, `tests/unit/infrastructure/api/judgment` — **99 passed, 0 failed, 0 errors, 0 skipped.** Confirms the currently-narrow gates are fully green today, exactly as expected: the gap this design closes is one of unrealized availability, not of any failing behavior.
