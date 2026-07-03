# Atlas Internal v1 Release Candidate

**Sprint:** 217
**Date:** 2026-07-03
**Version:** 0.1.0
**Release stage:** Internal v1 RC — Weekly Review

---

## What Is Atlas Internal v1

Atlas internal v1 is a CLI-first, local-only Weekly Investment Review workflow
for long-term investment reasoning.

It loads a local portfolio, watchlist, optional investor profile, optional
decision journal, optional company facts, optional financials, and optional
scope notes. It renders a deterministic 10-section Weekly Review that surfaces
portfolio context, watchlist state, open decisions, missing evidence,
follow-up questions, and reasons to wait.

It does not provide investment recommendations, valuation forecasts, market-timing
signals, live news, live market data, broker integrations, UI, AI-generated
conclusions, or Atlas Edge behavior.

Atlas supports better judgment. It does not replace it.

---

## Included Capabilities

| Capability | Sprint | Status |
|-----------|--------|--------|
| `atlas weekly-review` command | 211 | Current |
| Local portfolio input (positions and accounts formats) | 210 | Current |
| Local watchlist input (rich v1 format with status/evidence/questions) | 210 | Current |
| Optional investor profile (principles, constraints, risk tolerance, time horizon) | 210/213 | Current — rendered in Sections 5 and 6 |
| Optional decision journal (raw entries, entry count, follow-up triggers) | 212/213 | Current |
| Optional company facts directory (per-ticker JSON presence check) | 213 | Current |
| Optional financials directory (per-ticker CSV presence check) | 213 | Current |
| Optional scope notes (markdown preview, header-stripped) | 213 | Current |
| Deterministic input validation with structured warnings | 210 | Current |
| Deterministic warning rendering | 210 | Current |
| Section 1 — Review Scope | 211/212 | Current |
| Section 2 — Portfolio Context (weights, sectors, concentration notes) | 212 | Current |
| Section 3 — Watchlist Review (per-item status, evidence gaps, questions) | 212 | Current |
| Section 4 — Company Reviews Needing Attention (portfolio/watchlist overlap, visible holdings) | 212 | Current |
| Section 5 — Portfolio Fit and Suitability Notes (profile fields, structural observations) | 212/213 | Current — local-input-derived, not engine-wired |
| Section 6 — Risk and Principle Guardrails (principles, risk scores, sector concentration) | 212/213 | Current — local-input-derived, not engine-wired |
| Section 7 — Open Decisions (journal summaries, follow-up triggers, aging notes) | 212/214 | Current |
| Section 8 — Missing Evidence (watchlist gaps, per-ticker missing facts/financials) | 212/213 | Current |
| Section 9 — Follow-Up Questions (watchlist questions, journal triggers) | 212 | Current |
| Section 10 — Non-Actions / Reasons to Wait (always non-empty) | 212 | Current |
| Journal aging alerts (open entries older than 90 days, uses `as_of`) | 214 | Current |
| Weekly Review usage guide | 215 | Current |

---

## Excluded Capabilities (Intentionally Deferred)

The following are not part of internal v1. They are documented limitations,
not regressions.

- Live market data or live prices
- Live news or earnings release ingestion
- Broker synchronisation (Avanza, Nordnet, or any other)
- Automatic portfolio import from external sources
- Screenshot or image ingestion
- Automatic research import
- Company analysis engine wired into Section 4
- Suitability engine wired into Section 5
- Risk/principles engine wired into Section 6
- Numerical financial CSV analysis (presence check only)
- Background alerts or notifications
- Investment recommendations of any kind
- Valuation forecasts or analyst-style targets
- Market-timing signals
- User interface or dashboard
- Multilingual renderer output
- LLM or AI-generated conclusions
- External API calls beyond existing opt-in provider behavior
- Atlas Edge concepts, naming, or architecture

---

## Command Surface

**Minimal command (required inputs only):**

```bash
atlas weekly-review \
  --portfolio my_review/portfolio.json \
  --watchlist my_review/watchlist.json
```

**Full command (all optional inputs):**

```bash
atlas weekly-review \
  --portfolio my_review/portfolio.json \
  --watchlist my_review/watchlist.json \
  --profile my_review/investor_profile.json \
  --journal my_review/decision_journal.json \
  --company-facts my_review/company_facts \
  --financials my_review/financials \
  --as-of 2026-01-01 \
  --scope-notes my_review/scope_notes.md
```

