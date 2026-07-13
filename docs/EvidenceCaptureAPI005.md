# API-005 — Evidence Capture

**Status:** Implemented, pending review.
**Scope:** Preserve information the investor considered supportive of or challenging to a line of reasoning. `Evidence` is a fully independent, immutable aggregate — no relationship to Hypothesis, Observation, Decision, or DecisionContext.
**Depends on:** nothing. Verified by grep in both import directions, the same standard applied to API-003 and API-004.

---

## 1. Purpose

API-005 answers: *"what spoke for or against what I believed?"* Evidence
is a time-bound record of information the investor regarded as
supportive of or challenging to a line of reasoning. It does **not**
represent objective truth. Atlas preserves:

> "That the investor regarded this information as evidence."

Atlas does **not** assert:

> "That the information proves or disproves anything."

## 2. Observation vs. Hypothesis vs. Evidence

Three aggregates now exist that all capture investor-authored free text
before a Decision is made. The role each plays in reasoning is what
distinguishes them, not merely their content:

| | Observation (API-003) | Hypothesis (API-004) | Evidence (API-005) |
|---|---|---|---|
| Answers | "What did I notice?" | "What might this mean?" | "What spoke for or against what I believed?" |
| Nature | A fact, pre-interpretation | A provisional interpretation | An assessed input to reasoning |
| Example | "Revenue increased by 18 percent." | "Demand for AI infrastructure may be accelerating faster than the market expects." | "The 18 percent revenue increase supports the belief that demand is accelerating." |
| Timestamp field | `observed_at` | `formulated_at` | `observed_at` |
| Distinguishing field | — | — | `direction` (SUPPORTS / CHALLENGES) |

The same underlying information may later be represented as both an
Observation and as Evidence — API-005 introduces **no relationship**
between those aggregates; each is captured and stored completely
independently. The distinction is enforced only through documentation
and UX — the domain performs **no semantic validation** of whether a
`Statement` "sounds like" evidence.

## 3. Meaning of SUPPORTS and CHALLENGES

`Direction` is a required two-value enum:

- **SUPPORTS** — the investor regarded the Evidence as strengthening a
  belief.
- **CHALLENGES** — the investor regarded the Evidence as weakening,
  questioning, or contradicting a belief.

Deliberately, no other values exist: no `PROVES`, `DISPROVES`, `TRUE`,
`FALSE`, `POSITIVE`, `NEGATIVE`, `CONFIRMING`, or `DISCONFIRMING`.
**Evidence influences reasoning. It does not determine truth** — this is
the aggregate's central design principle, and `Direction`'s two-value
shape is the mechanism that enforces it structurally: there is no code
path through which Evidence could assert correctness rather than
relevance.

## 4. Folder and Package Structure

Evidence is added as a new, standalone bounded context — a sibling to
`decision`, `decision_context`, `observation`, and `hypothesis`, not
nested inside any of them:

```
atlas/core/
  domain/
    decision/                      # API-001 — untouched
    decision_context/               # API-002 — untouched
    observation/                    # API-003 — untouched
    hypothesis/                     # API-004 — untouched
    evidence/                       # API-005 — new
      value_objects.py             # EvidenceId, Statement, Direction
      entity.py                    # Evidence aggregate
      exceptions.py
      repository.py                # interface only
  application/
    ...
    evidence/                       # API-005 — new
      capture_evidence.py
  infrastructure/
    persistence/
      ...
      evidence/                    # API-005 — new
        table.py
        sqlalchemy_repository.py
    api/
      app.py                       # composition root — updated, additively only
      ...
      evidence/                    # API-005 — new
        schemas.py
        router.py
        dependencies.py
        errors.py

tests/unit/
  domain/evidence/
  application/evidence/
  infrastructure/persistence/evidence/
  infrastructure/api/evidence/
```

The only file this increment touches outside `evidence/`'s own subtree is
[`atlas/core/infrastructure/api/app.py`](../atlas/core/infrastructure/api/app.py) —
a pure addition (two import lines, one `include_router`, one
`register_error_handlers` call), confirmed by diff.

## 5. Aggregate and Value-Object Rationale

