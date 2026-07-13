# ADR-004 — API Serialization Standard

**Status:** Implemented. Atlas's first Product Increment after the v0.1.0-beta baseline freeze.

---

## Context

API-001 (Decision Capture) and API-002 (Decision Context) were each
implemented literally per their own specifications. API-001's endpoints
serialize JSON in snake_case (`decision_type`, `decided_at`). API-002's
specification gave an explicit worked example in camelCase
(`portfolioRelevance`, `capturedAt`), implemented literally as given.

The result: two live endpoints under the same API with two different JSON
casing conventions. This was flagged as a non-blocking observation in both
increments' delivery reports and documented in
[docs/DecisionContextAPI002.md §5, §10](DecisionContextAPI002.md).

## Decision

- **camelCase** for all public REST API request/response bodies.
- **snake_case** internally — Python domain, application, and
  infrastructure code (including the Python attribute names on the API
  schema classes themselves) keeps its existing convention throughout.

The boundary between the two stays exactly where API-002 already put it:
pydantic schemas at the API layer translate between the wire format and
the Python-side attribute names via an alias generator, so this is a
serialization-layer decision only — it does not reach into domain models,
value objects, or persistence.

**Implementation:** a single shared base,
`atlas.core.infrastructure.api.serialization.CamelModel`
(`alias_generator=to_camel`, `populate_by_name=True`), used by every schema
class under `atlas/core/infrastructure/api/**/schemas.py`. API-002's
schemas already had this pattern locally (`_CamelModel`); they now import
the shared one instead, with no behavior change. API-001's schemas
(`CreateDecisionRequest`, `DecisionSummary`, `DecisionCreatedResponse`)
were the only ones that changed behavior: `userId`, `decisionType`,
`decidedAt`, `recordedAt` replace `user_id`, `decision_type`, `decided_at`,
`recorded_at` on the wire.

## Migration Approach (resolves "Why Deferred" below)

**Responses:** a single coordinated cutover, not versioning or a
deprecation window. Every API-001 response is camelCase now,
unconditionally. Atlas is local-only with no evidence of external
integrators depending on the pre-standard format; introducing API
versioning or dual-format response negotiation for a Beta-stage,
not-yet-externally-consumed API would have been exactly the kind of
speculative, generic-enterprise machinery this project's engineering
discipline has consistently avoided.

**Requests:** `populate_by_name=True` means a request body may still use
the old snake_case keys (`user_id`, `decision_type`, ...) — this was
already true for API-002 before this ADR, and now holds for API-001 too.
This is the concrete backward-compatibility guarantee: any existing caller
sending a snake_case request body continues to work unchanged; only the
response format is a clean, unconditional cutover.

## Why It Was Deferred (historical)

At the time this ADR was written, changing API-001's existing snake_case
responses inside an unrelated Product Increment would have been exactly
the kind of incidental refactor the engineering discipline established
across API-001 and API-002 had deliberately avoided. It was scoped as its
own increment specifically so the migration approach above could be
decided deliberately, on its own terms, rather than as a side effect of
other work — which is what happened once its own Product Increment
specification arrived.

## Action

Done. See [DecisionCaptureAPI001.md](DecisionCaptureAPI001.md) and
[DecisionContextAPI002.md](DecisionContextAPI002.md) for the per-endpoint
detail; both docs' notes about the casing inconsistency this ADR describes
have been updated to reflect that it's now resolved.
