# API-004 — Hypothesis Capture

**Status:** Implemented, pending review.
**Scope:** Preserve what an investor believed might be true before that belief becomes evidence, a decision, or an outcome. `Hypothesis` is a fully independent, immutable aggregate — no relationship to Observation, Decision, DecisionContext, or Evidence.
**Depends on:** nothing. Verified by grep in both import directions, the same standard applied to API-003.

---

## 1. Purpose

A Hypothesis captures the investor's provisional interpretation of
reality — "what do I believe this may mean?" It is deliberately **not**:

- an Observation (a raw, pre-interpretation fact the investor noticed),
- Evidence (a later, assembled artifact),
- a Decision (a committed course of action),
- an Outcome,
- a truth claim,
- an Atlas-generated conclusion.

Atlas assigns no truth value, confidence, or conviction to a Hypothesis.
A changed belief is represented by capturing a brand-new Hypothesis, never
by editing an existing one.

## 2. Observation vs. Hypothesis

The two aggregates are easy to conflate because both are investor-authored
free text captured before a Decision exists. The distinction that matters:

| | Observation (API-003) | Hypothesis (API-004) |
|---|---|---|
| Answers | "What did I notice?" | "What might this mean?" |
| Nature | A fact, pre-interpretation | A provisional interpretation |
| Example | "Several semiconductor companies raised capex guidance." | "Demand for AI infrastructure may be accelerating faster than the market expects." |
| Timestamp field | `observed_at` | `formulated_at` |

This distinction is enforced only through documentation and UX — the
domain performs **no semantic validation** of whether a `Statement`
"sounds like" a hypothesis rather than an observation. The API preserves
the investor's own wording verbatim (beyond stripping surrounding
whitespace), exactly as instructed.

## 3. Folder and Package Structure

Hypothesis is added as a new, standalone bounded context — a sibling to
`decision`, `decision_context`, and `observation`, not nested inside any
of them:

```
atlas/core/
  domain/
    decision/                      # API-001 — untouched
    decision_context/               # API-002 — untouched
    observation/                    # API-003 — untouched
    hypothesis/                     # API-004 — new
      value_objects.py             # HypothesisId, Statement
      entity.py                    # Hypothesis aggregate
      exceptions.py
      repository.py                # interface only
  application/
    decision/                      # API-001 — untouched
    decision_context/               # API-002 — untouched
    observation/                    # API-003 — untouched
    hypothesis/                     # API-004 — new
      capture_hypothesis.py
  infrastructure/
    persistence/
      decision/                    # API-001 — untouched
      decision_context/             # API-002 — untouched
      observation/                  # API-003 — untouched
      hypothesis/                   # API-004 — new
        table.py
        sqlalchemy_repository.py
    api/
      app.py                       # composition root — updated, additively only
      decision/                    # API-001 — untouched
      decision_context/             # API-002 — untouched
      observation/                  # API-003 — untouched
      hypothesis/                   # API-004 — new
        schemas.py
        router.py
        dependencies.py
        errors.py

tests/unit/
  domain/hypothesis/
  application/hypothesis/
  infrastructure/persistence/hypothesis/
  infrastructure/api/hypothesis/
```

The only file this increment touches outside `hypothesis/`'s own subtree
is [`atlas/core/infrastructure/api/app.py`](../atlas/core/infrastructure/api/app.py) —
a pure addition (two import lines, one `include_router`, one
`register_error_handlers` call), confirmed by diff.

## 4. Aggregate and Value-Object Rationale

[`atlas/core/domain/hypothesis/entity.py`](../atlas/core/domain/hypothesis/entity.py) —
`Hypothesis`, a frozen dataclass:

| Field | Required | Rule |
|---|---|---|
| `id` | yes | fresh `HypothesisId`, assigned once at capture |
| `statement` | yes | `Statement` — non-empty after stripping whitespace |
| `formulated_at` | yes | timezone-aware `datetime`, **preserved exactly as given** |
| `recorded_at` | yes | Atlas's own UTC clock, assigned once at capture |
| `note` | no | plain `str \| None` — blank/whitespace normalizes to `None` |

[`atlas/core/domain/hypothesis/value_objects.py`](../atlas/core/domain/hypothesis/value_objects.py):

