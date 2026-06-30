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

## 2026-06-30: Model Research as Structured Understanding

Decision: implement `atlas.domains.research` as research projects, notes,
questions, assumptions, evidence references, thesis fragments, summaries, and
validation.

Rationale: research should connect curiosity, evidence, assumptions, and open
questions before Atlas reaches conclusions. Keeping Research independent of AI,
UI, persistence, providers, and recommendations preserves the Blueprint
principle that understanding comes before judgment.

## 2026-06-30: Build Company Analysis as a Capability

Decision: implement `atlas.capabilities.company_analysis` as a consumer of
Company, Knowledge, Research, and Decision structures rather than as a new
domain owner.

Rationale: Company Analysis should organize existing structured evidence into
explainable business understanding. Keeping it in `atlas.capabilities` prevents
it from owning Knowledge, Research, or Decision responsibilities and preserves
the Blueprint principle that Atlas helps investors understand businesses before
forming conviction.

## 2026-06-30: Build Watchlist Intelligence as Structured Observation

Decision: implement `atlas.capabilities.watchlist_intelligence` as a consumer of
Research, Knowledge, and Company Analysis structures rather than as a domain
owner.

Rationale: a watchlist should help investors track unanswered questions without
creating noise or trading behavior. Keeping Watchlist Intelligence in
`atlas.capabilities` preserves clean domain ownership and reinforces the
Blueprint principle that Atlas supports understanding before action.

## 2026-06-30: Build Discovery as Structured Curiosity

Decision: implement `atlas.capabilities.discovery` as a deterministic consumer
of Knowledge, Research, Company Analysis, and Watchlist Intelligence structures.

Rationale: Discovery should help investors decide what deserves further study,
not what action to take. Keeping it in `atlas.capabilities` preserves domain
ownership boundaries and aligns with the Blueprint principle that discovery is
the disciplined pursuit of understanding before conviction.

## 2026-06-30: Introduce `atlas.adapters` as the Legacy-to-Domain Bridge

Decision: add `atlas.adapters.portfolio.legacy_portfolio_to_domain_portfolio`
and a new, additive `atlas portfolio summary` CLI command that calls
`atlas.domains.portfolio` directly, instead of rewriting the existing
`atlas portfolio analyze`/`atlas portfolio review` commands.

Rationale: the legacy CLI portfolio file format
(`atlas.analysis.portfolio.Portfolio`, positions with a relative `weight`
and no absolute market value) answers a different question (ticker-fit
analysis, CIO review with provider/profile/market dependencies) than the
Portfolio Domain (portfolio understanding: allocation, concentration,
validation). Forcing the existing commands onto the domain would have been
a disguised behavior change, not a safe migration. Adding `atlas.adapters`
as the one layer permitted to import both legacy and domain code lets the
CLI begin exercising `atlas.domains.portfolio` today, on a read-only path,
without touching the two existing commands or their output. Architecture
boundary tests were updated so domains may never import adapters back,
keeping the dependency direction one-way (legacy/CLI -> adapters -> domains).
