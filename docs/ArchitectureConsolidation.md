# Architecture Consolidation (Sprint 44)

This document records the current state of Atlas architecture as of Sprint 44,
clarifies which layers are current vs. legacy, and defines guardrails for
future sprints. It does not change runtime behavior.

## Current Layers

Atlas currently has two parallel layers that have not yet been merged:

### 1. Blueprint-aligned layer (current architecture)

- `atlas/domains/` — owns canonical concepts and contracts: `portfolio`,
  `watchlist`, `research`, `decision`, `decision_journal`, `daily_brief`,
  `knowledge`, `ai`, `authentication`. Domains depend only on
  `atlas.shared` entities.
- `atlas/capabilities/` — composes domains into product-level, deterministic
  reasoning: `company_analysis`, `discovery`, `watchlist_intelligence`.
  Capabilities depend on domains, not on providers or legacy engines.
- `atlas/shared/` — canonical, immutable entities (`Portfolio`, `Holding`,
  `Company`, `Watchlist`, `ResearchNote`, `JournalEntry`, `User`,
  `MarketEvent`, `Decision`, `KnowledgeNode`).

This is the architecture all new product work should build on.

### 2. Legacy / engine layer (compatibility, not for expansion)

Modules such as `atlas/analysis/`, `atlas/portfolio_review/`,
`atlas/watchlist_review/`, `atlas/comparison/`, `atlas/conversation/`,
`atlas/dashboard/`, `atlas/daily/`, `atlas/decision_journal/` (top-level),
`atlas/economics/`, `atlas/evidence/`, `atlas/home/`, `atlas/intelligence/`,
`atlas/language/`, `atlas/market/`, `atlas/memory/`, `atlas/monitoring/`,
`atlas/principles/`, `atlas/profile/`, `atlas/reasoning/`, `atlas/risk/`,
`atlas/risk_drift/`, `atlas/suitability/`, `atlas/themes/`, `atlas/database/`,
`atlas/services/`, `atlas/models/` are the original working engines that
predate the domain/capability split. They remain functional and fully
tested, and the CLI currently calls them exclusively.

These modules are compatibility layers. They should not gain new
responsibilities; new product capabilities belong in
`atlas/domains`/`atlas/capabilities`.

### 3. Provider layer

`atlas/providers/` defines `CompanyDataProvider` (interface),
`MockCompanyAnalysisProvider` (default, no network access), and
`YahooFinanceProvider` (live HTTP calls via `urllib.request.urlopen`,
`atlas/providers/yahoo.py`).

### 4. CLI / runtime layer

`atlas/cli/main.py` is the Typer entry point (`atlas` console script). As of
this sprint, **every CLI command imports exclusively from the legacy engine
layer and `atlas.services`** — there are no imports from `atlas.domains` or
`atlas.capabilities` in the CLI today. This is the central migration gap:
the Blueprint-aligned layer exists and is tested, but nothing user-facing
exercises it yet.

## Known Duplication

- Portfolio reasoning exists both as `atlas.analysis.portfolio` (legacy,
  CLI-wired) and `atlas.domains.portfolio` (Blueprint-aligned, not
  CLI-wired).
- Decision/decision-journal logic exists both as top-level
  `atlas/decision/`, `atlas/decision_journal/` (legacy, CLI-wired) and
  `atlas.domains.decision`, `atlas.domains.decision_journal`
  (Blueprint-aligned, not CLI-wired).
- Watchlist reasoning exists both as `atlas.analysis.watchlist` /
  `atlas.watchlist_review` (legacy, CLI-wired) and `atlas.domains.watchlist`
  / `atlas.capabilities.watchlist_intelligence` (Blueprint-aligned, not
  CLI-wired).

This duplication is expected during a deliberate migration and is not itself
a defect. It becomes a defect if the legacy layer keeps growing instead of
shrinking.

## Migration Path

1. Pick one duplicated concern at a time (e.g. portfolio).
2. Migrate the corresponding CLI command(s) to call the
   `atlas.domains`/`atlas.capabilities` structures instead of the legacy
   module.
3. Add tests proving behavioral parity with the legacy command before
   removing the legacy call site.
4. Only delete legacy code once nothing references it and parity is proven.
5. Repeat per concern. Do not attempt a single big-bang rewrite.

## Rules for Future Sprints

- New product capabilities are built in `atlas/domains` and
  `atlas/capabilities`, not in the legacy engine layer.
- Domains must not import capabilities, providers, the CLI, or
  frontend/backend/database/services modules.
- Capabilities must not call external APIs or providers directly.
- Providers remain opt-in: importing Atlas, running its test suite, or
  invoking default CLI commands must never trigger network access. Live
  providers are only reachable through explicit flags (e.g.
  `atlas analyze TICKER --provider yahoo`).
- Legacy engine modules may be bug-fixed but should not gain new features.
- No naming that implies "Atlas Edge" (a separate, unrelated product) should
  appear in code, filenames, or docs. If found, it is technical debt to
  rename or remove.