See [docs/AtlasWeeklyReviewUsageGuide.md](AtlasWeeklyReviewUsageGuide.md) for
setup instructions, file format details, and output interpretation.

---

## Acceptance Criteria Checklist

All items must be met for internal v1 RC status.

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Repository identity confirmed as Atlas, not Atlas Edge | ✓ Met |
| 2 | `atlas weekly-review` command exists | ✓ Met |
| 3 | Minimal command exits 0 | ✓ Met |
| 4 | Full command exits 0 | ✓ Met |
| 5 | Realistic command exits 0 (if bundle exists) | ✓ Met |
| 6 | Local portfolio input loads (positions and accounts formats) | ✓ Met |
| 7 | Local watchlist input loads (rich v1 format) | ✓ Met |
| 8 | Optional inputs warn rather than fail | ✓ Met |
| 9 | All 10 sections render | ✓ Met |
| 10 | Section 10 is present and non-empty | ✓ Met |
| 11 | Output is deterministic with same inputs | ✓ Met |
| 12 | Journal aging uses `as_of`, not live clock | ✓ Met |
| 13 | Output avoids recommendation language | ✓ Met |
| 14 | Output avoids forecast/target language | ✓ Met |
| 15 | Output avoids action-pressure language | ✓ Met |
| 16 | Provider/network boundary is clean | ✓ Met |
| 17 | No broker integration introduced | ✓ Met |
| 18 | No live data dependency introduced | ✓ Met |
| 19 | Usage guide exists | ✓ Met |
| 20 | README points to usage guide | ✓ Met |
| 21 | Tests pass | ✓ Met — 2275 passed, 3 skipped |
| 22 | Demo passes | ✓ Met — RC2 green |
| 23 | Release verification passes | ✓ Met — RC2 green |
| 24 | Closed cleanup deletion targets remain absent | ✓ Met |

**Result: All 24 acceptance criteria met. Internal v1 RC status confirmed.**

---

## Guardrail Acceptance

| Guardrail | Status |
|-----------|--------|
| No investment recommendations in output | ✓ |
| No valuation forecasts or analyst-style targets in output | ✓ |
| No action-pressure language in output | ✓ |
| No market-timing claims in output | ✓ |
| No live provider dependency | ✓ |
| No Atlas Edge concepts | ✓ |
| Human judgment remains final | ✓ — "Atlas supports better judgment. It does not replace it." |
| No action warranted remains valid outcome | ✓ — Section 10 always states this explicitly |

Atlas Weekly Review v1 is a process support tool for investment reasoning
workflows. It is not investment advice. All output is derived from user-supplied
local files.

---

## Verification Results

| Check | Result |
|-------|--------|
| `python -m compileall atlas tests` | Clean — no errors |
| `pytest` | 1954 passed, 3 skipped |
| `scripts/verify_release_candidate.sh` | RC2 green |
| `scripts/run_daily_brief_demo.sh` | Green |
| `atlas weekly-review` minimal | Exit 0, all 10 sections |
| `atlas weekly-review` full | Exit 0, all 10 sections |
| `atlas weekly-review` realistic (with `--as-of 2026-01-01`) | Exit 0, all 10 sections, NESTE aging alert correct |

---

## Known Limitations

These are intentional deferred items for v1.1+:

1. Company analysis engine not wired into Section 4 — qualitative attention notes only
2. Suitability engine not wired into Section 5 — structural notes only
3. Risk/principles engine not wired into Section 6 — user-supplied data only
4. Financial CSV files not numerically analysed — presence check only
5. Profile principles/constraints not rule-checked against holdings
6. No live data of any kind
7. No multilingual output
8. No UI

---

## Defining Documents

| Document | Purpose |
|----------|---------|
| [docs/AtlasV1OperatingMode.md](AtlasV1OperatingMode.md) | v1 product boundary definition |
| [docs/AtlasWeeklyInvestmentReviewSpec.md](AtlasWeeklyInvestmentReviewSpec.md) | Full workflow specification |
| [docs/AtlasWeeklyReviewUsageGuide.md](AtlasWeeklyReviewUsageGuide.md) | v1 user-facing usage guide |
| [docs/WeeklyReviewReleaseHardening.md](WeeklyReviewReleaseHardening.md) | Sprint 216 hardening record |
| [docs/DecisionLog.md](DecisionLog.md) | Sprint-by-sprint decision record |

