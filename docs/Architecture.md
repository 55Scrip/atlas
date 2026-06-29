# Atlas Architecture

Atlas is a deterministic investment reasoning platform. The architecture favors
clear boundaries, explainable outputs, and replaceable services over hidden
automation.

## System Shape

Atlas is organized into six long-term areas:

- `frontend/`: future user interfaces.
- `backend/`: documentation pointer to the Python backend in `atlas/`.
- `atlas/shared/`: canonical entities shared across domains.
- `atlas/domains/`: domain ownership boundaries.
- `atlas/ai/`: interfaces for future AI services.
- `infrastructure/`: deployment and operational configuration.

The current product remains a Python backend and CLI. Sprint 36 adds structure
without moving existing engines or changing public behavior.

## Information Flow

Market data and user context flow into deterministic engines. Engines produce
structured outputs. Shared language and principles layers make those outputs
consistent before they reach the CLI or future UI.

```text
Providers and User Context
        ↓
Shared Entities
        ↓
Domain Engines
        ↓
Evidence, Reasoning, Suitability, Risk, Memory
        ↓
Language and Principles
        ↓
CLI and Future Frontend
```

## Domain Ownership

Each domain package exposes the canonical models or service interfaces that
belong to that area. Existing engines can migrate gradually to these boundaries
without breaking current APIs.

## AI Boundary

Atlas AI is interface-first. Reasoning, knowledge retrieval, summarization,
discovery, and decision support are defined as replaceable protocols. Future AI
implementations must explain uncertainty and preserve human judgment.