- **`Statement`** performs only a non-empty-after-strip check — the same
  minimal validation pattern as `Observation.Statement`,
  `DecisionContext.Situation`, and `Decision.InvestmentCase`. No linguistic
  or semantic check of any kind is applied, per §2 and per the spec's own
  explicit instruction not to attempt to validate whether the text "sounds
  like" a hypothesis.
- **`HypothesisId`** is the same UUID-wrapper pattern as `DecisionId`,
  `ContextId`, and `ObservationId` (`default_factory=uuid.uuid4`).

There is no `Hypothesis`-specific `Subject` value object. Unlike
Observation, the spec defines no subject/topic field for Hypothesis —
only `Statement`, `FormulatedAt`, `RecordedAt`, and the optional `Note`.
Nothing was added beyond what §"Required Fields"/"Optional Fields"
specify.

**The same offset-preservation asymmetry as Observation and
DecisionContext:** `formulated_at` is **not** normalized to UTC.
`_validated_formulated_at` only checks the value is a timezone-aware
`datetime`; it never calls `.astimezone(timezone.utc)`. This matches
`Observation.observed_at` and `DecisionContext.captured_at` exactly, and
for the same reason: it is the investor's own account of *when they
formed the belief*, not a value Atlas is free to renormalize.
`recorded_at`, being Atlas's own system clock, stays UTC.

## 5. Explicitly Excluded Fields

Per the spec, none of the following exist anywhere in this aggregate,
its persistence, or its API: `Confidence`, `Conviction`, `Probability`,
`Uncertainty score`, `Truth status`, `Validation status`, `Supporting
evidence`, `Opposing evidence`, `Source`, `Tags`, `Category`, `Owner
type`, `GeneratedBy`, `Model confidence`. These are explicitly deferred
to future, separate domain decisions — not omitted by oversight.

## 6. Core Domain Decision, As Implemented

- `Hypothesis` is a fully standalone aggregate. It holds no reference to
  `Decision`, `DecisionContext`, `Observation`, or `Evidence`, and none of
  those hold a reference to it. There is no `ObservationId`, `DecisionId`,
  `EvidenceId`, foreign key, graph edge, or compatibility layer anywhere
  in this increment.
- Verified structurally, not just by omission: `grep -r` across
  `atlas/core/domain/hypothesis/`, `atlas/core/application/hypothesis/`,
  and `atlas/core/infrastructure/persistence/hypothesis/` found zero
  imports of `decision`, `decision_context`, or `observation` modules.
  The reverse search (those modules referencing `hypothesis`) also
  returned nothing: `app.py`'s additive wiring is the sole integration
  point between this bounded context and the rest of the system.

## 7. Legacy Naming Collision Check

Before writing any code, the repository was inspected for existing
classes, enums, tables, or modules named `Hypothesis`:

- `grep -rn "class Hypothesis\|Hypothesis("` across the entire repository
  returned **no matches** — no class, no table, no enum member.
- The only textual mentions of the word "Hypothesis" found were: a string
  literal in `tests/test_evidence_assembly_v1_sprint281.py`'s
  `INFORMATION_TYPES` list (a documentation-consistency test asserting the
  word appears in a doc, not a domain type), and a docstring reference in
  `atlas/core/domain/observation/entity.py` (an explanatory mention of the
  concept, not an import).

**Conclusion: no legacy naming collision exists.** Unlike API-003 (which
found a genuine bare-name collision with `atlas.domains.decision.models.
Observation`), this increment required no stop-and-report step and no
Future Backlog entry for a naming conflict.

## 8. Persistence Design

