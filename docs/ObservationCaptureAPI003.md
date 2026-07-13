# API-003 — Observation Capture

**Status:** Implemented, pending review.
**Scope:** Preserve an investor's observations before they become hypotheses, evidence, or decisions. `Observation` is a fully independent, immutable aggregate — no relationship to `Decision`, `DecisionContext`, `Hypothesis`, or `Evidence`.
**Depends on:** nothing. This is the point of the increment — verified by grep, not just by design intent (§3).

---

## 1. Folder and Package Structure

Observation is added as a new, standalone bounded context — a sibling to
`decision` and `decision_context`, not nested inside either:

```
atlas/core/
  domain/
    decision/                      # API-001 — untouched
    decision_context/               # API-002 — untouched
    observation/                    # API-003 — new
      value_objects.py             # ObservationId, Subject, Statement
      entity.py                    # Observation aggregate
      exceptions.py
      repository.py                # interface only
  application/
    decision/                      # API-001 — untouched
    decision_context/               # API-002 — untouched
    observation/                    # API-003 — new
      capture_observation.py
  infrastructure/
    persistence/
      decision/                    # API-001 — untouched
      decision_context/             # API-002 — untouched
      observation/                  # API-003 — new
        table.py
        sqlalchemy_repository.py
    api/
      app.py                       # composition root — updated, additively only
      decision/                    # API-001 — untouched
      decision_context/             # API-002 — untouched
      observation/                  # API-003 — new
        schemas.py
        router.py
        dependencies.py
        errors.py

tests/unit/
  domain/observation/
  application/observation/
  infrastructure/persistence/observation/
  infrastructure/api/observation/
```

**Why a sibling, not a subfolder of anything else:** the spec is explicit
that Observation introduces no relationship to any existing aggregate.
Nesting it under `decision/` or `decision_context/` would visually suggest
a dependency that doesn't exist. `app.py` is the *only* file this increment
touches outside `observation/`'s own subtree, and that touch is a pure
addition (three import lines, one `include_router`, one
`register_error_handlers` call — see the diff quoted in §3).

## 2. Aggregate and Value-Object Rationale

[`atlas/core/domain/observation/entity.py`](../atlas/core/domain/observation/entity.py) —
`Observation`, a frozen dataclass:

| Field | Required | Rule |
|---|---|---|
| `id` | yes | fresh `ObservationId`, assigned once at capture |
| `subject` | yes | `Subject` — non-empty after stripping whitespace |
| `statement` | yes | `Statement` — non-empty after stripping whitespace |
| `observed_at` | yes | timezone-aware `datetime`, **preserved exactly as given** |
| `recorded_at` | yes | Atlas's own UTC clock, assigned once at capture |
| `source` | no | plain `str \| None` — blank/whitespace normalizes to `None` |
| `note` | no | plain `str \| None` — blank/whitespace normalizes to `None` |

[`atlas/core/domain/observation/value_objects.py`](../atlas/core/domain/observation/value_objects.py):

- **`Subject`** is deliberately its own value object, *not* a reuse of
  `atlas.domains.decision.models`' or API-001's `Subject`. The spec
  explicitly forbids any relationship to Decision, and this Subject is
  broader in practice — "US interest rates" or "My portfolio liquidity",
  not necessarily a ticker. Same reasoning API-001/002 already used for
  keeping structurally-identical concepts as distinct types
  (`AlternativesConsidered`/`Uncertainties`, `DecisionId`/`UserId`).
- **`Statement`** mirrors the same non-empty-after-strip pattern as
  `Subject`, `Situation` (API-002), and `InvestmentCase` (API-001) — a
  factual description of what was noticed, not an interpretation.
- **`ObservationId`** is the same UUID-wrapper pattern as `DecisionId` and
  `ContextId` (`default_factory=uuid.uuid4`).

**The one behavioral asymmetry, carried forward from API-002's precedent:**
`observed_at` is **not** normalized to UTC. `_validated_observed_at` only
checks the value is a timezone-aware `datetime`; it never calls
`.astimezone(timezone.utc)`. This matches `DecisionContext.captured_at`
exactly, and for the same reason: it is the investor's own account of
*when they noticed something*, not a value Atlas is free to renormalize.
`recorded_at`, being Atlas's own system clock, stays UTC — consistent with
`Decision.recorded_at` and `DecisionContext.recorded_at`.

