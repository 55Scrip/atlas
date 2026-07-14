# ATLAS-009 — Reflection Response

**Status:** Implemented, pending review.
**Scope:** Lets an investor explicitly, voluntarily preserve their verbatim response to one Decision Coach question — the first concept in the Understanding lineage (Decision Timeline, Pattern, Strategy Signature, Decision Reflection, Decision Coach) whose purpose is to persist rather than remain ephemeral.
**Depends on:** ATLAS-009-D's authoritative Reflection Response definition, and `DecisionReflection`/`CoachingQuestion` (ATLAS-007/008), read but never modified.

---

## 1. Purpose

Decision Coach's ephemeral response (ATLAS-008) is discarded by design.
Reflection Response gives the investor an explicit, optional way to
override that default and keep their own words — not because Atlas
needs them, but because the investor decided something they said was
worth having on record. This is the first genuinely new persistence
surface in this lineage since API-005.

## 2. Two Prerequisite-Style Corrections Made Before Implementation

1. **`ResponseText` stores the investor's text unmodified.** Unlike
   `Subject`/`InvestmentCase`/`Statement` elsewhere in this codebase,
   which strip and store the stripped value, `ResponseText` checks
   `value.strip()` only to reject empty/whitespace-only input — the
   stored value is never reassigned. Validation must not become
   transformation (ATLAS-009-D invariant 10).
2. **The provenance snapshot captures `reflection.description` itself**,
   verbatim, alongside the structural Pattern/Signature membership data
   — the exact sentence the investor read, not a reconstruction from
   structured fields, immune to any future change in how those fields'
   own description templates are worded.

## 3. Reflection Response Domain Model

```python
@dataclass(frozen=True)
class PatternMembershipSnapshot:
    strategy_name: str
    member_decision_ids: tuple[DecisionId, ...]

@dataclass(frozen=True)
class ProvenanceSnapshot:
    reflection_description: str
    coaching_question_text: str
    grounding_pattern: PatternMembershipSnapshot
    strategy_signature_patterns: tuple[PatternMembershipSnapshot, ...]
    reasoning_context_subject: str | None
    reasoning_context_decision_type: str | None
    reasoning_context_confidence: int | None

@dataclass(frozen=True)
class ReflectionResponse:
    id: ReflectionResponseId
    decision_id: DecisionId
    response_text: ResponseText
    provenance: ProvenanceSnapshot
    recorded_at: datetime
```

`decision_id` is the only durable-identity reference this aggregate
holds — valid because a Decision, once recorded, never changes. Every
other field is a snapshot of plain values (strings, ints, tuples of
`DecisionId`) copied at the moment of capture — never a reference to
`RecognizedPattern`/`RecognizedStrategySignature`/`DecisionReflection`/
`CoachingQuestion`, all of which are ephemeral and may never be
recomputed identically again.

## 4. Provisional-State Model

```python
@dataclass(frozen=True)
class ProvisionalReflectionResponse:
    response_text: str  # raw, exactly as typed
    provenance: ProvenanceSnapshot
```

Held only in a local variable inside `conversation/cli.py`'s own loop —
never on `ConversationSession`. Real in that the investor made a
genuine choice, but not yet a lasting domain fact, because there is no
`decision_id` to anchor it to yet. Becomes durable only at the exact
transition to `ConversationStep.DECISION_RECORDED`; discarded, with no
separate cleanup step, if that transition never happens.

## 5. Explicit Preservation-Choice Flow

Extends ATLAS-008's ephemeral-response step without touching
`decision_coach/` at all:

1. (Unchanged) Reflection shown, Coach's question shown, one
   `input_fn("> ")` reads the response text.
2. If empty, stop — nothing further asked, nothing preserved.
3. If non-empty, a second, separate, explicit — and deliberately
   mechanical, not a coaching question — save/discard question is asked;
   a small local keyword parser (`reflection_response/preservation_choice.py`,
   mirroring `conversation/prompts.py`'s own pattern without touching
   that file) resolves the answer.
