# Atlas Decision Log

This log records architectural decisions that shape future development.

## 2026-06-29: Keep Sprint 36 as a Foundation Sprint

Decision: establish boundaries, canonical entities, docs, CI, hooks, and AI
interfaces without rewriting existing engines.

Rationale: Atlas already has working deterministic engines. A large migration
would add risk without improving the investor experience.

## 2026-06-29: Use Python Backend as the Source of Truth

Decision: keep existing backend code under `atlas/` and document `backend/` as
the backend boundary.

Rationale: this preserves all existing APIs and test coverage while making the
repository easier to navigate.

## 2026-06-29: Add Strict TypeScript Configuration Before Frontend Code

Decision: add `frontend/tsconfig.json` and `frontend/package.json` with strict
type checking, but no frontend runtime.

Rationale: future UI work should start from strong defaults without forcing an
application framework too early.

## 2026-06-29: Define AI as Interfaces First

Decision: create `atlas.ai` protocols for reasoning, knowledge, summary,
discovery, and decision support services.

Rationale: Atlas should remain deterministic and explainable until concrete AI
services can be evaluated against the Constitution.

## 2026-06-29: Build Portfolio as the First Real Domain

Decision: implement deterministic portfolio calculations, validation, and
structured observations inside `atlas.domains.portfolio`.

Rationale: portfolio understanding is foundational to Atlas. A portfolio is not
just a list of positions; it is a collection of investment decisions. The domain
therefore starts with value, allocation, concentration, and data quality before
any user-facing action language.

## 2026-06-29: Separate Decision Reasoning From Recommendations

Decision: add `atlas.domains.decision` as a non-advisory reasoning foundation
instead of modifying the older action-oriented `atlas.decision` package.

Rationale: Sprint 38 is about evidence, observations, unknowns, confidence, and
explainability. Keeping the new domain separate preserves existing behavior and
gives future AI services a deterministic reasoning contract.

## 2026-06-30: Model Knowledge as Attributed Facts

Decision: implement `atlas.domains.knowledge` as immutable nodes, edges,
facts, sources, references, and deterministic queries.

Rationale: Atlas knowledge should be structured evidence, not generated
opinion. The domain should remain independent of AI providers, vector databases,
and graph storage so future Portfolio, Research, Decision Engine, and AI layers
can share the same factual foundation.
