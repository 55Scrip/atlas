# Sprint 36 Summary

## Sprint Mission

Sprint 36 marks Atlas Edge's transition from blueprint to implementation.

The mission was to strengthen the platform foundation without adding product
features. The sprint focused on architecture, domain ownership, canonical shared
models, AI service boundaries, documentation, and code quality tooling.

## What Changed

- Added canonical shared entities in `atlas/shared`.
- Added domain boundary packages in `atlas/domains`.
- Added AI service interfaces in `atlas/ai`.
- Added top-level repository boundaries for future frontend, backend, shared
  packages, AI services, and infrastructure.
- Added strict TypeScript configuration for future frontend work.
- Added CI and local hook configuration.
- Added architecture and development documentation.
- Added tests that protect the new foundation.

No existing user-facing behavior was changed.

## Alignment With Atlas Blueprint

These changes align with Atlas Blueprint by prioritizing:

- Simplicity before sophistication.
- Explainable and deterministic systems.
- Modular ownership boundaries.
- Long-term maintainability.
- Human judgment over automation.

The sprint avoided building advanced AI, UI, or new investment features before
the platform foundation was ready.

## New Project Structure

```text
atlas/
  ai/                 Future AI service interfaces
  domains/            Domain ownership boundaries
  shared/             Canonical shared entities
  ...                 Existing deterministic Atlas engines
frontend/             Future TypeScript user interface
backend/              Backend boundary documentation
shared/               Future shared package artifacts
ai_services/          Future AI service implementations
infrastructure/       Deployment and operational configuration
docs/                 Product and architecture documentation
tests/                Python unit and smoke tests
.github/workflows/    CI configuration
```

## New Domain Boundaries

Sprint 36 introduced explicit domain ownership boundaries for:

- Portfolio
- Watchlist
- Research
- Decision Journal
- Daily Brief
- Knowledge
- AI
- Authentication

These packages are intentionally thin. They define ownership and public
contracts without moving existing engines or duplicating business logic.

## New Shared Entities

Canonical entities now live in `atlas.shared.entities`:

- `Portfolio`
- `Holding`
- `Company`
- `Watchlist`
- `ResearchNote`
- `JournalEntry`
- `User`
- `MarketEvent`
- `Decision`
- `KnowledgeNode`

These models are immutable dataclasses. Metadata fields are frozen to reduce
hidden mutation and make future cross-service usage safer.

## New AI Service Interfaces

`atlas.ai` now defines replaceable protocol interfaces for future AI services:

- `ReasoningService`
- `KnowledgeService`
- `SummaryService`
- `DiscoveryService`
- `DecisionEngine`

These are contracts only. Sprint 36 does not add LLM calls, live AI workflows,
or advanced automation.

## Code Quality Tooling Added

- Strict TypeScript configuration in `frontend/tsconfig.json`.
- Frontend package metadata in `frontend/package.json`.
- Ruff lint configuration in `pyproject.toml`.
- Local hook configuration in `.pre-commit-config.yaml`.
- CI workflow in `.github/workflows/ci.yml`.

## Tests Run And Result

Verification commands:

```bash
python -m compileall atlas tests
pytest
```

Result at implementation time:

- Compile check passed.
- Full test suite passed.

## Known Limitations

- The frontend directory is a foundation only; no UI application exists yet.
- AI services are interfaces only; no AI implementation exists yet.
- Top-level `backend/`, `shared/`, `ai_services/`, and `infrastructure/`
  directories are boundary markers, not complete deployable systems.
- Existing engines have not yet migrated to the new domain packages.
- CI is configured for Python verification only; future frontend CI should be
  expanded when frontend code exists.

## Recommended Next Sprint

The next sprint should connect one existing engine to the new foundation in a
small, reversible way.

Recommended direction:

- Pick one domain, such as Portfolio or Watchlist.
- Use the new canonical shared entities at the boundary.
- Avoid broad migrations.
- Keep public behavior unchanged.
- Add tests proving the new boundary improves clarity without adding coupling.

