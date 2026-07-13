# API-002 — Decision Context

**Status:** Implemented, pending review.
**Scope:** Record the circumstances surrounding an existing Decision — a separate, immutable aggregate referencing a `DecisionId`. No authentication, no live portfolio integration, no market data, no reflections, no outcomes.
**Depends on:** [API-001 — Decision Capture](DecisionCaptureAPI001.md), whose behavior is unchanged by this increment.

---

## 1. Folder and Package Structure

Decision Context is added as a sibling bounded context to Decision, at every
layer, following exactly the shape API-001 established:

```
atlas/core/
  domain/
    decision/                      # API-001 — untouched
    decision_context/               # API-002 — new
      value_objects.py             # ContextId, Situation, AlternativesConsidered, Uncertainties
      entity.py                    # DecisionContext aggregate
      exceptions.py
      repository.py                # interface only
  application/
    decision/                      # API-001 — untouched
    decision_context/               # API-002 — new
      capture_decision_context.py
  infrastructure/
    persistence/
      decision/                    # API-001 — untouched
      decision_context/             # API-002 — new
        table.py
        sqlalchemy_repository.py
    api/
      app.py                       # composition root — updated, additively
      decision/                    # API-001 — untouched
      decision_context/             # API-002 — new
        schemas.py
        router.py
        dependencies.py
        errors.py

tests/unit/
  domain/decision_context/
  application/decision_context/                 # new test category this increment
  infrastructure/persistence/decision_context/
  infrastructure/api/decision_context/
```

**Why a sibling, not a subfolder of `decision/`:** the Core Domain Decision
in the spec is explicit — DecisionContext is "a separate immutable
aggregate," not a part of Decision. Nesting it inside `domain/decision/`
would visually suggest ownership or coupling that doesn't exist. The two
packages share only `DecisionId` (imported from `decision.value_objects`,
not redefined) — a deliberate, minimal reference, not a shared kernel of
behavior.

**New test category — `tests/unit/application/`:** API-001 never needed
this folder, because its only cross-cutting logic (translate primitives →
aggregate → persist) had no branching worth testing in isolation from the
API layer. API-002's application service has real branching logic — decision
must exist, context must not already exist — that spans two repositories
and is exactly what deserves a direct, non-HTTP test.

## 2. Aggregate and Value-Object Rationale

[`atlas/core/domain/decision_context/entity.py`](../atlas/core/domain/decision_context/entity.py) —
`DecisionContext`, a frozen dataclass:

| Field | Required | Rule |
|---|---|---|
| `context_id` | yes | fresh `ContextId`, assigned once at capture |
| `decision_id` | yes | API-001's `DecisionId` — reused, not redefined |
| `situation` | yes | `Situation` — non-empty after stripping whitespace |
| `captured_at` | yes | timezone-aware `datetime`, **preserved exactly as given** |
| `recorded_at` | yes | Atlas's own UTC clock, assigned once at capture |
| `portfolio_relevance` | no | plain `str \| None` — no validation, see §6 |
| `capital_considerations` | no | plain `str \| None` — no validation, see §6 |
| `alternatives_considered` | no | `AlternativesConsidered` — ordered, may be empty, no empty items |
| `uncertainties` | no | `Uncertainties` — ordered, may be empty, no empty items |

[`atlas/core/domain/decision_context/value_objects.py`](../atlas/core/domain/decision_context/value_objects.py):

- **`Situation`** mirrors API-001's `InvestmentCase`/`Subject` pattern
  exactly: non-empty after `.strip()`, its own `MissingSituationError`.
- **`AlternativesConsidered` / `Uncertainties`** are two distinct frozen
  dataclasses wrapping `tuple[str, ...]`, not one generic "list of strings"
  type. They're structurally identical and share a validation helper
  (`_validated_items`), but kept as separate classes so the type system
  still catches "alternatives passed where uncertainties expected" — the
  same reasoning API-001 used for keeping `DecisionId`/`UserId` distinct
  despite both wrapping a `uuid.UUID`.
