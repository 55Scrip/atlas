# Weekly Review Release Hardening — Sprint 216

**Date:** 2026-07-03
**Scope:** Sprints 209–215 (Weekly Investment Review v1 track)

---

## Hardening Summary

Sprint 216 verified that all Weekly Review sprints from specification (Sprint 209)
through usage guide (Sprint 215) remain stable, provider-free, deterministic,
and usable before further product expansion.

---

## Commands Run

### Minimal command

```bash
atlas weekly-review \
  --portfolio examples/weekly_review/portfolio.json \
  --watchlist examples/weekly_review/watchlist.json
```

**Result:** Exit 0. All 10 sections rendered. Section 10 present and non-empty.
4 expected warnings (no profile, no journal, no company facts, no financials).

### Full minimal-bundle command

```bash
atlas weekly-review \
  --portfolio examples/weekly_review/portfolio.json \
  --watchlist examples/weekly_review/watchlist.json \
  --profile examples/weekly_review/investor_profile.json \
  --journal examples/weekly_review/decision_journal.json \
  --company-facts examples/weekly_review/company_facts \
  --financials examples/weekly_review/financials \
  --as-of 2026-01-01 \
  --scope-notes examples/weekly_review/scope_notes.md
```

**Result:** Exit 0. All 10 sections rendered. Per-ticker missing facts/financials
noted in Sections 8 and 10. No aging alerts (journal entries within 90 days of
2026-01-01). Section 10 non-empty.

### Realistic bundle command

```bash
atlas weekly-review \
  --portfolio examples/weekly_review_realistic/portfolio.json \
  --watchlist examples/weekly_review_realistic/watchlist.json \
  --profile examples/weekly_review_realistic/investor_profile.json \
  --journal examples/weekly_review_realistic/decision_journal.json \
  --company-facts examples/weekly_review_realistic/company_facts \
  --financials examples/weekly_review_realistic/financials \
  --as-of 2026-01-01 \
  --scope-notes examples/weekly_review_realistic/scope_notes.md
```

**Result:** Exit 0. All 10 sections rendered. NESTE journal note (2024-09-15,
473 days from 2026-01-01) correctly flagged with `[Aging Note]` in Section 7 and
`Reason to Wait` in Section 10. LVMH (75 days), MSFT (24 days), ADYEN (57 days)
not flagged. Section 10 non-empty.

---

## Output Contract Status

| Contract item | Status |
|---------------|--------|
| All 10 sections present | ✓ |
| Section 10 always non-empty | ✓ |
| Input status block deterministic | ✓ |
| Warnings block deterministic | ✓ |
| No recommendation language | ✓ |
| No price target language | ✓ |
| No urgent language | ✓ |
| No buy/sell language in output | ✓ |

---

## Journal Aging Verification

| Behavior | Status |
|----------|--------|
| Notes older than 90 days flagged when as_of provided | ✓ (NESTE: 473 days) |
| Exactly 90-day notes not flagged | ✓ (verified by test) |
| Younger notes not flagged | ✓ (LVMH 75d, MSFT 24d, ADYEN 57d clean) |
| Closed/resolved entries skipped | ✓ |
| Missing date does not fail rendering | ✓ |
| Invalid date does not fail rendering | ✓ |
| Aging note in Section 7 | ✓ |
| Reason to Wait in Section 10 | ✓ |
| No live clock dependency | ✓ (requires as_of) |

---

## Usage Guide Verification

| Item | Status |
|------|--------|
| All documented flags exist in CLI | ✓ |
| All referenced example paths exist | ✓ (13/13 paths verified) |
| Required files accurately described | ✓ |
| Optional files accurately described | ✓ |
| All 10 sections explained | ✓ |
| Journal aging behavior matches implementation | ✓ |
| Common warnings match loader warning codes | ✓ |
| Limitations are accurate | ✓ |
| README pointer correct | ✓ |

---

## Fix Applied

**CLI docstring stale:** `atlas/cli/main.py` still said "Run the Atlas Weekly
Investment Review **skeleton**" and imported `render_weekly_review_skeleton`
(the Sprint 211 alias). Updated to use `render_weekly_review` directly and
updated docstring to reflect current behavior. No behavioral change — the alias
delegates to the same function.

---

## Provider / Network Boundary

| Check | Status |
|-------|--------|
| `atlas.providers` not imported in `weekly_review/` | ✓ |
| `requests` not imported | ✓ |
| `urllib` not imported | ✓ |
| `httpx` not imported | ✓ |
| `aiohttp` not imported | ✓ |
| No live market data | ✓ |
| No live news | ✓ |
| No broker API | ✓ |

---

## Language Guardrails

Forbidden terms scanned across:
- `examples/weekly_review/` — clean
- `examples/weekly_review_realistic/` — clean
- `docs/AtlasWeeklyReviewUsageGuide.md` — clean
- `atlas/weekly_review/render.py` — clean
- `atlas/weekly_review/inputs.py` — clean

`docs/AtlasWeeklyInvestmentReviewSpec.md` contains forbidden terms in
**guardrail definition context only** (e.g., "No buy/sell language in decision
status", "Forbidden: No price targets") — this is the spec listing what is
prohibited, not using forbidden language in output. Consistent with all prior
sprint audits.

---

## Prior Closed Cleanup Track Stability

| Deleted target | Status |
|----------------|--------|
| `atlas/reasoning/` | Absent ✓ |
| `atlas/reports/` | Absent ✓ |
| `atlas/storage/` | Absent ✓ |
| `atlas/models/investment_report.py` | Absent ✓ |
| `atlas/services/kpi_service.py` | Absent ✓ |
| `tests/test_kpi_service.py` | Absent ✓ |
| Provider re-exports from `atlas.analysis` | Absent ✓ |
| Atlas Edge naming in active code | Absent ✓ (only in boundary test assertions) |

---

## Test Results

| Suite | Result |
|-------|--------|
| `test_weekly_review_inputs_sprint210.py` | ✓ |
| `test_weekly_review_cli_sprint211.py` | ✓ |
| `test_weekly_review_renderer_sprint212.py` | ✓ |
| `test_weekly_review_trial_sprint213.py` | ✓ |
| `test_weekly_review_journal_aging_sprint214.py` | ✓ |
| `test_weekly_review_usage_guide_sprint215.py` | ✓ |
| Full suite | 1954 passed, 3 skipped |
| RC2 | Green |
| Demo | Green |
| Release verification | Green |

---

## Remaining Implementation Gaps

The following are documented limitations, not regressions:

- Company analysis engine not wired into Section 4
- Suitability engine not wired into Section 5
- Risk/principles engine not wired into Section 6
- Financial CSV not parsed numerically (presence check only)
- No live data
- No UI
- No multilingual renderer

---

## Sprint 217 Recommendation

**Release candidate freeze for internal v1.**

After six productization sprints and a hardening checkpoint, `atlas weekly-review`
is stable, documented, and usable with local files. The next highest-value step
before further engine wiring is to formally mark this as the internal v1 release
candidate — update version metadata, close the Weekly Review v1 track in docs,
and confirm all guardrail acceptance criteria are met.

This gives a clear marker before deeper engine integration begins, and ensures
the local-only deterministic foundation is explicitly approved before complexity
increases.

Alternative if team prefers to continue feature work immediately:
**Load investor profile principles and constraints more deeply into Weekly Review** —
make principles enforce-checked against holdings/watchlist and render as pass/fail
guardrails in Section 6, without invoking the full suitability engine.
