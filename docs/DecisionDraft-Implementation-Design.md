# DecisionDraft Implementation Design

**Sprint 8 — Engineering sprint.** This document is the complete, implementation-ready design for `ADR-DD-001-Decision-Draft.md` (Accepted). It contains no ontology work, no redesign, and no new architectural decisions — every choice below either (a) is dictated directly by `ADR-DD-001`'s own Decision section, or (b) is a mechanical engineering choice made by following an existing, cited precedent elsewhere in this codebase. Where a choice required judgment beyond direct precedent, that judgment and its grounds are stated explicitly rather than left implicit.

All evidence in this document was gathered by reading the current repository fresh during this sprint: `atlas/core/domain/decision/`, `atlas/core/domain/decision_context/`, `atlas/core/domain/case/`, `atlas/alpha/security_confirmation/`, `atlas/core/infrastructure/persistence/shared/schema_sync.py`, `atlas/core/infrastructure/api/serialization.py`, `atlas/core/infrastructure/api/app.py`, `frontend/src/history/securityConfirmationApi.ts`, `frontend/src/routes/`, and the `tests/unit/**/decision_context/` test layout. No claim below is inherited from prior-sprint memory without being re-verified against the file it cites.

---

## 1. Executive Summary

**Scope.** The complete backend implementation (domain, application, persistence, API) and Alpha frontend integration for `DecisionDraft`, as adopted by `ADR-DD-001`: a Case-scoped, investor-owned, editable-over-time record that lets an investor save incomplete Decision Workspace work and resume it later, with an explicit commit action that produces a real `Decision` (and, optionally, a real `DecisionContext`) through the existing, unmodified capture paths.

**Goals.**
- Implement `DecisionDraft` exactly as `ADR-DD-001` §1–§6 specify: Case-scoped identity, event-sourced lifecycle, an unmodified commit boundary, a narrow Daily Brief projection, optional-additive provenance back-reference, and the five rejected models genuinely excluded.
- Reuse `SecurityConfirmationEvent`'s proven persistence shape (`ADR-DD-001` §2) at the *pattern* level, not the *package* level (see §2.1 below for why).
- Leave `Decision`, `DecisionContext`, `Case`, and `SecurityConfirmation` completely unmodified, per `ADR-DD-001`'s own Migration section.