[`atlas/core/domain/evidence/entity.py`](../atlas/core/domain/evidence/entity.py) —
`Evidence`, a frozen dataclass:

| Field | Required | Rule |
|---|---|---|
| `id` | yes | fresh `EvidenceId`, assigned once at capture |
| `statement` | yes | `Statement` — non-empty after stripping whitespace |
| `direction` | yes | `Direction` — `SUPPORTS` or `CHALLENGES` only |
| `observed_at` | yes | timezone-aware `datetime`, **preserved exactly as given** |
| `recorded_at` | yes | Atlas's own UTC clock, assigned once at capture |
| `source` | no | plain `str \| None` — blank/whitespace normalizes to `None` |
| `note` | no | plain `str \| None` — blank/whitespace normalizes to `None` |

[`atlas/core/domain/evidence/value_objects.py`](../atlas/core/domain/evidence/value_objects.py):

- **`Statement`** performs only a non-empty-after-strip check — the same
  minimal validation pattern as `Observation.Statement` and
  `Hypothesis.Statement`. No linguistic or semantic check of any kind is
  applied, per the spec's own explicit instruction.
- **`Direction`** is a `str` `Enum` with a `.coerce()` classmethod,
  matching the exact pattern established by API-001's `DecisionType`:
  accepts a `Direction` instance or a matching string, raises
  `InvalidDirectionError` for anything else (missing or unknown value).
- **`EvidenceId`** is the same UUID-wrapper pattern as `DecisionId`,
  `ContextId`, `ObservationId`, and `HypothesisId`.

**The same offset-preservation asymmetry as every prior increment:**
`observed_at` is **not** normalized to UTC. `_validated_observed_at` only
checks the value is a timezone-aware `datetime`; it never calls
`.astimezone(timezone.utc)`. This matches `Observation.observed_at` and
`Hypothesis.formulated_at` exactly, and for the same reason: it is the
investor's own account of *when the information became known or
relevant*, not a value Atlas is free to renormalize. `recorded_at`,
being Atlas's own system clock, stays UTC.

## 6. Explicitly Excluded Fields

Per the spec, none of the following exist anywhere in this aggregate,
its persistence, or its API: `strength`, `weight`, `confidence`,
`conviction`, `probability`, `uncertainty score`, `reliability score`,
`source credibility`, `truth status`, `verification status`,
`objectivity score`, `model confidence`, `generatedBy`, `owner type`,
`tags`, `categories`. These are explicitly deferred to future, separate
domain decisions — not omitted by oversight. This exclusion is also the
direct point of contrast with the legacy `atlas.evidence` package (§9),
which implements exactly these concepts for a different purpose.

## 7. Core Domain Decision, As Implemented

- `Evidence` is a fully standalone aggregate. It holds no reference to
  `Hypothesis`, `Observation`, `Decision`, or `DecisionContext`, and none
  of those hold a reference to it. There is no `HypothesisId`,
  `ObservationId`, `DecisionId`, `DecisionContextId`, foreign key,
  relation table, graph edge, or compatibility layer anywhere in this
  increment.
- Verified structurally, not just by omission: `grep -r` across
  `atlas/core/domain/evidence/`, `atlas/core/application/evidence/`, and
  `atlas/core/infrastructure/persistence/evidence/` found zero imports of
  `decision`, `decision_context`, `observation`, or `hypothesis` modules.
  The reverse search (those modules referencing `evidence`) also returned
  nothing.

## 8. Legacy Naming Collision — Reported and Resolved Before Implementation

Before writing any code, the repository was inspected for existing
classes, enums, tables, modules, or domain concepts named `Evidence`.
This search found a **materially larger** collision than API-003's single
`Observation` class:

1. **`atlas.domains.decision.models.Evidence`** — an exact bare-name
   collision. A frozen dataclass: `id, category (EvidenceCategory),
   statement, source, strength (EvidenceStrength: STRONG/MODERATE/
   LIMITED/MISSING), data`. Docstring: *"Fact used by the decision
   domain. Evidence contains facts only."* — deterministic,
   category-classified, strength-graded.