[`atlas/core/infrastructure/persistence/hypothesis/`](../atlas/core/infrastructure/persistence/hypothesis/) —
a new `hypotheses` table, own `MetaData()` (not shared with `decisions`,
`decision_contexts`, or `observations`), same reasoning as prior
increments: separate schema lifecycle for a separate bounded context,
same physical `atlas.db` file via the same shared engine (reused
read-only from `decision`'s dependencies module).

| Column | Notes |
|---|---|
| `hypothesis_id` | primary key |
| `statement` | text, not null |
| `note` | nullable text |
| `formulated_at` | ISO-8601 text, offset preserved exactly |
| `recorded_at` | ISO-8601 text, always UTC |

Exactly the five columns the spec lists — nothing added.

**No foreign keys, asserted by a structural test** (matching API-003's
convention): `tests/unit/infrastructure/persistence/hypothesis/` inspects
`hypotheses_table`'s column set and `foreign_keys` attribute directly,
and a separate test confirms `decisions`, `decision_contexts`, and
`observations` tables are byte-for-byte unchanged in column shape.

**A genuine, non-obvious design decision — chronological ordering across
mixed timezone offsets.** The spec requires `list_all()` to return
Hypotheses ordered by `formulated_at` ascending (then `recorded_at`, then
`hypothesis_id` as tie-breaker). Because `formulated_at` preserves its
original offset rather than being normalized to UTC, a plain SQL
`ORDER BY` on the stored ISO-8601 *text* column would **not** produce
correct chronological order: e.g. `"2026-03-01T10:00:00+05:00"` sorts
lexicographically *after* `"2026-03-01T06:00:00+00:00"` even though the
first instant is earlier in absolute time. `SqlAlchemyHypothesisRepository.
list_all()` fetches all rows and sorts them in Python using the
constructed `Hypothesis` objects' tz-aware `datetime` values — which
compare by true absolute instant regardless of stored offset — rather
than relying on the database to sort the text representation. This is
covered by a dedicated test
(`test_chronological_order_compares_true_instant_across_mixed_offsets`)
that constructs two timestamps with different offsets representing
different instants and confirms the correct absolute ordering, not the
lexicographic one.

No Alembic, same standing product decision as prior increments: a
genuinely new table with no prior schema to migrate is exactly the case
Alembic is deferred past.

## 9. Application Behavior

[`atlas/core/application/hypothesis/capture_hypothesis.py`](../atlas/core/application/hypothesis/capture_hypothesis.py) —
`HypothesisService` implements all three use cases the spec asks for
directly (unlike API-003, where `capture` was the only application-layer
service and `get`/`list_all` were done straight against the repository
from the router):

- `capture(request)` — constructs and persists a new `Hypothesis`.
- `get(hypothesis_id)` — returns the matching `Hypothesis`, or raises
  `HypothesisNotFoundError` if none exists (mirroring the
  `DecisionNotFoundError` pattern from API-002: a missing reference, not a
  malformed value, and deliberately not a `HypothesisValidationError`).
- `list_all()` — delegates directly to the repository, which already
  returns the correct chronological order (§8).

RecordedAt is assigned through the same injectable-clock pattern used by
`Observation.capture()` and `DecisionContext.capture()` — a `clock`
keyword parameter on the aggregate's `capture()` classmethod, defaulting
to `datetime.now(timezone.utc)`.

## 10. API Contract

```
POST /hypotheses          201 Created
GET  /hypotheses           200 OK   (list, chronological — formulated_at asc)
GET  /hypotheses/{id}      200 OK, or 404
```

**Example request:**

```json
POST /hypotheses
{
  "statement": "Demand for AI infrastructure may be accelerating faster than the market expects.",
  "note": "Revisit after the next reporting cycle.",
  "formulatedAt": "2026-07-13T18:30:00+02:00"
}
```

**Example response (201):**

```json
{
  "hypothesisId": "78ef9fb2-...-...-...-...",
  "statement": "Demand for AI infrastructure may be accelerating faster than the market expects.",
  "note": "Revisit after the next reporting cycle.",
  "formulatedAt": "2026-07-13T18:30:00+02:00",
  "recordedAt": "2026-07-13T19:30:13.234401Z"
}
```

Confirmed by a live `uvicorn` smoke test against exactly this payload
shape: `formulatedAt`'s offset round-trips unchanged, and `recordedAt` is
Atlas's own UTC timestamp, rendered with a `Z` suffix by pydantic v2's
default JSON encoding — the same behavior already observed and documented
in API-003.

**ID format:** the spec's illustrative example uses a prefixed identifier
style (`"hyp_01J..."`). Implemented as a plain UUID instead, matching
every other aggregate's identity scheme (`DecisionId`, `ContextId`,
`ObservationId`) — the same reasoning API-002 used for not adopting its
own spec's illustrative `ctx_01J.../dec_01J...` example literally: the
example wasn't read as a mandate to change the approved baseline's
identity scheme.

