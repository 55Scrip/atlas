# Atlas

Private investment research platform. Local-only. Deterministic. Non-advisory.

**Version:** v0.1.0 — Internal Release Candidate 2 (Sprint 71)

---

## What Atlas Is

Atlas is a local deterministic investment research platform. It organises
structured data — research notes, company analysis, watchlist intelligence,
discovery candidates, and knowledge facts — into a calm, readable Daily Brief.

Atlas does not provide investment recommendations. It does not call external
APIs. It does not use AI or LLMs. It does not fetch live market data or news.

## What Atlas Is Not

- Not an AI trading assistant
- Not a recommendation engine
- Does not produce forecasts or targets
- Does not call external APIs
- Does not use LLMs or AI
- Does not fetch live market data or news
- Does not compare companies as investment opportunities

## Current Capabilities (RC2)

| Capability | Module | Status |
|---|---|---|
| Portfolio Domain | `atlas.domains.portfolio` | Current |
| Research Domain | `atlas.domains.research` | Current |
| Knowledge Domain | `atlas.domains.knowledge` | Current |
| Decision Engine | `atlas.domains.decision` | Current |
| Company Analysis | `atlas.capabilities.company_analysis` | Current |
| Watchlist Intelligence | `atlas.capabilities.watchlist_intelligence` | Current — `--knowledge` flag added (RC2) |
| Discovery | `atlas.capabilities.discovery` | Current |
| Daily Brief | `atlas.capabilities.daily_brief` | Current — all five input surfaces (RC2) |
| JSON export pipeline | `atlas.cli` + `atlas.adapters` | Current |
| Local demo | `examples/daily_brief_demo/` | Current — portfolio + evidence link resolution (RC2) |
| Weekly Investment Review | `atlas weekly-review` | Current — local-only, 10-section deterministic output |
| Decision Capture (API-001) | `atlas.core.domain.decision` | Current — Atlas Beta baseline |
| Decision Context (API-002) | `atlas.core.domain.decision_context` | Current — Atlas Beta baseline |

For the v1 local Weekly Review workflow, see [docs/AtlasWeeklyReviewUsageGuide.md](docs/AtlasWeeklyReviewUsageGuide.md).
For the Atlas Beta baseline (Decision Capture / Decision Context), see [docs/DecisionCaptureAPI001.md](docs/DecisionCaptureAPI001.md) and [docs/DecisionContextAPI002.md](docs/DecisionContextAPI002.md).

