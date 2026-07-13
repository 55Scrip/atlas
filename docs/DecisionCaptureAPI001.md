# API-001 — Decision Capture

**Status:** Approved as the official baseline for Atlas Beta. First runtime capability of Atlas Beta.
**Scope:** Register and permanently preserve a single investment decision. No AI analysis, no portfolio intelligence, no market data.

**Revision note (Architecture Review):** `Subject` was promoted from optional
storage-only context to a required aggregate invariant. A valid `Decision`
now contains `DecisionId, DecisionType, Subject, InvestmentCase, Confidence,
DecidedAt` — every investment decision must be about something. This
document reflects that update; see §3–5, §8, §10, and §13 for what changed.

---

## 1. Project Folder Structure

Decision Capture lives entirely under a new `atlas/core/` tree, organised by
Clean Architecture layer rather than by technical kind (no repo-wide
`models/`, `services/`, `controllers/`). Each layer only knows about the
layer(s) beneath it:

```
atlas/core/
  domain/                        # business rules — no framework imports
    decision/
      value_objects.py
      entity.py
      exceptions.py
      repository.py              # interface only
  application/                   # use-case orchestration
    decision/
      capture_decision.py
  infrastructure/                # framework / IO — depends inward on domain
    persistence/
      decision/
        table.py
        sqlalchemy_repository.py
    api/
      app.py                     # composition root
      decision/
        schemas.py
        router.py
        dependencies.py
        errors.py

tests/unit/
  domain/decision/                          # pure domain tests, no DB, no HTTP
  infrastructure/persistence/decision/       # repository against real SQLite
  infrastructure/api/decision/               # HTTP layer via FastAPI TestClient
```

**Why this shape:** `domain/` never imports SQLAlchemy, FastAPI, or pydantic.
It is plain Python + dataclasses. That is what makes the domain tests run in
0.04s with zero fixtures, and it's what makes "swap SQLite for Postgres" or
"swap FastAPI for a CLI" a change confined to `infrastructure/`.

## 2. Package Structure

Three packages, one per layer, each importing only from the layer(s) inside
it: `infrastructure` → `application` → `domain`. `domain` has no outgoing
dependency on either. This is checked implicitly by the fact that
`atlas/core/domain/decision/*.py` contains no `import fastapi`, `import
sqlalchemy`, or `import pydantic` anywhere — verify with:

```
grep -rE "fastapi|sqlalchemy|pydantic" atlas/core/domain
```

## 3–5. Domain Model, Aggregate, Value Objects

[`atlas/core/domain/decision/value_objects.py`](../atlas/core/domain/decision/value_objects.py):

| Value object | Rule it enforces |
|---|---|
| `DecisionType` (str Enum) | one of `BUY, SELL, HOLD, WATCH, PASS`; `.coerce()` turns a raw string or `None` into a validated member |
| `Subject` | value must be non-empty after stripping whitespace — what the decision is about (e.g. a ticker); **required**, per Architecture Review |
| `InvestmentCase` | `reason` must be non-empty after stripping whitespace — the case *as reasoned*, not a later edit |
| `Confidence` | integer, `0–100` inclusive |
| `DecisionSource` (str Enum) | `Manual, Import, BrokerSync, API` |
| `DecisionId`, `UserId` | thin UUID wrappers — prevents passing a `UserId` where a `DecisionId` is expected, a real class of bug in a multi-id domain |

[`atlas/core/domain/decision/entity.py`](../atlas/core/domain/decision/entity.py) —
the `Decision` aggregate: a frozen dataclass. Fields, in the order the
Domain Contract lists them: `id`, `user_id` (inferred necessity, see §12),
`decision_type`, `subject`, `investment_case`, `confidence`, `decided_at`,
`recorded_at`, `source` (defaults to `Manual` — the only non-invariant
field).

The one constructor that matters is `Decision.register(...)`:

- Always assigns a fresh `id`.
- Always sets `recorded_at = now()` — this is Atlas's own clock, not the
  investor's, and it is never a caller-supplied value.
- `decided_at` defaults to `now()` if the investor doesn't supply one
  (immediate decisions), but accepts a past timestamp for backdated/import
  scenarios — validated to be timezone-aware and normalised to UTC.
- Rejects an invalid or missing `DecisionType` at the single point strings
  enter the domain, so the "Invalid DecisionType" test can assert against
  the aggregate directly rather than against an HTTP status code.

There is no setter, no `update()`, no `with_confidence(...)`. **A changed
opinion is expressed by calling `Decision.register()` again — never by
mutating an existing instance.** The dataclass is `frozen=True`, so
attribute assignment raises at runtime, not just by convention.

## 6. Repository Interface

[`atlas/core/domain/decision/repository.py`](../atlas/core/domain/decision/repository.py) —
a `Protocol` with exactly three methods: `add`, `get`, `list_all`. **There is
no `update` method.** This is the load-bearing design choice for "Decision
History is immutable — only INSERT, never UPDATE": the rule isn't a comment
or a code review convention, it's structurally impossible to violate through
this interface.