**New in this increment — blank-normalizes-to-`None`:** `source` and
`note` are optional context. Rather than rejecting `""`/whitespace-only
input outright (as `Subject`/`Statement` do) or storing it verbatim, both
fields pass through `_normalize_blank()` in `Observation.__post_init__`,
which strips and collapses blank input to `None`. This is a literal
reading of the spec's own invariant list, distinct from how API-002 left
`portfolio_relevance`/`capital_considerations` completely unvalidated —
API-003's spec asked for normalization specifically, so that's what was
built, without extending the same treatment to those API-002 fields
retroactively.

## 3. Core Domain Decision, As Implemented — and the Naming Collision

- `Observation` is a fully standalone aggregate. It holds no reference to
  `Decision`, `DecisionContext`, `Hypothesis`, or `Evidence`, and none of
  those hold a reference to it. `ObservationRepository` has no foreign key
  and no cross-repository dependency.
- Verified structurally, not just by omission: `grep -r` across
  `atlas/core/domain/observation/` and `atlas/core/application/observation/`
  found zero imports of `decision` or `decision_context` modules (one
  explanatory docstring *mentions* the legacy class by name — see below —
  which is not a functional import). The reverse search (`decision`/
  `decision_context` referencing `observation`) also returned nothing:
  `app.py`'s additive wiring is the sole integration point between this
  bounded context and the rest of the system.

**Naming collision, reported and resolved before implementation began:**
`atlas.domains.decision.models` already defines a class named
`Observation` — an unrelated, differently-scoped concept (an
evidence-derived reasoning output, part of a different pipeline) that
happens to share the exact bare name with this increment's aggregate root.
This was flagged as a genuine architectural conflict per the spec's own
instruction to stop and report before writing code. The Product Owner's
resolution, applied literally:

- Treat it as a **non-blocking legacy naming collision**.
- Do **not** rename or modify `atlas.domains.decision.models.Observation`.
- Implement API-003's `Observation` entirely within the new
  `atlas/core/domain/observation/` bounded context — no compatibility
  layer, no refactor, no shared base class.
- **Record it as a Future Backlog item** for a later architecture
  consolidation increment (§10).

No code was written to bridge, alias, or disambiguate the two classes.
They are distinguished only by their fully-qualified module path
(`atlas.domains.decision.models.Observation` vs.
`atlas.core.domain.observation.entity.Observation`) — the same kind of
namespace collision already on record for `DecisionType`/`Observation`-
adjacent legacy names elsewhere in the codebase (see
[ArchitectureConsolidation.md](ArchitectureConsolidation.md)).

## 4. Persistence Design

[`atlas/core/infrastructure/persistence/observation/`](../atlas/core/infrastructure/persistence/observation/) —
a new `observations` table, own `MetaData()` (not shared with `decisions`
or `decision_contexts`), same reasoning as API-001/002: separate schema
lifecycle for a separate bounded context, same physical `atlas.db` file
via the same shared engine (reused read-only from `decision`'s
dependencies module, per §5).

| Column | Notes |
|---|---|
| `observation_id` | primary key |
| `subject` | text, not null |
| `statement` | text, not null |
| `source` | nullable text |
| `note` | nullable text |
| `observed_at` | ISO-8601 text, offset preserved exactly |
| `recorded_at` | ISO-8601 text, always UTC |

**No foreign keys, deliberately.** Unlike `decision_contexts.decision_id`
(which is `UNIQUE` and references `decisions`), `observations` has no
column referencing any other table — there is no cross-aggregate
invariant to enforce, because the spec introduces none. This absence is
asserted directly by a structural test
(`tests/unit/infrastructure/persistence/observation/`) that inspects the
table's column set for foreign-key constraints, rather than relying on
nobody adding one later.

No Alembic, same standing product decision as API-001/002: a genuinely
new table with no prior schema to migrate is exactly the case Alembic is
deferred past.

## 5. API Contract

```
POST /observations       201 Created
GET  /observations        200 OK   (list, oldest RecordedAt first)
GET  /observations/{id}   200 OK, or 404
```

**Example request:**