**Non-goals.**
- No change to `Decision.register()`, `DecisionContext.capture()`, or either of their repositories' public interfaces.
- No new ontology, no Monitoring/Invalidation/`CaseCondition` content (`ADR-CC-001`, separately Not Implemented — see Sprint 7's own Conformance Report), no `Assumption` content (`ADR-AS-001`, same).
- No authentication/authorization system — none exists anywhere in this codebase today (verified: no `current_user`, `Authorization`, or JWT dependency exists under `atlas/core/infrastructure/api/`; `user_id` is a plain client-supplied field on every existing write endpoint, e.g. `CreateDecisionRequest.user_id`). `DecisionDraft` follows the identical convention; inventing an auth layer here would be new architecture this ADR does not require.
- No resolution of `ADR-DD-001`'s own genuinely open ontological questions (provenance retention, abandon-vs-delete semantics, expiration, collaboration). Where an *engineering* decision is still required to ship something (e.g., abandon vs. delete must resolve to *some* concrete event model), §3 below makes that call explicitly and marks it as an implementation-level resolution, not a reopening of the ADR's own Open Questions.

**Relationship to `ADR-DD-001`.** This document converts every Decision point in that ADR into a concrete build. Section 11 (Conformance Matrix) maps each one explicitly. Nothing here may be read as amending, reinterpreting, or narrowing the ADR — where this document makes a choice the ADR left open, that choice is flagged as an implementation detail, not an architecture decision, and remains subordinate to the ADR if the two ever appear to conflict.

---

## 2. Existing Architecture Review

### 2.1 Package layout — Core, not Alpha

Two live precedents exist for "editable-over-time, event-sourced" content in this codebase, and they use *different* package layouts:

| | `Decision` / `DecisionContext` | `SecurityConfirmation` |
|---|---|---|
| Location | `atlas/core/domain/`, `atlas/core/application/`, `atlas/core/infrastructure/{persistence,api}/` | `atlas/alpha/security_confirmation/` (flat package, own `api/` subfolder) |
| Status | Core ontology objects, produced by the same ADR Investigation → ADR conversion process as `DecisionDraft` itself | An Alpha-specific, single-product-flow feature (per its own module docstring: "First Product Flow"), never part of the Investigation Series or OE-series ontology |

`DecisionDraft` was investigated (`Investigation-003`) and converted (`ADR-DD-001`) through the exact same discipline as `Decision` and `DecisionContext` — it is a Core ontology object, not an Alpha-specific feature. **Decision: `DecisionDraft` is built under `atlas/core/domain/decision_draft/`, `atlas/core/application/decision_draft/`, `atlas/core/infrastructure/persistence/decision_draft/`, `atlas/core/infrastructure/api/decision_draft/`** — following `Decision`/`DecisionContext`'s own layering exactly. `SecurityConfirmationEvent` is reused only for its *event-sourcing shape* (append-only rows, one `event_type` column, a derived "current state" read), never its package location or its own types.

### 2.2 What is directly reusable

- **`Decision.register()` and `DecisionContext.capture()`** (`atlas/core/domain/decision/entity.py`, `atlas/core/domain/decision_context/entity.py`) — unmodified, called exactly as they exist today at commit time. Confirmed: neither classmethod has any optional "draft" parameter or awareness of drafts, and none should be added.
- **`DecisionRepository.add()` / `DecisionContextRepository.add()`** (`atlas/core/domain/decision/repository.py`, `atlas/core/domain/decision_context/repository.py`) — unmodified Protocols, called directly at commit time, exactly as every other write in this codebase calls its own aggregate's repository.
- **`sync_table_schema`** (`atlas/core/infrastructure/persistence/shared/schema_sync.py`) — the codebase-wide schema-creation/evolution helper. Confirmed: there is no migration framework in this repository (`database/atlas.db` is a gitignored, disposable local SQLite file — stated explicitly in `schema_sync.py`'s own docstring). `create_decision_draft_events_table(engine)` will call this directly, identically to every other `create_X_table` function.
- **`CamelModel`** (`atlas/core/infrastructure/api/serialization.py`, `ADR-004`) — every new schema subclasses this, unchanged.
- **The append-only-event-plus-derived-projection pattern** (`atlas/alpha/security_confirmation/models.py`, `table.py`, `repository.py`) — the direct structural template for `DecisionDraftEvent`, per `ADR-DD-001` §2.
- **The 409-on-conflict-with-client-self-heal pattern** (`atlas/alpha/security_confirmation/service.py`'s `ConflictingConfirmationError`; `frontend/src/history/securityConfirmationApi.ts`'s `confirmSecuritySelection`, which re-reads on 409 rather than surfacing a raw error) — reused directly for Alpha's own conflict handling (§7).
- **`_next_recorded_at`** (`security_confirmation/service.py`) — the exact idiom for guaranteeing strictly-increasing event timestamps under both a real and an injected test clock. Reused verbatim in `DecisionDraftService`.
- **The `errors.py` / `dependencies.py` / `router.py` / `schemas.py` four-file API-module split** (`atlas/core/infrastructure/api/decision_context/`) — reused directly for `atlas/core/infrastructure/api/decision_draft/`.

### 2.3 What is explicitly not reusable, and why

- **`Decision`'s own value objects** (`Subject`, `InvestmentCase`, `Confidence` — `atlas/core/domain/decision/value_objects.py`) validate on construction (`Subject` rejects empty strings, `Confidence` rejects out-of-range integers, `InvestmentCase.reason` rejects empty strings). A draft, by definition, may be incomplete. Reusing these value objects directly on draft content would make "save incomplete work" impossible. **Decision: draft content fields are plain, unvalidated `str | None` / `int | None` / `datetime | None`** — validation is deferred entirely to commit time, when real `Decision`/`DecisionContext` construction (and therefore their existing, unmodified value-object validation) actually occurs. This is the direct engineering consequence of `ADR-DD-001` §3's own "constructed fresh from whatever the draft held at the moment of commit."
- **`CaseId` and `UserId`** (`atlas/core/domain/case/value_objects.py`, `atlas/core/domain/decision/value_objects.py`) *are* reused directly for the draft's own identity fields — these are never incomplete (a draft cannot exist without a known Case and a known investor), unlike the draft's own content.
- **`atlas/monitoring`** — no relationship; confirmed untouched by Sprint 7's own audit and not implicated here either.

### 2.4 Alpha frontend: no existing surface to extend

`frontend/src/routes/` has no Decision Workspace page today (confirmed: no file or component matching "Decision Workspace" anywhere under `frontend/src/`). `frontend/src/investmentCase/` holds only read-only Investment Case display components (`HeroCard.tsx`, `AtlasReasoningSection.tsx`, etc.) — no decision-recording form exists yet to attach draft behavior to. `frontend/src/history/securityConfirmationApi.ts` is the one existing precedent for a typed `fetch`-based API client with no framework/state-library dependency, and is the direct template for `decisionDraftApi.ts` (§7).

---

## 3. Aggregate Design

### 3.1 Two logical objects, one physical table

Per `ADR-DD-001` §1–§2: `DecisionDraft` is a stable identity; its lifecycle is entirely event-sourced. Directly mirroring `SecurityConfirmationEvent` — which has **no separate root table** for `ConfirmedSecuritySelection` at all — `DecisionDraft` has no separate root table either. One physical table, `decision_draft_events`, holds every event; `draft_id`, `case_id`, and `user_id` are repeated on every row (never joined back), exactly matching `security_confirmations`' own repeated-field-per-row discipline. "The `DecisionDraft`" as a queryable thing is the derived, latest-event projection over this one table — never a separately, directly edited row.

### 3.2 Identity

`DraftId` — a new value object, `atlas/core/domain/decision_draft/value_objects.py`, structurally identical to `DecisionId`/`ContextId` (`uuid.UUID = field(default_factory=uuid.uuid4)`). Generated once, at the moment a draft is first created (the first `"revised"` event), and never reused. There is no natural pre-existing external key to anchor drafts to (unlike `SecurityConfirmationEvent`, which anchors to an already-existing `decision_id`) — no `Decision` exists yet at draft time, exactly as `ADR-DD-001` §1 states, so `DraftId` must be freshly minted.

### 3.3 Ownership

`case_id: CaseId` (required) and `user_id: UserId` (required) — both reused directly from their existing value-object modules, per §2.3. Per `ADR-DD-001` §1: never `decision_id`.

### 3.4 Cardinality — multiple concurrent drafts per Case

`ADR-DD-001`'s own Open Questions leave "whether multiple simultaneous drafts per Case should be permitted or capped at one" unresolved, noting "evidence leans against a hard ontological cap." **Implementation decision: no cap.** A fresh `POST` mints a new `DraftId` unconditionally; nothing checks for an existing active draft on the same Case before creating another. This is the simpler build (no additional existence-check, no new error type for "a draft already exists") and does not foreclose a future product decision to cap at one, which would be a UI-layer choice (simply stop offering "New Draft" once one exists) requiring no backend change.

### 3.5 Invariants

- A `DecisionDraft`'s identity (`draft_id`, `case_id`, `user_id`) is fixed at creation and never changes across any subsequent event.
- No event is ever `UPDATE`d or `DELETE`d. "Current state" is always the single latest event for a `draft_id`, ordered `(recorded_at DESC, id DESC)` — the identical tiebreak idiom `security_confirmation/repository.py`'s `get_latest_event` already uses, reused verbatim for the same reason (deterministic ordering under an injected test clock).
- Draft content fields carry no validation beyond basic type/shape (e.g. `alternatives_considered` is a list of strings, not an empty-string-rejecting list) — full domain validation happens only at commit, via unmodified `Decision`/`DecisionContext` construction.
- A draft that has been committed or abandoned never accepts a further `"revised"` event — enforced at the application-service layer (§5), not the database layer, matching how `DuplicateDecisionContextError`/`ConflictingConfirmationError` are also application-layer, not `CHECK`-constraint, invariants in every existing precedent.
- Nothing is ever physically deleted. "Discard" (product language) and "abandon" (this design's own single terminal non-commit event, §4) are the same action — see §3.6.

### 3.6 Lifecycle — three events, two terminal states, no separate "Draft" state on `DecisionDraft` itself

Directly reapplying `ADR-CC-001`/`ADR-AS-001`'s own established economy (fewer real states than a naive reading suggests) to this aggregate:

- **`revised`** — the non-terminal event. The very first `revised` event *is* creation; every subsequent edit is another `revised` event, each carrying the *full* current content snapshot (never a delta), matching `SecurityConfirmationEvent`'s own fully-self-describing-row discipline.
- **`abandoned`** — the terminal "I am done with this, without recording a Decision" event. `ADR-DD-001`'s own Open Questions ask whether "abandon" and "delete" are the same action or two distinct events. **Implementation decision: they are the same event.** Nothing in this codebase is ever physically deleted (§3.5); a "delete" action from the investor's own point of view is realized, honestly, as an `abandoned` event — there is no second, physical-delete code path to build. This is the natural, minimal reading of the ADR's own append-only invariant, not a reinterpretation of it; it is flagged here as an implementation-level resolution of a question the ADR itself left open, and does not preclude a future product distinction if evidence ever justifies one.
- **`committed`** — the terminal "this became a real Decision" event, carrying an optional-but-always-populated-on-this-event-type `committed_decision_id` back-reference, matching the `observation_id` optional-additive-reference pattern `ADR-DD-001` §5 already establishes for the *other* direction (Decision → Draft) applied here in the direction the commit action itself naturally produces (Draft → Decision).

"Active" (the state Daily Brief and the Alpha UI care about) is a pure projection: **a draft is Active if and only if its latest event's `event_type` is `"revised"`.** Never a stored field.

---

## 4. Event Model

All events share one table (`decision_draft_events`, §5). All payload fields below beyond `id`/`draft_id`/`case_id`/`user_id`/`event_type`/`recorded_at` are nullable at the storage layer; which are populated depends on `event_type` as noted.

### Event: `revised`

- **Payload:** `id` (event id, UUID), `draft_id`, `case_id`, `user_id`, `event_type="revised"`, `decision_type: str | None`, `subject: str | None`, `reason: str | None`, `confidence: int | None`, `decided_at: datetime | None`, `source: str | None`, `situation: str | None`, `portfolio_relevance: str | None`, `capital_considerations: str | None`, `alternatives_considered: list[str]` (default `[]`), `uncertainties: list[str]` (default `[]`), `recorded_at`.
- **Invariant:** Carries the complete draft-content snapshot as of this edit — never a partial delta. May only be appended while the draft's own prior latest event (if any) is itself `"revised"` or absent (i.e., never after `abandoned`/`committed`).
- **Producer:** `DecisionDraftService.create()` (first `revised` event for a new `draft_id`) and `DecisionDraftService.revise()` (every subsequent one).
- **Consumer:** `DecisionDraftService.get()` (derives current state for the "read one draft" / "resume draft" use case); the Alpha UI's own draft-editing form (via the API, §6).

### Event: `abandoned`

- **Payload:** `id`, `draft_id`, `case_id`, `user_id`, `event_type="abandoned"`, all content fields `None`, `recorded_at`.
- **Invariant:** May only be appended while the latest prior event is `"revised"`. Idempotent at the service layer: calling abandon again on an already-abandoned draft is a no-op, mirroring `revoke()`'s own idempotency in `security_confirmation/service.py`.
- **Producer:** `DecisionDraftService.abandon()`.
- **Consumer:** The "Active" projection (§3.6) — an abandoned draft is excluded from `list_active_for_case` and from the Daily Brief projection.

### Event: `committed`

- **Payload:** `id`, `draft_id`, `case_id`, `user_id`, `event_type="committed"`, all draft-content fields `None`, `committed_decision_id: str` (the newly-created `Decision.id`, always populated on this event type), `recorded_at`.
- **Invariant:** May only be appended while the latest prior event is `"revised"`, and only after a real `Decision` (and, if applicable, `DecisionContext`) has already been successfully constructed and persisted via their own unmodified paths (§5.3). Never appended speculatively before those writes succeed.
- **Producer:** `DecisionDraftService.commit()`.
- **Consumer:** The "Active" projection (excludes committed drafts from further editing); the Alpha UI's own "this draft became Decision X" affordance (§7); `ADR-CR-001`'s own future Reconsideration workflow, per that ADR's own Related section, if and when it is built.

---

## 5. Repository Design

### 5.1 Domain repository interface

`atlas/core/domain/decision_draft/repository.py`:

```python
class DecisionDraftEventRepository(Protocol):
    def add(self, event: DecisionDraftEvent) -> None:
        """Insert a new event. Never UPDATEs or DELETEs."""
        ...

    def get_latest_event(self, draft_id: DraftId) -> DecisionDraftEvent | None:
        """The single most recent event for a draft, or None if it never existed."""
        ...

    def list_events(self, draft_id: DraftId) -> list[DecisionDraftEvent]:
        """Full history for one draft, oldest first."""
        ...

    def list_latest_by_case(self, case_id: CaseId) -> list[DecisionDraftEvent]:
        """The latest event for every distinct draft_id ever created under this Case
        (regardless of current status) — filtering to Active is an application-layer
        concern (§3.6), not a repository one, matching every other 'current state is
        derived' read in this codebase."""
        ...
```

Naming and shape directly mirror `DecisionRepository`/`DecisionContextRepository`'s own Protocol style (insert-only, no update method — the "no UPDATE, ever" rule enforced at the type level, per `decision/repository.py`'s own docstring) plus `security_confirmation/repository.py`'s own `get_latest_event`/`list_events` read shape.

### 5.2 Persistence model

`atlas/core/infrastructure/persistence/decision_draft/table.py`:

```python
decision_draft_events_table = Table(
    "decision_draft_events",
    metadata,  # this bounded context's own MetaData, per every existing table module
    Column("id", String, primary_key=True),
    Column("draft_id", String, nullable=False, index=True),
    Column("case_id", String, nullable=False, index=True),
    Column("user_id", String, nullable=False, index=True),
    Column("event_type", String, nullable=False),
    Column("decision_type", String, nullable=True),
    Column("subject", String, nullable=True),
    Column("reason", String, nullable=True),
    Column("confidence", Integer, nullable=True),
    Column("decided_at", String, nullable=True),
    Column("source", String, nullable=True),
    Column("situation", String, nullable=True),
    Column("portfolio_relevance", String, nullable=True),
    Column("capital_considerations", String, nullable=True),
    Column("alternatives_considered", String, nullable=True),  # JSON-encoded list, matching decision_contexts_table's own convention
    Column("uncertainties", String, nullable=True),            # same
    Column("committed_decision_id", String, nullable=True, index=True),
    Column("recorded_at", String, nullable=False),
)

def create_decision_draft_events_table(engine: Engine) -> None:
    sync_table_schema(engine, decision_draft_events_table)
```

No `ForeignKey` on `draft_id`, `case_id`, `user_id`, or `committed_decision_id` — matching the codebase-wide, explicitly-documented no-FK convention (`decision/table.py`'s own docstring: "matching the codebase-wide no-FK convention already established for every other cross-aggregate reference").

### 5.3 Indexes

`draft_id` (per-draft lookups: `get_latest_event`, `list_events`), `case_id` (per-Case listing: `list_latest_by_case`), `user_id` (a low-cost forward-compatibility index for a future "my drafts across every Case" query — not required by any endpoint in this design, added because the cost of the index is negligible and adding it later would need a migration this codebase's own `sync_table_schema` handles for nullable columns but not for indexes on existing large tables), `committed_decision_id` (supports a future "which draft became this Decision" reverse lookup, same forward-compatibility rationale).

### 5.4 Uniqueness rules

None. Unlike `decision_contexts_table`'s own `decision_id` `UNIQUE` constraint (at most one `DecisionContext` per `Decision`), no column here is ever unique — many events share one `draft_id`, and (per §3.4) many drafts may share one `case_id`. This is a deliberate absence, not an oversight: `ADR-DD-001` names no uniqueness invariant for `DecisionDraft` beyond `DraftId` itself already being generated as a fresh UUID per row.

### 5.5 Concurrency assumptions

Directly reapplying `security_confirmation/service.py`'s own `_next_recorded_at` idiom: every write path in `DecisionDraftService` computes its event's `recorded_at` as `max(clock(), previous_latest.recorded_at + timedelta(microseconds=1))` rather than a bare clock call, guaranteeing strictly-increasing timestamps for the same `draft_id` even under an injected, fixed test clock. `sync_table_schema`'s own per-table-name threading lock (already shared, codebase-wide infrastructure — see `schema_sync.py` §"Sprint 1, Commit 11") already protects concurrent `CREATE TABLE`/`ALTER TABLE` races on first use; no additional locking is introduced for row inserts, matching every other repository in this codebase (a plain `engine.begin()` transaction per `add()` call, no explicit row-level locking).

**Multi-writer conflict** (two browser tabs editing the same draft) is handled at the application-service layer (§6.4), not here — the repository itself has no opinion about whether a write "should" be accepted, only whether it succeeds as an insert.

---

## 6. API Design

All routes live in `atlas/core/infrastructure/api/decision_draft/router.py`, registered in `atlas/core/infrastructure/api/app.py` alongside every other router (one `include_router(decision_draft_router)` line and one `register_decision_draft_error_handlers(app)` line — see §8).

### 6.1 Routes

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/cases/{case_id}/decision-drafts` | Create a new draft (first `revised` event). |
| `GET` | `/cases/{case_id}/decision-drafts` | List every Active draft for a Case (full content — used by the Decision Workspace's own "resume one of your drafts" picker). |
| `GET` | `/decision-drafts/{draft_id}` | Read one draft's current derived state, including its `status`. |
| `GET` | `/decision-drafts/{draft_id}/events` | Full event history for one draft (audit/debug use; not consumed by Alpha's v1 UI). |
| `PATCH` | `/decision-drafts/{draft_id}` | Revise a draft's content (new `revised` event). |
| `POST` | `/decision-drafts/{draft_id}/abandon` | Abandon/discard a draft (new `abandoned` event; idempotent). |
| `POST` | `/decision-drafts/{draft_id}/commit` | Commit a draft: construct a real `Decision` (+ optional `DecisionContext`), then append a `committed` event. |
| `GET` | `/decision-drafts/daily-brief-summary` | The narrow, `ADR-DD-001` §4-conformant projection: `draftId`, `caseId`, `subject`, `createdAt` only — never full content. Query param: `userId` (required — Daily Brief is always scoped to one investor, matching every other Alpha per-user read). |

Route prefixing follows existing precedent exactly: `/cases/{case_id}/...` mirrors nothing existing directly (no other aggregate is listed under `/cases/{id}/...` today), but is the natural, minimal choice given `DecisionDraft`'s own Case-scoped identity (§3.3) — `/decisions/{id}/...` (the `DecisionContext` precedent) is not available here since no `Decision` exists yet, exactly per `ADR-DD-001` §1's own stated reason for keying on `case_id` rather than `decision_id`.

### 6.2 Requests

```python
class CreateDecisionDraftRequest(CamelModel):
    user_id: uuid.UUID
    decision_type: str | None = None
    subject: str | None = None
    reason: str | None = None
    confidence: int | None = None
    decided_at: datetime | None = None
    source: str | None = None
    situation: str | None = None
    portfolio_relevance: str | None = None
    capital_considerations: str | None = None
    alternatives_considered: list[str] = []
    uncertainties: list[str] = []

class ReviseDecisionDraftRequest(CamelModel):
    # identical field set to CreateDecisionDraftRequest minus user_id
    # (ownership is fixed at creation, never revised, per §3.5) plus:
    expected_latest_event_id: str | None = None  # optimistic-conflict guard, §6.4
```

`CommitDecisionDraftRequest` takes no body — commit uses exactly whatever the draft's own latest `revised` event already holds; this is the direct engineering meaning of `ADR-DD-001` §3's "constructed fresh from whatever the draft held at the moment of commit." Allowing the commit call to also carry last-minute overrides would blur the commit boundary the ADR treats as load-bearing, so it is deliberately not offered.

### 6.3 Responses

```python
class DecisionDraftResponse(CamelModel):
    draft_id: uuid.UUID
    case_id: uuid.UUID
    user_id: uuid.UUID
    status: Literal["active", "abandoned", "committed"]
    decision_type: str | None
    subject: str | None
    reason: str | None
    confidence: int | None
    decided_at: datetime | None
    source: str | None
    situation: str | None
    portfolio_relevance: str | None
    capital_considerations: str | None
    alternatives_considered: list[str]
    uncertainties: list[str]
    committed_decision_id: uuid.UUID | None
    latest_event_id: str          # for a future PATCH's own expected_latest_event_id
    created_at: datetime          # recorded_at of the first (revised) event
    updated_at: datetime          # recorded_at of the latest event

class DecisionDraftSummaryResponse(CamelModel):  # daily-brief-summary only
    draft_id: uuid.UUID
    case_id: uuid.UUID
    subject: str | None
    created_at: datetime

class CommitDecisionDraftResponse(CamelModel):
    decision: DecisionSummary          # reused, unmodified, from decision/schemas.py
    decision_context: DecisionContextResponse | None  # reused, unmodified, from decision_context/schemas.py
    draft: DecisionDraftResponse       # the now-committed draft, status="committed"
```

Reusing `DecisionSummary` and `DecisionContextResponse` directly (rather than redefining equivalent shapes) is a deliberate application of "reuse existing infrastructure wherever possible" — the commit endpoint returns exactly what those two existing aggregates' own schemas already say a `Decision`/`DecisionContext` look like.

### 6.4 Errors

| Condition | Exception | HTTP | Precedent |
|---|---|---|---|
| `case_id` in the URL does not correspond to an existing `Case` | `CaseNotFoundError` | 404 | Same shape as `DecisionNotFoundError` in `decision_context/exceptions.py` |
| `draft_id` does not exist | `DecisionDraftNotFoundError` | 404 | Same |
| `PATCH`/`abandon`/`commit` called on a draft whose latest event is already `abandoned` | `DecisionDraftAlreadyAbandonedError` | 409 | Same status-conflict shape as `DuplicateDecisionContextError` |
| `PATCH`/`commit` called on a draft whose latest event is already `committed` | `DecisionDraftAlreadyCommittedError` | 409 | Same |
| `PATCH` supplies `expected_latest_event_id` that does not match the server's actual latest event | `DecisionDraftConflictError` | 409 | Same 409-on-conflict shape as `ConflictingConfirmationError` |
| `commit` called while required `Decision` fields are missing/invalid on the draft's own current content | Whatever `Decision.register()`'s own value objects already raise (`MissingSubjectError`, `MissingReasonError`, `InvalidConfidenceError`, `InvalidDecisionTypeError`) | 400 | **Not re-implemented** — `DecisionDraftService.commit()` lets these propagate from the unmodified `Decision.register()` call, then a shared error handler (reusing `decision`'s own exception-to-HTTP mapping, extended to be registered for this router too) translates them, exactly as `decision`'s own router already does for direct `POST /decisions` calls |
| Validation error on any draft-content field type (e.g. `confidence` not an int) | FastAPI/Pydantic's own automatic 422 | 422 | Standard framework behavior, unchanged |

### 6.5 Authorization

None — matching every existing endpoint in this codebase (§1 Non-goals). `user_id` is supplied by the client and trusted, exactly as `CreateDecisionRequest.user_id` already is today.

### 6.6 Validation

Two layers, exactly matching `DecisionContext`'s own split: (1) Pydantic/FastAPI schema-level validation (types, required-ness of `user_id` specifically) at the transport boundary; (2) no domain-level content validation at all for draft fields (§2.3) — deferred entirely to commit time, where it is the *existing*, unmodified `Decision`/`DecisionContext` validation that runs, not new validation written for this feature.

---

## 7. Alpha UI

No existing component to extend (§2.4); this is new frontend surface. Proposed location: `frontend/src/decisionWorkspace/` (new directory — this is the Decision Workspace UX-009 has always described but which has never had frontend code before), containing `decisionDraftApi.ts` (typed client, directly modeled on `securityConfirmationApi.ts`'s own shape: plain `fetch` wrappers, no state management library, no caching) and the Decision Workspace's own form component(s), which this document does not further design — UI component structure is a UI-team implementation detail, not an architecture question `ADR-DD-001` or this design document governs.

### 7.1 Draft UX

The Decision Workspace form auto-saves: on every meaningful field blur (or a short debounce while typing free-text fields), the client calls `PATCH /decision-drafts/{draftId}` (or `POST .../decision-drafts` if no `draftId` exists yet for this editing session) with the form's current full state. No explicit "Save" button is required for draft persistence — matching UX-009's own cross-session-persistence requirement (`ADR-DD-001`'s own Problem statement: "a draft must survive panel collapse, page navigation, browser refresh"). The client keeps `draftId` and `latestEventId` in local component state (not `sessionStorage` — a page refresh should re-fetch from the server via `GET /decision-drafts/{draftId}`, which is authoritative, rather than trust a client-cached copy that could be stale).

### 7.2 Resume Draft

`GET /cases/{caseId}/decision-drafts` populates a "You have N draft(s) for this Case" affordance wherever the Decision Workspace is entered for a Case that already has Active drafts. Selecting one calls `GET /decision-drafts/{draftId}` and populates the form from the response. Per `ADR-DD-001` §4, this full-content read is legitimate here (unlike Daily Brief's own narrow projection) — resuming genuinely requires the full content to repopulate the form.

### 7.3 Discard Draft

Calls `POST /decision-drafts/{draftId}/abandon`. Idempotent client-side too: disable the control immediately on click (no need to wait for the response before reflecting "discarded" in the UI), matching the backend's own idempotent handling of a double-call.

### 7.4 Commit Draft

Calls `POST /decision-drafts/{draftId}/commit` with no body (§6.2). On success, the response's `decision.id` becomes the canonical Decision the UI now navigates to or confirms; the draft itself is no longer editable (its own `status` is now `"committed"`) and should disappear from any "resume draft" list on the client's next fetch. On a `MissingSubjectError`/`MissingReasonError`/`InvalidConfidenceError`/`InvalidDecisionTypeError` 400 (§6.4), the UI surfaces the specific missing/invalid field(s) inline on the form — the same fields the investor would need to fill in for a direct, non-draft `POST /decisions` call today, since commit performs exactly that same construction.

### 7.5 Conflict handling

Directly reusing the established pattern from `confirmSecuritySelection` (`securityConfirmationApi.ts`): every `PATCH` call includes the client's own last-known `latestEventId` as `expectedLatestEventId`. On a `409 DecisionDraftConflictError` (another tab/session revised the same draft since this client last read it), the client re-fetches `GET /decision-drafts/{draftId}` and either (a) shows the investor the newer server state before allowing further edits, or (b) — the simpler v1 behavior, matching this codebase's own general bias toward "no silent overwrite, but no elaborate merge UI either" — surfaces a plain "This draft was updated elsewhere; reload to continue editing" message with a reload action. No field-level merge UI is designed here; multi-tab/multi-session editing of the same draft is not a scenario `ADR-DD-001` treats as needing more than last-write-rejected-with-a-clear-message handling (its own Open Questions explicitly defer full collaboration support).

---

## 8. Migration Plan

### 8.1 New files

```
atlas/core/domain/decision_draft/
    __init__.py
    entity.py                 # DecisionDraftEvent dataclass + DraftId-keyed derivation helpers
    value_objects.py          # DraftId
    exceptions.py             # DecisionDraftError and subclasses (§6.4)
    repository.py             # DecisionDraftEventRepository Protocol

atlas/core/application/decision_draft/
    __init__.py
    decision_draft_service.py # DecisionDraftService: create/revise/abandon/commit/get/list_active_for_case/list_events/daily_brief_summary

atlas/core/infrastructure/persistence/decision_draft/
    __init__.py
    table.py                  # decision_draft_events_table, create_decision_draft_events_table
    sqlalchemy_repository.py  # SqlAlchemyDecisionDraftEventRepository

atlas/core/infrastructure/api/decision_draft/
    __init__.py
    schemas.py                 # requests/responses, §6.2-6.3
    router.py                  # routes, §6.1
    errors.py                  # exception -> HTTP mapping, §6.4
    dependencies.py            # FastAPI Depends wiring

frontend/src/decisionWorkspace/
    decisionDraftApi.ts         # typed client, §7
```

### 8.2 Modified files

- `atlas/core/infrastructure/api/app.py` — two additions, in the same style as the existing `decision_context_router`/`register_decision_context_error_handlers` lines: `app.include_router(decision_draft_router)` and `register_decision_draft_error_handlers(app)`. No other change to this file.

No other existing file is modified. In particular: `atlas/core/domain/decision/entity.py`, `atlas/core/domain/decision/repository.py`, `atlas/core/domain/decision_context/entity.py`, `atlas/core/domain/decision_context/repository.py`, `atlas/core/domain/case/entity.py`, and every file under `atlas/alpha/security_confirmation/` remain byte-for-byte unchanged.

### 8.3 Affected tests

New (mirroring `tests/unit/**/decision_context/`'s own layout exactly):

```
tests/unit/domain/decision_draft/test_entity.py
tests/unit/domain/decision_draft/test_value_objects.py
tests/unit/application/decision_draft/test_decision_draft_service.py
tests/unit/infrastructure/persistence/decision_draft/test_sqlalchemy_repository.py
tests/unit/infrastructure/api/decision_draft/test_router.py
```

No existing test file is modified — `DecisionDraft` introduces no change to `Decision`, `DecisionContext`, or `Case`'s own behavior, so their existing test suites (`tests/unit/domain/decision/`, `tests/unit/domain/decision_context/`, `tests/unit/domain/case/`, and each layer above them) require no edits and should be re-run only as an unmodified regression check (§9.5).

---

## 9. Testing Strategy

**Unit — domain (`tests/unit/domain/decision_draft/`).** `DraftId` generation/uniqueness (mirrors `test_value_objects.py` for `ContextId`). `DecisionDraftEvent` construction for each of the three `event_type` values; confirm the dataclass is frozen (no mutation possible).

**Unit — application (`tests/unit/application/decision_draft/`).** For `DecisionDraftService`: `create()` writes exactly one `revised` event with a fresh `draft_id`; `revise()` appends a new `revised` event and never mutates the prior one; `revise()`/`abandon()`/`commit()` each reject being called after the draft is already `abandoned` or `committed` (409-mapped exceptions); `abandon()` is idempotent (calling twice writes exactly one `abandoned` event); `commit()` on a fully-populated draft calls the real, unmodified `Decision.register()` and (when context fields are present) `DecisionContext.capture()`, persists both via their own real repositories, and only then appends the `committed` event carrying the resulting `decision_id`; `commit()` on a draft missing a required `Decision` field propagates the exact exception `Decision.register()`/its value objects raise, unmodified — this is the single most important test in this suite, since it is the direct, executable proof that the commit boundary in `ADR-DD-001` §3 was not reimplemented; `commit()` on an already-committed draft raises `DecisionDraftAlreadyCommittedError` without touching `DecisionRepository`/`DecisionContextRepository` again (no duplicate `Decision` created) — the concrete regression test for the partial-failure risk named in §10; ordering under an injected fixed clock (mirroring `security_confirmation/service.py`'s own `clock=lambda: ...` test pattern) confirms `_next_recorded_at` prevents same-instant ordering ambiguity.

**Integration — persistence (`tests/unit/infrastructure/persistence/decision_draft/`).** `SqlAlchemyDecisionDraftEventRepository` against a real (in-memory/temp-file) SQLite engine: `add`/`get_latest_event`/`list_events`/`list_latest_by_case` round-trip correctly, including JSON round-trip for `alternatives_considered`/`uncertainties`; `get_latest_event` correctly orders by `(recorded_at DESC, id DESC)` when two events share an identical `recorded_at` (constructed directly in the test, not relying on real-clock timing); `sync_table_schema` creates the table cleanly on a fresh engine (mirrors `decision_context`'s own persistence test setup).

**API (`tests/unit/infrastructure/api/decision_draft/`).** Every route in §6.1 against FastAPI's `TestClient`, mirroring `decision_context/test_router.py`'s own structure: 201 on create, 200 on read/list, 200 on revise, 204 on abandon, 200 on commit returning the composed `CommitDecisionDraftResponse`, 404/409/400/422 for each error condition in §6.4's table, and a dedicated test that `GET /decision-drafts/daily-brief-summary` response never contains `reason`, `confidence`, `situation`, or any other full-content field — a direct, automated enforcement of `ADR-DD-001` §4's own narrow-projection invariant, not merely a documented intention.

**End-to-end.** One test exercising the full product flow against real (non-mocked) repositories: create a draft with partial content → revise it twice → commit it → assert a real `Decision` row and (if context fields were present) a real `DecisionContext` row now exist, correctly populated from the draft's own final content, and that the draft's own `GET` now returns `status: "committed"` with the correct `committedDecisionId`. This is the executable form of `ADR-DD-001`'s own central claim ("a new Decision is constructed fresh from whatever the draft held at the moment of commit") and should be treated as the definitive conformance check for §3 of that ADR.

**Regression.** Full existing suite (`tests/unit/domain/decision/`, `decision_context/`, `case/`, and `tests/unit/alpha/security_confirmation/`) re-run unmodified, confirming zero behavioral change to any aggregate this design reuses but does not touch.

---

## 10. Risks

**Technical.**
- *Partial commit failure.* `commit()` performs three sequential, independently-transacted writes (`Decision` insert, optional `DecisionContext` insert, `committed` event insert) — the same non-atomic-across-calls risk profile `security_confirmation/service.py`'s own `correct()` already carries and this codebase already accepts (it writes a `revoked` and a `confirmed` event as two separate transactions). If the process crashes between the `Decision` insert and the `committed` event insert, the resulting `Decision` is real and correct, but the draft would still show as `"active"`, and a retried `commit()` call would create a *second* `Decision`. **Mitigation implemented in this design:** none beyond the idempotency guard against re-committing an *already-committed* draft (§6.4) — this specific gap (crash mid-commit, before the terminal event lands) is not fully closed by that guard and is accepted as a known, low-probability, already-precedented risk class in this codebase, not newly introduced here. **Explicitly not recommended:** wrapping all three writes in a single cross-repository transaction — this would be a new abstraction this codebase does not use anywhere else, and is disproportionate to a risk every other multi-write operation here already accepts.
- *JSON-encoded list columns.* `alternatives_considered`/`uncertainties` reuse `decision_contexts_table`'s own JSON-string-in-a-`String`-column convention — a known, accepted, existing pattern in this codebase (not SQLite JSON1), inheriting whatever limitations that convention already has (no server-side querying into list contents; acceptable, since nothing in this design needs it).

**Migration.** None — every new table is additive (`sync_table_schema` creates it fresh); no existing table's schema changes.

**Performance.** `list_latest_by_case` (used by both `GET /cases/{case_id}/decision-drafts` and, filtered, the Daily Brief projection) requires, per current design, reading every event row for a Case and reducing to the latest per `draft_id` — for typical draft counts (a handful per Case) this is trivial; if draft volume per Case ever grows unusually large, a materialized "latest event id per draft" side-index would be the natural future optimization, not required at this scale and not built now (avoiding a new abstraction not yet justified by evidence, per this program's own recurring discipline).

**Future compatibility.** The `committed_decision_id` back-reference (§4) is exactly the shape `ADR-DD-001` §5 requires for any *future* reverse reference — nothing here forecloses `ADR-CR-001`'s own Reconsideration workflow (should it later be built) from starting a reconsideration as a fresh `DecisionDraft`, since draft creation has no dependency on why the investor is creating one.

---

## 11. Conformance Matrix

| `ADR-DD-001` Decision point | Implemented by | Verification method |
|---|---|---|
| §1 — Adopt `DecisionDraft`, Case-scoped, optional-never-`decision_id` identity | §3.2–§3.3: `DraftId`, `case_id`/`user_id` fields, no `decision_id` field anywhere on draft content | `tests/unit/domain/decision_draft/test_entity.py`; schema review (§5.2 has no `decision_id` column) |
| §2 — Event-sourced lifecycle, append-only, derived current state | §3.1, §3.5, §4: `decision_draft_events` table, `get_latest_event` derivation, no update method on the repository Protocol | `tests/unit/infrastructure/persistence/decision_draft/test_sqlalchemy_repository.py`; Protocol has no `update`/`revise` method to call by accident (type-level enforcement, matching `DecisionRepository`'s own docstring reasoning) |
| §3 — Commit boundary remains unmodified `Decision.register()`/`DecisionContext.capture()` | §6.4 (errors table), §9 (application test): `commit()` calls both classmethods directly, unmodified, and lets their own validation exceptions propagate | The dedicated "commit on incomplete draft propagates `Decision`'s own exception, unmodified" unit test (§9); the end-to-end test (§9) |
| §4 — Daily Brief narrow-projection-only | §6.1 (`GET .../daily-brief-summary`), §6.3 (`DecisionDraftSummaryResponse`) | The dedicated API test asserting the summary response never contains full-content fields (§9) |
| §5 — Any future `Decision`-side draft reference must be optional/additive; `IMPORT`/`API`/`BROKER_SYNC` never pass through a draft | §4 (`committed_decision_id` is additive, on the *event*, never a required field on `Decision` itself); no change to `Decision`'s own `source`/value objects (§2.2, §8.2) | Regression suite (§9) confirms `Decision`'s own schema/entity is byte-for-byte unchanged |
| §6 — Rejected models (transient-only; mutable `DRAFT` status on `Decision`; `DecisionContext` doubling as draft; generic untyped state bag; event-only with no derived projection) | §3.1 (physical table + derived projection, not event-only); §2.3 (no field added to `Decision`); §3 generally (a dedicated, typed aggregate, not a generic bag) | Code review against this document; `Decision`'s own entity file has no new field (§8.2 confirms no modification) |

---

## 12. Definition of Done

- [ ] All eight new packages/modules listed in §8.1 exist, each containing exactly the files listed, no more, no fewer.
- [ ] `atlas/core/infrastructure/api/app.py` contains exactly the two additions in §8.2 and no other change.
- [ ] `Decision`, `DecisionContext`, `Case`, and every file under `atlas/alpha/security_confirmation/` are confirmed byte-for-byte unchanged (`git diff --stat` shows zero lines touched in any of them).
- [ ] Every route in §6.1 is implemented exactly as specified, including the exact error/status-code mapping in §6.4 — no additional, undocumented routes, no additional, undocumented request/response fields.
- [ ] `commit()` calls `Decision.register()` and (when applicable) `DecisionContext.capture()` directly — grep-verifiable: no draft-specific reimplementation of either classmethod's own validation logic exists anywhere in `decision_draft_service.py`.
- [ ] All five test suites in §8.3 exist and pass; the full existing regression suite (§9) passes unmodified.
- [ ] The dedicated Daily Brief narrow-projection test (§9) passes, proving §4's own invariant is enforced, not merely documented.
- [ ] The dedicated "commit propagates `Decision`'s own validation error unmodified" test (§9) passes, proving §3's own commit-boundary invariant is enforced, not merely documented.
- [ ] The end-to-end test (§9) passes against real, non-mocked repositories.
- [ ] Every row of the Conformance Matrix (§11) has a passing, named test or a direct code-review artifact cited against it — no row left as "trust the design."
- [ ] No `TODO`, `FIXME`, `NotImplementedError`, or placeholder return value exists anywhere in the new code.
- [ ] This document's own Section 3.6 implementation-level resolutions (abandon = delete; no cap on concurrent drafts per Case) are called out explicitly in the PR description that ships this feature, so a future reader does not mistake them for `ADR-DD-001`'s own text.

## Related

`docs/ADR-DD-001-Decision-Draft.md` (the ADR this document implements). `docs/ADR-DC-001-Decision-Context.md`, `docs/ADR-CR-001-Decision-Review-and-Supersession.md` (neighboring, already-Accepted Wave 1 ADRs whose entities this design reuses unmodified). `docs/ADR-DD-001-Conformance-Report.md` (Sprint 7's own audit, the direct predecessor of this sprint's own "Not Implemented" starting point). `atlas/alpha/security_confirmation/` (the direct persistence-pattern template, reused at the pattern level only — see §2.1).