2. **The entire `atlas.evidence` package**
   (`atlas/evidence/engine.py`, `atlas/evidence/__init__.py`) — a
   pre-existing bounded context literally named "evidence":
   `EvidenceClaim`, `EvidenceInput`, `EvidenceRationale`,
   `EvidenceAssessment`, `EvidenceQualityEngine`, plus enums
   `EvidenceSource`, `EvidenceStrength` (`VERY_STRONG`…`INSUFFICIENT`),
   `EvidenceAction` (`UPDATE_ASSESSMENT`, `REDUCE_CONFIDENCE`, …). This
   engine automatically grades strength, computes a `confidence_impact`
   score, and recommends actions — precisely the category of concept
   (strength / weight / confidence / reliability scoring) API-005
   explicitly excludes (§6).
3. Weaker, adjacent name overlaps: `atlas.domains.decision.engine.
   EvidenceEngine` and `atlas.domains.research.models.
   ResearchEvidenceReference`.

No table named `evidence` existed in any SQL schema — no
persistence-level collision.

This was reported to the Product Owner before any code was written
(unlike the observation-collision path in API-003, this was flagged as
"clearly isolated and non-blocking, but larger than the API-003
precedent, therefore worth explicit confirmation" rather than a
hard stop). **Product Owner decision, applied literally:**

- Treat both as a non-blocking legacy naming collision.
- Do not rename any legacy class or package.
- Do not modify `atlas.evidence` or
  `atlas.domains.decision.models.Evidence`.
- Do not introduce a compatibility layer.
- Do not consolidate anything in API-005.
- Build the new `Evidence` aggregate entirely inside `atlas/core`, exactly
  as specified.
- Maintain zero imports in either direction between
  `atlas/core/domain/evidence` and the legacy evidence concepts.
- Record the collision and its semantic difference here (§9).

**Reasoning, as given:** API-005 models investor-authored reasoning
evidence. The legacy `atlas.evidence` package models automated assessment
and evidence-quality concepts. Although they share a name, they represent
different bounded contexts and different ubiquitous language. As with the
Observation collision, the architecture remains aggregate-first and
bounded-context-first. A future architecture consolidation increment will
decide whether the legacy terminology should eventually be renamed or
merged.

No code was written to bridge, alias, or disambiguate the concepts. They
are distinguished only by their fully-qualified module path.

## 9. Semantic Difference — API-005 Evidence vs. Legacy Evidence Concepts

| | API-005 `atlas.core.domain.evidence.Evidence` | Legacy `atlas.domains.decision.models.Evidence` | Legacy `atlas.evidence` package |
|---|---|---|---|
| Authorship | Investor-authored, verbatim | Deterministic domain fact | Investor input, automatically assessed |
| Core question | "Did the investor regard this as supporting or challenging a belief?" | "What fact does the decision engine use?" | "How strong/credible is this claim?" |
| Grading | None — `Direction` only | `EvidenceStrength` (STRONG…MISSING) | `EvidenceStrength` (VERY_STRONG…INSUFFICIENT), `confidence_impact`, `EvidenceAction` |
| Categorization | None | `EvidenceCategory` (Portfolio/Company/Market/…) | `EvidenceSource` (audited report/social media post/…) |
| Truth stance | Explicitly agnostic — investor's own assessment | Implicitly authoritative ("facts only") | Assesses claim strength/verifiability |
| Persistence | New, standalone `evidence` table | In-memory dataclass, no dedicated table found | In-memory dataclass, no dedicated table found |

## 10. Persistence Design