4. Only on an explicit "yes" is a `ProvisionalReflectionResponse`
   constructed, with a `ProvenanceSnapshot` built from the
   `reflection`/`coaching_question`/`context` objects already in scope.

## 6. Decision-Capture Commit Boundary

Verified directly against `conversation/orchestrator.py`: Decision
capture succeeds exactly when `session.current_step` transitions to
`ConversationStep.DECISION_RECORDED` — fully observable from outside,
no orchestrator change needed. **Decision capture and Reflection
Response capture are two separate writes, not one transaction** — this
cannot be made atomic without modifying `CommitDecisionFromConclusionService`,
which this increment preserves unchanged. The second write is attempted
immediately after the first succeeds, in the same loop iteration.

## 7. Failure and Abandonment Behavior

- Declining at either point: nothing constructed, nothing persisted.
- Confidence capture fails and is re-asked: the provisional response
  simply stays held until capture eventually succeeds or the
  conversation ends.
- Abandonment before `DECISION_RECORDED`: the local variable is
  discarded when `run()` exits — no durable record was ever created.
- **Decision capture succeeds, but the Reflection Response write
  fails:** the recorded Decision is completely unaffected (it already
  committed independently); no `ReflectionResponse` exists; the CLI
  prints an explicit, honest line — *"Your decision was recorded, but
  the response you chose to keep could not be saved."* — never silently
  swallowed; no retry, no duplicate-write attempt, no rollback of the
  Decision.

## 8. Persistence and Read-Isolation Boundary

New domain aggregate, following this codebase's established
three-layer convention exactly (`atlas/core/domain/reflection_response/`,
`atlas/core/infrastructure/persistence/reflection_response/`,
`atlas/core/application/reflection_response/`), mirroring
`decision/table.py`'s own style — own `MetaData`, `String`/`Integer`
columns, string-serialized ids/datetimes. The two variable-length
nested provenance fields (`grounding_pattern`,
`strategy_signature_patterns`) are JSON-encoded text columns — an
infrastructure-layer detail only; the domain model itself stays
strongly typed.

`ReflectionResponseRepository`/`CaptureReflectionResponseService` are
constructed only inside `reflection_response/composition.py` and
`conversation/cli.py` — verified by a test asserting none of
`pattern_recognition`, `strategy_signature`, `decision_reflection`, or
`decision_coach`'s own composition/coach modules import anything from
`reflection_response/`.

**Retrieval is explicitly out of scope** — this increment is
capture-only, per ATLAS-009-D §13/§15.

## 9. Folder Structure

```
atlas/core/domain/reflection_response/
    entity.py, value_objects.py, repository.py, exceptions.py

atlas/core/infrastructure/persistence/reflection_response/
    table.py, sqlalchemy_repository.py

atlas/core/application/reflection_response/
    provisional_response.py, capture_reflection_response.py,
    preservation_choice.py, composition.py

tests/unit/domain/reflection_response/
tests/unit/infrastructure/persistence/reflection_response/
tests/unit/application/reflection_response/
```

One disclosed touch to `conversation/cli.py` — its **fourth**
(ATLAS-003, ATLAS-007, ATLAS-008, now this). `decision_coach/coach.py`
and `CommitDecisionFromConclusionService` are untouched.

## 10. Test Summary

32 new tests, regression-clean:

- **`test_value_objects.py`** (14) — `ResponseText` preserves leading/
  trailing whitespace, casing, punctuation, and internal multiple
  spacing exactly; rejects empty/whitespace-only input via `.strip()`
  checks that never mutate the stored value; `ProvenanceSnapshot`
  validation.
- **`test_entity.py`** (4) — `register()` construction, fresh ids,
  clock-sourced `recorded_at`, immutability.
- **`test_sqlalchemy_repository.py`** (4) — round-trip `add`/`get`,
  including verbatim text and JSON-encoded nested fields.
