# Knowledge Domain

Sprint 39 introduces the Atlas Knowledge domain.

The Knowledge domain stores structured facts, source attribution, and explicit
relationships. It does not generate opinions, predictions, or conclusions.

## Domain Responsibility

The domain is responsible for:

- Knowledge nodes.
- Knowledge relationships.
- Attributed knowledge facts.
- Source references.
- Deterministic in-memory collections.
- Simple deterministic queries.

It is not responsible for AI reasoning, semantic search, vector retrieval, or
graph database persistence.

## Relationship Model

Relationships are explicit structure only. Supported relationships include:

- Company -> Sector
- Company -> Industry
- Company -> Country
- Company -> Competitor
- Company -> Supplier
- Company -> Customer
- Company -> Technology
- Company -> Theme
- Theme -> Theme

The relationship engine creates edges. It does not infer missing relationships.

## Source Model

Every `KnowledgeFact` supports:

- `source`
- `timestamp`
- `confidence`
- `evidence_reference`

This keeps Atlas aligned with evidence before opinion. Future reasoning engines
should be able to trace facts back to their origin.

## Query Layer

`KnowledgeQueryService` supports deterministic queries:

- find connected companies
- list suppliers
- list competitors
- find companies in a theme
- retrieve facts for a company

Queries operate on `KnowledgeCollection`, an immutable in-memory collection of
nodes, edges, and facts.

## Future Graph Architecture

This sprint does not implement a graph database.

Future backends such as SQLite, PostgreSQL, or a graph database can adapt to the
same domain models. The domain should remain provider-independent so Portfolio,
Research, Decision Engine, and future AI capabilities can depend on stable
contracts rather than storage details.

## Known Limitations

- No persistence.
- No graph database.
- No embeddings.
- No semantic search.
- No LLM calls.
- No inferred conclusions.
- Duplicate handling keeps the last supplied object for each id and returns
  collections sorted by id.