[`atlas/core/infrastructure/persistence/evidence/`](../atlas/core/infrastructure/persistence/evidence/) —
a new, **singular** `evidence` table (per the spec, "evidence" is treated
as an uncountable noun in this domain and API naming — not `evidences`),
own `MetaData()` (not shared with `decisions`, `decision_contexts`,
`observations`, or `hypotheses`), same reasoning as prior increments:
separate schema lifecycle for a separate bounded context, same physical
`atlas.db` file via the same shared engine (reused read-only from
`decision`'s dependencies module).

| Column | Notes |
|---|---|
| `evidence_id` | primary key |
| `statement` | text, not null |
| `direction` | text, not null (`"SUPPORTS"` / `"CHALLENGES"`) |
| `source` | nullable text |
| `note` | nullable text |
| `observed_at` | ISO-8601 text, offset preserved exactly |
| `recorded_at` | ISO-8601 text, always UTC |

Exactly the seven columns the spec lists — nothing added.

**No foreign keys, asserted by a structural test** (matching API-003/004's
convention): `tests/unit/infrastructure/persistence/evidence/` inspects
the table's column set and `foreign_keys` attribute directly, confirms
the table name is the singular `"evidence"`, and a separate test confirms
`decisions`, `decision_contexts`, `observations`, and `hypotheses` tables
are byte-for-byte unchanged in column shape.

**Chronological ordering across mixed timezone offsets — same
architectural decision as API-004's Hypothesis, applied again here.**
`observed_at` preserves its original offset rather than being normalized
to UTC, so a plain SQL `ORDER BY` on the stored ISO-8601 text column would
not produce correct chronological order. `SqlAlchemyEvidenceRepository.
list_all()` fetches all rows and sorts them in Python using the
constructed `Evidence` objects' tz-aware `datetime` values — comparing by
true absolute instant regardless of stored offset — exactly mirroring
`SqlAlchemyHypothesisRepository`'s approach. Covered by a dedicated test
(`test_chronological_order_compares_true_instant_across_mixed_offsets`)
with two timestamps at different offsets representing different instants.

No Alembic, same standing product decision as prior increments.

## 11. Application Behavior

[`atlas/core/application/evidence/capture_evidence.py`](../atlas/core/application/evidence/capture_evidence.py) —
`EvidenceService` implements all three use cases directly, matching
API-004's pattern (not API-003's, where retrieval bypassed the service):

- `capture(request)` — constructs and persists a new `Evidence` record.
- `get(evidence_id)` — returns the matching `Evidence`, or raises
  `EvidenceNotFoundError` if none exists (mirroring `HypothesisNotFoundError`
  / `DecisionNotFoundError`: a missing reference, not a malformed value,
  deliberately not an `EvidenceValidationError`).
- `list_all()` — delegates directly to the repository, which already
  returns the correct chronological order (§10).

RecordedAt is assigned through the same injectable-clock pattern used by
every prior increment's `capture()` classmethod.

## 12. API Contract

```
POST /evidence          201 Created
GET  /evidence           200 OK   (list, chronological — observed_at asc)
GET  /evidence/{id}      200 OK, or 404
```

Singular `/evidence` throughout, per the spec — not `/evidences`.

**Example request:**

```json
POST /evidence
{
  "statement": "Order intake increased by 24 percent and management raised full-year guidance for the second consecutive quarter.",
  "direction": "SUPPORTS",
  "source": "Quarterly earnings report",
  "note": "The comparison benefits from a weak prior-year period.",
  "observedAt": "2026-07-13T09:15:00+02:00"
}
```

**Example response (201):**

```json
{
  "evidenceId": "2ae53603-...-...-...-...",
  "statement": "Order intake increased by 24 percent and management raised full-year guidance for the second consecutive quarter.",
  "direction": "SUPPORTS",
  "source": "Quarterly earnings report",
  "note": "The comparison benefits from a weak prior-year period.",
  "observedAt": "2026-07-13T09:15:00+02:00",
  "recordedAt": "2026-07-13T20:20:50.378654Z"
}
```

Confirmed by a live `uvicorn` smoke test against exactly this payload
shape, plus a `CHALLENGES` capture, an invalid-`direction` 400, a
blank-`statement` 400, blank `source`/`note` normalizing to `null`, list,
get-by-id, and 404-for-unknown — all passing, alongside `GET /decisions`,
`GET /observations`, and `GET /hypotheses` still returning 200.

**ID format:** the spec's illustrative example uses a prefixed identifier
style (`"evd_01J..."`). Implemented as a plain UUID instead, matching
every other aggregate's identity scheme — the same reasoning API-002,
API-003, and API-004 used for not adopting their own specs' illustrative
prefixed-ID examples literally.