```json
POST /observations
{
  "subject": "Semiconductor sector",
  "statement": "Several semiconductor companies raised capital expenditure guidance during the same reporting period.",
  "source": "Quarterly earnings reports",
  "note": "Follow whether equipment suppliers report the same pattern.",
  "observedAt": "2026-07-13T10:30:00+02:00"
}
```

**Example response (201):**

```json
{
  "observationId": "3fa2c1e0-...-...-...-...",
  "subject": "Semiconductor sector",
  "statement": "Several semiconductor companies raised capital expenditure guidance during the same reporting period.",
  "source": "Quarterly earnings reports",
  "note": "Follow whether equipment suppliers report the same pattern.",
  "observedAt": "2026-07-13T10:30:00+02:00",
  "recordedAt": "2026-07-13T18:45:42.652738Z"
}
```

Confirmed by a live `uvicorn` smoke test against exactly this payload
shape: the offset on `observedAt` round-trips unchanged, and `recordedAt`
is Atlas's own UTC timestamp — pydantic v2's default JSON encoding
renders a UTC-aware `datetime` with a `Z` suffix with no extra code
required, matching this format precisely.

| Failure | Status | Body |
|---|---|---|
| Blank `subject` or `statement` | 400 | `{"detail": "<domain message>"}` |
| Missing `observedAt`, or malformed request shape entirely | 422 | FastAPI's default — the domain's own `InvalidObservedAtError` is never reached for a field that's absent or fails pydantic's own datetime parsing |
| Unknown `observation_id` on `GET /observations/{id}` | 404 | `{"detail": "Observation not found"}` |

No `PATCH`, no `DELETE`, no update path anywhere — matches "insert-only"
literally; there is no code path that could perform either.

**Casing and status-code conventions, applied from the start, not
retrofitted:** unlike API-001 (originally snake_case, migrated by
ADR-004) and API-002 (originally its own local `_CamelModel`, later
consolidated), API-003's schemas
([`schemas.py`](../atlas/core/infrastructure/api/observation/schemas.py))
subclass the shared `atlas.core.infrastructure.api.serialization.CamelModel`
directly — this is the first increment built entirely after ADR-004
existed, so there was no interim snake_case period to migrate away from.
Status code for domain validation failures is `400`
([`errors.py`](../atlas/core/infrastructure/api/observation/errors.py)),
matching API-002's convention rather than API-001's `422` — per the
spec's own instruction, an intentional, disclosed inconsistency, not a
new one invented here.

## 6. Sequence Diagram — `POST /observations`

```
Investor      Router      CaptureObservationService   ObservationRepository   SQLite
   |             |                     |                          |               |
   |--POST------>|                     |                          |               |
   |  {subject,  |--Request---------->|                          |               |
   |   statement,|                     |--Subject(...)                            |
   |   ...}      |                     |--Statement(...)                          |
   |             |                     |   [blank -> raise *ValidationError -> 400]|
   |             |                     |--Observation.capture()                   |
   |             |                     |   (validates ObservedAt;                 |
   |             |                     |    normalizes blank source/note to None; |
   |             |                     |    assigns id + recorded_at)             |
   |             |                     |--add(observation)------------------------>|
   |             |                     |                                          |--INSERT-->|
   |             |                     |<--ok--------------------------------------|           |
   |<--201 + Observation ---------------|                                                       |
```

No other aggregate or repository appears in this flow — the entire path
from request to persistence touches only `Observation`'s own bounded
context, which is the structural guarantee behind "introduces no
relationship to Decision, DecisionContext, Hypothesis, or Evidence."

## 7. Test Summary

57 new tests, regression-clean against the existing suite:

- **Domain (31 tests):** [`tests/unit/domain/observation/`](../tests/unit/domain/observation/)
  — value object validation (`Subject`, `Statement`, `ObservationId`),
  aggregate creation via `capture()`, `observed_at` offset-preservation vs.
  `recorded_at` UTC, missing/naive `observed_at` rejection, blank
  `source`/`note` normalizing to `None`, meaningful `source`/`note` stripped
  but preserved, immutability.
- **Application (4 tests):** [`tests/unit/application/observation/`](../tests/unit/application/observation/)
  — capture with all fields, capture with optional fields omitted, blank
  optional fields normalize to `None` through the service, no
  cross-repository calls are made (single repository only).
