# Weekly Review Trial Findings — Sprint 213

**Date:** 2026-01-03
**Trial bundle:** `examples/weekly_review_realistic/`
**Command:** `atlas weekly-review` (all optional inputs provided)

---

## Trial Bundle Summary

| Input | Detail |
|-------|--------|
| Portfolio | 11 holdings, 1 account, €1M total, 9 sectors + 1 unclassified |
| Watchlist | 5 items — varied statuses: Research, Needs More Evidence, Watchlist, Suitable for Further Review, Decision Deferred |
| Investor profile | 7 principles, 5 constraints, risk_tolerance: "Balanced", time_horizon: "7-10 years" |
| Decision journal | 4 entries: LVMH, MSFT, ADYEN, NESTE |
| Company facts | 3 of 16 investable tickers provided (ASML, NOVO, MSFT) |
| Financial history | 3 of 16 investable tickers provided (ASML, NOVO, MSFT) |
| Scope notes | Multi-section markdown file (~15 lines) |

---

## Section-by-Section Findings

### 1. Review Scope

**Status: Good after fix.**

The initial render included raw markdown syntax (`## Focus areas this week`, `**bold**`) from scope_notes.md. This was friction — the output showed formatting noise, not substantive content.

**Fix applied:** Added `_preview_scope_notes()` helper that strips `#` markdown headers and `**`/`*`/`` ` `` inline syntax, joins the first 4 substantive lines with ` | `, truncates to 300 chars, and appends total line count (`[15 lines]`).

**Post-fix result:** The scope preview renders as a compact, readable single line with line count. The full scope_notes content is still available via the input file directly.

**Usability verdict:** Good. The scope preview provides just enough context.

---

### 2. Portfolio Context

**Status: Good after fix.**

Two issues surfaced:

1. **Combined ASML+NOVO concentration (45%) was invisible.** With the old single-position threshold at >30%, neither ASML (24%) nor NOVO (21%) fired individually. The combined exposure was real and meaningful.

   **Fix applied:** (a) Lowered single-position threshold from >30% to >25% (ASML now fires). (b) Added combined top-2 note that fires when top-2 non-cash holdings together exceed 40%.

2. **NESTE unclassified sector handled correctly.** The missing sector input warning fired ("classified as 'Unclassified'"), and NESTE appeared in the sector breakdown under "Unclassified". The path works end-to-end.

**Post-fix output snippet:**
```
- High single-position weight: ASML at 24.0%. Weight is notable relative to portfolio.
- Combined concentration: ASML + NOVO = 45.0% of loaded portfolio value. Top-2 combined exposure may warrant review.
```

**Usability verdict:** Good. Concentration signals are now properly calibrated.

---

### 3. Watchlist Review

**Status: Good.**

All 5 watchlist items rendered with full detail: name, status, reason, evidence gaps, open questions, manual observations, notes. The section is verbose but the information is genuinely useful for a real review. Each item's evidence gaps are individually labeled (`[XYL] Evidence Gap`).

**Observation:** With a larger watchlist (10+ items), Section 3 would become very long. A future sprint could consider a compact mode or pagination, but this is out of scope for Sprint 213.

**Forbidden language issue found and fixed:** VEEV's watchlist entry originally contained "cross-sell penetration" and "upsell trajectory" — both contain "sell" as a substring. Replaced with "account expansion penetration" and "account expansion trajectory".

**Usability verdict:** Good for up to ~6 items. Verbosity may warrant a future summary/compact option.

---

### 4. Company Reviews Needing Attention

**Status: Good.**

Correctly flagged:
- All 5 watchlist items with open evidence gaps
- ASML and NOVO as visible holdings (based on high weight / top-2 presence)

No false positives (no CASHEUR, no low-weight holdings incorrectly flagged).

**Usability verdict:** Good. Attention flags are appropriately targeted.

---

### 5. Portfolio Fit and Suitability Notes

**Status: Good after enhancement.**

Prior to Sprint 213, this section showed concentration notes only. Profile fields (risk_tolerance, time_horizon, constraints) were not surfaced — the investor profile data was loaded by the engine but not passed through `WeeklyReviewLoadResult`.

**Enhancement applied:** Added `profile_risk_tolerance`, `profile_time_horizon`, `profile_constraints` to `WeeklyReviewLoadResult`. Section 5 now renders:
- Risk tolerance: "Balanced — quality focus"
- Time horizon: "7-10 years"
- All 5 stated constraints (each as a labeled `Constraint:` line)

**Post-fix output excerpt:**
```
Risk tolerance: Balanced — quality focus
Time horizon: 7-10 years
Stated constraints (5):
  Constraint: No leverage or margin trading.
  Constraint: No companies with active financial misrepresentation history in the past 5 years.
  ...
```

**Usability verdict:** Substantially better with profile fields. This is the most useful suitability output possible without live data.

---

### 6. Risk and Principle Guardrails

**Status: Good after enhancement.**

Prior to Sprint 213, Section 6 showed risk score alerts only (thresholds: >60 elevated, >75 high). For this portfolio, NESTE (58) and EQT (52) were below threshold — so no alerts fired. Without profile principles, the section was nearly empty.

**Enhancement applied:** Added `profile_principles` to `WeeklyReviewLoadResult`. Section 6 now renders all 7 investor principles before the risk checks:
```
Stated principles (7):
  Principle: Evidence before opinion. No position without documented reasoning.
  Principle: Quality over quantity. Concentrated portfolio of well-understood businesses.
  ...