## 7. Application Service

[`atlas/core/application/decision/capture_decision.py`](../atlas/core/application/decision/capture_decision.py) —
`CaptureDecisionService.capture(request)` is the one place raw primitives
(a `uuid.UUID`, a plain `str`, a plain `int` — the shape anything outside
the domain speaks) are translated into value objects and the aggregate, then
persisted.

**Read paths (`GET /decisions`, `GET /decisions/{id}`) skip this service
entirely** and call the repository directly from the API layer. There is no
business rule on the read side — no filtering, no computed fields, nothing
to orchestrate — so a `GetDecisionQuery` class would be a pass-through
wrapper around `repository.get(...)`. Introducing it would be exactly the
kind of ceremony the brief asks to avoid. If a read-side rule shows up later
(e.g. redaction, pagination), that's when the wrapper earns its place.

## 8. REST Controller

[`atlas/core/infrastructure/api/decision/router.py`](../atlas/core/infrastructure/api/decision/router.py),
built on FastAPI (new dependency — the repo had no HTTP framework yet;
FastAPI was chosen because `pydantic` was already a dependency and pairs
directly with it for request/response validation).

| Endpoint | Behaviour |
|---|---|
| `POST /decisions` | 201 + the persisted Decision (`subject` now required in the request body) + a learning-status message |
| `GET /decisions` | 200 + every recorded Decision (oldest first) |
| `GET /decisions/{id}` | 200 + the Decision, or 404 if the id is unknown |

Validation failures ([`errors.py`](../atlas/core/infrastructure/api/decision/errors.py))
map every `DecisionValidationError` and stray `ValueError` (e.g. an unknown
`source`) to `422` with the domain's own message as `detail` — malformed
JSON shapes (wrong types, missing required fields) are already caught by
FastAPI/pydantic before they reach the domain.

Request/response bodies live in
[`schemas.py`](../atlas/core/infrastructure/api/decision/schemas.py), kept
deliberately separate from the domain's value objects: JSON-over-HTTP is a
transport concern (UUIDs as strings, ISO datetimes), not a business rule,
and the two are free to diverge.

**UX principle, applied literally:** every `POST /decisions` response
carries a `message` field — *"Atlas has recorded your decision. It has
started learning, but does not yet understand your decision patterns."*
This is a static, honest string, not a first-decision-only special case.
Making it conditional on "is this the user's first decision" would require
counting prior decisions per user inside the write path for a UX/copy
concern — and the sentence is equally true on decision #1 and decision
#50, since pattern analysis doesn't exist yet regardless of count. If the
product later wants a distinct one-time onboarding moment, that's a
read-count check added to the application service, not a rearchitecture.

## 9. Persistence Implementation

[`atlas/core/infrastructure/persistence/decision/`](../atlas/core/infrastructure/persistence/decision/) —
SQLAlchemy Core (not the ORM) against SQLite. Two deliberate choices:

- **Its own `MetaData()`**, not the legacy `atlas.database.connection.Base`
  used by the company/financials tables. Decision Capture's schema
  lifecycle shouldn't be coupled to an unrelated bounded context's; the two
  can still point at the same physical `atlas.db` file via the same engine.
- **Timestamps stored as ISO-8601 text**, not SQLAlchemy's `DateTime`
  column type. SQLite has no native timezone-aware datetime type, and
  `DateTime(timezone=True)` on the SQLite dialect silently returns naive
  datetimes on read — which would then fail the aggregate's own
  "`decided_at` must be timezone-aware" invariant on the very next read.
  Storing/parsing ISO-8601 text explicitly sidesteps that and matches how
  every other table in this repo's `schema.sql` already stores dates.

`add()` is a single `INSERT`. There is no `UPDATE` statement anywhere in
this file.

## 10. Tests

75 new tests, organised by what they exercise rather than by file count:

- **Domain (50 tests,** [`tests/unit/domain/decision/`](../tests/unit/domain/decision/)**):**
  value object validation (range, non-empty, coercion) for `Subject`
  alongside `DecisionType`, `InvestmentCase`, `Confidence`; aggregate
  creation including "register rejects a missing subject"; the
  `decided_at` vs. `recorded_at` distinction; immutability
  (`FrozenInstanceError`); "a changed opinion is a new Decision."
- **Aggregate persistence (7 tests,** [`tests/unit/infrastructure/persistence/decision/`](../tests/unit/infrastructure/persistence/decision/)**):**
  create, persist, read-by-id, read-all, and a full field-by-field
  round-trip equality check (including `Subject`) against a real
  (in-memory) SQLite database — not a mock.
- **API (18 tests,** [`tests/unit/infrastructure/api/decision/`](../tests/unit/infrastructure/api/decision/)**):**
  POST success, seven distinct POST validation failure scenarios (empty
  reason, empty subject, empty type, invalid type, confidence out of
  range — parametrized over three values, malformed UUID, unknown
  source), GET list (empty and populated), GET single (found and 404).