---

## Productization Track Summary

| Sprint | Milestone |
|--------|-----------|
| 208 | Atlas v1 operating mode defined |
| 209 | Weekly Investment Review specified |
| 210 | Local input schemas implemented |
| 211 | `atlas weekly-review` CLI command added |
| 212 | Deterministic renderer implemented |
| 213 | Realistic portfolio trial run |
| 214 | Journal aging alerts added |
| 215 | v1 usage guide created |
| 216 | Release hardening checkpoint |
| 217 | Internal v1 RC freeze |

---

## After the Freeze

The internal v1 RC baseline is now established. Further product expansion should
build on this foundation without changing the local-only, deterministic, provider-free
character of the Weekly Review workflow.

**Sprint 218 (post-v1 improvement — complete):**
Investor profile principles and constraints are now rendered in Sections 5, 6,
and 10. Each principle appears as a "Reason to Wait" in Section 10; each
constraint appears as a "No Action Warranted" note. Malformed fields warn and
fail safely. No suitability scoring, no engine wiring, no provider dependency.

**Sprint 219 (post-v1 improvement — complete):**
Per-ticker local evidence presence checks added. `WeeklyReviewTickerEvidence`
dataclass tracks presence and source for each investable ticker. Section 8 emits
per-ticker `Evidence Gap [TICKER]` lines. Section 9 adds per-ticker follow-up
questions. Section 10 adds per-ticker reasons to wait. No provider dependency.

**Sprint 220 (post-v1 improvement — complete):**
Second realistic trial run. Four verbosity problems found and fixed: Section 8
combined "both missing" into one line per ticker; Section 9 replaced 24 identical
per-ticker questions with two grouped lists; Section 10 consolidated 24 per-ticker
reasons into two summary lines and collapsed principle/constraint boilerplate into
blocks. Section 10 reduced from ~40 to ~18 lines.

**Sprint 221 (post-v1 specification — complete):**
Snapshot / Screenshot Input workflow specified. New document
`docs/AtlasSnapshotInputWorkflow.md` defines seven snapshot types (Portfolio,
Watchlist, Open Orders, News, External Analysis, Research Notes, Company Facts),
a classification contract, a draft contract with five confirmation states, accuracy
and safety guardrails, a privacy and security boundary, mapping from each snapshot
type to existing Atlas local input files, and relationship to future chat-first
workspace UX. No runtime behavior changed. No OCR, AI, image parsing, or provider
dependency introduced. Internal v1 foundation unchanged.

**Sprint 222 (post-v1 improvement — complete):**
Research notes input added to Weekly Review. New `--research-notes DIR` CLI
argument. Per-ticker `research_notes/<TICKER>/notes.md` files are loaded with
bounded reads and lightweight section parsing. Evidence gaps surface in Section 8;
open questions and risks in Section 9; reasons to wait in Section 10. Missing or
malformed notes are non-blocking. Two example files added. No OCR, AI, image
parsing, or provider dependency introduced. Internal v1 foundation unchanged.

**Sprint 223 (post-v1 improvement — complete):**
Snapshot Draft schema defined. New `atlas/snapshot_input/` package. `SnapshotType`
(8 values), `SnapshotConfirmationStatus` (5 states), `SnapshotConfidence` (4 levels),
`SnapshotDraft` dataclass with validation, serialization (`to_dict`/`from_dict`/
`to_json`/`from_json`), and file helpers (`load_snapshot_draft`/`save_snapshot_draft`).
Three example draft files. No OCR, AI, or provider dependency. No Weekly Review
behavior changed. Internal v1 foundation unchanged.

**Sprint 224 (post-v1 improvement — complete):**
`atlas snapshot validate <path>` CLI command added. Validates a Snapshot Draft JSON
file and renders a human-readable summary: type, confidence, confirmation status,
target local file, related tickers, uncertainties, missing required fields, and
safety boundary. Exit 0 on valid, exit 1 on invalid JSON, invalid schema, or missing
file. No file writing. No mutation. New `atlas/snapshot_input/render.py`. CLI extended
with `snapshot_app` Typer sub-group. No provider imports. No network calls. No
Weekly Review behavior changed. Internal v1 foundation unchanged.