| Failure | Status | Body |
|---|---|---|
| Blank or whitespace-only `statement` | 400 | `{"detail": "Statement.value must not be empty"}` |
| Missing `formulatedAt`, or malformed request shape entirely | 422 | FastAPI's default — the domain's own `InvalidFormulatedAtError` is never reached for a field that's absent or fails pydantic's own datetime parsing |
| Unknown `hypothesis_id` on `GET /hypotheses/{id}` | 404 | `{"detail": "No Hypothesis found with id ..."}` |

No `PATCH`, no `PUT`, no `DELETE`, no filtering, no search, no
pagination — matches "insert-only" and the explicit non-goals list
literally; there is no code path that could perform any of them.

**On the spec's "error code equivalent to INVALID_HYPOTHESIS":** this is
realized as the `HypothesisValidationError` exception class itself (and
its more specific subclasses, `MissingStatementError` /
`InvalidFormulatedAtError`) mapping to HTTP 400 — not as an added `code`
field on the JSON response body. Every other Atlas core endpoint returns
the plain `{"detail": "<message>"}` shape, and the spec explicitly says
not to redesign the repository-wide error contract in this increment;
adding a new `code` field would itself be exactly that redesign. This
interpretation is a disclosed judgment call, not a silent one — see §14.

**Casing convention, built camelCase-first:** like API-003, this
increment's schemas
([`schemas.py`](../atlas/core/infrastructure/api/hypothesis/schemas.py))
subclass the shared `CamelModel` directly. `populate_by_name=True` means
a snake_case request body (`formulated_at`) is still accepted, verified
by a dedicated backward-compatibility test.

## 11. Sequence Diagram — `POST /hypotheses`

```
Investor      Router      HypothesisService   HypothesisRepository   SQLite
   |             |                |                     |               |
   |--POST------>|                |                     |               |
   |  {statement,|--Request------>|                     |               |
   |   note,     |                |--Statement(...)                     |
   |   ...}      |                |   [blank -> raise MissingStatementError -> 400]
   |             |                |--Hypothesis.capture()                |
   |             |                |   (validates FormulatedAt;           |
   |             |                |    normalizes blank note to None;    |
   |             |                |    assigns id + recorded_at)         |
   |             |                |--add(hypothesis)-------------------->|
   |             |                |                                      |--INSERT-->|
   |             |                |<--ok---------------------------------|           |
   |<--201 + Hypothesis -----------|                                                  |
```

No other aggregate or repository appears in this flow — the entire path
from request to persistence touches only `Hypothesis`'s own bounded
context.

## 12. Test Summary

55 new tests, regression-clean against the existing suite:

- **Domain (22 tests):** [`tests/unit/domain/hypothesis/`](../tests/unit/domain/hypothesis/)
  — `HypothesisId` and `Statement` value-object validation, aggregate
  creation via `capture()`, `formulated_at` offset-preservation vs.
  `recorded_at` UTC, missing/naive `formulated_at` rejection, blank `note`
  normalizing to `None`, meaningful `note` stripped but preserved,
  immutability.
- **Application (6 tests):** [`tests/unit/application/hypothesis/`](../tests/unit/application/hypothesis/)
  — capture, `recorded_at` assigned by Atlas's clock, retrieve by id,
  unknown id raises `HypothesisNotFoundError`, multiple Hypotheses
  returned in chronological order, empty list when nothing captured. Runs
  against a real (in-memory) SQLite repository, not a fake.
- **Persistence (14 tests):** [`tests/unit/infrastructure/persistence/hypothesis/`](../tests/unit/infrastructure/persistence/hypothesis/)
  — create/persist/read/round-trip-equals-original, insert-only
  (no `update`/`delete` method exists), `formulated_at`'s exact offset
  round-tripping unchanged, chronological ordering by `formulated_at`
  ascending, the mixed-offset true-instant ordering case (§8), tie-break
  ordering by `recorded_at` then `hypothesis_id`, a structural no-foreign-
  keys check, and a check that `decisions`/`decision_contexts`/
  `observations` tables are unchanged.
- **API (13 tests):** [`tests/unit/infrastructure/api/hypothesis/`](../tests/unit/infrastructure/api/hypothesis/)
  — POST success (camelCase response shape, optional-note omission),
  blank-note-normalizes-to-`None` at the HTTP layer, snake_case request
  backward compatibility, two validation-failure scenarios (400 for blank/
  empty statement, 422 for missing/malformed `formulatedAt`), GET list
  (empty and populated), GET by id (found and 404).