| Failure | Status | Body |
|---|---|---|
| Blank or whitespace-only `statement` | 400 | `{"detail": "Statement.value must not be empty"}` |
| Invalid `direction` (not `SUPPORTS`/`CHALLENGES`) | 400 | `{"detail": "Unknown Direction: '...'"}` |
| Missing `observedAt`, or malformed request shape entirely | 422 | FastAPI's default — the domain's own `InvalidObservedAtError` is never reached for a field that's absent or fails pydantic's own datetime parsing |
| Unknown `evidence_id` on `GET /evidence/{id}` | 404 | `{"detail": "No Evidence found with id ..."}` |

No `PATCH`, no `PUT`, no `DELETE`, no filtering, no search, no
pagination — matches "insert-only" and the explicit non-goals list
literally.

**Casing convention, built camelCase-first:** like API-003/004, this
increment's schemas subclass the shared `CamelModel` directly.
`populate_by_name=True` means a snake_case request body (`observed_at`)
is still accepted, verified by a dedicated backward-compatibility test.

**Error contract:** consistent with the Architecture Review outcome
recorded for API-004, no new `code` field was added to error responses —
`EvidenceValidationError` (→ 400) and `EvidenceNotFoundError` (→ 404) use
the existing plain `{"detail": "<message>"}` shape. A shared, structured
Error Contract remains its own confirmed future Product Increment.

## 13. Sequence Diagram — `POST /evidence`

```
Investor      Router      EvidenceService   EvidenceRepository   SQLite
   |             |               |                  |               |
   |--POST------>|               |                  |               |
   |  {statement,|--Request----->|                  |               |
   |   direction,|                |--Statement(...)                 |
   |   ...}      |                |--Direction.coerce(...)          |
   |             |                |   [blank/invalid -> raise *ValidationError -> 400]
   |             |                |--Evidence.capture()             |
   |             |                |   (validates ObservedAt;        |
   |             |                |    normalizes blank source/note |
   |             |                |    to None; assigns id +        |
   |             |                |    recorded_at)                 |
   |             |                |--add(evidence)------------------>|
   |             |                |                                  |--INSERT-->|
   |             |                |<--ok------------------------------|           |
   |<--201 + Evidence --------------|                                             |
```

No other aggregate or repository appears in this flow — the entire path
from request to persistence touches only `Evidence`'s own bounded
context.

## 14. Test Summary

72 new tests, regression-clean against the existing suite:

- **Domain (34 tests):** [`tests/unit/domain/evidence/`](../tests/unit/domain/evidence/)
  — `EvidenceId`/`Statement`/`Direction` value-object validation
  (including `Direction.coerce()` accepting `SUPPORTS`/`CHALLENGES`,
  rejecting unknown/missing values), aggregate creation via `capture()`,
  `observed_at` offset-preservation vs. `recorded_at` UTC, missing/naive
  `observed_at` rejection, blank `source`/`note` normalizing to `None`,
  meaningful `source`/`note` stripped but preserved, immutability.
- **Application (7 tests):** [`tests/unit/application/evidence/`](../tests/unit/application/evidence/)
  — capture, `recorded_at` assigned by Atlas's clock, retrieve by id,
  unknown id raises `EvidenceNotFoundError`, multiple records returned in
  chronological order, mixed-UTC-offset true-instant ordering, empty list
  when nothing captured. Runs against a real (in-memory) SQLite
  repository, not a fake.
- **Persistence (15 tests):** [`tests/unit/infrastructure/persistence/evidence/`](../tests/unit/infrastructure/persistence/evidence/)
  — create/persist/read/round-trip-equals-original (including
  `Direction` round-tripping for both values), insert-only, `observed_at`'s
  exact offset round-tripping unchanged, chronological ordering by
  `observed_at` ascending, the mixed-offset true-instant ordering case,
  tie-break ordering, a structural no-foreign-keys and singular-table-name
  check, and a check that `decisions`/`decision_contexts`/`observations`/
  `hypotheses` tables are unchanged.
- **API (16 tests):** [`tests/unit/infrastructure/api/evidence/`](../tests/unit/infrastructure/api/evidence/)
  — POST success (camelCase response shape), `CHALLENGES` accepted,
  invalid `direction` rejected (400), optional-field omission, blank
  `source`/`note` normalizes to `null`, snake_case request backward
  compatibility, two validation-failure scenarios (400 for blank/empty
  statement, 422 for missing/malformed `observedAt`), GET list (empty and
  populated), GET by id (found and 404).