- **`ContextId`** is `DecisionId`'s pattern copied exactly (UUID wrapper,
  `default_factory=uuid.uuid4`).

**The one deliberate asymmetry with API-001:** `captured_at` is **not**
normalised to UTC the way `Decision.decided_at` is. `_validated_captured_at`
only checks the value is a timezone-aware `datetime` — it never calls
`.astimezone(timezone.utc)`. This is a direct reading of the spec's own
Persistence test requirement ("chronological timestamps retain timezone
information") and its worked example, where the response echoes back the
exact `+02:00` offset from the request. `recorded_at`, being Atlas's own
system clock rather than investor-supplied data, stays UTC — consistent
with `Decision.recorded_at`.

## 3. Core Domain Decision, As Implemented

- `DecisionContext` is a separate aggregate. `Decision` (API-001) was not
  touched — no new fields, no new methods, no changed invariants.
- The cross-aggregate rules ("must reference an existing Decision," "at
  most one context per Decision") are enforced by the **application
  service**, not by either aggregate reaching into the other. Neither
  aggregate holds a reference to a repository or to the other's internals.
- Capturing context only ever **reads** from `DecisionRepository` (`.get(...)`)
  — it is never given a way to call anything that would mutate a Decision,
  because no such method exists on `Decision` or its repository interface.
  Invariant 7 ("must not modify the referenced Decision") is therefore
  enforced by the absence of a mutation path, the same structural argument
  API-001 used for "Decision History is immutable."

## 4. Persistence Design

[`atlas/core/infrastructure/persistence/decision_context/`](../atlas/core/infrastructure/persistence/decision_context/) —
a new `decision_contexts` table, own `MetaData()` (not shared with
`decisions`), same reasoning as API-001: separate schema lifecycle for a
separate bounded context, same physical `atlas.db` file via the same
shared engine.

| Column | Notes |
|---|---|
| `context_id` | primary key |
| `decision_id` | **`UNIQUE`, indexed** — enforces "at most one context per Decision" at the database level, not only in the application service |
| `situation` | text |
| `portfolio_relevance`, `capital_considerations` | nullable text |
| `alternatives_considered`, `uncertainties` | JSON-encoded text (a single ordered list has no natural relational shape simpler than JSON for a V1 slice with no query/filter requirement on list contents) |
| `captured_at`, `recorded_at` | ISO-8601 text, same reasoning as API-001 (SQLite has no native tz-aware datetime type) |

**The UNIQUE constraint is deliberate defense in depth, not speculation.**
The application service already checks for an existing context before
calling `add()`; the database constraint is what makes that check
race-safe, and it's exactly what invariant 3 asks for ("at most one"), not
an invented extra. When the constraint is violated, `SqlAlchemyDecisionContextRepository.add()`
catches SQLAlchemy's `IntegrityError` and re-raises the domain's own
`DuplicateDecisionContextError` — infrastructure exceptions never leak past
this module.

No Alembic. Per the standing product decision, this local-development
`create-if-not-exists` table doesn't trigger it — a genuinely new table with
no prior schema to migrate is exactly the case Alembic is deferred past.

## 5. API Contract

```
POST /decisions/{decision_id}/context   201 Created
GET  /decisions/{decision_id}/context   200 OK
```

| Failure | Status | Body |
|---|---|---|
| Decision does not exist | 404 | `{"detail": "No Decision found with id ..."}` |
| Context already exists | 409 | `{"detail": "DecisionContext already exists for Decision ..."}` |
| Situation blank / alternative or uncertainty item blank | 400 | `{"detail": "<domain message>"}` |
| Malformed request shape (missing field, wrong type) | 422 | FastAPI's default — unchanged from API-001 |

No `GET /decisions/{id}/context` list, no `PATCH`, no `DELETE` — matches
"There is: no UPDATE, no DELETE, no replacement of existing context"
literally; there is no code path that could perform any of them.

**Two deliberate divergences from API-001's conventions, both directly
requested by this spec, neither touching API-001 itself:**

1. **JSON casing.** The spec's example request/response uses camelCase
   (`portfolioRelevance`, `capturedAt`, `contextId`). API-001's endpoints
   are snake_case. Implemented literally via pydantic's `to_camel` alias
   generator (`schemas.py`) — the Python-side attribute names stay
   snake_case, only the wire format changes. The two endpoints now speak
   different JSON conventions; see §7.
2. **Status code for invalid content.** The spec calls for `400`, where
   API-001 uses `422` for the equivalent case. Implemented via a **new**
   exception handler registered only for `DecisionContextValidationError`
   (`decision_context/errors.py`) — API-001's existing `DecisionValidationError`/`ValueError`
   handlers (`decision/errors.py`, both still 422) are completely
   untouched. The one gap this leaves: a malformed request *shape* (e.g. a
   missing `situation` field entirely) still returns FastAPI's default 422,
   not 400 — only domain-raised validation failures (blank `situation`, an
   empty item in a list) get the spec's 400. Overriding FastAPI's global
   `RequestValidationError` handler to return 400 for this router alone
   would require path-sniffing inside a handler shared by both endpoints,
   which risks changing API-001's malformed-request behavior too. Kept
   narrow and scoped rather than reaching for that.

**ID format:** `ContextId` and `decisionId` are plain UUIDs, matching
API-001's `DecisionId`, not the `ctx_01J.../dec_01J...` prefixed style
shown in the spec's illustrative example — the example wasn't read as a
mandate to change the approved baseline's identity scheme.

## 6. What Was Deliberately Left Unvalidated

`portfolio_relevance` and `capital_considerations` are plain `str | None`
with **no** non-empty check, unlike `situation`. This mirrors exactly how
`Subject` was treated in API-001 before its Architecture Review promotion:
the spec's own Invariants list (items 1–7) validates `situation`,
`alternatives_considered`, and `uncertainties` explicitly, and says nothing
about these two "Optional Fields." Implemented literally — no invented
constraint. If a future review wants `""` rejected here the way `Subject`
was later tightened, that's a small, contained change to two fields, not a
restructure.

## 7. Sequence Diagram — `POST /decisions/{decision_id}/context`

```
Investor      Router      CaptureDecisionContextService   DecisionRepository   DecisionContextRepository   SQLite
   |             |                     |                          |                      |                   |
   |--POST------>|                     |                          |                      |                   |
   |  {situation, |--Request---------->|                          |                      |                   |
   |   ...}      |                     |--get(decision_id)------->|                      |                   |
   |             |                     |<--Decision or None-------|                      |                   |
   |             |                     |   [None -> raise DecisionNotFoundError -> 404]   |                   |
   |             |                     |--get_by_decision_id----------------------------->|                   |
   |             |                     |<--DecisionContext or None-----------------------|                   |
   |             |                     |   [found -> raise DuplicateDecisionContextError -> 409]              |
   |             |                     |--DecisionContext.capture()                       |                   |
   |             |                     |   (validates Situation, Alternatives,            |                   |
   |             |                     |    Uncertainties, CapturedAt;                    |                   |
   |             |                     |    assigns context_id + recorded_at)             |                   |
   |             |                     |--add(context)------------------------------------>|                   |
   |             |                     |                                                    |--INSERT--------->|
   |             |                     |                                                    |   (decision_id    |
   |             |                     |                                                    |    UNIQUE)        |
   |             |                     |<--ok----------------------------------------------|                   |
   |<--201 + DecisionContext ----------|                                                                        |
```

Note the `DecisionRepository` is only ever read (`get`), never written to —
the structural guarantee behind invariant 7.

## 8. Test Summary

55 new tests, regression-clean against the existing suite:

- **Domain (51 tests):** [`tests/unit/domain/decision_context/`](../tests/unit/domain/decision_context/)
  — value object validation (`Situation`, `AlternativesConsidered`,
  `Uncertainties`, `ContextId`), aggregate creation, `captured_at`
  offset-preservation vs. `recorded_at` UTC (the key behavioral difference
  from API-001), missing/naive `captured_at`, immutability, empty
  collections allowed, empty *items within* a collection rejected.
- **Application (4 tests):** [`tests/unit/application/decision_context/`](../tests/unit/application/decision_context/)
  — context attaches to an existing Decision; a nonexistent Decision is
  rejected; a duplicate context is rejected; capturing context does not
  modify the Decision (asserted by re-reading the Decision from its
  repository before and after).
- **Persistence (9 tests):** [`tests/unit/infrastructure/persistence/decision_context/`](../tests/unit/infrastructure/persistence/decision_context/)
  — create/persist/read/round-trip-equals-original against a real
  (in-memory) SQLite database, the database-level UNIQUE constraint
  translated to `DuplicateDecisionContextError`, `captured_at`'s exact
  offset round-tripping unchanged.
- **API (11 tests):** [`tests/unit/infrastructure/api/decision_context/`](../tests/unit/infrastructure/api/decision_context/)
  — POST success (including camelCase response shape and optional-field
  omission), three validation-failure scenarios (400), unknown Decision
  (404), duplicate (409), GET success, GET with no context yet (404), GET
  for an unknown Decision (404).

**Regression:** the pre-existing API-001 test modules
(`tests/unit/domain/decision/`, `tests/unit/infrastructure/persistence/decision/`,
`tests/unit/infrastructure/api/decision/`) were run in isolation and all 75
pass unchanged. Full repository suite: 7,041 passed, 3 skipped (6,986
pre-existing + 55 new).

## 9. Architectural Decisions

1. **Cross-aggregate invariants live in the application service, not in
   either aggregate.** `Decision` and `DecisionContext` remain fully
   decoupled at the domain layer — neither imports the other's repository
   or has a method that reaches across. `CaptureDecisionContextService`
   is the one place that knows about both, which is exactly what an
   application service is for.
2. **`AlternativesConsidered` and `Uncertainties` are distinct types**
   despite identical shape, for the same reason `DecisionId`/`UserId`
   stayed distinct in API-001 — type safety across conceptually different
   domain concepts is worth two small classes plus one shared helper
   function, not worth collapsing into one generic list type.
3. **The database UNIQUE constraint on `decision_id` is not speculative.**
   It implements invariant 3 literally ("at most one DecisionContext"); the
   application-layer check alone would leave a race window under
   concurrent requests, which is exactly what a database constraint is for.
4. **`captured_at` intentionally does not follow `decided_at`'s
   UTC-normalisation precedent.** This was the one place this increment
   consciously diverges from an established API-001 pattern rather than
   copying it forward — justified directly by the spec's own persistence
   test requirement and worked example, not by preference.

## 10. Genuine Risks / Unresolved Questions

- **JSON casing is now inconsistent across the two live endpoints**
  (§5.1). Not a defect in either increment individually — a cumulative
  cross-increment consistency question worth a decision before API-003,
  one way or the other.
- **400 vs. 422 boundary is a little uneven** (§5.2): a domain-rejected
  value (blank situation) is 400; a missing field entirely is 422. Both
  are "invalid context" from the caller's point of view but produce
  different codes. Flagged, not fixed, per the instruction not to touch
  API-001's global error handling to chase full consistency.
- **`portfolio_relevance` / `capital_considerations` are unvalidated free
  text** (§6) — same category of open question API-001's `Subject` was
  in before its promotion. Worth a conscious decision either way before
  it's built upon.
- **No test exercises two DecisionContext-shaped requests racing
  concurrently** against the UNIQUE constraint (SQLite + the synchronous
  test client make this hard to observe meaningfully); the constraint's
  correctness rests on standard relational-database guarantees rather
  than an empirical concurrency test.
