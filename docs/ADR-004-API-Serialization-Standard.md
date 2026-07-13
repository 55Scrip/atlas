# ADR-004 — API Serialization Standard

**Status:** Proposed. Backlog item — not implemented. To be addressed as its own dedicated Product Increment, not folded into API-001, API-002, or any increment that follows before it is scheduled.

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

Not yet made. Recommendation on the table, pending its own Product
Increment:

- **camelCase** for all public REST API request/response bodies.
- **snake_case** internally — Python domain, application, and
  infrastructure code keeps its existing convention throughout.

The boundary between the two stays exactly where API-002 already put it:
pydantic schemas at the API layer translate between the wire format and
the Python-side attribute names (e.g. via an alias generator), so this is a
serialization-layer decision only — it does not reach into domain models,
value objects, or persistence.

## Why Deferred

Changing API-001's existing snake_case responses is a breaking change for
any caller already integrated against it. Addressing this now, inside an
unrelated Product Increment, would be exactly the kind of incidental
refactor the engineering discipline established across API-001 and API-002
has deliberately avoided. This is scoped as its own increment so the
migration (versioning, deprecation window, or a coordinated single cutover)
can be decided on its own terms rather than as a side effect of other work.

## Action

None at this time. Do not implement. Await a dedicated Product Increment
specification for this ADR.