**Regression:** API-001 through API-004 test modules were run in
isolation and all **243 pass unchanged** (matching the pre-API-005 count
exactly: 188 for API-001/002/003 + 55 for API-004). A live `uvicorn`
smoke test additionally confirmed `GET /decisions`, `GET /observations`,
and `GET /hypotheses` still return 200 alongside working
`POST/GET /evidence` calls in the same running app. Full repository
suite: **7,226 passed, 3 skipped** (7,154 pre-existing + 72 new). Scoped
lint (`atlas/core`, `tests/unit`): clean. Whole-repo `ruff check .` count
unchanged at 1,202 pre-existing findings.

## 15. Architectural Decisions

1. **The legacy naming collision was reported and confirmed before any
   code was written**, following the same protocol as API-003's
   `Observation` collision, but escalated appropriately given its larger
   scope (an entire pre-existing bounded context, not a single class).
   The Product Owner's decision — build in full isolation, zero imports,
   record the collision, no compatibility layer — was applied literally.
2. **`Direction` uses the exact `.coerce()` pattern from API-001's
   `DecisionType`**, not a new validation approach — consistency with an
   established precedent rather than inventing a parallel mechanism for
   an equivalent problem (a required enum-like field with a small, fixed
   value set).
3. **Chronological ordering by `observed_at` is computed in Python, not
   SQL**, identical reasoning and identical mechanism to API-004's
   Hypothesis — the pattern is now established across two increments,
   not a one-off.
4. **The application service owns `get`/`list_all`, not just `capture`,**
   matching API-004's convention (not API-003's, which left retrieval to
   the router).
5. **No new `code` field was added to error responses**, per the
   Architecture Review decision already recorded for API-004 — this
   increment's `errors.py` module deliberately follows that precedent
   rather than re-opening the question independently.
6. **Table name is the singular `evidence`, not `evidences`**, and the
   REST path is `/evidence`, not `/evidences` — both explicit, literal
   spec requirements, not a stylistic default.

## 16. Genuine Risks / Unresolved Questions

- **Two legacy "Evidence" concepts, not one, now coexist unresolved**
  (§8, §9) — a larger surface for future confusion than API-003's single
  `Observation` collision. Any future work importing `Evidence` without a
  fully-qualified path risks importing the wrong one; there are now three
  distinct classes/packages sharing the name across the repository.
- **400 vs. 422 boundary is uneven, same category already on record for
  API-002/003/004:** a domain-rejected value (blank statement, invalid
  direction) is 400; a missing field entirely is 422. Flagged, not fixed.
- **In-Python sort of `list_all()` is O(n log n) in application memory,**
  the same non-issue-for-now already flagged in API-004's documentation —
  worth revisiting if a future increment adds pagination.
- **Reused engine dependency (`get_decision_engine`) is a read-only
  cross-module import**, the same coupling point flagged in API-003/004's
  documentation — worth naming again since a fifth bounded context now
  depends on it.

## 17. Future Backlog / Architecture Consolidation

**New item — legacy Evidence naming collision (this increment):**
`atlas.domains.decision.models.Evidence` (deterministic, category-classified,
strength-graded fact) and the entire `atlas.evidence` package
(`EvidenceClaim`/`EvidenceInput`/`EvidenceAssessment`/`EvidenceQualityEngine`,
automated strength/credibility/confidence-impact assessment) both use the
word "Evidence" for concepts materially different from
`atlas.core.domain.evidence.Evidence` (investor-authored, unscored,
direction-only reasoning input). A future architecture consolidation
increment should decide whether to rename the legacy concepts, rename
this one, or formally document the three-way disambiguation rule. Out of
scope for API-005 per explicit Product Owner instruction — see §8 for the
full semantic comparison already recorded to support that future
decision.

**Carried forward from API-004:** the shared, structured Error Contract
(a real `code` field across all Atlas core error responses, and the
400-vs-422 inconsistency spanning API-002 through API-005) remains
confirmed as its own future Product Increment. The brittle hard-coded
test-count assertion in `README.md` / `tests/test_release_candidate.py`
also remains an open backlog item from API-004's review, unaffected by
this increment.
