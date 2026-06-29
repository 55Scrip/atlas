# Atlas Project Structure

Sprint 36 establishes the long-term repository shape.

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
.github/workflows/    CI
```

## Canonical Models

Canonical business entities live in `atlas.shared.entities`:

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

Domain packages should import these models instead of defining competing entity
shapes.

## Domain Packages

`atlas.domains` provides stable ownership boundaries for:

- Portfolio
- Watchlist
- Research
- Decision Journal
- Daily Brief
- Knowledge
- AI
- Authentication

These packages intentionally stay small. They should collect public contracts,
not become dumping grounds for unrelated engine logic.