- **`test_capture_reflection_response.py`** (4) — `build_provenance_snapshot`
  captures `reflection.description` and every constituent Signature
  Pattern; proves the snapshot never holds a `RecognizedPattern`
  instance; `CaptureReflectionResponseService` persists correctly.
- **`test_reflection_response_integration.py`** (6) — explicit yes
  persists, explicit no persists nothing, an empty ephemeral response
  never even asks the preservation question; abandonment before
  Decision capture persists nothing; the partial-failure case (Decision
  valid, no Reflection Response, honest message, no crash); read
  isolation from every other capability's own composition/coach module.
- **`test_decision_reflection_integration.py`** (updated) — the
  ATLAS-007/008 tests updated for `_maybe_reflect_and_coach`'s new
  signature and second `input_fn` call.
- **Manual verification:** the ATLAS-007/008 three-conversation
  scenario, extended with a real preservation choice including
  deliberately awkward whitespace/punctuation — confirmed byte-for-byte
  verbatim storage, correct Decision anchoring, and correct provenance
  via direct database query.

**Regression:** full repository suite: **7,644 passed, 3 skipped**
(7,612 pre-existing + 32 new). Scoped lint: clean. Whole-repo `ruff
check .` count unchanged at 1,202. `git diff --stat` confirms the only
existing files touched are `conversation/cli.py` and the pre-existing
ATLAS-007/008 test file (updated for the new function signature) —
everything else purely additive.

## 11. Architectural Decisions

1. **No normalization on `ResponseText`** — the one value object in
   this codebase where validation must not become transformation.
2. **`reflection.description` captured verbatim**, distinct from and in
   addition to structural Pattern/Signature membership data.
3. **Two separate, non-atomic writes**, with the second write's failure
   handled by honest reporting rather than a shared transaction that
   would require modifying `CommitDecisionFromConclusionService`.
4. **A CLI-level check on `session.current_step is DECISION_RECORDED`**,
   never a hook inside `ConversationOrchestrator` — the Core Loop stays
   fully untouched.
5. **An explicit, separate save/discard question**, not inferred from
   whether the investor typed anything.
6. **JSON-encoded columns for variable-length nested provenance data**
   — the smallest adequate serialization for write-once, read-isolated
   content.

## 12. Anything That Feels Overengineered

Nothing. The domain aggregate mirrors existing conventions exactly; the
CLI integration is five straightforward lines beyond ATLAS-008's own.

## 13. What Can Be Simplified

Nothing further at this stage.

## 14. Genuine Risks / Unresolved Questions

- **The two writes are not atomic** — a real, disclosed failure window
  exists between Decision commit and Reflection Response write,
  explicitly handled rather than hidden.
- **No retrieval surface exists yet** — explicitly authorized limitation
  (ATLAS-009-D §13/§15); the investor cannot yet see what they preserved
  through any dedicated interface.
- **A second explicit input turn is added** whenever the investor types
  a non-empty ephemeral response — a real, disclosed change to the
  conversation's input shape.
- **`conversation/cli.py` has now been touched four times** — still
  additive each time, worth continuing to name explicitly.
- **JSON-encoded columns are not queryable by SQL** — acceptable given
  the read-isolation boundary; nothing needs to filter on them.
- **No authentication** — same placeholder-identity gap disclosed in
  every prior increment.

## 15. Future Backlog

- A retrieval interface letting the investor read their own preserved
  Reflection Responses — explicitly permitted by ATLAS-009-D §13/§15,
  deferred to its own increment.
- Extending confidence-grounded correspondence once ATLAS-007's own
  second integration point exists.
- Carried forward, unaffected by this increment: re-evaluating
  `reasoning_link`'s placement and permanence, a REST API layer for the
  Core Loop, the shared structured Error Contract, the brittle
  hard-coded test-count assertion in `README.md`/`tests/test_release_candidate.py`.
- **Recommendation for the next sprint:** design the retrieval interface
  ATLAS-009-D §13/§15 explicitly anticipates — its own domain question
  (what does an investor "looking back" at their preserved Reflection
  Responses represent?) has not yet been asked.