Legacy engines (`atlas/analysis/`, `atlas/daily/`, `atlas/intelligence/`, etc.)
remain functional. **New Product Increment work belongs in `atlas/core/`** —
not in `atlas/domains/` or `atlas/capabilities/`, which are pre-existing and
are not the current default for new work. See
[Architecture State](#architecture-state) for details.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

`.[dev]` installs `pytest` alongside Atlas's runtime dependencies — required
to run the test suite below. `pip install -e .` alone (without `[dev]`)
installs Atlas itself but not its test tooling.

## Run Tests

```bash
.venv/bin/python -m compileall atlas tests
.venv/bin/python -m pytest
```

7,041 tests pass, 3 skipped, as of the Atlas Beta baseline freeze
(API-001 Decision Capture + API-002 Decision Context).

## Quickstart: Daily Brief Demo

```bash
bash scripts/run_daily_brief_demo.sh
```

Runs a 7-step local pipeline (AMD + NVDA demo data) with no network calls.
Outputs to `tmp/atlas_demo/` including `daily_brief.txt`.

```bash
rm -rf tmp/atlas_demo   # clean up
```

Full details: [examples/daily_brief_demo/README.md](examples/daily_brief_demo/README.md)

## Architecture State

Atlas has three layers. **`atlas/core/` is the Atlas Beta baseline and the
official location for new Product Increment work** — read this section
before adding a new capability anywhere else.

**`atlas/core/` — Atlas Beta baseline (current, official location for new Product Increment work):**
- Clean Architecture: `domain/` → `application/` → `infrastructure/`
  (`persistence/`, `api/`); no layer depends outward on the one above it.
- `atlas/core/domain/decision/` — `Decision`, the aggregate root for API-001
  (Decision Capture). This is the approved baseline `Decision` concept.
- `atlas/core/domain/decision_context/` — `DecisionContext`, a separate
  aggregate for API-002 (Decision Context), referencing `Decision` by id
  only. This is the approved baseline `DecisionContext` concept.
- Full design of each: [docs/DecisionCaptureAPI001.md](docs/DecisionCaptureAPI001.md),
  [docs/DecisionContextAPI002.md](docs/DecisionContextAPI002.md).
- New Product Increments that extend Decision/DecisionContext, or that
  follow the same Clean Architecture pattern, belong here.

**Blueprint-aligned layer (pre-existing; not the current default for new work):**
- `atlas/domains/` — canonical concepts: portfolio, research, knowledge, decision, daily_brief, watchlist, ai, authentication
- `atlas/capabilities/` — product capabilities: company_analysis, discovery, watchlist_intelligence, daily_brief
- `atlas/shared/` — immutable canonical entities
- `atlas/adapters/` — bridges between domain types and legacy types
- `atlas/providers/` — opt-in market data providers (not called by demo or Daily Brief)
- `atlas/cli/` — CLI commands
- This layer remains functional and is not being touched or deprecated by
  the Atlas Beta baseline freeze. It is simply no longer the default
  location for *new* Product Increment work — that is `atlas/core/`, above.

**Legacy (preserved, not for expansion):**
- `atlas/analysis/`, `atlas/daily/`, `atlas/dashboard/`, `atlas/home/`,
  `atlas/intelligence/`, `atlas/portfolio_review/`, `atlas/watchlist_review/`,
  and others — original working engines. Remain functional and fully tested.
- **Note on naming:** `atlas/domains/decision/`, `atlas/decision/`, and
  `atlas/decision_journal/` each define their own, older Decision-shaped
  concepts — in places using the same names (`DecisionContext`,
  `DecisionType`) for different meanings than the `atlas/core/` baseline
  above. These predate the Atlas Beta baseline, are unrelated to it, and
  are deliberately left untouched until a separate future consolidation
  Product Increment addresses them explicitly — see the Future Backlog in
  [docs/BetaBaselineReadiness.md](docs/BetaBaselineReadiness.md). Do not
  treat any of them as the current `Decision`/`DecisionContext` baseline.

See [docs/ArchitectureConsolidation.md](docs/ArchitectureConsolidation.md)
for the older domains/capabilities guardrails.

## Documentation

| Document | Purpose |
|---|---|
| [docs/ATLAS_CONSTITUTION.md](docs/ATLAS_CONSTITUTION.md) | Mission and values |
| [docs/ATLAS_PRODUCT.md](docs/ATLAS_PRODUCT.md) | Product scope |
| [docs/ATLAS_ARCHITECTURE.md](docs/ATLAS_ARCHITECTURE.md) | Architecture intent |
| [docs/ArchitectureConsolidation.md](docs/ArchitectureConsolidation.md) | Current layer map and guardrails |
| [docs/DecisionCaptureAPI001.md](docs/DecisionCaptureAPI001.md) | Atlas Beta baseline — Decision Capture (`atlas/core`) |
| [docs/DecisionContextAPI002.md](docs/DecisionContextAPI002.md) | Atlas Beta baseline — Decision Context (`atlas/core`) |
| [docs/ObservationCaptureAPI003.md](docs/ObservationCaptureAPI003.md) | Atlas Beta baseline — Observation Capture (`atlas/core`) |
| [docs/HypothesisCaptureAPI004.md](docs/HypothesisCaptureAPI004.md) | Atlas Beta baseline — Hypothesis Capture (`atlas/core`) |
| [docs/EvidenceCaptureAPI005.md](docs/EvidenceCaptureAPI005.md) | Atlas Beta baseline — Evidence Capture (`atlas/core`) |
| [docs/CoreLoopATLAS001.md](docs/CoreLoopATLAS001.md) | Core Loop Skeleton — Question through Learning reasoning cycle (`atlas/core`) |
| [docs/FirstDecisionConversationATLAS002.md](docs/FirstDecisionConversationATLAS002.md) | First Decision Conversation — standalone CLI, Question through Decision (`atlas/core`) |
| [docs/DecisionReviewATLAS003.md](docs/DecisionReviewATLAS003.md) | Decision Review — standalone CLI, Outcome through Learning for a prior Decision (`atlas/core`) |
| [docs/DecisionTimelineATLAS004.md](docs/DecisionTimelineATLAS004.md) | Decision Timeline — standalone read-only CLI, chronological Decision history with nested review chains (`atlas/core`) |
| [docs/PatternRecognitionATLAS005.md](docs/PatternRecognitionATLAS005.md) | Pattern Recognition — standalone read-only CLI, discovers recurring structure across recorded Decisions (`atlas/core`) |
| [docs/StrategySignatureATLAS006.md](docs/StrategySignatureATLAS006.md) | Strategy Signature Recognition — standalone read-only CLI, connected-component coherence across recognized Patterns (`atlas/core`) |
| [docs/DecisionReflectionATLAS007.md](docs/DecisionReflectionATLAS007.md) | Decision Reflection — optional, occasion-bound correspondence between an ongoing First Decision Conversation and recognized Patterns/Strategy Signatures (`atlas/core`) |
| [docs/ADR-004-API-Serialization-Standard.md](docs/ADR-004-API-Serialization-Standard.md) | ADR — API serialization standard (implemented: camelCase wire format) |
| [docs/BetaBaselineReadiness.md](docs/BetaBaselineReadiness.md) | Atlas Beta baseline release-readiness review |
| [docs/LegacyConsolidationPlan.md](docs/LegacyConsolidationPlan.md) | Legacy module inventory and migration plan |
| [docs/DailyBrief.md](docs/DailyBrief.md) | Daily Brief capability reference |
| [docs/CompanyAnalysis.md](docs/CompanyAnalysis.md) | Company Analysis reference |
| [docs/DecisionLog.md](docs/DecisionLog.md) | Sprint decision history |
| [docs/ReleaseCandidate.md](docs/ReleaseCandidate.md) | RC1 and RC2 release notes |
| [docs/DevelopmentGuide.md](docs/DevelopmentGuide.md) | Developer guide |
| [docs/SprintHistory.md](docs/SprintHistory.md) | Historical sprint notes (Sprints 37–72) |
| [examples/daily_brief_demo/README.md](examples/daily_brief_demo/README.md) | Demo walkthrough |

## Constraints

Providers are opt-in. The demo pipeline and Daily Brief make no network calls.
No UI. No AI. No external APIs. No recommendation language.

---

## Sprint History

Historical sprint notes (Sprints 37–72) have been moved to
[docs/SprintHistory.md](docs/SprintHistory.md).