All 6,904 pre-existing tests still pass unmodified; the full suite is at
6,986 passed, 3 skipped.

## 11. Sequence Diagram — `POST /decisions`

```
Investor          FastAPI Router        Application Service       Decision (domain)      Repository            SQLite
   |                    |                        |                        |                    |                   |
   |--POST /decisions-->|                        |                        |                    |                   |
   |  {user_id, type,   |--CaptureDecisionRequest>|                        |                    |                   |
   |   subject, reason, |                        |--Decision.register()-->|                    |                   |
   |   confidence}      |                        |   (validates VOs,      |                    |                   |
   |                    |                        |    incl. Subject;      |                    |                   |
   |                    |                        |    assigns id +        |                    |                   |
   |                    |                        |    recorded_at)        |                    |                   |
   |                    |                        |<---Decision------------|                    |                   |
   |                    |                        |--add(decision)----------------------------->|                   |
   |                    |                        |                        |                    |--INSERT---------->|
   |                    |                        |                        |                    |<--ok---------------|
   |                    |<---Decision------------|                        |                    |                   |
   |<--201 + Decision --|                        |                        |                    |                   |
   |  + learning        |                        |                        |                    |                   |
   |  message           |                        |                        |                    |                   |

  Validation failure path (e.g. confidence=500):
   |--POST /decisions-->|                        |                        |                    |                   |
   |                    |--CaptureDecisionRequest>|                        |                    |                   |
   |                    |                        |--Confidence(500)------>|                    |                   |
   |                    |                        |          raises InvalidConfidenceError       |                   |
   |                    |<--(propagates)---------|                        |                    |                   |
   |<--422 {"detail":"Confidence must be         |                        |                    |                   |
   |   between 0 and 100, got 500"}              |                        |                    |                   |
```

Note nothing is written to the repository on the failure path — the
aggregate never comes into existence, so there's nothing to roll back.

## 12. Explanation of Architectural Decisions

1. **Plain dataclasses in the domain, pydantic only at the API boundary.**
   The rest of this codebase's domain-shaped code (`atlas/domains/*`,
   `atlas/shared/entities.py`) already uses `@dataclass(frozen=True)`. The
   code this replaced used heavyweight pydantic `BaseModel` subclasses with
   custom `__init__`/coercion logic for every value object — more ceremony
   than the domain needs, and inconsistent with the rest of the repo.
   pydantic earns its place at the API layer, where FastAPI needs it for
   request parsing anyway.
2. **UUID parsing happens at the API boundary, not in the domain.** FastAPI
   + pydantic already validates `user_id: uuid.UUID` in the request schema
   before a `UserId` is ever constructed. "Is this string a well-formed
   UUID" is a data-format concern, not a business rule — the domain trusts
   its inputs are already the right shape, the boundary layer is
   responsible for getting them there.
3. **`DecisionSource` is a closed enum, not an open string, for V1.** The
   brief lists it as "Source examples," which reads as non-exhaustive, but
   no fifth source is ever named anywhere in the spec. Building an
   extensible source-registry for values that don't exist yet is exactly
   the speculative future-proofing the brief asks to avoid. Widening it to
   a plain `str` later is a one-line change if a real fifth source shows
   up.
4. **`UserId` remains a required field on `Decision`,** even though the
   Domain Contract enumerates `DecisionId, DecisionType, Subject,
   InvestmentCase, Confidence, DecidedAt` and doesn't name it. An investment
   decision with no owner has no meaning in a system whose whole premise is
   "learn from *your* decisions." This one inference was necessary to make
   the aggregate constructible at all; everything else in the Domain
   Contract is implemented literally.
5. **`Subject` is a value object (`Subject.value`), not a bare `str`** —
   per Architecture Review, it now carries the same invariant rigor as
   `InvestmentCase` and `Confidence`: non-empty after stripping whitespace,
   validated at construction, with its own `MissingSubjectError`. It sits
   in the aggregate's field order (and the Domain Contract's) right after
   `decision_type`, ahead of `investment_case`.

## 13. Suggestions — Genuine Issues Only

- **`GET /decisions` has no user scoping and no authentication.** It
  currently returns every decision from every user. This is explicitly
  out of scope per the brief (no mention of auth), but it's a real
  question to answer before this endpoint is exposed anywhere beyond
  local development — it is the kind of thing that's easy to forget once
  the endpoint "already works."
- **Pre-existing architectural sprawl (not touched by this change, flagged
  for awareness):** the repo already has at least four other "Decision"-
  shaped concepts under different names — `atlas/shared/entities.py`
  (`Decision` dataclass), `atlas/domains/decision/models.py` (`Decision`
  dataclass), `atlas/decision/*` (a "decision engine" for comparisons), and
  `atlas/decision_journal/`. None of these were modified or depended on by
  API-001, and `atlas/core/` was kept intentionally separate to avoid
  inheriting that sprawl. Long-term, consolidating "Decision" to one
  canonical meaning across the codebase is worth a dedicated sprint — but
  that's a redesign decision for the team, not something to fold into this
  increment.