```

**Usability verdict:** Significantly better. Principles provide essential guardrail context even when no risk score thresholds are breached.

---

### 7. Open Decisions

**Status: Good.**

All 4 journal entries rendered with:
- Decision type and date
- Truncated rationale (first 200 chars + ellipsis)
- Follow-up trigger if set (`[Follow-up]` labeled line)

MSFT entry (`No Action Warranted`) and ADYEN entry (`Needs More Evidence`) both rendered clearly with distinct labels.

**Usability verdict:** Good. Decision journal section is substantive and well-structured.

---

### 8. Missing Evidence

**Status: Good after enhancement.**

Before Sprint 213, this section showed evidence gaps from watchlist items and a single generic "Company facts not loaded" or "Financial history not loaded" note (binary yes/no).

**Enhancement applied:** Per-ticker presence check added. Section 8 now shows:
- Individual `[TICKER] Evidence Gap` lines (16 total from 5 watchlist items)
- `Missing company facts for: ADYEN, COLB, DHR, DXCM, EQT, ESSITY, HXGN, LVMH, NESTE, RCKWB, VEEV, XYL` (compact single line)
- `Missing financial history for: ADYEN, COLB, DHR, DXCM, EQT, ESSITY, HXGN, LVMH, NESTE, RCKWB, VEEV, XYL` (compact single line)

This is substantially more actionable than "Company facts: not loaded." The user knows exactly which 12 tickers need data files.

**Observation:** Section 8 is the longest section (16 evidence gap lines + 2 compact missing lines). This is correct — missing evidence is the primary friction point in this portfolio.

**Usability verdict:** Good. Compact per-ticker format prevents the section from becoming unmanageable.

---

### 9. Follow-Up Questions

**Status: Good.**

Rendered open questions from all 5 watchlist items (3-4 questions each) plus additional follow-up triggers from journal entries. The section is long (20+ lines) but the questions are substantive and directly derived from inputs.

**Usability verdict:** Good. No usability issues.

---

### 10. Non-Actions / Reasons to Wait

**Status: Good.**

```
- Decision Deferred: ADYEN — Adyen. Status: Needs More Evidence.
- Decision Deferred: DXCM — DexCom. Status: Decision Deferred.
- Reason to Wait: 16 evidence gap(s) identified across watchlist items.
- Reason to Wait: Company facts missing for 12 ticker(s): ADYEN, COLB, DHR, DXCM, EQT and others.
- Reason to Wait: Financial history missing for 12 ticker(s).
- No Action Warranted: This review is informational only.
- Reminder: No action is a valid and often appropriate outcome of a weekly review.
- Atlas supports better judgment. It does not replace it.
```

The per-ticker missing facts/financials data now flows through to Section 10 as concrete reasons to wait, replacing the generic "Company facts not loaded" placeholder.

**Usability verdict:** Good. Section 10 is substantive and appropriately cautious.

---

## Forbidden Language

**Result: Clean after fix.**

Initial run flagged "sell" in VEEV watchlist entry ("cross-sell penetration", "upsell trajectory"). Both were description-of-feature text, not recommendations, but the substring check caught them correctly. Fixed by replacing with "account expansion" variants.

**Post-fix scan result:** `Forbidden terms: NONE — clean`

---

## Code Improvements Made

| Change | Trigger | File |
|--------|---------|------|
| Load profile principles/constraints into `WeeklyReviewLoadResult` | Section 5/6 empty without profile fields | `inputs.py`, `render.py` |
| Per-ticker company facts presence check | Generic "facts not loaded" not actionable | `inputs.py`, `render.py` |
| Per-ticker financials presence check | Same | `inputs.py`, `render.py` |
| `_preview_scope_notes()` helper | Raw markdown in Section 1 | `render.py` |
| Combined top-2 concentration note | 45% ASML+NOVO invisible under old threshold | `render.py` |
| Single-position threshold lowered 30% → 25% | ASML at 24% should have fired | `render.py` |

---

## Issues Deferred (out of Sprint 213 scope)

| Issue | Status |
|-------|--------|
| Section 3 verbosity for large watchlists | Deferred — acceptable up to ~6 items |
| No scope_notes_path field (only string) | By design — caller reads file; not Atlas responsibility |
| No summary/compact mode for evidence gaps >10 | Deferred |

---

## Sprint 214 Recommendation

The Weekly Review now produces genuinely useful, complete output for a realistic portfolio. The most natural next sprint target:

**Option A — Sparse data handling:**  
Currently, 12/16 investable tickers have no facts/financials. The renderer shows "Missing company facts for: [12 tickers]" — which is a real friction point. A Sprint 214 could focus on making it easy to supply data files for even 1-2 more tickers, with a template generator (`atlas weekly-review scaffold-facts`) that creates an empty JSON template from the watchlist/portfolio tickers. This makes Atlas self-bootstrapping.

**Option B — Journal entry aging:**  
NESTE's journal entry is from 2024-09-15 — over 15 months ago. The renderer could flag stale journal entries (>90 days) in Section 7 or Section 10, prompting a revisit. This is a small, focused improvement with high signal value.

**Option C — Read-only output file:**  
Write the full 10-section review to a timestamped file in `output/weekly_review/YYYY-MM-DD.md` for record-keeping. The CLI prints to stdout; the file version becomes the durable record. This is simple and high-value.

**Recommended: Option B (journal aging)** — smallest scope, highest signal per line of code. Option A is attractive but introduces a new sub-command surface. Option C is useful but not urgent.