**Regression:** API-001, API-002, and API-003 test modules were run in
isolation and all **188 pass unchanged** (matching the pre-API-004 count
exactly: 131 for API-001/002 + 57 for API-003). A live `uvicorn` smoke
test additionally confirmed `GET /decisions` and `GET /observations`
still return 200 alongside working `POST/GET /hypotheses` calls in the
same running app. Full repository suite: **7,154 passed, 3 skipped**
(7,099 pre-existing + 55 new). Scoped lint (`atlas/core`, `tests/unit`):
clean. Whole-repo `ruff check .` count unchanged at 1,202 pre-existing
findings.

## 13. Architectural Decisions

1. **No legacy naming collision existed, so none was reported or
   deferred.** The mandatory pre-implementation scan (§7) found only
   incidental string matches, not a genuine class/table/enum conflict —
   a materially different outcome from API-003's `Observation` collision,
   worth stating explicitly rather than silently proceeding without
   showing the check was done.
2. **Chronological ordering by `formulated_at` is computed in Python, not
   SQL, because the column preserves arbitrary offsets.** This is the one
   place this increment required real engineering judgment beyond
   copying API-003's pattern forward — a naive port of Observation's
   `ORDER BY recorded_at` (always UTC, always safe to sort as text) would
   have silently produced wrong results here.
3. **The application service owns `get`/`list_all`, not just `capture`,**
   per this increment's own explicit instruction — a deliberate divergence
   from API-003's application layer, which left retrieval to the router
   talking to the repository directly.
4. **"Error code equivalent to INVALID_HYPOTHESIS" is realized via the
   exception class, not a new JSON field**, to honor the spec's own
   "do not redesign the repository-wide error contract" constraint over
   its more general "use an error code" phrasing. Disclosed here and in
   the final delivery report, not resolved silently.
5. **No `Subject`-equivalent value object was added.** The spec's
   Required/Optional field lists define no subject/topic concept for
   Hypothesis — only `Statement`. Nothing was invented to parallel
   Observation's `Subject`.

## 14. Genuine Risks / Unresolved Questions

- **The INVALID_HYPOTHESIS "error code" instruction was interpreted, not
  implemented literally** (§10, §13.4) — if a future increment or client
  integration expects a machine-readable `code` field in the response
  body, this increment does not provide one. Flagged for explicit
  Product Owner confirmation before any future increment builds against
  an assumed `code` field.
- **400 vs. 422 boundary is uneven, same category already on record for
  API-002/API-003:** a domain-rejected value (blank statement) is 400; a
  missing field entirely is 422. Flagged, not fixed, per the instruction
  not to touch shared error-handling behavior to chase full consistency.
- **In-Python sort of `list_all()` is O(n log n) in application memory,**
  not delegated to the database. For the current insert-only, no-filter,
  no-pagination scope this is a non-issue; it would need revisiting if a
  future increment adds pagination against a large Hypothesis table.
- **Reused engine dependency (`get_decision_engine`) is a read-only
  cross-module import**, the same coupling point already flagged in
  API-003's documentation — worth naming again here since a fourth
  bounded context now depends on it.

## 15. Future Backlog

No Future Backlog item is required for a naming collision — none exists
(§7).

**Architecture Review outcome (API-004, approved):** the
`HypothesisValidationError`-to-400 implementation with no added `code`
field is accepted as final for this increment, not merely deferred. A
shared, structured Error Contract — covering both a real `code` field
across all Atlas core error responses and the existing 400-vs-422
inconsistency (API-002/API-003/API-004) — is confirmed as its own future
Product Increment, out of scope for API-001 through API-004.

**New backlog item, raised during API-004 review:** replace the brittle
hard-coded test-count assertion (`README.md`'s "7,041 tests pass..." line
and `tests/test_release_candidate.py::test_readme_mentions_current_test_count`,
which asserts the literal string `"7,041"`) with a stable release-readiness
check that doesn't require a documentation edit on every increment that
adds tests. This count has already drifted twice — the real full-suite
count is 7,154 as of this increment — without the assertion failing,
because the test only checks for one specific hard-coded substring rather
than verifying the actual invariant it's meant to protect (that the
documented count isn't stale). Acknowledged during this review; explicitly
not fixed as part of API-004 — a candidate for its own small future
Product Increment.