- **Persistence (10 tests):** [`tests/unit/infrastructure/persistence/observation/`](../tests/unit/infrastructure/persistence/observation/)
  — create/persist/read/round-trip-equals-original against a real
  (in-memory) SQLite database, `observed_at`'s exact offset round-tripping
  unchanged, `list_all` ordering, and a structural check that the table
  defines no foreign-key columns.
- **API (12 tests):** [`tests/unit/infrastructure/api/observation/`](../tests/unit/infrastructure/api/observation/)
  — POST success (camelCase response shape, optional-field omission),
  blank-optional-fields-normalize-to-`None` at the HTTP layer, three
  validation-failure scenarios (400 for blank subject/statement, 422 for
  missing/malformed `observedAt`), GET list (empty and populated), GET by
  id (found and 404).

**Regression:** API-001 and API-002 test modules were run in isolation
and all 131 pass unchanged (matching the pre-API-003 count exactly). A
live `uvicorn` smoke test additionally confirmed `GET /decisions` still
returns `200 []` alongside working `POST/GET /observations` calls in the
same running app. Full repository suite: **7,099 passed, 3 skipped**
(7,042 pre-existing + 57 new).

## 8. Architectural Decisions

1. **Observation is verified standalone, not just declared standalone.**
   Both directions of import were grep-checked (`observation` importing
   `decision`/`decision_context`, and the reverse) rather than trusting
   folder placement alone to guarantee decoupling.
2. **No foreign keys, asserted by a structural test.** The absence of a
   cross-aggregate relationship is enforced the same way API-001 enforces
   "no update method exists" — by testing for the absence, not merely by
   not writing the code.
3. **The legacy `Observation` naming collision is recorded, not resolved.**
   Per explicit Product Owner instruction: no rename, no compatibility
   layer, no refactor in this increment. The two classes coexist under
   different fully-qualified paths, disambiguated only by their module
   path, until a future consolidation increment addresses it.
4. **Built camelCase-first, not migrated.** Because ADR-004 existed before
   this increment started, `schemas.py` subclasses `CamelModel` from day
   one — there was never a snake_case version of this API to migrate away
   from, unlike API-001 and API-002.
5. **Blank-normalizes-to-`None` is scoped to `source`/`note` only,** per
   this spec's own invariants — not retroactively applied to API-002's
   similarly free-text `portfolio_relevance`/`capital_considerations`,
   which remain a separate, already-flagged open question (see
   [DecisionContextAPI002.md §10](DecisionContextAPI002.md)).

## 9. Genuine Risks / Unresolved Questions

- **Legacy naming collision remains unresolved by design** (§3, §10) —
  `atlas.domains.decision.models.Observation` and
  `atlas.core.domain.observation.entity.Observation` are both live,
  identically-named classes with opposite meanings (a reasoning-pipeline
  output vs. raw pre-interpretation input). Any future work that imports
  `Observation` without a fully-qualified path or a very deliberate import
  alias risks importing the wrong one silently — there is no compiler or
  linter rule currently guarding against this.
- **400 vs. 422 boundary is uneven, same category as API-002's** (§5): a
  domain-rejected value (blank subject) is 400; a missing field entirely
  is 422. Flagged, not fixed, per the instruction not to touch shared
  error-handling behavior to chase full consistency across increments.
- **No test exercises concurrent inserts** — unlike `decision_contexts`,
  `observations` has no uniqueness constraint to race against, so this is
  a smaller concern here than it was for API-002, but it's also untested
  for the same synchronous-test-client reason.
- **Reused engine dependency (`get_decision_engine`) is a read-only
  cross-module import**, not a shared abstraction — if API-001's
  dependency function signature changes in a future increment,
  `observation/dependencies.py` would need a matching update. This is the
  same pattern API-003 was told to use (share the physical database, not
  the schema), just worth naming as a coupling point to watch.

## 10. Future Backlog

- **Architecture consolidation: resolve the `Observation` naming
  collision.** `atlas.domains.decision.models.Observation` (legacy,
  evidence-derived reasoning output) and
  `atlas.core.domain.observation.entity.Observation` (API-003, raw
  investor-noticed input) share an identical bare class name with
  materially different meanings. A future increment should decide whether
  to rename the legacy class, rename this one, or formally document the
  disambiguation rule — out of scope for this increment per explicit
  Product Owner instruction ("no compatibility layer or refactoring is
  required in this Product Increment").
